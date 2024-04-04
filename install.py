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


def set_api_key(key_string):
    # save api key to secrets.json
    if not os.path.exists("secrets.json"):
        with open("secrets.json", "w") as fp:
            json.dump({}, fp)  # Create an empty JSON object if file doesn't exist
    with open("secrets.json", "r+") as fp:
        json_data = json.load(fp)
        json_data["API_KEY"] = key_string
        fp.seek(0)  # Move the file pointer to the beginning
        json.dump(json_data, fp, sort_keys=True, indent=4)
        fp.truncate()  # Truncate the file to remove any remaining data


def set_base_url(url_string):
    # save base url to secrets.json
    if not os.path.exists("secrets.json"):
        with open("secrets.json", "w") as fp:
            json.dump({}, fp)
    with open("secrets.json", "r+") as fp:
        json_data = json.load(fp)
        if "openrouter" in url_string.lower():
            json_data["BASE_URL"] = "https://openrouter.ai/api/v1"
            # Set default model to google/gemma-7b-it:free if base URL contains openrouter
            json_data["MODEL"] = "google/gemma-7b-it:free"
        else:
            json_data["BASE_URL"] = "https://api.openai.com/v1"   
            json_data["MODEL"] = "gpt-4"
        fp.seek(0)
        json.dump(json_data, fp, sort_keys=True, indent=4)
        fp.truncate()

def set_base_model(model_string):
    # Save model to secrets.json if model_string is not empty
    if model_string:
        if not os.path.exists("secrets.json"):
            with open("secrets.json", "w") as fp:
                json.dump({"MODEL": model_string}, fp, sort_keys=True, indent=4)
        else:
            with open("secrets.json", "r+") as fp:
                json_data = json.load(fp)
                if "MODEL" in json_data:
                    json_data["MODEL"] = model_string
                    fp.seek(0)
                    json.dump(json_data, fp, sort_keys=True, indent=4)
                    fp.truncate()



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
        msg += "Base requirements satisfied."
    print(msg)
    return return_val


def install_reqs():
    """Install python requirements with poetry."""
    output = subprocess.run(["poetry", "install"], capture_output=True, text=True)
    print(output.stdout)


def main():
    print("This script will guide you through installation.\n")
    if not check_base_reqs():
        return

    while True:
        if os.path.exists("secrets.json"):
            print("secrets.json already exists, continuing...")
            break
        else:
            base_url_str = input(
                f"\n[1/3] All settings will be stored in {PROJECT_FOLDER}/secrets.json.\n[OPTINAL] Type openreouter or leave Empty for default: "
            )
            key_str = input(
                f"\n[2/3] REQUIRED.\nProvide your api_key [openai/openrouter] : "
            )
            model_str = input(
                f"\n[3/3] defaults: openai/gpt-4, openrouter/gemma-7b .\nType model name or leave Empty for defaults: "
            )
            set_api_key(key_str)
            set_base_url(base_url_str)
            set_base_model(model_str)
    
            yn_resp = input(f"is this correct? (y/n): {key_str}, {base_url_str}, {model_str} (y/n): ")
            if yn_resp.lower() in ("yes", "y", ""):
                """ set_api_key(key_str)
                set_base_url(base_url_str)
                set_base_model(model_str) """
                break

    resp = input("Install python requirements? (y/n): ")
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
