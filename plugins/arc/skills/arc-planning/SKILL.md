---
name: arc-planning
description: Autonomously breaks down the investigated spec into TDD task checklist, runs a self-review feedback loop for quality, posts tasks as an Issue comment, then automatically transitions into the implementation phase without human intervention. Use after reviewing investigation results and deciding on direction. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Planning

specをTDDタスクに分解し、自律レビューFBループで品質を確認後、Issueコメントに投稿して自動的に実装フェーズへ移行する。

## Workflow

### Step 1: Spec・調査結果の自動取得

**ISSUE_NUM・REPOの取得（bash不要）**

1. `ISSUE_NUM`: システムプロンプトの `gitStatus` セクションに含まれる現在のブランチ名（例: `feature/issue-42-add-auth`）から正規表現 `issue-(\d+)` で抽出する。該当しない場合はユーザーに正しいブランチへ切り替えるよう案内して終了する。

2. `REPO`: 以下のコマンドで取得する（worktree環境でも動作する）：
   ```bash
   REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
   ```

**Spec・調査結果の取得**:

```bash
SPEC_CONTENT=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .body')
INVESTIGATION=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
  --jq '[.[] | select(.body | startswith("<!-- arc:design -->"))][0] | .body')
```

`<!-- arc:design -->` コメントが存在しない場合は、`/arc-designing` を先に実行するよう案内して終了。

### Step 2: 実装対象コードの詳細調査

`../../agents/implementation-analyst.md` を Read し、`[specの内容]` と `[docsの内容]` を実際の内容で置換して、Exploreエージェントを起動する。

docsの内容は `docs/` ディレクトリから対応ファイルを読み取る。

### Step 3: TDDタスク分解

調査結果をもとにタスクを分解する。各タスクは以下の規則に従う：

**TDD単位の原則**:
- `[test]` タスクは必ず対応する `[impl]` タスクの直前に置く
- 1つのテストファイル/テスト関数が1つの `[test]` タスク
- 各タスクは独立してコミット可能なサイズにする

**タスク例**:
```
- [ ] [test] UserService.createUser()のユニットテストを書く
- [ ] [impl] UserService.createUser()を実装する
- [ ] [test] POST /api/users のインテグレーションテストを書く
- [ ] [impl] UsersControllerにPOSTエンドポイントを追加する
```

`../../templates/tasks.md.template` を参照してタスクリストの初版を作成する。

### Step 3.5: Goal→タスクのトレーサビリティマトリックス作成

specのGoalおよびAcceptance Criteriaと、作成したタスクを紐付けるマトリックスを作成する：

```
| Goal / AC | 対応タスク |
|-----------|-----------|
| Goal 1: ○○できる | [test] UserService.createUser()テスト, [impl] UserService.createUser()実装 |
| AC-1: 〜の場合〜となること | [test] UserService.createUser()テスト |
```

**カバレッジチェック**: 全Goal・全ACに対応するタスクがあるか確認する。
対応するタスクがないGoal/ACがある場合は、対応する `[test]`/`[impl]` タスクを追加する。

このマトリックスはタスクコメントの先頭に含める。

### Step 4: 自律タスクレビューFBループ

以下の品質観点でタスクリストをレビューし、問題があれば修正する（最大3回繰り返す）：

1. **TDD対応**: 全ての `[impl]` タスクに対応する `[test]` タスクが直前にあるか
2. **Specカバレッジ**: 全てのGoal・ACに対応するタスクがトレーサビリティマトリックスに存在するか
3. **粒度の適切さ**: 1タスクが1〜2時間程度で完了できるサイズか
4. **依存関係の順序**: 依存するコードが先に実装されるよう順序付けられているか
5. **インフラ・設定**: DBマイグレーション・設定変更など非機能タスクが含まれているか

問題がある場合はタスクを修正・分割・統合・並び替えして再度チェックする。

**重要**: Goal/ACに対応するタスクがないことはFBループの最優先修正対象とする。

### Step 5: タスクリストをIssueコメントに投稿

品質基準を満たしたタスクリストをIssueコメントとして投稿する：

```bash
gh issue comment ${ISSUE_NUM} --body "$(cat <<'EOF'
<!-- arc:tasks -->
...タスクリストの内容...
EOF
)"
```

タスク一覧を出力して確認できるようにする。

### Step 6: 実装フェーズへ自動移行

人間の介入なしに実装フェーズへ移行する：

1. "タスク分解が完了しました。実装フェーズを開始します..." と表示する
2. **`Agent` ツールで sub-agent を spawn し、以下の prompt を渡す：**
   ```
   ISSUE_NUM=<N>、REPO=<owner/repo> のIssueに対して arc-implementing のワークフローを Step 1 から実行してください。ISSUE_NUM と REPO はこの prompt の値を使用すること。
   ```
   `<N>` と `<owner/repo>` は Step 1 で取得済みの値に置換する。

## Notes

- `plans/` ディレクトリは使用しない（タスクリストはIssueコメントで管理）
- タスク数は通常5〜15個が適切。20個を超える場合は機能分割を検討する
