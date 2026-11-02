#!/bin/sh
set -eu
exec dbus-run-session -- python3 - <<'SUPERVISOR'
import os,time,signal,subprocess,ctypes
from pathlib import Path
ctypes.CDLL(None).prctl(36,1,0,0,0)
os.umask(0o077)
for path in ['/root/.config','/root/.cache','/tmp/runtime']:Path(path).mkdir(parents=True,exist_ok=True)
os.chmod('/tmp/runtime',0o700)
os.environ.update(HOME='/root',XDG_CONFIG_HOME='/root/.config',XDG_CACHE_HOME='/root/.cache',XDG_RUNTIME_DIR='/tmp/runtime',DISPLAY=':99')
stop=False
def stopping(*args):
 global stop
 stop=True
signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
# The isolated container is stopped before every new start; stale X sockets cannot belong to a running server.
for stale in ['/tmp/.X99-lock','/tmp/.X11-unix/X99']:
 try:os.unlink(stale)
 except FileNotFoundError:pass
xlog=open('/tmp/x.log','ab');plog=open('/tmp/pmhq.log','ab')
x=subprocess.Popen(['Xvfb',':99','-screen','0','1280x720x24','-ac','+extension','GLX','-noreset','-dpi','96'],stdout=xlog,stderr=xlog)
time.sleep(1)
if x.poll() is not None:raise SystemExit(71)
p=subprocess.Popen(['/opt/pmhq','--config=/opt/pmhq_config.json','--qq-path=/opt/QQ/qq','--so=/opt/libpmhq.so','--qq-args=--no-sandbox --disable-dev-shm-usage --disable-gpu-sandbox --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader'],stdout=plog,stderr=plog)
def mains():
 found=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   exe=(d/'exe').resolve();cmd=(d/'cmdline').read_bytes();stat=(d/'stat').read_text()
   if str(exe)=='/opt/QQ/qq' and b'--type=' not in cmd and stat.split(') ',1)[1][0]!='Z':found.append(int(d.name))
  except (OSError,ValueError):pass
 return found
start=time.monotonic();seen=False;rc=0
while not stop:
 q=mains()
 if q:seen=True
 if x.poll() is not None:rc=72;break
 if p.poll() not in (None,0):rc=73;break
 if seen and not q:rc=74;break
 if not seen and time.monotonic()-start>35:rc=75;break
 # Reap adopted children; Popen retains its own launcher status.
 p.poll()
 while True:
  try:
   child,_=os.waitpid(-1,os.WNOHANG)
   if child==0:break
  except ChildProcessError:break
 time.sleep(1)
for pid in mains()+[p.pid,x.pid]:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
limit=time.monotonic()+5
while mains() and time.monotonic()<limit:time.sleep(.2)
for pid in mains()+[p.pid,x.pid]:
 try:os.kill(pid,signal.SIGKILL)
 except ProcessLookupError:pass
raise SystemExit(rc)

SUPERVISOR
