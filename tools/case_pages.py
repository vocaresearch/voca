"""Keep gallery summaries in the main page and each case in a separate HTML page."""
from pathlib import Path
import html
import re

PAGE = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'(<details class="(?:example-choice|agent-case-choice)"[^>]*\sid="([^"]+)"[^>]*>.*?)(<article\b[^>]*>)(.*?)</article>', re.S)

def split_cases(markup, group):
    directory = PAGE / 'pages' / group
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    def replace(match):
        prefix, identifier, article, body = match.groups()
        title = re.search(r'<span class="(?:choice-title|agent-choice-title)">(.*?)</span>', prefix, re.S)
        title = title.group(1) if title else identifier
        rel = f'pages/{group}/{identifier}.html'
        path = PAGE / rel
        paths.append(rel)
        path.write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<base href="../../"><title>{title} · Voca</title><link rel="stylesheet" href="static/css/style.css"></head>
<body><main class="wrap case-page"><a href="index.html#{identifier}">← Back to examples</a><h2>{title}</h2>
<div id="case-content">{body}</div></main></body></html>''')
        fallback = f'<p><a href="{html.escape(rel)}">Open this example on its own page</a></p>'
        return prefix + article + f'<div class="case-fragment" data-case-src="{rel}" aria-live="polite">{fallback}</div></article>'
    result = PATTERN.sub(replace, markup)
    for old in directory.glob('*.html'):
        if old.relative_to(PAGE).as_posix() not in paths:
            old.unlink()
    return result, paths
