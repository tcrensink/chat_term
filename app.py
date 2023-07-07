#!/usr/bin/env python3
import os
import json
import openai
import pyperclip
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, Footer, Static, Label
from textual.containers import VerticalScroll


# stores chat history until reset.
SESSION_CONTEXT = {
    "role": "system",
    "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible. If you are not sure, just say 'I don't know'.",
}


try:
    BASE_PATH = os.path.dirname(__file__)
except NameError:
    BASE_PATH = os.getcwd()

with open(os.path.join(BASE_PATH, "config.jsonc")) as fp:
    lines = fp.readlines()
    json_str = "".join(
        [line for line in lines if not line.lstrip().startswith("//")])
    CONFIG = json.loads(json_str)


def set_key():
    secrets_file = os.path.join(BASE_PATH, "secrets.json")
    with open(secrets_file) as fp:
        secrets = json.load(fp)
        OPENAI_API_KEY = secrets.get("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise Exception("OPENAI_API_KEY in secrets.json is required")
        openai.api_key = OPENAI_API_KEY


class InputText(Static):
    """Formatted widget that contains prompt text."""


class ResponseText(Static):
    """Formatted widget that contains response text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = ""

    def append_text(self, new_text):
        self._text += new_text
        self.update(self._text)

    def clear_text(self):
        self._text = ""
        self.update(self._text)


class ChatApp(App):
    """chat TUI"""

    CSS_PATH = "chat.css"
    BINDINGS = [tuple(k) for k in CONFIG["keybindings"]]
    chat_history = [SESSION_CONTEXT]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="content_window"):
            yield InputText(id="results")
        yield Input(id="input", placeholder="Send a message...")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    def action_copy_text(self) -> None:
        try:
            pyperclip.copy(str(self.chat_history))
        except Exception as e:
            print(e, "copy to clipboard failed")

    def action_focus_input(self) -> None:
        self.query_one(Input).focus()

    def action_reset_chat_session(self) -> None:
        self.chat_history = [SESSION_CONTEXT]
        window = self.query_one("#content_window")
        window.query("InputText").remove()
        window.query("ResponseText").remove()
        input_widget = self.query_one("#input", Input)
        input_widget.value = ""
        input_widget.focus()

    def action_add_query(self, query_str) -> None:
        """Add next query section."""
        self.chat_history.append(
            {"role": "user", "content": query_str}
        )
        input_widget = self.query_one("#input", Input).value = ""
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

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "input":
            query_str = self.query_one("#input", Input).value
            if query_str:
                self.issue_query(query_str)
            else:
                pass

    @work(exclusive=True)
    async def issue_query(self, query_str: str) -> None:
        """Query chat gpt."""
        self.action_add_query(query_str=query_str)
        response_text = self.action_add_response()
        current_response = ""
        async for chunk in await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=self.chat_history,
            stream=True,
        ):
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content is not None:
                current_response += content
                response_text.append_text(content)

        if current_response is not None:
            self.chat_history.append(
                {"role": "assistant", "content": str(current_response)})


if __name__ == "__main__":

    set_key()
    app = ChatApp()
    app.run()
