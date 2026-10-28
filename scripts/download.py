import json, re, subprocess, os, sys, time
base = sys.argv[1]
posts = json.load(open(f'{base}/posts.json'))
featured = {4: 'BeerLabel_Batch01-200x180.jpg', 8: 'BeerLabel_Batch02-200x180.jpg', 10: 'BeerLabel_Batch03-200x180.jpg',
            13: 'BeerLabel_Batch04-200x180.jpg', 73: 'malt-200x180.jpg', 170: 'label-200x180.jpeg', 141: 'dragons_death-200x180.jpeg'}
fdir = {4: '2014/09', 8: '2014/09', 10: '2014/09', 13: '2014/09', 73: '2014/12', 170: '2016/04', 141: '2015/11'}
urls = set()
for p in posts:
    for m in p['media']: urls.add(m.split('?')[0])
for k, v in featured.items(): urls.add(f'http://hhogh.no/wp-content/uploads/{fdir[k]}/{v}')
def orig(u): return re.sub(r'-\d+x\d+(\.\w+)$', r'\1', u)
want = {}
for u in urls: want.setdefault(orig(u), set()).add(u)
result = {}
for o, variants in sorted(want.items()):
    cands = [o] + sorted(variants - {o}, key=lambda v: -int((re.search(r'-(\d+)x\d+\.', v) or [0, 0])[1]))
    rel = o.split('/uploads/')[1]
    dest = f'{base}/media/{rel}'
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    got = None
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        got = 'cached'; cands = []
    for c in cands:
      for attempt in range(6):
        time.sleep(4)
        r = subprocess.run(['curl', '-sL', '-m', '120', '-o', dest, '-w', '%{http_code} %{content_type}', f'https://web.archive.org/web/2018id_/{c}'], capture_output=True, text=True)
        code, _, ctype = r.stdout.partition(' ')
        if code in ('000', '429', '503', '502'):
            time.sleep(30 * (attempt + 1)); continue
        break
      if code == '200' and 'html' not in ctype and os.path.getsize(dest) > 500:
          got = c; break
    if not got and os.path.exists(dest): os.remove(dest)
    result[o] = {'got': got, 'file': rel if got else None, 'variants': sorted(variants)}
    print('OK ' if got else 'MISS', o.split('/uploads/')[1], '<-', got.split('/')[-1] if got else code, flush=True)
json.dump(result, open(f'{base}/media.json', 'w'), indent=1)
