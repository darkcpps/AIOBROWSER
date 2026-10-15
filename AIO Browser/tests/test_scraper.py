"""Tests for core.scraper HTML parsing with a stubbed HTTP layer."""
from core import scraper

SEARCH_HTML = """
<html><body>
  <article>
    <h2 class="entry-title"><a href="https://fitgirl-repacks.site/game-a/">Game A</a></h2>
  </article>
  <article>
    <h2 class="entry-title"><a href="https://fitgirl-repacks.site/game-b/">Game B</a></h2>
  </article>
</body></html>
"""


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def test_scrape_search_results_parses_articles(monkeypatch):
    monkeypatch.setattr(
        scraper.requests, "get", lambda *a, **k: FakeResponse(SEARCH_HTML)
    )

    results = scraper.scrape_search_results(
        "https://fitgirl-repacks.site/?s=game", "FitGirl"
    )

    assert [r["title"] for r in results] == ["Game A", "Game B"]
    assert all(r["source"] == "FitGirl" for r in results)
    assert results[0]["link"].endswith("/game-a/")


def test_scrape_search_results_handles_network_error(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(scraper.requests, "get", boom)

    assert scraper.scrape_search_results("https://example.com", "X") == []


def test_scrape_magnet_returns_first_magnet(monkeypatch):
    html = '<html><body><a href="magnet:?xt=urn:btih:abc">magnet</a></body></html>'
    monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: FakeResponse(html))

    assert scraper.scrape_magnet("https://example.com/page") == "magnet:?xt=urn:btih:abc"


def test_scrape_magnet_returns_none_when_absent(monkeypatch):
    monkeypatch.setattr(
        scraper.requests, "get", lambda *a, **k: FakeResponse("<html></html>")
    )
    assert scraper.scrape_magnet("https://example.com/page") is None
