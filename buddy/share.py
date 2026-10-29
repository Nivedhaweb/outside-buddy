"""Shareable bits: the parent invite message and the 'touch grass receipt'."""

from __future__ import annotations

import base64
from datetime import datetime
from urllib.parse import quote
from xml.sax.saxutils import escape

from .models import Mission

FACES = ["😞", "😕", "😐", "🙂", "😄"]


def invite_text(m: Mission, together: bool = False) -> str:
    """A short, non-naggy message a parent can send. Built from a template (no extra AI call)."""
    opener = "Side quest for us this week 🌿" if together else "Got a side quest for you 🌿"
    steps = " → ".join(s.rstrip(".") for s in m.steps[:3])
    return (f"{opener}\n\n*{m.title}* ({m.duration_min} min)\n{m.goal}\n📍 {m.where}\n"
            f"{steps}\n\nPhone stays in your pocket. Tell me one thing you spotted 👀")


def whatsapp_link(text: str) -> str:
    # Only the mission text goes in the link — no names, numbers or locations of the user.
    return "https://wa.me/?text=" + quote(text)


def receipt_svg(m: Mission, spotted: int, observe_total: int, feeling: int, xp: int,
                level: str, streak_days: int) -> str:
    """An SVG 'receipt' to screenshot or share. All text is XML-escaped."""
    t = escape(m.title[:34])
    when = datetime.now().strftime("%d %b %Y · %H:%M")
    face = FACES[max(1, min(feeling, 5)) - 1]
    rows = [
        ("Time outside", f"{m.duration_min} min"),
        ("Screen time swapped", f"{m.duration_min} min"),
        ("Things spotted", f"{spotted}/{observe_total}"),
        ("Vibe after", face),
        ("Streak", f"{streak_days} day{'s' if streak_days != 1 else ''} 🔥"),
        ("Level", escape(level)),
    ]
    y, body = 210, []
    for label, val in rows:
        body.append(f"<text x='28' y='{y}' class='r'>{label}</text>"
                    f"<text x='332' y='{y}' class='r' text-anchor='end'>{val}</text>")
        y += 30
    bars = "".join(
        f"<rect x='{28 + i * 7}' y='{y + 70}' width='{(i * 37) % 4 + 1}' height='38' fill='#18233D'/>"
        for i in range(43)
    )
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='360' height='{y + 150}' viewBox='0 0 360 {y + 150}'>
<style>
 .h{{font:800 26px 'Bricolage Grotesque',system-ui,sans-serif;fill:#18233D}}
 .s{{font:600 13px 'Figtree',system-ui,sans-serif;fill:#18233D;opacity:.7}}
 .t{{font:800 19px 'Bricolage Grotesque',system-ui,sans-serif;fill:#18233D}}
 .r{{font:500 15px ui-monospace,'Courier New',monospace;fill:#18233D}}
 .x{{font:800 30px 'Bricolage Grotesque',system-ui,sans-serif;fill:#18233D}}
</style>
<rect x='3' y='3' width='354' height='{y + 144}' rx='18' fill='#FFFFFF' stroke='#18233D' stroke-width='3'/>
<rect x='3' y='3' width='354' height='96' rx='18' fill='#22B07D' stroke='#18233D' stroke-width='3'/>
<text x='28' y='48' class='h' style='fill:#fff'>touch grass receipt</text>
<text x='28' y='76' class='s' style='fill:#fff;opacity:.9'>Outside Buddy · {when}</text>
<text x='28' y='140' class='t'>{t}</text>
<line x1='28' y1='164' x2='332' y2='164' stroke='#18233D' stroke-dasharray='5 5'/>
{''.join(body)}
<line x1='28' y1='{y - 10}' x2='332' y2='{y - 10}' stroke='#18233D' stroke-dasharray='5 5'/>
<text x='28' y='{y + 30}' class='x'>+{xp} XP</text>
<rect x='212' y='{y + 6}' width='120' height='34' rx='17' fill='#FFD23F' stroke='#18233D' stroke-width='2'/>
<text x='272' y='{y + 29}' class='s' text-anchor='middle' style='opacity:1'>main character</text>
{bars}
</svg>"""


def svg_data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
