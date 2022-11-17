from pathlib import Path

import click

AppName = "algokit"


def get_config_dir():
    return Path(click.get_app_dir(AppName))


def read(file_name: str):
    return get_config_dir().joinpath(file_name).read_text("utf-8")


def write(file_name: str, content: str):
    get_config_dir().mkdir(parents=True, exist_ok=True)
    config_file = get_config_dir().joinpath(file_name)
    click.echo(click.style(f"Writing content to {config_file}", fg="blue"))
    config_file.write_text(content, "utf-8")
