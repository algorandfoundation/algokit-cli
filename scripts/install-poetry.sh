#!/bin/bash

function installPoetry () {
  pyenv="$(pyenv --version 2>/dev/null)"
  if [[ $? -ne 0 ]]; then
    echo "Error: can't install poetry, pyenv is not available ❌"
    return 1
  fi

  echo "Installing poetry..."

  pyenv exec pip install poetry
  if [[ $? -ne 0 ]]; then
    return 1
  fi
}

installPoetry
