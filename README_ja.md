# 画像検索アプリケーション

[English Edition](./README.md) | [中国語版](./README_zh.md)

## 紹介

OceanBase のベクトル保存および検索機能を活用することで、画像検索アプリケーションを構築できます。このアプリケーションは画像をベクトルとして埋め込み、データベースに保存します。ユーザーが画像をアップロードすると、アプリケーションはデータベース内から最も類似した画像を検索して返します。

注意：画像データはご自身で用意し、UI上の `Image Base` 設定を更新する必要があります。ローカルに画像がない場合は、Kaggle の [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) データセットなどのオンラインデータセットをダウンロードして利用できます。

## 準備

1. 依存関係管理ツールとして [uv](https://github.com/astral-sh/uv) をインストールします。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. システムで `make` コマンドが利用可能であることを確認してください。

## アプリケーションの構築手順

### 1. 環境変数の設定

`.env.example` ファイルを `.env` にコピーし、必要に応じて設定を修正します。

```bash
cp .env.example .env
```

**重要な設定項目：**

- **API_KEY**（全文検索/ハイブリッド検索に必須）：画像自動キャプション機能用の API キー
  - 純粋なベクトル検索（ベクトル重み=1.0）のみを使用する場合は設定不要です。
  - テキスト検索またはハイブリッド検索（ベクトル重み<1.0）を使用する場合は必須です。
  - OpenAI、Qwen（通義千問）など、OpenAI API 互換のサービスをサポートしています。
  - Qwen API の取得方法：[Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/apiKey) から API Key を取得してください。
- **BASE_URL**：API サービスのベース URL（デフォルトは Qwen のエンドポイント）
- **MODEL**：使用するモデル名（デフォルトは `qwen-vl-max`）

設定例（`.env`）：
```bash
API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-vl-max
```

### 2. 環境の初期化

このコマンドは、OceanBase データベースコンテナを起動し、すべての依存関係をインストールします。

```bash
make init
```

### 3. アプリケーションの起動

```bash
make start
```

### 4. 画像データの処理と保存

アプリケーション画面が開いたら、左側のサイドバーにある "Image Base" 入力欄に、用意した画像ディレクトリの絶対パスを入力し、"Load Images" ボタンをクリックします。アプリケーションが画像を処理して保存し、画面に進捗が表示されます。

### 5. 画像検索の使用

画像の処理が完了すると、画面中央上部にアップロード欄が表示されます。検索したい画像をアップロードすると、データベース内から最も類似した画像（デフォルトで上位10枚）が返されます。

![image_search_ui](./data/demo/image-search-demo.png)

## その其他のコマンド

### アプリケーションの停止

```bash
make stop
```

### リソースのクリーンアップ

```bash
make clean
```

## よくある質問

### 1. libGL.so.1 が見つからないというエラーが出る場合は？

UI 実行時に `ImportError: libGL.so.1: cannot open shared object file` というエラーが発生した場合は、[こちらのスレッド](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo) を参照して解決してください。

CentOS/RedHat 系の場合：

```bash
sudo yum install mesa-libGL -y
```

Ubuntu/Debian 系の場合：

```bash
sudo apt-get install libgl1
```

### 2. Docker のインストールで問題が発生した場合は？

Docker のインストールや OceanBase コンテナの起動で問題が発生した場合は、[OceanBase OBI](https://www.oceanbase.com/obi) にてサポートを確認してください。
