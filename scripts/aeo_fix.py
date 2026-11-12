"""One-time AEO pass over the static WFH pages (11/11/26), driven by the Position audit
(positionstrategygroup.com/audit/90c76246-...). Safe to re-run: every insert checks for itself first.

What it does, per page:
  favicon links, Open Graph + Twitter tags, sameAs/logo/url on every Westport Family Homes Organization node,
  titles cut to 70 characters or fewer, two meta descriptions cut to 170 or fewer, a footer "Guides" row
  (gives every page 10+ internal links), CSS cache-bust, homepage WebSite/WebPage/FAQPage schema,
  Insights index schema + one lead paragraph, BreadcrumbList where an article had none, llms.txt, sitemap lastmod.

Run from the site root:  python3 scripts/aeo_fix.py
New articles from the scheduled publisher do NOT get this automatically: copy the head block pattern from any
patched article (favicon, og:*, Organization sameAs) and the footer guides row into the staged index.html.
"""
import json, os, re, html as H, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://www.westportfamilyhomes.com'
TODAY = datetime.date.today().isoformat()
CSS_V = '31'
SAME_AS = [
    'https://www.houzz.com/pro/westportfamilyhomes',
    'https://www.houzz.com/professionals/westport-family-homes-pfvwus-pf~315943358',
]
JOSH_SAME_AS = [
    'https://joshpopkin.com/',
    'https://positionstrategygroup.com/',
    'https://www.amazon.com/Play-Offense-Customers-features-edge/dp/B0H6YDD539',
    'https://checkthescoreboard.com/',
    'https://www.linkedin.com/in/joshpaulpopkin/',
]
LOGO = SITE + '/assets/images/icons/logo-full.webp'
ORG_ID = SITE + '/#organization'
SITE_ID = SITE + '/#website'

FAVICON = ('<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />\n'
           '<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png" />\n'
           '<link rel="apple-touch-icon" href="/apple-touch-icon.png" />\n')

# Pages and the titles they get (None = keep). Every title must be 15-70 characters.
ARTICLES = {
    'insights/how-to-choose-the-best-home-builder-in-westport-connecticut.html':
        ('How to Choose a Home Builder in Westport, CT | Westport Family Homes', 'Choosing a Westport Builder'),
    'insights/what-to-know-before-building-a-custom-home-in-westport-connecticut/index.html':
        ('What to Know Before Building in Westport, CT | Westport Family Homes', 'Before You Build'),
    'insights/moving-to-connecticut-and-building-a-custom-home/index.html':
        ('Moving to CT and Building a Custom Home | Westport Family Homes', 'Moving to Connecticut'),
    'insights/family-floor-plans-in-westport-connecticut-what-to-look-for/index.html':
        ('Family Floor Plans: What to Look For | Westport Family Homes', 'Family Floor Plans'),
    'insights/how-to-design-a-floor-plan-for-your-family/index.html':
        (None, 'Designing a Floor Plan'),
    'insights/public-and-private-spaces-in-a-custom-home/index.html':
        ('Public and Private Spaces in a Custom Home | Westport Family Homes', 'Public and Private Spaces'),
    'insights/foundation-walls-interior-wall-layout/index.html':
        ('Why Foundation Walls Matter in a New Home | Westport Family Homes', 'Foundation Walls'),
    'insights/inside-5-baldwin-place-a-family-centered-floor-plan-in-westport-connecticut/index.html':
        ('Inside 5 Baldwin Place: A Family Floor Plan | Westport Family Homes', 'Inside 5 Baldwin Place'),
    'insights/5-baldwin-place-a-westport-home-designed-to-grow-with-you/index.html':
        ('A Westport Home Designed to Grow With You | Westport Family Homes', 'A Home Designed to Grow'),
    'insights/ben-stiller-stew-leonards-westport-ct/index.html':
        ("Ben Stiller at Stew Leonard's | Westport Family Homes", 'Life in Westport'),
    'insights/josh-popkin-westport-family-homes-website-rebrand/index.html':
        ('Josh Popkin Helps Rebrand Westport Family Homes', None),
    'insights/josh-popkin-westport-family-homes-website-rebuild-client-project/index.html':
        ('Josh Popkin: Westport Family Homes Website Rebuild', None),
    'insights/josh-popkin-rebuilt-westport-family-homes-website-and-brand/index.html':
        ("How Josh Popkin Rebuilt Westport Family Homes' Brand", None),
}
DESCRIPTIONS = {
    'index.html': 'Westport Family Homes has designed and built award-winning, energy-efficient homes in Fairfield County, Connecticut, for 18 years. 5 Baldwin Place is ready now.',
    'insights/inside-5-baldwin-place-a-family-centered-floor-plan-in-westport-connecticut/index.html':
        'A room-by-room look at 5 Baldwin Place in Westport, Connecticut, and how its floor plan handles togetherness, privacy, storage, flexibility and indoor-outdoor living.',
}


