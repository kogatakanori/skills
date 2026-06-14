---
name: arc-designing
description: Autonomously designs the HOW for the current spec — feasibility check, overall design, scope definition, implementation constraints, and ADR. Extracts the issue number from the branch name, reads the spec from the Issue comment, runs parallel investigation agents (dependency and conflict analysis), and posts the design as an Issue comment. Use after reviewing and approving the spec from /arc-specifying. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Designing

**役割: 意図（Spec）をHOWに変換する**

arc-specifyingで「実現したいこと（意図）」が確定した後、このフェーズでその意図を実現するための設計を行う。実現性の確認・全体設計・スコープ定義・実装制約・ADRを策定する。

**重要な原則: 意図は変えない。アプローチだけを調整する。**

調査の結果「実現困難」と判明した場合、やりたいことを諦めるのではなく、**同じ意図を達成できる別のアプローチ**を提案する。Specに戻って修正するのは「アプローチ（ADR）」であり、「Goal/AC/Why」ではない。

現在のブランチに対応するspecをIssueコメントから読み取り、設計結果をIssueコメントに投稿する。

## Workflow

### Step 1: Spec自動取得

**ISSUE_NUM・REPOの取得（bash不要）**

1. `ISSUE_NUM`: システムプロンプトの `gitStatus` セクションに含まれる現在のブランチ名（例: `feature/issue-42-add-auth`）から正規表現 `issue-(\d+)` で抽出する。該当しない場合はユーザーに正しいブランチへ切り替えるよう案内して終了する。

2. `REPO`: 以下のコマンドで取得する（worktree環境でも動作する）：
   ```bash
   REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
   ```

**Specの取得**:

```bash
SPEC_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body')
```

`SPEC_CONTENT` が空の場合は、`/arc-specifying <N>` を先に実行するよう案内して終了。

### Step 1.5: design-clarifier【Phase 1】変更タイプの判断

`../../agents/design-clarifier.md` を Read し、`[specの内容]` を SPEC_CONTENT で置換し、`[調査結果の要約]` は**空のまま**にしてExploreエージェントを起動する。

design-clarifierが以下を判断する：
- **踏襲型**: 既存の設計・パターンを踏まえて機能を追加・拡張する
- **変革型**: 既存の設計を大きく変更・置き換える、または全く新しい設計を導入する

出力を受け取り `CHANGE_TYPE`（`踏襲型` / `変革型`）として記録する。

判断が曖昧な場合はdesign-clarifierが1問生成するので、ユーザーに確認してからStep 2へ進む。

**⚠️ 仮にCHANGE_TYPEの判断が誤っていても、Step 2.5のQ&Aで修正できる。ここで完璧を求めない。**

### Step 2: 並列技術調査

#### Phase 2a: ローカル調査（CHANGE_TYPEに応じて構成変更）

以下エージェントのファイルを Read し、プレースホルダーを置換して**同時に**起動する：

**Agent A（codebase-analyst）**: `[specの全文]` と `[変更タイプ]` を置換して起動。CHANGE_TYPEによって調査の焦点が変わる：
- 踏襲型: 参考パターン・再利用可能なコンポーネントを調査
- 変革型: 変更・置き換え対象の既存実装と影響範囲を特定

**Agent B（architecture-analyst）**: `[specの全文]` を置換して起動（常に起動。アーキテクチャ制約・既存docs・テスト基盤を調査）

**Agent C（dependency-analyst）**: `[specの全文]` を置換して起動（常に起動。ライブラリ・外部APIの存在・バージョン適合性を確認）

**Agent D（risk-analyst）**: `[specの全文]` を置換して起動（常に起動。破壊的変更・パフォーマンスリスク・セキュリティ設計制約・テスト基盤を調査。変革型では特に網羅的に）

#### Phase 2b: Web調査クエリの生成

Phase 2a の結果から、以下の条件に該当する項目をリストアップする：
- dependency-analyst が `不明` または `バージョン競合` と判定したライブラリ
- 外部 API のステータスが `不明` または `利用不可` のもの
- セキュリティアドバイザリの確認を推奨したもの

リストが空（全項目が `利用可能`/`確認済み`/`実現可能`）の場合は Phase 2c をスキップする。

#### Phase 2c: Web調査（Phase 2b のリストが空でない場合のみ）

`../../agents/web-research-analyst.md` を Read し、`[調査クエリリスト]` を Phase 2b で生成したリスト（ライブラリ名・バージョン・確認したい点を1行ずつ）で置換して、Exploreエージェントを起動する：

**Agent C（web-research-analyst）**: WebSearch/WebFetch でメンテナンス状況・セキュリティ・breaking changes・外部 API 可用性を確認

#### Phase 2d: 残存する不明項目のユーザー確認（必要な場合のみ）

Phase 2cの後、全エージェントの結果を照合し、依然として`不明`のままの項目がある場合は `AskUserQuestion` でユーザーに確認する（最大2問まで）。

確認例：
- 「○○ライブラリのv2.xとの互換性がWeb上でも確認できませんでした。プロジェクトで使用中のバージョンを教えてください」
- 「△△ APIの利用可否が不明です。アクセス権限・契約状況を確認できますか？」

ユーザーの回答を踏まえて該当項目の判定を更新し、Step 3へ進む。

### Step 2.5: design-clarifier【Phase 2】HOW判断のQ&A

`../../agents/design-clarifier.md` を Read する。以下のプレースホルダーを置換してExploreエージェントを起動する：
- `[specの内容]` → SPEC_CONTENTの内容
- `[調査結果の要約]` → 「CHANGE_TYPE: 踏襲型/変革型」＋ Phase 2a〜2dの全エージェント結果のサマリー（判明した制約・パターン・実現可能性の要点）

