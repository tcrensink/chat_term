#! /usr/bin/env python
import json
import os
import subprocess
import shutil

PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))

bash_func_str = f"""
function chat() {{
    bash "{PROJECT_FOLDER}/run.sh" "$@"
}}
"""


def set_openai_key(key_string):
    # save api key to secrets.json
    os.system("touch secrets.json")
    with open("secrets.json", "w") as fp:
        json_data = {"OPENAI_API_KEY": key_string}
        json.dump(json_data, fp, sort_keys=True, indent=4)


def openai_api_key_exists():
    with open("secrets.json") as fp:
        secrets = json.load(fp)
        return bool(secrets.get("OPENAI_API_KEY"))


def check_base_reqs() -> bool:
    """Check if tmux, uv are installed (required for installation)."""

    return_val = True
    msg = ""
    if shutil.which("uv") is None:
        msg += "install uv tp continue: https://docs.astral.sh/uv/getting-started/installation/.\n"
        return_val = False
    if shutil.which("tmux") is None:
        msg += "tmux not found; install tmux to continue.\n"
        return_val = False

    if return_val is False:
        msg += "Installation failed."
    else:
        msg += "Found uv and tmux..."
    print(msg)
    return return_val


def install_reqs():
    """Install python requirements with uv."""
    output = subprocess.run(["uv", "sync"], capture_output=True, text=True)
    print(output.stdout)


def main():
    print("This script will guide you through installation.\n")
    if not check_base_reqs():
        return

    if not os.path.exists("secrets.json"):
        set_openai_key("")
    if not openai_api_key_exists():
        resp = input("add openai_api_key to `secrets.json`:\n")
        if resp:
            set_openai_key(resp)

    print("installing python environment...")
    install_reqs()

    while True:
        shell_file = input(
            "Provide a shell file path to add the `chat` function (e.g. ~/.bashrc, ~/.zshrc), or return to skip:"
        )
        shell_file = os.path.expanduser(shell_file)
        if shell_file == "":
            print("chat command not added.")
            break
        elif os.path.exists(shell_file):
            try:
                with open(shell_file, "a") as shell_file:
                    shell_file.write(bash_func_str)
                    print(f"`chat` function added to {shell_file}.")
                    break
            except Exception as e:
                print(f"error writing to {shell_file}: {e}")
        else:
            print("shell file not found; try again.")

    print("installation complete.\n\nOpen a new shell session and type `chat`!")


if __name__ == "__main__":
    main()
