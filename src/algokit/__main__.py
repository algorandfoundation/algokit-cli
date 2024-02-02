import sys
from multiprocessing import freeze_support

from algokit.cli import algokit

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    freeze_support()
algokit()
