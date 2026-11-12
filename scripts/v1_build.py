#!/usr/bin/env python3
"""Put the v1 Traditional redesign (11/12/26) on the live site.

Run from the site root:  python3 scripts/v1_build.py

What it does
- Homepage and /insights/: body from the approved v1 preview, <head> kept from the live page
  (titles, descriptions, canonicals, Open Graph, JSON-LD stay exactly as the 11/11 AEO pass left them).
- Every article in /insights/: <head> kept from the live page, body rebuilt in the v1 article template
  from the article's own content (headline, date, hero photo, text, figures).
- Copies v1 CSS/JS to /css/site.css and /js/site.js and the 5 Baldwin photos it uses to /assets/images/v1/.
- Adds the site-traffic tag to every page it writes.
It never touches /5baldwinplace/, the redirect pages, robots.txt, CNAME or the IndexNow key.
Idempotent: it reads the article content from the page itself, so it can run again after edits,
but the homepage and insights index come from the preview folder (V1 below).
"""
import html as H
import os
import re
import shutil
import sys

SITE = 'https://www.westportfamilyhomes.com'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V1 = os.path.expanduser('~/Desktop/Claude/WFH Redesign 2026-11/v1-traditional')
SHARED = os.path.expanduser('~/Desktop/Claude/WFH Redesign 2026-11/shared/img')
VER = '20261112'
# pre-redesign copies of the pages this script rewrites (kept outside the served site)
ORIG = os.path.expanduser('~/Desktop/Claude/WFH Redesign 2026-11/live-originals')

TRACK = ("<!-- site-traffic --><script>(function(){try{if(localStorage.getItem('st_off'))return;var q=new URLSearchParams(location.search);"
         "var d=JSON.stringify({p:location.pathname,r:document.referrer,u:q.get('utm_source')||''});"
         "if(!navigator.sendBeacon||!navigator.sendBeacon('https://traffic.positionstrategygroup.com/__st?s=westportfamilyhomes.com',d))"
         "{fetch('https://traffic.positionstrategygroup.com/__st?s=westportfamilyhomes.com',{method:'POST',body:d,keepalive:true,mode:'no-cors'})}}catch(e){}})();</script>")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Jost:wght@400;500&display=swap">\n'
         f'<link rel="stylesheet" href="/css/site.css?v={VER}">\n')


