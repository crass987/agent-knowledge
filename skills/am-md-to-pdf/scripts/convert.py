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

def main():
    ap = argparse.ArgumentParser(description='Convert Markdown to a polished dark-theme PDF.')
    ap.add_argument('input'); ap.add_argument('output')
    ap.add_argument('--logo', default=None)
    ap.add_argument('--title', default=None)
    ap.add_argument('--chrome', default=CHROME_DEFAULT)
    ap.add_argument('--keep-html', action='store_true')
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        sys.exit('input not found: %s' % args.input)
    if not os.path.isfile(args.chrome):
        sys.exit('chrome not found: %s (pass --chrome PATH)' % args.chrome)
    if args.logo and not os.path.isfile(args.logo):
        sys.exit('logo not found: %s' % args.logo)

    md = open(args.input, encoding='utf-8').read()
    logo_uri = 'file://%s' % os.path.abspath(args.logo) if args.logo else None
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
    if not args.keep_html:
        shutil.rmtree(os.path.dirname(html_path), ignore_errors=True)

if __name__ == '__main__':
    main()
