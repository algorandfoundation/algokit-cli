<#
    .SYNOPSIS
        AlgoKit CLI dev environment setup.
    .DESCRIPTION
        The goal of this script is that every dev can go from clean (or dirty :P) machine -> clone -> setup.ps1 -> open in IDE -> F5 debugging in minutes, cross-platform.
        If you find problems with your local environment after running this (or during running this!) be sure to contribute fixes :)
        This script is idempotent and re-entrant; you can safely execute it multiple times.
    .EXAMPLE
        ./setup.ps1
        This executes everything
    .EXAMPLE
        ./setup.ps1 -SkipPythonInstall
        This skips the install of Python and Poetry; ensure Python 3.10+ and Poetry is already installed and available via `python`
#>
[CmdletBinding(SupportsShouldProcess = $true)]
Param(
  [Parameter(Mandatory = $false)]
  [switch] $SkipPythonInstall = $false,

  [Parameter()]
  [switch]
  $Force
)
# https://dille.name/blog/2017/08/27/how-to-use-shouldprocess-in-powershell-functions/
Begin {
  if (-not $PSBoundParameters.ContainsKey('Verbose')) {
    $VerbosePreference = $PSCmdlet.SessionState.PSVariable.GetValue('VerbosePreference')
  }
  if (-not $PSBoundParameters.ContainsKey('Confirm')) {
    $ConfirmPreference = $PSCmdlet.SessionState.PSVariable.GetValue('ConfirmPreference')
  }
  if (-not $PSBoundParameters.ContainsKey('WhatIf')) {
    $WhatIfPreference = $PSCmdlet.SessionState.PSVariable.GetValue('WhatIfPreference')
  }
  Write-Verbose ('[{0}] ConfirmPreference={1} WhatIfPreference={2} VerbosePreference={3}' -f $MyInvocation.MyCommand, $ConfirmPreference, $WhatIfPreference, $VerbosePreference)
}
Process {
  $ScriptPath = Split-Path $MyInvocation.MyCommand.Path
  Import-Module (Join-Path $ScriptPath "utilities.psm1") -Force -Global  

  #Requires -Version 7.0.0
  Set-StrictMode -Version "Latest"
  $ErrorActionPreference = "Stop"
  $LASTEXITCODE = 0

  Push-Location (Join-Path $PSScriptRoot ..)
  try {

    if (-not $IsWindows) {
      Write-Host "Not running in Windows; executing setup.sh via bash instead..."
      & bash ./setup.sh
      return
    }
    
    $pythonMinVersion = [version]'3.10'
    $pythonInstallVersion = '3.10.8'

    $isPyenvInstalled = $null -ne (Get-Command "pyenv" -ErrorAction SilentlyContinue)
    $isPoetryInstalled = $null -ne (Get-Command "poetry" -ErrorAction SilentlyContinue)
    $isPythonInstalled = $null -ne (Get-Command "python" -ErrorAction SilentlyContinue) -and ([version](((Invoke-Command { pyenv exec python --version }) -split ' ' -replace 'b', '')[1]) -ge $pythonMinVersion)

    $needsInstall = -not $isPoetryInstalled -or -not $isPythonInstalled

    if (-not $needsInstall) {
      Write-Header "All dependencies are installed (pyenv, poetry, python $pythonMinVersion+) ✅"
    }
    else {

      Write-Header "Detected some dependencies aren't installed (poetry and/or python $pythonMinVersion+), attempting to correct..."

      Invoke-Confirm "Install Chocolatey" $PSCmdlet {
        Install-Chocolatey
      }

      if (-not $SkipPythonInstall) {
        Write-Header "Install pyenv"
        Install-ChocolateyPackage -PackageName pyenv-win
        Test-ThrowIfNotSuccessful

        Write-Header "Install Python $pythonMinVersion+"
        if (-not $isPythonInstalled) {
          Set-StrictMode -Off # On Windows pyenv is a .ps1 and strict mode breaks it :P
          try {
            Invoke-Confirm "Install Python $pythonInstallVersion via pyenv" $PSCmdlet {
              Invoke-Expression "pyenv update" -ErrorAction SilentlyContinue
              Test-ThrowIfNotSuccessful
              Invoke-Expression "pyenv install $pythonInstallVersion" -ErrorAction SilentlyContinue
              Test-ThrowIfNotSuccessful
              Invoke-Expression "pyenv global $pythonInstallVersion" -ErrorAction SilentlyContinue
              Test-ThrowIfNotSuccessful
            }
          }
          finally {
            Set-StrictMode -Version "Latest"
          }
        }
        else {
          Write-Host "Python $pythonMinVersion+ already installed"
        }

        # Install Poetry
        Write-Header "Install Poetry"
        & pyenv exec pip install poetry
        Test-ThrowIfNotSuccessful
      }
    }
    
    # Set up file permissions for .venv (if you run as admin then this is important)
    if (-not (Test-Path .venv)) {
      Invoke-Confirm "Create .venv folder with rwx permissions for all users" $PSCmdlet {
        Write-Header "Setting up file permissions so normal users can rwx in .venv to avoid potential file permission issues"
        New-Item -ItemType Directory -Force -Path .venv
        icacls .venv /grant everyone:f
      }
    }

    Write-Header "Installing Python dependencies via Poetry"
    Invoke-Confirm "Run poetry install" $PSCmdlet {
      if ($isPoetryInstalled) {
        & poetry install
        Test-ThrowIfNotSuccessful
      }
      elseif ($isPyenvInstalled) {
        & pyenv exec poetry install
        Test-ThrowIfNotSuccessful
      }
      else {
        throw "Unable to run poetry install"
      }
    }

    # Windows doesn't have bin folder or python3 so setting up symlinks so the behaviour is mimic'd cross-platform and all of our IDE settings work properly
    Write-Header "Creating venv symlinks so .venv/bin works on Windows too"
    if (-not (Test-Administrator)) {
      Write-Warning "Re-run as Administrator to set up symlink for .venv/bin -> .venv/Scripts`r`nIf you don't it will still work, but you'll manually need to select the Python interpreter in VS Code.`r`n"
    }
    else {
      if (-not (Test-Path (Join-Path ".venv" "bin"))) {
        New-Item -ItemType symboliclink -path .venv -name bin -value (Resolve-Path (Join-Path .venv Scripts))
      }
      if (-not (Test-Path (Join-Path ".venv" "bin" "python3.exe"))) {
        New-Item -ItemType symboliclink -path (Join-Path .venv bin) -name python3.exe -value (Resolve-Path (Join-Path .venv Scripts python.exe))
      }
      if (-not (Test-Path (Join-Path ".venv" "bin" "python"))) {
        New-Item -ItemType symboliclink -path (Join-Path .venv bin) -name python -value (Resolve-Path (Join-Path .venv Scripts python.exe))
      }
    }

  }
  finally {
    Pop-Location
  }

}
End {
  Write-Verbose ('Completed: [{0}]' -f $MyInvocation.MyCommand)
}