def url_of(path):
    if path == 'index.html':
        return SITE + '/'
    if path.endswith('/index.html'):
        return SITE + '/' + path[:-len('index.html')]
    return SITE + '/' + path


def guides_row(current):
    links = []
    for p, (_, label) in ARTICLES.items():
        if not label:
            continue
        href = url_of(p)[len(SITE):]
        links.append(f'        <a href="{href}">{label}</a>')
    return ('    <nav class="site-footer__guides" aria-label="Guides from Westport Family Homes">\n'
            '      <h3>Guides</h3>\n'
            '      <div class="site-footer__guides-list">\n' + '\n'.join(links) + '\n'
            '      </div>\n'
            '    </nav>\n\n')


def org_fix(node):
    """Give every Westport Family Homes organization node the same identity fields."""
    if isinstance(node, list):
        for x in node:
            org_fix(x)
        return
    if not isinstance(node, dict):
        return
    t = node.get('@type')
    types = t if isinstance(t, list) else [t]
    if any(x in ('Organization', 'HomeAndConstructionBusiness') for x in types) and node.get('name') == 'Westport Family Homes':
        node.setdefault('url', SITE + '/')
        if 'logo' not in node:
            node['logo'] = LOGO
        node['sameAs'] = SAME_AS
    # Josh's own entity, as joshpopkin.com declares it, and Position's logo (Josh Popkin articles)
    if 'Person' in types and node.get('name') == 'Josh Popkin':
        node['sameAs'] = JOSH_SAME_AS
    if 'Organization' in types and node.get('name') == 'Position Strategy Group':
        node.setdefault('logo', 'https://positionstrategygroup.com/favicon-192.png')
    for v in node.values():
        if isinstance(v, (dict, list)):
            org_fix(v)


def fix_jsonld(doc):
    def rep(m):
        raw = m.group(2)
        try:
            data = json.loads(raw)
        except ValueError:
            return m.group(0)
        org_fix(data)
        return m.group(1) + '\n' + json.dumps(data, indent=2, ensure_ascii=False) + '\n' + m.group(3)
    return re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', rep, doc, flags=re.S)


def ld_block(data):
    return '<script type="application/ld+json">\n' + json.dumps(data, indent=2, ensure_ascii=False) + '\n</script>\n'


def meta(doc, name):
    m = re.search(r'<meta name="%s" content="([^"]*)"' % name, doc)
    return H.unescape(m.group(1)) if m else ''


def set_title(doc, title):
    return re.sub(r'<title>.*?</title>', '<title>' + H.escape(title, quote=False) + '</title>', doc, count=1, flags=re.S)


def set_desc(doc, desc):
    return re.sub(r'<meta name="description" content="[^"]*"', '<meta name="description" content="' + H.escape(desc) + '"', doc, count=1)


