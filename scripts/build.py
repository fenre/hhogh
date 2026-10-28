"""Bygger det statiske nettstedet fra Wayback-uttrekket.

Bruk: python3 scripts/build.py <uttrekk-mappe>
Uttrekk-mappa lages av extract.py (posts.json) og download.py (media.json + media/).
"""
import html, json, os, re, shutil, sys
from datetime import datetime

src, root = sys.argv[1], os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
posts = json.load(open(f'{src}/posts.json'))
media = json.load(open(f'{src}/media.json'))
TITLE = 'Hafrsfjord Hornmusik og Haandbryggerlaug'
SITE = 'https://hhogh.no'
SLUG = {4: 'batch-01-sloppy-joe', 8: 'batch-02-single-hop-amarillo', 10: 'batch-03-hattrick', 13: 'batch-04-amber-christmas',
        33: 'batch-05-black-santa', 73: 'batch-06-american-brown-ale', 89: 'batch-07-golden-standard', 116: 'batch-08-black-ipanema',
        128: 'batch-09-dragonstout', 141: 'batch-10-dragons-death', 146: 'batch-11-cor-jesu', 170: 'batch-12-corpus-christi',
        183: 'batch-13-crimond'}
# Fremhevet bilde (etikett) for poster der det ikke står i selve teksten
FEATURED = {4: '2014/09/BeerLabel_Batch01.jpg', 8: '2014/09/BeerLabel_Batch02.jpg', 10: '2014/09/BeerLabel_Batch03.jpg',
            13: '2014/09/BeerLabel_Batch04.jpg', 73: '2014/12/malt.jpg', 141: '2015/11/dragons_death.jpeg', 170: '2016/04/label.jpeg'}
UP = 'http://hhogh.no/wp-content/uploads/'
MONTHS = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember']
have = {o: m['file'] for o, m in media.items() if m['file']}
posts.sort(key=lambda p: p['date'])


def orig(u):
    return re.sub(r'-\d+x\d+(\.\w+)$', r'\1', u.split('?')[0])


def nodate(iso):
    d = datetime.fromisoformat(iso)
    return f'{d.day}. {MONTHS[d.month - 1]} {d.year}'


def page(title, desc, path, body, image=None):
    t = html.escape(f'{title} — {TITLE}' if title != TITLE else TITLE)
    og = f'\n  <meta property="og:image" content="{SITE}{image}">' if image else ''
    return f'''<!DOCTYPE html>
<html lang="nb">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{t}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{SITE}{path}">
  <meta property="og:site_name" content="{TITLE}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:url" content="{SITE}{path}">{og}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Roboto:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
</head>
<body class="theme-blogger">
  <header class="site-header">
    <div class="site-header__inner">
    <a class="site-title" href="/">{TITLE}</a>
    <div class="site-header__right">
      <nav class="site-nav" aria-label="Primary"><a href="/">Alle brygg</a> · <a href="https://www.fsudmann.com/">fsudmann.com</a></nav>
    </div>
    </div>
  </header>
  <main class="site-main" id="main">
{body}
  </main>
</body>
</html>
'''


def clean(p, slug, used):
    def local(u):
        f = have.get(orig(u))
        if not f:
            return None
        used.add(f)
        return f'/{slug}/media/{os.path.basename(f)}'

    b = p['body']
    b = re.sub(r'<p><span id="more-\d+"></span></p>\s*', '', b)
    b = re.sub(r'<!--\[if lt IE 9\]>.*?<!\[endif\]-->', '', b, flags=re.S)
    b = re.sub(r'\s(?:srcset|sizes)="[^"]*"', '', b)

    def vid(m):
        s = local(re.search(r'src="([^"]+)"', m.group(0)).group(1))
        return f'<video class="hhogh-video" controls preload="metadata" src="{s}"></video>' if s else ''
    b = re.sub(r'<div[^>]*class="wp-video"[^>]*>.*?</video></div>', vid, b, flags=re.S)

    def img(m):
        tag = m.group(0)
        s = local(re.search(r'src="([^"]+)"', tag).group(1))
        if not s:
            return ''
        tag = re.sub(r'src="[^"]+"', f'src="{s}" loading="lazy"', tag)
        return re.sub(r'\s(?:width|height)="\d+"', '', tag)
    b = re.sub(r'<img[^>]*>', img, b)

    def link(m):
        href, inner = m.group(1), m.group(2)
        s = local(href)
        if s:
            return f'<a href="{s}">{inner}</a>'
        if '<img' in inner:
            return inner
        # filnavn som lenketekst til en fil som ikke ble reddet: fjern helt
        return '' if inner.startswith('http') or inner.strip() in href else re.sub('<[^>]+>', '', inner)
    b = re.sub(r'<a href="(' + re.escape(UP) + r'[^"]+)"[^>]*>(.*?)</a>', link, b, flags=re.S)
    b = re.sub(r'href="http://hhogh\.no/\?p=(\d+)"', lambda m: f'href="/{SLUG[int(m.group(1))]}/"', b)
    b = re.sub(r'<p>\s*(?:Oppskrift:\s*)?</p>|<div[^>]*>\s*</div>', '', b)
    return b.strip()


