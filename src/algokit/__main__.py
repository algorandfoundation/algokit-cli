from multiprocessing import freeze_support

from algokit.cli import algokit
from algokit.cli.common.utils import is_binary_mode

# Required to support full feature parity when running in binary execution mode
if is_binary_mode():
    freeze_support()

algokit()