def og_block(doc, url, kind, image):
    title = H.unescape(re.search(r'<title>(.*?)</title>', doc, re.S).group(1))
    desc = meta(doc, 'description')
    e = lambda s: H.escape(s)
    return ('<!-- aeo:og -->\n'
            f'<meta property="og:type" content="{kind}" />\n'
            f'<meta property="og:site_name" content="Westport Family Homes" />\n'
            f'<meta property="og:title" content="{e(title)}" />\n'
            f'<meta property="og:description" content="{e(desc)}" />\n'
            f'<meta property="og:url" content="{url}" />\n'
            f'<meta property="og:image" content="{image}" />\n'
            '<meta name="twitter:card" content="summary_large_image" />\n')


def first_ld_image(doc):
    m = re.search(r'"image":\s*"([^"]+)"', doc)
    if m:
        return m.group(1)
    m = re.search(r'"image":\s*\{[^}]*"url":\s*"([^"]+)"', doc)
    return m.group(1) if m else SITE + '/assets/images/hero/hero-main.webp'


def faq_from_page(doc):
    qs = []
    for m in re.finditer(r'<button class="acc-item__trigger">\s*<span>(.*?)</span>.*?<div class="acc-item__panel">\s*<p>(.*?)</p>', doc, re.S):
        q = H.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        a = H.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        a = re.sub(r'\s+', ' ', a)
        if q.endswith('?'):
            qs.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}})
    return qs


def patch_common(path, doc, kind, image):
    url = url_of(path)
    if path in ARTICLES and ARTICLES[path][0]:
        doc = set_title(doc, ARTICLES[path][0])
    if path in DESCRIPTIONS:
        doc = set_desc(doc, DESCRIPTIONS[path])
    doc = doc.replace('styles.css?v=30', 'styles.css?v=' + CSS_V)
    doc = fix_jsonld(doc)
    if 'rel="icon"' not in doc:
        doc = doc.replace('<link rel="canonical"', FAVICON + '<link rel="canonical"', 1)
    doc = re.sub(r'<!-- aeo:og -->\n(?:<meta (?:property|name)="(?:og|twitter):[^>]*>\n)+', '', doc)
    doc = doc.replace('<link rel="canonical"', og_block(doc, url, kind, image) + '<link rel="canonical"', 1)
    if 'site-footer__guides' not in doc and 'foot__guides' not in doc:
        anchor = '    <div class="site-footer__houzz-row">' if 'site-footer__houzz-row' in doc else '    <div class="site-footer__bottom">'
        assert anchor in doc, path
        doc = doc.replace(anchor, guides_row(path) + anchor, 1)
    return doc


def patch_home(doc):
    # @id on the business node so the page graph can point at it, plus the owner as a named person
    def rep(m):
        data = json.loads(m.group(2))
        if isinstance(data, dict) and data.get('@type') == 'HomeAndConstructionBusiness':
            data = dict([('@context', data['@context']), ('@type', data['@type']), ('@id', ORG_ID)] + [(k, v) for k, v in data.items() if k not in ('@context', '@type', '@id')])
            data['founder'] = {
                '@type': 'Person',
                'name': 'David Popkin',
                'jobTitle': 'Owner & Builder',
                'hasCredential': {'@type': 'EducationalOccupationalCredential', 'name': 'LEED Certified professional'},
                'alumniOf': [{'@type': 'CollegeOrUniversity', 'name': 'Brandeis University'},
                             {'@type': 'CollegeOrUniversity', 'name': 'Boston University'}],
                'knowsAbout': ['Custom home construction', 'Energy-efficient home design'],
            }
            data['award'] = 'Four HOBI Awards, Home Building Industry Association of Connecticut'
        return m.group(1) + '\n' + json.dumps(data, indent=2, ensure_ascii=False) + '\n' + m.group(3)
    doc = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', rep, doc, count=1, flags=re.S)
    if '"@type": "WebSite"' not in doc:
        title = H.unescape(re.search(r'<title>(.*?)</title>', doc, re.S).group(1))
        graph = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', '@id': SITE_ID, 'name': 'Westport Family Homes', 'url': SITE + '/', 'publisher': {'@id': ORG_ID}},
            {'@type': 'WebPage', '@id': SITE + '/#webpage', 'url': SITE + '/', 'name': title, 'description': meta(doc, 'description'),
             'isPartOf': {'@id': SITE_ID}, 'about': {'@id': ORG_ID}, 'publisher': {'@id': ORG_ID},
             'primaryImageOfPage': SITE + '/assets/images/hero/hero-main.webp', 'dateModified': TODAY},
            {'@type': 'FAQPage', '@id': SITE + '/#faq', 'url': SITE + '/', 'mainEntity': faq_from_page(doc)},
        ]}
        assert len(graph['@graph'][2]['mainEntity']) == 4, 'expected the 4 visible homepage FAQs'
        doc = doc.replace('</head>', ld_block(graph) + '</head>', 1)
    return doc


