---
name: project-init
description: プロジェクトの初期設定を行うスキル。Claude Code用の.claude/settings.json（パーミッション・カスタムフック・ステータスライン・context7 MCP設定）、README.md（プロジェクト名と目次）、AGENT.md（エージェント向け指示）、CLAUDE.md（@AGENT.mdへのリンク）、.gitignoreを生成する。新規プロジェクトで「初期設定」「プロジェクトをセットアップ」「settings.jsonを作成」「CLAUDE.mdを作成」「.gitignoreを作りたい」などと言った場合に使用。既存ファイルはスキップし、不足している設定のみ提案する。
user_invocable: true
---

# Project Init

新規プロジェクトに必要なClaude Code設定ファイル・ドキュメントをまとめてセットアップするスキル。

## このスキルが作成するもの

| ファイル | 内容 |
|---------|------|
| `.claude/settings.json` | セキュリティdeny設定・PostToolUseフック・ステータスライン・context7プラグイン設定 |
| `.claude/statusline.sh` | セッション情報（モデル・コンテキスト・コスト・ブランチ）を表示するスクリプト |
| `README.md` | プロジェクト名・目次・docs/へのリンク |
| `AGENT.md` | エージェントへの指示（アーキテクチャ・開発ルールなど） |
| `CLAUDE.md` | `@AGENT.md` への参照のみ |
| `.gitignore` | 汎用的な除外設定 |

## 実行フロー

### Step 1: プロジェクト名を確認する

ユーザーがプロジェクト名を指定していない場合は、現在のディレクトリ名を候補として提示し確認を取る。

```bash
basename $(pwd)
```

### Step 2: 既存ファイルを確認する

以下のファイルが既に存在するか確認する：

```bash
ls -la .claude/settings.json README.md AGENT.md CLAUDE.md .gitignore 2>/dev/null
```

**存在するファイルは上書きしない。** 代わりに不足している設定を特定して提案する（Step 5参照）。

### Step 3: 新規ファイルを作成する

存在しないファイルについて、以下の順で作成する。

#### .claude/settings.json

テンプレート（`assets/templates/settings.json.template`）を使用して `.claude/settings.json` を作成する。

```bash
mkdir -p .claude
```

作成する内容：
- **respectGitignore**: true
- **language**: japanese
- **statusLine**: `type: "command"`, `command: ".claude/statusline.sh"`
- **enabledPlugins**: `context7@claude-plugins-official: true`（Claude公式プラグインとして有効化）
- **permissions.allow**: プロジェクト内のRead/Edit/Write（`/**`スコープ）・git読み取り系（log/show/diff/status/branch/remote/worktree list/ls-files）・gh読み取り系（repo view/issue list|view|status/pr list|view|status/run list|view/workflow list|view）
- **permissions.deny**: .env・SSH鍵・秘密鍵・credentials.json・sudo・rm -rf などのセキュリティ除外設定
- **hooks.PostToolUse**: Write/Edit ツール使用後に `.claude/hooks/post_write_lint.sh` を実行
- **env.CLAUDE_CODE_DISABLE_1M_CONTEXT**: `"1"`（1Mコンテキスト無効化）

#### README.md

テンプレート（`assets/templates/README.md.template`）を使用し、`{{PROJECT_NAME}}` をプロジェクト名に置換して作成する。

`docs/` ディレクトリも作成する：
```bash
mkdir -p docs
```

#### AGENT.md

テンプレート（`assets/templates/AGENT.md.template`）を使用し、`{{PROJECT_NAME}}` を置換して作成する。

エージェントへの指示ファイル。後からユーザーが編集してプロジェクト固有の情報を追加するための雛形。

#### CLAUDE.md

テンプレート（`assets/templates/CLAUDE.md.template`）をそのままコピーして作成する。

内容は `@AGENT.md` の1行のみ。Claude Codeがセッション開始時にAGENT.mdを自動読み込みするための設定。

#### .claude/statusline.sh

テンプレート（`assets/templates/statusline.sh.template`）をそのままコピーして `.claude/statusline.sh` として作成し、実行権限を付与する。

```bash
chmod +x .claude/statusline.sh
```

セッションのモデル・コンテキスト使用率・コスト・経過時間・ブランチ名を表示するステータスラインスクリプト。

#### .gitignore

テンプレート（`assets/templates/.gitignore.template`）をそのままコピーして作成する。

### Step 4: 作成結果を報告する

作成したファイルの一覧と、各ファイルへのユーザーが次に行うべきアクションを簡潔に伝える。

**報告フォーマット例：**
```
以下のファイルを作成しました：
- ✅ .claude/settings.json  — セキュリティdeny設定・PostToolUseフック・context7プラグイン設定済み
- ✅ .claude/statusline.sh  — セッション情報ステータスラインスクリプト作成済み
- ✅ README.md              — プロジェクト名とdocs/へのリンク追加済み
- ✅ AGENT.md               — 雛形作成済み。プロジェクト固有情報を追記してください
- ✅ CLAUDE.md              — @AGENT.md を参照するよう設定済み
- ✅ .gitignore             — 汎用設定適用済み
- ⏭ docs/                  — ディレクトリ作成済み

次のステップ：
1. AGENT.md にプロジェクトのアーキテクチャや開発ルールを追記
2. .claude/settings.json の permissions.allow にプロジェクト固有のコマンドを追加
```

### Step 5: 既存ファイルの不足設定を提案する（既存プロジェクトの場合）

既存ファイルが存在した場合、以下を確認して不足部分をユーザーに提案する。

#### settings.json のチェック項目

```bash
cat .claude/settings.json
```

確認する項目：
- `enabledPlugins["context7@claude-plugins-official"]` が設定されているか
- `permissions` ブロックが存在するか
- `hooks.PostToolUse` が設定されているか
- `statusLine` が設定されているか
- `.claude/statusline.sh` が存在し実行権限があるか

不足している場合は、追加すべきJSONスニペットを提示し、ユーザーが手動で追加できるよう案内する。上書きはしない。

#### .gitignore のチェック項目

テンプレートに含まれるパターンのうち、既存の `.gitignore` に存在しないものをリストアップして提案する。

## テンプレートファイルの場所

```
assets/templates/
├── settings.json.template  — .claude/settings.json の雛形
├── statusline.sh.template  — .claude/statusline.sh の雛形（実行権限付与が必要）
├── README.md.template      — README.md の雛形（{{PROJECT_NAME}} プレースホルダーあり）
├── AGENT.md.template       — AGENT.md の雛形（{{PROJECT_NAME}} プレースホルダーあり）
├── CLAUDE.md.template      — CLAUDE.md の雛形（@AGENT.md の1行のみ）
└── .gitignore.template     — .gitignore の雛形
```

テンプレートを読み込んでから内容を確認し、適切に `{{PROJECT_NAME}}` を置換して使用すること。
