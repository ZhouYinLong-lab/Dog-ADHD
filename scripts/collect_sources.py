from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, json

ROOT = Path(__file__).resolve().parent.parent / 'research' / 'source-snapshots'
ROOT.mkdir(parents=True, exist_ok=True)
REPOS = {
    'ponytail': ('DietrichGebert/ponytail', ['skills/ponytail/SKILL.md', 'benchmarks/results/2026-10-07-agentic.md', 'hooks/hooks.json', 'INSTALL.md']),
    'adhd': ('ayghri/i-have-adhd', ['skills/i-have-adhd/SKILL.md', 'evals/rubric.md', 'evals/README.md', 'hooks/hooks.json', 'INSTALL.md']),
    'humanizer': ('blader/humanizer', ['SKILL.md']),
    'stop-slop': ('hardikpandya/stop-slop', ['SKILL.md']),
    'anti-sycophancy': ('talhapythoneer/anti-sycophancy-prompt', ['prompt.md']),
    'caveman': ('JuliusBrussee/caveman', ['skills/caveman/SKILL.md']),
}

def get(url):
    with urlopen(Request(url, headers={'User-Agent':'Research-source-audit'}), timeout=25) as r:
        return r.read()

def collect(item):
    label, (repo, files) = item
    access_date = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    record = {'project':label, 'repository':repo, 'access_date':access_date, 'files':[]}
    try:
        commit = json.loads(get(f'https://api.github.com/repos/{repo}/commits/main'))['sha']
        record['commit'] = commit
    except Exception as e:
        commit = 'main'
        record['revision_error'] = str(e)
    for file in files:
        url = f'https://raw.githubusercontent.com/{repo}/{commit}/{file}'
        target = ROOT / (label + '__' + file.replace('/','__'))
        try:
            data = get(url)
            target.write_bytes(data)
            record['files'].append({'path':file, 'url':url, 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)})
        except Exception as e:
            record['files'].append({'path':file, 'url':url, 'error':str(e)})
    return record

with ThreadPoolExecutor(max_workers=6) as pool:
    records = list(pool.map(collect, REPOS.items()))
manifest_text = json.dumps(records, ensure_ascii=False, indent=2)
(ROOT / 'manifest.json').write_text(manifest_text, encoding='utf-8')
(ROOT.parent / 'source-manifest.json').write_text(manifest_text, encoding='utf-8')
for r in records:
    print(r['project'], r.get('commit', 'unresolved'), [(f['path'], f.get('bytes', f.get('error'))) for f in r['files']])