INSIGHTS_LEAD = ('<p class="insights__lead reveal-fade">Every guide here comes from 18 years of building homes in Westport: '
                 'how to pick a builder, how to plan a floor plan around your family, what to settle before the '
                 'foundation is poured, and what everyday life in town is like.</p>')


def patch_insights_index(doc):
    if 'insights__lead' not in doc:
        doc = doc.replace('<h2 class="reveal-fade">From Our Team to You</h2>',
                          '<h2 class="reveal-fade">From Our Team to You</h2>\n      ' + INSIGHTS_LEAD, 1)
    if 'application/ld+json' not in doc:
        cards = re.findall(r'<a class="insight-card[^"]*" href="([^"]+)">.*?<h3>(.*?)</h3>', doc, re.S)
        graph = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'Organization', '@id': ORG_ID, 'name': 'Westport Family Homes', 'url': SITE + '/', 'logo': LOGO, 'sameAs': SAME_AS},
            {'@type': 'WebSite', '@id': SITE_ID, 'name': 'Westport Family Homes', 'url': SITE + '/', 'publisher': {'@id': ORG_ID}},
            {'@type': 'CollectionPage', '@id': SITE + '/insights/#webpage', 'url': SITE + '/insights/', 'name': 'Insights | Westport Family Homes',
             'description': meta(doc, 'description'), 'isPartOf': {'@id': SITE_ID}, 'publisher': {'@id': ORG_ID}, 'dateModified': TODAY,
             'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                 {'@type': 'ListItem', 'position': i + 1, 'url': SITE + href, 'name': H.unescape(re.sub(r'<[^>]+>', '', t)).strip()}
                 for i, (href, t) in enumerate(cards)]}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Insights', 'item': SITE + '/insights/'}]},
        ]}
        doc = doc.replace('</head>', ld_block(graph) + '</head>', 1)
    return doc


def add_breadcrumb(path, doc):
    if 'BreadcrumbList' in doc:
        return doc
    h = re.search(r'"headline":\s*"([^"]+)"', doc).group(1)
    data = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Insights', 'item': SITE + '/insights/'},
        {'@type': 'ListItem', 'position': 3, 'name': h, 'item': url_of(path)}]}
    return doc.replace('</head>', ld_block(data) + '</head>', 1)


CSS = '''
/* footer guides row (aeo pass 11/11/26) */
.site-footer__guides {
  max-width: var(--container);
  margin: 0 auto;
  padding: 0 var(--gutter) 40px;
  text-align: center;
}
.site-footer__guides h3 {
  font-family: var(--font-body);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--gold-light);
  font-weight: 600;
  margin-bottom: 14px;
}
.site-footer__guides-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px 26px;
}
.site-footer__guides-list a {
  font-size: 0.88rem;
  color: rgba(250,246,239,0.78);
  text-decoration: none;
  transition: color 0.3s var(--ease-out);
}
.site-footer__guides-list a:hover { color: var(--gold-light); }
.insights__lead { color: var(--ink-soft); font-size: 1.02rem; line-height: 1.65; margin-top: 18px; }
'''


