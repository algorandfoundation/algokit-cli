# Re-create the version based on the wheel file name.
# NOTE: x.y.x-beta.12 versions are not supported by chocolatey and need to be rewritten as x.y.z-beta12 (however this will likely change soon)
# "special version part" requirements. <20 characters, no '.' no '+'
$wheelFiles = Get-ChildItem -File -Filter algokit*-py3-none-any.whl dist
if ($wheelFiles.count -ne 1) {
    Throw "Packaging error. build artifact contained $($wheelFileName.count) normally named wheel files"
}
$wheelFile = $wheelFiles[0]
$wheelFileName = $wheelFile.Name
if ($wheelFileName -Match '-([0-9]+\.[0-9]+\.[0-9]+)b?([0-9]*)(\+(.*?))?(.[0-9]+)?-') {
    $version_number = $Matches[1]
    $version_beta = $Matches[2]
    $version_branch = $Matches[4]
    $version_branch = $version_branch ? $version_branch.Replace(".", "") : "" # dots aren't valid here
    $version_betanumber = $Matches[5]
    $version_beta_truncated = "beta$($version_beta)$($version_branch)"
    #$version_beta_truncated = "beta$($version_beta)$($version_branch)$($version_betanumber)" # When chocolatey supports semver v2.0
    $version_beta_truncated = $version_beta_truncated.subString(0, [System.Math]::Min(20, $version_beta_truncated.Length - 1)) # chocolatey has a limit of 20 characters on "special version part"
}
else {
    Throw "Packaging error. Unrecognised file name pattern $($wheelFileName[0].Name)"
}

$version = $version_number
$release_tag = "v${version_number}"
if ($version_beta) {
    $version = "$($version)-$($version_beta_truncated)"
    $release_tag = "${release_tag}-beta.${version_beta}"
}

# Update VERIFICATION.txt with current URL & SHA256
$verification = Get-Item -Path .\scripts\chocolatey\algokit\tools\VERIFICATION.txt
$wheel_url = "https://github.com/algorandfoundation/algokit-cli/releases/download/${release_tag}/${wheelFileName}"
$sha_256 = Get-FileHash $wheelFile
(Get-Content $verification).replace("{wheel_url}", $wheel_url).replace("{sha256}", $sha_256.Hash) | Set-Content $verification

echo "version=$version" | Tee-Object -Append -FilePath $env:GITHUB_OUTPUT
echo "wheelFileName=${wheelFileName}" | Tee-Object -Append -FilePath $env:GITHUB_OUTPUT
