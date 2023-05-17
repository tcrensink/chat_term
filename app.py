#!/usr/bin/env python3
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, Markdown, Button, Footer, Static
from textual.containers import VerticalScroll

import os
import json
import openai
import pyperclip


def set_key():
    secrets_file = os.path.join(os.path.dirname(__file__), "secrets.json")
    with open(secrets_file) as fp:
        secrets = json.load(fp)
        OPENAI_API_KEY = secrets.get("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise Exception("OPENAI_API_KEY in secrets.json is required")
        openai.api_key = OPENAI_API_KEY


class Prompt(Static):
    """Prompt input + submit button."""

    def compose(self) -> ComposeResult:
        yield Input(id="input", placeholder="return to submit query; ctrl-c to detach")
        yield Button("copy text", id="copy")


class MarkdownMem(Markdown):
    """Markdown widget that stores text content."""

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
    """llm chat."""

    CSS_PATH = "chat.css"
    BINDINGS = [
        ("shift+right", "copy_text()", "Copy response text"),
        ("shift+up", "focus_input()", "focus input"),
    ]

    def compose(self) -> ComposeResult:
        yield Prompt()
        with VerticalScroll(id="markdown"):
            yield MarkdownMem(id="results")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    def action_copy_text(self) -> None:
        markdown_mem = self.query_one("#results", Markdown)
        try:
            pyperclip.copy(markdown_mem._text)
        except Exception as e:
            print(e, "copy to clipboard failed")

    def action_focus_input(self) -> None:
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "input":
            query_str = self.query_one("#input", Input).value
            if query_str:
                self.issue_query(query_str)
            else:
                self.query_one("#results", Markdown).update("(prompt is empty)")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """A coroutine to handle a text changed prompt."""
        self.action_copy_text()

    @work(exclusive=True)
    async def issue_query(self, query_str: str) -> None:
        """Query chat gpt."""
        markdown_mem = self.query_one("#results", Markdown)
        markdown_mem.clear_text()
        async for chunk in await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible. If you are not sure, just say 'I don't know'.",
                },
                {
                    "role": "user",
                    "content": query_str,
                },
            ],
            stream=True,
        ):
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content is not None:
                markdown_mem.append_text(content)

    def make_word_markdown(self, results: object) -> str:
        """Convert the results in to markdown."""
        return results


if __name__ == "__main__":

    set_key()
    app = ChatApp()
    app.run()
