# Arc

GitHub IssueからPRまでをAIが自律的に推進するSDLCワークフロープラグイン。

## 概要

Arcは6つのスキルで構成され（コアスキル4つ＋bug fix/調査系2つ）、仕様策定・技術調査・タスク計画・TDD実装を一貫して自動化します。ユーザーが関与するのは「specの承認」「調査結果の方向性確認」「カバレッジ確認（CRITICAL/HIGH指摘時のみ）」「PR pushの承認」の4点のみです（bug fix/調査系トラックも同様に最小限の人間ゲートで進みます）。

新機能開発は `/arc-specifying` から始まるspec/design/plan/implementの4フェーズフローを使います。バグ修正やコード理解・設計調査のようにGoal/Use Cases/Acceptance Criteriaを固める必要がないタスクには、spec/designを持たない軽量な `/arc-investigating` → `/arc-bugfixing` トラックを使います（詳細は後述）。

spec・plan・taskはGitHub Issueのコメントとして管理します。実装した機能のドキュメントのみ `docs/` ファイルとして保存します。PRに `Closes #NNN` を記載するため、マージ時にIssueは自動でクローズされます。

## ワークフロー全体図

```
GitHub Issue
      │
      ▼
/arc-specifying <N>
  ├─ spec-clarifier    Q&A
  └─ spec-reviewer     品質チェック
      │
      │ specコメント ──────────────────────→ Issue
      │ docs/ ──────────────────────────→ リポジトリ
      │
      │ ← Issueのspecコメントを確認・承認
      ▼
/arc-designing
  ├─ codebase-analyst       ┐
  ├─ architecture-analyst   │
  ├─ dependency-analyst     │ 並列調査
  ├─ performance-analyst    │
  └─ security-analyst       ┘
      │
      │ designコメント（<!-- arc:design -->）──→ Issue
      │
      │ ← 調査結果を確認し方向性を決定
      ▼
/arc-planning
  └─ implementation-analyst   詳細調査
      │
      │ tasksコメント ──────────────────→ Issue
      │
      │（自動移行・人間の介入なし）
      ▼
/arc-implementing
  ループ: 未完了タスクがある間
  ペアごとにサブエージェントで実装（[test]+[impl] = 1サブエージェント）
  ├─ [test] テストコードを書く（Red）
  └─ [impl] 実装する（Green）+ type-check/lint スクリプト実行
       │
       └─ docs/（ADRセクションにIssue番号）
  全ペア完了後 → tasksコメント一括更新 ────→ Issue
  └─ Step 4 レビューサブエージェント
       ├─ quality-reviewer        ┐
       ├─ architecture-linter     │ 常時
       ├─ spec-coverage-reviewer  ┘
       ├─ security-reviewer       ┐
       ├─ architecture-reviewer   │ 条件付き
       └─ cicd-reviewer           ┘
      │
      │ ← git push / PR作成の承認
      ▼
   PR作成（Closes #NNN → マージ時にIssue自動クローズ）
```

## bug fix / 調査系トラック（spec/designを持たない軽量フロー）

```
GitHub Issue（省略可）
      │
      ▼
/arc-investigating [<N>]
  Exploreエージェントで即調査（コードは変更しない）
      │
      │ 調査結果 ──→ <!-- arc:investigation --> としてIssueコメント（Issue番号ありの場合のみ）
      │
      │ ← 調査結果を確認。修正が必要か判断
      ▼
/arc-bugfixing <N>
  └─ implementation-analyst   詳細調査（<!-- arc:investigation --> またはIssue本文が入力）
      │
      │ tasksコメント（Goal→タスク対応表なし。カバレッジチェックもなし）──→ Issue
      │
      │（自動移行・人間の介入なし）
      ▼
/arc-implementing（既存を無改造で流用）
   ... 以降は通常フローと同じ
```

