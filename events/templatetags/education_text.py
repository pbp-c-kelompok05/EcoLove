"""A small, escaped text format for existing plain-text articles; no raw HTML."""
import re

from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()


@register.filter
def structured_text(value):
    blocks, pending = [], []
    mode = None

    def flush():
        if not pending:
            return
        if mode in ('ul', 'ol'):
            items = format_html_join('', '<li>{}</li>', ((line,) for line in pending))
            blocks.append(format_html('<ul>{}</ul>' if mode == 'ul' else '<ol>{}</ol>', items))
        else:
            lines = format_html_join(' ', '{}', ((line,) for line in pending))
            blocks.append(format_html('<p>{}</p>', lines))
        pending.clear()

    for line in str(value or '').splitlines():
        line = line.strip()
        if not line:
            flush()
            mode = None
            continue
        heading = re.match(r'^(#{1,3})\s+(.+)$', line)
        bullet = re.match(r'^[-*]\s+(.+)$', line)
        numbered = re.match(r'^\d+\.\s+(.+)$', line)
        if heading:
            flush()
            mode = None
            blocks.append(format_html('<h3>{}</h3>' if len(heading[1]) == 3 else '<h2>{}</h2>', heading[2]))
            continue
        new_mode = 'ul' if bullet else 'ol' if numbered else 'p'
        if new_mode != mode:
            flush()
            mode = new_mode
        pending.append(bullet[1] if bullet else numbered[1] if numbered else line)
    flush()
    return format_html_join('\n', '{}', ((block,) for block in blocks))
