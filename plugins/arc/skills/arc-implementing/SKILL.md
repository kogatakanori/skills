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

2. `REPO`: 以下のコマンドを単体で実行して取得する（worktree環境でも動作する）：
   ```bash
   gh repo view --json nameWithOwner -q .nameWithOwner
   ```

3. `ISSUE_URL`: `https://github.com/<REPO>/issues/<ISSUE_NUM>` として構築する（bashコマンド不要）。

**タスク・Spec・Designの取得**（コマンドは1つずつ単体で実行し、`<REPO>` `<ISSUE_NUM>` は実際の値で置換する）:

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .id'
```

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .body'
```

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body'
```

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:design -->"))][0] | .body'
```

tasksコメントが見つからない場合は `/arc-planning` を先に実行するよう案内して終了。
spec（意図）・design（ADR・スコープ）・docsも読み込んで実装の文脈として利用する。

### Step 2: Claude Code Task への登録

Issue コメントから取得した全タスクを `TaskCreate` ツールで登録する（Claude Code UI のスピナーで進捗を表示するため）。

- 各タスクの `subject` は `[test] <タスク説明>` / `[impl] <タスク説明>` の形式で登録する
- 登録した Task の ID とタスク行の順序を対応づけてメモリに保持する（後の TaskUpdate で使用）
- 全タスクは `pending` ステータスで登録される

### Step 3: タスクペアサブエージェントによる実装ループ

タスクリストの `[test]`+`[impl]` ペアを先頭から順番に取り出し、ペアごとにサブエージェントを起動する。

---

**ペアの識別**: タスクリストを先頭から走査し、`[test]` タスクと直後の `[impl]` タスクを1ペアとして扱う。

**1ペアの処理フロー:**

1. 対応する Task を `TaskUpdate` で `in_progress` に更新する（[test] と [impl] 両方）

2. `Agent` ツールでタスクペアサブエージェントを起動する。`<...>` を実際の値に置換したプロンプトを渡す：

   ```
   ISSUE_NUM=<N>、REPO=<owner/repo> のIssueの以下のタスクをTDDで実装してください。

   # Spec
   <SPEC_CONTENTの全文>

   # Design
   <DESIGN_CONTENTの全文>

   # 実装するタスク
   [test] <test_task_description>
   [impl] <impl_task_description>

   # 手順

   ① テストコードを書く（Red phase）
   - specのGoalとDesignの仕様に基づいてテストケースを設計する
   - テストファイルが存在しない場合は新規作成する
   - 境界値・エラーケース・正常系を含める

   ② テスト実行 → 失敗確認
   - テストを実行してREDになることを確認する
   - テストが誤って通ってしまう場合はテストコードを修正する

   ③ 実装コードを書く（Green phase）
   - 直前の [test] タスクのテストをパスさせることだけにフォーカスする
   - 過度な抽象化や先読み実装はしない

   ④ テスト実行 → パス確認
   - テストが全てGREENになることを確認する
   - 失敗した場合は実装を修正して④を繰り返す

   ⑤ type-check の実行
   - 以下の順で検出して実行する:
     1. package.json の scripts に type-check キーがあれば npm run type-check
     2. package.json の scripts に typecheck キーがあれば npm run typecheck
     3. npx --no-install tsc --noEmit を試みる（ネットワークインストールは行わない）
     4. いずれも存在しない場合はスキップ
   - エラーがあれば実装コードを修正する（最大2回。解消しない場合は失敗として終了）

   ⑥ テスト再実行 → 最終確認
   - 全テストがGREENであることを確認する

   ⑦ Docsの更新
   - 実装した機能に合わせて docs/ の該当ファイルを更新する
   - ## ADR セクションが存在しない場合は末尾に追加する（ISSUE_NUM=<N>、ISSUE_URL=<URL>）:
     ## ADR
     この機能の設計判断・代替案の検討・採用理由は [Issue #<N>](<URL>) を参照。
   - 既存の ## ADR セクションがある場合は新しいIssue番号とURLに更新する

   ⑧ コミット（Conventional Commits形式）
   - git commit -m "test: add tests for <task description> (#<N>)"
   - git commit -m "feat: implement <task description> (#<N>)"

   # 失敗時のリトライ
   - 型エラー・テスト失敗が解消しない場合は最大3回まで修正を試みる
   - 3回試みても解消しない場合は「失敗: <エラー内容の要約>」として終了する

   # テストコマンドの検出
   プロジェクトの package.json / Makefile / pyproject.toml から自動検出する。検出できない場合はスキップする。
   ```

3. サブエージェントが完了したら結果を確認する：
   - **成功（コミット済み）**: `TaskUpdate` を `completed` に更新して次のペアへ進む
   - **失敗**: ユーザーに「タスク [task description] が失敗しました: [エラー内容]」と報告して停止する。ユーザーが修正後に再開を指示したら同じペアから再実行する

---

**⑨ Issue コメントを一括更新**

