param(
    [string]$InputDirectory = ".\dist\perfwatch",
    [string]$OutputDirectory = ".\release"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$repositoryPrefix = $repositoryRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) +
    [IO.Path]::DirectorySeparatorChar
$resolvedInputDirectory = (Resolve-Path -LiteralPath $InputDirectory).Path.TrimEnd(
    [IO.Path]::DirectorySeparatorChar
)
if (-not $resolvedInputDirectory.StartsWith(
    $repositoryPrefix,
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "input directory must be under the repository: $resolvedInputDirectory"
}
$resolvedOutputDirectory =
    $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)

$version = (& python -c "import pathlib,tomllib; print(tomllib.loads(pathlib.Path('python/pyproject.toml').read_text(encoding='utf-8'))['project']['version'])").Trim()
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^\d+\.\d+\.\d+$') {
    throw "project version is not semantic: $version"
}

$requiredRelativePaths = @(
    "perfwatch.exe"
    "README.md"
    "LICENSE"
    "_internal\dashboard\index.html"
    "_internal\perfwatch\storage\schema.sql"
)
New-Item -ItemType Directory -Path $resolvedOutputDirectory -Force | Out-Null
$archiveName = "perfwatch-$version-windows-x64.zip"
$archivePath = Join-Path $resolvedOutputDirectory $archiveName
$checksumPath = "$archivePath.sha256"
foreach ($outputPath in @($archivePath, $checksumPath)) {
    if (Test-Path -LiteralPath $outputPath -PathType Container) {
        throw "release output path is a directory: $outputPath"
    }
    if (Test-Path -LiteralPath $outputPath -PathType Leaf) {
        Remove-Item -LiteralPath $outputPath -Force
    }
}

Compress-Archive -Path $resolvedInputDirectory -DestinationPath $archivePath
$hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content `
    -LiteralPath $checksumPath `
    -Value "$hash  $archiveName" `
    -Encoding ascii

$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd(
    [IO.Path]::DirectorySeparatorChar
)
$temporaryDirectory = Join-Path $temporaryRoot (
    "perfwatch-release-" + [Guid]::NewGuid().ToString("N")
)
$temporaryPrefix = $temporaryRoot + [IO.Path]::DirectorySeparatorChar
if (-not $temporaryDirectory.StartsWith(
    $temporaryPrefix,
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "invalid temporary directory: $temporaryDirectory"
}

New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null
try {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $temporaryDirectory
    $expandedProductDirectory = Join-Path $temporaryDirectory "perfwatch"
    foreach ($relativePath in $requiredRelativePaths) {
        if (-not (Test-Path -LiteralPath (
            Join-Path $expandedProductDirectory $relativePath
        ) -PathType Leaf)) {
            throw "archive is missing required product file: $relativePath"
        }
    }
    $expandedNativeModules = @(Get-ChildItem `
        -LiteralPath (Join-Path $expandedProductDirectory "_internal") `
        -Filter "perfwatch_native*.pyd" `
        -File)
    if ($expandedNativeModules.Count -ne 1) {
        throw "archive contains $($expandedNativeModules.Count) perfwatch_native modules"
    }

}
finally {
    if (Test-Path -LiteralPath $temporaryDirectory -PathType Container) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
    }
}

$archiveSize = (Get-Item -LiteralPath $archivePath).Length
Write-Host "Archive: $archivePath"
Write-Host "Bytes: $archiveSize"
Write-Host "SHA-256: $hash"
Write-Host "Checksum: $checksumPath"
Write-Host "Extraction: PASS"
