# Arc

GitHub IssueからPRまでをAIが自律的に推進するSDLCワークフロープラグイン。

## 概要

Arcは4つのスキルで構成され、仕様策定・技術調査・タスク計画・TDD実装を一貫して自動化します。ユーザーが関与するのは「specの承認」「調査結果の確認」「PR pushの承認」の3点のみです。

spec・plan・taskはGitHub Issueのコメントとして管理します。実装した機能のドキュメントのみ `docs/` ファイルとして保存します。PRに `Closes #NNN` を記載するため、マージ時にIssueは自動でクローズされます。

## ワークフロー全体図

```
GitHub Issue
      │
      ▼
/arc-specifying <N>
  ├─ codebase-analyst       ┐
  └─ architecture-analyst   ┘ 並列調査
      │
      │ specコメント ──────────────────────→ Issue
      │ docs/ ──────────────────────────→ リポジトリ
      │
      │ ← Issueのspecコメントを確認・承認
      ▼
/arc-designing
  ├─ dependency-analyst     ┐
  └─ conflict-analyst       ┘ 並列調査
      │
      │ investigationコメント ───────────→ Issue
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
  ├─ [test] テストコードを書く（Red）
  └─ [impl] 実装する（Green）
       ├─ security-reviewer       ┐
       ├─ architecture-reviewer   │
       ├─ quality-reviewer        ┘ 並列レビュー
       └─ cicd-reviewer
       │
       └─ tasksコメント更新 ───────────→ Issue
       └─ docs/（ADRセクションにIssue番号）
      │
      │ ← git push / PR作成の承認
      ▼
   PR作成（Closes #NNN → マージ時にIssue自動クローズ）

# PRマージ後（任意のタイミングで実行）
/arc-cleaning
  └─ マージ済みworktreeを検出して削除
```

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
- **codebase-analyst** と **architecture-analyst** を並列起動してコードベースを調査
- specを `<!-- arc:spec -->` 識別子付きでIssueコメントとして投稿
- `docs/<feature-name>.md` を生成（何を・どう使うか）
- 完了後、specコメントの確認を促して `/arc-designing` へ案内

### `/arc-designing`

Issueのspecコメントを読み取り技術的実現性を調査し、調査結果をIssueコメントに投稿する。

- IssueコメントからspecをAPIで取得
- **dependency-analyst** と **conflict-analyst** を並列起動
- 実現性を3段階で判定：
  - `実現可能` — 制約なし、そのまま進める
  - `条件付き` — 特定の対応が必要だが実現できる
  - `実現困難` — 根本的な問題あり、代替案を提示してspecコメントの修正を促す
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

### `/arc-cleaning`

ローカルの `.claude/worktrees/issue-*` を一覧表示し、対応するPRがマージ済みのworktreeを削除する。

- `git worktree list` でローカルのworktreeを取得
- 各worktreeのブランチに対応するPRのマージ状態を `gh pr list` で確認
- マージ済みのworktreeを確認後に `git worktree remove` と `git branch -d` で削除
- 未マージのworktreeはそのまま保持

### `/arc-implementing`

TDDで全タスクを自律実装し、専門レビューFBループ後にPRを作成する。

- IssueコメントからtasksとspecをAPIで取得
- タスク完了のたびにtasksコメントをPATCH更新（`- [ ]` → `- [x]`）
- 各 `[impl]` タスクの実装後に4種の専門レビューエージェントを並列起動：

| エージェント | レビュー観点 |
|---|---|
| security-reviewer | 脆弱性・インジェクション・認証 |
| architecture-reviewer | ADRとの整合性・設計パターン |
| quality-reviewer | コード品質・可読性・テストカバレッジ |
| cicd-reviewer | CI/CD設定・デプロイ・インフラ |

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
| codebase-analyst | 類似機能・踏襲すべきパターンを調査 | arc-specifying |
| architecture-analyst | アーキテクチャ制約・テスト基盤を調査 | arc-specifying |
| dependency-analyst | ライブラリ・外部APIの存在・バージョン適合性を確認 | arc-designing |
| conflict-analyst | 既存コードとの競合・破壊的変更を調査 | arc-designing |
| implementation-analyst | 実装対象コードの詳細調査 | arc-planning |
| security-reviewer | セキュリティレビュー | arc-implementing |
| architecture-reviewer | アーキテクチャレビュー | arc-implementing |
| quality-reviewer | コード品質レビュー | arc-implementing |
| cicd-reviewer | CI/CDレビュー | arc-implementing |

