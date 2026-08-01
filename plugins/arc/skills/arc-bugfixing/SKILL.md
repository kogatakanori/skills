---
name: arc-bugfixing
description: Plans a TDD bug fix from a GitHub Issue — reads the investigation comment (or the issue body directly for obvious bugs), breaks the fix into a TDD task checklist via implementation-analyst, runs a self-review feedback loop (TDD compliance, granularity, dependency order — no spec/AC coverage check), posts tasks as an Issue comment, then automatically transitions into arc-implementing. Skips spec and design entirely; use after /arc-investigating (or directly for self-evident bugs). Part of the Arc SDLC workflow (bug-fix track).
user_invocable: true
---

# Arc Bugfixing

**役割: bug修正をTDDタスクに分解する。arc-planningのbug fix版。**

specやdesignは作らない。原因が分かっている（または自明な）bugを、`[test]`→`[impl]`のTDDタスクに分解し、自律レビュー後に自動でarc-implementingへ引き継ぐ。

## Workflow

### Step 1: Issueブランチの作成

1. Issue情報を取得する：
   ```bash
   gh issue view <N> --json title,body,url
   ```

2. Issue用ブランチを作成してチェックアウトする：
   ```bash
   gh issue develop <N> --checkout
   ```
   `gh issue develop` が使えない場合は代替する：
   ```bash
   git checkout -b issue-<N>
   ```

**既に対応するIssueブランチにいる場合**（手動で `issue-<N>` ブランチへ切り替え済みの場合など）はこのステップをスキップする。`arc-investigating` はブランチを作成・切り替えしないため、その直後であっても本ステップは必要。

### Step 2: sub-agent への委譲（メインコンテキスト保護）

**このステップのみメインコンテキストで実行し、以降の全処理は sub-agent に委譲する。**

1. `REPO` を取得する：
   ```bash
   gh repo view --json nameWithOwner -q .nameWithOwner
   ```

2. `Agent` ツールで sub-agent を spawn し、以下の prompt を渡す：
   ```
   ISSUE_NUM=<N>、REPO=<owner/repo> のIssueに対して arc-bugfixing のワークフローを Step 3 から実行してください。ISSUE_NUM・REPO はこの prompt の値を使用すること。
   ```

3. sub-agent の完了を待ち、結果（Issue コメント URL・タスク一覧）をユーザーに表示して終了する。

---

### Step 3: 調査結果の取得

```bash
gh api repos/<REPO>/issues/<ISSUE_NUM>/comments --jq '[.[] | select(.body | startswith("<!-- arc:investigation -->"))][0] | .body'
```

**`<!-- arc:investigation -->` コメントが見つからない場合**、Issue本文（title + body）を代わりに使う（自明なbugは `/arc-investigating` を省略できる）：

```bash
gh issue view <ISSUE_NUM> --json title,body
```

以降 `INVESTIGATION_CONTENT` としてどちらかの内容を保持する。

### Step 4: implementation-analystによる詳細調査

`../../agents/implementation-analyst.md` を Read し、以下のプレースホルダーを置換してExploreエージェントを起動する：
- `[specの内容]` → `INVESTIGATION_CONTENT`（調査結果またはIssue本文）
- `[docsの内容]` → 関連する `docs/` ファイルの内容（見つかった場合のみ。なければ空欄）

CREATE/MODIFY/DELETE単位の具体的な変更対象とテスト要件を特定する。

### Step 5: TDDタスク分解

調査結果をもとにタスクを分解する。arc-planningと同じTDD単位の原則に従う：

- `[test]` タスクは必ず対応する `[impl]` タスクの直前に置く
- 1つのテストファイル/テスト関数が1つの `[test]` タスク
- 各タスクは独立してコミット可能なサイズにする

**タスク例**：
```
- [ ] [test] UserService.createUser()がnullを渡された場合の異常系テストを書く
- [ ] [impl] UserService.createUser()のnullチェックを修正する
```

`../../templates/tasks.md.template` を参考にタスクリストの初版を作成する（Goal→タスク対応表は使わない。bug fixにGoal/ACは存在しない）。

### Step 6: 自律タスクレビューFBループ

以下の3観点でタスクリストをレビューし、問題があれば修正する（最大3回繰り返す）：

1. **TDD対応**: 全ての `[impl]` タスクに対応する `[test]` タスクが直前にあるか
2. **粒度の適切さ**: 1タスクが1〜2時間程度で完了できるサイズか
3. **依存関係の順序**: 依存するコードが先に実装されるよう順序付けられているか

**Goal/ACカバレッジチェックは行わない**（specが存在しないため）。

問題がある場合はタスクを修正・分割・統合・並び替えして再度チェックする。

### Step 7: タスクリストをIssueコメントに投稿

```bash
gh issue comment ${ISSUE_NUM} --body "$(cat <<'EOF'
<!-- arc:tasks -->
...タスクリストの内容...
EOF
)"
```

タスク一覧を出力して確認できるようにする。

### Step 8: 実装フェーズへ自動移行

人間の介入なしに実装フェーズへ移行する：

1. "タスク分解が完了しました。実装フェーズを開始します..." と表示する
2. `Agent` ツールで sub-agent を spawn し、以下の prompt を渡す：
   ```
   ISSUE_NUM=<N>、REPO=<owner/repo> のIssueに対して arc-implementing のワークフローを Step 1 から実行してください。ISSUE_NUM・REPO はこの prompt の値を使用すること。
   ```

## Notes

- `plans/` ディレクトリは使用しない（タスクリストはIssueコメントで管理）
- arc-implementingは無改造で流用する。spec/designコメントが存在しないため、Step 3のサブエージェントプロンプトの `# Spec` `# Design` セクションおよびStep 4のspec-coverage-reviewerは実質空振りになるが許容する
- タスク数は通常3〜8個程度（bug fixはfeature実装より小規模なことが多い）
- `<!-- arc:investigation -->` も Issue本文も手がかりが薄い場合は、Step 4のimplementation-analystの調査結果を優先してタスクを組み立てる