**既存4フェーズフローとの違い**:
- spec・designは作らない（Goal/Use Cases/Acceptance Criteria/ADRを固める必要がないため）
- `<!-- arc:investigation -->` コメントが無くても、自明なバグなら `/arc-bugfixing` から直接開始できる
- `/arc-investigating` はIssue番号なしでも使えるアドホックな調査ツール（コード変更やPRを一切伴わない）
- `arc-implementing` は無改造で流用するため、spec-coverage-reviewerの起動やPR本文のSummary抽出は空振りになるが許容している

## データの置き場所

| 種別 | 保存先 | 管理方法 |
|------|--------|---------|
| Spec（Why・ADR） | GitHub Issue コメント | `<!-- arc:spec -->` で識別 |
| 実現性調査結果 | GitHub Issue コメント | `<!-- arc:design -->` で識別 |
| Taskリスト | GitHub Issue コメント | `<!-- arc:tasks -->` で識別 |
| ドキュメント（What） | `docs/*.md` | 常に最新版を上書き保存 |

## スキル一覧

### `/arc-specifying <N>`

GitHub Issue番号を受け取り、featureブランチを作成してspecをIssueコメントに投稿し、docsを生成する。

- `gh issue view <N>` でIssueを取得
- **spec-clarifier** でWhy/Who/What/Use Cases/Constraints/Domain ModelのQ&Aを実施
- **spec-reviewer** でSpec品質チェック（CRITICAL/HIGH/MEDIUM）
- specを `<!-- arc:spec -->` 識別子付きでIssueコメントとして投稿
- `docs/<feature-name>.md` を生成（何を・どう使うか）
- 完了後、specコメントの確認を促して `/arc-designing` へ案内

### `/arc-designing`

Issueのspecコメントを読み取り技術的実現性を調査し、調査結果をIssueコメントに投稿する。

- IssueコメントからspecをAPIで取得
- **design-clarifier**（Phase 1）で踏襲型/変革型を判断して調査戦略を決定
- **codebase-analyst** を常時起動。**architecture-analyst**・**dependency-analyst** は変革型なら常時起動、踏襲型ならSpecのキーワードに応じて条件付き起動。**performance-analyst**・**security-analyst** はSpecのキーワードに応じて条件付き起動（最大5並列）
- 踏襲型かつキーワード非該当の場合はcodebase-analystのみが起動する軽量パスとなり、調査コストを抑えられる
- **design-clarifier**（Phase 2）でHOW判断Q&Aを実施
- 実現性を3段階で判定：
  - `実現可能` — 制約なし、そのまま進める
  - `条件付き` — 特定の対応が必要だが実現できる
  - `実現困難` — 根本的な問題あり、代替案を2案以上提示してHOW（アプローチ）の変更を促す（SpecのGoal/Constraintsは変更しない）
- **design-reviewer** でDesign品質チェック（Spec要件カバレッジ・トレーサビリティ・Constraintガードレール）を実施
- 調査結果を `<!-- arc:design -->` 識別子付きでIssueコメントとして投稿
- 完了後、方向性の確認を促して `/arc-planning` へ案内

### `/arc-planning`

specをTDDタスクリストに分解し、品質確認後にIssueコメントとして投稿し、自動で実装フェーズへ移行する。

- **implementation-analyst** で実装対象コードを詳細調査
- `[test]` → `[impl]` のペアでタスクを分解
- 以下の観点で自律レビューFBループ（最大3回）：
  1. TDD対応（全`[impl]`に対応する`[test]`があるか）
  2. 粒度の適切さ（1〜2時間程度のサイズか）
  3. 依存関係の順序
  4. Goalのカバレッジ
  5. 非機能タスクの有無
- タスクリストを `<!-- arc:tasks -->` 識別子付きでIssueコメントとして投稿
- **人間の介入なしに `Agent` ツールで sub-agent を spawn し、`arc-implementing` を新しいコンテキストで実行**

### `/arc-investigating [<N>]`

コードベース・設計に関する質問に即座に調査して回答する。**コードは変更しない。**

- Issue番号は任意。指定なしならアドホックな対話として完結し、指定ありなら調査結果を `<!-- arc:investigation -->` 識別子付きでIssueコメントに投稿する
- 明確化のためのQ&Aは挟まず、質問をそのまま `Explore` エージェントに渡して調査する（専用の投資対象エージェントファイルは作らない）
- bugの調査の場合は再現条件・影響範囲・修正方針の候補も報告する
- 修正が必要と分かった場合は `/arc-bugfixing <N>` へ引き継ぐよう案内する

