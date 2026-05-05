#!/bin/bash
# Claude Code が stdin に送信する JSON データを読み取る
input=$(cat)
# デバッグ用: 受け取った JSON をファイルに保存（必要に応じてコメントアウト）
# echo "$input" > .claude/last_status.json

# トークン数を K/M 表示に変換する関数
format_tokens() {
  local n=$1
  if [ "$n" -ge 1000000 ] 2>/dev/null; then
    awk "BEGIN { printf \"%.1fM\", $n/1000000 }"
  elif [ "$n" -ge 1000 ] 2>/dev/null; then
    awk "BEGIN { printf \"%.1fK\", $n/1000 }"
  else
    echo "$n"
  fi
}

# セッション時間を HH:MM:SS 形式（不要な部分は省略）に変換する関数
format_duration() {
  local ms=$1
  local total_sec=$(( ms / 1000 ))
  local h=$(( total_sec / 3600 ))
  local m=$(( (total_sec % 3600) / 60 ))
  local s=$(( total_sec % 60 ))
  if [ "$h" -gt 0 ]; then
    printf "%dh%02dm%02ds" "$h" "$m" "$s"
  elif [ "$m" -gt 0 ]; then
    printf "%dm%02ds" "$m" "$s"
  else
    printf "%ds" "$s"
  fi
}

# モデル
MODEL=$(echo "$input" | jq -r '.model.display_name')

# "// 0" はフィールドが null の場合のフォールバックを提供します
PCT_INT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
PCT=$(LC_ALL=C printf '%.1f' "$(echo "$input" | jq -r '.context_window.used_percentage // 0')")
RAW_IN=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0' | cut -d. -f1)
RAW_OUT=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0' | cut -d. -f1)
RAW_CTX=$(echo "$input" | jq -r '.context_window.context_window_size // 0' | cut -d. -f1)
TOTAL_INPUT_TOKEN=$(format_tokens "$RAW_IN")
TOTAL_OUTPUT_TOKEN=$(format_tokens "$RAW_OUT")
RAW_USED=$(echo "$input" | jq -r '
  (.context_window.current_usage.input_tokens // 0) +
  (.context_window.current_usage.output_tokens // 0) +
  (.context_window.current_usage.cache_creation_input_tokens // 0) +
  (.context_window.current_usage.cache_read_input_tokens // 0)
')
USED_TOKENS=$(format_tokens "$RAW_USED")
CTX_SIZE=$(format_tokens "$RAW_CTX")

# コスト
RAW_COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
COST=$(LC_ALL=C printf '$%.2f' "$RAW_COST")

# セッション時間
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0' | cut -d. -f1)
DURATION=$(format_duration "$DURATION_MS")

# カレントディレクトリ
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
# git ブランチ名
CWD=$(echo "$input" | jq -r '.cwd // ""')
BRANCH=$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# コンテキスト使用率に応じた色（50% 未満は色なし）
if   [ "$PCT_INT" -ge 85 ]; then COLOR="\033[31m"       RESET="\033[0m"  # 赤
elif [ "$PCT_INT" -ge 70 ]; then COLOR="\033[38;5;208m" RESET="\033[0m"  # オレンジ
elif [ "$PCT_INT" -ge 50 ]; then COLOR="\033[33m"       RESET="\033[0m"  # 黄
else                              COLOR=""              RESET=""          # 色なし
fi

# ステータスライン出力
echo -e "$MODEL | 📊 ${COLOR}${USED_TOKENS}/${CTX_SIZE} ${PCT}%${RESET} | ↑${TOTAL_INPUT_TOKEN} ↓${TOTAL_OUTPUT_TOKEN} | 💰 ${COST} | ⏱️ ${DURATION}"
if [ -n "$BRANCH" ]; then
  echo -e "📁 ${DIR##*/}/ on $BRANCH"
else
  echo -e "📁 ${DIR##*/}/"
fi