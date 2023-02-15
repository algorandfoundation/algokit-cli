$ErrorActionPreference = 'Stop'

# ensure pipx is installed. Just in case someone has removed it manually
python -m pip --disable-pip-version-check install --user pipx 2>&1
if ($LASTEXITCODE -ne 0) {
  Throw "Error configuring pipx for uninstalling"
}

# For some reason pipx outputs normal messages to stderr, which causes choco to complain.
# So when calling pipx redirect stderr to stdout and rely on return value for errors

# zap it
python -m pipx uninstall $env:ChocolateyPackageName 2>&1
if ($LASTEXITCODE -ne 0) {
  if ($cmdOutput -match "Nothing to uninstall" ) {
    Write-Output "$($env:ChocolateyPackageName) already uninstalled by pipx. Ignoring"
  }
  else {
    Throw "Error running pipx uninstall $($env:ChocolateyPackageName)"
  }
}
