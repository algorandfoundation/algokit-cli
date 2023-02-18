$ErrorActionPreference = 'Stop'

# ensure pipx is installed. Just in case someone has removed it manually
python -m pip install --disable-pip-version-check --no-warn-script-location --user pipx
if ($LASTEXITCODE -ne 0) {
  Throw "Error configuring pipx for uninstalling"
}

# zap it
&{
  #pipx outputs to stderr as part of normal execution, so ignore stderr
  $ErrorActionPreference = 'Continue'
  python -m pipx uninstall $env:ChocolateyPackageName 2>&1
  if ($LASTEXITCODE -ne 0) {
    if ($cmdOutput -match "Nothing to uninstall" ) {
      Write-Output "$($env:ChocolateyPackageName) already uninstalled by pipx. Ignoring"
    }
    else {
      Throw "Error running pipx uninstall $($env:ChocolateyPackageName)"
    }
  }
}

Uninstall-BinFile -Name algokit