#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS記事のbulletpoints生成ツール
RSSフィードから記事を読み込み、OpenAI APIを使ってbulletpointsを生成します。
"""

import os
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import time
import sys
import json

# 環境変数を読み込み
load_dotenv()

class RSSBulletPointsGenerator:
    def __init__(self, config_file="config.json"):
        """初期化"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEYが.envファイルに設定されていません")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # 設定ファイルを読み込み
        self.config = self.load_config(config_file)
        self.rss_url = self.config['rss_url']
    
    def load_config(self, config_file):
        """設定ファイルを読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"設定ファイルを読み込みました: {config_file}")
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイル '{config_file}' が見つかりません")
        except json.JSONDecodeError:
            raise ValueError(f"設定ファイル '{config_file}' のJSONフォーマットが正しくありません")
        
    def fetch_rss_articles(self, limit=5):
        """RSSフィードから記事のURL一覧を取得"""
        try:
            print(f"RSSフィードを取得中: {self.rss_url}")
            feed = feedparser.parse(self.rss_url)
            
            if not feed.entries:
                print("記事が見つかりません")
                return []
            
            list_articles = []
            for entry in feed.entries[:limit]:
                article_info = {
                    'title': entry.get('title', 'タイトル不明'),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', '日付不明'),
                    'summary': entry.get('summary', '')
                }
                list_articles.append(article_info)
                
            print(f"{len(list_articles)}件の記事を取得しました")
            return list_articles
            
        except Exception as e:
            print(f"RSSフィードの取得でエラーが発生しました: {e}")
            return []
    
    def fetch_article_content(self, url):
        """記事のURLから本文を取得"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 不要なタグを削除
            for tag_to_remove in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag_to_remove.decompose()
            
            # 記事本文を取得（複数のパターンを試行）
            content_selectors = [
                'article', '.entry-content', '.post-content', '.content', 
                '.article-body', 'main', '.main-content', 'p'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    if len(content) > 100:  # 十分な長さのコンテンツが見つかった場合
                        break
            
            if not content:
                content = soup.get_text(strip=True)
            
            # 長すぎる場合は制限
            max_length = self.config.get('max_content_length', 8000)
            if len(content) > max_length:
                content = content[:max_length] + "..."
                
            return content
            
        except Exception as e:
            print(f"記事の取得でエラーが発生しました ({url}): {e}")
            return ""
    
    def generate_bulletpoints(self, title, content):
        """OpenAI APIを使ってbulletpointsを生成"""
        if not content or len(content.strip()) < 50:
            return ["記事の内容を取得できませんでした"]
        
        try:
            # 設定ファイルからプロンプトテンプレートとシステムメッセージを取得
            prompt_template = self.config.get('prompt_template', 
                "以下の記事のタイトルと内容を読んで、要点を日本語のbulletpoints（箇条書き）で5つ以内にまとめてください。\n各ポイントは簡潔で分かりやすくしてください。\n\nタイトル: {title}\n\n記事内容:\n{content}\n\nbulletpoints:")
            
            system_message = self.config.get('system_message', 
                "あなたは記事の要点を整理する専門家です。重要なポイントを簡潔にまとめることが得意です。")
            
            # プロンプトにタイトルと内容を埋め込み
            prompt = prompt_template.format(title=title, content=content)

            # AIモデルの設定を取得
            model = self.config.get('model', 'gpt-4o-mini')
            max_tokens = self.config.get('max_tokens', 1000)
            temperature = self.config.get('temperature', 0.3)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            bulletpoints_text = response.choices[0].message.content.strip()
            
            # bulletpointsをリストに変換
            list_bulletpoints = []
            for line in bulletpoints_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # 記号を削除して追加
                    clean_point = line.lstrip('•-*').strip()
                    if clean_point:
                        list_bulletpoints.append(clean_point)
                elif line and not line.startswith(('bulletpoints', 'Bulletpoints', '要点', '箇条書き')):
                    # 番号付きリストの場合
                    if '.' in line and line.split('.')[0].isdigit():
                        clean_point = '.'.join(line.split('.')[1:]).strip()
                        if clean_point:
                            list_bulletpoints.append(clean_point)
                    elif line:
                        list_bulletpoints.append(line)
            
            return list_bulletpoints if list_bulletpoints else [bulletpoints_text]
            
        except Exception as e:
            print(f"bulletpoints生成でエラーが発生しました: {e}")
            return [f"エラー: {str(e)}"]
    
    def process_articles(self, limit=5):
        """記事を処理してbulletpointsを生成"""
        list_articles = self.fetch_rss_articles(limit)
        
        if not list_articles:
            print("処理する記事がありません")
            return
        
        print("\n" + "="*80)
        print("RSS記事のbulletpoints生成結果")
        print("="*80)
        
        for i, article in enumerate(list_articles, 1):
            print(f"\n【記事 {i}/{len(list_articles)}】")
            print(f"タイトル: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"公開日: {article['published']}")
            print("-" * 60)
            
            # 記事内容を取得
            content = self.fetch_article_content(article['url'])
            
            if content:
                print("記事内容を取得中...")
                # bulletpointsを生成
                list_bulletpoints = self.generate_bulletpoints(article['title'], content)
                
                print("Bulletpoints:")
                for j, point in enumerate(list_bulletpoints, 1):
                    print(f"  {j}. {point}")
            else:
                print("記事内容を取得できませんでした")
            
            print("-" * 60)
            
            # API制限を考慮して少し待機
            if i < len(list_articles):
                delay = self.config.get('request_delay_seconds', 1)
                time.sleep(delay)

def main():
    """メイン処理"""
    try:
        generator = RSSBulletPointsGenerator()
        
        # 処理する記事数を指定（設定ファイルのデフォルト値を使用）
        article_limit = generator.config.get('default_article_limit', 5)
        if len(sys.argv) > 1:
            try:
                article_limit = int(sys.argv[1])
            except ValueError:
                print("引数は数値で指定してください。デフォルトの5件で処理します。")
        
        print(f"最大{article_limit}件の記事を処理します...")
        generator.process_articles(limit=article_limit)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 