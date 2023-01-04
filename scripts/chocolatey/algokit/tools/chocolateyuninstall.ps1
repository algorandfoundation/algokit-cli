# ensure pipx is installed. Just in case someone has removed it manually
python -m pip --disable-pip-version-check install --user pipx
if ($LASTEXITCODE -ne 0) {
  Throw "Error configuring pipx for uninstalling"
}

# zap it
python -m pipx uninstall $env:ChocolateyPackageName | Tee-Object -Variable cmdOutput
if ($LASTEXITCODE -ne 0) {
  if ($cmdOutput -match "Nothing to uninstall" ) {
    Write-Output "$($env:ChocolateyPackageName) already uninstalled by pipx. Ignoring"
  }
  else {
    Throw "Error running pipx uninstall $($env:ChocolateyPackageName)"
  }
}