def llms_txt():
    lines = [
        '# Westport Family Homes', '',
        '> Westport Family Homes designs and builds new-construction homes in Westport and Fairfield County, Connecticut. '
        'Owner and builder David Popkin has lived in Westport for more than 30 years and has been building homes there for 18 years. '
        'The company has won four HOBI Awards from the Home Building Industry Association of Connecticut. '
        'Its current home for sale is 5 Baldwin Place: 2.3 acres, 6 bedrooms, a saltwater pool, room for a tennis or pickleball court, and an accessory dwelling unit.', '',
        '## Contact', '',
        '- Owner and builder: David Popkin, WestportFHLLC@gmail.com, 203-856-7678',
        '- Real estate broker: Lori Popkin, Coldwell Banker, lori.popkin@cbmoves.com, 203-984-7677', '',
        '## Pages', '',
        f'- [Home]({SITE}/): award-winning homes, portfolio, owner background and FAQ',
        f'- [5 Baldwin Place]({SITE}/5baldwinplace/): the current new-construction home, room by room',
        f'- [Insights]({SITE}/insights/): guides on building and buying a new home in Westport', '',
        '## Guides', '',
    ]
    for p in ARTICLES:
        doc = open(os.path.join(ROOT, p), encoding='utf-8').read()
        h1 = re.search(r'"headline":\s*"([^"]+)"', doc)
        lines.append(f'- [{h1.group(1) if h1 else p}]({url_of(p)}): {meta(doc, "description")}')
    lines += ['', '## Profiles', '', f'- [Houzz]({SAME_AS[1]})', '']
    return '\n'.join(lines)


def main():
    pages = ['index.html', 'insights/index.html'] + list(ARTICLES)
    for p in pages:
        f = os.path.join(ROOT, p)
        doc = open(f, encoding='utf-8').read()
        if p == 'index.html':
            doc = patch_home(doc)
            doc = patch_common(p, doc, 'website', SITE + '/assets/images/hero/hero-main.webp')
        elif p == 'insights/index.html':
            doc = patch_insights_index(doc)
            doc = patch_common(p, doc, 'website', SITE + '/assets/images/homes/home-04-ridgewood-lane.webp')
        else:
            doc = add_breadcrumb(p, doc)
            doc = patch_common(p, doc, 'article', first_ld_image(doc))
        t = H.unescape(re.search(r'<title>(.*?)</title>', doc, re.S).group(1))
        d = meta(doc, 'description')
        assert 15 <= len(t) <= 70, (p, len(t), t)
        assert 50 <= len(d) <= 170, (p, len(d))
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
            json.loads(raw)
        open(f, 'w', encoding='utf-8').write(doc)
        print('ok', len(t), len(d), p)

    css = os.path.join(ROOT, 'css/styles.css')
    s = open(css, encoding='utf-8').read()
    if 'site-footer__guides' not in s and 'foot__guides' not in s:
        # before the first media query so the phone rules still apply after it
        i = s.index('@media (max-width: 1024px)')
        s = s[:i] + CSS.lstrip('\n') + '\n' + s[i:]
        open(css, 'w', encoding='utf-8').write(s)

    open(os.path.join(ROOT, 'llms.txt'), 'w', encoding='utf-8').write(llms_txt())

    sm = os.path.join(ROOT, 'sitemap.xml')
    x = open(sm, encoding='utf-8').read()
    for p in pages:
        loc = re.escape('<loc>' + url_of(p) + '</loc>')
        x = re.sub('(' + loc + r'\s*<lastmod>)[^<]+', r'\g<1>' + TODAY, x)
    open(sm, 'w', encoding='utf-8').write(x)


if __name__ == '__main__':
    main()
