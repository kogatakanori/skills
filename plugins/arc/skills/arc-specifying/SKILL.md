---
name: arc-specifying
description: Generates spec comment and docs from a GitHub Issue. Immediately after retrieving the issue, runs spec-validator to clarify Why, What, Constraints, and Domain Model one question at a time. Then runs parallel investigation agents and creates a spec built on clear, confirmed intent — without Scope, frameworks, or ADR (those belong to arc-designing). Fully stops after posting and waits for human approval. Part of the Arc SDLC workflow.
user_invocable: true
---

# Arc Specifying

GitHub IssueからSpec（なぜ・意思決定）をIssueコメントとして投稿し、Docs（何を・最新仕様）を `docs/` に生成する。

Specは全開発の土台。**最初に意図を明確にしてから書く**。

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

### Step 1.5: spec-validatorによる設計ツリーの明確化

Issue取得直後に `../../agents/spec-validator.md` を Read し、`[issueまたはspecの内容]` をIssueの全文（タイトル＋本文）で置換してExploreエージェントを起動する。

spec-validatorは：
1. 設計に必要な全決定事項をツリーとして展開する
2. コードベースを調査して自律的に答えられる項目を解決する
3. 残った確認事項を「推奨回答付き質問リスト」として返す

**spec-validatorの出力を受け取ったら、以下のフォーマットで1問ずつ聞く**：

```
Q1. [質問内容]

推奨: [spec-validatorが提案した推奨回答と根拠]
```

ユーザーは「はい（推奨通り）」「いいえ（○○にしたい）」「別の理由で〜」等と答える。
回答を受け取ったら次の質問へ進む。質問リストを全て消化するか、意図が十分に明確になったら次へ進む。

**「明確化の必要なし」と返ってきた場合**、または全質問を消化したら即座にStep 2へ。

得られた全ての回答（調査結果＋ユーザー確認結果）を「明確化されたコンテキスト」として記録し、Step 2以降に活用する。

**⚠️ 注意**: spec-validatorはWhy/What/Constraints/Domain Modelのみを明確化する。Scope（境界）・実装アプローチ・技術選択は一切聞かない。

### Step 2: Spec作成と投稿

Step 1.5の明確化されたコンテキストをもとに、`../../templates/spec.md.template` を参照しながらSpecを作成する。

重要な点：
- **Context（Why）**: Issueの背景・解決する課題を明確に記述
- **Users（誰が使うか）**: 役割・技術レベル・利用文脈を記述（spec-validatorのWho確認結果を反映）
- **Goal**: 「〜できる」「〜になる」形式で達成可能なアウトカムを記述
- **Use Cases**: GoalをどのようなシナリオでUserが利用するかを具体的に記述（UC-1, UC-2形式）
- **Acceptance Criteria**: 各Goalに対してビジネス視点での完了条件（Step 1.5の明確化で得た合意内容を反映）
- **Constraints**: ビジネスルール・不変条件・品質の下限（予算・法律・UX・応答速度など。HOWには踏み込まない）
- **Domain Model**: この機能で登場するエンティティ・概念の定義（spec-validatorの調査で確認した既存用語を反映）

**Specに含めないもの**: スコープ（In/Out of Scope）・実装アプローチ・技術選択・コードパターン → これらはarc-designingで決定する

作成したSpecをIssueにGitHubコメントとして投稿する：

```bash
gh issue comment <N> --body "$(cat <<'EOF'
<!-- arc:spec -->
...specの内容...
EOF
)"
```

### Step 3: Docsファイル生成

`../../templates/docs.md.template` を参照して `docs/<feature-name>.md` を生成する。

フォーマットは `references/docs-format.md` に従う。機能の概要・使い方・仕様を記述する（「何を・どう使うか」にフォーカス）。

### Step 4: コミットと完全停止（人間の承認を待つ）

```bash
git add docs/
git commit -m "spec: add docs for issue #NNN - <title>"
```

以下を表示してワークフローを**完全に停止する**：

```
📋 IssueのSpecコメントを確認してください: <ISSUE_URL>

確認すべき点:
- Context（Why）: 解決したい課題が正確に記述されているか
- Users: 誰が使うかが明確か（役割・技術レベル・文脈）
- Goal: 達成したいアウトカムが正確に表現されているか
- Use Cases: Goalを実現する具体的なシナリオが記述されているか
- Acceptance Criteria: ビジネス視点での完了条件が全Goalをカバーしているか
- Constraints: ビジネスルール・不変条件・品質の下限が網羅されているか
- Domain Model: 機能で使う用語・概念が明確に定義されているか

承認する場合: `/arc-designing` を実行してください
修正が必要な場合: 会話でAIに修正箇所を伝えてください（Spec修正フローが起動します）
```

**⚠️ 重要: このステップでワークフローは必ず終了する。ユーザーの明示的な指示なしに `/arc-designing` を自動実行してはならない。**

## Spec修正フロー（会話でアドホックに起動）

ユーザーが「ここを直したい」「このGoalが違う」等と伝えてきた場合、以下のフローで対応する：

**フェーズ1: 修正意図の明確化（spec-validatorを使う）**

- `../../agents/spec-validator.md` を Read し、`[issueまたはspecの内容]` を「現在のspec内容 + ユーザーの修正コメント」に置換してExploreエージェントを起動する
- spec-validatorが設計ツリーを再展開し、修正に関わる決定事項を特定・調査して残った質問リストを返す
- Step 1.5と同じフォーマット（推奨回答付き）で1問ずつ聞く
- 修正意図が明確になったら次のフェーズへ

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
- `docs/` ファイルも必要に応じて更新してコミットする
- 再度 Step 5 の完全停止メッセージを表示して承認を待つ

## Notes

- specの内容はIssueコメントに保存される（`specs/` ディレクトリは使用しない）
- `docs/` ディレクトリが存在しない場合は作成する
- 既存の `docs/` ファイルがある場合は上書き更新する
- **arc-specifyingは後続フェーズに自動移行しない唯一のスキル**。Specは全開発の土台であるため、人間の確認・承認が必須
- spec-validatorが「明確化の必要なし」と返した場合でも、Issueが短すぎる・抽象的すぎると感じたら追加で確認してよい
