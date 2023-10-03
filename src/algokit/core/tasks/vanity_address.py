import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from multiprocessing import Manager, Pool, cpu_count
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Event as EventClass
from timeit import default_timer as timer

import algosdk
from algosdk import mnemonic

logger = logging.getLogger(__name__)

PROGRESS_REFRESH_INTERVAL_SECONDS = 5


class MatchType(Enum):
    START = "start"
    ANYWHERE = "anywhere"
    END = "end"


MatchFunction = Callable[[str, str], bool]

MATCH_FUNCTIONS: dict[MatchType, MatchFunction] = {
    MatchType.START: lambda addr, keyword: addr.startswith(keyword),
    MatchType.ANYWHERE: lambda addr, keyword: keyword in addr,
    MatchType.END: lambda addr, keyword: addr.endswith(keyword),
}


@dataclass
class VanityAccount:
    mnemonic: str
    address: str
    private_key: str


def _log_progress(shared_data: DictProxy, stop_event: EventClass, start_time: float) -> None:
    """Logs progress of address matching at regular intervals."""
    last_log_time = start_time

    try:
        while not stop_event.is_set():
            total_count = sum(count.value for count in shared_data["counts"])
            if timer() - last_log_time >= PROGRESS_REFRESH_INTERVAL_SECONDS:
                elapsed_time = timer() - start_time
                message = (
                    f"Iterated over ~{total_count} addresses in {elapsed_time:.2f} seconds."
                    if total_count > 0
                    else f"Elapsed time: {elapsed_time:.2f} seconds."
                )
                logger.info(f"Still searching for a match. {message}")
                last_log_time = timer()
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()


def _search_for_matching_address(
    worker_id: int, keyword: str, match: MatchType, stop_event: EventClass, shared_data: DictProxy
) -> None:
    """
    Searches for a matching address based on the specified keyword and matching criteria.

    Args:
        keyword (str): The keyword to search for in the address.
        match (MatchType): The matching criteria for the keyword. It can be "start" to match addresses that start with
        the keyword, "anywhere" to match addresses that contain the keyword anywhere,
        or "end" to match addresses that end with the keyword.
        lock (LockBase): A multiprocessing lock object to synchronize access to the shared data.
        stop_event (EventClass): A multiprocessing event object to stop the search when a match is found.
        shared_data (DictProxy): A multiprocessing dictionary to share data between processes.
    """

    local_count = 0
    batch_size = 1000 * (cpu_count() - 1)

    try:
        while not stop_event.is_set():
            private_key, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]

            local_count += 1

            if local_count % batch_size == 0:
                shared_data["counts"][worker_id].value += local_count
                local_count = 0

            if MATCH_FUNCTIONS[match](address, keyword):
                stop_event.set()
                generated_mnemonic = mnemonic.from_private_key(private_key)  # type: ignore[no-untyped-call]
                shared_data.update({"mnemonic": generated_mnemonic, "address": address})
                return
    except KeyboardInterrupt:
        stop_event.set()


def generate_vanity_address(keyword: str, match: MatchType) -> VanityAccount:
    """
    Generate a vanity address in the Algorand blockchain.

    Args:
        keyword (str): The keyword to search for in the address.
        match (MatchType): The matching criteria for the keyword. It can be "start" to match addresses that start with
        the keyword, "anywhere" to match addresses that contain the keyword anywhere,
        or "end" to match addresses that end with the keyword.

    Returns:
        VanityAccount: An object containing the generated mnemonic and address
        that match the specified keyword and matching criteria.
    """

    manager = Manager()
    num_processes = cpu_count()
    shared_data = manager.dict()
    shared_data["counts"] = [manager.Value("i", 0) for _ in range(num_processes - 1)]
    stop_event = manager.Event()

    start_time: float = timer()
    pool = Pool(processes=num_processes)
    try:
        for worker_id in range(num_processes - 1):
            pool.apply_async(_search_for_matching_address, (worker_id, keyword, match, stop_event, shared_data))

        # Start the logger process
        pool.apply_async(_log_progress, (shared_data, stop_event, start_time))

        pool.close()
        pool.join()
    except KeyboardInterrupt as ex:
        stop_event.set()
        pool.terminate()
        pool.join()
        raise ex

    logger.debug(f"Vanity address generation time: {timer() - start_time:.2f} seconds")

    if "mnemonic" not in shared_data or "address" not in shared_data:
        raise Exception("No matching account was found")

    return VanityAccount(
        mnemonic=shared_data["mnemonic"],
        address=shared_data["address"],
        private_key=mnemonic.to_private_key(shared_data["mnemonic"]),  # type: ignore[no-untyped-call]
    )