design-clarifierの出力を受け取ったら、以下のフォーマットで1問ずつ聞く：

```
Q1. [設計判断の質問]

推奨: [design-clarifierが提案した推奨アプローチと根拠]
```

ユーザーは「はい（推奨通り）」「いいえ（〇〇にしたい）」等と答える。
回答を受け取ったら次の質問へ進む。全質問を消化するか、設計方針が十分に明確になったら次へ進む。

**「確認の必要なし」と返ってきた場合**、または全質問を消化したら即座にStep 3へ。

得られた全ての回答を「確定した設計方針（DESIGN_DIRECTION）」として記録し、Step 3以降のADR策定に活用する。

### Step 3: 調査結果の統合と実現性評価

全エージェントの結果を統合し、実現性を3段階で評価：

**実現可能**: 制約なしで進められる

**条件付き**: 特定の制約や追加作業があるが実現できる
- 何の対応が必要かを明示

**実現困難**: 根本的な問題がある
- 具体的な代替アーキテクチャ案を2つ以上提示する
- `AskUserQuestion` でユーザーに代替案を選択させる：
  > "以下の技術的問題により、元のアプローチは実現困難です:
  > 【理由】[実現困難と判断した具体的な根拠]
  >
  > 代替案A: [概要・採用すべき理由]
  > 代替案B: [概要・採用すべき理由]
  >
  > どちらで進めますか？"
- 選択された代替案を `DESIGN_DIRECTION` に記録して Step 4 以降の ADR 策定に反映する
- ⚠️ Spec の Goal/Why/Constraints は変更しない。HOW（アプローチ）のみを代替案に切り替える

### Step 4: スコープ定義とPhase分け

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

### Step 5: Design作成・品質チェック・投稿

#### Step 5-a: 設計内容の作成（下書き）

Step 2.5 の DESIGN_DIRECTION と Step 3 の実現性評価をもとに、以下のテンプレートで設計内容を作成する（まだ投稿しない）：

```
<!-- arc:design -->
## Design

**実現性**: 実現可能 / 条件付き / 実現困難
**設計日**: YYYY-MM-DD

### 調査結果サマリー

#### コードベース調査（codebase-analyst）
[類似機能・踏襲すべきパターン・ADR文脈]

#### アーキテクチャ制約（architecture-analyst）
[既存アーキテクチャ制約・docs・テスト基盤]

#### 依存関係（dependency-analyst）
[ライブラリ・外部API確認結果]

#### リスク分析（risk-analyst）
[既存コードとの競合・パフォーマンス懸念]

#### Web調査（web-research-analyst）
[確認した内容 / または「スキップ（ローカル調査で十分）」]

### 実現性評価
[なぜこの判定か、具体的な根拠]

### 対応が必要な事項（条件付きの場合）
- [ ] 対応事項1

### Spec→Designトレーサビリティ

| Spec要件 | 種別 | 設計上の対応 |
|---------|------|------------|
| Goal 1: 〜できる | Goal | [ADRのどのアプローチが対応するか] |
| UC-1: 〜のとき〜する | Use Case | [どのコンポーネント/フローが処理するか] |
| Constraint: 〜 | Constraint | [設計上のガードレール] |
| Goal N: 〜 | Goal | Phase 2 #NNN で対応 |

### ADR（Architecture Decision Record）

**採用するアプローチ**:
[specの意図を実現するための具体的な実装方針。依存ライブラリ・パターン・アーキテクチャを明記]

**検討した代替案と却下理由**:
- **案A**: [概要] — 却下理由: [技術的制約・コスト・既存コードとの相性等]
- **案B**: [概要] — 却下理由: [...]

**トレードオフ・リスク**:
- [このアプローチを選んだことで生じる制約や将来への影響]

**テスト戦略**:
- ユニットテスト境界: [どこまでをユニットテストでカバーするか]
- インテグレーションテスト: [外部依存との境界]
- モック方針: [外部API/DBをどうモックするか]

### スコープ（今回実装する範囲）

**In Scope（Phase 1で実装）**: [今回実装するGoalの一覧]
**Out of Scope（Phase 2以降）**: なし / #NNN [タイトル]（Issue URL）
```

#### Step 5-b: design-reviewerによる品質チェック

`../../agents/design-reviewer.md` を Read し、以下のプレースホルダーを置換してExploreエージェントを起動する：
- `[specの内容]` → SPEC_CONTENTの内容
- `[designの内容]` → Step 5-aで作成したDesignの全文

design-reviewerの結果を受け取ったら：
- **問題なし**: 即座に Step 5-c へ進む
- **MEDIUM指摘**: 改善推奨として記録し、Designを修正して Step 5-c へ進む
- **HIGH指摘**: Designを自動修正して Step 5-b を再実行する（最大2回）
- **CRITICAL指摘**: `AskUserQuestion` でユーザーに確認を求める（GoalがDesignでカバーされていない等の根本的な欠落）

#### Step 5-c: Issueコメントへの投稿

品質チェック通過後、既存の `<!-- arc:design -->` コメントがある場合は更新し、なければ新規投稿する：

```bash
COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:design -->"))][0] | .id')

BODY="$(cat <<'EOF'
[Step 5-aで作成した設計内容の全文]
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
git commit -m "spec: update docs with design constraints for issue #NNN"
```

### Step 7: 案内

IssueのURLを表示し、**"設計結果を確認し方向性を決定したら、`/arc-planning` を実行してください"** と案内する。

## Notes

- 実現困難と判断した場合でも、必ず代替案を提示して前に進めるようにする
- 技術的な判断に迷う場合は、よりシンプルなアプローチを優先する
- specのファイルは存在しない（Issueコメントが正とする）
- スコープ（In/Out of Scope）はこのフェーズで定義する（Specには含まれない）
