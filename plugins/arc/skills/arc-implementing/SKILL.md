---
name: arc-implementing
description: Autonomously implements all tasks in the Issue's tasks comment using TDD (Red-Green cycle), with parallel specialist review agents per task, updates the tasks comment as tasks complete, then automatically creates a PR. Runs without human intervention from task implementation to PR creation. Can be invoked directly or is automatically triggered by /arc-planning. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Implementing

IssueのtasksコメントのタスクをTDDで全て自律実装し、専門レビューエージェントによるFBループ後にPRを作成する。

## Workflow

### Step 1: Issue情報・タスク・Spec読み込み

**ISSUE_NUM・REPO・ISSUE_URLの取得（bash不要）**

1. `ISSUE_NUM`: システムプロンプトの `gitStatus` セクションに含まれる現在のブランチ名（例: `feature/issue-42-add-auth`）から正規表現 `issue-(\d+)` で抽出する。該当しない場合はユーザーに正しいブランチへ切り替えるよう案内して終了する。

2. `REPO`: 以下のコマンドで取得する（worktree環境でも動作する）：
   ```bash
   REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
   ```

3. `ISSUE_URL`: `https://github.com/${REPO}/issues/${ISSUE_NUM}` として構築する（bashコマンド不要）。

**タスク・Spec・Designの取得**:

```bash
TASKS_COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .id')
TASKS_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .body')
SPEC_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body')
DESIGN_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:design -->"))][0] | .body')
```

tasksコメントが見つからない場合は `/arc-planning` を先に実行するよう案内して終了。
spec（意図）・design（ADR・スコープ）・docsも読み込んで実装の文脈として利用する。

**worktreeのセットアップ（必要な場合のみ）**

以下のいずれかに該当する場合、worktreeを作成してセッションを切り替える：
- `TASKS_CONTENT` に `<!-- worktree: true -->` が含まれる
- 起動プロンプトに `WORKTREE_NEEDED=true` が含まれる

該当する場合：

1. `.claude/settings.json` に `WorktreeCreate` / `WorktreeRemove` hookが未設定であれば自動セットアップする：
   1. `.claude/hooks/` ディレクトリを作成
   2. `../../templates/hooks/worktree-create.sh` を `.claude/hooks/worktree-create.sh` にコピー
   3. `../../templates/hooks/worktree-remove.sh` を `.claude/hooks/worktree-remove.sh` にコピー
   4. 両ファイルに実行権限を付与：`chmod +x .claude/hooks/worktree-*.sh`
   5. `.claude/settings.json` の `hooks` に以下をマージ：
      ```json
      {
        "WorktreeCreate": [{"type": "command", "command": "bash .claude/hooks/worktree-create.sh"}],
        "WorktreeRemove": [{"type": "command", "command": "bash .claude/hooks/worktree-remove.sh"}]
      }
      ```

2. `EnterWorktree` ツールで `name=issue-<N>` を指定してworktreeを作成する
   - `.worktreeinclude` に記載されたファイルが自動コピーされる
   - `WorktreeCreate` hook が自動実行される
   - 現在のセッションがworktree内に切り替わる

どちらにも該当しない場合は、arc-specifyingで作成済みのブランチのまま実装を進める。

### Step 2: TDD実装ループ（全タスク完了まで繰り返す）

未完了タスク（`- [ ]`）を順番に処理する。

---

#### `[test]` タスクの処理

**① テストコードを書く（Red phase）**
- specのGoalとdocsの仕様に基づいてテストケースを設計する
- テストファイルが存在しない場合は新規作成する
- 境界値・エラーケース・正常系を含める

**② テスト実行 → 失敗確認**
- テストを実行してREDになることを確認する
- テストが誤って通ってしまう場合はテストコードを修正する