### `/arc-bugfixing <N>`

bug修正をTDDタスクリストに分解し、自動で実装フェーズへ移行する。`arc-planning`のbug fix版で、**spec・designは作らない。**

- `<!-- arc:investigation -->` コメント（なければIssue本文）を入力に **implementation-analyst** で実装対象コードを詳細調査
- `[test]` → `[impl]` のペアでタスクを分解（Goal→タスク対応表は使わない）
- 以下の観点で自律レビューFBループ（最大3回）：
  1. TDD対応（全`[impl]`に対応する`[test]`があるか）
  2. 粒度の適切さ（1〜2時間程度のサイズか）
  3. 依存関係の順序
  - **Goal/ACカバレッジチェックは行わない**（specが存在しないため）
- タスクリストを `<!-- arc:tasks -->` 識別子付きでIssueコメントとして投稿
- **人間の介入なしに `Agent` ツールで sub-agent を spawn し、`arc-implementing` を新しいコンテキストで実行**（既存を無改造で流用するため、spec-coverage-reviewerの起動などは空振りになるが許容する）

### `/arc-implementing`

TDDで全タスクを自律実装し、最終横断レビュー後にPRを作成する。

- IssueコメントからtasksとspecをAPIで取得（spec+designはサブエージェントプロンプトに埋め込む）
- `[test]`+`[impl]` ペアごとにサブエージェントを起動（各サブエージェントは実装 + type-check/lint スクリプトのみ実行）
- 全ペア完了後にtasksコメントを一括PATCH更新（`- [ ]` → `- [x]`）
- 全タスク完了後にStep 4レビューサブエージェントを起動：

| エージェント | 起動条件 | レビュー観点 |
|---|---|---|
| quality-reviewer | 常時 | コード品質・可読性 |
| architecture-linter | 常時 | TDD遵守・レイヤー境界・ADRルール |
| spec-coverage-reviewer | 常時 | Goal/AC/Constraintsのテストカバレッジ |
| security-reviewer | 条件付き | 脆弱性・インジェクション・認証 |
| architecture-reviewer | 条件付き | ADRとの整合性・設計パターン |
| cicd-reviewer | 条件付き | CI/CD設定・デプロイ・インフラ |

- `docs/` ファイルの `## ADR` セクションにIssue番号を記載
- PRボディに `Closes #NNN` と `## Spec / ADR` セクションを記載してIssueを参照

## ディレクトリ構成（利用プロジェクト側）

```
<your-project>/
└── docs/                    # 機能ドキュメント（最新仕様）
    └── <feature-name>.md
```

spec・plan・taskはGitHub Issueのコメントで管理するため、リポジトリに `specs/` や `plans/` ディレクトリは作成されない。

## エージェント一覧

| ファイル | 役割 | 利用スキル |
|---|---|---|
| spec-clarifier | Why/Who/What/Use Cases/Constraints/Domain ModelのQ&A生成 | arc-specifying |
| spec-reviewer | Spec完全性・AC・UC↔Goal整合・Constraints・内部整合性をレビュー | arc-specifying |
| design-clarifier | Phase 1: 踏襲型/変革型判断。Phase 2: HOW判断Q&A | arc-designing |
| design-reviewer | Spec要件カバレッジ・トレーサビリティ・Constraintガードレールをレビュー | arc-designing |
| codebase-analyst | 踏襲型: パターン・再利用コンポーネント調査。変革型: 変更対象・影響範囲を特定 | arc-designing |
| architecture-analyst | アーキテクチャ制約・テスト基盤を調査（変革型は常時／踏襲型は条件付き） | arc-designing |
| dependency-analyst | ライブラリ・外部APIの存在・バージョン適合性・破壊的変更リスクを確認（変革型は常時／踏襲型は条件付き） | arc-designing |
| performance-analyst | パフォーマンス設計制約（クエリ・キャッシュ・同時実行）を調査 | arc-designing |
| security-analyst | セキュリティ設計制約（認証・認可・データ機密性）を特定 | arc-designing |
| implementation-analyst | 実装対象コードの詳細調査 | arc-planning, arc-bugfixing |
| quality-reviewer | コード品質レビュー（命名・責務・重複・複雑度） | arc-implementing |
| architecture-linter | TDD遵守・レイヤー境界・ADRルールの静的チェック | arc-implementing |
| spec-coverage-reviewer | Goal/AC/Constraintsのテストカバレッジ検証 | arc-implementing |
| security-reviewer | セキュリティレビュー（条件付き） | arc-implementing |
| architecture-reviewer | アーキテクチャレビュー（条件付き） | arc-implementing |
| cicd-reviewer | CI/CDレビュー（条件付き） | arc-implementing |

