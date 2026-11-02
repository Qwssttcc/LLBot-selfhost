"""Create independent credentials and empty data directories; never imports account sessions."""
import argparse,copy,getpass,json,os,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--non-interactive',action='store_true',help='Generate credentials; display the initial WebUI password locally');args=p.parse_args()
state=ROOT/'state';files=[state/'llbot-default.json',state/'llbot-data/webui_token.txt',state/'api-access.secret']
if any(f.exists() for f in files):raise SystemExit('Configuration already exists; refusing to overwrite credentials.')
os.umask(0o077)
pwd='' if args.non_interactive else getpass.getpass('WebUI password (blank: generate): ')
generated=not pwd
if generated:pwd=secrets.token_urlsafe(24)
if len(pwd)<12:raise SystemExit('Use at least 12 characters for the new independent installation.')
api=secrets.token_urlsafe(32)
cfg=json.loads((ROOT/'config/llbot-default.example.json').read_text(encoding='utf-8'))
cfg['webui']={'enable':True,'host':'0.0.0.0','port':3080}
cfg['milky']['enable']=True;cfg['milky']['http'].update({'host':'0.0.0.0','port':5010,'prefix':'','accessToken':api});cfg['milky']['webhook']={'urls':[],'accessToken':''}
cfg['ob11']['enable']=False;cfg['satori']['enable']=False;cfg['log']=False;cfg['logLevel']='warn';cfg['musicSignUrl']=''
for d in [state,state/'llbot-data',state/'qq-home']:d.mkdir(mode=0o700,parents=True,exist_ok=True);d.chmod(0o700)
for target,value in [(files[0],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n'),(files[1],pwd),(files[2],api)]:
 with target.open('x',encoding='utf-8',newline='\n') as f:f.write(value)
 target.chmod(0o600)
print('Independent configuration created; no account profile was imported.')
if generated:print('Initial WebUI password: '+pwd)
print('Milky access token is in state/api-access.secret; keep it private.')
