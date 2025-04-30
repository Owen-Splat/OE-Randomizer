# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['randomizer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('RandomizerCore/Data/StageList.yml', 'RandomizerCore/Data'),
        ('RandomizerCore/Data/Weapons.yml', 'RandomizerCore/Data')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='Octo Expansion Randomizer',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
)

app = BUNDLE(exe,
    name='Octo Expansion Randomizer.app',
    bundle_identifier=None,
    info_plist={
        "LSBackgroundOnly": False,
        "CFBundleDisplayName": "Octo Expansion Randomizer",
        "CFBundleName": "OE Randomizer",
        "CFBundleShortVersionString": "0.1.0"
    })

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Octo Expansion Randomizer',
)
