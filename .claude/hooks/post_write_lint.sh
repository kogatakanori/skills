#!/usr/bin/env bash
# PostToolUse hook - Write/Edit後にlintを実行
# matcher: "Write|Edit" で呼び出し元を限定済みのため TOOL_NAME チェック不要

set -euo pipefail
trap 'echo "[lint hook] unexpected error (line $LINENO)" >&2; exit 2' ERR

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

echo "[lint hook] $FILE_PATH" >&2

LINT_FAILED=0

case "$FILE_PATH" in
    *.py)
        if command -v ruff &>/dev/null; then
            ruff check "$FILE_PATH" >&2 || LINT_FAILED=1
        elif command -v flake8 &>/dev/null; then
            flake8 "$FILE_PATH" >&2 || LINT_FAILED=1
        fi
        ;;
    *.js|*.ts|*.jsx|*.tsx)
        if command -v eslint &>/dev/null; then
            eslint "$FILE_PATH" >&2 || LINT_FAILED=1
        fi
        ;;
    *.sh)
        if command -v shellcheck &>/dev/null; then
            shellcheck "$FILE_PATH" >&2 || LINT_FAILED=1
        fi
        ;;
esac

if [ "$LINT_FAILED" -eq 1 ]; then
    exit 2
fi
