---
title: arc-planning sub-agent transition
issue: "#3"
last_updated: 2026-06-07
---

# arc-planning sub-agent transition

## 概要

arc-planning の Step 6 において、実装フェーズへの移行を直接継続方式からsub-agent spawnに変更する機能。これによりplanningフェーズのコンテキストが実装ループに引き継がれなくなり、コンテキストウィンドウの圧迫を防ぐ。

## 使い方

ユーザーからの操作は変わらない。`/arc-planning` を実行すると、タスク分解・IssueコメントへのPOST完了後、自動的にsub-agentが起動してarc-implementingワークフローを実行する。

```
/arc-planning
↓（自動）
sub-agent spawn → arc-implementing Step 1から実行
```

## 仕様

### 変更前（Step 6）

```
/arc-implementing スキルのワークフローを Step 1 から実行する
```

planningフェーズのコンテキスト（spec・調査結果・タスク分解の思考過程）がそのまま実装ループに引き継がれる。

### 変更後（Step 6）

`Agent` ツールで sub-agent を spawn し、以下の prompt を渡す：

```
ISSUE_NUM=<N>、REPO=<owner/repo> のIssueに対して arc-implementing のワークフローを Step 1 から実行してください。ISSUE_NUM と REPO はこの prompt の値を使用すること。
```

- `<N>` と `<owner/repo>` は arc-planning Step 1 で取得済みの値に置換する
- ISSUE_NUM・REPOを明示的に渡すことで、sub-agentのgitStatus継承に依存しない
- メインセッション（planning）のコンテキストはsub-agent起動後に終了し、実装ループの影響を受けない

### コンテキスト分離の効果

| フェーズ | 方式 | コンテキスト |
|---------|------|------------|
| 変更前 | 直接継続 | planning + implementing が同一コンテキスト |
| 変更後 | sub-agent spawn | planning / implementing が分離 |

タスク数が5〜15個の場合、各タスクのテスト作成・実装・4エージェントレビューがすべて独立したコンテキスト内で実行されるため、後半タスクの品質低下を防ぐ。

## 前提条件・制約

- sub-agentの `gitStatus` にブランチ名（`issue-N`）が含まれること（ISSUE_NUM自己取得の前提）
- arc-implementing Step 3 のユーザー確認プロンプト（PR作成確認）がsub-agent経由でもメインセッションに届くこと

## ADR

この機能の設計判断・代替案の検討・採用理由は [Issue #3](https://github.com/kogatakanori/skills/issues/3) を参照。
