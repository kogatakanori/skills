# App Router パターン & ベストプラクティス

## 目次
- [ディレクトリ構造](#ディレクトリ構造)
- [ルーティングパターン](#ルーティングパターン)
- [レイアウト](#レイアウト)
- [データフェッチング](#データフェッチング)
- [サーバーコンポーネント](#サーバーコンポーネント)
- [クライアントコンポーネント](#クライアントコンポーネント)
- [メタデータ](#メタデータ)
- [エラーハンドリング](#エラーハンドリング)

## ディレクトリ構造

```
app/
├── layout.tsx                 # ルートレイアウト
├── page.tsx                   # ホームページ
├── globals.css               # グローバルスタイル
├── (auth)/                   # ルートグループ（URLに影響なし）
│   ├── login/
│   │   └── page.tsx
│   └── register/
│       └── page.tsx
├── dashboard/
│   ├── layout.tsx            # ダッシュボードレイアウト
│   ├── page.tsx              # ダッシュボードページ
│   └── settings/
│       └── page.tsx
├── api/                      # APIルート
│   └── users/
│       └── route.ts
└── components/               # 共有コンポーネント
    ├── ui/
    └── features/
```

## ルーティングパターン

### 動的ルート
```typescript
// app/products/[id]/page.tsx
export default function Product({ params }: { params: { id: string } }) {
  return <div>Product ID: {params.id}</div>
}
```

### キャッチオールルート
```typescript
// app/blog/[...slug]/page.tsx
export default function BlogPost({ params }: { params: { slug: string[] } }) {
  // /blog/a/b/c → slug = ['a', 'b', 'c']
  return <div>Slug: {params.slug.join('/')}</div>
}
```

### 並列ルート
```typescript
// app/@modal/default.tsx と app/@sidebar/default.tsx
export default function Layout({
  children,
  modal,
  sidebar,
}: {
  children: React.ReactNode
  modal: React.ReactNode
  sidebar: React.ReactNode
}) {
  return (
    <>
      {children}
      {sidebar}
      {modal}
    </>
  )
}
```

## レイアウト

### ルートレイアウト
```typescript
// app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'My Next.js App',
  description: 'Built with App Router',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

### ネストされたレイアウト
```typescript
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="dashboard">
      <nav>Dashboard Navigation</nav>
      <main>{children}</main>
    </div>
  )
}
```

## データフェッチング

### サーバーコンポーネントでのフェッチ
```typescript
// app/posts/page.tsx
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    cache: 'no-store', // または 'force-cache', { next: { revalidate: 3600 } }
  })

  if (!res.ok) {
    throw new Error('Failed to fetch posts')
  }

  return res.json()
}

export default async function Posts() {
  const posts = await getPosts()

  return (
    <ul>
      {posts.map((post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

### 並列データフェッチング
```typescript
async function getUser(id: string) { /* ... */ }
async function getPosts(userId: string) { /* ... */ }

export default async function Profile({ params }: { params: { id: string } }) {
  // 並列実行
  const [user, posts] = await Promise.all([
    getUser(params.id),
    getPosts(params.id),
  ])

  return (
    <div>
      <h1>{user.name}</h1>
      <Posts posts={posts} />
    </div>
  )
}
```

## サーバーコンポーネント

### デフォルトの動作
```typescript
// このコンポーネントはサーバーで実行される
export default async function ServerComponent() {
  // 直接データベースアクセスも可能
  const data = await db.query('SELECT * FROM users')

  return <div>{/* ... */}</div>
}
```

### サーバーアクション
```typescript
// app/actions.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const title = formData.get('title')
  const content = formData.get('content')

  // データベースに保存
  await db.insert({ title, content })

  // キャッシュを再検証
  revalidatePath('/posts')
}
```

## クライアントコンポーネント

### 'use client'ディレクティブ
```typescript
// app/components/Counter.tsx
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  )
}
```

### サーバーとクライアントの組み合わせ
```typescript
// app/posts/[id]/page.tsx (サーバーコンポーネント)
import Comments from './Comments'

export default async function Post({ params }: { params: { id: string } }) {
  const post = await getPost(params.id)

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
      <Comments postId={params.id} /> {/* クライアントコンポーネント */}
    </article>
  )
}
```

## メタデータ

### 静的メタデータ
```typescript
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Us',
  description: 'Learn more about our company',
  openGraph: {
    title: 'About Us',
    description: 'Learn more about our company',
    images: ['/og-image.jpg'],
  },
}
```

### 動的メタデータ
```typescript
export async function generateMetadata(
  { params }: { params: { id: string } }
): Promise<Metadata> {
  const product = await getProduct(params.id)

  return {
    title: product.title,
    description: product.description,
    openGraph: {
      images: [product.image],
    },
  }
}
```

## エラーハンドリング

### error.tsx
```typescript
// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

### not-found.tsx
```typescript
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <p>Could not find requested resource</p>
      <Link href="/">Return Home</Link>
    </div>
  )
}
```

### loading.tsx
```typescript
// app/loading.tsx
export default function Loading() {
  return <div>Loading...</div>
}
```