Param(
  [Parameter(Mandatory=$true)]
  [String]
  $binaryDir,

  [Parameter(Mandatory=$true)]
  [String]
  $releaseVersion,

  [Parameter(Mandatory=$true)]
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
$buildDir = New-Item -ItemType Directory -Path .\build\winget

# Add installer assets
$assetsDir = New-Item -ItemType Directory -Path (Join-Path $buildDir assets)
Copy-Item -Path .\scripts\winget\assets\* -Destination $assetsDir -Recurse | Out-Null

# Add manifest file
$version = if ($releaseVersion) { $releaseVersion } else { '0.0.1' }
(Get-Content (Resolve-Path .\scripts\winget\AppxManifest.xml)).Replace('0.0.1.0', "$($version).0") | Set-Content (Join-Path $buildDir AppxManifest.xml)

# Generate pri resource map for installer assets
$priConfig = (Resolve-Path .\scripts\winget\priconfig.xml)
Push-Location $buildDir
MakePri new /ProjectRoot $buildDir /ConfigXml $priConfig | Out-Null
ThrowOnNonZeroExit "Failed to create pri file"
Pop-Location

# Add algokit binaries
Copy-Item -Path (Join-Path $binaryDir *) -Destination $buildDir -Recurse | Out-Null

# Generate msix
MakeAppx pack /o /h SHA256 /d $buildDir /p $outputFile | Out-Null
ThrowOnNonZeroExit "Failed to build msix"
