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


def page(title, desc, path, main, rel, image=None):
    """Contango-oppsettet fra originalen: header, innhold (grid_11), sidekolonne (grid_5), bunntekst.
    rel: prefiks for interne lenker ('' på rot, '../' i en post), så siden virker både på
    hhogh.no og på fenre.github.io/hhogh/. None = absolutte stier (404-siden)."""
    t = html.escape(f'{title} | {TITLE}' if title != TITLE else TITLE)
    og = f'\n<meta property="og:image" content="{SITE}{image}">' if image else ''
    out = f'''<!DOCTYPE html>
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
<link href="https://fonts.googleapis.com/css?family=Open+Sans%7CNixie+One&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/theme/960.css">
<link rel="stylesheet" href="/theme/contango.css">
<link rel="stylesheet" href="/theme/hhogh.css">
</head>
<body class="custom-background">
<div id="page" class="wrapper hfeed site">
  <header id="masthead" class="site-header">
    <div class="container_16 clearfix">
      <div class="grid_16">
        <div id="headimg">
          <div id="logo-text">
            <span class="site-name"><a href="/" rel="home">{TITLE}</a></span>
          </div>
        </div>
      </div>
    </div>
  </header>
  <div class="container_16 clearfix">
    <nav id="site-navigation" class="grid_16 main-navigation"><div class="menu clearfix"></div></nav>
  </div>
  <div id="content" class="site-content clearfix">
    <div class="container_16 clearfix">
      <div class="grid_11">
        <div id="primary" class="content-area">
          <main id="main" class="site-main">
{main}
          </main>
        </div>
      </div>
{SIDEBAR_HTML}
    </div>
  </div>
  <div class="container_16 containter_footer">
    <footer id="colophon" class="grid_16 site-footer">
      <div class="copyright clearfix">
        <div class="copyright_inside">&copy; 2014–2016 <a href="/">{TITLE}</a></div>
      </div>
      <div class="credit clearfix">
        <div class="credit_inside"><a href="https://github.com/fenre/hhogh">Hentet fra Internet Archive</a> &sdot; <a href="http://designorbital.com/contango/">Contango Theme</a> (GPLv3) &sdot; <a href="https://www.fsudmann.com/">fsudmann.com</a></div>
      </div>
    </footer>
  </div>
</div>
</body>
</html>
'''
    if rel is not None:
        out = out.replace('href="/', f'href="{rel}').replace('src="/', f'src="{rel}')
    return out


def date_block(iso, href):
    d = datetime.fromisoformat(iso)
    return (f'<time class="entry-date entry-time updated" datetime="{iso}"><a href="{href}" rel="bookmark">'
            f'<span class="entry-date-day">{d.day:02d}</span><span class="entry-date-month-year">{d.strftime("%b %Y")}</span></a></time>')


def meta_group(p, title, href, tag):
    return f'''  <div class="entry-meta-group clearfix">
    <div class="grid_2 alpha">
      {date_block(p['date'], href)}
    </div>
    <div class="grid_8 omega">
      <{tag} class="entry-title{' entry-title-single' if tag == 'h1' else ''}">{f'<a href="{href}" rel="bookmark">{html.escape(title)}</a>' if tag == 'h2' else html.escape(title)}</{tag}>
      <div class="entry-meta"><span class="entry-author author vcard">by <span class="entry-author-name fn">{html.escape(p['author'])}</span></span></div>
    </div>
  </div>
'''


def clean(p, slug, used):
    def local(u):
        f = have.get(orig(u))
        if not f:
            return None
        used.add(f)
        return f'/{slug}/media/{os.path.basename(f)}'

    b = p['body']
    b = re.sub(r'<span id="more-\d+"></span>', '<!--more-->', b)
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

THUMB = {**FEATURED, 33: '2014/10/blacksanta.png', 89: '2015/01/goldenstandard2.jpg',
         128: '2015/04/Skjermbilde-2015-05-06-kl.-20.45.26.png', 146: '2016/01/goldenstandard20.jpg'}
built = []
for p in posts:
    slug, used = SLUG[p['id']], set()
    body = clean(p, slug, used)
    title = html.unescape(p['title']).replace('  ', ' ')
    thumb = THUMB.get(p['id']) if THUMB.get(p['id']) in have.values() else None
    if thumb:
        used.add(thumb)
        thumb = f'/{slug}/media/{os.path.basename(thumb)}'
    label = FEATURED.get(p['id']) if FEATURED.get(p['id']) in have.values() else None
    if label:
        body = f'<p><img src="/{slug}/media/{os.path.basename(label)}" alt="" class="hhogh-label"></p>\n' + body
    built.append((p, slug, title, body, thumb, used))

newest = list(reversed(built))
recent_posts = ''.join(f'            <li><a href="/{b[1]}/">{html.escape(b[2])}</a></li>\n' for b in newest[:5])
all_comments = sorted(((c, b) for b in built for c in b[0]['comments']), key=lambda x: x[0]['date'], reverse=True)
recent_comments = ''.join(
    f'            <li class="recentcomments"><span class="comment-author-link">{html.escape(c["author"])}</span> on <a href="/{b[1]}/#comment-{c.get("id", "")}">{html.escape(b[2])}</a></li>\n'
    for c, b in all_comments)
