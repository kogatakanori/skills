---
name: arc-specifying
description: Generates spec comment and docs from a GitHub Issue. Immediately after retrieving the issue, clarifies ambiguities via one-at-a-time questions before drafting. Runs parallel investigation agents, validates the spec with a self-review loop, posts as an Issue comment, and creates docs/ files. Fully stops after posting and waits for human approval. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Specifying

GitHub IssueからSpec（なぜ・意思決定）をIssueコメントとして投稿し、Docs（何を・最新仕様）を `docs/` に生成する。

## Workflow

### Step 0: Hooks設定チェックと自動セットアップ

#### 0-a: Readパーミッション設定チェック

arcプラグインはプロジェクト外のパスにあるため、プロジェクト設定（`.claude/settings.json`）では許可できない。グローバル設定（`~/.claude/settings.json`）の `permissions.allow` 配列にarcプラグインのルートパスを含むエントリ（`~/...arc.../**` のようなパターン）が存在しない場合、以下を自動セットアップする：

1. `Read` ツールでこのSKILL.mdを読み込んだ際の絶対パス（例: `/home/user/.../plugins/arc/skills/arc-specifying/SKILL.md`）から2階層上（`../..`）でarcのルートディレクトリを計算する
2. 計算した絶対パスを `~/` 形式に変換する（`$HOME` に一致するプレフィックス部分を `~/` に置換）
3. `~/.claude/settings.json`（存在しない場合は新規作成）の `permissions.allow` に `Read(~/path/to/arc/**)` を追加する（既存設定とマージ）

**`~/` 形式を使う理由**: グローバル設定では `~/` プレフィックス形式が推奨。絶対パス（`/home/user/...` のような形式）は移植性が低い。

**設定反映のタイミング**: グローバル設定の変更はClaude Codeの再起動後に有効になります。設定を書き換えた場合はユーザーに「設定を反映するにはClaude Codeを再起動してください」と案内し、再起動後に改めて `/arc-specifying` を実行するよう促す。

arcルートへのReadパーミッションが既に設定済みの場合はこのステップをスキップする。

#### 0-b: Hooks設定チェック

`.claude/settings.json` に `WorktreeCreate` / `WorktreeRemove` hookが未設定の場合、以下を自動セットアップする：

1. `.claude/hooks/` ディレクトリを作成
2. `../../templates/hooks/worktree-create.sh` を `.claude/hooks/worktree-create.sh` にコピー
3. `../../templates/hooks/worktree-remove.sh` を `.claude/hooks/worktree-remove.sh` にコピー
4. 両ファイルに実行権限を付与：`chmod +x .claude/hooks/worktree-*.sh`
5. `.claude/settings.json` に hooks エントリを追加（既存設定とマージ）：
   ```json
   {
     "hooks": {
       "WorktreeCreate": [{"type": "command", "command": "bash .claude/hooks/worktree-create.sh"}],
       "WorktreeRemove": [{"type": "command", "command": "bash .claude/hooks/worktree-remove.sh"}]
     }
   }
   ```

hookの内容：
- **worktree-create.sh**: worktree作成 → `.worktreeinclude` のファイルコピー → 依存関係インストール（コメントアウト済み）
- **worktree-remove.sh**: worktreeとブランチを削除

既に両hookが設定済みの場合はこのステップをスキップする。

### Step 1: Issue取得とworktree作成

1. Issue情報を取得する：
   ```bash
   gh issue view <N> --json title,body,labels,assignees,url
   ```

2. `EnterWorktree` ツールで `name=issue-<N>` を指定してworktreeを作成する
   - `.worktreeinclude` に記載されたファイルが自動コピーされる
   - `WorktreeCreate` hook が自動実行される
   - 現在のセッションがworktree内に切り替わる

### Step 1.5: Issue内容の解釈と事前質問ループ

Issueのタイトル・本文を即座に解釈し、**仕様作成に支障をきたす不明点・矛盾・漏れ**を検出する。

**質問が必要な場合**（以下に該当する点があれば）：
- 目的や成果が曖昧で複数の解釈が可能
- 複数の要件が矛盾している（例：「高速」かつ「精度重視」で両立不可能な場合）
- スコープが不明確（どこまでがこのIssueで対応するか）
- 技術的な前提条件が書かれていない

**質問ルール**：
- **1回の返答につき質問は1問のみ**。複数の疑問点があっても最も重要なものから1問ずつ
- 質問は「Yes/No」でなく、相手の意図・理由・優先度を引き出す開かれた問い
- 前の回答を踏まえて次の質問を決める。回答が明確なら次の疑問点へ
- **AI自律判断で終了**: 意図が十分に明確になったと判断したら質問を止める
- Issueの内容が明確で疑問点がない場合は質問せずに次へ進む（0問も可）

**質問例（実際は状況に応じた内容で）**：
> 「Issue #42の『リアルタイム同期機能』について確認です。クライアント間の同期はWebSocket接続を想定していますか？それとも定期的なポーリングで十分でしょうか？」

質問ループで得た回答を記録し、Step 2以降の調査とSpec草案作成に反映させる。

### Step 2: 並列コードベース調査

