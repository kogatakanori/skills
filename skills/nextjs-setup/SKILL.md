---
name: nextjs-setup
description: Next.js環境を設定するための包括的なツールキット。App Router優先でTypeScript、Material-UI、Zustand、Tailwind CSS、テスト環境の設定をサポート。新規プロジェクト作成、既存プロジェクトへのパッケージ追加、設定ファイルの最適化を含む。ユーザーが「Next.jsプロジェクトを作成」「Next.jsをセットアップ」「ReactアプリをNext.jsに変換」などと言った時に使用。
---

# Next.js環境セットアップ

## Overview

このスキルは、Next.jsプロジェクトの初期設定と環境構築を効率的に行うためのツールキットを提供します。App Router（Next.js 13+）を優先的にサポートし、TypeScript、Material-UI、Zustand、各種開発ツールの設定を含みます。

## クイックスタート

### 新規プロジェクトの作成

最も簡単な方法：
```bash
npx create-next-app@latest my-app --typescript --tailwind --app --eslint
cd my-app
```

またはスクリプトを使用：
```bash
bash scripts/init-nextjs-project.sh my-app
```

### 既存プロジェクトへの追加

既存プロジェクトにNext.js機能を追加する場合：

1. **Material-UIのセットアップ**：
   ```bash
   bash scripts/setup-material-ui.sh
   ```

2. **Zustand（状態管理）のセットアップ**：
   ```bash
   bash scripts/setup-zustand.sh
   ```

3. **テスト環境のセットアップ**：
   ```bash
   bash scripts/setup-testing.sh
   ```

## 主要な設定作業

### TypeScript設定

`assets/templates/tsconfig.template.json`をコピーして使用：
```bash
cp assets/templates/tsconfig.template.json tsconfig.json
```

主要な設定：
- strict モード有効
- パスエイリアス設定済み（`@/*`, `@components/*`, etc.）
- Next.js プラグイン設定済み

### ESLint & Prettier設定

コード品質ツールの設定：
```bash
# ESLint設定
cp assets/templates/.eslintrc.template.json .eslintrc.json

# Prettier設定
cp assets/templates/.prettierrc.template.json .prettierrc.json

# 必要なパッケージをインストール
npm install --save-dev eslint-config-prettier prettier prettier-plugin-organize-imports prettier-plugin-tailwindcss
```

### Material-UI統合

Material-UIテーマの設定：
```typescript
// app/providers.tsx を作成
'use client'

import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import theme from '@/styles/theme'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  )
}
```

テーマファイルをコピー：
```bash
mkdir -p src/styles
cp assets/templates/mui-theme.template.ts src/styles/theme.ts
```

ルートレイアウトで適用：
```typescript
// app/layout.tsx
import { Providers } from './providers'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

### Zustand状態管理

Zustandストアの作成：
```bash
mkdir -p src/store
cp assets/templates/zustand-store.template.ts src/store/useExampleStore.ts
```

使用例：
```typescript
'use client'

import { useExampleStore } from '@/store/useExampleStore'

export function Counter() {
  const count = useExampleStore((state) => state.count)
  const increment = useExampleStore((state) => state.increment)

  return (
    <button onClick={increment}>
      Count: {count}
    </button>
  )
}
```

### 環境変数の設定

`.env.local`ファイルを作成：
```bash
# Public環境変数（クライアントで使用可能）
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_APP_NAME=My Next.js App

# サーバー環境変数（サーバーのみ）
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET=your-secret-key
```

## プロジェクト構造

推奨される構造の詳細は `references/project-structure.md` を参照してください。

基本構造：
```
app/           # App Router
components/    # Reactコンポーネント
lib/           # ユーティリティ関数
store/         # Zustand状態管理
styles/        # スタイルファイル
types/         # TypeScript型定義
public/        # 静的ファイル
tests/         # テストファイル
```

## App Routerパターン

App Router固有の実装パターンは `references/app-router-patterns.md` を参照してください。

主要な概念：
- サーバーコンポーネント（デフォルト）
- クライアントコンポーネント（'use client'）
- サーバーアクション
- 並列ルート
- インターセプトルート

## 開発ワークフロー

### 開発サーバーの起動
```bash
npm run dev
# http://localhost:3000 で起動
```

### ビルドと本番モード
```bash
npm run build
npm run start
```

### 静的エクスポート
```javascript
// next.config.js
module.exports = {
  output: 'export',
}
```

### Vercelへのデプロイ
```bash
npm install -g vercel
vercel
```

## トラブルシューティング

### よくある問題と解決策

1. **"Module not found" エラー**
   - `tsconfig.json`のパスエイリアスを確認
   - `npm install`を再実行

2. **TypeScriptエラー**
   - `npm run type-check`でエラーを確認
   - `tsconfig.json`のstrict設定を確認

3. **スタイルが適用されない**
   - Tailwind CSSの設定を確認
   - `globals.css`のインポートを確認

4. **環境変数が読み込まれない**
   - `NEXT_PUBLIC_`プレフィックスを確認（クライアント用）
   - `.env.local`ファイルの配置を確認

## 高度な設定

### カスタムサーバー
```javascript
// server.js
const express = require('express')
const next = require('next')

const dev = process.env.NODE_ENV !== 'production'
const app = next({ dev })
const handle = app.getRequestHandler()

app.prepare().then(() => {
  const server = express()

  server.all('*', (req, res) => {
    return handle(req, res)
  })

  server.listen(3000)
})
```

### 国際化（i18n）
```javascript
// next.config.js
module.exports = {
  i18n: {
    locales: ['ja', 'en'],
    defaultLocale: 'ja',
  },
}
```

### PWA設定
```bash
npm install next-pwa
```

```javascript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
})

module.exports = withPWA({
  // 他の設定
})
```

## Resources

このスキルには以下のリソースが含まれています：

### scripts/
Next.jsプロジェクトのセットアップを自動化するスクリプト：
- `init-nextjs-project.sh` - 新規プロジェクトの作成
- `setup-material-ui.sh` - Material-UIのインストールと設定
- `setup-zustand.sh` - Zustand状態管理のインストール
- `setup-testing.sh` - Jest、React Testing Library、Cypressの設定

### references/
詳細なドキュメントとガイドライン：
- `app-router-patterns.md` - App Routerのパターンとベストプラクティス
- `project-structure.md` - 推奨プロジェクト構造とファイル命名規則

### assets/templates/
設定ファイルとコードテンプレート：
- `tsconfig.template.json` - TypeScript設定テンプレート
- `.eslintrc.template.json` - ESLint設定テンプレート
- `.prettierrc.template.json` - Prettier設定テンプレート
- `zustand-store.template.ts` - Zustandストアのテンプレート
- `mui-theme.template.ts` - Material-UIテーマのテンプレート
