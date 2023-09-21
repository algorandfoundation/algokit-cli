import json
import logging
import re
import time
from multiprocessing import Event, Manager, Pool, cpu_count
from pathlib import Path
from timeit import default_timer as timer

import algosdk
import click

logger = logging.getLogger(__name__)
stop_event = Event()


@click.command(
    name="vanity_address",
    help="""Generate a vanity Algorand address. Your KEYWORD can only include letters A - Z and numbers 2 - 7.
    Keeping your KEYWORD under 5 characters will usually result in faster generation.
    Note: The longer the KEYWORD, the longer it may take to generate a matching address.
    Please be patient if you choose a long keyword.
    """,
)
@click.argument("keyword")
@click.option(
    "--match",
    "-m",
    default="Start",
    type=click.Choice(["Start", "Anywhere", "End"]),
    help="Location where the keyword will be included. Default is Start.",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Choice(["stdout", "alias", "file"]),
    help="How the output will be presented.",
)
@click.option("--alias", "-a", required=False, help='Alias for the address. Required if output is "alias".')
@click.option(
    "--output-file",
    "-f",
    required=False,
    type=click.Path(),
    help='File to dump the output. Required if output is "file".',
)
def vanity_address(
    keyword: str, match: str, output: str, alias: str | None = None, output_file: str | None = None
) -> None:
    if not re.match("^[A-Z2-7]+$", keyword):
        click.echo("Invalid KEYWORD. It can only include letters A-Z and numbers 2-7.")
        return

    if output == "alias" and alias is None:
        click.echo("Alias is required when output is set to 'alias'")
        return

    if output == "file" and output_file is None:
        click.echo("Output file is required when output is set to 'file'")
        return

    manager = Manager()
    shared_dict = manager.dict()

    start: float = timer()
    logger.info(f"start: {start}")
    with Pool(processes=cpu_count()) as pool:
        for _ in range(cpu_count()):
            pool.apply_async(generate_vanity_address, (keyword, match, shared_dict))

        pool.close()
        pool.join()

    end: float = timer()

    result_data = shared_dict.get("result", None)
    if output == "stdout":
        click.echo(result_data[1])
    elif output == "alias" and alias is not None:
        add_to_wallet(alias, result_data[1])
    elif output == "file" and output_file is not None:
        output_path = Path(output_file)
        with output_path.open("w") as f:
            json.dump(result_data[1], f)
    logger.info(f"Execution Time: {end - start:.4f} seconds")


def generate_vanity_address(keyword: str, match: str, shared_dict: dict | None = None) -> None:
    while not stop_event.is_set():
        private_key, address = algosdk.account.generate_account()
        if (
            (match == "Start" and address.startswith(keyword))
            or (match == "Anywhere" and keyword in address)
            or (match == "End" and address.endswith(keyword))
        ):
            stop_event.set()
            if shared_dict is not None:
                shared_dict["result"] = (private_key, address)

            return


def show_progress() -> None:
    while not stop_event.is_set():
        time.sleep(5)


def add_to_wallet(alias: str, output_data: str) -> None:
    logger.info(f"Adding {output_data} to wallet {alias}")
