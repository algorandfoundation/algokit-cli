# AlgoKit CLI

## ⚠️ Pre-Alpha Software ⚠️

### This software may break your computer or (more likely) just not do anything useful yet and be a general pain to install.

Still not deterred?

Here's how to test it out and maybe even start hacking, assuming you have access to this repo.

### Install

1. Ensure [Python](https://www.python.org/downloads/) 3.10 or higher is installed on your system and available on your `PATH`
    - Note there is probably a better way to install Python than to download it directly, e.g. your friendly local Linux package manager, Homebrew on macOS, chocolatey on Windows
2. Install [pipx](https://pypa.github.io/pipx/)
   - Make sure to follow _all_ the instructions for your OS, there will be two commands, the first to install, and the second to ensure your path is setup. Make sure to read the output of this second command as well, as it'll probably tell you to relaunch your terminal.
3. Checkout this repo e.g. with git clone
4. If you want to start hacking on algokit-cli, run `poetry install` to install dependencies (including dev dependencies) and activate the virtual environment it creates in `.venv` in your checkout (you can run `poetry shell` or just activate it directly if you know what you're doing). If you're using an IDE it should probably do that for you though.
5. Optionally, if you want to rest running `algokit`, then:
   1. Run `poetry build` in the checkout (you shouldn't need to activate the venv first). This will output a "source distribution" (a tar.gz file) and a "binary distribution" (a .whl file) in the `dist/` directory.
   2. Run `pipx install ./dist/algokit-<TAB>-<TAB>` (ie the .whl file)
   3. You can now run `algokit` and should see a help message! 🎉

