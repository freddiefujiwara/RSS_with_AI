import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
import types
from types import SimpleNamespace
import builtins

import pytest

import rss_bulletpoints_generator as rbg

# Helper dummy response for requests.get
class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.apparent_encoding = 'utf-8'
        self.encoding = None
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception('HTTP error')


def setup_generator(monkeypatch, tmp_config):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    dummy_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: None)))
    monkeypatch.setattr(rbg, 'OpenAI', lambda api_key=None: dummy_client)
    return rbg.RSSBulletPointsGenerator(config_file=tmp_config)


def create_tmp_config(tmp_path):
    cfg = tmp_path / 'config.json'
    cfg.write_text('{"rss_url": "http://example.com/feed"}', encoding='utf-8')
    return str(cfg)


def test_load_config_success(tmp_path):
    cfg_path = create_tmp_config(tmp_path)
    gen = rbg.RSSBulletPointsGenerator.__new__(rbg.RSSBulletPointsGenerator)
    config = gen.load_config(cfg_path)
    assert config['rss_url'] == 'http://example.com/feed'


def test_load_config_missing_file():
    gen = rbg.RSSBulletPointsGenerator.__new__(rbg.RSSBulletPointsGenerator)
    with pytest.raises(FileNotFoundError):
        gen.load_config('no_such_config.json')


def test_fetch_rss_articles(monkeypatch, tmp_path):
    cfg_path = create_tmp_config(tmp_path)
    feed = SimpleNamespace(entries=[{
        'title': 'T1',
        'link': 'http://a/1',
        'published': 'today',
        'summary': 'sum'
    }])
    monkeypatch.setattr(rbg.feedparser, 'parse', lambda url: feed)
    gen = setup_generator(monkeypatch, cfg_path)
    articles = gen.fetch_rss_articles(limit=1)
    assert articles == [{'title': 'T1', 'url': 'http://a/1', 'published': 'today', 'summary': 'sum'}]


def test_fetch_article_content(monkeypatch, tmp_path):
    cfg_path = create_tmp_config(tmp_path)
    html = '<html><body><article><p>' + ('a'*120) + '</p></article></body></html>'
    monkeypatch.setattr(rbg.requests, 'get', lambda url, headers=None, timeout=10: DummyResponse(html))
    gen = setup_generator(monkeypatch, cfg_path)
    content = gen.fetch_article_content('http://example.com/article')
    assert 'a'*100 in content


def test_generate_bulletpoints(monkeypatch, tmp_path):
    cfg_path = create_tmp_config(tmp_path)
    bp_text = '• Point1\n- Point2\n3. Point3'
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=bp_text))])
    dummy_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))
    monkeypatch.setenv('OPENAI_API_KEY', 'dummy')
    monkeypatch.setattr(rbg, 'OpenAI', lambda api_key=None: dummy_client)
    gen = rbg.RSSBulletPointsGenerator(config_file=cfg_path)
    points = gen.generate_bulletpoints('title', 'x'*100)
    assert points == ['Point1', 'Point2', 'Point3']


def test_generate_bulletpoints_short_content(monkeypatch, tmp_path):
    cfg_path = create_tmp_config(tmp_path)
    gen = setup_generator(monkeypatch, cfg_path)
    result = gen.generate_bulletpoints('title', 'short')
    assert result == ['記事の内容を取得できませんでした']
