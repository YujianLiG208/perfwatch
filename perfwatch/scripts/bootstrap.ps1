$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonDir = Join-Path $RootDir "python"
$VenvDir = Join-Path $PythonDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

py -3.11 -m venv $VenvDir
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "${PythonDir}[dev]"
