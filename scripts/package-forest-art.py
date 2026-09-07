"""Package an art-only overlay into the known working pygbag archive.

The existing loader and all pre-existing payloads except the import in main.py
are retained byte-for-byte. Run from any directory.
"""
from pathlib import Path
import io
import tarfile
import hashlib

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / "game/web.tar.gz"
with tarfile.open(archive, "r:gz") as original:
    members = {m.name: (m, original.extractfile(m).read() if m.isfile() else None) for m in original.getmembers()}
main_info, main_bytes = members["assets/main.py"]
marker = b"from visual_skin import install\ninstall()\n\n"
if marker not in main_bytes:
    main_bytes = main_bytes.replace(b"from game import main", marker + b"from game import main", 1)
    if marker not in main_bytes:
        raise RuntimeError("Shipped entry point has changed; inspect before packaging.")
members["assets/main.py"] = (main_info, main_bytes)
for source in [ROOT / "game/visual_skin.py", *(ROOT / "game/art").glob("*.png")]:
    name = "assets/visual_skin.py" if source.name == "visual_skin.py" else "assets/art/" + source.name
    data = source.read_bytes()
    info = tarfile.TarInfo(name)
    info.mode = 0o644
    members[name] = (info, data)
temp = archive.with_suffix(".next.gz")
with tarfile.open(temp, "w:gz") as target:
    for name, (info, data) in members.items():
        if data is not None:
            info.size = len(data)
        target.addfile(info, io.BytesIO(data) if data is not None else None)
with tarfile.open(temp) as check:
    for name, (info, data) in members.items():
        if data is not None and check.extractfile(name).read() != data:
            raise RuntimeError("Packaging verification failed: " + name)
temp.replace(archive)
print("Art package verified:", len(members), "entries,", archive.stat().st_size, "bytes")
print("sha256:", hashlib.sha256(archive.read_bytes()).hexdigest())
