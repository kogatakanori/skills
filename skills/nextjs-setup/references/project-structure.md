# Next.js プロジェクト構造ガイドライン

## 推奨ディレクトリ構造

```
my-nextjs-app/
├── app/                      # App Router
│   ├── layout.tsx           # ルートレイアウト
│   ├── page.tsx            # ホームページ
│   ├── globals.css         # グローバルスタイル
│   ├── (auth)/             # ルートグループ
│   ├── api/                # APIルート
│   └── [feature]/          # 機能別ページ
├── components/              # React コンポーネント
│   ├── ui/                 # UIコンポーネント
│   │   ├── Button/
│   │   ├── Card/
│   │   └── Modal/
│   ├── features/           # 機能別コンポーネント
│   │   ├── auth/
│   │   └── dashboard/
│   └── layouts/            # レイアウトコンポーネント
├── lib/                     # ユーティリティ関数
│   ├── api/               # API関連
│   ├── hooks/             # カスタムフック
│   ├── utils/             # ユーティリティ
│   └── constants/         # 定数
├── store/                   # 状態管理（Zustand）
│   ├── useAuthStore.ts
│   └── useUIStore.ts
├── styles/                  # スタイルファイル
│   ├── themes/            # MUIテーマ
│   └── components/        # コンポーネントスタイル
├── types/                   # TypeScript型定義
│   ├── api.ts
│   └── models.ts
├── public/                  # 静的ファイル
│   ├── images/
│   └── fonts/
├── tests/                   # テストファイル
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.local              # 環境変数
├── .env.example            # 環境変数の例
├── next.config.js          # Next.js設定
├── tsconfig.json           # TypeScript設定
├── tailwind.config.js      # Tailwind CSS設定
├── jest.config.js          # Jest設定
└── package.json            # 依存関係
```

## コンポーネント構造

### UIコンポーネントの構造
```
components/ui/Button/
├── Button.tsx              # メインコンポーネント
├── Button.types.ts         # 型定義
├── Button.styles.ts        # スタイル
├── Button.test.tsx         # テスト
├── Button.stories.tsx      # Storybook
└── index.ts               # エクスポート
```

### 機能コンポーネントの構造
```
components/features/auth/
├── LoginForm/
│   ├── LoginForm.tsx
│   ├── LoginForm.types.ts
│   └── index.ts
├── RegisterForm/
│   ├── RegisterForm.tsx
│   └── index.ts
└── hooks/
    └── useAuth.ts
```

## ファイル命名規則

### コンポーネント
- PascalCase: `UserProfile.tsx`
- ディレクトリも同じ: `UserProfile/UserProfile.tsx`

### フック
- camelCase with "use" prefix: `useAuth.ts`

### ユーティリティ
- camelCase: `formatDate.ts`

### 型定義
- PascalCase for types/interfaces: `User.ts`
- camelCase for files: `userTypes.ts`

### APIルート
- kebab-case: `api/user-profile/route.ts`

## インポート構造

### パスエイリアスの設定
```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@lib/*": ["./src/lib/*"],
      "@store/*": ["./src/store/*"],
      "@types/*": ["./src/types/*"],
      "@styles/*": ["./src/styles/*"]
    }
  }
}
```

### インポート順序
```typescript
// 1. React/Next.js
import { useState } from 'react'
import { useRouter } from 'next/navigation'

// 2. 外部ライブラリ
import { Button } from '@mui/material'
import { format } from 'date-fns'

// 3. 内部モジュール（絶対パス）
import { useAuth } from '@lib/hooks/useAuth'
import { UserCard } from '@components/ui/UserCard'

// 4. 内部モジュール（相対パス）
import { formatUserName } from './utils'
import styles from './UserProfile.module.css'

// 5. 型定義
import type { User } from '@types/models'
```

## 環境変数の管理

### .env.localの構造
```bash
# Public環境変数（クライアントで使用可能）
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_APP_NAME=My Next.js App
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# サーバー環境変数（サーバーのみ）
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET=your-secret-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

### 環境変数の型定義
```typescript
// types/env.d.ts
declare namespace NodeJS {
  interface ProcessEnv {
    DATABASE_URL: string
    JWT_SECRET: string
    NEXT_PUBLIC_API_URL: string
    NEXT_PUBLIC_APP_NAME: string
  }
}
```

## ベストプラクティス

### 1. コロケーション
関連するファイルは近くに配置する
```
app/dashboard/
├── page.tsx
├── layout.tsx
├── loading.tsx
├── error.tsx
└── components/        # ページ固有のコンポーネント
    └── DashboardChart.tsx
```

### 2. バレルエクスポート
```typescript
// components/ui/index.ts
export { Button } from './Button'
export { Card } from './Card'
export { Modal } from './Modal'
```

### 3. 型の共有
```typescript
// types/models.ts
export interface User {
  id: string
  name: string
  email: string
}

// コンポーネントで使用
import type { User } from '@types/models'
```

### 4. カスタムフック
```typescript
// lib/hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}
```