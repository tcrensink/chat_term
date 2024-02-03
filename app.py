#!/usr/bin/env python
import os
import json
from openai import AsyncOpenAI
import pyperclip
from textual.binding import Binding
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Label, TextArea
from textual.containers import VerticalScroll
from textual import events
from textual.reactive import var

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


class ResponseText(Static):
    """Formatted widget that contains response text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = ""

    def on_click(self) -> None:
        """Visual feedback if copy successful"""
        copied = copy_to_clipboard(self._text)
        if copied:
            self.styles.opacity = 0.0
            self.styles.animate(
                attribute="opacity", value=1.0, duration=0.3, easing="out_expo"
            )

    def append_text(self, new_text):
        self._text += new_text
        self.update(self._text)

    def clear_text(self):
        self._text = ""
        self.update(self._text)


class MyTextArea(TextArea):
    BINDINGS = [tuple(k) for k in CONFIG["keybindings"]] + [
        Binding("ctrl+c", "", "", show=False)
    ]
    show_line_numbers = CONFIG["show_line_numbers"]


class ChatApp(App):
    """chat TUI"""

    CSS_PATH = "chat.css"
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

    def action_add_response(self) -> None:
        """Add next response section."""
        response_text = ResponseText()
        self.query_one("#content_window").mount(response_text)
        response_text.scroll_visible()
        return response_text

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
        response_text = self.action_add_response()
        current_response = ""
        client = AsyncOpenAI(api_key=get_key())
        stream = await client.chat.completions.create(
            messages=self.chat_history,
            model=CONFIG["model"],
            stream=True,
        )
        async for part in stream:
            content = part.choices[0].delta.content or ""
            if content is not None:
                current_response += content
                response_text.append_text(content)

        if current_response is not None:
            self.chat_history.append(
                {"role": "assistant", "content": str(current_response)}
            )


if __name__ == "__main__":
    app = ChatApp()
    app.run()
