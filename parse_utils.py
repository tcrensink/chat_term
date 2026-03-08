import re
from rich.markdown import (
    Console,
    ConsoleOptions,
    Markdown,
    TextElement,
    Token,
    RenderResult,
)
from rich.text import Text


class RevisedHeading(TextElement):
    """A heading with minimal formatting."""

    @classmethod
    def create(cls, markdown: "Markdown", token: Token) -> "Heading":
        return cls(token.tag)

    def on_enter(self, context: "MarkdownContext") -> None:
        self.text = Text()
        context.enter_style(self.style_name)

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.style_name = "bold"
        super().__init__()

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.text


# this is a Markdown class with slightly simplified rendering
class MinimalMarkdown(Markdown):
    Markdown.elements["heading_open"] = RevisedHeading


# Matches fenced code blocks. The backreference \1 requires the closing fence to
# use the same characters and length as the opening, so backticks inside a block
# won't close it prematurely. Unterminated blocks simply don't match.
_FENCE_RE = re.compile(
    r"^[ \t]*(`{3,}|~{3,})[ \t]*(\w*)[ \t]*\n(.*?)\n[ \t]*\1[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def parse_text(text):
    """Split text into alternating text/code segments."""
    output = []
    last_pos = 0

    for m in _FENCE_RE.finditer(text):
        block = text[last_pos : m.start()]
        if block.strip():
            output.append({"raw_text": block, "display_text": block.strip(), "type": "text"})
        output.append({
            "raw_text": m.group(0),
            "display_text": m.group(3),
            "type": "code",
            "lang": m.group(2),
        })
        last_pos = m.end()

    block = text[last_pos:]
    if block.strip():
        output.append({"raw_text": block, "display_text": block.strip(), "type": "text"})
    return output


def test_parse_text():

    no_text_code = "just some non-code text"
    assert parse_text(no_text_code) == [
        {
            "raw_text": "just some non-code text",
            "display_text": "just some non-code text",
            "type": "text",
        }
    ]
    assert len(parse_text(no_text_code)[0]["raw_text"]) == len(no_text_code)

    text_code_only = """```python\nprint("hello world")\n```"""
    assert parse_text(text_code_only) == [
        {
            "raw_text": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")',
            "type": "code",
            "lang": "python",
        }
    ]
    assert len(parse_text(text_code_only)[0]["raw_text"]) == len(text_code_only)

    code_then_text = """```python\nprint("hello world")\n```\n\n\n\nand some other stuff"""
    assert parse_text(code_then_text) == [
        {
            "raw_text": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")',
            "type": "code",
            "lang": "python",
        },
        {
            "raw_text": "\n\n\n\nand some other stuff",
            "display_text": "and some other stuff",
            "type": "text",
        },
    ]
    assert sum([len(x["raw_text"]) for x in parse_text(code_then_text)]) == len(
        code_then_text
    )

    text_then_code = """starting text, then:\n```python\nprint("hello world")\n```"""
    assert parse_text(text_then_code) == [
        {
            "raw_text": "starting text, then:\n",
            "display_text": "starting text, then:",
            "type": "text",
        },
        {
            "raw_text": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")',
            "type": "code",
            "lang": "python",
        },
    ]
    assert sum([len(x["raw_text"]) for x in parse_text(text_then_code)]) == len(
        text_then_code
    )

    text_code_alternating = """```python\nprint("hello world")\n```\nok some more text, and\n```python\nprint("hello world")\n```\nend text here"""
    assert parse_text(text_code_alternating) == [
        {
            "raw_text": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")',
            "type": "code",
            "lang": "python",
        },
        {
            "raw_text": "\nok some more text, and\n",
            "display_text": "ok some more text, and",
            "type": "text",
        },
        {
            "raw_text": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")',
            "type": "code",
            "lang": "python",
        },
        {"raw_text": "\nend text here", "display_text": "end text here", "type": "text"},
    ]
    assert sum([len(x["raw_text"]) for x in parse_text(text_code_alternating)]) == len(
        text_code_alternating
    )
