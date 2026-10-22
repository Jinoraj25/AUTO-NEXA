<#
.SYNOPSIS
    Registers a Windows Scheduled Task to run the AutoNexa Daily Stock Ingestion Daemon every morning.
.DESCRIPTION
    Creates 'AutoNexa_Daily_Stock_Sync' in Windows Task Scheduler to execute:
    python "D:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\scripts\daily_stock_sync_daemon.py" --once
    Every day at 08:30 AM.
#>

param(
    [string]$TaskName = "AutoNexa_Daily_Stock_Sync",
    [string]$DailyTime = "08:30AM",
    [string]$ProjectDir = "D:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT"
)

$PythonExe = (Get-Command python).Source
$ScriptPath = Join-Path $ProjectDir "scripts\daily_stock_sync_daemon.py"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "AutoNexa Windows Scheduled Task Setup for Daily Stock Sync" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Python Path  : $PythonExe"
Write-Host "Script Path  : $ScriptPath"
Write-Host "Daily Trigger: $DailyTime"

# Check existing task
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Unregistering previous scheduled task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`" --once" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At $DailyTime
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "AutoNexa Morning Stock Sync Daemon - Automatically ingests daily TVS stock file into live inventory DB."

Write-Host "SUCCESS: Scheduled task '$TaskName' registered to run daily at $DailyTime!" -ForegroundColor Green
Write-Host "Logs are recorded at: $ProjectDir\logs\stock_auto_sync.log"
