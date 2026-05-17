#!/usr/bin/env bash
# WorktreeCreate hook: worktreeを作成して初期セットアップを行う
INPUT=$(cat)
NAME=$(echo "$INPUT"      | jq -r '.worktree_name')
CWD=$(echo "$INPUT"       | jq -r '.cwd')
BASE_PATH=$(echo "$INPUT" | jq -r '.base_path')

WORKTREE_PATH="${BASE_PATH}/${NAME}"

# worktreeを作成（ブランチが存在しない場合は新規作成）
git -C "$CWD" worktree add "$WORKTREE_PATH" -b "$NAME" 2>/dev/null \
  || git -C "$CWD" worktree add "$WORKTREE_PATH" "$NAME" 2>/dev/null

# .worktreeinclude のファイルをコピー
# （WorktreeCreate hookを定義するとデフォルトのコピー処理が無効になるため自前で行う）
if [ -f "$CWD/.worktreeinclude" ]; then
  while IFS= read -r file || [ -n "$file" ]; do
    [[ "$file" =~ ^# || -z "$file" ]] && continue
    if [ -f "$CWD/$file" ]; then
      mkdir -p "$WORKTREE_PATH/$(dirname "$file")"
      cp "$CWD/$file" "$WORKTREE_PATH/$file"
    fi
  done < "$CWD/.worktreeinclude"
fi

# 依存関係のインストール（必要に応じてコメントアウトを外す）
# npm --prefix "$WORKTREE_PATH" install >&2
# bundle install --gemfile "$WORKTREE_PATH/Gemfile" >&2
# pip install -r "$WORKTREE_PATH/requirements.txt" >&2

echo "$WORKTREE_PATH"
