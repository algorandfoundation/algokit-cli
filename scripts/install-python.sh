#!/bin/bash

function installPython () {

  if [ $# -ne 1 ]; then
    echo Error: missing python version argument, e.g.: install-python.sh 3.10.6
    return 1
  fi

  PYTHON_VERSION=$1

  if [ "$(uname -s)" == Linux ]; then
    echo "Installing python build pre-requisistes..."
    # install python build pre-requisites https://github.com/pyenv/pyenv/wiki#suggested-build-environment
    sudo apt-get update; sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
  fi

  pyenv="$(pyenv --version 2>/dev/null)"
  if [[ $? -ne 0 ]]; then
    echo "Error: can't install python, pyenv is not available (if it just installed you might need to restart your shell for environment to update) ❌"
    return 1
  fi

  echo "Installing python..."

  # install and use python via pyenv
  pyenv install ${PYTHON_VERSION}
  pyenv global ${PYTHON_VERSION}
}

installPython $1