## セットアップ（推奨）

### Worktree設定

`/arc-specifying` 実行時に `EnterWorktree` でworktreeが作成されます。初回実行時に hooks が自動セットアップされますが、カスタマイズする場合は以下を参考にしてください。

**`.worktreeinclude`**（プロジェクトルートに配置）

worktree作成時にコピーするファイルを列挙する。ただし `WorktreeCreate` hookを定義した場合はhookが `.worktreeinclude` の処理を担当する（後述）：

```
.env
.env.local
```

以下のスクリプトはarcプラグインの `templates/hooks/` に収録されており、`/arc-specifying` の初回実行時にプロジェクトの `.claude/hooks/` へ自動コピーされます。カスタマイズする場合は以下を参考にしてください。

**`.claude/hooks/worktree-create.sh`**

```bash
#!/usr/bin/env bash
# WorktreeCreate hook: worktreeを作成して初期セットアップを行う
INPUT=$(cat)
NAME=$(echo "$INPUT"      | jq -r '.worktree_name')
CWD=$(echo "$INPUT"       | jq -r '.cwd')
BASE_PATH=$(echo "$INPUT" | jq -r '.base_path')

WORKTREE_PATH="${BASE_PATH}/${NAME}"

# worktreeを作成（ブランチが存在しない場合は新規作成）
git -C "$CWD" worktree add "$WORKTREE_PATH" -b "$NAME" 2>/dev/null \
  || git -C "$CWD" worktree add "$WORKTREE_PATH" "$NAME" 2>/dev/null

# .worktreeinclude のファイルをコピー
# （WorktreeCreate hookを定義するとデフォルトのコピー処理が無効になるため自前で行う）
if [ -f "$CWD/.worktreeinclude" ]; then
  while IFS= read -r file || [ -n "$file" ]; do
    [[ "$file" =~ ^# || -z "$file" ]] && continue
    if [ -f "$CWD/$file" ]; then
      mkdir -p "$WORKTREE_PATH/$(dirname "$file")"
      cp "$CWD/$file" "$WORKTREE_PATH/$file"
    fi
  done < "$CWD/.worktreeinclude"
fi

# 依存関係のインストール（必要に応じてコメントアウトを外す）
# npm --prefix "$WORKTREE_PATH" install >&2
# bundle install --gemfile "$WORKTREE_PATH/Gemfile" >&2
# pip install -r "$WORKTREE_PATH/requirements.txt" >&2

echo "$WORKTREE_PATH"
```

**`.claude/hooks/worktree-remove.sh`**

```bash
#!/usr/bin/env bash
# WorktreeRemove hook: worktreeとブランチを削除する
INPUT=$(cat)
WORKTREE_PATH=$(echo "$INPUT" | jq -r '.worktree_path')
CWD=$(echo "$INPUT"          | jq -r '.cwd')

NAME=$(basename "$WORKTREE_PATH")

git -C "$CWD" worktree remove "$WORKTREE_PATH" --force 2>/dev/null || true
git -C "$CWD" branch -d "$NAME" 2>/dev/null || true
```

**`.claude/settings.json`**（hookの登録）

```json
{
  "hooks": {
    "WorktreeCreate": [{
      "type": "command",
      "command": "bash .claude/hooks/worktree-create.sh"
    }],
    "WorktreeRemove": [{
      "type": "command",
      "command": "bash .claude/hooks/worktree-remove.sh"
    }]
  }
}
```

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