def rd(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def wr(p, s):
    if os.path.dirname(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


# ---------- images ----------
def find_live(name):
    for d in ('assets/images/homes', 'assets/images/hero', 'assets/images/icons'):
        if os.path.exists(os.path.join(ROOT, d, name)):
            return '/' + d + '/' + name
    if os.path.exists(os.path.join(ROOT, name)):
        return '/' + name
    return None


copied = set()


def img_url(rel):
    """rel = path under shared/img (e.g. great-room-1600.webp, portfolio/x.webp, brand/x.png)."""
    base = os.path.basename(rel)
    if rel.startswith(('portfolio/', 'brand/')):
        hit = find_live(base)
        if hit:
            return hit
    dst = os.path.join(ROOT, 'assets/images/v1', rel)
    if rel not in copied:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(SHARED, rel), dst)
        copied.add(rel)
    return '/assets/images/v1/' + rel


def fix_body(s, depth_insights=False):
    s = re.sub(r'(?:\.\./)+shared/img/([^"\s,]+)', lambda m: img_url(m.group(1)), s)
    s = re.sub(r'(?:\.\./)*js/site\.js', f'/js/site.js?v={VER}', s)
    s = re.sub(r'href="(?:\.\./)*index\.html#', 'href="/#', s)
    s = re.sub(r'href="(?:\.\./)*index\.html"', 'href="/"', s)
    s = re.sub(r'href="(?:\.\./)+insights/', 'href="/insights/', s)
    if depth_insights:
        s = s.replace('href="../"', 'href="/insights/"')
    s = s.replace('href="insights/', 'href="/insights/')
    s = re.sub(r'href="https://www\.westportfamilyhomes\.com/', 'href="/', s)
    return s


def live_head(page_html):
    head = re.search(r'<head>(.*?)</head>', page_html, re.S).group(1)
    head = re.sub(r'\s*<link rel="preconnect"[^>]*>', '', head)
    head = re.sub(r'\s*<link[^>]+fonts\.googleapis\.com/css2[^>]*>', '', head)
    head = re.sub(r'\s*<link rel="stylesheet" href="/?css/styles\.css[^"]*"\s*/?>', '', head)
    head = re.sub(r'\s*<link rel="stylesheet" href="/css/site\.css[^"]*">', '', head)
    head = re.sub(r'\s*<meta name="robots" content="noindex"\s*/?>', '', head)
    head = head.replace("<script>document.documentElement.classList.add('js')</script>\n", '')
    vp = re.search(r'<meta name="viewport"[^>]*>\n?', head)
    ins = "<script>document.documentElement.classList.add('js')</script>\n" + FONTS
    head = head[:vp.end()] + ins + head[vp.end():] if vp else ins + head
    return '<head>' + head.rstrip() + '\n</head>'


def with_track(body):
    body = body.replace(TRACK, '')
    return body.replace('</body>', TRACK + '\n</body>')


def v1_body(path):
    s = rd(path)
    return s[s.index('<body'):s.index('</html>')]


# ---------- article cards (from the live insights index, which v1 rebuilt verbatim) ----------
def card_data():
    s = rd(os.path.join(V1, 'insights/index.html'))
    out = {}
    for m in re.finditer(r'<article class="(?:lead-)?card">(.*?)</article>', s, re.S):
        a = m.group(1)
        href = re.search(r'<h[23][^>]*><a href="([^"]+)"', a).group(1)
        slug = href.replace(SITE, '').rstrip('/').split('/')[-1]
        out[slug] = a
    return out


def chrome_parts():
    s = rd(os.path.join(V1, 'insights/5-baldwin-place-a-westport-home-designed-to-grow-with-you/index.html'))
    top = s[s.index('<body'):s.index('<main id="main">')]
    see = s[s.index('<section class="sec ground-parch" aria-labelledby="see-h">'):s.index('<section class="sec" aria-labelledby="related-h">')]
    foot = s[s.index('</main>') + len('</main>'):s.index('</html>')]
    return top, see, foot


def clean_article(inner):
    inner = re.sub(r'\s*class="reveal-[a-z]+"', '', inner)
    inner = re.sub(r'\s+reveal-[a-z]+(?=")', '', inner)
    inner = inner.replace('class="article-figure article-figure--portrait"', 'class="portrait"')
    inner = inner.replace(' class="article-figure"', '')
    inner = re.sub(r'<p>', '<p class="lead">', inner, count=1)
    inner = re.sub(r'href="https://www\.westportfamilyhomes\.com/', 'href="/', inner)
    # indent consistently inside .prose
    # anchor ids on subheadings (AEO: answer engines and the Position grader link to sections)
    used = set()
    def _id(m):
        txt = re.sub(r'<[^>]+>', '', m.group(2))
        slug = re.sub(r'[^a-z0-9]+', '-', H.unescape(txt).lower()).strip('-')[:60] or 'section'
        base, k = slug, 2
        while slug in used:
            slug, k = f'{base}-{k}', k + 1
        used.add(slug)
        return f'<h2{m.group(1)} id="{slug}">{m.group(2)}</h2>'
    inner = re.sub(r'<h2((?:(?!id=)[^>])*)>(.*?)</h2>', _id, inner, flags=re.S)
    lines = [ln.strip() for ln in inner.strip().splitlines() if ln.strip()]
    return '\n'.join('      ' + ln for ln in lines)


def build_article(path, s, slug, order, cards, top, see, foot):
    head = live_head(s)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1)
    h1 = re.sub(r'</?span[^>]*>', ' ', h1)
    h1 = re.sub(r'\s+', ' ', h1).strip()
    h1 = re.sub(r'</?em>', '', h1)  # the old hero italicised a line break, not a word
    metas = re.findall(r'<p class="article-meta[^"]*">(.*?)</p>', s, re.S)
    img = re.search(r'<img[^>]*class="hero__img"[^>]*>|<img[^>]*src="[^"]+"[^>]*class="hero__img[^"]*"[^>]*>', s).group(0)
    src = re.search(r'src="([^"]+)"', img).group(1)
    alt = re.search(r'alt="([^"]*)"', img).group(1)
    w = re.search(r'width="(\d+)"', img)
    hh = re.search(r'height="(\d+)"', img)
    dims = f' width="{w.group(1)}" height="{hh.group(1)}"' if w and hh else ''
    body = re.search(r'<article class="article-body">(.*?)</article>', s, re.S).group(1)
    cat = 'Insights'
    if slug in cards:
        lab = re.search(r'<span class="label">(.*?)</span>', cards[slug], re.S)
        if lab:
            cat = lab.group(1).split('&middot;')[0].strip()
    meta_html = ''.join(f'\n      <p class="a-meta">{m.strip()}</p>' for m in metas)
    # three related articles: the next three in the insights order
    i = order.index(slug) if slug in order else -1
    rel = [order[(i + k) % len(order)] for k in range(1, len(order)) if order[(i + k) % len(order)] != slug][:3]
    rel_html = '\n'.join('      <article class="card">' + cards[r] + '</article>' for r in rel if r in cards)
    main = f'''<main id="main">
<article>
  <header class="a-head">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/insights/">Insights</a><span aria-hidden="true">/</span><span>{cat}</span></nav>
      <h1>{h1}</h1>{meta_html}
    </div>
  </header>
  <div class="wrap a-hero">
    <img src="{src}" alt="{alt}"{dims} fetchpriority="high">
  </div>
  <div class="wrap">
    <div class="prose">
{clean_article(body)}
    </div>
  </div>
</article>

{see}<section class="sec" aria-labelledby="related-h">
  <div class="wrap">
    <div class="head">
      <div class="head__title">
        <span class="label">Insights</span>
        <h2 class="display" id="related-h">Further Reading</h2>
      </div>
      <div class="head__aside head__aside--link"><a class="more" href="/insights/"><span>All insights</span></a></div>
    </div>
    <div class="cards">
{rel_html}
    </div>
  </div>
</section>
</main>'''
    top_fixed = top.replace('<body class="page-solid">', '<body class="page-solid page-article">')
    out = '<!doctype html>\n<html lang="en">\n' + head + '\n' + fix_body(top_fixed + main + foot, depth_insights=True)
    out = with_track(out.rstrip() + '\n</html>\n')
    wr(path, out)
    return h1


