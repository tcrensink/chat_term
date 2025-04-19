import json
import os
import shutil

PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))
SECRETS_PATH = os.path.join(PROJECT_FOLDER, "secrets.json")
CONFIG_PATH = os.path.join(PROJECT_FOLDER, "config.json")


bash_func_str = f"""
function chat() {{
    bash "{PROJECT_FOLDER}/run.sh" "$@"
}}
"""


def get_secrets():
    """Get dictionary of secrets from file."""
    if os.path.exists(SECRETS_PATH):
        with open("secrets.json", "r") as fp:
            secrets = json.load(fp)
    return secrets


def write_secrets(secrets_json):
    with open(SECRETS_PATH, "w") as fp:
        json.dump(secrets_json, fp, sort_keys=True, indent=4)


def create_or_update_model_config_secret(model_config_id, secret):
    """Create a secret for a model_config_id in config.json."""
    secrets = get_secrets()
    secrets[model_config_id] = secret
    write_secrets(secrets)


def secret_exists(model_config_id):
    with open("secrets.json") as fp:
        secrets = json.load(fp)
        return bool(secrets.get(model_config_id))


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

    resp = input(
        f"Adjust model configs here: {CONFIG_PATH}\nCorresponding api keys are stored in {SECRETS_PATH}\n(press return)\n"
    )

    if not os.path.exists(SECRETS_PATH):
        write_secrets({})
    secrets = get_secrets()
    if not secrets.get("gpt"):
        resp = input("add an OPENAI_API_KEY to use the `gpt` model config? (Y/n)\n")
        if resp == "" or resp.lower().startswith("y"):
            api_key_resp = input("enter OPENAI_API_KEY:\n")
            secrets["gpt"] = api_key_resp
            write_secrets(secrets)

    while True:
        shell_path = input(
            "Provide a shell file path to add the `chat` function (e.g. ~/.bashrc, ~/.zshrc), or return to skip:\n"
        )
        shell_path = os.path.expanduser(shell_path)
        if shell_path == "":
            print("chat command not added to bash file")
            print(f"chat_term can also be run: `cd {PROJECT_FOLDER} && uv run app.py`")
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

    print("installation complete")
    if shell_path:
        print("run `source {shell_path}` and type `chat`")


if __name__ == "__main__":
    main()
