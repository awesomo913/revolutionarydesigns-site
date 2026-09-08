"""Build the game from its canonical deployed-source successor, game/src."""
from pathlib import Path
import hashlib
import io
import tarfile
import py_compile

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'game/src'
files={f'assets/{p.name}':p for p in src.glob('*.py')}
art_names=['panda-journey.png','creatures-journey.png','relics-journey.png','worlds-grove.png','worlds-beyond.png']
files.update({f'assets/art/{name}':ROOT/'game/art'/name for name in art_names})
files['assets/mutant.png']=ROOT/'game/art/legacy-mutant.png'
files.update({f'assets/audio/{p.name}':p for p in (ROOT/'game/audio').glob('*') if p.suffix in ('.wav','.ogg','.json')})
for p in src.glob('*.py'): py_compile.compile(str(p),doraise=True)
archive=ROOT/'game/web.tar.gz'
temp=archive.with_suffix('.next.gz')
with tarfile.open(temp,'w:gz') as tar:
    for name,p in sorted(files.items()):
        data=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644
        tar.addfile(info,io.BytesIO(data))
with tarfile.open(temp) as tar:
    assert set(tar.getnames())==set(files)
    for name,p in files.items(): assert tar.extractfile(name).read()==p.read_bytes()
temp.replace(archive)
print(f'Verified {len(files)} archive files; {archive.stat().st_size:,} bytes')
print('SHA256',hashlib.sha256(archive.read_bytes()).hexdigest())
