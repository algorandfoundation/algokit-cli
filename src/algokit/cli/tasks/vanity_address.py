import json
import logging
import re
from multiprocessing import Manager, Pool, cpu_count
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.synchronize import Lock as LockBase
from pathlib import Path
from timeit import default_timer as timer

import algosdk
import click
from algosdk import mnemonic

logger = logging.getLogger(__name__)
SECOND = 5


@click.command(
    name="vanity-address",
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
    default="start",
    type=click.Choice(["start", "anywhere", "end"]),
    help="Location where the keyword will be included. Default is start.",
)
@click.option(
    "--output",
    "-o",
    required=False,
    default="stdout",
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
        raise click.ClickException("Invalid KEYWORD. It can only include uppercase letters A-Z and numbers 2-7.")

    if output == "alias" and alias is None:
        raise click.ClickException(
            "The '--alias' option must be provided when setting the '--output' option to "
            "'alias'. Please specify an alias for the generated address using '--alias'."
        )

    if output == "file" and output_file is None:
        raise click.ClickException(
            "When setting the '--output' option to 'file', you must also provide a path to the "
            "output file using the '--output-file' option. Please specify the desired file path "
            "and try again."
        )

    manager = Manager()
    shared_dict = manager.dict()
    shared_dict["count"] = 0
    lock = manager.Lock()
    stop_event = manager.Event()

    start: float = timer()
    with Pool(processes=cpu_count()) as pool:
        for _ in range(cpu_count()):
            pool.apply(generate_vanity_address, (keyword, match, start, lock, stop_event, shared_dict))

        pool.close()
        pool.join()

    end: float = timer()

    result_data: dict[str, str] = {k: v for k, v in shared_dict.items() if k in ["mnemonic", "address"]}
    if output == "stdout":
        logger.warning(
            "Your mnemonic is displayed on the console. "
            "Ensure its security by keeping it confidential."
            "Consider clearing your terminal history after noting down the token.\n"
        )

        click.echo(result_data)

    elif output == "alias" and alias is not None:
        add_to_wallet(alias, result_data)
    elif output == "file" and output_file is not None:
        output_path = Path(output_file)
        with output_path.open("w") as f:
            json.dump(result_data, f, indent=4)

    logger.info(f"Execution Time: {end - start:.2f} seconds")


def generate_vanity_address(  # noqa: PLR0913
    keyword: str,
    match: str,
    start_time: float,
    lock: LockBase,
    stop_event: EventClass,
    shared_dict: DictProxy,
) -> None:
    last_log_time = start_time
    while not stop_event.is_set():
        private_key, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]
        generated_mnemonic = mnemonic.from_private_key(private_key)  # type: ignore[no-untyped-call]
        with lock:
            shared_dict["count"] += 1
        if (
            (match == "start" and address.startswith(keyword))
            or (match == "anywhere" and keyword in address)
            or (match == "end" and address.endswith(keyword))
        ):
            stop_event.set()

            if shared_dict is not None:
                shared_dict["mnemonic"] = generated_mnemonic
                shared_dict["address"] = address

            return
        elapsed_time = timer() - last_log_time
        waiting_time = timer() - start_time
        if elapsed_time >= SECOND:
            log_progress(shared_dict["count"], waiting_time)
            last_log_time = timer()


def log_progress(count: int, waiting_time: float) -> None:
    logger.info(
        f"We are still searching for a match. Please be patient. current number of addresses generated is {count}"
        f" in the past {waiting_time:.2f} seconds"
    )


def add_to_wallet(alias: str, output_data: dict) -> None:
    logger.info(f"Adding {output_data} to wallet {alias}")
