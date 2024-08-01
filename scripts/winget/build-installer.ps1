Param(
  [Parameter(Mandatory = $true)]
  [String]
  $binaryDir,

  [Parameter(Mandatory = $false)]
  [AllowEmptyString()]
  [String]
  $releaseVersion,

  [Parameter(Mandatory = $true)]
  [String]
  $outputFile
)

Function ThrowOnNonZeroExit {
  Param( [String]$Message )
  If ($LastExitCode -ne 0) {
    Throw $Message
  }
}

$ErrorActionPreference = 'Stop'

Remove-Item -Path build -Recurse -ErrorAction Ignore
$buildDir = New-Item -ItemType Directory -Path .\build\winget\installer
$installerContentDir = '.\scripts\winget\installer'

# Add installer assets
$assetsDir = New-Item -ItemType Directory -Path (Join-Path $buildDir assets)
Copy-Item -Path "$installerContentDir\assets\*" -Destination $assetsDir -Recurse | Out-Null

# Add manifest file
$version = if ($releaseVersion) { 
  # Strip the pre-release meta, as it's not valid
  $releaseVersion -replace '-\w+(\.\d+)?|\+.+$', ''
}
else {
  '0.0.1'
}
(Get-Content (Resolve-Path "$installerContentDir\AppxManifest.xml")).Replace('"0.0.1.0"', "$("$version.0")").Replace('"0.0.1"', "$("$version")") | Set-Content (Join-Path $buildDir AppxManifest.xml)

# Generate pri resource map for installer assets
$priConfig = (Resolve-Path "$installerContentDir\priconfig.xml")
Push-Location $buildDir
makepri new /ProjectRoot $buildDir /ConfigXml $priConfig | Out-Null
ThrowOnNonZeroExit "Failed to create pri file"
Pop-Location

# Add algokit binaries
Copy-Item -Path (Join-Path $binaryDir *) -Destination $buildDir -Recurse | Out-Null

# Generate msix
makeappx pack /o /h SHA256 /d $buildDir /p $outputFile | Out-Null
ThrowOnNonZeroExit "Failed to build msix"

