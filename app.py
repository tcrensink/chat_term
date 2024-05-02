#!/usr/bin/env python
import os
import json
import marko
import re
from marko.block import BlockElement, FencedCode
from openai import AsyncOpenAI
import pyperclip
from textual.binding import Binding
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Label, TextArea, Markdown
from textual.containers import VerticalScroll
from textual import events
from textual.reactive import var
from marko.source import Source
from typing import TYPE_CHECKING, Any, Match, NamedTuple
from marko import inline

# stores chat history until reset.
SESSION_CONTEXT = {
    "role": "system",
    "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as accurately and concisely as possible. If you are not sure, just say 'I don't know'.",
}

try:
    BASE_PATH = os.path.dirname(__file__)
except NameError:
    BASE_PATH = os.getcwd()

with open(os.path.join(BASE_PATH, "config.jsonc")) as fp:
    lines = fp.readlines()
    json_str = "".join([line for line in lines if not line.lstrip().startswith("//")])
    CONFIG = json.loads(json_str)


def copy_to_clipboard(text):
    """Copy text to clipboard; return True if successful."""
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(e, "copy to clipboard failed")
        return False
    return True


def get_key():
    """Return the open ai api key."""
    secrets_file = os.path.join(BASE_PATH, "secrets.json")
    with open(secrets_file) as fp:
        secrets = json.load(fp)
        openai_api_key = secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise Exception("you must provide your OPENAI_API_KEY in secrets.json")
    return openai_api_key


class InputText(Static):
    """Formatted widget that contains prompt text."""

    pass


class ResponseCode(Markdown):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._markdown = ""
        self._display_text = ""

    def on_click(self) -> None:
        """copy extracted code block to clipboard"""
        copied = copy_to_clipboard(self._display_text)
        if copied:
            self.styles.opacity = 0.0
            self.styles.animate(
                attribute="opacity", value=1.0, duration=0.3, easing="out_expo"
            )

    def append_text(self, text, display_text):
        self._markdown += text
        self._display_text += display_text
        self.update(self._markdown)

    def clear_text(self):
        self._markdown = ""
        self._display_text = ""
        self.update(self._markdown)

    def set_text(self, text, display_text):
        self._markdown = text
        self._display_text = display_text
        self.update(self._markdown)