**③ tasksコメントを更新し、テストタスクをコミット**
- type-check を実行してエラーがないことを確認する（未実装シンボル由来の型エラーは許容する。それ以外のエラーがあればテストコードを修正する。検出できない場合はスキップする。最大2回修正しても解消しない場合はユーザーに報告する）
- 検出したテストコマンドを実行して RED になることを最終確認する（検出できない場合はスキップする）
- IssueのtasksコメントをPATCHして該当タスクを `- [x]` に更新する：
  ```bash
  gh api repos/${REPO}/issues/comments/${TASKS_COMMENT_ID} \
    -X PATCH -f body="<更新後のtasks内容>"
  ```
- `git commit -m "test: add tests for <task description> (#NNN)"`
- ⑩へ進む

---

#### `[impl]` タスクの処理

**④ 実装コードを書く（Green phase）**
- 直前の `[test]` タスクのテストをパスさせることだけにフォーカスする
- 過度な抽象化や先読み実装はしない

**⑤ テスト実行 → パス確認**
- テストが全てGREENになることを確認する
- 失敗した場合は実装を修正して⑤を繰り返す

**⑥ 専門レビューエージェントを選択・並列起動**

`git diff HEAD` を実行してdiffと変更ファイル一覧を取得する：

```bash
DIFF=$(git diff HEAD)
CHANGED_FILES=$(git diff HEAD --name-only)
CHANGED_COUNT=$(echo "$CHANGED_FILES" | grep -c .)
NEW_FILES=$(git diff HEAD --name-only --diff-filter=A)
```

変更ファイル一覧を以下のルールで照合し、起動するエージェントを決定する：

| エージェント | 起動条件 |
|---|---|
| **quality-reviewer** | 常に起動 |
| **architecture-linter** | 常に起動（ADRとの整合性チェック） |
| **security-reviewer** | `CHANGED_FILES` に（**大文字小文字を区別せず**）`auth\|login\|password\|token\|jwt\|session\|permission\|oauth\|api/\|route\|controller\|handler\|sql\|query\|repository\|validator\|middleware\|sanitize\|secret\|crypto\|hash\|serial\|upload\|billing\|payment` のいずれかを含む場合 |
| **architecture-reviewer** | `CHANGED_COUNT` が3以上 OR `NEW_FILES` が**2件以上** OR `CHANGED_FILES` に `service\|domain\|infra\|repository\|module\|core\|gateway\|usecase\|adapter` のいずれかを含む場合 |
| **cicd-reviewer** | `CHANGED_FILES` に（**大文字小文字を区別せず**）`.github/\|.gitlab-ci\|Jenkinsfile\|.circleci\|migration\|migrate\|schema\|\.env\|config/\|settings\|package\.json\|package-lock\|yarn\.lock\|pnpm-lock\|poetry\.lock\|Pipfile\.lock\|pyproject\.toml\|requirements\.txt\|Cargo\.toml\|go\.mod\|Makefile\|Dockerfile\|docker-compose\|terraform/\|\.tf\|k8s/\|kubernetes/\|helm/\|ansible/\|bitbucket-pipelines` のいずれかを含む場合 |

起動対象と判定したエージェントファイルを Read し、対応するプレースホルダーを置換して**同時に**起動する：

- **`../../agents/quality-reviewer.md`** (常時): `[git diff HEAD の出力]` を置換
- **`../../agents/architecture-linter.md`** (常時): `[git diff HEAD の出力]` と `[designコメントのADRセクション]` を置換（`DESIGN_CONTENT`の`### ADR`セクション部分を渡す）
- **`../../agents/security-reviewer.md`** (条件該当時): `[git diff HEAD の出力]` と `[specの内容]` を置換
- **`../../agents/architecture-reviewer.md`** (条件該当時): `[git diff HEAD の出力]`・`[designコメントのADRセクション]`・`[観察された主要なアーキテクチャパターン]` を置換（ADRは`DESIGN_CONTENT`から）
- **`../../agents/cicd-reviewer.md`** (条件該当時): `[git diff HEAD の出力]` と `[specの内容]` を置換

