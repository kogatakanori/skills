---
name: arc-investigating
description: Autonomously investigates the technical feasibility of the spec for the current branch. Extracts the issue number from the branch name, reads the spec from the Issue comment, runs parallel investigation agents (dependency and conflict analysis), and posts findings as an Issue comment. Use after reviewing and approving the spec from /arc-specifying. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Investigating

現在のブランチに対応するspecをIssueコメントから読み取り、技術的実現性を自律調査して結果をIssueコメントに投稿する。

## Workflow

### Step 1: Spec自動取得

```bash
ISSUE_NUM=$(git branch --show-current | grep -oE 'issue-[0-9]+' | grep -oE '[0-9]+')
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
SPEC_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body')
```

`SPEC_CONTENT` が空の場合は、`/arc-specifying <N>` を先に実行するよう案内して終了。

### Step 2: 並列技術調査

#### Phase 2a: ローカル調査（常に実行）

`../../agents/dependency-analyst.md` と `../../agents/conflict-analyst.md` を Read し、`[specの全文]` を実際のspec内容で置換して、2体のExploreエージェントを**同時に**起動する：

**Agent A（dependency-analyst）**: ライブラリ・外部APIの存在・バージョン適合性を確認

**Agent B（conflict-analyst）**: 既存コードとの競合・破壊的変更・パフォーマンス懸念を調査

#### Phase 2b: Web調査クエリの生成

Phase 2a の結果から、以下の条件に該当する項目をリストアップする：
- dependency-analyst が `不明` または `バージョン競合` と判定したライブラリ
- 外部 API のステータスが `不明` または `利用不可` のもの
- セキュリティアドバイザリの確認を推奨したもの

リストが空（全項目が `利用可能`/`確認済み`/`実現可能`）の場合は Phase 2c をスキップする。

#### Phase 2c: Web調査（Phase 2b のリストが空でない場合のみ）

`../../agents/web-research-analyst.md` を Read し、`[調査クエリリスト]` を Phase 2b で生成したリスト（ライブラリ名・バージョン・確認したい点を1行ずつ）で置換して、Exploreエージェントを起動する：

**Agent C（web-research-analyst）**: WebSearch/WebFetch でメンテナンス状況・セキュリティ・breaking changes・外部 API 可用性を確認

### Step 3: 調査結果の統合と評価

全エージェントの結果を統合し、実現性を3段階で評価：

**実現可能**: 制約なしで進められる

**条件付き**: 特定の制約や追加作業があるが実現できる
- 何の対応が必要かを明示

**実現困難**: 根本的な問題がある
- 具体的な代替アーキテクチャ案を提示
- specの修正が必要であることをユーザーに伝える

### Step 4: Phaseスコープ評価とIssue作成

SpecのGoalと調査結果を照合し、今回実装するスコープ（Phase 1）と後続フェーズ（Phase 2+）に分類する。

**Phase 2以降への延期基準**（いずれかに該当するGoal・作業を延期対象とする）：
- `条件付き`と判定されたが、対応工数が大きく今回のスコープに収まらないもの
- `実現困難`と判定されたGoalで、代替案の実装も複雑なもの
- Specに含まれているがMVPとして必須でない機能
- 調査で新たに判明した追加作業・改善点

延期項目がある場合、それぞれについてGitHub Issueを作成する：

```bash
gh issue create \
  --title "Phase 2: <延期する機能の概要>" \
  --body "$(cat <<'EOF'
## 背景
#${ISSUE_NUM} のPhase 1実装後に対応する機能。

## 内容
[延期した理由と具体的な作業内容]

## 前提条件
- Phase 1 (#${ISSUE_NUM}) の完了
EOF
)"
```

作成したIssue番号とURLを記録し、Step 5のコメントに含める。延期項目がない場合はこのステップをスキップする。

### Step 5: 調査結果をIssueコメントに投稿

既存の `<!-- arc:investigation -->` コメントがある場合は更新し、なければ新規投稿する：

```bash
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:investigation -->"))][0] | .id')

BODY="$(cat <<'EOF'
<!-- arc:investigation -->
## Feasibility Investigation

**判定**: 実現可能 / 条件付き / 実現困難
**調査日**: YYYY-MM-DD

### 依存関係・統合（Agent A）
[Agent Aの調査結果サマリー]

### コード競合・パフォーマンス（Agent B）
[Agent Bの調査結果サマリー]

### Web調査・外部情報（Agent C）
[Agent Cの調査結果サマリー / または「スキップ（ローカル調査で十分と判断）」]

### 結論
[なぜこの判定か、具体的な理由]

### 対応が必要な事項（条件付きの場合）
- [ ] 対応事項1
- [ ] 対応事項2

### 代替案（実現困難の場合）
- **案A**: [概要と採用すべき理由]
- **案B**: [概要と採用すべき理由]

**次のステップ**: Issueのspecコメントを修正し（ADRセクションで上記代替案を検討・採用アプローチを再決定）、再度 `/arc-investigating` を実行してください。

### Phase分け
**Phase 1（今回）**: [今回実装するGoalの一覧]
**Phase 2以降**: なし / #NNN [タイトル]（作成したIssueのURL）
EOF
)"

if [ -n "$COMMENT_ID" ]; then
  gh api repos/${REPO}/issues/comments/${COMMENT_ID} -X PATCH -f body="$BODY"
else
  gh issue comment ${ISSUE_NUM} --body "$BODY"
fi
```

### Step 6: Docsの更新

調査で発覚した制約・前提条件を `docs/` ファイルの仕様セクションに反映する（変更がある場合のみ）。

変更がある場合はコミットする：

```bash
git add docs/
git commit -m "spec: update docs with feasibility constraints for issue #NNN"
```

### Step 7: 案内

IssueのURLを表示し、**"調査結果を確認し方向性を決定したら、`/arc-planning` を実行してください"** と案内する。

実現困難の場合は代替案を提示し、specの修正を促す。

## Notes

- 実現困難と判断した場合でも、必ず代替案を提示して前に進めるようにする
- 技術的な判断に迷う場合は、よりシンプルなアプローチを優先する
- specのファイルは存在しない（Issueコメントが正とする）
