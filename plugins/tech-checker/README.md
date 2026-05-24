# Tech Checker

プロジェクトの依存パッケージを自律調査し、バージョン状況・破壊的変更・依存関係の連鎖をまとめてレポートするプラグイン。

## 概要

パッケージのアップグレードを安全に判断するために必要な3つの観点を並列調査します：

1. **バージョン状況**: 現在バージョン vs 最新バージョン・LTS/EOL状態
2. **破壊的変更**: breaking changesの内容と既存コードへの影響箇所
3. **依存関係の連鎖**: peer dependency制約・transitive依存・アップグレードブロックの検出

## 使い方

```bash
# プロジェクト全体を調査
/tech-checking

# 特定パッケージのみ調査
/tech-checking node typescript

# フレームワーク系のみなど、実行後に絞り込みも可能
/tech-checking
```

## 出力例

```
## Tech Stack Health Report
実行日: 2026-05-24

### サマリー
| ⚠️ 要対応 | 📋 推奨 | ✅ 任意 | 🔒 制約あり |
|----------|---------|---------|------------|
| 1件      | 2件     | 3件     | 1件        |

---

### Node.js ⚠️ 要対応
現在: v20.x | 最新: v22.x | LTS状態: メンテナンスフェーズ（2026-04 EOL予定）

**Breaking Changes**: なし

**依存関係への影響**: なし

**推奨アップグレード手順**
1. .nvmrc を `22` に更新
2. CI/CDのNode.jsバージョン指定を更新

---

### TypeScript 📋 推奨
現在: v5.3 | 最新: v6.0 | LTS状態: 安定版

**Breaking Changes**
- `moduleResolution: bundler` がデフォルト化（影響: tsconfig.json）
- strict型推論の強化（影響: src/types/user.ts:L12, src/api/client.ts:L45）

**依存関係への影響**
- `ts-jest@29` は TypeScript@6 未対応 → `ts-jest@30` への同時更新が必要

**推奨アップグレード手順**
1. `ts-jest@30` を先にアップグレード
2. `typescript@6` をアップグレード
3. tsconfig.json の moduleResolution を明示的に設定
```

## エージェント構成

| ファイル | 役割 |
|---|---|
| version-analyst | 現在バージョン取得・最新版/LTS/EOL調査 |
| breaking-change-analyst | breaking changes調査・既存コードへの影響箇所特定 |
| dependency-graph-analyst | peer deps・transitive deps・競合・連鎖更新の分析 |

## ワークフロー

```
/tech-checking [packages]
      │
      ▼
  Step 1: 対象パッケージの確定
      │
      ▼
  Step 2a: version-analyst（現在/最新バージョン取得）
      │
      ▼（バージョン差分を渡して並列起動）
      ├─ breaking-change-analyst（breaking changes + 影響箇所）
      └─ dependency-graph-analyst（依存関係の連鎖・競合）
      │
      ▼
  Step 3-5: 推奨度決定 → レポート出力 → 次のアクション案内
```

## arcとの連携

`/tech-checking` で「要対応」と判定されたパッケージは、arcワークフローでアップグレード作業を進めることができます：

```bash
# アップグレード作業をIssue化して管理
gh issue create --title "chore: upgrade TypeScript to v6"
/arc-specifying <issue番号>
```
