"""Build and test the historical LLBot fork; never starts the bot or deploys it."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
from prepare import ROOT, MANIFEST, prepare_tools

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--node', default=shutil.which('node'))
args = parser.parse_args()
if not args.node:
    parser.error('Node.js 24 is required; provide --node PATH')
node = str(Path(args.node).resolve())
version = subprocess.check_output([node, '--version'], text=True).strip()
if int(version.lstrip('v').split('.')[0]) != MANIFEST['node_major']:
    parser.error('use the pinned Node.js major version 24')
prepare_tools()
env = os.environ.copy()
env.update({'YARN_ENABLE_SCRIPTS': 'false', 'YARN_ENABLE_TELEMETRY': '0',
            'YARN_TASK_POOL_CONCURRENCY': '1', 'YARN_TASK_POOL_MODE': 'async'})
env['PATH'] = str(Path(node).parent) + os.pathsep + env.get('PATH', '')
yarn = ROOT / 'selfhost/tools/yarn/bin/yarn.js'
pnpm = ROOT / 'selfhost/tools/pnpm/bin/pnpm.mjs'
steps = [
    ('backend-install', [node, str(yarn), 'install', '--immutable', '--mode=skip-build'], ROOT),
    ('frontend-install', [node, str(pnpm), 'install', '--frozen-lockfile', '--ignore-scripts',
      '--config.manage-package-manager-versions=false', '--config.package-manager-strict=false'], ROOT / 'src/webui/FE'),
    ('backend-build', [node, str(ROOT / 'node_modules/vite/bin/vite.js'), 'build'], ROOT),
    ('frontend-build', [node, str(ROOT / 'src/webui/FE/node_modules/vite/bin/vite.js'), 'build'], ROOT / 'src/webui/FE'),
    ('unit-tests', [node, str(ROOT / 'node_modules/vitest/vitest.mjs'), 'run', '--config', 'vitest.config.ts'], ROOT),
]
report = {'version': MANIFEST['fork_version'], 'node': version, 'steps': [], 'runtime_tested': False,
          'server_modified': False}
try:
    for name, command, cwd in steps:
        log = ROOT / 'selfhost' / (name + '.log')
        with log.open('w', encoding='utf-8') as output:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
        report['steps'].append({'name': name, 'exit_code': result.returncode})
        print(f'{name}: exit {result.returncode}', flush=True)
        result.check_returncode()
    shutil.copy2(ROOT / 'LICENSE', ROOT / 'dist/LICENSE')
    shutil.copy2(ROOT / 'README.selfhost.md', ROOT / 'dist/README.selfhost.md')
    report['status'] = 'build_and_tests_passed_runtime_unverified'
finally:
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    (ROOT / 'selfhost/build-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
