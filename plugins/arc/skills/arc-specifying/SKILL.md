---
name: arc-specifying
description: Generates spec comment and docs from a GitHub Issue. Checks out a feature branch, runs parallel investigation agents (codebase and architecture analysis), posts spec as an Issue comment, and creates docs/ files. Use at the start of a new feature development cycle. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Specifying

GitHub IssueからSpec（なぜ・意思決定）をIssueコメントとして投稿し、Docs（何を・最新仕様）を `docs/` に生成する。

## Workflow

### Step 1: Issue取得とブランチ作成

```bash
gh issue view <N> --json title,body,labels,assignees,url
git checkout -b feature/issue-<N>-<slug>
```

### Step 2: 並列コードベース調査

`../../agents/codebase-analyst.md` と `../../agents/architecture-analyst.md` を Read し、`[issueのタイトルと本文]` を実際のIssue内容で置換して、2体のExploreエージェントを**同時に**起動する：

**Agent A（codebase-analyst）**: 類似機能・競合コード・踏襲すべきパターンを調査

**Agent B（architecture-analyst）**: アーキテクチャ制約・既存docs・テスト基盤を調査

調査結果を統合し、解消不可能な重大な曖昧点のみ `AskUserQuestion` で確認する（最大2問まで）。

### Step 3: Specコメント投稿

`../../templates/spec.md.template` を参照してSpecの内容を作成し、IssueにGitHubコメントとして投稿する：

```bash
gh issue comment <N> --body "$(cat <<'EOF'
<!-- arc:spec -->
...specの内容...
EOF
)"
```

フォーマットは `references/spec-format.md` に従う。重要な点：
- **Context（Why）**: Issueの背景・解決する課題を明確に記述
- **ADR**: なぜこのアーキテクチャを選択したか、代替案と却下理由を必ず含める
- **Goal/Non-Goals**: スコープを明確に定義する

### Step 4: Docsファイル生成

`../../templates/docs.md.template` を参照して `docs/<feature-name>.md` を生成する。

フォーマットは `references/docs-format.md` に従う。機能の概要・使い方・仕様を記述する（「何を・どう使うか」にフォーカス）。

### Step 5: コミットと案内

```bash
git add docs/
git commit -m "spec: add docs for issue #NNN - <title>"
```

**"IssueのSpecコメントを確認し承認したら、`/arc-investigating` を実行してください"** と案内する。IssueのURLも合わせて表示する。

## Notes

- specの内容はIssueコメントに保存される（`specs/` ディレクトリは使用しない）
- `docs/` ディレクトリが存在しない場合は作成する
- 既存の `docs/` ファイルがある場合は上書き更新する
