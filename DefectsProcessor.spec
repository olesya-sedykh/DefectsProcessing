# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend', 'backend'),
        ('frontend', 'frontend'),
        ('temp', 'temp'),
        ('models', 'models'),
        ('icons', 'icons'),
    ],
    hiddenimports = [
        'numpy',
        'numpy.core._multiarray_umath',
        'pywt',
        'shutil',
        'tempfile',
        
        'cv2',
        'cv2.dnn',
        'cv2.data',
        'cv2.videoio',
        
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        
        'tensorflow',
        'tensorflow.python.keras',
        'keras.api._v2.keras',
        'h5py',

        'ultralytics',
        'ultralytics.models',
        'ultralytics.nn',
        'ultralytics.utils',
        'ultralytics.data',
        'ultralytics.engine'
        
        'torch',
        'torch.nn',
        'torch._C',
        
        'skimage',
        'skimage.io',
        'skimage.restoration',
        'skimage.filters',
        'skimage._shared.geometry',
        
        'backend.ProcessingClass',
        'frontend.MainScrean',
        'frontend.PreviewWindowImage',
        'frontend.PreviewWindowVideo',
        'frontend.PreviewWindowDataset',
        'frontend.QFlowLayout',
        'frontend.ParameterDialog'
    ]
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DefectsProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False
)