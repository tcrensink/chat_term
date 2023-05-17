#! /usr/bin/env python3

import json
import os

# This file asks user successive prompts; based on the result will update various code bits
print("This script will guide you through installation.\n")


PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))

bash_func_str = """
function chat() {{
    bash "{PROJECT_FOLDER}/run.sh" "$@"
}}
"""


def set_openai_key(key_string):
    # save api key to secrets.json
    if not os.path.exists("secrets.json"):
        os.system("touch secrets.json")
    with open("secrets.json", "w") as fp:
        json_data = {"OPENAI_API_KEY": key_string}
        json.dump(json_data, fp, sort_keys=True, indent=4)


def _guess_shell_file():
    """Guess the shell file used in the current shell (e.g. .bash_profile, .bashrc, .zshrc)"""
    shell = os.path.realpath(f"/proc/{os.getppid()}/exe")

    if "bash" in shell and os.path.exists(
        os.path.join(os.path.expanduser("~"), ".bash_profile")
    ):
        return os.path.join(os.path.expanduser("~"), ".bash_profile")

    if "bash" in shell and os.path.exists(
        os.path.join(os.path.expanduser("~"), ".bashrc")
    ):
        return os.path.join(os.path.expanduser("~"), ".bashrc")

    if "zsh" in shell and os.path.exists(
        os.path.join(os.path.expanduser("~"), ".zshrc")
    ):
        return os.path.join(os.path.expanduser("~"), ".zshrc")
    else:
        return None


def tmux_exists() -> bool:
    """Detect if tmux is installed."""
    if os.system("which tmux") == 0:
        return True
    return False


def main():
    print("This script will guide you through installation.")
    print("looking for tmux...")
    if not tmux_exists():
        print("Please install tmux and try again.")
        return

    while True:
        if os.path.exists("secrets.json"):
            raise Exception("secrets.json already exists; Delete it before proceeding.")
        key_str = input(
            f"\nEnter openai_api_key (required). This will be stored in {PROJECT_FOLDER}/secrets.json: "
        )
        yn_resp = input(f"is this correct? (y/n): {key_str}")
        if yn_resp.lower() in ("yes", "y", ""):
            set_openai_key(key_str)
            break

    resp = input("Install requirements? (y/n): ")
    if resp.lower() in ("yes", "y", ""):
        os.system("python3 -m pip install -r requirements.txt")
        print("requirements installed.")

    if shell_file := _guess_shell_file():
        resp = input(f"Add chat term to shell file {shell_file}? (y/n)")
        if resp.lower() in ("yes", "y", ""):
            with open(shell_file, "a") as shell_file:
                shell_file.write(bash_func_str.format(PROJECT_FOLDER=PROJECT_FOLDER))
                print(f"'function `chat` added to {str(shell_file)}.")
    else:
        input(
            "unable to determine shell file. Add the following function to your e.g. .bashrc (press return to continue):"
        )
        print(bash_func_str.format(PROJECT_FOLDER=PROJECT_FOLDER))

    print("installation complete.\n\nOpen a new session and type `chat`!")


if __name__ == "__main__":
    main()
