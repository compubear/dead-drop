"""Dead Drop — Sprint 5 tests: Publishing connectors."""

import pytest
from unittest.mock import patch, MagicMock

from pipeline.publishers.beehiiv import BeehiivPublisher
from pipeline.publishers.twitter import TwitterPublisher
from pipeline.publishers.telegram import TelegramPublisher
from pipeline.publishers.reddit import RedditPublisher
from pipeline.publishers.orchestrator import PublishResult, publish_story


class TestBeehiiv:
    """Test beehiiv newsletter publisher."""

    def test_no_api_key_returns_none(self):
        with patch("pipeline.publishers.beehiiv.settings") as mock_s:
            mock_s.BEEHIIV_API_KEY = ""
            mock_s.BEEHIIV_PUBLICATION_ID = ""
            pub = BeehiivPublisher()
            result = pub.create_post("Title", "<p>Content</p>")
            assert result is None

    @patch("pipeline.publishers.beehiiv.httpx.Client")
    def test_create_post_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"id": "post_123"}}
        mock_client.post.return_value = mock_resp

        with patch("pipeline.publishers.beehiiv.settings") as mock_s:
            mock_s.BEEHIIV_API_KEY = "test-key"
            mock_s.BEEHIIV_PUBLICATION_ID = "pub_123"
            pub = BeehiivPublisher()
            pub.client = mock_client
            result = pub.create_post("Title", "<p>Content</p>")
            assert result is not None


class TestTwitter:
    """Test Twitter publisher."""

    def test_no_bearer_token_returns_none(self):
        with patch("pipeline.publishers.twitter.settings") as mock_s:
            mock_s.TWITTER_BEARER_TOKEN = ""
            mock_s.TWITTER_API_KEY = ""
            mock_s.TWITTER_API_SECRET = ""
            mock_s.TWITTER_ACCESS_TOKEN = ""
            mock_s.TWITTER_ACCESS_SECRET = ""
            pub = TwitterPublisher()
            result = pub.post_tweet("Test tweet")
            assert result is None

    def test_parse_thread_json_format(self):
        with patch("pipeline.publishers.twitter.settings") as mock_s:
            mock_s.TWITTER_BEARER_TOKEN = "test"
            mock_s.TWITTER_API_KEY = ""
            mock_s.TWITTER_API_SECRET = ""
            mock_s.TWITTER_ACCESS_TOKEN = ""
            mock_s.TWITTER_ACCESS_SECRET = ""
            pub = TwitterPublisher()
            content = '["Tweet 1", "Tweet 2", "Tweet 3"]'
            tweets = pub.parse_thread_content(content)
            assert len(tweets) == 3
            assert tweets[0] == "Tweet 1"

    def test_parse_thread_numbered_format(self):
        with patch("pipeline.publishers.twitter.settings") as mock_s:
            mock_s.TWITTER_BEARER_TOKEN = "test"
            mock_s.TWITTER_API_KEY = ""
            mock_s.TWITTER_API_SECRET = ""
            mock_s.TWITTER_ACCESS_TOKEN = ""
            mock_s.TWITTER_ACCESS_SECRET = ""
            pub = TwitterPublisher()
            content = "1. First tweet\n2. Second tweet\n3. Third tweet"
            tweets = pub.parse_thread_content(content)
            assert len(tweets) == 3


class TestTelegram:
    """Test Telegram publisher."""

    def test_no_bot_token_returns_none(self):
        with patch("pipeline.publishers.telegram.settings") as mock_s:
            mock_s.TELEGRAM_BOT_TOKEN = ""
            mock_s.TELEGRAM_CHANNEL_ID = ""
            pub = TelegramPublisher()
            result = pub.send_message("Test")
            assert result is None


class TestReddit:
    """Test Reddit publisher."""

    def test_not_configured(self):
        with patch("pipeline.publishers.reddit.settings") as mock_s:
            mock_s.REDDIT_CLIENT_ID = ""
            mock_s.REDDIT_CLIENT_SECRET = ""
            mock_s.REDDIT_USERNAME = ""
            mock_s.REDDIT_PASSWORD = ""
            pub = RedditPublisher()
            assert pub.client_id == ""


class TestPublishOrchestrator:
    """Test publisher orchestrator."""

    def test_publish_result_tracking(self):
        result = PublishResult("Test Story")
        result.add_result("beehiiv", True)
        result.add_result("twitter", False, "error")
        assert not result.all_success
        assert result.summary["beehiiv"] is True
        assert result.summary["twitter"] is False

    def test_publish_result_all_success(self):
        result = PublishResult("Test Story")
        result.add_result("beehiiv", True)
        result.add_result("twitter", True)
        assert result.all_success

    @patch("pipeline.publishers.orchestrator.settings")
    def test_dry_run_all_succeed(self, mock_settings):
        mock_settings.BEEHIIV_API_KEY = ""
        mock_settings.TWITTER_BEARER_TOKEN = ""
        mock_settings.TELEGRAM_BOT_TOKEN = ""
        mock_settings.REDDIT_CLIENT_ID = ""

        result = publish_story(
            story={"title": "Test Story"},
            content_outputs={
                "newsletter": "Newsletter content",
                "twitter_thread": '["Tweet 1"]',
                "telegram": "Telegram post",
                "reddit_post": "Reddit content",
            },
            dry_run=True,
        )
        assert result.all_success

    @patch("pipeline.publishers.orchestrator.settings")
    def test_publish_not_configured_channels(self, mock_settings):
        mock_settings.BEEHIIV_API_KEY = ""
        mock_settings.TWITTER_BEARER_TOKEN = ""
        mock_settings.TELEGRAM_BOT_TOKEN = ""
        mock_settings.REDDIT_CLIENT_ID = ""

        result = publish_story(
            story={"title": "Test Story"},
            content_outputs={
                "newsletter": "content",
                "twitter_thread": "content",
                "telegram": "content",
                "reddit_post": "content",
            },
            dry_run=False,
        )
        # All should fail gracefully with "not_configured"
        for ch, data in result.channels.items():
            assert data["detail"] == "not_configured"
