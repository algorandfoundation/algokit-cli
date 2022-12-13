$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

# run refreshenv to ensure python is on path. If it was just installed
$ChocolateyProfile = "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
if (Test-Path($ChocolateyProfile)) {
  Import-Module "$ChocolateyProfile"
}
else {
  Write-Output "couldn't find chocolatey profile script"
}
RefreshEnv.cmd

# ensure pipx is installed
python -m pip --disable-pip-version-check install --user pipx
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
$pipxListOutput = pipx list
if ($LASTEXITCODE -ne 0) {
  Throw "Error searching for existing packages"
}
if ($pipxListOutput -match "$env:ChocolateyPackageName.*") {
  pipx uninstall $env:ChocolateyPackageName
  if ($LASTEXITCODE -ne 0) {
    Throw "Error removing existing version"
  }
}

# install the bundled wheel file.
# For some reason pipx outputs normal messages to stderr, which causes choco to complain. Redirect stderr to stdout and rely on return value for errors
pipx install $wheelFileName[0].FullName 2>&1
if ($LASTEXITCODE -ne 0) {
  Throw "Error installing $($wheelFileName[0].FullName)"
}