`arc-investigating` は上記の専用エージェントファイルを持たず、`Explore` エージェントを直接起動する（軽量さ優先のため）。

## セットアップ（推奨）

### パーミッション設定

#### プロジェクト設定（`.claude/settings.json`）

arcをプロジェクトで使用する際、`Write`・`Edit` ツールのパーミッションプロンプトを省略するため、プロジェクトの `.claude/settings.json` に以下の設定を追加することを推奨します。

```json
{
  "permissions": {
    "allow": [
      "Write(/**)",
      "Edit(/**)"
    ]
  }
}
```

- プロジェクトの `.claude/settings.json` に記載した `/` 始まりのパスはプロジェクトルート以下に自動スコープされます（Claude Code の仕様）。そのため `/**` と書いてもプロジェクト外のファイルには影響しません
- `deny` ルールが存在する場合はそちらが優先されます（`.env` や `~/.ssh` 等の保護は維持されます）
- `.claude/settings.json` が存在しない場合は新規作成してください

#### グローバル設定（`~/.claude/settings.json`）

arcはテンプレートファイル（`templates/`）やエージェント定義（`agents/`）をプラグインディレクトリから読み込みます。このディレクトリはプロジェクト外のため、**グローバル設定**（`~/.claude/settings.json`）へのReadパーミッション追加が必要です（プロジェクト設定では許可できません）。

`/arc-specifying` の初回実行時に自動セットアップされます。手動で設定する場合：

```json
// ~/.claude/settings.json
{
  "permissions": {
    "allow": [
      "Read(~/path/to/your/skills/plugins/arc/**)"
    ]
  }
}
```

- `~/` プレフィックスを使うことで移植性が高く（ホームディレクトリ基準）、マシン間で共有しやすい
- `/**` で `templates/`・`agents/` 以下すべてのファイルをカバー
- `~/path/to/your/skills/plugins/arc` の `path/to/your/skills/plugins/arc` 部分を、ホームディレクトリからの実際の相対パスに置き換えてください（例: `~/ghq/github.com/yourname/skills/plugins/arc`）
- `~/.claude/settings.json` が存在しない場合は新規作成してください

## 使い方

```bash
# 1. IssueからSpec（Issueコメント）・Docs（docs/）を生成
/arc-specifying 42

# → Issueのspecコメントを確認して承認

# 2. 技術的実現性を調査（結果もIssueコメントに投稿）
/arc-designing

# → 調査結果を確認し方向性を決定

# 3. タスク分解（Issueコメントに投稿）→ 自動的に実装・PR作成まで実行
/arc-planning

# → git push / PR作成の確認のみ
# PRマージ時にIssueは自動クローズ（Closes #NNN）
```

### bug fix / 調査系タスク（spec/designなしの軽量トラック）

```bash
# 1. 調査（Issue番号は任意。コードは変更しない）
/arc-investigating 42

# → 調査結果（<!-- arc:investigation -->）を確認

# 2. bug修正をTDDタスクに分解 → 自動的に実装・PR作成まで実行
/arc-bugfixing 42

# → git push / PR作成の確認のみ
```

自明なバグは調査結果コメントがなくても `/arc-bugfixing <N>` から直接開始できる（Issue本文から詳細調査する）。
