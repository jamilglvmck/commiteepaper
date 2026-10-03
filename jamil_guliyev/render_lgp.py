"""Render a Leadership Growth Plan markdown draft to a PDF in the ROYG LGP layout.

Usage: python3 render_lgp.py [input.md] [output.pdf]
Requires: pip install reportlab
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

HERE = Path(__file__).parent
NAVY = colors.HexColor("#051C2C")
BLUE = colors.HexColor("#2251FF")

STYLES = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY, spaceAfter=10),
    "h1": ParagraphStyle("h1", keepWithNext=1, fontName="Helvetica-Bold", fontSize=12.5, textColor=BLUE, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", keepWithNext=1, fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, spaceBefore=7, spaceAfter=4),
    "h3": ParagraphStyle("h3", keepWithNext=1, fontName="Helvetica-Bold", fontSize=9.5, textColor=BLUE, spaceBefore=6, spaceAfter=3),
    "label": ParagraphStyle("label", keepWithNext=1, fontName="Helvetica", fontSize=9, leading=12, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=3),
}


def inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\[\[(.+?)\]\]", r'<span backColor="#FFF200">[\1]</span>', text)


def parse(md: str):
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if m:
        for line in m.group(1).splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        md = md[m.end():]
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    return meta, md.splitlines()


def build_story(lines, name):
    story = [Paragraph(escape(name), STYLES["title"])]
    bullets = []

    def flush():
        if not bullets:
            return
        items = []
        for level, text in bullets:
            para = Paragraph(inline(text), STYLES["body"])
            if level == 0 or not items:
                items.append([para])
            else:
                items[-1].append(para)
        flow_items = []
        for group in items:
            head, *subs = group
            content = [head]
            if subs:
                content.append(ListFlowable(
                    [ListItem(s, leftIndent=12) for s in subs],
                    bulletType="bullet", start="\u25e6", leftIndent=12, bulletFontSize=7,
                ))
            flow_items.append(ListItem(content, leftIndent=12))
        story.append(ListFlowable(flow_items, bulletType="bullet", start="\u2022", leftIndent=12, bulletFontSize=8))
        bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        bullet = re.match(r"^(\s*)- (.*)$", line)
        if bullet:
            bullets.append((1 if len(bullet.group(1)) >= 2 else 0, bullet.group(2)))
            continue
        flush()
        if not line.strip():
            continue
        for prefix, style in (("### ", "h3"), ("## ", "h2"), ("# ", "h1")):
            if line.startswith(prefix):
                story.append(Paragraph(inline(line[len(prefix):]), STYLES[style]))
                break
        else:
            style = "label" if line.startswith("**") and line.endswith("**") else "body"
            story.append(Paragraph(inline(line), STYLES[style]))
    flush()
    return story


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "Guliyev_Jamil_ROYG_Leadership_Growth_Plan.md"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".pdf")
    meta, lines = parse(src.read_text(encoding="utf-8"))
    name = meta.get("name", "")
    header = f"Leadership Growth Plan {meta.get('cycle', '')}"

    def decorate(canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, height - 1.2 * cm, "Confidential")
        canvas.drawCentredString(width / 2, height - 1.2 * cm, name)
        canvas.drawRightString(width - 2 * cm, height - 1.2 * cm, header)
        canvas.drawRightString(width - 2 * cm, 1 * cm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.6 * cm, title=f"{name} - {header}", author=name,
    )
    doc.build(build_story(lines, name), onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