**⑦ 指摘の統合と修正**
- 全エージェントの指摘を統合する
- CRITICAL/HIGHの指摘は必ず修正する（architecture-linterのCRITICALはADR違反なので最優先で修正）
- MEDIUM/LOWの指摘は修正が適切かを判断して対応する
- 修正後は⑤へ戻ってテストをパスすることを確認する（最大2回まで。解消できない場合はユーザーに報告して判断を仰ぐ）

**⑧ Docsの更新**
- 実装した機能に合わせて `docs/` の該当ファイルを更新する
- 仕様の変更・追加があれば反映する
- `## ADR` セクションが存在しない場合は末尾に追加する（`ISSUE_URL` は Step 1 で取得済み）：
  ```markdown
  ## ADR
  この機能の設計判断・代替案の検討・採用理由は [Issue #${ISSUE_NUM}](${ISSUE_URL}) を参照。
  ```
- 既存の `## ADR` セクションがある場合（別Issueで作られた機能の修正時）は、新しい Issue 番号と URL に更新する

**⑨ tasksコメントを更新し、実装タスクをコミット**
- type-check を実行してエラーがないことを確認する（エラーがあれば実装コードを修正する。検出できない場合はスキップする。最大2回修正しても解消しない場合はユーザーに報告する）
- 検出したテストコマンドを実行して全テストが GREEN になることを最終確認する（検出できない場合はスキップする）
- IssueのtasksコメントをPATCHして該当タスクを `- [x]` に更新する：
  ```bash
  gh api repos/${REPO}/issues/comments/${TASKS_COMMENT_ID} \
    -X PATCH -f body="<更新後のtasks内容>"
  ```
- `git commit -m "feat: implement <task description> (#NNN)"`

---

**⑩ 次の未完了タスクへ**
- `- [ ]` のタスクが残っていれば、タスク種別（`[test]` or `[impl]`）を確認して①または④へ戻る
- 全タスク完了したらStep 2.5へ

### Step 2.5: 最終一括レビュー＋Specカバレッジチェック

全`[impl]`タスクの実装完了後、PRブランチ全体を対象に最終レビューを実施する。

```bash
BASE=$(git merge-base HEAD origin/HEAD 2>/dev/null \
  || git merge-base HEAD origin/main 2>/dev/null \
  || git merge-base HEAD origin/master 2>/dev/null)
# BASEが空の場合（デフォルトブランチがmain/master以外、またはorigin/HEADが未設定）は
# ユーザーにベースブランチ名を確認してから git merge-base HEAD origin/<branch> で取得する
FULL_DIFF=$(git diff "${BASE}")
FULL_CHANGED_FILES=$(git diff "${BASE}" --name-only)
FULL_CHANGED_COUNT=$(echo "$FULL_CHANGED_FILES" | grep -c .)
FULL_NEW_FILES=$(git diff "${BASE}" --name-only --diff-filter=A)
```

**2.5-A: 既存レビューエージェント（横断チェック）**

⑥のフィルタリングルール表を参照してエージェントを選択し、**spec-coverage-reviewerと同時に**起動する。判定変数の対応は以下の通り：

| ⑥の変数名 | Step 2.5 での対応変数 |
|---|---|
| `CHANGED_FILES` | `FULL_CHANGED_FILES` |
| `CHANGED_COUNT` | `FULL_CHANGED_COUNT` |
| `NEW_FILES` | `FULL_NEW_FILES` |

各エージェントのプレースホルダーは以下の通り置換する：
- `[git diff HEAD の出力]` → `FULL_DIFF` の内容（**PRブランチ全体のdiff**。エージェント起動時の指示にも「このdiffはPR全体の累積差分です」と明記してコンテキストを正確に伝える）
- `[designコメントのADRセクション]` → `DESIGN_CONTENT` の `### ADR` セクション部分（Step 1で取得済み）
- その他のプレースホルダーは⑥と同様