class ResponseText(Static):
    """Formatted widget that contains response text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = ""
        self._display_text = ""

    def on_click(self) -> None:
        """Visual feedback if copy successful"""
        copied = copy_to_clipboard(self._display_text)
        if copied:
            self.styles.opacity = 0.0
            self.styles.animate(
                attribute="opacity", value=1.0, duration=0.3, easing="out_expo"
            )

    def append_text(self, new_text, display_text):
        self._text += new_text
        self._display_text += display_text
        self.update(self._text)

    def clear_text(self):
        self._text = ""
        self._display_text = ""
        self.update(self._text)

    def set_text(self, text, display_text):
        self._text = text
        self._display_text = display_text
        self.update(self._text)


class MyTextArea(TextArea):
    BINDINGS = [tuple(k) for k in CONFIG["keybindings"]] + [
        Binding("ctrl+c", "", "", show=False)
    ]
    show_line_numbers = CONFIG["show_line_numbers"]


class ChatApp(App):
    """chat TUI"""

    CSS_PATH = os.path.join(BASE_PATH, "chat.css")
    BINDINGS = [tuple(k) for k in CONFIG["keybindings"]] + [
        Binding("ctrl+c", "", "", show=False)
    ]

    chat_history = [SESSION_CONTEXT]

    expanded_input = var(False)

    def watch_expanded_input(self, expanded_input: bool) -> None:
        """Called when expanded_input is modified."""
        self.set_class(expanded_input, "-expanded-input")

    def action_toggle_input(self) -> None:
        """Toggle expanded input."""
        self.expanded_input = not self.expanded_input

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="content_window"):
            yield InputText(id="results")
        yield MyTextArea(id="input", soft_wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(MyTextArea).focus()

    def action_focus_input(self) -> None:
        self.query_one(MyTextArea).focus()

    def action_reset_chat_session(self) -> None:
        self.chat_history = [SESSION_CONTEXT]
        window = self.query_one("#content_window")
        window.query("InputText").remove()
        window.query("ResponseText").remove()
        window.query("ResponseCode").remove()
        input_widget = self.query_one("#input", MyTextArea)
        input_widget.load_text("")
        input_widget.focus()

    def action_add_query(self, query_str) -> None:
        """Add next query section."""
        self.chat_history.append({"role": "user", "content": query_str})
        input_widget = self.query_one("#input", MyTextArea).load_text("")
        query_text = InputText(query_str)
        content_window = self.query_one("#content_window", VerticalScroll)
        content_window.mount(query_text)
        query_text.scroll_visible()
        return query_text

    def action_add_response_widget(self, widget):
        """Add next response section."""
        self.query_one("#content_window").mount(widget)
        # response_text.scroll_visible()
        return widget

    async def action_submit(self) -> None:
        """Submit chat text."""
        widget = self.query_one("#input", MyTextArea)
        query_str = widget.text
        if query_str:
            widget.clear()
            self.issue_query(query_str)
        else:
            pass

    @work(exclusive=True)
    async def issue_query(self, query_str: str) -> None:
        """Query chat gpt."""
        self.action_add_query(query_str=query_str)
        client = AsyncOpenAI(api_key=get_key())
        stream = await client.chat.completions.create(
            messages=self.chat_history,
            model=CONFIG["model"],
            stream=True,
        )
        await self.render_response(stream)

    async def render_response(self, stream):
        """Given a stream object, render response widgets.

        algo:
        - use parse_text(current_text) to identify text spans for widgets
        - create current_widget if it doesn't exist
        - if only one output, update display_text of current_widget
        - if multiple outputs, create new widgets for each output and make last one current_widget
        - append entire response to text history
        """
        # text for full response and current widget
        response_text = ""
        curr_text = ""
        # the latest widget; may be updated with streamed text
        current_widget = None

        async for part in stream:
            text_chunk = part.choices[0].delta.content or ""
            response_text += text_chunk
            curr_text += text_chunk
            outputs = parse_text(curr_text)

            # create current_widget if it doesn't exist
            if not current_widget and outputs:
                if outputs[0]["type"] == "code":
                    current_widget = ResponseText()
                else:
                    current_widget = ResponseText()
                self.action_add_response_widget(current_widget)

            # typical case: update display_text of current_widget
            if len(outputs) == 1:
                text = outputs[0]["text_span"]
                display_text = outputs[0]["display_text"]
                current_widget.set_text(text, display_text)

            # case where first widget should be updated, subsequent created
            elif len(outputs) > 1:
                text = outputs[0]["text_span"]
                display_text = outputs[0]["display_text"]
                for output in outputs[1:]:
                    if output["type"] == "code":
                        current_widget = ResponseText()
                    else:
                        current_widget = ResponseText()
                    current_widget.set_text(text, display_text)
                    self.action_add_response_widget(current_widget)
                curr_text = outputs[-1]["text_span"]

        self.update_chat_history(response_text)

    def update_chat_history(self, response_text: str):
        """update chat history with current response."""
        if response_text is not None:
            self.chat_history.append(
                {"role": "assistant", "content": str(response_text)}
            )


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
                    {"text_span": block, "display_text": block.strip(), "type": "text"}
                )
            # append code block
            block = text[child.start : child.end]
            output.append(
                {
                    "text_span": block,
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
            {"text_span": block, "display_text": block.strip(), "type": "text"}
        )
    return output


def test_parse_text():

    no_text_code = "just some non-code text"
    parse_text(no_text_code)
    assert parse_text(no_text_code) == [
        {
            "text_span": "just some non-code text",
            "display_text": "just some non-code text",
            "type": "text",
        }
    ]
    assert len(parse_text(no_text_code)[0]["text_span"]) == len(no_text_code)

    text_code_only = """```python\nprint("hello world")\n```"""
    assert parse_text(text_code_only) == [
        {
            "text_span": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")\n',
            "type": "code",
        }
    ]
    assert len(parse_text(text_code_only)[0]["text_span"]) == len(text_code_only)

    code_then_text = (
        """```python\nprint("hello world")\n```\n\n\n\nand some other stuff"""
    )
    assert parse_text(code_then_text) == [
        {
            "text_span": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {
            "text_span": "\n\n\nand some other stuff",
            "display_text": "and some other stuff",
            "type": "text",
        },
    ]
    assert sum([len(x["text_span"]) for x in parse_text(code_then_text)]) == len(
        code_then_text
    )

    text_then_code = """starting text, then:\n```python\nprint("hello world")\n```"""
    assert parse_text(text_then_code) == [
        {
            "text_span": "starting text, then:\n",
            "display_text": "starting text, then:",
            "type": "text",
        },
        {
            "text_span": '```python\nprint("hello world")\n```',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
    ]
    assert sum([len(x["text_span"]) for x in parse_text(text_then_code)]) == len(
        text_then_code
    )

    text_code_alternating = """```python\nprint("hello world")\n```\nok some more text, and\n```python\nprint("hello world")\n```\nend text here"""
    assert parse_text(text_code_alternating) == [
        {
            "text_span": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {
            "text_span": "ok some more text, and\n",
            "display_text": "ok some more text, and",
            "type": "text",
        },
        {
            "text_span": '```python\nprint("hello world")\n```\n',
            "display_text": 'print("hello world")\n',
            "type": "code",
        },
        {"text_span": "end text here", "display_text": "end text here", "type": "text"},
    ]
    assert sum([len(x["text_span"]) for x in parse_text(text_code_alternating)]) == len(
        text_code_alternating
    )


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

if __name__ == "__main__":
    app = ChatApp()
    app.run()
