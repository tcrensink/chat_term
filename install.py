#! /usr/bin/env python
import json
import os
import subprocess
import shutil
import sys

PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))

bash_func_str = f"""
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


def check_base_reqs() -> bool:
    """Check if tmux, poetry are installed (required for installation)."""

    return_val = True
    msg = ""
    if shutil.which("poetry") is None:
        msg += "Poetry not found; install Poetry before continuing: https://python-poetry.org/docs/#installation.\n"
        return_val = False
    if shutil.which("tmux") is None:
        msg += "tmux not found; install tmux before continuing.\n"
        return_val = False

    if return_val is False:
        msg += "Installation failed."
    else:
        msg += "Found poetry and tmux."
    print(msg)
    return return_val


def install_reqs():
    """Install python requirements with poetry."""
    output = subprocess.run(["poetry", "install"], capture_output=True, text=True)
    print(output.stdout)

    output = subprocess.run(["poetry", "install"], capture_output=True, text=True)
    if output.returncode != 0:
        error_message = output.stderr
        print(error_message)
        if "version" in error_message:
            print(f"use pyenv to install a specific version of python: https://github.com/pyenv/pyenv#getting-pyenv")
        sys.exit(1)

def main():
    print("This script will guide you through installation.\n")
    if not check_base_reqs():
        return

    while True:
        if os.path.exists("secrets.json"):
            print("secrets.json already exists, continuing...")
            break
        else:
            key_str = input(
                f"\nEnter openai_api_key (required). This will be stored in {PROJECT_FOLDER}/secrets.json: "
            )
            yn_resp = input(f"is this correct? (Y/n): {key_str}")
            if yn_resp.lower() in ("yes", "y", ""):
                set_openai_key(key_str)
                break

    resp = input("Install python requirements? (Y/n): ")
    if resp.lower() in ("yes", "y", ""):
        install_reqs()
        print("requirements installed.")

    while True:
        shell_file = input(
            "Provide a shell file that is sourced to add the `chat` function (e.g. ~/.bashrc, ~/.zshrc): "
        )
        shell_file = os.path.expanduser(shell_file)
        if os.path.exists(shell_file):
            try:
                with open(shell_file, "a") as shell_file:
                    shell_file.write(bash_func_str)
                    print(f"`chat` function added to {shell_file}.")
                    break
            except Exception as e:
                print(f"error writing to {shell_file}: {e}")
        else:
            print("shell file doesn't exist; try again.")

    print("installation complete.\n\nOpen a new shell session and type `chat`!")


if __name__ == "__main__":
    main()
