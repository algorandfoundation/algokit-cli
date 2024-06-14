from multiprocessing import freeze_support

from algokit.cli import algokit
from algokit.core.utils import enable_utf8_on_windows

# Required to support full feature parity when running in binary execution mode
freeze_support()
enable_utf8_on_windows()
algokit()
