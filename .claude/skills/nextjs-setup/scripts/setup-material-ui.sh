#!/bin/bash
set -e

# Material-UIのセットアップスクリプト

echo "🎨 Material-UIをインストール中..."

# Material-UI core packages
npm install @mui/material @emotion/react @emotion/styled

# Material-UI icons (オプション)
read -p "Material-UI Iconsをインストールしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install @mui/icons-material
fi

# Material-UI lab (experimental components)
read -p "Material-UI Lab (実験的コンポーネント)をインストールしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install @mui/lab
fi

# Material-UI x-data-grid
read -p "Material-UI DataGridをインストールしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install @mui/x-data-grid
fi

# Material-UI date pickers
read -p "Material-UI Date Pickersをインストールしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install @mui/x-date-pickers dayjs
fi

echo "✅ Material-UIのインストールが完了しました"
echo ""
echo "使用方法:"
echo "  import { Button } from '@mui/material';"
echo "  import { ThemeProvider } from '@mui/material/styles';"