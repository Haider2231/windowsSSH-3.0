# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/piloto.ico', 'resources'), ('styles/copilot.qss', 'styles'), ('styles/main.qss', 'styles'), ('UglyWidgets/static/sshconfrontend.js', 'UglyWidgets/static'), ('UglyWidgets/static/winconfrontend.js', 'UglyWidgets/static'), ('UglyWidgets/static/xterm-addon-fit.min.js', 'UglyWidgets/static'), ('UglyWidgets/static/xterm.min.css', 'UglyWidgets/static'), ('UglyWidgets/static/xterm.min.js', 'UglyWidgets/static'), ('UglyWidgets/qtsshcon.html', 'UglyWidgets')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
