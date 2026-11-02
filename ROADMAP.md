# 追加予定の機能 / Roadmap

日本語 | [English](#english)

公開後に順番に追加していく予定の機能です。実装したらチェックを付け、バージョンと日付を書き足します。予定は変わることがあります。

## 公開済み

- [x] v0.1.0（2026-11-02）：見本画像からコマ割りを選ぶ（196種類・2〜6コマ）、コマ入力ノードの自動増減と入力の退避・復元、共通の人物2人、1コマ2発言、空のコマ枠モード

## 予定

### 自作のコマ割り

- [ ] **自作コマ割りノード（最小版）**：各コマを「左・上・右・下（%）」で1行ずつ書くだけで、同梱以外のコマ割りをその場で使えるようにします。重なり・はみ出しは自動で検査します。
- [ ] **自作コマ割りの保存**：自作した配置を ComfyUI の `user` フォルダへ保存し、次回から選び直せるようにします。ノードを更新しても消えません。
- [ ] **自作コマ割りの見本を一覧に追加**：MOSS の「空のコマ枠」モードで見本を生成し、選択画面に「自作」として並べます。見本はモデル出力そのままを使います。

### 表現の幅

- [ ] **共通の人物を3人以上に**：今は2人までの人物設定を増やせるようにします。
- [ ] **1コマのセリフを3つ以上に**：今は1コマ2発言までの上限を広げます。
- [ ] **人物と吹き出しの位置指定**：今はコマ内の固定配置です。左右・上下などを選べるようにします。

### 使いやすさ

- [ ] **コマ入力ノードの名前に位置を表示**：今は「1コマ目（1コマ目）」と表示される配置があります。「右上」「下段」などの位置名を出します。
- [ ] **英語の画面表示**：ノード名・入力欄・選択画面を英語でも使えるようにします。
- [ ] **Comfy Registry への登録**：ComfyUI-Manager から検索して導入できるようにします。

---

<a id="english"></a>

# Roadmap

[日本語](#追加予定の機能--roadmap) | English

Features planned after the initial release. Each item will be checked off with its version and date when it ships. Plans may change.

## Released

- [x] v0.1.0 (2026-11-02): pick a layout from preview images (196 layouts, 2–6 panels), automatic panel node add/remove with input stash and restore, two shared characters, two lines per panel, empty panel frame mode

## Planned

### Custom layouts

- [ ] **Custom layout node (minimal)**: describe each panel as one line of left, top, right, bottom (%) to use layouts beyond the bundled set. Overlaps and out-of-bounds panels are checked automatically.
- [ ] **Save custom layouts**: store your layouts in ComfyUI's `user` folder so you can pick them again later. They survive node updates.
- [ ] **Previews for custom layouts**: generate a preview with MOSS's empty panel frame mode and list it in the picker as "custom". The preview is the model output as is.

### More expression

- [ ] **Three or more shared characters**: raise the current limit of two characters.
- [ ] **Three or more lines per panel**: raise the current limit of two lines per panel.
- [ ] **Character and balloon placement**: choose left/right or top/bottom instead of the current fixed positions.

### Usability

- [ ] **Show panel positions in node titles**: some layouts currently show titles like "1コマ目（1コマ目）". Show positions such as "top right" or "bottom row" instead.
- [ ] **English UI**: make node names, input fields, and the picker available in English.
- [ ] **Comfy Registry listing**: make the node searchable and installable from ComfyUI-Manager.
