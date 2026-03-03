# AlgoKit CLI Installer for Windows (PowerShell)
# Usage: irm https://raw.githubusercontent.com/algorandfoundation/algokit-cli/main/scripts/install/install.ps1 | iex
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$UV_INSTALL_URL = "https://astral.sh/uv/install.ps1"
$PYTHON_VERSION = "3.12"
$PACKAGE = "algokit"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $color = switch ($Level) {
        "INFO"  { "Green" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    Write-Host "[algokit] $Message" -ForegroundColor $color
}

function Stop-WithError {
    param([string]$Message)
    Write-Log $Message "ERROR"
    exit 1
}

function Install-UV {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvVersion = (uv --version 2>$null) -replace 'uv ', '' -replace '\n', ''
        Write-Log "uv found: uv $uvVersion"
        return
    }

    Write-Log "Installing uv..."
    try {
        Invoke-RestMethod $UV_INSTALL_URL | Invoke-Expression
    }
    catch {
        Stop-WithError "Failed to install uv: $($_.Exception.Message)"
    }

    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:USERPROFILE\.local\bin;$env:PATH"

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Stop-WithError "uv installed but not found on PATH. Restart your shell and try again."
    }
    Write-Log "uv installed successfully."
}

function Install-Python {
    try {
        $pythonList = uv python list 2>$null | Out-String
        if ($pythonList -match "cpython-$PYTHON_VERSION") {
            Write-Log "Python $PYTHON_VERSION found."
            return
        }
    }
    catch {
        Write-Log "Could not query Python versions: $($_.Exception.Message)" "WARN"
    }

    Write-Log "Installing Python $PYTHON_VERSION via uv..."
    try {
        uv python install $PYTHON_VERSION
        Write-Log "Python $PYTHON_VERSION installed."
    }
    catch {
        Stop-WithError "Failed to install Python $PYTHON_VERSION."
    }
}

function Install-AlgoKit {
    Write-Log "Installing $PACKAGE..."
    try {
        uv tool install $PACKAGE
        Write-Log "$PACKAGE installed successfully."
    }
    catch {
        Stop-WithError "Failed to install ${PACKAGE}: $($_.Exception.Message)"
    }

    $toolPath = Get-Command algokit -ErrorAction SilentlyContinue
    if ($toolPath) {
        $version = algokit --version 2>$null
        Write-Log "Installed: $version"
        Write-Log "Run 'algokit --help' to get started."
    }
    else {
        Write-Log "$PACKAGE installed but not found on PATH. Restart your shell and try again." "WARN"
    }
}

try {
    Write-Log "AlgoKit CLI Installer"
    Write-Host ""

    Install-UV
    Install-Python
    Install-AlgoKit

    Write-Host ""
    Write-Log "Done."
}
catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR"
    exit 1
}
