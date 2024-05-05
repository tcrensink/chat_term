import marko
import re
import copy
from marko import inline
from marko.block import BlockElement, FencedCode
from marko.source import Source
from typing import TYPE_CHECKING, Any, Match, NamedTuple
from rich.markdown import Markdown
from rich.markdown import TextElement, Token, Console, ConsoleOptions, RenderResult
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
    elements = copy.deepcopy(Markdown.elements)
    elements["heading_open"] = RevisedHeading


# this is a modified and monkey patched version of marko.block.FencedCode
class FencedCode(FencedCode):
    """Fenced code block: (```python\nhello\n```\n)"""

    priority = 7
    pattern = re.compile(r"( {,3})(`{3,}|~{3,})[^\n\S]*(.*?)$", re.M)

    class ParseInfo(NamedTuple):
        prefix: str
        leading: str
        lang: str
        extra: str

    def __init__(self, match: tuple[str, str, str, str, str]) -> None:
        # def __init__(self, match: tuple[str, str, str]) -> None:

        self.lang = inline.Literal.strip_backslash(match[0])
        self.extra = match[1]
        self.children = [inline.RawText(match[2], False)]
        ## MODIFIED CODE ##
        self.start = match[3] if len(match) > 3 else None
        self.end = match[4] if len(match) > 4 else None
        ## MODIFIED CODE ##

    @classmethod
    def parse(cls, source: Source) -> tuple[str, str, str]:
        ## MODIFIED CODE ##
        start = source.pos
        ## MODIFIED CODE ##
        source.next_line()
        source.consume()
        lines = []
        parse_info: FencedCode.ParseInfo = source.context.code_info
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            source.consume()
            m = re.match(r" {,3}(~+|`+)[^\n\S]*$", line, flags=re.M)
            if m and parse_info.leading in m.group(1):
                break

            prefix_len = source.match_prefix(parse_info.prefix, line)
            if prefix_len >= 0:
                line = line[prefix_len:]
            else:
                line = line.lstrip()
            lines.append(line)
        ## MODIFIED CODE ##
        end = source.pos
        ## MODIFIED CODE ##
        # return parse_info.lang, parse_info.extra, "".join(lines)
        return parse_info.lang, parse_info.extra, "".join(lines), start, end


marko.block.FencedCode = FencedCode


def parse_text(text):
    """Identify text spans, display text, and widget type.

    text spans and display text must both be tracked.
    """
    parsed = marko.parse(text)
    output = []
    idx1 = 0
    idx2 = len(text)
    for child in parsed.children:
        if isinstance(child, marko.block.FencedCode):
            # append previous block if it exists
            block = text[idx1 : child.start]
            if idx1 < child.start and len(block.strip()) > 0:
                output.append(
                    {"raw_text": block, "display_text": block, "type": "text"}
                )
            # append code block
            block = text[child.start : child.end]
            output.append(
                {
                    "raw_text": block,
                    "display_text": child.children[0].children,
                    "type": "code",
                }
            )
            idx1 = child.end
            idx2 = len(text)

    # end block
    block = text[idx1:idx2]
    if len(block.strip()) > 0:
        output.append(
            {"raw_text": block, "display_text": block.strip(), "type": "text"}
        )
    return output


def test_parse_text():

    no_text_code = "just some non-code text"
    parse_text(no_text_code)
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
            "display_text": 'print("hello world")\n',
            "type": "code",
        }
    ]
    assert len(parse_text(text_code_only)[0]["raw_text"]) == len(text_code_only)

    code_then_text = (
        """```python\nprint("hello world")\n```\n\n\n\nand some other stuff"""
    )
    assert parse_text(code_then_text) == [
        {
            "raw_text": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {
            "raw_text": "\n\n\nand some other stuff",
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
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
    ]
    assert sum([len(x["raw_text"]) for x in parse_text(text_then_code)]) == len(
        text_then_code
    )

    text_code_alternating = """```python\nprint("hello world")\n```\nok some more text, and\n```python\nprint("hello world")\n```\nend text here"""
    assert parse_text(text_code_alternating) == [
        {
            "raw_text": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {
            "raw_text": "ok some more text, and\n",
            "display_text": "ok some more text, and",
            "type": "text",
        },
        {
            "raw_text": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {"raw_text": "end text here", "display_text": "end text here", "type": "text"},
    ]
    assert sum([len(x["raw_text"]) for x in parse_text(text_code_alternating)]) == len(
        text_code_alternating
    )
