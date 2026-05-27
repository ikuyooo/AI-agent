$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$url = "http://localhost:8501"
$healthUrl = "$url/_stcore/health"

if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) {
    Start-Process $url
    Write-Host "App is already listening at $url"
    exit 0
}

Start-Job -ArgumentList $healthUrl, $url -ScriptBlock {
    param($healthUrl, $url)
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        try {
            $health = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
            if ($health.Content.Trim() -eq "ok") {
                Start-Process $url
                return
            }
        } catch {
            # Keep waiting while Streamlit initializes.
        }
    }
} | Out-Null

.venv\Scripts\python -m streamlit run app\streamlit_app.py --server.headless=true --browser.gatherUsageStats=false
