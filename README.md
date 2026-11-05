# MOSS漫画コマ割りデータセット

日本語 | [English](#english)

ComfyUIの中で漫画のコマ割りを画像から選び、人物・場面・セリフを専用欄に入力してMOSSへ渡すカスタムノードです。配置ごとのワークフローのダウンロードや、JSON・座標の手書きは不要です。

![ComfyUI内の選択画面](docs/picker.jpg)

https://github.com/user-attachments/assets/05a9d952-7a60-448c-94f5-e35ae3029449

[デモ動画（mp4・30秒）](docs/demo.mp4)：ComfyUIで四コマを選び、人物とセリフを入力して生成するまでの実際の操作を録画したものです。操作待ち・生成待ちを短縮し、上端に操作案内の字幕を入れています。漫画の画像には手を加えていません。

## できること

- 見本の画像からコマ割りを選択。2〜6コマに対応します。
- コマ数・種類・名前で絞り込み、お気に入りを登録できます。
- 配置を選ぶと、コマ入力ノードと接続が自動で増減します。
- 減らしたコマの入力を退避し、コマ数を戻すと復元します。人物・セリフ・モデル・サンプラー・シード設定を維持します。
- 人物の外見と場面は英語で入力し、セリフは描かせたい言語のまま渡します。翻訳や追加のLLMは使いません。
- 見本・配置情報を同梱しているため、導入後のカタログ閲覧に外部サービスへの接続は不要です。
- ComfyUIの表示言語が日本語ならノード名・入力欄・選択肢・選択画面を日本語で、それ以外の言語なら英語で表示します。どちらの言語で保存したワークフローもそのまま開けます。
- 入力に誤りがあると、どの欄をどう直せばよいかを日本語と英語で示して止まります（例: 登場人物にいない人物を話者に選んだとき）。
- 1人・2人・3人向けの構図見本120種類から、コマごとにカメラ構図を選べます。
- 共通の人物は最大3人。1コマに最大3人・3発言を指定できます。
- 人物画像から外見を英語の文章へ抽出して入力できます。MOSSのテキストエンコーダー（Qwen）を共用し、追加のモデルは不要です。
- 基本の漫画生成から構図指定・人物画像の利用まで、すぐ試せるサンプルワークフローを同梱しています（[選び方](#サンプルワークフローの選び方)）。

## 導入

1. このリポジトリを `ComfyUI/custom_nodes/ComfyUI-MossPanelDataset` に配置してください。ZIPの場合は、展開したフォルダの直下に `__init__.py` がある形にします。`web` だけ、またはノードのPythonファイルだけをコピーせず、`data` と `images` も一緒に置いてください。
2. 下記のMOSS対応ComfyUIとモデルを用意してください。このノード専用の追加パッケージやインストールスクリプトはありません。
3. ComfyUIを再起動し、ブラウザーを再読み込みしてください。
4. 最初の一度だけ [make_manga.json](example_workflows/make_manga.json) をComfyUIへドラッグ＆ドロップして開き、ComfyUI側へ保存してください。ComfyUIの「テンプレート」画面にも `ComfyUI-MossPanelDataset` の `make_manga` として表示されるので、そこから開くこともできます。以後はそのワークフローを開いて配置を選び直せます。

旧試作版を導入済みの場合は、同じノードのフォルダやジャンクションを重複して置かないでください。配布版のコマ割りJSONは同梱196種類だけを収録しており、除外した配置や旧試作専用の配置を使うワークフローは選択し直す必要があります。

Gitを使う場合は、`ComfyUI/custom_nodes` で次を実行します。Registryの0.1.0はFlaggedで、0.1.1は未公開です。状態は [公開API](https://api.comfy.org/nodes/comfyui-moss-panel-dataset/versions?include_status_reason=true) で確認できます。

```text
git clone https://github.com/sepiablue-ai/ComfyUI-MossPanelDataset.git
```

## 必要な環境とモデル

Python 3.10以降と、MOSS-Imageのネイティブ対応を含むComfyUIが必要です。動作確認はComfyUI v0.42.0（Python 3.13）で行いました。`CLIPLoader` の種類に `moss_image` がなく、`EmptyFlux2LatentImage` ノードもない古いComfyUIでは動きません。その場合はComfyUIを更新してください。モデル重みは同梱していません。[MOSS公式のComfyUI案内](https://github.com/OpenMOSS/MOSS-Image/blob/main/comfyui/README.md)と[Comfy-Orgのモデル配布ページ](https://huggingface.co/Comfy-Org/MOSS-Image)を参照してください。

同梱ワークフローで指定しているファイルは次の3つです。

| 配置先 | ファイル名 |
| --- | --- |
| `ComfyUI/models/diffusion_models/` | `moss_image_sft_int8_convrot.safetensors` |
| `ComfyUI/models/text_encoders/` | `qwen3.5_9b_int8_convrot.safetensors` |
| `ComfyUI/models/vae/` | `flux2-vae.safetensors` |

モデル選択欄で各ファイルを確認してください。別名やサブフォルダへ置いた場合は、ローダーの選択を変更します。`CLIPLoader` の種類は `moss_image` です。重みを自動でダウンロードする機能はありません。

元のデータセット生成はWindows・RTX 3060 12GBで実施しました。同梱ワークフローは1024×1536、25ステップ、CFG 2.5、`er_sde` / `simple`、DMD LoRAなしです。他のGPU・OSでの実生成は未確認です。

## 使い方

1. 「画像からコマ割りを選ぶ」を押し、見本画像を選びます。初期表示は通常の直線配置です。「斜め」「特殊」へ切り替えることもできます。
2. 「共通の人物設定」で、人物1・人物2の名前と外見を入力します。外見は英語で記述します。名前は管理用で、日本語でも構いません。
3. 各コマの「場面」を英語で入力し、「登場人物」を選びます。
4. 「話者1」と「セリフ1」を入力します。本文だけ入力し、外側のかぎ括弧やJSONは不要です。日本語なら日本語、英語なら英語のまま使います。2発言目は話者2・セリフ2を使います。
5. 無言なら話者を「セリフなし」にし、本文を空欄にしてください。「人物なし」なら背景だけを指定できます。
6. ComfyUIの「実行する」を押します。

空枠だけを生成する場合は、選択ノードの「生成内容」を「空のコマ枠」に変えます。人物・場面・セリフをプロンプトから除き、枠だけをMOSSに描かせます。

### プロンプトを確認・編集する（任意）

実際にMOSSへ渡すプロンプトを見たいときは、「MOSSプロンプトを確認・編集」ノードを「コマ割りを選ぶ」の `MOSS用プロンプト` 出力と `CLIPTextEncode` の間に挟みます。標準の `make_manga.json` には入れていません。最初から挟んだ [make_manga_edit_prompt.json](example_workflows/make_manga_edit_prompt.json)（テンプレート画面では `make_manga_edit_prompt`）も同梱しているので、プロンプトを触りたいときはこちらを開いてください。

1. 「使うプロンプト」を「受け取ったまま」にして実行すると、下の「受け取ったプロンプト」欄に実際のプロンプトを表示します。編集欄が空なら、同じ内容が編集欄にも入ります。
2. 編集欄で文を直し、「使うプロンプト」を「編集した文」に変えて実行すると、直した内容をMOSSへ渡します。
3. 人物やセリフを変えて作り直したいときは、「受け取ったまま」に戻すか、「受け取ったプロンプトを編集欄へコピー」で編集欄を最新の内容に置き換えます。手で直した編集欄は自動では上書きしません。

編集欄はJSONとして読める形にしてください。括弧やカンマが壊れている場合は、実行時に行と文字の位置を示して止まります。

人物やセリフなどの作業内容と、退避したコマの入力は、通常のComfyUIワークフローとして保存してください。お気に入りはブラウザーの保存領域に記録します。別のブラウザーには自動で移らず、サイトデータを削除すると消えます。同梱JSONへの書き込みは行いません。

## サンプルワークフローの選び方

`example_workflows` に、基本の漫画生成から構図指定・人物画像の利用までのサンプルを同梱しています。初めて使う場合は **[make_manga.json](example_workflows/make_manga.json)** から始めてください。

| ファイル | できること | 使う場面 |
| --- | --- | --- |
| [make_manga.json](example_workflows/make_manga.json) | 人物の外見・各コマの場面・セリフを文章で入力して漫画を生成します。初期設定は2人の人物による4コマで、コマごとの構図選択ノードはありません。 | まず基本操作を試すとき。コマ割りと内容を自分で設定して漫画を作るとき。 |
| [make_manga_edit_prompt.json](example_workflows/make_manga_edit_prompt.json) | 基本ワークフローに「MOSSプロンプトを確認・編集」を追加したものです。自動で組み立てたプロンプトを確認し、編集した文へ切り替えて生成できます。 | MOSSへ渡す内容を確認したり、プロンプトを直接調整したりするとき。編集欄は有効なJSONで記述します。 |
| [composition_duo.json](example_workflows/composition_duo.json) | 2人の会話を4コマで生成します。各コマに構図選択ノードを接続し、正面の掛け合い・横並び・机越し・近距離の言い合いを設定済みです。 | 2人の位置関係やカメラの構図を、見本から選んで指定したいとき。 |
| [composition_1to3.json](example_workflows/composition_1to3.json) | 3人の共通人物設定を使い、1人・2人・3人が登場する3コマを生成します。人数に合わせた構図と、最大3人分のセリフを接続済みです。 | コマごとに登場人数を変えたいとき。3人目の人物や3発言の指定方法を確認するとき。 |
| [composition_character_images.json](example_workflows/composition_character_images.json) | 人物画像から外見を英語の文章へ抽出し、構図つきの3コマを生成します。「画像から抽出」「画像から抽出＋文章で補足」「文章のみ」の3方式を設定済みです。 | 参考画像をもとに人物の外見を入力したいとき。画像の読み込み先を自分の画像に変更してください。 |
| [composition_duo.api.json](example_workflows/composition_duo.api.json) | `composition_duo.json` のAPI形式です。2人・4コマの構図つき生成を、スクリプトなどからComfyUIのAPIへ送るためのノード定義を収録しています。 | APIから実行するとき。画面でノードを操作する場合は `composition_duo.json` を使ってください。 |

API形式以外の5ファイルは、ComfyUIへドラッグ＆ドロップして開けます。必要なモデルと配置先は [必要な環境とモデル](#必要な環境とモデル) を参照してください。

人物画像を使うサンプルの参考画像は同梱していません。「文章のみ」の人物3は設定方法の見本で、初期状態の各コマには登場しません。また、構図の見本や人物画像そのものをMOSSの参照画像として渡す方式ではなく、構図の文章・領域指定や、画像から抽出した外見文で誘導します。

## 構図テンプレートの追加

「構図を選ぶ（見本画像）」ノードを追加しました。「画像から構図を選ぶ」で一覧を開き、人数・カテゴリ・名前・英語プロンプトによる検索と、お気に入りによる絞り込みができます。お気に入りは使用中のブラウザーに保存されます。

1. [構図つきサンプル](example_workflows/composition_duo.json) を開きます。
2. 構図選択ノードで見本を選び、出力「コマに接続する構図」を各「コマの内容」ノードの任意入力「構図」へ接続します。
3. 共通の人物設定、各コマの場面・セリフ、コマ割りを入力して生成します。場面と外見は英語、セリフは描かせたい言語で入力します。

構図の英語プロンプトを場面へ追記し、見本の人物領域を各コマの内側領域へ比率に応じて割り当てます。選んだ登場人物を番号順に構図へ割り当て、話す順番を変えても人物位置は入れ替わりません。接続しなければ従来の処理になります。見本と登場人物の人数を合わせてください。

構図見本は1人40種類・2人40種類・3人40種類の計120種類です。既存の2人20種類はID・名称を維持して追加しました。構図の英語プロンプトは、カメラ・寄り引き・人物の配置・体と顔の向き・姿勢・配置用の家具だけを指定します。表情・感情・会話の動作・小物・光は指定しないので、場面の文で自由に指定できます。見本画像は、MOSSが実際に出力した正方形1024×1024のPNGを、配布容量を抑えるため非可逆WebP（品質90）へ変換したものです（120枚で約178MBから約25MBへ）。変換による圧縮で細部は元のPNGと完全には一致しません。変換以外の処理（文字入れ、合成、縮小、切り抜き）は行っていません。PNGに埋め込まれていた生成時の英語プロンプト・シード・モデル・条件と、人物領域・元PNGのSHA256は `data/compositions.json` に収録します。肩越し・顔アップ・全身・俯瞰・あおりなどで分類します。構図一覧には見本画像・名前・人数・カテゴリ・お気に入りを表示し、品質判定は検証記録で確認できます。不一致や人物増加を画像修復で補うことはしません。

同じ構図を縦長・横長のコマにも使用できます。画像そのものを参照入力に渡す方式ではなく、英語プロンプトと領域指定による誘導です。見本との完全一致、特殊形状への追従、文字や人物の正確性は保証しません。画像の合成・文字修復・枠線補修は行いません。

## 3人までの人物指定

「共通の人物設定」の「人物3_名前」「人物3_外見」を両方入力すると3人目を使えます。両方空欄なら従来の2人設定です。各コマの「登場人物」で1〜3人の任意の組み合わせを選び、「話者1〜3」「セリフ1〜3」で最大3発言を指定できます。人物3を話者に選ぶ場合も、そのコマの登場人物に含めてください。

[1〜3人の混在サンプル](example_workflows/composition_1to3.json) では人物設定・構図・セリフを接続済みです。吹き出し領域は1発言なら上部中央〜右、2発言なら右上・左上、3発言なら右上・中央上・左上に指定します。構図の空き領域を自動推論する機能ではありません。

## 人物画像から外見を入力する

https://github.com/user-attachments/assets/be8c36de-7fbd-4c9c-9487-b3eec56cc5ca

[デモ動画（mp4・30秒）](docs/demo_character_images.mp4)：人物画像を2枚読み込み、各コマの構図とコマ割りを一覧から選んで生成するまでの実際の操作を録画したものです。操作と生成待ちを早送りし、実行ボタンの場面だけ拡大しています。字幕は入れていません。最後に入力画像・コマ割り・構図・生成結果を並べて表示します。漫画の画像には手を加えていません。

[画像から外見を抽出するサンプル](example_workflows/composition_character_images.json) を開き、2つの「画像を読み込む」で自分の人物画像を選んでください。サンプル内のファイル名は検証用のもので、参考画像は同梱していません。

「人物の外見（画像／文章）」には3つの指定方法があります。

- **文章のみ**：外見プロンプトをそのまま渡します。Qwen・参考画像の接続は不要です。接続されていても遅延評価でモデルや画像の処理は実行しません。
- **画像から抽出**：人物画像から、見た目の年代・顔立ち・体格・髪型・服装・装飾などを英語の外見文へ変換します。年代は別の短い質問で「子ども・10代前半・10代後半・若い大人・30代・中年・高齢」から1つ選ばせ、`Apparent age group: …` として文の先頭に付けます。
- **画像から抽出＋文章で補足**：抽出文へ、入力した補足文を追記します。補足文の翻訳は行いません。

MOSSで使う `CLIPLoader` の `type=moss_image` と `qwen3.5_9b_int8_convrot.safetensors` を共用できます。別のVLMやP-H3のモデル、追加のPythonパッケージは不要です。動作確認環境はComfyUI 0.42.0です。

外見ノードの「人物設定に渡す外見」を、共通の人物設定の各「人物N_外見」へ接続します。サンプルは接続済みです。自分で組む場合は外見欄を入力へ変換して接続してください。人物1〜3でそれぞれ画像・文章の方法を選べます。従来の文章入力だけのワークフローもそのまま使えます。

結果の外見文はノード内へ表示します。「結果を文章欄へコピー（文章のみに切替）」を押すと、手直しした文章を再利用できます。参考画像を含む上流ノードを外して保存すれば、別の環境でも画像ファイルに依存せず文章だけで使えます。通常のComfyUIキャッシュも利用し、構図やシードだけを変更しても外見抽出は再実行されません。

解析時だけ、必要なら長辺768pxまで比率を維持して縮小します。元画像の画素は変更しません。1ノードにつき画像は1枚で、人物が複数いる画像では主に手前の大きい人物を説明する指示です。人物が1人の参考画像を推奨します。

画像を外見文へ変換してMOSSへ渡す方式で、参照画像そのものを描画モデルへ渡す方式ではありません。見えていない服の推測や、画風説明が抽出文に混ざることがあります。正確な人物同一性は保証しません。漫画の顔は年代にかかわらず若く描かれることが多く、年代の判定は外れることがあります。外れたときは「結果を文章欄へコピー」で年代を書き直してください。

漫画ページの生成文は、以前は全員に大人の体型（`natural adult proportions`）を指定していました。現在は、各人物の外見文に書かれた年代と体型で描くよう指定します。外見文に年代を書かない場合、同じシードでも以前と結果が変わることがあります。

## 同梱するコマ割り

通常の追加100種類と、先行100種類から近似重複候補4種類を除いた96種類の、計196種類です。見本画像は合計約2.8MBです。

| コマ数 | 通常の追加分 | 先行分 | 合計 |
| --- | ---: | ---: | ---: |
| 2 | 20 | 18 | 38 |
| 3 | 20 | 19 | 39 |
| 4 | 20 | 20 | 40 |
| 5 | 20 | 20 | 40 |
| 6 | 20 | 19 | 39 |
| 合計 | 100 | 96 | 196 |

すべての見本はMOSSが生成した画像です。配布容量を抑えるため、元のPNG（1024×1536）を非可逆WebP（品質90）へ変換しました。変換による圧縮で、細部や白地のノイズは元のPNGと完全には一致しません。変換以外の処理（文字入れ、合成、枠線の描き直し、縮小、切り抜き）は行っていません。ファイル名は配置IDへそろえています。元PNGに含まれていた生成時のプロンプト情報は、WebPには引き継いでいません。不要な生成履歴・失敗画像・個別プロンプトファイルは同梱していません。

コマ数は閉じた白い領域の数で自動検査しました。近似重複は閉領域の矩形座標差（最大2％・平均0.8％以内）と、許容幅付き枠線一致率95％以上から検出しています。「似ていない」「構図が正確」と人間が全件確認したものではありません。

## 制限

今後追加する予定の機能は [ROADMAP.md](ROADMAP.md) にまとめています。

- 共通人物は最大3人、1コマにつき最大3人・3発言です。人物3は名前と外見の入力が必要です。4人以上には対応していません。
- コマ入力の自動増減は、このノードと `MossMangaPanel` の組み合わせで動きます。別ノードへも接続されているコマ入力は削除しません。
- 座標と説明でモデルに指示する方式です。見本画像を直接コピーする方式ではなく、生成のたびにコマの形・比率・数が変わることがあります。
- 斜め線や特殊形状は説明文でも指示します。モデルに渡す領域情報は矩形であり、多角形の輪郭を強制するマスクではありません。
- 人物と吹き出しはコマ内の簡単な固定配置です。場面に応じた最適な配置や吹き出しの尻尾を推論する機能はありません。
- 文字の誤字・崩れ、人物の混線、コマ数の増減を保証して防ぐものではありません。生成画像に文字や枠を重ねて補修する処理はありません。
- 導入時のモデルダウンロードとComfyUI本体の環境設定は利用者側で行います。

## 更新と検査

フォルダを更新後、ComfyUIを再起動してブラウザーを再読み込みしてください。人物・セリフを同梱JSONに保存しないため、ノードの更新と利用者のワークフロー保存は別です。お気に入りは配置IDを使い、ワークフローの選択値は配置名を使います。今後の更新では既存IDと配置名を維持します。

0.1.1ではコマ割り196種類も `data/layouts.json` から読み取ります。利用時のデータベース接続は不要です。実験用SQLiteと生成履歴は配布物に含めません。ID・名称・配置・構図・見本画像は維持しています。

構図見本のうち46種類は、英語プロンプトに表情・感情・会話の動作・小物・光の指定が入っていたため、構図だけの文に直して見本画像をMOSSで再生成しました。ID・名称・人物領域は変わらないので、保存済みワークフローはそのまま開けます。接続した構図の文が変わるため、同じシードでも生成結果は以前と変わります。

Registry向け配布では `.comfyignore` によりテストと開発用ファイルを除外します。テストはGitHubのソースには残します。

開発時は、このフォルダで次を実行できます。既存のComfyUI用Pythonなど、`aiohttp` を利用できる環境を使ってください。Node.jsは画面の増減処理の検査にだけ使用し、通常の利用には不要です。

```text
python -m unittest discover -s tests
node tests/test_picker_state.mjs
```

## ライセンスと出典

本プロジェクト独自のコード・配置データ・同梱見本画像は、MITライセンスで配布します。全文は [LICENSE](LICENSE) を参照してください。

見本画像はMOSS-Imageによる生成物です。MOSS-Imageのモデル重み（Comfy-Org配布版）とMOSS-Image公式リポジトリのコードは Apache License 2.0 で公開されています（2026年11月2日に各配布ページで確認）。モデルの重み・ComfyUI・その他の第三者の実装は本リポジトリに含まず、本リポジトリのライセンスの対象でもありません。利用時はそれぞれの配布元のライセンスを確認してください。

- [MOSS-Image公式リポジトリ](https://github.com/OpenMOSS/MOSS-Image)
- [Comfy-OrgのMOSS-Imageモデル](https://huggingface.co/Comfy-Org/MOSS-Image)
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI)

---

<a id="english"></a>

# MOSS Manga Panel Layout Dataset

[日本語](#moss漫画コマ割りデータセット) | English

A ComfyUI custom node for MOSS-Image. Pick a manga panel layout from preview images inside ComfyUI, then enter characters, scenes, and dialogue in dedicated fields. The node builds the MOSS prompt for you, so you do not need to download a workflow per layout or write JSON and coordinates by hand.

![Layout picker in ComfyUI](docs/picker.jpg)

https://github.com/user-attachments/assets/05a9d952-7a60-448c-94f5-e35ae3029449

[Demo video (mp4, 30 s)](docs/demo.mp4): a real screen recording of choosing a four-panel layout, entering characters and dialogue, and generating the page in ComfyUI. Waiting time is shortened and Japanese operation captions are shown at the top. The manga image itself is not edited.

The node UI is shown in English unless ComfyUI's language is set to Japanese. The steps below give the Japanese label in 「」 followed by the English label in parentheses, and the table in [Node labels](#node-labels) lists both.

## Features

- Choose a panel layout from preview images. Layouts with 2 to 6 panels are supported.
- Filter by panel count, type, and name, and mark favorites.
- When you pick a layout, the panel input nodes and their connections are added or removed automatically.
- Inputs of removed panels are stashed and restored when you increase the panel count again. Characters, dialogue, model, sampler, and seed settings are kept.
- Write character appearance and scenes in English. Dialogue is passed through in whatever language you want rendered. No translation or extra LLM is used.
- Previews and layout data are bundled, so browsing the catalog needs no external service.
- Node names, input fields, choices, and picker dialogs follow ComfyUI's display language: Japanese when it is set to Japanese, English otherwise. Workflows saved in either language open as is.
- Input mistakes stop the run with a message in Japanese and English that names the field and how to fix it (for example, a speaker who is not one of the panel's characters).
- Choose a camera composition for each panel from 120 composition previews for one, two, or three characters.
- Up to three shared characters, with up to three characters and three lines per panel.
- Extract a character's appearance from a reference image as English text. It reuses the MOSS text encoder (Qwen), so no extra model is needed.
- Sample workflows are included, from basic manga generation to compositions and character images ([which one to use](#choosing-a-sample-workflow)).

## Installation

1. Place this repository at `ComfyUI/custom_nodes/ComfyUI-MossPanelDataset`. If you use a ZIP, make sure `__init__.py` is directly inside the extracted folder. Copy the whole folder, including `data` and `images`, not just `web` or the Python files.
2. Prepare a MOSS-capable ComfyUI and the models listed below. This node needs no extra Python packages or install scripts.
3. Restart ComfyUI and reload the browser page.
4. Open [make_manga.json](example_workflows/make_manga.json) once by dragging it into ComfyUI, then save it in ComfyUI. It also appears as `make_manga` under `ComfyUI-MossPanelDataset` in ComfyUI's Templates browser. After that, open the saved workflow and pick layouts from it.

If you installed an earlier prototype, do not keep a second copy or junction of the same node. The bundled layout JSON contains only the 196 layouts listed below; workflows that used excluded or prototype-only layouts need a new selection.

To install with Git, run the following in `ComfyUI/custom_nodes`. On the Comfy Registry, version 0.1.0 is Flagged and 0.1.1 is not yet published. You can check the status in the [public API](https://api.comfy.org/nodes/comfyui-moss-panel-dataset/versions?include_status_reason=true).

```text
git clone https://github.com/sepiablue-ai/ComfyUI-MossPanelDataset.git
```

## Requirements and models

Python 3.10 or later and a ComfyUI build with native MOSS-Image support are required. Tested with ComfyUI v0.42.0 (Python 3.13). Older ComfyUI versions without the `moss_image` type in `CLIPLoader` or without the `EmptyFlux2LatentImage` node will not work; update ComfyUI in that case. Model weights are not included. See the [official MOSS ComfyUI guide](https://github.com/OpenMOSS/MOSS-Image/blob/main/comfyui/README.md) and the [Comfy-Org model page](https://huggingface.co/Comfy-Org/MOSS-Image).

The bundled workflow uses these three files:

| Folder | File name |
| --- | --- |
| `ComfyUI/models/diffusion_models/` | `moss_image_sft_int8_convrot.safetensors` |
| `ComfyUI/models/text_encoders/` | `qwen3.5_9b_int8_convrot.safetensors` |
| `ComfyUI/models/vae/` | `flux2-vae.safetensors` |

Check each file in the loader dropdowns. If you saved them under another name or subfolder, change the loader selection. The `CLIPLoader` type is `moss_image`. Weights are not downloaded automatically.

The original dataset was generated on Windows with an RTX 3060 12GB. The bundled workflow uses 1024×1536, 25 steps, CFG 2.5, `er_sde` / `simple`, and no DMD LoRA. Generation on other GPUs and operating systems has not been tested.

## Usage

1. Press 「画像からコマ割りを選ぶ」 (Choose a layout from images) and click a preview. The default view shows standard straight layouts; you can switch the type to 「斜め」 (diagonal) or 「特殊」 (special).
2. In 「共通の人物設定」 (Shared characters), enter the name and appearance of character 1 and character 2. Write appearance in English. Names are for your own reference and can be in any language.
3. In each panel node, write the 「場面」 (scene) in English and choose the 「登場人物」 (characters in the panel).
4. Choose 「話者1」 (speaker 1) and type 「セリフ1」 (line 1). Enter only the text, without surrounding quotation brackets or JSON. Japanese stays Japanese and English stays English. Use speaker 2 / line 2 for a second line.
5. For a silent panel, set the speaker to 「セリフなし」 (no dialogue) and leave the text empty. Choose 「人物なし」 (no characters) to describe a background only.
6. Press the Run button in ComfyUI.

To generate empty panel frames only, set 「生成内容」 (output) on the layout node to 「空のコマ枠」 (empty panel frames). Characters, scenes, and dialogue are then left out of the prompt, and MOSS draws only the frames.

### Viewing and editing the prompt (optional)

To see the exact prompt sent to MOSS, insert the 「MOSSプロンプトを確認・編集」 (View and edit MOSS prompt) node between the layout node's `MOSS用プロンプト` output and `CLIPTextEncode`. It is not part of `make_manga.json`. [make_manga_edit_prompt.json](example_workflows/make_manga_edit_prompt.json) (`make_manga_edit_prompt` in the Templates browser) already includes it, so open that one when you want to work with the prompt.

1. With 「使うプロンプト」 (Prompt to use) set to 「受け取ったまま」 (as received), run the workflow. The 「受け取ったプロンプト」 (Received prompt) box shows the actual prompt. If the edit box is empty, the same text is copied into it.
2. Edit the text in the edit box, switch to 「編集した文」 (edited text), and run again to send your edited prompt to MOSS.
3. After changing characters or dialogue, switch back to 「受け取ったまま」, or press 「受け取ったプロンプトを編集欄へコピー」 (Copy received prompt to the edit box) to refresh it. A hand-edited box is never overwritten automatically.

The edit box must stay valid JSON. Broken brackets or commas stop the run with the line and column of the error.

Save your characters, dialogue, and stashed panel inputs as a normal ComfyUI workflow. Favorites are stored in the browser's local storage; they do not move to other browsers and are lost if you clear site data. The node never writes to the bundled JSON files.

## Choosing a sample workflow

`example_workflows` contains samples ranging from basic manga generation to compositions and character images. If you are new to the node, start with **[make_manga.json](example_workflows/make_manga.json)**.

| File | What it does | When to use it |
| --- | --- | --- |
| [make_manga.json](example_workflows/make_manga.json) | Generates manga from text descriptions of character appearance, panel scenes, and dialogue. The default is a four-panel page with two characters, without composition nodes. | To try the basics, or to set up the layout and content yourself. |
| [make_manga_edit_prompt.json](example_workflows/make_manga_edit_prompt.json) | The basic workflow plus 「MOSSプロンプトを確認・編集」 (View and edit MOSS prompt). You can check the generated prompt and switch to an edited version. | To check what is sent to MOSS, or to adjust the prompt directly. The edit box must be valid JSON. |
| [composition_duo.json](example_workflows/composition_duo.json) | Generates a four-panel conversation between two characters. Each panel has a composition node, preset to face-to-face, side by side, across a desk, and a close-up argument. | To choose the positions of two characters and the camera composition from previews. |
| [composition_1to3.json](example_workflows/composition_1to3.json) | Uses three shared characters to generate three panels with one, two, and three characters. Compositions matching each count and up to three lines are already connected. | To change the number of characters per panel, or to see how the third character and three lines are set. |
| [composition_character_images.json](example_workflows/composition_character_images.json) | Extracts character appearance from images as English text and generates three panels with compositions. The three methods "extract from image", "extract from image + text", and "text only" are preset. | To describe characters from reference images. Change the image loaders to your own images. |
| [composition_duo.api.json](example_workflows/composition_duo.api.json) | The API format of `composition_duo.json`, with node definitions for sending the two-character four-panel composition workflow to the ComfyUI API from a script. | To run from the API. Use `composition_duo.json` to work with the nodes in the UI. |

All files except the API format can be opened by dragging them into ComfyUI. See [Requirements and models](#requirements-and-models) for the required models and folders.

Reference images for the character-image sample are not included. Character 3 in "text only" is an example of the setting and does not appear in the default panels. Neither the composition previews nor the character images are passed to MOSS as reference images; generation is guided by composition text and regions, and by the appearance text extracted from the images.

## Composition templates

The 「構図を選ぶ（見本画像）」 (Choose a composition from previews) node opens a catalog with 「画像から構図を選ぶ」 (Choose a composition from images). You can search by character count, category, name, or English prompt, and filter by favorites. Favorites are stored in your browser.

1. Open the [composition sample](example_workflows/composition_duo.json).
2. Pick a preview in the composition node and connect its 「コマに接続する構図」 (composition for the panel) output to the optional 「構図」 (composition) input of each 「コマの内容」 (Panel content) node.
3. Enter the shared characters, the scene and dialogue for each panel, and the layout, then generate. Write scenes and appearance in English, and dialogue in the language you want rendered.

The composition's English prompt is appended to the scene, and the character regions of the preview are mapped to the inner region of each panel in proportion. The selected characters are assigned to the composition in numerical order, so changing the speaking order does not swap their positions. Without a connection, the node works as before. Match the number of characters in the preview and in the panel.

There are 120 compositions: 40 each for one, two, and three characters. The original 20 two-character compositions keep their IDs and names. The English composition prompts specify only the camera, shot size, character placement, body and face direction, pose, and furniture used for staging. They do not specify facial expressions, emotions, talking, props, or lighting, so you can describe those freely in the scene. The previews are the square 1024×1024 PNGs actually output by MOSS, converted to lossy WebP (quality 90) to reduce the download size (about 178 MB to about 25 MB for 120 images). Because of the compression, fine details do not exactly match the original PNGs. No other processing was applied (no added text, compositing, downscaling, or cropping). The English generation prompt, seed, model, and settings that were embedded in the PNGs, the character regions, and the SHA256 of each original PNG are stored in `data/compositions.json`. Compositions are categorized as over-the-shoulder, face close-up, full body, high angle, low angle, and so on. The catalog shows the preview, name, character count, category, and favorites; quality checks are in the validation records. Mismatches or extra characters are not fixed by image editing.

The same composition can be used for tall or wide panels. The preview image is not passed as a reference input; the model is guided by the English prompt and regions. An exact match with the preview, following special panel shapes, and correct text or characters are not guaranteed. No compositing, text repair, or border repair is applied.

## Up to three characters

Enter both 「人物3_名前」 (character 3 name) and 「人物3_外見」 (character 3 appearance) in 「共通の人物設定」 (Shared characters) to use a third character. If both are empty, the node uses the two-character setup as before. In each panel, choose any combination of one to three characters in 「登場人物」, and set up to three lines with 「話者1〜3」 (speakers 1–3) and 「セリフ1〜3」 (lines 1–3). To make character 3 a speaker, include them in the panel's characters too.

The [one-to-three character sample](example_workflows/composition_1to3.json) has the characters, compositions, and dialogue connected. Speech balloon regions are top center to right for one line, top right and top left for two, and top right, top center, and top left for three. The node does not infer empty space in the composition.

## Appearance from character images

https://github.com/user-attachments/assets/be8c36de-7fbd-4c9c-9487-b3eec56cc5ca

[Demo video (mp4, 30 s)](docs/demo_character_images.mp4): a real screen recording of loading two character images, choosing a composition for each panel and a layout from the lists, and generating the page. Operations and generation are sped up, and only the run button scene is zoomed in. No captions are added. At the end, the input images, layout, compositions, and result are shown side by side. The manga image itself is not edited.

Open the [appearance extraction sample](example_workflows/composition_character_images.json) and choose your own character images in the two 「画像を読み込む」 (Load Image) nodes. The file names in the sample are from testing, and the reference images are not included.

「人物の外見（画像／文章）」 (Character appearance (image / text)) offers three methods.

- **文章のみ (text only)**: passes the appearance prompt as is. Qwen and a reference image are not needed. Even if connected, they are lazily evaluated and the model and image are not processed.
- **画像から抽出 (extract from image)**: converts the apparent age group, face, build, hairstyle, clothing, accessories, and so on in the character image into English appearance text. The age group is chosen in a separate short question from child, young teenager, older teenager, young adult, adult in their thirties, middle-aged, and elderly, and is added at the start as `Apparent age group: …`.
- **画像から抽出＋文章で補足 (extract from image + text)**: appends your supplementary text to the extracted text. The supplementary text is not translated.

It can share the `CLIPLoader` with `type=moss_image` and `qwen3.5_9b_int8_convrot.safetensors` used for MOSS. No other VLM, P-H3 model, or extra Python package is needed. Tested with ComfyUI 0.42.0.

Connect the appearance node's 「人物設定に渡す外見」 (appearance for shared characters) output to each 「人物N_外見」 (character N appearance) in the shared characters node. The sample is already connected. When building your own, convert the appearance field to an input and connect it. Characters 1–3 can each use an image or text method. Existing text-only workflows still work.

The resulting appearance text is shown in the node. Press 「結果を文章欄へコピー（文章のみに切替）」 (Copy result to the text field and switch to text only) to reuse and refine the text. If you remove the upstream nodes, including the reference image, and save, the workflow works with text alone in another environment, without the image files. The normal ComfyUI cache is also used, so changing only the composition or seed does not rerun the extraction.

For analysis only, the image is downscaled to 768 px on the long side while keeping the aspect ratio, if needed. The original pixels are not changed. Each node takes one image; for images with several people, the instruction describes mainly the large person in front. A reference image with one person is recommended.

The image is converted to appearance text for MOSS; the reference image itself is not passed to the image model. The extracted text may guess clothing that is not visible or include descriptions of the art style. Exact character identity is not guaranteed. Manga often draws faces young at any age, so the age group can be wrong; if so, use the copy button and correct it in the text.

The manga page prompt used to specify adult proportions (`natural adult proportions`) for everyone. It now asks for the age and body proportions written in each character's appearance text. If the appearance text gives no age, results can differ from before even with the same seed.

## Node labels

| Japanese label | English meaning |
| --- | --- |
| コマ割りを選ぶ（2〜6コマ） | Choose a panel layout (2–6 panels) |
| 共通の人物設定（普通の文章で入力） | Shared characters (plain text) |
| コマの内容（場面・登場人物・セリフ） | Panel content (scene, characters, dialogue) |
| MOSSプロンプトを確認・編集 | View and edit MOSS prompt |
| 構図を選ぶ（見本画像） | Choose a composition (preview images) |
| 人物の外見（画像／文章） | Character appearance (image / text) |
| コマ割り | Layout |
| 生成内容: 漫画 / 空のコマ枠 | Output: manga / empty panel frames |
| 人物1_名前 / 人物1_外見 | Character 1 name / appearance |
| 場面 | Scene |
| 人物3_名前 / 人物3_外見 | Character 3 name / appearance (optional) |
| 登場人物: 人物1のみ / 人物2のみ / 人物3のみ / 人物1と人物2 / 人物1と人物3 / 人物2と人物3 / 人物1と人物2と人物3 / 人物なし | Characters: 1 only / 2 only / 3 only / 1 and 2 / 1 and 3 / 2 and 3 / 1, 2, and 3 / none |
| 話者1〜3・セリフ1〜3 | Speakers 1–3, lines 1–3 |
| セリフなし | No dialogue |
| 構図 / コマに接続する構図 | Composition / composition for the panel |
| 指定方法: 文章のみ / 画像から抽出 / 画像から抽出＋文章で補足 | Method: text only / extract from image / extract from image + text |
| 外見プロンプト / 参考画像 | Appearance prompt / reference image |
| 人物設定に渡す外見 | Appearance for shared characters |

## Bundled layouts

196 layouts in total: 100 standard layouts added later, plus 96 from the earlier set of 100 after removing 4 near-duplicate candidates. The preview images total about 2.8 MB.

| Panels | Standard (added) | Earlier set | Total |
| --- | ---: | ---: | ---: |
| 2 | 20 | 18 | 38 |
| 3 | 20 | 19 | 39 |
| 4 | 20 | 20 | 40 |
| 5 | 20 | 20 | 40 |
| 6 | 20 | 19 | 39 |
| Total | 100 | 96 | 196 |

Every preview was generated by MOSS. To reduce the download size, the original PNGs (1024×1536) were converted to lossy WebP (quality 90). Because of the compression, fine details and noise in white areas do not exactly match the original PNGs. No other processing was applied (no added text, compositing, redrawn borders, downscaling, or cropping). Files were renamed to their layout IDs. The generation prompt metadata stored in the original PNGs is not carried over to the WebP files. Generation history, failed images, and per-image prompt files are not included.

Panel counts were checked automatically by counting closed white regions. Near-duplicates were detected from the rectangle coordinates of closed regions (max 2%, mean 0.8% difference) and a border match rate of 95% or more with tolerance. A human has not reviewed every layout for distinctness or accuracy.

## Limitations

Planned features are listed in [ROADMAP.md](ROADMAP.md).

- Up to three shared characters, and up to three characters and three lines per panel. The third character requires both a name and an appearance description. Four or more characters are not supported.
- Automatic panel adding and removing works with this node and `MossMangaPanel`. Panel inputs that are also connected to other nodes are not deleted.
- The model is guided by coordinates and descriptions; previews are not copied into the image. Panel shapes, proportions, and count can change from run to run.
- Diagonal and special shapes are also described in text. The regions passed to the model are rectangles, not masks that force a polygon outline.
- Characters and speech balloons use simple fixed positions inside each panel. The node does not infer the best placement for a scene or the balloon tail direction.
- Typos or broken text, mixed-up characters, and changes in panel count are not prevented. Nothing is overlaid on the generated image to fix text or borders.
- Downloading models and setting up ComfyUI itself are up to you.

## Updating and tests

After updating the folder, restart ComfyUI and reload the browser page. Characters and dialogue are not stored in the bundled JSON files, so updating the node is separate from your saved workflows. Favorites use layout IDs, and workflow selections use layout names; future updates will keep existing IDs and names.

Since 0.1.1, the 196 layouts are also read from `data/layouts.json`, so no database connection is needed at runtime. The experimental SQLite database and generation history are not distributed. IDs, names, layouts, compositions, and preview images are unchanged.

46 of the compositions had facial expressions, emotions, talking, props, or lighting in their English prompts. Their prompts were rewritten to describe only the composition, and their previews were regenerated with MOSS. IDs, names, and character regions are unchanged, so saved workflows still open. Because the connected composition text changed, results differ from before even with the same seed.

For the Registry package, `.comfyignore` excludes tests and development files; the tests remain in the GitHub source.

For development, you can run the following in this folder. Use an environment that has `aiohttp`, such as your ComfyUI Python. Node.js is used only to test the panel add/remove logic and is not needed for normal use.

```text
python -m unittest discover -s tests
node tests/test_picker_state.mjs
```

## License and credits

The original code, layout data, and bundled preview images of this project are distributed under the MIT License. See [LICENSE](LICENSE) for the full text.

The preview images were generated with MOSS-Image. The MOSS-Image model weights (Comfy-Org distribution) and the official MOSS-Image repository code are published under the Apache License 2.0 (checked on each distribution page on November 2, 2026). Model weights, ComfyUI, and other third-party implementations are not included in this repository and are not covered by its license. Check each project's license before use.

- [MOSS-Image official repository](https://github.com/OpenMOSS/MOSS-Image)
- [Comfy-Org MOSS-Image models](https://huggingface.co/Comfy-Org/MOSS-Image)
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI)

