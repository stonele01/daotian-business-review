"""Install this complete skill without copying Git history or private/generated files."""
import argparse
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent.parent
INCLUDE=('SKILL.md','README.md','THIRD_PARTY.md','QA.md','requirements.txt','agents','assets','examples','references','scripts','tests')


def install(dest,update=False):
    dest=Path(dest).expanduser().resolve()
    if dest==ROOT:
        print(f'Already at source: {dest}');return
    sources=[]
    for name in INCLUDE:
        p=ROOT/name
        if not p.exists():continue
        sources.extend([p] if p.is_file() else (f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'))
    conflicts=[str(s.relative_to(ROOT)) for s in sources if (dest/s.relative_to(ROOT)).exists() and s.read_bytes()!=(dest/s.relative_to(ROOT)).read_bytes()]
    if conflicts and not update:
        raise SystemExit('Existing files differ; review before using --update: '+', '.join(conflicts))
    for s in sources:
        d=dest/s.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d)
    print(f'Installed {len(sources)} files to {dest}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dest',default=str(Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'skills'/'daotian-business-review'))
    p.add_argument('--update',action='store_true')
    args=p.parse_args();install(args.dest,args.update)
