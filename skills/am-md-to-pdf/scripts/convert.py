#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""am-md-to-pdf — convert a Markdown file to a polished dark-theme PDF.

The HTML is GENERATED FROM THE .md programmatically. Never hand-transcribe the
markdown into HTML by eye — that is exactly the failure mode this tool exists to
prevent (text drifts from the source within a few edits).

Usage:
  convert.py <input.md> <output.pdf> [--logo PATH] [--title TEXT] [--chrome PATH] [--keep-html]

  --logo PATH    Logo image/SVG shown top-left on every page (page 1: logo+title,
                 inner pages: logo only). Omit for no logo.
  --title TEXT   Document title in the page-1 header (default: first H1 in the .md).
  --chrome PATH  Path to a Chrome/Chromium binary
                 (default: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome).
  --keep-html    Keep the intermediate .html next to the .pdf (default: temp, deleted).

Pipeline: .md -> styled HTML (this script) -> headless Chrome --print-to-pdf.
Verify afterwards with:  pdftotext <out.pdf> - | grep '<a key phrase from the .md>'
"""
import argparse, re, html, subprocess, sys, os, tempfile, shutil
try:
    import fitz  # PyMuPDF — repeating header mark + page numbers (post-process overlay)
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

CHROME_DEFAULT = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

CSS = """
:root{--bg:#03122e;--panel:#0c1830;--border:#243553;--text:#eaf0fb;--body:#cfd6e4;--mut:#9aa4bd;--dim:#6b7896;
--accent:#009cfe;--cyan:#2ebbff;--green:#43f0a8;--red:#ff5b5b;--code:#1b2a4a;
--font:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--mono:'SF Mono',ui-monospace,'JetBrains Mono',Menlo,Consolas,monospace}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--body);font-family:var(--font);line-height:1.6;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
body{padding:40px 52px;max-width:820px;margin:0 auto}
.head{display:flex;align-items:center;gap:16px;margin-bottom:4px}
.head .ttl{color:var(--text);font-size:18px;font-weight:800;letter-spacing:-.2px;line-height:1.2}
.logo{height:34px;width:auto}
.accent-bar{height:3px;width:100%;background:linear-gradient(90deg,var(--accent),rgba(0,156,254,0));border-radius:2px;margin:8px 0 6px}
.page{break-before:page;page-break-before:always;padding-top:32px}
h1{color:var(--text);font-size:24px;font-weight:800;margin:4px 0 2px;letter-spacing:-.3px;line-height:1.24}
h2{color:var(--text);font-size:18px;font-weight:700;margin:14px 0 9px;padding-left:13px;border-left:4px solid var(--accent);line-height:1.3;break-after:avoid;page-break-after:avoid}
h3{color:var(--text);font-size:15px;font-weight:700;margin:12px 0 6px}
p{margin:0 0 10px;font-size:13.5px;orphans:2;widows:2}
strong{color:var(--text);font-weight:600} em{color:var(--cyan);font-style:italic}
a{color:var(--cyan);text-decoration:none}
code{font-family:var(--mono);font-size:12px;background:var(--code);color:#cfe6ff;padding:1px 5px;border-radius:4px}
pre{background:var(--code);border:1px solid var(--border);border-radius:8px;padding:12px 14px;overflow-x:auto;margin:10px 0;break-inside:avoid}
pre code{background:none;padding:0;color:#cfe6ff;font-size:11.5px;line-height:1.5}
ul,ol{margin:8px 0;padding-left:22px}
li{font-size:13.5px;margin:4px 0;break-inside:avoid}
ul li::marker{color:var(--accent)}
blockquote{background:rgba(0,156,254,.07);border:1px solid rgba(0,156,254,.32);border-left:4px solid var(--accent);
  border-radius:8px;padding:10px 15px;margin:10px 0;color:#dcefff;font-size:13px;break-inside:avoid}
.cols{display:flex;gap:14px;margin:8px 0}
.card{background:var(--panel);border:1px solid var(--border);border-radius:11px;padding:11px 14px;break-inside:avoid;flex:1}
.card h3{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:7px;display:flex;align-items:center;gap:8px}
.card.build h3{color:var(--green)}.card.nobuild h3{color:var(--cyan)}
.card h3 .d{width:8px;height:8px;border-radius:50%}
.card.build h3 .d{background:var(--green)}.card.nobuild h3 .d{background:var(--cyan)}
.card ul{list-style:none;padding:0;margin:0}
.card li{padding:3px 0 3px 20px;position:relative;font-size:11.5px;line-height:1.35;break-inside:avoid}
.card.build li::before{content:"";position:absolute;left:1px;top:9px;width:9px;height:5px;border-left:2px solid var(--green);border-bottom:2px solid var(--green);transform:rotate(-45deg)}
.card.nobuild li::before{content:"";position:absolute;left:3px;top:8px;width:8px;height:8px;border:1.5px solid var(--cyan);border-radius:50%}
.callout{background:rgba(67,240,168,.07);border:1px solid rgba(67,240,168,.3);border-left:4px solid var(--green);border-radius:8px;padding:10px 15px;margin:10px 0;font-size:12.8px;color:#dff7ec;break-inside:avoid}
hr{border:none;border-top:1px solid var(--border);margin:14px 0}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:11px;break-inside:avoid}
th{background:var(--panel);color:var(--accent);font-weight:700;text-transform:uppercase;font-size:9px;letter-spacing:.4px;text-align:left;padding:7px 8px;border:1px solid var(--border)}
td{padding:7px 8px;border:1px solid var(--border);color:var(--body);vertical-align:top;line-height:1.35}
td strong{color:var(--text)}
tr:nth-child(even) td{background:rgba(13,26,48,.55)}
.foot{margin-top:22px;padding-top:11px;border-top:1px solid var(--border);color:var(--dim);font-size:10px}
@page{size:A4;margin:12mm}
"""

def inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

def trim(p):
    p = list(p)
    while p and not p[0].strip(): p.pop(0)
    while p and not p[-1].strip(): p.pop()
    return p

def convert(blk):
    """Convert a list of md lines (one page) to HTML."""
    out = []; i = 0; n = len(blk)
    lst = None  # 'ul' | 'ol' | None
    def cl():
        nonlocal lst
        if lst: out.append('</%s>' % lst); lst = None
    while i < n:
        l = blk[i]; s = l.strip()
        if not s:
            cl(); i += 1; continue
        # code fence
        if s.startswith('```'):
            cl(); lang = s[3:].strip(); i += 1; code = []
            while i < n and not blk[i].strip().startswith('```'):
                code.append(html.escape(blk[i])); i += 1
            i += 1  # skip closing fence
            out.append('<pre><code>%s</code></pre>' % '\n'.join(code)); continue
        # headings
        if s.startswith('### '):
            cl(); out.append('<h3>%s</h3>' % inline(s[4:])); i += 1; continue
        if s.startswith('## '):
            cl(); out.append('<h2>%s</h2>' % inline(s[3:])); i += 1; continue
        if s.startswith('# '):
            cl(); out.append('<h1>%s</h1>' % inline(s[2:])); i += 1; continue
        # hr
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', s):
            cl(); out.append('<hr>'); i += 1; continue
        # blockquote
        if s.startswith('> '):
            cl(); out.append('<blockquote>%s</blockquote>' % inline(s[2:].strip())); i += 1; continue
        # table
        if s.startswith('|'):
            cl(); rows = []
            while i < n and blk[i].strip().startswith('|'): rows.append(blk[i].strip()); i += 1
            cells = lambda r: [c.strip() for c in r.strip('|').split('|')]
            hdr = cells(rows[0]); data = [cells(r) for r in rows[2:]] if len(rows) > 2 else []
            t = ['<table>', '<tr>' + ''.join('<th>%s</th>' % inline(c) for c in hdr) + '</tr>']
            for r in data: t.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
            t.append('</table>'); out.append('\n'.join(t)); continue
        # card: **label:** followed by a list (two consecutive → side-by-side cols)
        mb = re.match(r'^\*\*(.+?)\*\*[:]?\s*(.*)$', s)
        if mb and i + 1 < n and re.match(r'^[-*]\s', blk[i + 1].strip()):
            cl()
            def card_for(idx):
                mm = re.match(r'^\*\*(.+?)\*\*[:]?\s*(.*)$', blk[idx].strip())
                label = mm.group(1).rstrip(':')
                kind = 'nobuild' if re.search(r'\b(НЕ|не|not|no)\b', label) else 'build'
                items = []; idx = idx + 1
                while idx < n and re.match(r'^[-*]\s', blk[idx].strip()):
                    items.append(re.sub(r'^[-*]\s+', '', blk[idx].strip())); idx += 1
                ch = '<div class="card %s"><h3><span class="d"></span>%s</h3><ul>%s</ul></div>' % (
                    kind, inline(label), ''.join('<li>%s</li>' % inline(it) for it in items))
                return ch, idx
            c1, j = card_for(i)
            nxt = blk[j].strip() if j < n else ''
            if re.match(r'^\*\*.+\*\*[:]?\s*$', nxt) and j + 1 < n and re.match(r'^[-*]\s', blk[j + 1].strip()):
                c2, j = card_for(j)
                out.append('<div class="cols">%s%s</div>' % (c1, c2))
            else:
                out.append(c1)
            i = j; continue
        # callout: **summary-term ...** standalone paragraph
        if re.match(r'^\*\*(Гипотеза|Где помогает|Где может|Вход|Итог|Вывод|Резюме|Результат|Итого|Заключение|NB|Summary)', s):
            cl(); out.append('<div class="callout">%s</div>' % inline(s)); i += 1; continue
        # unordered list
        if re.match(r'^[-*]\s', s):
            if lst != 'ul': cl(); out.append('<ul>'); lst = 'ul'
            out.append('<li>%s</li>' % inline(re.sub(r'^[-*]\s+', '', s))); i += 1; continue
        # ordered list
        if re.match(r'^\d+\.\s', s):
            if lst != 'ol': cl(); out.append('<ol>'); lst = 'ol'
            out.append('<li>%s</li>' % inline(re.sub(r'^\d+\.\s+', '', s))); i += 1; continue
        # paragraph
        cl(); out.append('<p>%s</p>' % inline(s)); i += 1
    cl(); return '\n'.join(out)

def build_html(md, logo, title):
    lines = md.split('\n')
    h1 = title or ''
    # page boundaries: before each '## ' except the first; and before a '> ' blockquote
    # that is followed by a '## ' (keeps a Q with its answer).
    h2_count = 0
    boundary = [False] * len(lines)
    for idx, l in enumerate(lines):
        s = l.strip()
        if s.startswith('## '):
            h2_count += 1
            p = idx - 1
            while p >= 0 and not lines[p].strip():
                p -= 1
            prev_is_quote = p >= 0 and lines[p].strip().startswith('> ')
            if h2_count > 1 and not prev_is_quote:
                boundary[idx] = True
        elif s.startswith('> '):
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith('## '):
                boundary[idx] = True
    pages = []; cur = []
    for idx, l in enumerate(lines):
        s = l.strip()
        if s.startswith('# '):
            if not h1: h1 = s[2:].strip()
            continue
        if boundary[idx] and cur:
            pages.append(cur); cur = []
        cur.append(l)
    if cur:
        pages.append(cur)
    pages = [trim(p) for p in pages if trim(p)]
    if not h1:
        h1 = 'Document'
    blocks = [convert(p) for p in pages]
    logo_tag = '<img class="logo" src="%s" alt="logo">' % logo if logo else ''
    parts = []
    for idx, b in enumerate(blocks):
        if idx == 0:
            head = '<div class="head">%s%s</div><div class="accent-bar"></div>' % (
                logo_tag, '<div class="ttl">%s</div>' % inline(h1) if logo or title else '<h1>%s</h1>' % inline(h1))
            parts.append(head + '\n' + b)
        else:
            head = '<div class="page"><div class="head">%s</div><div class="accent-bar"></div>' % logo_tag
            parts.append(head + '\n' + b + '\n</div>')
    body = '\n'.join(parts)
    return '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>%s</title>' \
           '<link rel="preconnect" href="https://fonts.googleapis.com">' \
           '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">' \
           '<style>%s</style></head><body>\n%s\n</body></html>' % (html.escape(h1), CSS, body)

# --- Design-system mode (--design PATH) -------------------------------------
# When a DESIGN.md is supplied, tokens parsed from its YAML front matter drive
# the CSS (:root vars); the layout follows the prose (an ops-console dispatch:
# modular groups divided by hairlines, a one-time masthead, no repeating header,
# no drop cap, no stat tiles). See DESIGN.md. Without --design, the original
# "one page per ##" mode above is used (roadmap/strategy).

def parse_design(path):
    """Minimal parser for the DESIGN.md front matter we emit. Returns a dict of
    token groups: {colors, typography, rounded, spacing, components, meta}."""
    text = open(path, encoding='utf-8').read()
    m = re.search(r'^---\s*\n(.*?)\n---\s', text, re.S)
    if not m:
        return {}
    design = {'colors': {}, 'typography': {}, 'rounded': {}, 'spacing': {}, 'components': {}, 'meta': {}}
    section = sub = None
    for line in m.group(1).split('\n'):
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        kv = re.match(r'^([A-Za-z0-9_-]+)\s*:\s*(.*)$', line.strip())
        if not kv:
            continue
        key = kv.group(1); val = kv.group(2).strip().strip('"')
        if indent == 0:
            if val == '':
                section = key; sub = None
            else:
                design['meta'][key] = val
        elif indent == 2:
            if section in ('colors', 'rounded', 'spacing'):
                design[section][key] = val
            elif section in ('typography', 'components'):
                if val == '':
                    sub = key; design[section][sub] = {}
                else:
                    design[section].setdefault(sub, {})[key] = val
        elif indent >= 4:
            if section in ('typography', 'components') and sub:
                design[section].setdefault(sub, {})[key] = val
    return design

def build_css_dispatch(d):
    """Build the dispatch CSS from DESIGN.md tokens (:root vars) + static rules."""
    c = d.get('colors', {}); t = d.get('typography', {}); r = d.get('rounded', {}); sp = d.get('spacing', {})
    sans_stack = "'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
    mono_stack = "'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace"
    def fsize(role, default):
        return t.get(role, {}).get('fontSize', default)
    root = ['--ff-sans:%s' % sans_stack, '--ff-mono:%s' % mono_stack,
            '--fs-title:%s' % fsize('dispatch-title', '22px'),
            '--fs-flag:%s' % fsize('section-flag', '11px'),
            '--fs-feature:%s' % fsize('feature-head', '15px'),
            '--fs-body:%s' % fsize('body', '13px'),
            '--fs-mono:%s' % fsize('mono', '12px'),
            '--fs-meta:%s' % fsize('meta-caps', '10px')]
    for k, v in c.items():
        root.append('--%s:%s' % (k, v))
    for k, v in r.items():
        root.append('--r-%s:%s' % (k, v))
    for k, v in sp.items():
        root.append('--sp-%s:%s' % (k, v))
    rules = """
@page{size:A4;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--console,#03122e);color:var(--ink-body,#cfd6e4);
  font-family:var(--ff-sans);line-height:1.55;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body.dispatch{padding:0;max-width:none;margin:0}
.sheet{padding:var(--sp-page-top,49px) var(--sp-page-x,56px) var(--sp-page-bottom,49px);
  -webkit-box-decoration-break:clone;box-decoration-break:clone}
.masthead{display:flex;align-items:center;gap:14px;margin-bottom:3px}
.masthead .logo{height:26px;width:auto}
.masthead .ver{font-size:var(--fs-meta);font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-dim,#9aa4bd);margin-left:auto}
.rule{height:1px;background:var(--hairline,#243553);margin:9px 0 14px}
h1.doc-title{color:var(--ink,#eaf0fb);font-size:var(--fs-title);font-weight:800;line-height:1.2;
  letter-spacing:-.01em;margin:0 0 14px}
.group{break-inside:avoid;page-break-inside:avoid}
.group h1{font-size:var(--fs-flag);font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--primary,#009cfe);padding-top:14px;border-top:1px solid var(--hairline,#243553);
  margin:0 0 10px;break-after:avoid}
h2{color:var(--ink,#eaf0fb);font-size:var(--fs-feature);font-weight:700;line-height:1.3;
  margin:14px 0 6px;padding-left:10px;border-left:3px solid var(--primary,#009cfe);break-after:avoid}
h3{font-size:var(--fs-meta);font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--primary,#009cfe);margin:10px 0 4px}
p{font-size:var(--fs-body);line-height:1.55;margin:0 0 8px;color:var(--ink-body,#cfd6e4);orphans:2;widows:2}
strong{color:var(--ink,#eaf0fb);font-weight:600}
code{font-family:var(--ff-mono);font-size:var(--fs-mono);background:var(--code-well,#1b2a4a);
  color:var(--code-ink,#cfe6ff);padding:1px 5px;border-radius:var(--r-token,4px)}
pre{background:var(--code-well,#1b2a4a);border:1px solid var(--hairline,#243553);
  border-radius:var(--r-token,4px);padding:10px 12px;margin:8px 0;break-inside:avoid}
pre code{background:none;padding:0}
ul,ol{margin:5px 0;padding-left:18px}
li{font-size:var(--fs-body);margin:3px 0;color:var(--ink-body,#cfd6e4);break-inside:avoid}
ul li::marker{color:var(--primary,#009cfe)}
hr{border:none;border-top:1px solid var(--hairline,#243553);margin:12px 0}
a{color:var(--primary,#009cfe);text-decoration:none}
blockquote{border-left:3px solid var(--hairline,#243553);padding:4px 12px;color:var(--ink-dim,#9aa4bd);
  margin:8px 0;font-size:var(--fs-body)}
table{width:100%;border-collapse:collapse;margin:8px 0;font-size:var(--fs-mono);break-inside:avoid}
th{background:var(--panel,#0c1830);color:var(--primary,#009cfe);text-transform:uppercase;font-size:9px;
  letter-spacing:.1em;text-align:left;padding:6px;border:1px solid var(--hairline,#243553)}
td{padding:6px;border:1px solid var(--hairline,#243553);color:var(--ink-body,#cfd6e4)}
"""
    return ':root{%s}\n%s' % (';'.join(root), rules)

def build_html_dispatch(md, logo, title, d):
    lines = md.split('\n')
    h1 = title or ''
    # section boundaries: each '#' after the first opens a module group.
    h1_count = 0
    boundary = [False] * len(lines)
    for idx, l in enumerate(lines):
        s = l.strip()
        if s.startswith('# ') and not s.startswith('## '):
            h1_count += 1
            if h1_count > 1:
                boundary[idx] = True
    pages = []; cur = []; h1_seen = False
    for idx, l in enumerate(lines):
        s = l.strip()
        if s.startswith('# ') and not s.startswith('## '):
            if not h1_seen:
                h1_seen = True
                if not h1:
                    h1 = s[2:].strip()
                continue  # the first '#' becomes the masthead title
        if boundary[idx] and cur:
            pages.append(cur); cur = []
        cur.append(l)
    if cur:
        pages.append(cur)
    pages = [trim(p) for p in pages if trim(p)]
    if not h1:
        h1 = 'Document'
    blocks = [convert(p) for p in pages]
    logo_tag = '<img class="logo" src="%s" alt="logo">' % logo if logo else ''
    vm = re.search(r'(v\.?\d[\d.]*)', h1, re.I)
    ver = vm.group(1) if vm else ''
    ver_flag = 'ЧТО НОВОГО В РЕЛИЗЕ' + ('  ·  ' + ver if ver else '')
    parts = []
    for idx, b in enumerate(blocks):
        if idx == 0:
            masthead = ('<div class="masthead">%s<div class="ver">%s</div></div>'
                        '<div class="rule"></div><h1 class="doc-title">%s</h1>'
                        % (logo_tag, html.escape(ver_flag), inline(h1)))
            parts.append(masthead + '\n' + b)
        else:
            parts.append('<div class="group">\n' + b + '\n</div>')
    body = '<div class="sheet">\n' + '\n'.join(parts) + '\n</div>'
    css = build_css_dispatch(d)
    return '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>%s</title>' \
           '<link rel="preconnect" href="https://fonts.googleapis.com">' \
           '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">' \
           '<style>%s</style></head><body class="dispatch">\n%s\n</body></html>' % (html.escape(h1), css, body)

def post_process_pdf(pdf_path, header_logo=None, num_color=(0.604, 0.643, 0.741)):
    """Overlay repeating chrome that headless Chrome --print-to-pdf can't produce:
    a small wordless header mark on every page EXCEPT the first, and a centered
    'n / N' page number in the footer on every page when the doc has >1 page.
    Uses PyMuPDF (fitz). No-op if fitz isn't installed."""
    if not _HAS_FITZ:
        print('note: PyMuPDF (fitz) not installed — skipping header mark / page numbers')
        return
    doc = fitz.open(pdf_path)
    n = len(doc)
    # Rasterize the mark once (SVG -> alpha pixmap, crisp).
    pix = None
    if header_logo and os.path.isfile(header_logo):
        try:
            sdoc = fitz.open(stream=open(header_logo, 'rb').read(), filetype='svg')
            pix = sdoc[0].get_pixmap(matrix=fitz.Matrix(8, 8), alpha=True)
        except Exception as e:
            print('note: could not rasterize header logo: %s' % e)
            pix = None
    for i, page in enumerate(doc):
        r = page.rect
        if pix is not None and i > 0:           # header mark on inner pages only
            h = 16.0                             # ~5.6mm tall
            w = h * pix.width / pix.height
            x = r.x1 - 42.5 - w                  # 15mm right rail
            y = 12.0                             # ~4.2mm from top — sits above the section-flag hairline
            page.insert_image(fitz.Rect(x, y, x + w, y + h), pixmap=pix)
        if n > 1:                                # page number, centered footer
            num = '%d / %d' % (i + 1, n)
            tw = fitz.get_text_length(num, fontname='helv', fontsize=8)
            page.insert_text(((r.x0 + r.x1) / 2 - tw / 2, r.y1 - 20), num,
                             fontname='helv', fontsize=8, color=num_color)
    tmp = pdf_path + '.tmp'
    doc.save(tmp, deflate=True)
    doc.close()
    os.replace(tmp, pdf_path)

def main():
    ap = argparse.ArgumentParser(description='Convert Markdown to a polished dark-theme PDF.')
    ap.add_argument('input'); ap.add_argument('output')
    ap.add_argument('--logo', default=None)
    ap.add_argument('--title', default=None)
    ap.add_argument('--chrome', default=CHROME_DEFAULT)
    ap.add_argument('--keep-html', action='store_true')
    ap.add_argument('--design', default=None,
                    help='path to a DESIGN.md: render from its tokens (ops-console dispatch layout)')
    ap.add_argument('--header-logo', default=None,
                    help='path to a wordless mark SVG, placed in the header of every inner page')
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        sys.exit('input not found: %s' % args.input)
    if not os.path.isfile(args.chrome):
        sys.exit('chrome not found: %s (pass --chrome PATH)' % args.chrome)
    if args.logo and not os.path.isfile(args.logo):
        sys.exit('logo not found: %s' % args.logo)
    if args.design and not os.path.isfile(args.design):
        sys.exit('DESIGN.md not found: %s' % args.design)
    if args.header_logo and not os.path.isfile(args.header_logo):
        sys.exit('header logo not found: %s' % args.header_logo)

    md = open(args.input, encoding='utf-8').read()
    logo_uri = 'file://%s' % os.path.abspath(args.logo) if args.logo else None
    if args.design:
        d = parse_design(args.design)
        if not d or not d.get('colors'):
            sys.exit('could not parse DESIGN.md tokens: %s' % args.design)
        html_doc = build_html_dispatch(md, logo_uri, args.title, d)
    else:
        html_doc = build_html(md, logo_uri, args.title)

    out_dir = os.path.dirname(os.path.abspath(args.output)) or '.'
    if args.keep_html:
        html_path = os.path.abspath(os.path.splitext(args.output)[0] + '.html')
    else:
        html_path = os.path.join(tempfile.mkdtemp(), 'doc.html')
    open(html_path, 'w', encoding='utf-8').write(html_doc)

    cmd = [args.chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
           '--allow-file-access-from-files', '--print-to-pdf=%s' % os.path.abspath(args.output),
           'file://%s' % html_path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.isfile(args.output):
        sys.exit('PDF not created.\nstderr:\n' + r.stderr[-1000:])
    print('PDF created: %s' % args.output)
    if args.design or args.header_logo:
        post_process_pdf(args.output, header_logo=args.header_logo)
    if not args.keep_html:
        shutil.rmtree(os.path.dirname(html_path), ignore_errors=True)

if __name__ == '__main__':
    main()
