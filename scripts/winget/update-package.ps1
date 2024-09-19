Param(
  [Parameter(Mandatory = $true)]
  [String]
  $releaseVersion
)

Function ThrowOnNonZeroExit {
  Param( [String]$Message )
  If ($LastExitCode -ne 0) {
    Throw $Message
  }
}

$wingetPackage = 'AlgorandFoundation.AlgoKit'
$release = Invoke-RestMethod -uri "https://api.github.com/repos/algorandfoundation/algokit-cli/releases/tags/v$releaseVersion"
$installerUrl = $release | Select -ExpandProperty assets -First 1 | Where-Object -Property name -match '-windows_x64-winget\.msix$' | Select -ExpandProperty browser_download_url

$wingetDir = New-Item -Force -ItemType Directory -Path .\build\winget
$wingetExecutable = "$wingetDir\wingetcreate.exe"
Invoke-WebRequest https://aka.ms/wingetcreate/latest -OutFile $wingetExecutable
& $wingetExecutable update $wingetPackage -s -v $releaseVersion -u "$installerUrl" -t "$env:WINGET_GITHUB_TOKEN"
ThrowOnNonZeroExit "Failed to update winget package"
