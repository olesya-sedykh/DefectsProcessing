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
    hiddenimports=[
        'numpy',
        'pandas',
        'PIL',
        'PIL.Image',
        'matplotlib',
        'matplotlib.pyplot',
        'pywt',
        
        'cv2',
        'cv2.dnn',
        'cv2.data',
        'cv2.videoio',
        
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.sip',
        'PyQt5.QtWebEngineWidgets',
        
        'tensorflow',
        'tensorflow_core',
        'tensorflow.python',
        'tensorflow.keras',
        'tensorflow.keras.layers',
        'keras.api._v2.keras',
        
        'torch',
        'torch.nn',
        'torchvision',
        'torchvision.models',
        'ultralytics',
        'ultralytics.yolo',
        'ultralytics.models',
        'ultralytics.utils',
        'ultralytics.data',
        
        'skimage',
        'skimage.io',
        'skimage.transform',
        'skimage.restoration',
        'skimage.filters',
        
        'backend.ProcessingClass',
        'frontend.PreviewWindowImage',
        'frontend.PreviewWindowVideo',
        'frontend.PreviewWindowDataset',
        'frontend.QFlowLayout',
        'ParameterDialog',
    ],
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