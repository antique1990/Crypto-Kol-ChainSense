<<<<<<< HEAD
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('plotly') + collect_submodules('quant_factors')
=======
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('plotly') + collect_submodules('quant_factors')
>>>>>>> 58ca9b0f7c8abe4bc92b585453cae0db7dde4d66
datas = collect_data_files('plotly') + [
    ('quant_factors\\run_consensus.py', 'quant_factors'),
    ('quant_factors\\feature_engine.py', 'quant_factors'),
    ('quant_factors\\consensus_now.py', 'quant_factors'),
    ('quant_factors\\render_consensus.py', 'quant_factors'),
    ('quant_factors\\trader_composite.py', 'quant_factors'),
    ('quant_factors\\capabilities\\*.py', 'quant_factors\\capabilities'),
    # profiles_v2 is a flat directory of JSON profile files.  Use a glob here
    # (rather than Tree) because this PyInstaller version expects (src, dest)
    # pairs in the datas list.
    ('profiles_v2\\*.json', 'profiles_v2'),
    ('ohlc_daily.json', '.'),
<<<<<<< HEAD
    ('macro_daily.json', '.'),
    ('capabilities_v1.json', '.'),
    ('capabilities_seed.json', '.'),
]

a = Analysis(
    ['quant_factors\\consensus_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='consensus_gui',
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
=======
    ('macro_daily.json', '.'),
    ('capabilities_v1.json', '.'),
    ('capabilities_seed.json', '.'),
]

a = Analysis(
    ['quant_factors\\consensus_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='consensus_gui',
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
>>>>>>> 58ca9b0f7c8abe4bc92b585453cae0db7dde4d66
