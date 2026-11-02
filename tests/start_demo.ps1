# Chay hai phien ban API lab tren may va mo bang ket qua.
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue)) {
    $env:LAB_MODE = 'before'
    Start-Process -FilePath 'python' -ArgumentList '-m','uvicorn','app:app','--host','127.0.0.1','--port','8001' -WorkingDirectory $projectRoot -WindowStyle Hidden | Out-Null
    Remove-Item Env:LAB_MODE
}
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath 'python' -ArgumentList '-m','uvicorn','app:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden | Out-Null
}
Start-Sleep -Seconds 2

Write-Host "`n=== TRUOC KHI SUA ==="
python tests/live_demo.py --mode before --url http://127.0.0.1:8001
if ($LASTEXITCODE -ne 0) { throw 'Demo before failed' }
Write-Host "`n=== SAU KHI SUA ==="
python tests/live_demo.py --mode fixed --url http://127.0.0.1:8000
if ($LASTEXITCODE -ne 0) { throw 'Demo fixed failed' }
Write-Host "`n=== 23 CA KIEM THU ==="
python tests/demo.py
if ($LASTEXITCODE -ne 0) { throw 'Automated demo failed' }
Start-Process -FilePath (Join-Path $PSScriptRoot 'results\demo.html')