SIDEBAR_HTML = f'''      <div id="secondary" class="grid_5 widget-area">
        <div id="sidebar">
          <aside class="widget widget_recent_entries clearfix"><div class="widget-wrap widget-inside">
            <h3 class="widget-title">Recent Posts</h3>
            <ul>
{recent_posts}            </ul>
          </div></aside>
          <aside class="widget widget_recent_comments clearfix"><div class="widget-wrap widget-inside">
            <h3 class="widget-title">Recent Comments</h3>
            <ul id="recentcomments">
{recent_comments}            </ul>
          </div></aside>
        </div>
      </div>'''


for i, (p, slug, title, body, thumb, used) in enumerate(built):
    os.makedirs(f'{root}/{slug}/media', exist_ok=True)
    for f in used:
        shutil.copy(f'{src}/media/{f}', f'{root}/{slug}/media/')
    if not used:
        os.rmdir(f'{root}/{slug}/media')
    full = re.sub(r'<p[^>]*>\s*</p>\s*', '', body.replace('<!--more-->', ''))
    comments = ''
    if p['comments']:
        n = len(p['comments'])
        items, open_reply = '', False
        for c in p['comments']:
            li = f'''<li class="comment depth-{c['depth']}" id="li-comment-{c.get('id', '')}">
  <div id="comment-{c.get('id', '')}" class="comment">
    <div class="comment-meta"><div class="comment-author vcard"><span class="fn">{html.escape(c['author'])}</span> on <span>{datetime.fromisoformat(c['date']).strftime('%d/%m/%Y at %H:%M')}</span> <span class="says">said:</span></div></div>
    <div class="comment-content">{c['html']}</div>
  </div>
'''
            if c['depth'] > 1 and not open_reply:
                items = items[:-len('</li>\n')] + '<ul class="children">\n' + li + '</li>\n'
                open_reply = True
            elif c['depth'] > 1:
                items = items[:-len('</li>\n')] + li + '</li>\n'
            else:
                if open_reply:
                    items = items[:-len('</li>\n')] + '</ul>\n</li>\n'
                    open_reply = False
                items += li + '</li>\n'
        if open_reply:
            items = items[:-len('</li>\n')] + '</ul>\n</li>\n'
        word = 'thought' if n == 1 else 'thoughts'
        comments = f'''<div id="comments" class="grid_inside">
  <h3 id="comments-title">{n} {word} on &ldquo;<span>{html.escape(title)}</span>&rdquo;</h3>
  <ol class="commentlist">
{items}  </ol>
</div>
'''
    prev = built[i - 1] if i > 0 else None
    nxt = built[i + 1] if i + 1 < len(built) else None
    pager = '<nav class="hhogh-pager">'
    pager += f'<a href="/{prev[1]}/">&larr; {html.escape(prev[2])}</a>' if prev else '<span></span>'
    pager += f'<a href="/{nxt[1]}/">{html.escape(nxt[2])} &rarr;</a>' if nxt else ''
    pager += '</nav>\n'
    art = f'''<article id="post-{p['id']}" class="post type-post status-publish format-standard hentry">
{meta_group(p, title, f'/{slug}/', 'h1')}  <div class="entry-content clearfix">
{full}
  </div>
</article>
{pager}{comments}'''
    open(f'{root}/{slug}/index.html', 'w').write(page(title, excerpt(full, 155), f'/{slug}/', art, '../', thumb))

cards = []
for p, slug, title, body, thumb, used in newest:
    # Forsiden viser teksten fram til WordPress-markøren «more», som originalen
    intro, _, more = body.partition('<!--more-->')
    intro = re.sub(r'<p><img [^>]*class="hhogh-label"></p>\n', '', intro)
    intro = re.sub(r'<p[^>]*>\s*$', '', intro.rstrip())
    if len(re.findall(r'<p[ >]', intro)) > intro.count('</p>'):
        intro += '</p>'
    fi = f'<div class="entry-featured-image"><a href="/{slug}/"><img width="200" height="180" src="{thumb}" class="entry-image" alt=""></a></div>' if thumb else ''
    rm = f'<p> <a href="/{slug}/" class="more-link"><span>Read More &rarr;</span></a></p>' if more else ''
    cards.append(f'''<article id="post-{p['id']}" class="post type-post status-publish format-standard hentry{' has-post-thumbnail' if thumb else ''}">
{meta_group(p, title, f'/{slug}/', 'h2')}  <div class="entry-content clearfix">
    {fi}{intro.replace('<!--more-->', '')}
{rm}
  </div>
</article>
''')

# Gamle WordPress-lenker (hhogh.no/?p=13) sendes videre til riktig brygg
redirect = 'var m = location.search.match(/[?&]p=(\\d+)/), map = ' + json.dumps({str(k): f'{v}/' for k, v in SLUG.items()}) + ';\n  if (m && map[m[1]]) location.replace(map[m[1]]);'
index = f'''<script>
  {redirect}
</script>
{''.join(cards)}'''
open(f'{root}/index.html', 'w').write(page(TITLE, 'Bryggeloggen til Hafrsfjord Hornmusik og Haandbryggerlaug, 13 brygg fra 2014 til 2016.', '/', index, ''))
open(f'{root}/404.html', 'w').write(page('Fant ikke siden', 'Siden finnes ikke.', '/404.html',
    '<article class="post hentry"><h1 class="entry-title">Fant ikke siden</h1><div class="entry-content"><p><a href="/">Til alle brygg</a></p></div></article>', None))
urls = ['/'] + [f'/{b[1]}/' for b in built]
open(f'{root}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + ''.join(f'  <url><loc>{SITE}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
print(f'{len(built)} poster bygget')
