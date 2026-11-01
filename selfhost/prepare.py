"""Fetch pinned upstream artifacts without executing PMHQ or contacting QQ."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / 'selfhost/manifest.json').read_text(encoding='utf-8'))
MAX_ARCHIVE = 50 * 1024 * 1024
MAX_UNPACKED = 100 * 1024 * 1024

def fetch(key):
    spec = MANIFEST['artifacts'][key]
    cache = ROOT / 'selfhost/cache' / spec['cache_file']
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        data = cache.read_bytes()
    else:
        req = urllib.request.Request(spec['url'], headers={'User-Agent': 'LLBot-legacy-selfhost-build/1'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read(MAX_ARCHIVE + 1)
    if len(data) > MAX_ARCHIVE or hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError(f'{key}: artifact size or SHA256 mismatch; refusing extraction')
    cache.write_bytes(data)
    return data

def extract_checked(data, destination, expected_members=None):
    # Validate the complete archive before writing any member.
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        if sum(m.size for m in members) > MAX_UNPACKED:
            raise ValueError('archive exceeds extraction limit')
        files = []
        seen = set()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or '\\' in member.name or ':' in member.name:
                raise ValueError('unsafe archive path')
            if not path.parts or path.parts[0] != 'package' or member.name in seen:
                raise ValueError('unexpected or duplicate archive member')
            seen.add(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError('links and special files are not accepted')
            if expected_members is not None and member.name not in expected_members:
                continue
            blob = archive.extractfile(member).read()
            if expected_members is not None and hashlib.sha256(blob).hexdigest() != expected_members[member.name]:
                raise ValueError('native member SHA256 mismatch')
            files.append((Path(*path.parts[1:]), blob, member.mode))
        if expected_members is not None and set(expected_members) != {m.name for m in members if m.name in expected_members}:
            raise ValueError('required native member missing')
        for relative, blob, mode in files:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            # Do not follow a pre-existing output symlink.
            if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != destination.parent):
                raise ValueError('output symlink is not accepted')
            target.write_bytes(blob)
            if os.name != 'nt':
                target.chmod(mode & 0o755)

def prepare_tools():
    for key in ('yarn', 'pnpm'):
        extract_checked(fetch(key), ROOT / 'selfhost/tools' / key)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pmhq', action='store_true', help='also obtain unchanged official PMHQ 7.3.2 Linux x64 binaries')
    args = parser.parse_args()
    prepare_tools()
    if args.pmhq:
        spec = MANIFEST['artifacts']['pmhq_linux_x64']
        extract_checked(fetch('pmhq_linux_x64'), ROOT / 'selfhost/native/linux-x64', spec['members'])
    print(json.dumps({'tools_ready': True, 'official_legacy_pmhq_prepared': args.pmhq, 'runtime_tested': False}))
