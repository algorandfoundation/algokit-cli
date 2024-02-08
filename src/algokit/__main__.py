from multiprocessing import freeze_support

from algokit.cli import algokit

# Required to support full feature parity when running in binary execution mode
freeze_support()
algokit()
