param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"

$repositoryRoot = $PSScriptRoot
$buildRoot = Join-Path $repositoryRoot "build"
$binaryOutput = Join-Path $buildRoot "binary"
$workOutput = Join-Path $buildRoot "pyinstaller"
$distRoot = Join-Path $repositoryRoot "dist"
$productName = "構文エラー解析ツール_Windows"
$productDirectory = Join-Path $distRoot $productName
$archivePath = Join-Path $distRoot "$productName.zip"

foreach ($target in @($buildRoot, $distRoot)) {
    $resolvedParent = [System.IO.Path]::GetFullPath((Split-Path $target -Parent))
    if ($resolvedParent -ne [System.IO.Path]::GetFullPath($repositoryRoot)) {
        throw "ビルド出力先がリポジトリ外です: $target"
    }
}

& $PythonExecutable -c "import tkinter; interpreter = tkinter.Tcl(); print(interpreter.eval('info library'))"
if ($LASTEXITCODE -ne 0) {
    throw "Tcl/Tkを利用できるPythonが必要です。"
}

& $PythonExecutable -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $binaryOutput `
    --workpath $workOutput `
    (Join-Path $repositoryRoot "syntax_error_helper.spec")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstallerの実行に失敗しました。"
}

$executablePath = Join-Path $binaryOutput "構文エラー解析ツール.exe"
if (-not (Test-Path -LiteralPath $executablePath -PathType Leaf)) {
    throw "配布用実行ファイルが生成されませんでした。"
}

if (Test-Path -LiteralPath $productDirectory) {
    Remove-Item -LiteralPath $productDirectory -Recurse -Force
}
if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

New-Item -ItemType Directory -Path $productDirectory | Out-Null
Copy-Item -LiteralPath $executablePath -Destination $productDirectory
Copy-Item -LiteralPath (Join-Path $repositoryRoot "distribution\はじめに.txt") -Destination $productDirectory
Copy-Item -LiteralPath (Join-Path $repositoryRoot "LICENSE") -Destination (Join-Path $productDirectory "LICENSE.txt")
Copy-Item -LiteralPath (Join-Path $repositoryRoot "examples") -Destination $productDirectory -Recurse

Compress-Archive -LiteralPath $productDirectory -DestinationPath $archivePath -CompressionLevel Optimal

Write-Host "ビルドが完了しました。"
Write-Host "配布フォルダー: $productDirectory"
Write-Host "BOOTH登録用ZIP: $archivePath"