def excerpt(h, n=220):
    t = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', h))).strip()
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + ' …'


for d in os.listdir(root):
    if d.startswith('batch-'):
        shutil.rmtree(f'{root}/{d}')

cards, built = [], []
for i, p in enumerate(posts):
    slug, used = SLUG[p['id']], set()
    body = clean(p, slug, used)
    title = html.unescape(p['title']).replace('  ', ' ')
    label = FEATURED.get(p['id']) if FEATURED.get(p['id']) in have.values() else None
    if label:
        used.add(label)
        image = f'/{slug}/media/{os.path.basename(label)}'
        body = f'<p><img src="{image}" alt="" class="hhogh-label"></p>\n' + body
    else:
        m = re.search(r'<img[^>]*src="([^"]+)"', body)
        image = m.group(1) if m else None
    built.append((p, slug, title, body, image, used))

for i, (p, slug, title, body, image, used) in enumerate(built):
    os.makedirs(f'{root}/{slug}/media', exist_ok=True)
    for f in used:
        shutil.copy(f'{src}/media/{f}', f'{root}/{slug}/media/')
    if not used:
        os.rmdir(f'{root}/{slug}/media')
    comments = ''
    if p['comments']:
        cs = ''.join(
            f'''    <div class="hhogh-comment{' hhogh-comment--reply' if c['depth'] > 1 else ''}">
      <p class="hhogh-comment__meta"><strong>{html.escape(c['author'])}</strong> · <time datetime="{c['date']}">{nodate(c['date'])}</time></p>
      {c['html']}
    </div>
''' for c in p['comments'])
        comments = f'  <section class="hhogh-comments">\n    <h2>Kommentarer</h2>\n{cs}  </section>\n'
    prev = built[i - 1] if i > 0 else None
    nxt = built[i + 1] if i + 1 < len(built) else None
    pager = '  <nav class="hhogh-pager" aria-label="Andre brygg">\n'
    pager += f'    <a href="/{prev[1]}/">← {html.escape(prev[2])}</a>\n' if prev else '    <span></span>\n'
    pager += f'    <a href="/{nxt[1]}/">{html.escape(nxt[2])} →</a>\n' if nxt else ''
    pager += '  </nav>\n'
    art = f'''<article class="post blogger-post">
  <header class="post__header">
    <h1 class="post__title">{html.escape(title)}</h1>
    <p class="post__meta"><time datetime="{p['date']}">{nodate(p['date'])}</time> · av {html.escape(p['author'])}</p>
  </header>
  <div class="post__body">
{body}
  </div>
{comments}{pager}</article>'''
    open(f'{root}/{slug}/index.html', 'w').write(page(title, excerpt(body, 155), f'/{slug}/', art, image))
    thumb = f'''    <a class="post-card__thumb-link" href="/{slug}/" tabindex="-1" aria-hidden="true">
      <img class="post-card__thumb" src="{image}" alt="" width="320" height="200" loading="lazy" decoding="async">
    </a>
''' if image else ''
    cards.append(f'''  <article class="post-card{' post-card--with-thumb' if image else ''}">
{thumb}    <div class="post-card__body">
      <h2 class="post-card__title"><a href="/{slug}/">{html.escape(title)}</a></h2>
      <p class="post-card__meta"><time datetime="{p['date']}">{nodate(p['date'])}</time> · av {html.escape(p['author'])}</p>
      <p class="post-card__snippet">{html.escape(excerpt(body))}</p>
    </div>
  </article>
''')

# Gamle WordPress-lenker (hhogh.no/?p=13) sendes videre til riktig brygg
redirect = 'var m = location.search.match(/[?&]p=(\\d+)/), map = ' + json.dumps({str(k): f'/{v}/' for k, v in SLUG.items()}) + ';\n  if (m && map[m[1]]) location.replace(map[m[1]]);'
index = f'''<script>
  {redirect}
</script>
<section class="blogger-feed">
  <h1 class="blogger-feed__heading">{TITLE}</h1>
  <p class="hhogh-intro">Fra 2014 til 2016 brygget Fredrik, Steffen, Leif, Gaute og Jonas øl sammen, og skrev en kort post om hvert brygg. Her er alle de 13 postene, hentet tilbake fra Internet Archive.</p>
{''.join(reversed(cards))}</section>'''
open(f'{root}/index.html', 'w').write(page(TITLE, 'Bryggeloggen til Hafrsfjord Hornmusik og Haandbryggerlaug, 13 brygg fra 2014 til 2016.', '/', index))
open(f'{root}/404.html', 'w').write(page('Fant ikke siden', 'Siden finnes ikke.', '/404.html',
    '<section class="blogger-feed"><h1 class="blogger-feed__heading">Fant ikke siden</h1><p><a href="/">Til alle brygg</a></p></section>'))
urls = ['/'] + [f'/{b[1]}/' for b in built]
open(f'{root}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + ''.join(f'  <url><loc>{SITE}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
print(f'{len(built)} poster bygget')
