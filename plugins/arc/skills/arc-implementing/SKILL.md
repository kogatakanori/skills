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

**タスク・Specの取得**:

```bash
TASKS_COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .id')
TASKS_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .body')
SPEC_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body')
```

tasksコメントが見つからない場合は `/arc-planning` を先に実行するよう案内して終了。
specとdocsも読み込んで実装の文脈として利用する。

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

**⑥ 専門レビューエージェントを並列起動**

`git diff HEAD` を実行してdiffを取得する。以下の4つのエージェントファイルを Read し、対応するプレースホルダーを置換して、4つのgeneral-purposeエージェントを**同時に**起動してコードレビューを実施する：

- **`../../agents/security-reviewer.md`**: `[git diff HEAD の出力]` と `[specの内容]` を置換
- **`../../agents/architecture-reviewer.md`**: `[git diff HEAD の出力]`・`[specのADRセクション]`・`[観察された主要なアーキテクチャパターン]` を置換
- **`../../agents/quality-reviewer.md`**: `[git diff HEAD の出力]` を置換
- **`../../agents/cicd-reviewer.md`**: `[git diff HEAD の出力]` と `[specの内容]` を置換

**⑦ 指摘の統合と修正**
- 全エージェントの指摘を統合する
- CRITICAL/HIGHの指摘は必ず修正する
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
- IssueのtasksコメントをPATCHして該当タスクを `- [x]` に更新する（③と同様）
- `git commit -m "feat: implement <task description> (#NNN)"`

---

**⑩ 次の未完了タスクへ**
- `- [ ]` のタスクが残っていれば、タスク種別（`[test]` or `[impl]`）を確認して①または④へ戻る
- 全タスク完了したらStep 3へ

### Step 3: PR自動作成

全タスク完了後、ユーザーへ確認する：

> "全タスクの実装が完了しました。`git push` してPRを作成してよいですか？"

承認を得たら以下を実行する：

```bash
git push -u origin $(git branch --show-current)
```

specのContext/Goal/ADRとdocsの変更点からPR説明を生成する：

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

### Step 4: worktreeのクリーンアップ

PRがマージされたら `ExitWorktree` ツールを `action="remove"` で呼び出してworktreeを終了する。

セッションをまたいで実行しており `ExitWorktree` が使えない場合は以下を実行する：

```bash
git worktree remove .claude/worktrees/issue-<N>
git branch -d <branch-name>
```

## Notes

- テストコマンドはプロジェクトの package.json / Makefile / pyproject.toml から自動検出する
- コミットメッセージはConventional Commits形式に従う（`feat/fix/test/docs:` プレフィックス）
- `plans/` ディレクトリは使用しない（タスクの状態管理はIssueコメントで行う）
