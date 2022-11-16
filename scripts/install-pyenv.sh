#!/bin/bash

function installPyenvLinux () {
  # https://github.com/pyenv/pyenv-installer
  curl https://pyenv.run | bash
  if [[ $? -ne 0 ]]; then
    return 1
  fi

  # set up .bashrc for pyenv https://github.com/pyenv/pyenv-installer
  if ! grep -q "# pyenv config" ~/.bashrc; then
    echo '' >> ~/.bashrc
    echo '# pyenv config' >> ~/.bashrc
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
  fi
}

function installPyenvMac() {
  brew install pyenv
}

echo "Installing pyenv..."

if [ "$(uname -s)" == Darwin ]; then
  installPyenvMac
else
  installPyenvLinux
fi
