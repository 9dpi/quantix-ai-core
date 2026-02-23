$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotDir = "d:\Automator_Prj\Quantix_AI_Core\snapshots\Quantix_Snapshot_$Timestamp"
New-Item -ItemType Directory -Force -Path $SnapshotDir | Out-Null
New-Item -ItemType Directory -Force -Path "$SnapshotDir\docs" | Out-Null

Write-Host "[1/6] Created snapshot directory: $SnapshotDir"

# Read exclusions
$Exclusions = Get-Content "d:\Automator_Prj\Quantix_AI_Core\snapshot_exclude.txt"
$Exclusions = $Exclusions | Where-Object { $_ -ne "" }

Write-Host "[2/6] Copying backend code..."
# We manually copy to handle exclusions properly in a way similar to xcopy
$BackendSource = "d:\Automator_Prj\Quantix_AI_Core\backend"
$BackendDest = "$SnapshotDir\backend"

# Powershell way to copy with exclusions is a bit verbose if we want to be exact
# But for a snapshot, a simple recursive copy excluding patterns is usually enough
Get-ChildItem -Path $BackendSource -Recurse | Where-Object {
    $item = $_
    $skip = $false
    foreach ($pattern in $Exclusions) {
        if ($item.FullName -like "*$pattern*") {
            $skip = $true
            break
        }
    }
    !$skip
} | Copy-Item -Destination {
    $relPath = $_.FullName.Substring($BackendSource.Length)
    $target = Join-Path $BackendDest $relPath
    $parent = Split-Path $target
    if (!(Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $target
} -Force -ErrorAction SilentlyContinue

Write-Host "[3/6] Copying configuration files..."
$ConfigFiles = @(".env", "Procfile", "Dockerfile", "runtime.txt", "requirements.txt")
foreach ($file in $ConfigFiles) {
    if (Test-Path "d:\Automator_Prj\Quantix_AI_Core\$file") {
        Copy-Item -Path "d:\Automator_Prj\Quantix_AI_Core\$file" -Destination $SnapshotDir -Force
    }
}

Write-Host "[4/6] Copying documentation..."
Get-ChildItem -Path "d:\Automator_Prj\Quantix_AI_Core" -Filter "*.md" | Copy-Item -Destination $SnapshotDir -Force
if (Test-Path "d:\Automator_Prj\Quantix_AI_Core\backend\quantix_core\engine\Rules.txt") {
    Copy-Item -Path "d:\Automator_Prj\Quantix_AI_Core\backend\quantix_core\engine\Rules.txt" -Destination "$SnapshotDir\docs" -Force
}

Write-Host "[5/6] Creating snapshot manifest..."
$ManifestPath = "$SnapshotDir\SNAPSHOT_INFO.txt"
$ManifestContent = @"
QUANTIX AI CORE SNAPSHOT
=========================
Created: $(Get-Date)
Timestamp: $Timestamp

CONTENTS:
- Backend source code (quantix_core)
- Configuration files (.env, Procfile, etc)
- Documentation (Rules.txt, etc)
- Requirements and runtime specs

RESTORE INSTRUCTIONS:
1. Stop all running services
2. Backup current backend folder
3. Copy snapshot backend to main directory
4. Restore .env file
5. Run: pip install -r requirements.txt
6. Restart services
"@
$ManifestContent | Out-File -FilePath $ManifestPath -Encoding utf8

Write-Host "[6/6] Snapshot completed successfully at $SnapshotDir"
