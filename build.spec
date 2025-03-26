exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PoseEstimationApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
    onefile=True
) 