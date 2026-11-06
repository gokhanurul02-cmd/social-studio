& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'studio.py') @args
exit $LASTEXITCODE
