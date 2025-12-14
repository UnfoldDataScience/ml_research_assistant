# PowerShell script to copy project to EC2 excluding large directories
# Usage: .\deploy\copy_to_ec2.ps1 -KeyPath "C:\Users\amanr\Downloads\ml-research-assistant.pem" -InstanceIP "98.80.120.233"

param(
    [Parameter(Mandatory=$true)]
    [string]$KeyPath,
    
    [Parameter(Mandatory=$true)]
    [string]$InstanceIP,
    
    [string]$RemotePath = "/home/ubuntu/ml-research-assistant"
)

$ErrorActionPreference = "Stop"

Write-Host "Copying project to EC2 (excluding large files)..." -ForegroundColor Green

# Get the project root (parent of deploy folder)
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Create a temporary directory for filtered files
$TempDir = Join-Path $env:TEMP "ml-research-assistant-deploy"
if (Test-Path $TempDir) {
    Remove-Item -Path $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "Filtering files..." -ForegroundColor Yellow

# Copy files excluding large directories
$ExcludePatterns = @(
    ".venv",
    "__pycache__",
    "hf_cache",
    ".git",
    ".streamlit",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    "*.log",
    "logs",
    ".idea",
    ".vscode",
    "*.db",
    "*.sqlite"
)

Get-ChildItem -Path $ProjectRoot -Recurse | Where-Object {
    $item = $_
    $relativePath = $item.FullName.Substring($ProjectRoot.Length + 1)
    
    # Check if item matches any exclude pattern
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($relativePath -like $pattern -or 
            $relativePath -like "*\$pattern\*" -or 
            $relativePath -like "*\$pattern") {
            $shouldExclude = $true
            break
        }
    }
    
    return -not $shouldExclude
} | ForEach-Object {
    $sourcePath = $_.FullName
    $relativePath = $sourcePath.Substring($ProjectRoot.Length + 1)
    $destPath = Join-Path $TempDir $relativePath
    $destDir = Split-Path -Parent $destPath
    
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    
    if (-not $_.PSIsContainer) {
        Copy-Item -Path $sourcePath -Destination $destPath -Force
    }
}

Write-Host "Copying to EC2..." -ForegroundColor Yellow

# Use SCP to copy the filtered directory
$scpCommand = "scp -i `"$KeyPath`" -r `"$TempDir\*`" ubuntu@${InstanceIP}:${RemotePath}/"
Write-Host "Running: $scpCommand" -ForegroundColor Cyan
Invoke-Expression $scpCommand

# Cleanup
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path $TempDir -Recurse -Force

Write-Host "Done! Files copied to EC2." -ForegroundColor Green
Write-Host "SSH into your instance and run: cd $RemotePath && ./deploy/setup_ec2.sh" -ForegroundColor Cyan

