# https://github.com/MRCollective/repave.psm1/blob/master/repave.psm1
Function Test-Administrator() {
  $user = [Security.Principal.WindowsIdentity]::GetCurrent();
  return (New-Object Security.Principal.WindowsPrincipal $user).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

Function Test-ThrowIfNotSuccessful() {
  if ($LASTEXITCODE -ne 0) {
    throw "Error executing last command"
  }
}

Function Write-Header([string] $title) {
  Write-Host
  Write-Host "#########################"
  Write-Host "### $title"
  Write-Host "#########################"
}

Function Remove-Folder([string] $foldername) {
  if (Test-Path $foldername) { 
    Invoke-VerboseCommand {
      Remove-Item -LiteralPath $foldername -Force -Recurse 
    }
  }
}

Function Invoke-VerboseCommand {
  [CmdletBinding()]
  param (
    [Parameter(Mandatory = $true)]
    [scriptblock]
    $ScriptBlock
  )
  Begin {
    Write-Verbose "Running $Scriptblock"
  }
  Process {
    & $ScriptBlock
  }
  End {
    Write-Verbose "Completed running $Scriptblock"
  }
}

Function Invoke-Confirm {
  [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSShouldProcess', '', scope = 'function')]
  [CmdletBinding()]
  param (
    [Parameter(Mandatory = $true)]
    [string]$Description,
    [Parameter(Mandatory = $true)]
    [System.Management.Automation.Cmdlet]$ParentPSCmdlet,
    [Parameter(Mandatory = $true)]
    [scriptblock]
    $ScriptBlock
  )
  Process {
    if ($Force -or $ParentPSCmdlet.ShouldProcess($Description)) {
      $ConfirmPreference = 'None'
      Write-Header $Description
      . $ScriptBlock
    }
  }
}

# https://github.com/MRCollective/repave.psm1/blob/master/repave.psm1
function Install-Chocolatey() {
  try {
    (Invoke-Expression "choco list -lo") -Replace "^Reading environment variables.+$", "" | Set-Variable -Name "installedPackages" -Scope Global
    Write-Output "choco already installed with the following packages:`r`n"
    Write-Output $global:installedPackages
    Write-Output "`r`n"
  }
  catch {
    
    # Ensure running as admin
    Write-Header "Ensuring we are running as admin"
    if ($IsWindows -and -not (Test-Administrator)) {
      Write-Error "Re-run as Administrator`r`n"
      exit 1
    }
    
    Write-Output "Installing Chocolatey`r`n"
    Invoke-Expression ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";c:\programdata\chocolatey\bin", "Process")
    Write-Warning "If the next command fails then restart powershell and run the script again to update the path variables properly`r`n"
  }
}

# https://github.com/MRCollective/repave.psm1/blob/master/repave.psm1
function Install-ChocolateyPackage {
  [CmdletBinding()]
  Param (
    [String] $PackageName,
    [String] $InstallArgs,
    $RunIfInstalled
  )

  if ($global:installedPackages -match "^$PackageName \d") {
    Write-Output "$PackageName already installed`r`n"
  }
  else {
    
    # Ensure running as admin
    Write-Header "Ensuring we are running as admin"
    if ($IsWindows -and -not (Test-Administrator)) {
      Write-Error "Re-run as Administrator`r`n"
      exit 1
    }

    Invoke-Confirm "Install $PackageName from Chocolatey" $PSCmdlet {
      if ($null -ne $InstallArgs -and "" -ne $InstallArgs) {
        Write-Output "choco install -y $PackageName -InstallArguments ""$InstallArgs""`r`n"
        Invoke-Expression "choco install -y $PackageName -InstallArguments ""$InstallArgs""" | Out-Default
      }
      else {
        Write-Output "choco install -y $PackageName`r`n"
        Invoke-Expression "choco install -y $PackageName" | Out-Default
      }
    
      $env:ChocolateyInstall = Convert-Path "$((Get-Command choco).Path)\..\.."
      Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
      Update-SessionEnvironment
    }

    if ($null -ne $RunIfInstalled) {
      &$RunIfInstalled
    }
  }
}
