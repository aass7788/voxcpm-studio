# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — VoxCPM Studio (one-folder mode for PyTorch DLL compat)"""

import os
from pathlib import Path

# Collect torch DLLs
import torch
torch_lib = Path(torch.__file__).parent / 'lib'
torch_binaries = []
if torch_lib.exists():
    for dll in torch_lib.glob('*.dll'):
        torch_binaries.append((str(dll), 'torch/lib'))

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=torch_binaries,
    datas=[
        ('static', 'static'),
        ('VoxCPM/assets', 'assets'),
    ],
    hiddenimports=[
        'voxcpm', 'voxcpm.core', 'voxcpm.model', 'voxcpm.model.utils',
        'voxcpm.modules', 'voxcpm.utils', 'voxcpm.cli',
        'torch', 'torchaudio', 'torchcodec',
        'transformers', 'transformers.models',
        'soundfile', 'librosa',
        'einops', 'einops.layers',
        'funasr', 'funasr.models', 'funasr.utils',
        'safetensors', 'safetensors.torch',
        'modelscope', 'modelscope.hub',
        'huggingface_hub', 'huggingface_hub.utils',
        'spaces', 'addict', 'simplejson',
        'sortedcontainers', 'argbind',
        'wetext', 'inflect',
        'pydantic', 'pydantic.deprecated',
        'uvicorn', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'fastapi', 'starlette',
        'webview', 'webview.platforms', 'webview.platforms.edgechromium',
        'numpy', 'numpy.core',
        'matplotlib', 'PIL',
        'encodings.idna',
        'importlib.metadata', 'importlib.resources',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test', 'tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoxCPM_Studio',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoxCPM_Studio',
)
