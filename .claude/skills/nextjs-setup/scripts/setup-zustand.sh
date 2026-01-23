#!/bin/bash
set -e

# Zustandのセットアップスクリプト

echo "🐻 Zustandをインストール中..."

# Zustand本体のインストール
npm install zustand

# Zustand devtoolsのインストール（開発用）
read -p "Zustand DevToolsをインストールしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install --save-dev @redux-devtools/extension
fi

# immerの統合（不変性を保つため）
read -p "immerを統合しますか？（不変性管理用） (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install immer
fi

echo "✅ Zustandのインストールが完了しました"
echo ""
echo "使用例:"
echo "  import { create } from 'zustand';"
echo "  const useStore = create((set) => ({ ... }));"