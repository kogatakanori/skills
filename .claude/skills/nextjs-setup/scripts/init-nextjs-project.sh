#!/bin/bash
set -e

# Next.jsプロジェクトの初期化スクリプト

PROJECT_NAME="$1"
TYPESCRIPT="${2:-true}"
TAILWIND="${3:-true}"
APP_ROUTER="${4:-true}"
SRC_DIR="${5:-true}"
IMPORT_ALIAS="${6:-@/*}"

if [ -z "$PROJECT_NAME" ]; then
    echo "使用方法: ./init-nextjs-project.sh <プロジェクト名> [typescript] [tailwind] [app-router] [src-dir] [import-alias]"
    exit 1
fi

echo "📦 Next.jsプロジェクトを作成中: $PROJECT_NAME"

# create-next-appコマンドの構築
CMD="npx create-next-app@latest $PROJECT_NAME"

# TypeScript
if [ "$TYPESCRIPT" = "true" ]; then
    CMD="$CMD --typescript"
else
    CMD="$CMD --no-typescript"
fi

# Tailwind CSS
if [ "$TAILWIND" = "true" ]; then
    CMD="$CMD --tailwind"
else
    CMD="$CMD --no-tailwind"
fi

# App Router
if [ "$APP_ROUTER" = "true" ]; then
    CMD="$CMD --app"
else
    CMD="$CMD --no-app"
fi

# src directory
if [ "$SRC_DIR" = "true" ]; then
    CMD="$CMD --src-dir"
else
    CMD="$CMD --no-src-dir"
fi

# Import alias
CMD="$CMD --import-alias \"$IMPORT_ALIAS\""

# ESLint
CMD="$CMD --eslint"

# 実行
echo "実行中: $CMD"
eval "$CMD"

echo "✅ Next.jsプロジェクトが正常に作成されました: $PROJECT_NAME"
echo ""
echo "次のステップ:"
echo "  cd $PROJECT_NAME"
echo "  npm run dev"