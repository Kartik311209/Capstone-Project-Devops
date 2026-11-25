param(
    [Parameter(Mandatory=$true)]
    [ValidateRange(0, 100)]
    [int]$CanaryWeight
)

$BlueWeight = 100 - $CanaryWeight
$ConfPath = Join-Path $PSScriptRoot "..\observability\nginx\canary.conf"

$Content = @"
upstream pulsetrack_canary_pool {
    server app-blue:8000 weight=$BlueWeight;
    server app-green:8000 weight=$CanaryWeight;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://pulsetrack_canary_pool;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
    }

    location /nginx-health {
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
"@

if ($CanaryWeight -eq 0) {
    $Content = $Content -replace "server app-green:8000 weight=0;", "server app-green:8000 backup;"
}
if ($BlueWeight -eq 0) {
    $Content = $Content -replace "server app-blue:8000 weight=0;", "server app-blue:8000 backup;"
}

Set-Content -Path $ConfPath -Value $Content -Encoding UTF8
Write-Host "Updated Canary split: Blue=$BlueWeight%, Green(Canary)=$CanaryWeight%"
Write-Host "Reloading Nginx router if running..."
docker exec pulsetrack-router nginx -s reload 2>$null
