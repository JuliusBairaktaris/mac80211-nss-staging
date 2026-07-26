#!/usr/bin/env python3
"""Export the staging history back to openwrt's patches/nss/ dirs.

Each commit's subject is its destination path under patches/nss/:
nss/subsys/<name>.patch, nss/ath11k/<name>.patch, or nss/mesh/<name>.patch.
Mesh patches get a sequential NNNN- prefix so their lexical order preserves
the commit order. Commit bodies become the patch headers. A commit whose
subject is not such a path is not a shippable patch and is skipped. Usage:
tools/export.py <openwrt-mac80211-patches-nss-dir>
"""
import subprocess, sys, os, shutil, re

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout

dest = sys.argv[1]
commits = sh('git', 'rev-list', '--reverse', 'HEAD').split()
patches = [c for c in commits[1:]
           if sh('git', 'log', '--format=%s', '-1', c).startswith('nss/')]

for sub in ('subsys', 'ath11k', 'mesh'):
    d = os.path.join(dest, sub)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)

n_mesh = 0
for c in patches:
    subject = sh('git', 'log', '--format=%s', '-1', c).strip()
    body = sh('git', 'log', '--format=%b', '-1', c).rstrip()
    m = re.match(r'nss/(subsys|ath11k|mesh)/(.+\.patch)$', subject)
    assert m, f"unparseable subject: {subject}"
    if m.group(1) == 'mesh':
        n_mesh += 1
        out = os.path.join(dest, 'mesh', f"{n_mesh:04d}-{m.group(2)}")
    else:
        out = os.path.join(dest, m.group(1), m.group(2))
    diff = sh('git', 'show', '--format=', '--no-color', c)
    with open(out, 'w') as f:
        if body:
            f.write(body + '\n\n')
        f.write(diff)
print(f"exported {len(patches)} patches ({n_mesh} mesh)")
