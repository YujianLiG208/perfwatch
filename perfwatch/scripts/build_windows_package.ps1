param(
    [Parameter(Mandatory = $true)]
    [string]$NinjaPath,

    [Parameter(Mandatory = $true)]
    [string]$VsDevShellPath,

    [Parameter(Mandatory = $true)]
    [string]$Pybind11Directory,

    [string]$PythonPath = (Get-Command python).Source
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$resolvedNinja = (Resolve-Path -LiteralPath $NinjaPath).Path
$resolvedVsDevShell = (Resolve-Path -LiteralPath $VsDevShellPath).Path
$resolvedPybind11Directory = (Resolve-Path -LiteralPath $Pybind11Directory).Path
$resolvedPython = (Resolve-Path -LiteralPath $PythonPath).Path
if (-not (Test-Path -LiteralPath (
    Join-Path $resolvedPybind11Directory "pybind11Config.cmake"
) -PathType Leaf)) {
    throw "pybind11Config.cmake not found in $resolvedPybind11Directory"
}

$productDirectory = [IO.Path]::GetFullPath((Join-Path $repositoryRoot "dist\perfwatch"))
$pyinstallerWorkDirectory = [IO.Path]::GetFullPath(
    (Join-Path $repositoryRoot "build\pyinstaller")
)
$repositoryPrefix = $repositoryRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) +
    [IO.Path]::DirectorySeparatorChar
foreach ($ownedDirectory in @($productDirectory, $pyinstallerWorkDirectory)) {
    if (-not $ownedDirectory.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "refusing to remove path outside repository: $ownedDirectory"
    }
    if (Test-Path -LiteralPath $ownedDirectory) {
        Remove-Item -LiteralPath $ownedDirectory -Recurse -Force
    }
}

$pyinstallerVersion = (& $resolvedPython -m PyInstaller --version).Trim()
if ($LASTEXITCODE -ne 0 -or $pyinstallerVersion -ne "6.22.2") {
    throw "PyInstaller 6.22.2 is required; found '$pyinstallerVersion'"
}
& $resolvedVsDevShell -Arch amd64 -HostArch amd64 -SkipAutomaticLocation
if (-not $env:VSCMD_VER) {
    throw "Visual Studio developer shell did not initialize"
}

Push-Location (Join-Path $repositoryRoot "ui\dashboard")
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed" }
}
finally {
    Pop-Location
}

& cmake -S (Join-Path $repositoryRoot "cpp") `
    -B (Join-Path $repositoryRoot "build\phase8") `
    -G Ninja `
    -DCMAKE_BUILD_TYPE=Release `
    "-DCMAKE_MAKE_PROGRAM=$resolvedNinja" `
    "-DPython3_EXECUTABLE=$resolvedPython" `
    "-Dpybind11_DIR=$resolvedPybind11Directory"
if ($LASTEXITCODE -ne 0) { throw "native configure failed" }

& cmake --build (Join-Path $repositoryRoot "build\phase8")
if ($LASTEXITCODE -ne 0) { throw "native build failed" }

& $resolvedPython -m PyInstaller `
    --noconfirm `
    --distpath (Join-Path $repositoryRoot "dist") `
    --workpath $pyinstallerWorkDirectory `
    (Join-Path $repositoryRoot "packaging\perfwatch.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

if (-not (Test-Path -LiteralPath (Join-Path $productDirectory "perfwatch.exe"))) {
    throw "packaged executable not found"
}
Copy-Item -LiteralPath (Join-Path $repositoryRoot "README.md") -Destination $productDirectory
Copy-Item -LiteralPath (Join-Path $repositoryRoot "LICENSE") -Destination $productDirectory

Write-Host "Built $productDirectory"
