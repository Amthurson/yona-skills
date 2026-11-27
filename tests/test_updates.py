"""Real local Git origins and Windows PowerShell; no GitHub or business API calls."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
PUBLIC='https://github.com/Amthurson/yona-skills.git'
GITLAB='https://gitlab.example.test/customer/yona-skills.git'

class ManagedUpdateTest(unittest.TestCase):
    def setUp(self):
        parent=os.environ.get('YONA_SKILL_TEST_ROOT');self.temp=tempfile.TemporaryDirectory(prefix='yona-skills-',dir=parent);self.base=Path(self.temp.name)
        if parent:self.assertTrue(self.base.resolve().is_relative_to(Path(parent).resolve()))
        self.bare=self.base/'origin.git';self.author=self.base/'author';self.client=self.base/'client/.agents/skills/yona-supplier-catalog';self.state=self.base/'state'
        self.git(None,'init','--bare','--initial-branch=main',str(self.bare))
        self.author.mkdir()
        for p in ROOT.rglob('*'):
            relative=p.relative_to(ROOT)
            if '.git'in relative.parts or '__pycache__'in relative.parts or not p.is_file():continue
            target=self.author/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        self.git(self.author,'init','-b','main');self.git(self.author,'config','user.name','SYNTHETIC QA');self.git(self.author,'config','user.email','qa@example.test');self.git(self.author,'config','commit.gpgsign','false')
        self.git(self.author,'add','.');self.git(self.author,'commit','-m','Synthetic initial release');self.git(self.author,'tag','v0.2.0');self.git(self.author,'remote','add','origin',str(self.bare));self.git(self.author,'push','origin','main','--tags')
        self.env=os.environ.copy();self.env.update({'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'url.'+self.bare.as_uri()+'.insteadOf','GIT_CONFIG_VALUE_0':PUBLIC,'GIT_TERMINAL_PROMPT':'0'})
    def tearDown(self):self.temp.cleanup()
    def git(self,folder,*args):
        r=subprocess.run(['git',*(['-C',str(folder)]if folder else[]),*args],capture_output=True,text=True)
        self.assertEqual(0,r.returncode,r.stderr);return r.stdout.strip()
    def ps(self,script,*args,success=True):
        shell=shutil.which('powershell.exe')or shutil.which('pwsh')
        if not shell:self.skipTest('PowerShell not installed')
        r=subprocess.run([shell,'-NoProfile','-NonInteractive','-File',str(script),*map(str,args)],env=self.env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=60)
        if success:self.assertEqual(0,r.returncode,r.stdout+r.stderr);return json.loads(r.stdout.lstrip('\ufeff'))
        self.assertNotEqual(0,r.returncode);return r
    def install(self):return self.ps(ROOT/'scripts/install.ps1','-Destination',self.client,'-StateRoot',self.state)
    def update(self,*args,success=True):return self.ps(self.client/'scripts/update.ps1','-StateRoot',self.state,*args,success=success)
    def advance(self,published=True):
        p=self.author/'skill-release.json';v=json.loads(p.read_text());v['version']='0.2.1';p.write_text(json.dumps(v,indent=2),encoding='utf8')
        p=self.author/'SKILL.md';p.write_text(p.read_text(encoding='utf8').replace('version: 0.2.0','version: 0.2.1'),encoding='utf8')
        self.git(self.author,'add','.');self.git(self.author,'commit','-m','Synthetic next release')
        if published:self.git(self.author,'tag','v0.2.1')
        self.git(self.author,'push','origin','main','--tags')
    def test_install_check_update_rollback_and_latest(self):
        first=self.install();self.assertEqual('0.2.0',first['version']);self.assertFalse(first['serverChanged']);self.advance()
        check=self.update('-CheckOnly');self.assertEqual('0.2.0',check['version']);self.assertEqual('0.2.1',check['availableVersion']);self.assertFalse(check['changed'])
        updated=self.update();self.assertEqual('0.2.1',updated['version']);self.assertTrue(updated['changed'])
        self.assertEqual('0.2.0',self.update('-Version','0.2.0')['version']);self.assertEqual('0.2.1',self.update()['version'])
        self.assertEqual('',self.git(self.client,'status','--porcelain'))
    def test_copied_skill_is_backed_up_and_other_configuration_untouched(self):
        self.client.mkdir(parents=True);old='---\nname: yona-supplier-catalog\ndescription: SYNTHETIC old skill\n---\n'
        (self.client/'SKILL.md').write_text(old);other=self.base/'client/.codex/config.toml';other.parent.mkdir(parents=True);other.write_text('# SYNTHETIC existing MCP configuration\n')
        result=self.install();self.assertTrue(result['previousSkillRetained']);self.assertEqual(old,(Path(result['backup'])/'SKILL.md').read_text())
        self.assertEqual('# SYNTHETIC existing MCP configuration\n',other.read_text())
        self.assertNotIn('.agents/skills',result['backup'].replace('\\','/'))
    def test_dirty_local_skill_is_preserved(self):
        self.install();self.advance();p=self.client/'README.md';p.write_text('SYNTHETIC local customization')
        self.update(success=False);self.assertEqual('SYNTHETIC local customization',p.read_text());self.assertEqual('0.2.0',json.loads((self.client/'skill-release.json').read_text())['version'])
    def test_divergent_local_history_is_not_reset(self):
        self.install();self.git(self.client,'config','user.name','SYNTHETIC');self.git(self.client,'config','user.email','qa@example.test');self.git(self.client,'config','commit.gpgsign','false')
        p=self.client/'README.md';p.write_text('SYNTHETIC committed local customization');self.git(self.client,'add','.');self.git(self.client,'commit','-m','SYNTHETIC local change');old=self.git(self.client,'rev-parse','HEAD');self.advance()
        self.update(success=False);self.assertEqual(old,self.git(self.client,'rev-parse','HEAD'));self.assertEqual('SYNTHETIC committed local customization',p.read_text())
    def test_gitlab_source_switch_and_rejected_foreign_skill(self):
        self.install();self.advance();mirror=self.base/'gitlab.git';self.git(None,'clone','--bare',str(self.bare),str(mirror))
        self.env.update({'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_1':'url.'+mirror.as_uri()+'.insteadOf','GIT_CONFIG_VALUE_1':GITLAB})
        result=self.update('-Origin',GITLAB);self.assertEqual(GITLAB,result['origin']);self.assertEqual('0.2.1',result['version'])
        p=self.author/'skill-release.json';v=json.loads(p.read_text());v['skill']='foreign-skill';p.write_text(json.dumps(v));self.git(self.author,'add','.');self.git(self.author,'commit','-m','Synthetic invalid source');self.git(self.author,'push','origin','main')
        self.update('-Origin',PUBLIC,success=False);self.assertEqual(GITLAB,self.git(self.client,'config','--get','remote.origin.url'))
    def test_unsafe_url_and_backup_in_discovery_tree_are_rejected(self):
        self.ps(ROOT/'scripts/install.ps1','-Destination',self.client,'-Origin','ext::invalid','-StateRoot',self.state,success=False)
        self.ps(ROOT/'scripts/install.ps1','-Destination',self.client,'-StateRoot',self.client.parent/'backup',success=False)
        self.assertFalse(self.client.exists())
    def test_unpublished_main_is_not_installed(self):
        self.install();old=self.git(self.client,'rev-parse','HEAD');self.advance(published=False)
        self.update(success=False);self.assertEqual(old,self.git(self.client,'rev-parse','HEAD'))

if __name__=='__main__':unittest.main()