全ペア完了後、全タスクの `- [ ]` を `- [x]` に書き換えた内容で Issue コメントを1回だけ PATCH する：

```bash
gh api repos/${REPO}/issues/comments/${TASKS_COMMENT_ID} \
  -X PATCH -f body="<全タスクを [x] にした内容>"
```

その後 Step 4 へ。

### Step 4: 最終横断レビュー（サブエージェント）

全 `[impl]` タスクの実装完了後、`Agent` ツールでレビューサブエージェントを起動する。`<...>` を実際の値に置換したプロンプトを渡す：

```
ISSUE_NUM=<N>、REPO=<owner/repo> のPRブランチ全体のコードレビューを実施してください。

# Spec
<SPEC_CONTENTの全文>

# Design ADR
<DESIGN_CONTENTの ### ADR セクション>

# 手順

## 1. FULL_DIFF の取得

以下を順番に実行する（BASEが空の場合はユーザーにベースブランチ名を確認してから git merge-base HEAD origin/<branch> で取得）:
BASE=$(git merge-base HEAD origin/HEAD 2>/dev/null || git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null)
FULL_DIFF=$(git diff "${BASE}")
FULL_CHANGED_FILES=$(git diff "${BASE}" --name-only)
FULL_CHANGED_COUNT=$(echo "$FULL_CHANGED_FILES" | grep -c .)
FULL_NEW_FILES=$(git diff "${BASE}" --name-only --diff-filter=A)

## 2. レビューエージェントの選択と起動

以下のフィルタリングルールで選択し、spec-coverage-reviewer と同時に並列起動する。
各エージェントのプロンプトファイルは ../../agents/<name>.md から Read して使用する：

| エージェント | 起動条件 |
|---|---|
| quality-reviewer | 常に起動 |
| architecture-linter | 常に起動 |
| security-reviewer | FULL_CHANGED_FILES に（大文字小文字を区別せず）auth|login|password|token|jwt|session|permission|oauth|api/|route|controller|handler|sql|query|repository|validator|middleware|sanitize|secret|crypto|hash|serial|upload|billing|payment のいずれかを含む場合 |
| architecture-reviewer | FULL_CHANGED_COUNT が3以上 OR FULL_NEW_FILES が2件以上 OR FULL_CHANGED_FILES に service|domain|infra|repository|module|core|gateway|usecase|adapter のいずれかを含む場合 |
| cicd-reviewer | FULL_CHANGED_FILES に（大文字小文字を区別せず）.github/|.gitlab-ci|Jenkinsfile|.circleci|migration|migrate|schema|\.env|config/|settings|package\.json|package-lock|yarn\.lock|pnpm-lock|poetry\.lock|Pipfile\.lock|pyproject\.toml|requirements\.txt|Cargo\.toml|go\.mod|Makefile|Dockerfile|docker-compose|terraform/|\.tf|k8s/|kubernetes/|helm/|ansible/|bitbucket-pipelines のいずれかを含む場合 |
| spec-coverage-reviewer | 常に起動 |

プレースホルダーの置換：
- [git diff HEAD の出力] → FULL_DIFF（このdiffはPR全体の累積差分）
- [specの内容] → Spec全文
- [designコメントのADRセクション] → Design ADR
- [観察された主要なアーキテクチャパターン] → コードベースから観察したパターン

## 3. 指摘の処理

- CRITICAL/HIGH 指摘: 修正して再レビュー（最大2回）
- spec-coverage-reviewer の CRITICAL/HIGH: 未カバー要件の一覧を返す（修正はしない）
- LOW/MEDIUM 指摘: 記録のみ

## 4. 報告

以下の形式で報告する：
- 修正した指摘の一覧
- 未修正の LOW/MEDIUM 指摘の一覧
- spec-coverage-reviewer の未カバー要件（ある場合）
```

レビューサブエージェントの結果を受け取ったら：

**spec-coverage-reviewer の CRITICAL/HIGH 指摘がある場合**、`AskUserQuestion` でユーザーに確認する：

> "以下のGoal/Acceptance Criteriaに対応するテストが見つかりませんでした。テストを追加しますか、それともこのままPR作成に進みますか？
>
> [カバレッジマトリックスと推奨テストの一覧]"

- 「テストを追加する」を選択した場合: 推奨テストを元にテストを実装し、GREENを確認してコミットする
- 「そのまま進む」を選択した場合: PRの説明に「未カバー要件: [一覧]」をセクションとして追加してStep 5へ進む

その後、Step 5へ。

### Step 5: PR自動作成

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

## Notes

- テストコマンドはプロジェクトの package.json / Makefile / pyproject.toml から自動検出する
- コミットメッセージはConventional Commits形式に従う（`feat/fix/test/docs:` プレフィックス）
- `plans/` ディレクトリは使用しない（タスクの状態管理は Claude Code Task 機能（UI内リアルタイム）と Issue コメント（全タスク完了後に一括更新）で行う）
