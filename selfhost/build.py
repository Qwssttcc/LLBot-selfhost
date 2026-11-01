"""Build an external-PMHQ-only controller. Never starts or deploys QQ."""
import argparse,json,os,subprocess,shutil
from pathlib import Path
from datetime import datetime,timezone
from prepare import ROOT,MANIFEST,prepare_tools
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--node',default=shutil.which('node'));a=p.parse_args()
if not a.node:p.error('Provide Node.js 24 with --node')
node=str(Path(a.node).resolve());v=subprocess.check_output([node,'--version'],text=True).strip()
if int(v.lstrip('v').split('.')[0])!=MANIFEST['node_major']:p.error('Node.js 24 is required')
prepare_tools();env=os.environ.copy();env.update(YARN_ENABLE_SCRIPTS='false',YARN_ENABLE_TELEMETRY='0',YARN_TASK_POOL_CONCURRENCY='1',YARN_TASK_POOL_MODE='async');env['PATH']=str(Path(node).parent)+os.pathsep+env.get('PATH','')
fe=ROOT/'src/webui/FE';report={'version':MANIFEST['fork_version'],'server_modified':False,'real_qq_login_tested':False,'steps':[]}
steps=[('backend-install',[node,str(ROOT/'selfhost/tools/yarn/bin/yarn.js'),'install','--immutable','--mode=skip-build'],ROOT,False),('frontend-install',[node,str(ROOT/'selfhost/tools/pnpm/bin/pnpm.mjs'),'install','--frozen-lockfile','--ignore-scripts','--config.manage-package-manager-versions=false','--config.package-manager-strict=false'],fe,False),('backend-build',[node,str(ROOT/'node_modules/vite/bin/vite.js'),'build'],ROOT,False),('frontend-build',[node,str(fe/'node_modules/vite/bin/vite.js'),'build'],fe,False),('unit-tests',[node,str(ROOT/'node_modules/vitest/vitest.mjs'),'run','--config','vitest.config.ts'],ROOT,False),('backend-typecheck',[node,str(ROOT/'node_modules/typescript/bin/tsc'),'--noEmit'],ROOT,False),('frontend-typecheck',[node,str(fe/'node_modules/typescript/bin/tsc'),'--noEmit'],fe,True)]
try:
 for name,cmd,cwd,known_failure in steps:
  with (ROOT/'selfhost'/f'{name}.log').open('w',encoding='utf-8') as out:res=subprocess.run(cmd,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
  report['steps'].append({'name':name,'exit_code':res.returncode,'known_upstream_typecheck_failure':known_failure and res.returncode!=0});print(f'{name}: {res.returncode}',flush=True)
  if not known_failure:res.check_returncode()
 shutil.copy2(ROOT/'LICENSE',ROOT/'dist/LICENSE');shutil.copy2(ROOT/'README.selfhost.md',ROOT/'dist/README.selfhost.md')
 report['status']='experimental_build_verified_external_qq_backend_required'
finally:
 report['finished_at']=datetime.now(timezone.utc).isoformat();(ROOT/'selfhost/build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
