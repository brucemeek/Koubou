param(
    [string]$AppRepoRoot,
    [string]$FlutterAppDir,
    [string]$DeviceId = 'emulator-5556',
    [ValidateSet('light', 'dark', 'system')]
    [string]$ThemeMode = 'light',
    [int]$FixtureSeed = 1337,
    [string]$DartDefineFromFile,
    [string]$ReviewEmail,
    [string]$ReviewPassword,
    [string]$DriverPath = 'test_driver/app_store_screenshots_test.dart',
    [string]$TargetPath = 'integration_test/app_store_screenshots_test.dart'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-AppRepoRoot {
    param([string]$RequestedRoot)

    $repoRoot = (Resolve-Path $PSScriptRoot).Path

    if ($RequestedRoot) {
        return (Resolve-Path $RequestedRoot).Path
    }

    if ($env:DREAM_ORACLE_APP_ROOT) {
        return (Resolve-Path $env:DREAM_ORACLE_APP_ROOT).Path
    }

    $parentDir = Split-Path $repoRoot -Parent
    $candidates = @(
        (Join-Path $parentDir 'Dream_Oracle'),
        (Join-Path $parentDir 'dream-oracle'),
        (Join-Path $parentDir 'dream_oracle')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw 'Dream Oracle repo not found. Pass -AppRepoRoot or set DREAM_ORACLE_APP_ROOT.'
}

function Resolve-FlutterCommand {
    if (Get-Command puro -ErrorAction SilentlyContinue) {
        return @('puro', 'flutter')
    }

    if (Get-Command flutter -ErrorAction SilentlyContinue) {
        return @('flutter')
    }

    throw 'Neither puro nor flutter is available on PATH.'
}

$resolvedAppRepoRoot = Resolve-AppRepoRoot $AppRepoRoot

if (-not $FlutterAppDir) {
    $FlutterAppDir = Join-Path $resolvedAppRepoRoot 'apps\mobile_flutter'
}

$resolvedFlutterAppDir = (Resolve-Path $FlutterAppDir).Path
$driverFile = Join-Path $resolvedFlutterAppDir $DriverPath
$targetFile = Join-Path $resolvedFlutterAppDir $TargetPath

if (-not $DartDefineFromFile) {
    $envCandidates = @(
        (Join-Path $resolvedFlutterAppDir '.env'),
        (Join-Path $resolvedAppRepoRoot '.env')
    )

    foreach ($candidate in $envCandidates) {
        if (Test-Path $candidate) {
            $DartDefineFromFile = (Resolve-Path $candidate).Path
            break
        }
    }
}

if (-not (Test-Path $driverFile)) {
    throw "Flutter driver file not found: $driverFile"
}

if (-not (Test-Path $targetFile)) {
    throw "Flutter target file not found: $targetFile"
}

$flutterCommand = Resolve-FlutterCommand
$flutterExecutable = $flutterCommand[0]
$flutterPrefixArgs = @()

if ($flutterCommand.Count -gt 1) {
    $flutterPrefixArgs = $flutterCommand[1..($flutterCommand.Count - 1)]
}

Push-Location $resolvedFlutterAppDir
try {
    $flutterArgs = @(
        'drive',
        '--driver', $DriverPath,
        '--target', $TargetPath,
        '-d', $DeviceId,
        '--dart-define=FIXTURE_MODE=true',
        "--dart-define=FIXTURE_SEED=$FixtureSeed",
        '--dart-define=DISABLE_CRASH_REPORTING=true',
        "--dart-define=TEST_THEME_MODE=$ThemeMode"
    )

    if ($DartDefineFromFile) {
        $flutterArgs += @('--dart-define-from-file', $DartDefineFromFile)
    }

    if ($ReviewEmail) {
        $flutterArgs += "--dart-define=REVIEW_EMAIL=$ReviewEmail"
    }

    if ($ReviewPassword) {
        $flutterArgs += "--dart-define=REVIEW_PASSWORD=$ReviewPassword"
    }

    Write-Host "Running Flutter screenshot capture from $resolvedFlutterAppDir"
    & $flutterExecutable @flutterPrefixArgs @flutterArgs
}
finally {
    Pop-Location
}