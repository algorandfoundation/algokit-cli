import sys

# this isn't beautiful, but to avoid confusing user errors we need this check before we start importing our own modules

try:
    from algokit.core.log_handlers import initialise_logging, uncaught_exception_logging_handler
except ImportError as ex:
    # the above should succeed both in importing "algokit" itself, and we also know that "click" will
    # be imported too, if those basic packages aren't present, something is very wrong
    print(  # noqa: T201
        f"{ex}\nUnable to import require package(s), your install may be broken :(",
        file=sys.stderr,
    )
    sys.exit(-1)


initialise_logging()
sys.excepthook = uncaught_exception_logging_handler


if __name__ == "__main__":
    from algokit.cli import algokit

    algokit()
