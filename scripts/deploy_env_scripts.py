
import json
import os
import shutil
import sys

"""
    Creates env scripts to use PYTHONUSERSITE in our conda env
    Following these instructions on how to set this up:
    https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux

    Expected usage:
    ```
    conda activate openwpm
    conda info --json | python deploy_env_scripts.py
    conda activate openwpm
    ```

    This script aims to be plattform independent and idempotent
"""

CONDA_SCRIPT_DIR = "./etc/conda"


def main():
    conda_config = json.load(sys.stdin)
    conda_prefix = conda_config["active_prefix"]
    target_dir = os.path.join(conda_prefix, CONDA_SCRIPT_DIR)
    current_dir = os.path.dirname(__file__)
    shutil.copytree(os.path.join(current_dir, "conda_scripts"),
                    target_dir, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
