$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose could not start the lab.' }

foreach ($port in @(8001, 8000)) {
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/demo" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 750 }
    }
    if (-not $ready) { throw "Demo API on port $port did not become ready. Run: docker compose logs --tail 50" }
}
docker compose --profile tests run --rm --build regression
if ($LASTEXITCODE -ne 0) { throw 'Regression suite or OPA runtime verification failed.' }
Write-Host 'Ban truoc sua: http://127.0.0.1:8001/demo'
Write-Host 'Ban sau sua + OPA: http://127.0.0.1:8000/demo'
Write-Host "Bao cao 26 ca: $projectRoot\tests\results\demo.html"
Write-Host 'Mo Burp > Proxy > Open Browser, sau do truy cap hai dia chi tren.'
