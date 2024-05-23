#!/usr/bin/env python
import os
import json
from openai import AsyncOpenAI
import pyperclip
from textual.binding import Binding
from textual import events, work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Label, TextArea
from textual.containers import VerticalScroll
from textual.reactive import var
from parse_utils import parse_text, MinimalMarkdown
from textual.reactive import Reactive
from rich.style import Style

# stores chat history until reset.
SESSION_CONTEXT = {
    "role": "system",
    "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as accurately and concisely as possible. If you are not sure, just say 'I don't know'. Respond in markdown (without backticks) unless otherwise specified.",
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


class ResponseCode(Static):
    """Widget that contains code block.

    Separate from ResponseText to allow syntax highlighting.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw_text = ""
        self._display_text: Reactive = Reactive("")

    def on_click(self) -> None:
        """copy extracted code block to clipboard"""
        copied = copy_to_clipboard(self._display_text)
        if copied:
            self.styles.opacity = 0.0
            self.styles.animate(
                attribute="opacity", value=1.0, duration=0.3, easing="out_expo"
            )

    def set_text(self, text, display_text):
        self._raw_text = text
        self._display_text = display_text
        self.update(
            MinimalMarkdown(self._raw_text, hyperlinks=False, code_theme="nord-darker")
        )


class ResponseText(Static):
    """Formatted widget that contains response text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw_text = ""
        self._display_text: Reactive = Reactive("")

    def on_click(self) -> None:
        """Visual feedback if copy successful"""
        copied = copy_to_clipboard(self._display_text)
        if copied:
            self.styles.opacity = 0.0
            self.styles.animate(
                attribute="opacity", value=1.0, duration=0.3, easing="out_expo"
            )

    def set_text(self, text, display_text):
        self._raw_text = text
        self._display_text = display_text
        self.update(
            MinimalMarkdown(self._raw_text, hyperlinks=False, code_theme="nord-darker")
        )


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
        widget.scroll_visible()
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

        - parse_text(curr_text) splits text into code and text blocks
        - create current_widget if it doesn't exist
        - update text of first/current widget (often only)
        - if multiple outputs, create new widget for each output, mark last one current_widget
        - append entire response to text history
        """

        response_text = ""
        curr_text = ""
        # widget being updated
        current_widget = None

        async for part in stream:
            text_chunk = part.choices[0].delta.content or ""
            response_text += text_chunk
            curr_text += text_chunk
            outputs = parse_text(curr_text)

            # create current_widget if it doesn't exist
            if outputs:
                if not current_widget:
                    if outputs[0]["type"] == "code":
                        current_widget = ResponseCode()
                    else:
                        current_widget = ResponseText()
                    self.action_add_response_widget(current_widget)

                # always update first (often only) widget
                text = outputs[0]["raw_text"]
                display_text = outputs[0]["display_text"]
                current_widget.set_text(text, display_text)

                # create new widgets for each additional output; make last one current_widget
                for output in outputs[1:]:
                    text = output["raw_text"]
                    display_text = output["display_text"]
                    if output["type"] == "code":
                        current_widget = ResponseCode()
                    else:
                        current_widget = ResponseText()
                    current_widget.set_text(text, display_text)
                    self.action_add_response_widget(current_widget)
                # curr_text set by last widget
                curr_text = outputs[-1]["raw_text"]

        self.update_chat_history(response_text)

    def update_chat_history(self, response_text: str):
        """update chat history with current response."""
        if response_text is not None:
            self.chat_history.append(
                {"role": "assistant", "content": str(response_text)}
            )


if __name__ == "__main__":
    app = ChatApp()
    app.run()
