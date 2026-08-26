<#
.SYNOPSIS
    Validates every CloudFormation template in infra/templates/ with
    cfn-lint, using the Python interpreter in lab2's virtual environment
    (where cfn-lint is installed — see infra/README.md).

.DESCRIPTION
    Safe to run with no AWS account or credentials at all: cfn-lint only
    parses and statically analyzes the YAML, it never calls AWS.
#>
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$infraRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent $infraRoot
$python = Join-Path $repoRoot "lab2\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python venv not found at $python. Run: pip install cfn-lint inside lab2/.venv first."
    exit 1
}

$templates = Get-ChildItem (Join-Path $infraRoot "templates") -Filter "*.yaml" | Sort-Object Name

$hadIssues = $false
foreach ($template in $templates) {
    Write-Host "===== $($template.Name) ====="
    & $python -c @"
from cfnlint import api
matches = api.lint_all(open(r'$($template.FullName)', encoding='utf-8').read())
if not matches:
    print('OK - no issues')
for m in matches:
    print(m)
"@
}
