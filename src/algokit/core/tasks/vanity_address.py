import logging
import multiprocessing
import signal
import time
import types
import typing
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from multiprocessing import Process, Queue, cpu_count
from timeit import default_timer as timer

import algosdk
from algosdk.mnemonic import from_private_key, to_private_key

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


class Counter:
    def __init__(self, initial_value: int = 0):
        self.val = multiprocessing.RawValue("i", initial_value)
        self.lock = multiprocessing.Lock()

    def increment(self, value: int = 1) -> None:
        with self.lock:
            self.val.value += value

    @property
    def value(self) -> int:
        return int(self.val.value)


def _log_progress(counter: Counter, start_time: float) -> None:
    """Logs progress of address matching at regular intervals."""
    last_log_time = start_time

    try:
        while True:
            total_count = counter.value
            if timer() - last_log_time >= PROGRESS_REFRESH_INTERVAL_SECONDS:
                elapsed_time = timer() - start_time
                message = (
                    f"Iterated over ~{total_count} addresses in {elapsed_time:.2f} seconds."
                    if total_count > 0
                    else f"Elapsed time: {elapsed_time:.2f} seconds."
                )
                logger.info(f"Still searching for a match. {message}")
                last_log_time = timer()
            time.sleep(PROGRESS_REFRESH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        return


def _search_for_matching_address(keyword: str, match: MatchType, counter: Counter, queue: Queue) -> None:
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

    try:
        local_count = 0
        batch_size = 100

        while True:
            private_key, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]
            local_count += 1
            if local_count % batch_size == 0:
                counter.increment(local_count)
                local_count = 0

            if MATCH_FUNCTIONS[match](address, keyword):
                generated_mnemonic = from_private_key(private_key)  # type: ignore[no-untyped-call]
                queue.put((address, generated_mnemonic))
                return
    except KeyboardInterrupt:
        return


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
    jobs: list[Process] = []

    def signal_handler(sig: int, frame: types.FrameType | None) -> typing.NoReturn:
        logger.debug(f"KeyboardInterrupt captured for {sig} and frame {frame}. Terminating processes...")
        for p in jobs:
            p.terminate()
        raise KeyboardInterrupt

    num_processes = cpu_count()
    logger.info(f"Using {num_processes} processes to search for a matching address...")
    queue: Queue = Queue()
    counter = Counter()

    start_time: float = timer()
    for _ in range(num_processes):
        process = Process(target=_search_for_matching_address, args=(keyword, match, counter, queue))
        jobs.append(process)
        process.start()

    # Start the logger process
    logger_process = Process(target=_log_progress, args=(counter, start_time))
    jobs.append(logger_process)
    logger_process.start()

    signal.signal(signal.SIGINT, signal_handler)  # capture ctrl-c so we can report attempts and running time

    address, mnemonic = queue.get()  # this will return once one of the spawned processes finds a match

    logger.info(f"Vanity address generation time: {timer() - start_time:.2f} seconds")

    for p in jobs:
        p.terminate()

    return VanityAccount(
        mnemonic=mnemonic,
        address=address,
        private_key=to_private_key(mnemonic),  # type: ignore[no-untyped-call]
    )
