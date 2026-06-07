---
title: arc-implementing の Bash 呼び出し分割
issue: "#1"
last_updated: 2026-06-07
---

# arc-implementing の Bash 呼び出し分割

## 概要

`/arc-implementing` がIssueのtasksコメントを更新する際、変数代入と `gh api PATCH` を1つの Bash 呼び出しにまとめると Claude Code のパーミッションチェックに一致しない。`arc-implementing/SKILL.md` の ③・⑨ステップを修正し、PATCH 呼び出しを単独の Bash 呼び出しとして記述することで、確認プロンプトなしにタスク更新を自動実行できるようにする。

## 使い方

利用プロジェクトの `.claude/settings.json` の `permissions.allow` に以下を追加する：

```json
"Bash(gh api repos/<github-username>/*:*)"
```

`<github-username>` は実際の GitHub ユーザー名に置き換える（例: `Bash(gh api repos/kogatakanori/*:*)`）。

この設定と本修正を合わせることで、`/arc-implementing` 実行中のタスク更新が確認プロンプトなしに自動実行される。

## 仕様

### 問題のある複合コマンド（修正前）

```bash
TASKS_COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments --jq '...')
gh api repos/${REPO}/issues/comments/${TASKS_COMMENT_ID} -X PATCH -f body="..."
```

先頭が `TASKS_COMMENT_ID=` であるため `Bash(gh api repos/<owner>/*:*)` にマッチしない。

### 修正後の2ステップ構成

**Step 1 での ID 取得（既存・変更なし）:**

```bash
gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:tasks -->"))][0] | .id'
```

**③・⑨ステップでの PATCH（単独呼び出し）:**

```bash
gh api repos/${REPO}/issues/comments/${TASKS_COMMENT_ID} \
  -X PATCH -f body="<更新後のtasks内容>"
```

`gh api repos/` で始まるため `Bash(gh api repos/<owner>/*:*)` にマッチし、確認プロンプトなしで実行される。

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `plugins/arc/skills/arc-implementing/SKILL.md` | ③・⑨ステップを PATCH 単独呼び出しに修正 |

## ADR

この機能の設計判断・代替案の検討・採用理由は [Issue #1](https://github.com/kogatakanori/skills/issues/1) を参照。
