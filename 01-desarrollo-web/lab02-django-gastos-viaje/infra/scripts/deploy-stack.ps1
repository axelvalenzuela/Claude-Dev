<#
.SYNOPSIS
    Deploys one of this project's CloudFormation templates using the
    matching parameter file under infra/parameters/.

.DESCRIPTION
    Thin wrapper around `aws cloudformation deploy` so every stack is
    deployed the same way: same parameter-file convention, same
    capabilities flag (IAM roles are created here — see
    infra/docs/adr/0008 — so CAPABILITY_NAMED_IAM is required), same
    stack-naming pattern.

    This script does not run automatically as part of anything — it is
    provided for when you actually have an AWS account/credentials
    configured and are ready to deploy for real. Until then, use
    `cfn-lint` (see infra/README.md) to validate templates offline.

.PARAMETER StackName
    One of: network, storage, security, messaging, compute, edge.
    Deploy in that order — each later stack's parameter file needs
    output values from the ones before it (infra/docs/adr/0002).

.PARAMETER Environment
    Which parameters/<Environment>.json file to use. Defaults to "dev".

.EXAMPLE
    ./deploy-stack.ps1 -StackName network -Environment dev
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("network", "storage", "security", "messaging", "compute", "edge")]
    [string]$StackName,

    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$infraRoot = Split-Path -Parent $scriptDir
$templateFile = Join-Path $infraRoot "templates\$StackName.yaml"
$parametersFile = Join-Path $infraRoot "parameters\$Environment.json"

if (-not (Test-Path $parametersFile)) {
    Write-Error "Parameter file not found: $parametersFile`nCopy infra/parameters/dev.example.json to $Environment.json and fill in real values first."
    exit 1
}

$allParams = Get-Content $parametersFile -Raw | ConvertFrom-Json
$stackParams = $allParams.$StackName
if (-not $stackParams) {
    Write-Error "No '$StackName' section found in $parametersFile"
    exit 1
}

$overrides = @()
foreach ($prop in $stackParams.PSObject.Properties) {
    if ($prop.Name -eq "_comment") { continue }
    $overrides += "$($prop.Name)=$($prop.Value)"
}

$cfnStackName = "$($stackParams.ProjectName)-$($stackParams.Environment)-$StackName"

Write-Host "Deploying stack '$cfnStackName' from $templateFile ..."

aws cloudformation deploy `
    --stack-name $cfnStackName `
    --template-file $templateFile `
    --parameter-overrides $overrides `
    --capabilities CAPABILITY_NAMED_IAM `
    --no-fail-on-empty-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "Stack outputs:"
    aws cloudformation describe-stacks --stack-name $cfnStackName --query "Stacks[0].Outputs" --output table
}
