import re, json, glob, html, sys
base = sys.argv[1]
out = []
for f in glob.glob(f'{base}/posts/*.html'):
    s = open(f, errors='ignore').read()
    pid = int(re.search(r'p(\d+)\.html', f).group(1))
    title = html.unescape(re.search(r'<h1 class="entry-title[^"]*">(.*?)</h1>', s, re.S).group(1)).strip()
    date = re.search(r'<time[^>]*datetime="([^"]+)"', s).group(1)
    author = re.search(r'entry-author-name fn">([^<]+)<', s).group(1)
    body = re.search(r'<div class="entry-content clearfix">(.*?)</div> <!-- end \.entry-content -->', s, re.S).group(1)
    comments = []
    for c in re.finditer(r'<li class="([^"]*)" id="li-comment-(\d+)">\s*<div id="comment-\2"[^>]*>(.*?)<!-- end #comment-\2 -->', s, re.S):
        cls, cid, cb = c.groups()
        if 'pingback' in cls or 'trackback' in cls: continue
        a = re.search(r'<span class="fn">(.*?)</span>', cb, re.S)
        t = re.search(r'datetime="([^"]+)"', cb)
        txt = re.search(r'<div class="comment-content">(.*?)</div>', cb, re.S)
        comments.append({'id': cid, 'depth': int(re.search(r'depth-(\d)', cls).group(1)),
                         'author': re.sub('<[^>]+>', '', a.group(1)).strip() if a else None,
                         'date': t.group(1) if t else None, 'html': txt.group(1).strip() if txt else None})
    pings = len(re.findall(r'<li class="[^"]*(?:pingback|trackback)', s))
    media = sorted(set(re.findall(r'(?:src|href)="(https?://hhogh\.no/wp-content/uploads/[^"]+)"', body)))
    out.append(dict(pings=pings, id=pid, title=title, date=date, author=author, body=body, comments=comments, media=media))
out.sort(key=lambda p: p['date'])
json.dump(out, open(f'{base}/posts.json', 'w'), ensure_ascii=False, indent=1)
for p in out:
    print(p['id'], p['date'][:10], p['author'], '|', p['title'], '| media', len(p['media']), '| comments', [(c['author'], c['depth']) for c in p['comments']], 'pings', p['pings'])
