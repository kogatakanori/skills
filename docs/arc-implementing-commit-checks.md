---
title: arc-implementing の commit 前 type-check・test チェック
issue: "#2"
last_updated: 2026-06-07
---

# arc-implementing の commit 前 type-check・test チェック

## 概要

`/arc-implementing` の③・⑨ステップ（各タスクの commit 直前）に type-check と test の実行を追加する。PostToolUse hook（lint のみ）との役割分担を保ちながら、commit 単位で型エラー・テスト失敗を検出できるようにする。

## 使い方

特別な設定は不要。`/arc-implementing` を実行すると、各タスクの commit 直前に自動で type-check・test が実行される。

コマンドはプロジェクトの設定ファイルから自動検出される：
- `package.json` の `scripts` に `type-check` / `typecheck` があればそれを使用
- 見つからない場合は `npx --no-install tsc --noEmit` を試みる（ネットワークインストールは行わない）
- いずれも存在しない場合はスキップ（TypeScript を使わないプロジェクトは対象外）
- test コマンドは `package.json` / `Makefile` / `pyproject.toml` から自動検出。検出できない場合はスキップ

## 仕様

### hook との役割分担

| タイミング | 実行内容 | 仕組み |
|---|---|---|
| Write/Edit 後（毎回） | lint（ESLint / ruff / shellcheck）| PostToolUse hook |
| commit 直前（タスク完了時）| type-check・test | SKILL.md ワークフロー |

### ③ステップ（testタスクのcommit前）

1. type-check を実行（未実装シンボル由来の型エラーは許容。それ以外のエラーはテストコードを修正。最大2回、解消しない場合はユーザーに報告）
2. 検出したテストコマンドを実行して RED になることを最終確認する（誤って GREEN の場合はテストを修正）
3. エラー・予期しない通過がなければ commit する

### ⑨ステップ（implタスクのcommit前）

1. type-check を実行（エラーがあれば実装コードを修正。最大2回、解消しない場合はユーザーに報告）
2. 検出したテストコマンドを実行して全テストが GREEN になることを最終確認する
3. 全てパスすれば commit する

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `plugins/arc/skills/arc-implementing/SKILL.md` | ③・⑨ステップに type-check・test 実行ステップを追加、Notes に type-check コマンド検出ロジックを追記 |

## ADR

この機能の設計判断・代替案の検討・採用理由は [Issue #2](https://github.com/kogatakanori/skills/issues/2) を参照。
