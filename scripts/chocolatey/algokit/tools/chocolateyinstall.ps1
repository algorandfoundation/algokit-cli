$ErrorActionPreference = 'Stop'

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
python -m pip --disable-pip-version-check install --user pipx *>&1
if ($LASTEXITCODE -ne 0) {
  Throw "Error installing pipx"
}

# work out the wheel name and make sure there wasn't a packaging error
$wheelFileName = Get-ChildItem -File -Filter $env:ChocolateyPackageName*.whl $toolsDir
if ($wheelFileName.count -ne 1) {
  Throw "Packaging error. nupkg contained $($wheelFile.count) wheel files"
}

# For some reason pipx outputs normal messages to stderr, which causes choco to complain.
# So when calling pipx redirect stderr to stdout and rely on return value for errors

# determine if the package is already installed. In which case, uninstall it first
# Note - pipx upgrade does not work with local files
$pipxListOutput = python -m pipx list *>&1
if ($LASTEXITCODE -ne 0) {
  Throw "Error searching for existing packages"
}
if ($pipxListOutput -match "$env:ChocolateyPackageName.*") {
  python -m pipx uninstall $env:ChocolateyPackageName *>&1
  if ($LASTEXITCODE -ne 0) {
    Throw "Error removing existing version"
  }
}

# install the bundled wheel file.
python -m pipx install $wheelFileName[0].FullName *>&1
if ($LASTEXITCODE -ne 0) {
  Throw "Error installing $($wheelFileName[0].FullName)"
}
