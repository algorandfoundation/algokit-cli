$ErrorActionPreference = 'Stop'

$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

# ensure pipx is installed
python -m pip install --disable-pip-version-check --no-warn-script-location pipx
if ($LASTEXITCODE -ne 0) {
  Throw "Error installing pipx"
}

# work out the wheel name and make sure there wasn't a packaging error
$wheelFileName = Get-ChildItem -File -Filter $env:ChocolateyPackageName*.whl $toolsDir
if ($wheelFileName.count -ne 1) {
  Throw "Packaging error. nupkg contained $($wheelFile.count) wheel files"
}

# determine if the package is already installed. In which case, uninstall it first
# Note - pipx upgrade does not work with local files
$pipxListOutput = &{
  # pipx outputs to stderr if there are no packages, so ignore that error
  $ErrorActionPreference = 'Continue'
  python -m pipx list 2>&1
  if ($LASTEXITCODE -ne 0) {
    Throw "Error searching for existing packages"
  }
}

# uninstall existing package if present
if ($pipxListOutput -match "$env:ChocolateyPackageName.*") {
  &{
    #pipx outputs to stderr as part of normal execution, so ignore stderr
    $ErrorActionPreference = 'Continue'
    python -m pipx uninstall $env:ChocolateyPackageName 2>&1
    if ($LASTEXITCODE -ne 0) {
      Throw "Error removing existing version"
    }
  }
}

# install the bundled wheel file.
&{
  #pipx outputs to stderr as part of normal execution, so ignore stderr
  $ErrorActionPreference = 'Continue'
  python -m pipx install $wheelFileName[0].FullName 2>&1
  if ($LASTEXITCODE -ne 0) {
    Throw "Error installing $($wheelFileName[0].FullName)"
  }
}

#setup shim
$pipx_list = python -m pipx list --json | ConvertFrom-Json
$algokit_path = $pipx_list.venvs.algokit.metadata.main_package.app_paths.__Path__
Install-BinFile -Name algokit -Path $algokit_path