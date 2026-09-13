"""Write build/version_info.txt so PyInstaller stamps the exe with the app version
(visible in Explorer under Properties > Details)."""

import os

from version import __version__

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "version_info.txt")

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple}),
    prodvers=({tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Andres Perez'),
        StringStruct('FileDescription', 'AZ-Overlay input overlay'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', 'AZ-Overlay'),
        StringStruct('LegalCopyright', 'Copyright 2026 Andres Perez. MIT License.'),
        StringStruct('OriginalFilename', 'AZ-Overlay.exe'),
        StringStruct('ProductName', 'AZ-Overlay'),
        StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def version_tuple(version):
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return ", ".join(str(p) for p in parts[:4])


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(tuple=version_tuple(__version__), version=__version__))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
