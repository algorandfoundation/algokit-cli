
function version { echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'; }
function splitExtractElement {
  IFS="$2" read -a ARRAY <<< "$1"
  echo "${ARRAY[$3]}"
}

function runInstalls () {
  
  PYTHON_INSTALL_VERSION='3.10.8'
  PYTHON_MIN_VERSION='3.10'

  touch -a ~/.bashrc

  pyenv="$(pyenv --version 2>/dev/null)"
  if [[ $? -eq 0 ]]; then
    echo $pyenv is already installed ✅
  else
    . $SCRIPT_DIR/install-pyenv.sh

    if [[ $? -ne 0 ]]; then
      return 1
    fi

    source ~/.bashrc
  fi
  
  pythonv=$(splitExtractElement "$(pyenv version 2>/dev/null)" " " 0)
  if [ $(version $pythonv) -ge $(version "$PYTHON_MIN_VERSION") ]; then
    echo "Python $pythonv is already installed ✅"
  else
    . $SCRIPT_DIR/install-python.sh $PYTHON_INSTALL_VERSION
    
    if [[ $? -ne 0 ]]; then
      return 1
    fi

    source ~/.bashrc
  fi

  poetryv="$(pyenv exec poetry --version 2>/dev/null)"
  if [[ $? -eq 0 ]]; then
    echo $poetryv is already installed ✅
  else
    . $SCRIPT_DIR/install-poetry.sh

    if [[ $? -ne 0 ]]; then
      return 1
    fi
  fi
}

function setup () {
  
  runInstalls
  if [[ $? -ne 0 ]]; then
    echo "Error: install failed, please check output"
    return 1
  fi

  echo "Run poetry install"
  pyenv exec poetry install
}

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$SCRIPT_DIR/.."
setup
