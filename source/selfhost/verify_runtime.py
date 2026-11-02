"""Audit the built controller and smoke-test only on loopback with no QQ backend."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,socket,subprocess,time,urllib.request,urllib.error,secrets
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--node',required=True);a=p.parse_args()
dist=ROOT/'dist'
forbidden=['auth_token','auth-token','api-auth.luckylillia','llbot-api-auth','auth.luckylillia','SignProxy','sign-proxy','DirectQQProtocol']
findings=[]
for f in [dist/'llbot.js',*(dist/'webui').rglob('*.js')]:
 text=f.read_text(encoding='utf-8')
 findings.extend({'file':f.relative_to(dist).as_posix(),'marker':m} for m in forbidden if m in text)
native=[f.relative_to(dist).as_posix() for f in dist.rglob('*') if 'sign-proxy' in f.name.lower()]
assert not findings and not native,(findings,native)
# Copy into a fresh path; do not read or mutate any deployed/user data.
smoke=ROOT/'selfhost/smoke-data'
assert smoke.resolve().is_relative_to((ROOT/'selfhost').resolve())
if smoke.exists():shutil.rmtree(smoke)
shutil.copytree(dist,smoke/'runtime')
work=smoke/'runtime';(work/'data').mkdir(exist_ok=True)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
with socket.socket() as sock:sock.bind(('127.0.0.1',0));backend_port=sock.getsockname()[1]
config=json.loads((work/'default_config.json').read_text());config['webui']={'enable':True,'host':'127.0.0.1','port':port}
config['milky']['enable']=False;config['satori']['enable']=False;config['ob11']['enable']=False
(work/'default_config.json').write_text(json.dumps(config),encoding='utf-8')
password=secrets.token_urlsafe(24);(work/'data/webui_token.txt').write_text(password)
# Fail any accidental external fetch/WS instead of contacting provider, QQ, or signing services.
guard=smoke/'loopback-only.mjs';guard.write_text("""const fetch0=globalThis.fetch;
const allowed=u=>{const p=new URL(u);if(!['127.0.0.1','localhost','[::1]'].includes(p.hostname))throw new Error('External network prohibited by smoke test');};
globalThis.fetch=(u,...rest)=>{allowed(typeof u==='string'||u instanceof URL?u:u.url);return fetch0(u,...rest);};
const WS=globalThis.WebSocket;globalThis.WebSocket=class extends WS{constructor(u,...rest){allowed(u);super(u,...rest);}};
""",encoding='utf-8')
env=os.environ.copy();env['AUTH_TOKEN']='intentionally-invalid-test-value';env.pop('LL_IPC_PIPE',None)
report={'artifact_registration_markers':findings,'native_signing_modules':native,'server_modified':False,'real_qq_login_tested':False,'network_scope':'loopback only'}
def req(path,auth=False):
 headers={'X-Webui-Token':hashlib.sha256(password.encode()).hexdigest()} if auth else {}
 try:
  with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers=headers),timeout=2) as res:return res.status,res.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
process=None
try:
 with (ROOT/'selfhost/runtime-smoke.log').open('w',encoding='utf-8') as out:
  process=subprocess.Popen([a.node,'--import',guard.as_uri(),str(work/'llbot.js'),'--pmhq-port',str(backend_port)],cwd=work,env=env,stdout=out,stderr=subprocess.STDOUT)
  for _ in range(60):
   if process.poll() is not None:raise RuntimeError('Runtime exited before WebUI startup')
   try:status,body=req('/');break
   except (OSError,urllib.error.URLError):time.sleep(.2)
  else:raise RuntimeError('No local WebUI within bounded test')
  report['webui_http_status']=status;assert status==200
  report['protected_status_without_password']=req('/api/backend-status')[0];assert report['protected_status_without_password']==403
  status,body=req('/api/backend-status',True);report['backend_status']=json.loads(body)['data'];assert status==200 and report['backend_status']=={'mode':'external-pmhq','connected':False,'online':False}
  status,body=req('/api/login-info',True);report['login_online']=json.loads(body)['data']['online'];assert status==200 and report['login_online']==False
  report['removed_registration_endpoint_status']=req('/api/auth-token/status',True)[0];assert report['removed_registration_endpoint_status']==404
  report['platform_token_file_created']=any((work/'data').glob('auth_token*'));assert not report['platform_token_file_created']
  report['status']='passed_controller_smoke_only'
finally:
 if process is not None:
  process.terminate()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
 report['process_stopped']=process is None or process.poll() is not None
 (ROOT/'selfhost/runtime-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 # The fixture has only generated test data; preserve numeric reports, remove its random password.
 if smoke.exists():shutil.rmtree(smoke)
print(json.dumps(report,ensure_ascii=False))
