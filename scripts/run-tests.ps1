# SentinelAI test & validation commands (Windows PowerShell)
# Usage: .\scripts\run-tests.ps1 [command]

param(
    [Parameter(Position = 0)]
    [ValidateSet("test", "test-all", "test-cov", "smoke-test", "validate", "production-check", "replay-demo", "incidents", "incidents-async", "redis-diag", "full-validation", "install-test-deps")]
    [string]$Command = "test"
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Run-Python {
    param([string[]]$Args)
    & python @Args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

switch ($Command) {
    "test"           { Run-Python @("-m", "pytest", "-m", "not integration and not slow") }
    "test-all"       { Run-Python @("-m", "pytest") }
    "test-cov"       { Run-Python @("-m", "pytest", "-m", "not integration", "--cov=backend/app", "--cov-report=term-missing") }
    "smoke-test"     { Run-Python @("-m", "pytest", "backend/tests/test_pipeline.py", "backend/tests/test_health.py", "-v") }
    "validate"       { Run-Python @("scripts/test-platform.py") }
    "production-check" { Run-Python @("scripts/production-check.py") }
    "replay-demo"    { Run-Python @("scripts/demo-replay.py") }
    "incidents"      { Run-Python @("scripts/generate-incidents.py", "--all-types") }
    "incidents-async"{ Run-Python @("scripts/generate-incidents.py", "--all-types", "--async") }
    "redis-diag"     { Run-Python @("scripts/redis-diagnostics.py") }
    "full-validation" {
        Run-Python @("scripts/test-platform.py")
        Run-Python @("-m", "pytest", "backend/tests/test_pipeline.py", "backend/tests/test_health.py", "-v")
        Run-Python @("scripts/production-check.py")
    }
    "install-test-deps" {
        Run-Python @("-m", "pip", "install", "-r", "backend/requirements.txt", "-r", "backend/requirements-dev.txt")
    }
}
