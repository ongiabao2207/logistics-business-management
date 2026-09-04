$ErrorActionPreference = "Stop"
$composeFile = Join-Path $PSScriptRoot "docker-compose.yml"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")

function Invoke-DatabaseSeed {
    param(
        [string]$Service,
        [string]$DatabaseUser,
        [string]$DatabaseName,
        [string]$LocalFile,
        [string]$ContainerFile
    )

    docker compose -f $composeFile cp $LocalFile "${Service}:${ContainerFile}"
    if ($LASTEXITCODE -ne 0) { throw "Cannot copy seed file to $Service" }

    docker compose -f $composeFile exec -T $Service psql -v ON_ERROR_STOP=1 -U $DatabaseUser -d $DatabaseName -f $ContainerFile
    if ($LASTEXITCODE -ne 0) { throw "Database seed failed at $Service" }
}

Invoke-DatabaseSeed "contract-db" "contract_user" "contract_db" `
    (Join-Path $repoRoot "services/contract-service/db/payment_integration_seed.sql") "/tmp/payment_integration_seed.sql"
Invoke-DatabaseSeed "price-db" "price_user" "price_db" `
    (Join-Path $repoRoot "services/price-service/db/payment_integration_seed.sql") "/tmp/payment_integration_seed.sql"
Invoke-DatabaseSeed "production-db" "production_user" "production_db" `
    (Join-Path $repoRoot "services/production-service/db/payment_integration_seed.sql") "/tmp/payment_integration_seed.sql"
Invoke-DatabaseSeed "payment-db" "payment_user" "payment_db" `
    (Join-Path $repoRoot "services/payment-service/db/seed.sql") "/tmp/payment_seed.sql"

Write-Host "Seed completed. Contracts HD2026001-HD2026008 have Production data for all months of 2026."
