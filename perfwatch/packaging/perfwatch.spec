from pathlib import Path


project_root = Path(SPECPATH).resolve().parent
native_files = list((project_root / "build" / "phase8").glob("perfwatch_native*.pyd"))
if len(native_files) != 1:
    raise RuntimeError(f"expected one perfwatch_native .pyd, found {len(native_files)}")

a = Analysis(
    [str(project_root / "python" / "src" / "perfwatch" / "runtime.py")],
    pathex=[
        str(project_root / "python" / "src"),
        str(project_root / "build" / "phase8"),
    ],
    binaries=[(str(native_files[0]), ".")],
    datas=[
        (str(project_root / "ui" / "dashboard" / "dist"), "dashboard"),
        (
            str(project_root / "python" / "src" / "perfwatch" / "storage" / "schema.sql"),
            "perfwatch/storage",
        ),
    ],
    hiddenimports=["perfwatch_native"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="perfwatch",
    console=True,
    contents_directory="_internal",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="perfwatch",
)