`../../agents/codebase-analyst.md` と `../../agents/architecture-analyst.md` を Read し、`[issueのタイトルと本文]`（Step 1.5の質問回答も含む）を実際の内容で置換して、2体のExploreエージェントを**同時に**起動する：

**Agent A（codebase-analyst）**: 類似機能・競合コード・踏襲すべきパターンを調査

**Agent B（architecture-analyst）**: アーキテクチャ制約・既存docs・テスト基盤を調査

### Step 3: Spec草案の作成

`../../templates/spec.md.template` を参照してSpecの草案を作成する（まだIssueには投稿しない）。

フォーマットは `references/spec-format.md` に従う。重要な点：
- **Context（Why）**: Issueの背景・解決する課題を明確に記述
- **Goal**: 「〜できる」「〜になる」形式で達成可能なアウトカムを記述
- **Acceptance Criteria**: 各Goalに対してテスト可能な受け入れ基準を記述（必須）
- **ADR**: なぜこのアーキテクチャを選択したか、代替案と具体的な却下理由を必ず含める
- **Non-Goals**: スコープを明確に定義する

### Step 3.5: Spec自律検証FBループ

`../../agents/spec-validator.md` を Read し、`[specの内容]` を草案の内容で置換してExploreエージェントを起動する。

**CRITICAL / HIGH** の指摘がある場合は草案を修正して再度検証する（最大3回繰り返す）。3回修正してもCRITICALが残る場合はユーザーに報告して判断を仰ぐ。

**MEDIUM** 以下の指摘のみの場合（または問題なしの場合）は次のステップへ進む。

### Step 3.6: Specコメント投稿

検証を通過したSpecをIssueにGitHubコメントとして投稿する：

```bash
gh issue comment <N> --body "$(cat <<'EOF'
<!-- arc:spec -->
...specの内容...
EOF
)"
```

### Step 4: Docsファイル生成

`../../templates/docs.md.template` を参照して `docs/<feature-name>.md` を生成する。

フォーマットは `references/docs-format.md` に従う。機能の概要・使い方・仕様を記述する（「何を・どう使うか」にフォーカス）。

### Step 5: コミットと完全停止（人間の承認を待つ）

```bash
git add docs/
git commit -m "spec: add docs for issue #NNN - <title>"
```

以下を表示してワークフローを**完全に停止する**：

```
✅ Specの品質検証が完了しました（spec-validatorサマリー: CRITICAL X件修正・HIGH Y件修正）

📋 IssueのSpecコメントを確認してください: <ISSUE_URL>

確認すべき点:
- Context（Why）: 解決したい課題が正確に記述されているか
- Goal: 達成したいアウトカムがこのPRのスコープと合っているか
- Acceptance Criteria: テスト可能な受け入れ基準が全Goalをカバーしているか
- ADR: 採用アプローチ・代替案・却下理由が納得できるか
- Non-Goals: 今回やらないことが明確になっているか

承認する場合: `/arc-investigating` を実行してください
修正が必要な場合: 会話でAIに修正箇所を伝えてください（以下のSpec修正フローが起動します）
```

**⚠️ 重要: このステップでワークフローは必ず終了する。ユーザーの明示的な指示なしに `/arc-investigating` を自動実行してはならない。**

## Spec修正フロー（会話でアドホックに起動）

ユーザーが「ここを直したい」「このGoalが違う」等と伝えてきた場合、以下のフローで対応する：

**フェーズ1: 意図の深掘り**
- Step 1.5と同じルールで、修正意図を理解するための質問を1問ずつ行う
- 「なぜそう思ったか」「どういう状態になれば理想か」「他に関連して変えたい点はあるか」等を引き出す
- AI自律判断で意図が明確になったら質問を止める

**フェーズ2: まとめた修正提案**
- 質問で得た情報を統合し、修正が必要な全箇所をまとめて提示する
- 変更前後の差分形式で提示する（変更しない部分は省略）

**フェーズ3: 確認と反映**
- ユーザーが承認したら、Issueコメントを更新する：
  ```bash
  SPEC_COMMENT_ID=$(gh api repos/${REPO}/issues/${ISSUE_NUM}/comments \
    --jq '[.[] | select(.body | startswith("<!-- arc:spec -->"))][0] | .id')
  gh api repos/${REPO}/issues/comments/${SPEC_COMMENT_ID} \
    -X PATCH -f body="<更新後のspec全文>"
  ```
- spec-validatorを再実行してCRITICAL/HIGHがないことを確認する
- `docs/` ファイルも必要に応じて更新してコミットする
- 再度 Step 5 の完全停止メッセージを表示して承認を待つ

## Notes

- specの内容はIssueコメントに保存される（`specs/` ディレクトリは使用しない）
- `docs/` ディレクトリが存在しない場合は作成する
- 既存の `docs/` ファイルがある場合は上書き更新する
- Acceptance Criteriaがない場合はspec-validatorがCRITICALを返すため、必ずStep 3.5でキャッチされる
- **arc-specifyingは後続フェーズに自動移行しない唯一のスキル**。Specは全開発の土台であるため、人間の確認・承認が必須
- Step 1.5の質問は「疑問解消のための最小限の質問」であって、全ての詳細をIssueから引き出そうとしない。必要最小限の明確化にとどめる
