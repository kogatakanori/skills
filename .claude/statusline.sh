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

# rate_limits.*.resets_at（Unix epoch seconds）から現在時刻までの残り時間を d/h/m 表示に変換する関数
format_resets_in() {
  local resets_at=$1
  local now=$2
  local diff=$(( resets_at - now ))
  if [ "$diff" -le 0 ]; then
    echo "now"
    return
  fi
  local d=$(( diff / 86400 ))
  local h=$(( (diff % 86400) / 3600 ))
  local m=$(( (diff % 3600) / 60 ))
  if [ "$d" -gt 0 ]; then
    printf "%dd%02dh" "$d" "$h"
  elif [ "$h" -gt 0 ]; then
    printf "%dh%02dm" "$h" "$m"
  else
    printf "%dm" "$m"
  fi
}

# 使用率（整数）に応じた色エスケープシーケンスを返す関数（コンテキスト使用率と同じ閾値）
rate_limit_color() {
  local pct_int=$1
  if   [ "$pct_int" -ge 85 ]; then echo "\033[31m"       # 赤
  elif [ "$pct_int" -ge 70 ]; then echo "\033[38;5;208m" # オレンジ
  elif [ "$pct_int" -ge 50 ]; then echo "\033[33m"       # 黄
  else echo ""
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

# プランのレート制限（Claude.ai Pro/Max 契約時、セッション最初の API 応答後のみ存在）
NOW=$(date +%s)
RL_RESET="\033[0m"
FIVE_H_PCT=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
FIVE_H_RESETS=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
WEEK_PCT=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
WEEK_RESETS=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

RATE_LIMIT_TEXT=""
if [ -n "$FIVE_H_PCT" ]; then
  FIVE_H_INT=$(printf '%.0f' "$FIVE_H_PCT")
  FIVE_H_COLOR=$(rate_limit_color "$FIVE_H_INT")
  if [ -n "$FIVE_H_RESETS" ]; then
    FIVE_H_STR="${FIVE_H_COLOR}$(format_resets_in "$FIVE_H_RESETS" "$NOW")/5h ${FIVE_H_INT}%${RL_RESET}"
  else
    FIVE_H_STR="${FIVE_H_COLOR}5h ${FIVE_H_INT}%${RL_RESET}"
  fi
  RATE_LIMIT_TEXT="$FIVE_H_STR"
fi
if [ -n "$WEEK_PCT" ]; then
  WEEK_INT=$(printf '%.0f' "$WEEK_PCT")
  WEEK_COLOR=$(rate_limit_color "$WEEK_INT")
  if [ -n "$WEEK_RESETS" ]; then
    WEEK_STR="${WEEK_COLOR}$(format_resets_in "$WEEK_RESETS" "$NOW")/7d ${WEEK_INT}%${RL_RESET}"
  else
    WEEK_STR="${WEEK_COLOR}7d ${WEEK_INT}%${RL_RESET}"
  fi
  RATE_LIMIT_TEXT="${RATE_LIMIT_TEXT:+${RATE_LIMIT_TEXT}・}$WEEK_STR"
fi

# ステータスライン出力（1行目: モデル・コンテキスト・up/down・リミット・金額・時間／2行目: フォルダ・ブランチ）
LINE1="$MODEL | 📊 ${COLOR}${USED_TOKENS}/${CTX_SIZE} ${PCT}%${RESET} | ↑${TOTAL_INPUT_TOKEN} ↓${TOTAL_OUTPUT_TOKEN}"
[ -n "$RATE_LIMIT_TEXT" ] && LINE1="${LINE1} | ⏳ ${RATE_LIMIT_TEXT}"
LINE1="${LINE1} | 💰 ${COST} | ⏱️ ${DURATION}"
echo -e "$LINE1"

if [ -n "$BRANCH" ]; then
  echo -e "📁 ${DIR##*/}/ on $BRANCH"
else
  echo -e "📁 ${DIR##*/}/"
fi