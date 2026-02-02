# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('app', 'app')],
    hiddenimports=[],  # Removed legacy flet_desktop and flet_runtime
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Changed: removed a.binaries, a.zipfiles, a.datas for directory mode
    exclude_binaries=True,  # Added: keep binaries separate
    name='sos_digital_pyme',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png',
)

# Added COLLECT for directory mode
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sos_digital_pyme',
)
app = BUNDLE(
    exe,
    name='SOS Digital PyME.app',
    icon='assets/icon.png',
    bundle_identifier=None,
)
