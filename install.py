#! /usr/bin/env python

import json
import os

# This file asks user successive prompts; based on the result will update various code bits
print("This script will guide you through installation.\n")


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
        os.system("python -m pip install -r requirements.txt")
        print("requirements installed.")


    while True:
        shell_file = input("Provide a shell file that is sourced to add the `chat` function (e.g. ~/.bashrc, ~/.zshrc): ")
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
