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
    # save API key to secrets.json
    if os.path.exists("secrets.json"):
        with open("secrets.json", "r") as fp:
            secrets = json.load(fp)
    else:
        secrets = {}
    secrets["OPENAI_API_KEY"] = key_string
    with open("secrets.json", "w") as fp:
        json.dump(secrets, fp, sort_keys=True, indent=4)


def openai_api_key_exists():
    with open("secrets.json") as fp:
        secrets = json.load(fp)
        return bool(secrets.get("OPENAI_API_KEY"))


def check_base_reqs() -> bool:
    """Check if tmux, uv are installed (required for installation)."""

    return_val = True
    msg = ""
    if shutil.which("uv") is None:
        msg += "install uv to continue: https://docs.astral.sh/uv/getting-started/installation/.\n"
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


def main():
    print("This script will guide you through installation...\n")
    if not check_base_reqs():
        return

    if not os.path.exists("secrets.json"):
        set_openai_key("")
    if not openai_api_key_exists():
        resp = input("add OPENAI_API_KEY to ./secrets.json:\n")
        if resp:
            set_openai_key(resp)

    while True:
        shell_path = input(
            "Provide a shell file path to add the `chat` function (e.g. ~/.bashrc, ~/.zshrc), or return to skip:\n"
        )
        shell_path = os.path.expanduser(shell_path)
        if shell_path == "":
            print("chat command not added.")
            break
        elif os.path.exists(shell_path):
            try:
                with open(shell_path, "a") as fp:
                    fp.write(bash_func_str)
                    print(f"`chat` function added to {shell_path}.")
                    break
            except Exception as e:
                print(f"error writing to {shell_path}: {e}")
        else:
            print(f"shell file not found at {shell_path}.")

    print("installation complete.\n\nOpen a new shell session and type `chat`!")


if __name__ == "__main__":
    main()
