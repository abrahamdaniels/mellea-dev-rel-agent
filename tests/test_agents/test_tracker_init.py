from __future__ import annotations

from agents.tracker import detect_platform, infer_asset_type


def test_detect_twitter():
    assert detect_platform("https://x.com/user/status/123") == "twitter"
    assert detect_platform("https://twitter.com/user/status/456") == "twitter"


def test_detect_linkedin():
    assert detect_platform("https://linkedin.com/posts/some-post") == "linkedin"


def test_detect_medium():
    assert detect_platform("https://medium.com/@user/some-article") == "medium"


def test_detect_dev_to():
    assert detect_platform("https://dev.to/user/article") == "dev_to"


def test_detect_github_demo():
    url = "https://github.com/org/repo/tree/main/demos/example"
    assert detect_platform(url) == "github"


def test_detect_huggingface_blog():
    assert detect_platform("https://huggingface.co/blog/some-post") == "huggingface"


def test_detect_ibm_research():
    assert detect_platform("https://research.ibm.com/blog/article") == "ibm_research"


def test_detect_unknown_returns_none():
    assert detect_platform("https://example.com/page") is None


def test_infer_social_post_type():
    assert infer_asset_type("https://x.com/user/status/123") == "social_post"
    assert infer_asset_type("https://linkedin.com/posts/p") == "social_post"


def test_infer_blog_type():
    assert infer_asset_type("https://medium.com/@u/article") == "blog"
    assert infer_asset_type("https://dev.to/u/article") == "blog"
    assert infer_asset_type("https://huggingface.co/blog/post") == "blog"


def test_infer_demo_type():
    url = "https://github.com/org/repo/tree/main/demos/example"
    assert infer_asset_type(url) == "demo"


def test_infer_unknown_returns_none():
    assert infer_asset_type("https://example.com/page") is None
