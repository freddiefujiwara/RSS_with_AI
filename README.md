# RSS記事のbulletpoints生成ツール

このツールは、指定されたRSSフィードから記事を読み込み、OpenAI APIを使って各記事の要点をbulletpoints（箇条書き）として生成します。

## 機能

- RSSフィードから記事のURL一覧を取得
- 記事の内容をWebスクレイピングで取得
- OpenAI API（gpt-4o-mini）を使用してbulletpointsを生成
- 結果を日本語で表示
- 設定ファイル（config.json）によるカスタマイズ可能

## セットアップ

1. 必要なライブラリをインストール：
   ```bash
   pip install -r requirements.txt
   ```

2. `.env`ファイルを作成してOpenAI APIキーを設定：
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. 必要に応じて`config.json`ファイルを編集して設定をカスタマイズ

## 使用方法

### 基本実行（デフォルト5件の記事を処理）
```bash
python rss_bulletpoints_generator.py
```

### 処理する記事数を指定して実行
```bash
python rss_bulletpoints_generator.py 10
```

## 出力例

```
RSS記事のbulletpoints生成結果
================================================================================

【記事 1/5】
タイトル: 変更差分からユニットテスト/結合テスト/システムテストのテスト観点を出せるのか？【cursor】
URL: https://zenn.dev/jam0824/articles/877546e6d059fb
公開日: Mon, 16 Jun 2025 03:00:00 GMT
------------------------------------------------------------
記事内容を取得中...
Bulletpoints:
  1. Cursor + Claude-4-Sonnetを用いて、影響範囲を踏まえたテスト観点を自動生成
  2. ユニット、インテグレーション、システムの3レベルで整理。
  3. 拾えた：敵へのダメージ、弾幕負荷、他武器との競合など
  4. 不足：向きの反転、セーブ/ロード、特定の仕様反映
  5. AIだけで完結させず、「人の視点での補完」が重要
------------------------------------------------------------
```

## 注意事項

- OpenAI APIの利用料金が発生します
- RSSフィードや記事サイトがアクセスを制限している場合、取得に失敗することがあります
- 記事の内容が短すぎる場合やHTMLの構造によっては、適切に本文を抽出できない場合があります
- API呼び出し制限を考慮して、記事間に1秒の待機時間を設けています

## 設定ファイル（config.json）

`config.json`ファイルで以下の設定をカスタマイズできます：

```json
{
  "rss_url": "https://yoshikiito.github.io/test-qa-rss-feed/feeds/rss.xml",
  "model": "gpt-4o-mini",
  "prompt_template": "以下の記事のタイトルと内容を読んで、要点を日本語のbulletpoints（箇条書き）で5つ以内にまとめてください。\n各ポイントは簡潔で分かりやすく、技術的な内容も含めてください。\n\nタイトル: {title}\n\n記事内容:\n{content}\n\nbulletpoints:",
  "system_message": "あなたは記事の要点を整理する専門家です。重要なポイントを簡潔にまとめることが得意です。",
  "max_tokens": 1000,
  "temperature": 0.3,
  "max_content_length": 8000,
  "default_article_limit": 5,
  "request_delay_seconds": 1
}
```

### 設定項目の説明

- `rss_url`: 取得対象のRSSフィードのURL
- `model`: 使用するOpenAIモデル（例: gpt-4o-mini, gpt-4, gpt-3.5-turbo等）
- `prompt_template`: AIに送るプロンプトのテンプレート（{title}と{content}を含める）
- `system_message`: AIのシステムメッセージ
- `max_tokens`: AIレスポンスの最大トークン数
- `temperature`: AIの創造性を制御するパラメータ（0.0-2.0、低いほど一貫性が高い）
- `max_content_length`: 記事内容の最大文字数
- `default_article_limit`: デフォルトで処理する記事数
- `request_delay_seconds`: API呼び出し間の待機時間（秒）

## 対象RSS

- URL: https://yoshikiito.github.io/test-qa-rss-feed/feeds/rss.xml
- テスト・QA関連ブログのRSSフィード

## 必要なライブラリ

- feedparser: RSSフィードの解析
- requests: HTTP通信
- beautifulsoup4: HTML解析
- openai: OpenAI API
- python-dotenv: 環境変数管理
- lxml: XMLパーサー 