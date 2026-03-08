param(
    [string]$AppRepoRoot,
    [string]$FlutterAppDir,
    [string]$ConfigFile,
    [ValidateSet('ios', 'android')]
    [string]$Platform = 'ios',
    [string]$DeviceId = 'emulator-5556',
    [ValidateSet('light', 'dark', 'system')]
    [string]$ThemeMode = 'light',
    [int]$FixtureSeed = 1337,
    [string]$DartDefineFromFile,
    [string]$ReviewEmail,
    [string]$ReviewPassword,
    [switch]$SkipCapture,
    [ValidateSet('table', 'json')]
    [string]$Output = 'table'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-AppRepoRoot {
    param([string]$RequestedRoot, [string]$RepoRoot)

    if ($RequestedRoot) {
        return (Resolve-Path $RequestedRoot).Path
    }

    if ($env:DREAM_ORACLE_APP_ROOT) {
        return (Resolve-Path $env:DREAM_ORACLE_APP_ROOT).Path
    }

    $parentDir = Split-Path $RepoRoot -Parent
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

function Resolve-ConfigFile {
    param(
        [string]$RequestedConfigFile,
        [string]$RepoRoot,
        [string]$ResolvedAppRepoRoot,
        [string]$RequestedPlatform
    )

    if ($RequestedConfigFile) {
        return (Resolve-Path $RequestedConfigFile).Path
    }

    if ($RequestedPlatform -eq 'android') {
        $candidates = @(
            (Join-Path $RepoRoot 'configs\dream-oracle-android.yaml'),
            (Join-Path $RepoRoot 'configs\dream_oracle_android.yaml'),
            (Join-Path $ResolvedAppRepoRoot 'configs\dream-oracle-android.yaml'),
            (Join-Path $ResolvedAppRepoRoot 'configs\dream_oracle_android.yaml')
        )
    }
    else {
        $candidates = @(
            (Join-Path $RepoRoot 'configs\dream-oracle-polished-iphone6_9.yaml'),
            (Join-Path $RepoRoot 'configs\dream-oracle.yaml'),
            (Join-Path $RepoRoot 'configs\dream_oracle.yaml'),
            (Join-Path $ResolvedAppRepoRoot 'configs\dream-oracle-polished-iphone6_9.yaml'),
            (Join-Path $ResolvedAppRepoRoot 'configs\dream-oracle.yaml'),
            (Join-Path $ResolvedAppRepoRoot 'configs\dream_oracle.yaml')
        )
    }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw 'No Koubou config file found. Pass -ConfigFile with a Dream Oracle YAML config.'
}

function Resolve-PythonExecutable {
    param([string]$RepoRoot)

    $venvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) {
        return (Resolve-Path $venvPython).Path
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    throw 'Python is not available. Create the Koubou virtual environment or install Python.'
}

$repoRoot = (Resolve-Path $PSScriptRoot).Path
$resolvedAppRepoRoot = Resolve-AppRepoRoot $AppRepoRoot $repoRoot
$resolvedConfigFile = Resolve-ConfigFile $ConfigFile $repoRoot $resolvedAppRepoRoot $Platform
$pythonExecutable = Resolve-PythonExecutable $repoRoot
$captureScript = Join-Path $repoRoot 'capture_mobile_app_store_screenshots.ps1'

if (-not $FlutterAppDir) {
    $FlutterAppDir = Join-Path $resolvedAppRepoRoot 'apps\mobile_flutter'
}

if (-not (Test-Path $captureScript)) {
    throw "Capture script not found: $captureScript"
}

$dependencyCheck = & $pythonExecutable -c "import PIL, pydantic, rich, typer, yaml, watchdog" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'Koubou Python dependencies are missing. Run make install-dev or install the package into the selected Python environment.'
}

if (-not $SkipCapture) {
    & powershell -ExecutionPolicy Bypass -File $captureScript -AppRepoRoot $resolvedAppRepoRoot -FlutterAppDir $FlutterAppDir -DeviceId $DeviceId -ThemeMode $ThemeMode -FixtureSeed $FixtureSeed -DartDefineFromFile $DartDefineFromFile -ReviewEmail $ReviewEmail -ReviewPassword $ReviewPassword
}

$originalPythonPath = $env:PYTHONPATH

try {
    $repoSrc = Join-Path $repoRoot 'src'
    if ([string]::IsNullOrWhiteSpace($originalPythonPath)) {
        $env:PYTHONPATH = $repoSrc
    }
    else {
        $env:PYTHONPATH = "$repoSrc;$originalPythonPath"
    }

    Write-Host "Generating framed screenshots with config $resolvedConfigFile"
    & $pythonExecutable -m koubou.cli generate $resolvedConfigFile --output $Output
}
finally {
    $env:PYTHONPATH = $originalPythonPath
}