$ErrorActionPreference = 'Stop'
$vibesecRoot = Split-Path $PSScriptRoot -Parent
$vibesecData = Join-Path $vibesecRoot 'storage/mysql-data'
$vibesecServer = 'C:/Program Files/MySQL/MySQL Server 9.7/bin/mysqld.exe'
if (-not (Test-Path -LiteralPath (Join-Path $vibesecData 'auto.cnf'))) {
    if ((Test-Path -LiteralPath $vibesecData) -and (Get-ChildItem -LiteralPath $vibesecData -Force)) {
        throw 'Direktori MySQL berisi data yang belum dikenali; tidak diinisialisasi ulang.'
    }
    New-Item -ItemType Directory -Force -Path $vibesecData | Out-Null
    & $vibesecServer --no-defaults --initialize-insecure "--datadir=$vibesecData" --console
    if ($LASTEXITCODE -ne 0) { throw 'Inisialisasi MySQL gagal.' }
}
$vibesecRoute = (& wsl -d Ubuntu-24.04 -- ip -4 route show default) -split '\s+'
$vibesecGateway = $vibesecRoute[[Array]::IndexOf($vibesecRoute, 'via') + 1]
[void][System.Net.IPAddress]::Parse($vibesecGateway)
& $vibesecServer --no-defaults "--datadir=$vibesecData" --port=3308 `
    "--bind-address=127.0.0.1,$vibesecGateway" --mysqlx=OFF --innodb-buffer-pool-size=128M `
    "--log-error=$vibesecData/server.log" "--pid-file=$vibesecData/server.pid"
