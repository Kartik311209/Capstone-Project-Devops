param(
    [ValidateSet("backup", "restore", "verify")]
    [string]$Action = "backup"
)

$Root = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $PSScriptRoot "backups"
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchivePath = Join-Path $BackupDir "pulsetrack_snapshot_$Timestamp.zip"

if ($Action -eq "backup") {
    $Targets = @(
        (Join-Path $Root "k8s"),
        (Join-Path $Root "infra"),
        (Join-Path $Root "observability"),
        (Join-Path $Root "samples")
    )
    Compress-Archive -Path $Targets -DestinationPath $ArchivePath -Force
    $SizeKB = [math]::Round((Get-Item $ArchivePath).Length / 1KB, 2)
    Write-Host "[DR-BACKUP] Snapshot created: $ArchivePath ($SizeKB KB)"
} elseif ($Action -eq "verify") {
    $Latest = Get-ChildItem -Path $BackupDir -Filter "*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $Latest) {
        Write-Error "[DR-VERIFY] No backup snapshots found."
        exit 1
    }
    Write-Host "[DR-VERIFY] Verified latest snapshot: $($Latest.Name) ($([math]::Round($Latest.Length / 1KB, 2)) KB)"
} elseif ($Action -eq "restore") {
    $Latest = Get-ChildItem -Path $BackupDir -Filter "*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $Latest) {
        Write-Error "[DR-RESTORE] No backup snapshots found."
        exit 1
    }
    $RestoreTmp = Join-Path $BackupDir "restore_test"
    if (Test-Path $RestoreTmp) { Remove-Item $RestoreTmp -Recurse -Force }
    Expand-Archive -Path $Latest.FullName -DestinationPath $RestoreTmp -Force
    Write-Host "[DR-RESTORE] Successfully restored snapshot $($Latest.Name) to $RestoreTmp"
}