**2.5-B: Specカバレッジチェック（常に実行）**

`../../agents/spec-coverage-reviewer.md` を Read し、以下のプレースホルダーを置換してExploreエージェントを起動する（2.5-Aと同時に）：
- `[specの内容]` → SPEC_CONTENTの内容
- `[PRブランチのdiffの内容]` → FULL_DIFFの内容

**⑥ですでに検出・修正した指摘の重複は無視してよい。** 最終レビューの目的はタスク間をまたぐ横断的な問題（全タスクの組み合わせで生じる不整合・セキュリティ上の見落とし等）の検出である。

**カバレッジチェックの結果の処理**:

spec-coverage-reviewerのCRITICAL/HIGH指摘がある場合、**自動修正せず**に `AskUserQuestion` でユーザーに確認する：

> "以下のGoal/Acceptance Criteriaに対応するテストが見つかりませんでした。テストを追加しますか、それともこのままPR作成に進みますか？
>
> [カバレッジマトリックスと推奨テストの一覧]"

- ユーザーが「テストを追加する」を選択した場合: 推奨テストを元にテストを実装し、GREENを確認してコミットする
- ユーザーが「そのまま進む」を選択した場合: PRの説明に「未カバー要件: [一覧]」をセクションとして追加してStep 3へ進む

その後、他エージェントのCRITICAL/HIGHを修正してStep 3へ。

### Step 3: PR自動作成

全タスク完了後、ユーザーへ確認する：

> "全タスクの実装が完了しました。`git push` してPRを作成してよいですか？"

承認を得たら以下を実行する：

```bash
git push -u origin $(git branch --show-current)
```

specのContext/GoalとdesignのADR（`DESIGN_CONTENT`から）とdocsの変更点からPR説明を生成する：

```markdown
## Summary
[specのContextとGoalから抽出]

## Changes
[実装したタスクの一覧]

## Spec / ADR
詳細な背景・設計判断・代替案の検討は #NNN を参照してください。

## Test Plan
- [ ] 全ユニットテストのパスを確認
- [ ] 全インテグレーションテストのパスを確認
- [ ] [機能固有のテスト項目]

Closes #NNN

🤖 Generated with Claude Code
```

```bash
gh pr create --title "<feature title> (#NNN)" --body "$(cat <<'EOF'
[generated PR body]
EOF
)"
```

**PR URLを出力する。PRがマージされるとIssueは自動でクローズされる。**

### Step 4: worktreeのクリーンアップ（worktree使用時のみ）

Step 1でworktreeを作成した場合のみ実行する。

PRがマージされたら `ExitWorktree` ツールを `action="remove"` で呼び出してworktreeを終了する。

セッションをまたいで実行しており `ExitWorktree` が使えない場合は以下を実行する：

```bash
git worktree remove .claude/worktrees/issue-<N>
git branch -d <branch-name>
```

worktreeを使用していない場合は何もしない（ブランチはPRマージ後に `/arc-cleaning` でまとめて整理する）。

## Notes

- テストコマンドはプロジェクトの package.json / Makefile / pyproject.toml から自動検出する
- type-check コマンドは以下の順で検出する：
  1. `package.json` の `scripts` に `type-check` キーがあれば使用（`npm run type-check`）
  2. `package.json` の `scripts` に `typecheck` キーがあれば使用（`npm run typecheck`）
  3. 上記がなければ `npx --no-install tsc --noEmit` を試みる（ネットワークインストールは行わない）
  4. いずれも存在しない場合はスキップする
- テストコマンドが検出できない場合はスキップする
- lint は PostToolUse hook の責務（Write/Edit ごと）、type-check・test は本ワークフロー③・⑨の責務（commit 直前）。型検査を hook に移さないこと
- コミットメッセージはConventional Commits形式に従う（`feat/fix/test/docs:` プレフィックス）
- `plans/` ディレクトリは使用しない（タスクの状態管理はIssueコメントで行う）
