---
name: tech-checking
description: Audits the project's tech stack by checking current vs latest versions (LTS/EOL status), investigating breaking changes and their impact on existing code, and analyzing dependency graph conflicts and cascading upgrade requirements. Use when selecting technologies, planning upgrades, or doing periodic maintenance checks.
user_invocable: true
---

# Tech Checking

プロジェクトの依存パッケージを対象に、バージョン状況・破壊的変更・依存関係の連鎖を並列調査し、アップグレード判断に必要な情報をまとめて出力する。

## Workflow

実行前にコピーしてください：

```
Progress:
- [ ] Step 1: 対象パッケージの確定
- [ ] Step 2a: version-analyst 起動・完了待ち
- [ ] Step 2b: breaking-change-analyst / dependency-graph-analyst 並列起動
- [ ] Step 3: 推奨度の決定
- [ ] Step 4: レポート出力
- [ ] Step 5: 次のアクション案内
```

### Step 1: 対象パッケージの確定

**引数がある場合**（例: `/tech-checking node typescript express`）:
指定されたパッケージのみを調査対象とする。

**引数がない場合**:
以下のファイルから全依存を読み取り調査対象とする：
- `package.json` の `dependencies` + `devDependencies`
- `pubspec.yaml` の `dependencies` + `dev_dependencies`
- `go.mod` の `require` セクション
- `.nvmrc` / `.tool-versions` のランタイム
- その他 lockファイル

対象が20件を超える場合（調査・出力コストが大きくなるため）は `AskUserQuestion` でフィルタリング方針をユーザーに確認する：
- 直接依存のみ（transitive依存を除く）
- 特定のカテゴリのみ（例: フレームワーク系のみ）
- バージョン差分が major のもののみ

### Step 2: 並列調査

#### Step 2a: version-analyst（先行起動）

`../../agents/version-analyst.md` を Read し、`[対象パッケージリスト]` を Step 1 の結果で置換して **Agent A を起動する**：

**Agent A（version-analyst）**: 現在バージョンの取得と最新バージョン・LTS/EOL状況のWeb調査

Agent A の完了後、結果から以下の形式でバージョン差分リストを生成する（Agent B・C への入力となる）：

```
- express: 現在 v4.18.2 → 最新 v5.0.1 (major)
- typescript: 現在 v5.3.3 → 最新 v6.0.0 (major)
- lodash: 現在 v4.17.21 → 最新 v4.17.21 (最新)
- node: 現在 v20.x → 最新 v22.x (major, EOL予定)
```

#### Step 2b: breaking-change-analyst / dependency-graph-analyst（同時起動）

`../../agents/breaking-change-analyst.md` と `../../agents/dependency-graph-analyst.md` を Read し、`[バージョン差分リスト]` を Step 2a で生成したリストで置換して **Agent B・C を同時に起動する**：

**Agent B（breaking-change-analyst）**: breaking changesの内容と既存コードへの影響箇所の特定

**Agent C（dependency-graph-analyst）**: peer dependency・transitive dependencyの制約分析と連鎖更新・アップグレードブロックの検出

### Step 3: 推奨度の決定

各パッケージについて以下の基準で推奨度を決定する：

| 推奨度 | 条件 |
|--------|------|
| `⚠️ 要対応` | EOL済み / EOL予定（12ヶ月以内）/ セキュリティ脆弱性あり |
| `📋 推奨` | major バージョン差分あり / breaking changesあり（影響度「高」） |
| `✅ 任意` | minor/patch 差分のみ / breaking changesの影響度が「低」以下 |
| `🔒 制約あり` | アップグレードが他パッケージの制約でブロックされている |

### Step 4: レポート出力

以下の形式でターミナルに出力する：

```
## Tech Stack Health Report
実行日: YYYY-MM-DD

### サマリー
| ⚠️ 要対応 | 📋 推奨 | ✅ 任意 | 🔒 制約あり |
|----------|---------|---------|------------|
| N件      | N件     | N件     | N件        |

---

### [パッケージ名] [推奨度アイコン]
現在: vX.Y.Z | 最新: vA.B.C | LTS状態: [状態]

**Breaking Changes**（現在→最新）
- [変更の概要]（影響: src/xxx.ts:L23）
- なし

**依存関係への影響**
- `foo@5` は `bar@3+` が必要 → 現在 `bar@2` と競合（→ bar も同時更新が必要）
- なし

**推奨アップグレード手順**
1. [手順1]
2. [手順2]

---
```

パッケージが多い場合は「要対応」→「推奨」→「任意」の順に記載し、同じ推奨度内はパッケージ名のアルファベット順にする。

### Step 5: 次のアクション案内

レポートの末尾に以下を追記する：

```
## 次のステップ

### 今すぐ対応が必要なもの（⚠️ 要対応）
- [パッケージ名]: [理由と推奨アクション]

### アップグレード順序（依存関係を考慮）
1. [パッケージ名] （理由: [依存関係の制約など]）
2. [パッケージ名]
...

アップグレードを開始する場合は、対象パッケージを指定して再度 `/tech-checking <package>` を実行するか、
Issue を起票して `/arc-specifying` でアップグレード作業を開始してください。
```

## Notes

- 調査対象が多い場合でも、各パッケージのエントリをサマリーに省略せずに出力する（Breaking Changesなしのものは1行で済ませてよい）
- バージョン情報が取得できないパッケージは「情報取得失敗」と明記してスキップする
- lockファイルと `package.json` の記載が異なる場合は lockファイルを優先する（実際にインストールされているバージョンを使う）
- Web調査の結果が古い可能性がある場合は注記する
