from expando.text_convert import html_to_plain, markdown_to_plain


def test_markdown_to_plain():
    assert "Hello" in markdown_to_plain("**Hello** [world](https://x.test)")


def test_html_to_plain():
    assert html_to_plain("<p>Hello <b>world</b></p>") == "Hello world"