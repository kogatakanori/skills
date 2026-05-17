#!/usr/bin/env bash
# WorktreeRemove hook: worktreeとブランチを削除する
INPUT=$(cat)
WORKTREE_PATH=$(echo "$INPUT" | jq -r '.worktree_path')
CWD=$(echo "$INPUT"          | jq -r '.cwd')

NAME=$(basename "$WORKTREE_PATH")

git -C "$CWD" worktree remove "$WORKTREE_PATH" --force 2>/dev/null || true
git -C "$CWD" branch -d "$NAME" 2>/dev/null || true
