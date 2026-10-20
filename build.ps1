param([string]$Version = '0.2.0')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
python -m PyInstaller --noconfirm --windowed --onedir --name opzi --icon opzi.ico --add-data 'ui;ui' --hidden-import webview.platforms.edgechromium --hidden-import webview.platforms.winforms app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
Copy-Item -LiteralPath LICENSE,THIRD_PARTY_NOTICES.md,README.md -Destination dist\opzi
New-Item -ItemType Directory -Path dist\opzi\licenses -Force | Out-Null
@'
from importlib.metadata import distributions
from pathlib import Path
import shutil, sysconfig
out = Path('dist/opzi/licenses')
for dist in distributions():
    for file in dist.files or []:
        name = file.name.lower()
        if '.dist-info' not in str(file) or not name.startswith(('license', 'copying', 'notice')):
            continue
        src = Path(dist.locate_file(file))
        if src.is_file():
            target = out / dist.metadata['Name'] / str(file).split('.dist-info/', 1)[-1]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
license_file = Path(sysconfig.get_path('stdlib')).parent / 'LICENSE.txt'
if license_file.exists():
    shutil.copyfile(license_file, out / 'Python-LICENSE.txt')
'@ | python -
if ($LASTEXITCODE -ne 0) { throw 'License collection failed' }
New-Item -ItemType Directory -Path release -Force | Out-Null
Compress-Archive -Path dist\opzi\* -DestinationPath "release\opzi-$Version-windows-x64.zip" -Force
Write-Host "Built release/opzi-$Version-windows-x64.zip"
