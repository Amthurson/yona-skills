"""Validate the distributable Skill without customer connections or dependencies."""
from pathlib import Path
import json,re,sys

def validate(root):
    root=Path(root);manifest=json.loads((root/'skill-release.json').read_text(encoding='utf-8-sig'))
    skill=(root/'SKILL.md').read_text(encoding='utf-8-sig')
    assert manifest['schema']==1 and manifest['skill']=='yona-supplier-catalog'
    assert re.fullmatch(r'\d+\.\d+\.\d+',manifest['version']) and manifest['stableBranch']=='main'
    assert re.search(r'(?m)^name: yona-supplier-catalog$',skill)
    assert re.search(r'(?m)^  version: '+re.escape(manifest['version'])+r'$',skill)
    count=0
    for p in root.rglob('*'):
        relative=p.relative_to(root)
        if '.git'in relative.parts or '__pycache__'in relative.parts or not p.is_file():continue
        assert not p.is_symlink() and p.stat().st_size<1024*1024,relative
        assert p.suffix in ('.md','.json','.py','.ps1','.csv')or p.name in ('.gitignore','.gitattributes')or relative.as_posix()=='.github/workflows/validate.yml',relative
        text=p.read_text(encoding='utf-8-sig')
        if p.suffix=='.ps1':assert text.isascii(),('PowerShell scripts must parse on non-Chinese Windows locales',relative)
        assert not re.search(r'(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',text),relative
        if p.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if '://'in link or link.startswith('#')or '<'in link:continue
                target=(p.parent/link.split('#')[0]).resolve();assert target.is_relative_to(root.resolve())and target.is_file(),(relative,link)
        count+=1
    return {'skill':manifest['skill'],'version':manifest['version'],'files':count,'validated':True}

if __name__=='__main__':print(json.dumps(validate(Path(__file__).resolve().parents[1]),ensure_ascii=False))
