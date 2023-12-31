from ..constants import *
import requests
import subprocess
import configparser
import click
import os


def check_git_installed(func):
    def wrapper(*args, **kwargs):
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return func(*args, **kwargs)
        except subprocess.CalledProcessError:
            click.echo("Git is not installed or not available")

    return wrapper


class Git:
    def __init__(self):
        self.repo_name = "pyplater-templates"
        self.repo_path = BASE_PATH
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini"
        )

    @check_git_installed
    def push(self, folder: str) -> bool:
        folder_path = "-A" if folder == "all" else folder
        # Initialize the Git repository if Origin does not exist
        if not self._origin_branch_exists():
            try:
                subprocess.check_call(["git", "init"], cwd=self.repo_path)
                subprocess.check_call(
                    ["git", "branch", "-M", "main"], cwd=self.repo_path
                )
            except subprocess.CalledProcessError:
                return False

        try:
            # Add all files in the folder to the Git repository
            subprocess.check_call(["git", "add", folder_path], cwd=self.repo_path)

            # Commit the changes
            subprocess.check_call(
                ["git", "commit", "-m", f"Add {folder} to pyplater repository"],
                cwd=self.repo_path,
            )

            # Initialize the Git repository if Remote does not exist
            if not self._remote_branch_exists():
                remote_url = (
                    f"https://github.com/{self.get_github_user()}/{self.repo_name}.git"
                )
                try:
                    subprocess.check_call(
                        ["git", "remote", "add", "origin", remote_url],
                        cwd=self.repo_path,
                    )
                except subprocess.CalledProcessError:
                    return False

            # Push the changes to the remote repository
            subprocess.check_call(
                ["git", "push", "-u", "origin", "main"], cwd=self.repo_path
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @check_git_installed
    def pull(self, folder: str) -> bool:
        if folder == "all":
            try:
                subprocess.check_call(["git", "pull"], cwd=self.repo_path)
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            try:
                subprocess.check_call(
                    ["git", "checkout", "origin/main", "--", f"{folder}"],
                    cwd=self.repo_path,
                )
                return True
            except subprocess.CalledProcessError:
                return False

    @check_git_installed
    def create_repo(self, token: str) -> bool:
        create_url = "https://api.github.com/user/repos"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "name": "pyplater-templates",
            "description": "Project Templates Generated by pyplater-cli",
        }
        create_response = requests.post(create_url, headers=self.headers, json=payload)
        if create_response.status_code == 201:
            return True
        else:
            return False

    @check_git_installed
    def repo_exists(self, token: str) -> bool:
        url = f"https://api.github.com/repos/{self.get_github_user()}/{self.repo_name}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(url, headers=self.headers)
        return response.status_code == 200

    @check_git_installed
    def _origin_branch_exists(self) -> bool:
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.repo_path
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @check_git_installed
    def _remote_branch_exists(self) -> bool:
        try:
            subprocess.check_call(
                ["git", "remote", "get-url", "origin"], cwd=self.repo_path
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def set_github_user(self, username: str) -> None:
        config = configparser.ConfigParser()
        config.read(self.config_path)
        config["GitHub"] = {"username": username}
        with open(self.config_path, "w") as configfile:
            config.write(configfile)

    def get_github_user(self) -> str | bool:
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            username = config.get("GitHub", "username")
        except configparser.NoSectionError:
            return False
        return username
