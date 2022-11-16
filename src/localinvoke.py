# This script is for invoking algokit from your IDE with a dynamic set of args (defined in .env, which is in .gitignore)
# Copy .env.sample to .env and fill it in to get started!
import os
from os.path import dirname, join

from dotenv import load_dotenv  # type: ignore

from algokit import cli

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

args = os.environ.get("DEBUG_ARGS") or ""

cli(args.split(" "))
