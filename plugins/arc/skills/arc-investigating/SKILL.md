---
name: arc-investigating
description: Investigates a codebase or design question ad-hoc — root cause of a bug, how a feature works, blast radius of a change. Skips spec/design entirely; takes the question, runs a read-only investigation, and reports findings directly. GitHub Issue is optional for standalone use, but required when used as the precursor to /arc-bugfixing (posts findings as an Issue comment). Part of the Arc SDLC workflow (bug-fix / investigation track).
user_invocable: true
---

# Arc Investigating

**役割: 調査して答える。specやdesignは作らない。**

`/arc-specifying` 以降のフルフローはGoal/Use Cases/Acceptance Criteria/Domain Modelを固める前提の重量級フローで、「なぜこのバグが起きているか」「この機能はどう動いているか」のような調査系タスクには向かない。arc-investigatingは調査結果を返すことだけにフォーカスした軽量スキル。

**このスキルはコードを変更しない。** 修正が必要と分かった場合は `/arc-bugfixing` へ引き継ぐ。

## Workflow

### Step 1: 調査内容の確定

ユーザーの質問をそのまま調査対象とする。**明確化のためのQ&Aは挟まない。** 曖昧さがあっても、まず調査してから不明点として報告する。

Issue番号が指定された場合（例: `/arc-investigating 42` や「Issue #42を調べて」）のみ、Issue本文を取得して調査対象に加える：

```bash
gh issue view <N> --json title,body,url
```

Issue番号の指定がない場合はこのステップをスキップし、会話内の質問だけを調査対象とする。

### Step 2: 即座に調査

`Agent` ツールで `subagent_type: Explore` のエージェントを起動する（新規の専用エージェントファイルは作らない。読み取り専用ツールで完結する調査はExploreに一任する）。

プロンプトには以下を含める：

```
以下を調査し、根拠付きで報告してください。コードは変更しないでください。

# 調査内容
[Step 1で確定した質問。Issue取得した場合はIssueタイトル+本文も含める]

# 報告形式
- 結論: [分かったことを簡潔に]
- 根拠: [ファイルパス:行番号 と該当コードの要点。複数可]
- 確信度: 高 / 中 / 低
- 不明点: [コードベース調査だけでは判断できなかった点があれば]

bugの調査の場合は追加で:
- 再現条件: [分かる範囲で]
- 影響範囲: [同じ問題が起きうる箇所]
- 修正方針の候補: [1〜2案。深入りしすぎず方向性のみ]
```

複数の観点（例: フロントエンドとバックエンドの両方に跨る調査）が必要な場合は、観点ごとに複数のExploreエージェントを並列起動してよい。

### Step 3: 結果の提示

Step 2の結果をそのままユーザーに提示する。

**Issue番号が指定されている場合**、調査結果を `<!-- arc:investigation -->` 識別子付きでIssueコメントとして投稿する：

```bash
gh issue comment <N> --body "$(cat <<'EOF'
<!-- arc:investigation -->
## Investigation

**調査日**: YYYY-MM-DD
**調査内容**: [Step 1で確定した質問]

### 結論
[Step 2の結論]

### 根拠
[Step 2の根拠]

### 確信度
[高 / 中 / 低]

### 不明点
[あれば記載。なければ「なし」]
EOF
)"
```

**bugの調査の場合のみ**、上記の「不明点」セクションの後に以下を追記する（bugでない調査の場合はセクション自体を含めない）：

```
### bug調査の場合
**再現条件**: [...]
**影響範囲**: [...]
**修正方針の候補**: [...]
```

Issue番号が指定されていない場合は会話内の回答のみで完結し、Issueへの投稿は行わない。

**同じIssueに対して2回目以降の実行の場合**、新規投稿ではなく既存の `<!-- arc:investigation -->` コメントを上書き更新する：

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:investigation -->"))][0] | .id'
```

IDが取得できた場合は `gh api repos/<REPO>/issues/comments/<COMMENT_ID> -X PATCH -f body="..."` で更新する。IDが取得できなかった場合（初回実行）は上記の通り新規投稿する。

### Step 4: 案内

- Issueに投稿した場合: 「調査結果を確認し、修正が必要なら `/arc-bugfixing <N>` を実行してください」と案内する
- 投稿していない場合: 追加で調べたい点があれば会話を続ける旨を伝える

## Notes

- specやdesignのような品質レビュー専用エージェントは付けない（調査結果は人間が直接判断する）
- 既存4スキル（specifying/designing/planning/implementing）とは独立しており、どちらから開始してもよい