def main():
    os.chdir(ROOT)
    css = rd(os.path.join(V1, 'css/site.css')) + rd(os.path.join(ROOT, 'scripts/v1_live_extra.css'))
    css = re.sub(r'url\((?:\.\./)+shared/img/([^)]+)\)', lambda m: 'url(' + img_url(m.group(1)) + ')', css)
    wr('css/site.css', css)
    js = rd(os.path.join(V1, 'js/site.js'))
    wr('js/site.js', js)

    # homepage
    live_home = rd('index.html') if '<!-- v1-live -->' not in rd('index.html') else rd(os.path.join(ORIG, 'index.html'))
    if '<!-- v1-live -->' not in rd('index.html'):
        wr(os.path.join(ORIG, 'index.html'), live_home)
    vhome = rd(os.path.join(V1, 'index.html'))
    html_tag = re.search(r'<html[^>]*>', vhome).group(0)
    body = fix_body(v1_body(os.path.join(V1, 'index.html')))
    # keep the old #spotlight and #top anchors working
    body = body.replace('<main id="main">', '<main id="main"><span id="top"></span>', 1)
    body = re.sub(r'(<section[^>]*id="peeks"[^>]*>)', r'\1<span id="spotlight"></span>', body, count=1)
    wr('index.html', with_track('<!doctype html>\n' + html_tag + '\n<!-- v1-live -->\n' + live_head(live_home) + '\n' + body + '</html>\n'))

    # insights index
    live_ins = rd('insights/index.html') if '<!-- v1-live -->' not in rd('insights/index.html') else rd(os.path.join(ORIG, 'insights__index.html'))
    if '<!-- v1-live -->' not in rd('insights/index.html'):
        wr(os.path.join(ORIG, 'insights__index.html'), live_ins)
    vins = rd(os.path.join(V1, 'insights/index.html'))
    body = fix_body(v1_body(os.path.join(V1, 'insights/index.html')), depth_insights=True)
    body = body.replace('<div class="cards all-cards">', '<div class="cards all-cards">\n      <!-- scheduled-cards -->', 1)
    wr('insights/index.html', with_track('<!doctype html>\n<html lang="en">\n<!-- v1-live -->\n' + live_head(live_ins) + '\n' + body + '</html>\n'))

    # articles
    cards = card_data()
    order = [re.search(r'<h[23][^>]*><a href="([^"]+)"', m.group(1)).group(1).replace(SITE, '').rstrip('/').split('/')[-1]
             for m in re.finditer(r'<article class="(?:lead-)?card">(.*?)</article>', vins, re.S)]
    top, see, foot = chrome_parts()
    done = []
    for p in sorted([os.path.join('insights', d, 'index.html') for d in os.listdir('insights')
                     if os.path.isfile(os.path.join('insights', d, 'index.html'))] +
                    [os.path.join('insights', f) for f in os.listdir('insights') if f.endswith('.html') and f != 'index.html']):
        orig = os.path.join(ORIG, p.replace('/', '__'))
        if os.path.exists(orig):
            s = rd(orig)
        else:
            s = rd(p)
            if 'http-equiv="refresh"' in s:
                continue
            wr(orig, s)
        slug = p.split('/')[-2] if p.endswith('/index.html') else os.path.basename(p)
        h = build_article(p, s, slug, order, cards, top, see, foot)
        done.append((slug, h))
    for d in done:
        print('article:', d[0])
    print('images copied:', len(copied))


if __name__ == '__main__':
    main()
