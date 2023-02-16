﻿$ErrorActionPreference = 'Stop'

$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

# refresh environment variables to ensure python is on path. If it was just installed
$ChocolateyProfile = "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
if (Test-Path($ChocolateyProfile)) {
  Import-Module "$ChocolateyProfile"
}
else {
  Write-Output "couldn't find chocolatey profile script"
}
Update-SessionEnvironment

# ensure pipx is installed
python -m pip install --disable-pip-version-check --no-warn-script-location --user pipx
if ($LASTEXITCODE -ne 0) {
  Throw "Error installing pipx"
}
&{
  # pipx outputs to stderr if path is already configured, so ignore that error
  $ErrorActionPreference = 'Continue'
  python -m pipx ensurepath
  if ($LASTEXITCODE -ne 0) {
    Throw "Error configuring pipx path"
  }
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
  python -m pipx list
  if ($LASTEXITCODE -ne 0) {
    Throw "Error searching for existing packages"
  }
}

# uninstall existing package if present
if ($pipxListOutput -match "$env:ChocolateyPackageName.*") {
  &{
    #pipx outputs to stderr as part of normal execution, so ignore stderr
    $ErrorActionPreference = 'Continue'
    python -m pipx uninstall $env:ChocolateyPackageName
    if ($LASTEXITCODE -ne 0) {
      Throw "Error removing existing version"
    }
  }
}

# install the bundled wheel file.
&{
  #pipx outputs to stderr as part of normal execution, so ignore stderr
  $ErrorActionPreference = 'Continue'
  python -m pipx install $wheelFileName[0].FullName
  if ($LASTEXITCODE -ne 0) {
    Throw "Error installing $($wheelFileName[0].FullName)"
  }
}


