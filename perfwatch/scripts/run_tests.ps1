$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

python -m pytest python/tests

if (Get-Command cmake -ErrorAction SilentlyContinue) {
    cmake -S cpp -B build
    cmake --build build --config Debug
    ctest --test-dir build --output-on-failure -C Debug
}
