---
name: arc-cleaning
description: Scans local worktrees created by arc-specifying, checks if their corresponding PRs are merged on GitHub, and removes merged worktrees and branches. Run periodically to keep the workspace clean. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Cleaning

ローカルのworktreeを一覧表示し、対応するPRがマージ済みのものを削除する。

## Workflow

### Step 1: REPO取得とworktree一覧の取得

**REPOの取得（bash不要）**

Read ツールで `.git/config` を読み取り、`[remote "origin"]` の `url` 行から `owner/repo` 形式で抽出する。

**worktree一覧の取得**：

```bash
git worktree list --porcelain
```

`.claude/worktrees/issue-` のパターンにマッチするworktreeをフィルタリングする。該当するworktreeがない場合は「クリーンアップ対象のworktreeはありません」と表示して終了。

### Step 2: 各worktreeのマージ状態を確認

各worktreeについて以下を並列で実行する：

1. worktreeパスから `issue-(\d+)` の正規表現でISSUE_NUMを抽出する
2. worktreeのブランチ名を取得する：
   ```bash
   git -C <worktree_path> branch --show-current
   ```
3. 対応するPRのマージ状態を確認する：
   ```bash
   gh pr list --repo ${REPO} --head <branch-name> --state merged --json number,mergedAt
   ```

結果を「マージ済み」「未マージ」に分類する。

### Step 3: マージ済みworktreeの削除

マージ済みのworktreeが1件以上ある場合、削除対象の一覧を表示してユーザーに確認する。

承認を得たら各worktreeを削除する：

```bash
git worktree remove <worktree_path>
git branch -d <branch-name>
```

### Step 4: 結果の表示

以下の形式で結果を表示する：

```
✅ 削除済み:
  - .claude/worktrees/issue-42 (feature/issue-42-add-auth) ← PR #123 マージ済み
  - .claude/worktrees/issue-55 (feature/issue-55-fix-login) ← PR #130 マージ済み

⏳ 未マージのため保持:
  - .claude/worktrees/issue-67 (feature/issue-67-refactor) ← PR #140 レビュー中
```
