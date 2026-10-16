# -*- coding: utf-8 -*-
"""Renderização dos blocos em PDF (reportlab) + decoração de sistema + simulação de digitalização."""
import io, math, random, re, string
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, Flowable)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

from casos import rng, ch, dfmt, hora, nome
import datetime as dt

D = "/usr/share/fonts/truetype/dejavu/"
for fam, files in {"DejaVuSerif": ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf", "DejaVuSerif-Italic.ttf", "DejaVuSerif-BoldItalic.ttf"),
                   "DejaVuSans": ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"),
                   "DejaVuSansCond": ("DejaVuSansCondensed.ttf", "DejaVuSansCondensed-Bold.ttf", "DejaVuSansCondensed-Oblique.ttf", "DejaVuSansCondensed-BoldOblique.ttf")}.items():
    names = [fam, fam + "-Bold", fam + "-Italic", fam + "-BoldItalic"]
    for n, f in zip(names, files): pdfmetrics.registerFont(TTFont(n, D + f))
    addMapping(fam, 0, 0, names[0]); addMapping(fam, 1, 0, names[1]); addMapping(fam, 0, 1, names[2]); addMapping(fam, 1, 1, names[3])

FAMS = {"Times-Roman": ("Times-Roman", "Times-Bold", "Times-Italic"), "Helvetica": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
        "DejaVuSerif": ("DejaVuSerif", "DejaVuSerif-Bold", "DejaVuSerif-Italic"), "DejaVuSans": ("DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Italic"),
        "DejaVuSansCond": ("DejaVuSansCond", "DejaVuSansCond-Bold", "DejaVuSansCond-Italic"), "Courier": ("Courier", "Courier-Bold", "Courier-Oblique")}

EMPH = re.compile(r"^(CLÁUSULA [A-ZÉÍ]+|OUTORGANTE:|OUTORGADO\(S\):|OUTORGADOS:|PODERES:|VALIDADE:|PARTES:|OBJETO:|ESPECIALMENTE|ADVERTÊNCIA:|OBSERVAÇÕES:|CERTIFICO|Resposta:|Teor do ato:|Quesito \d+:)")

def fmt(t, bold_start=False):
    t = escape(t).replace("\n", "<br/>")
    m = EMPH.match(t)
    if m: t = f"<b>{m.group(0)}</b>" + t[m.end():]
    elif bold_start:
        m = re.match(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 .,&/\-]{8,}?)(,)", t)
        if m: t = f"<b>{m.group(1)}</b>" + t[m.end(1):]
    return t

class Style:
    def __init__(self, kind):
        lawyer = kind in ("adv_a", "adv_r")
        self.fam = rng.choices(list(FAMS), [5, 3, 1.5, 1.5, .8, .2] if lawyer else [3, 4, 1, 2, 1, .5])[0]
        self.reg, self.bold, self.it = FAMS[self.fam]
        self.size = rng.choice([11, 11.5, 12, 12, 12]) if lawyer else rng.choice([10, 10.5, 11, 11, 12])
        if self.fam.startswith("DejaVu"): self.size -= .8
        self.lead = self.size * rng.choice([1.25, 1.4, 1.5, 1.5, 1.65] if lawyer else [1.2, 1.3, 1.4])
        self.indent = rng.choice([0, 1.25 * cm, 2 * cm, 2.5 * cm, 3 * cm]) if lawyer else rng.choice([0, 0, 1 * cm, 1.5 * cm])
        self.gap = rng.choice([0, 4, 6, 8])
        self.lm = rng.choice([2.5, 3, 3]) * cm; self.rm = rng.choice([2, 2, 2.5]) * cm
        self.tm = rng.choice([1.6, 2, 2.5]) * cm; self.bm = rng.choice([2, 2.5]) * cm
        self.hcase = rng.random() < .5
        self.hnum_bold = True
        S = lambda **k: ParagraphStyle("x", fontName=self.reg, fontSize=self.size, leading=self.lead, **k)
        self.p = S(alignment=TA_JUSTIFY, firstLineIndent=self.indent, spaceAfter=self.gap)
        self.pn = S(alignment=TA_JUSTIFY, spaceAfter=self.gap)
        self.c = S(alignment=TA_CENTER, spaceAfter=self.gap)
        self.r = S(alignment=TA_RIGHT, spaceAfter=self.gap)
        self.li = S(alignment=TA_JUSTIFY, leftIndent=1 * cm if lawyer else .6 * cm, spaceAfter=max(2, self.gap / 2))
        self.q = ParagraphStyle("q", fontName=self.it if rng.random() < .6 else self.reg, fontSize=self.size - 1.5, leading=(self.size - 1.5) * 1.2,
                                alignment=TA_JUSTIFY, leftIndent=rng.choice([3, 4, 5]) * cm, spaceAfter=self.gap + 4, spaceBefore=4)
        self.small = ParagraphStyle("s", fontName=self.reg, fontSize=self.size - 2.5, leading=(self.size - 2.5) * 1.2, alignment=TA_JUSTIFY, spaceAfter=4)
        self.title = ParagraphStyle("t", fontName=self.bold, fontSize=self.size + rng.choice([0, 1, 2, 3]), leading=(self.size + 3) * 1.3,
                                    alignment=TA_CENTER, spaceBefore=8, spaceAfter=10)
        if rng.random() < .25: self.title.alignment = TA_LEFT if kind not in ("juiz",) else TA_CENTER
        self.addr = ParagraphStyle("a", fontName=self.bold, fontSize=self.size, leading=self.lead, alignment=TA_JUSTIFY, spaceAfter=6)
        self.h = ParagraphStyle("h", fontName=self.bold, fontSize=self.size, leading=self.lead, spaceBefore=8, spaceAfter=6,
                                alignment=rng.choice([TA_LEFT, TA_LEFT, TA_CENTER]))
        self.h2 = ParagraphStyle("h2", fontName=self.bold if rng.random() < .7 else self.it, fontSize=self.size, leading=self.lead, spaceBefore=4, spaceAfter=4)
        self.box = ParagraphStyle("b", fontName=self.bold if rng.random() < .5 else self.reg, fontSize=self.size - 1, leading=(self.size - 1) * 1.25, alignment=TA_JUSTIFY)
        self.sig = S(alignment=TA_CENTER, spaceAfter=0)
        self.kv_k = ParagraphStyle("k", fontName=self.bold, fontSize=self.size - 1, leading=(self.size - 1) * 1.2)
        self.kv_v = ParagraphStyle("v", fontName=self.reg, fontSize=self.size - 1, leading=(self.size - 1) * 1.2)

class Scribble(Flowable):
    """Assinatura manuscrita simulada."""
    def __init__(self, w=200, h=40, seed=None):
        super().__init__(); self.w, self.h = w, h; self.r = random.Random(seed or rng.random())
    def wrap(self, *a): return self.w, self.h
    def draw(self):
        c = self.canv; r = self.r
        c.setStrokeColor(colors.Color(.05, .1, r.uniform(.3, .55)) if r.random() < .7 else colors.black)
        c.setLineWidth(r.uniform(.7, 1.4)); c.setLineCap(1)
        x = self.w * .2; y = self.h * .45
        p = c.beginPath(); p.moveTo(x, y)
        for _ in range(r.randint(5, 9)):
            x2 = x + r.uniform(8, 28)
            p.curveTo(x + r.uniform(-6, 12), y + r.uniform(-4, 22), x2 + r.uniform(-14, 4), y + r.uniform(-20, 8), x2, y + r.uniform(-6, 6))
            x = x2
        c.drawPath(p, stroke=1, fill=0)
        if r.random() < .7:
            c.line(self.w * .18, self.h * .3 + r.uniform(-3, 3), x + r.uniform(-20, 10), self.h * .35 + r.uniform(-4, 6))

class Stamp(Flowable):
    """Carimbo retangular (reconhecimento de firma / protocolo)."""
    def __init__(self, lines, w=210, ang=None):
        super().__init__(); self.lines = lines; self.w = w; self.h = 12 + 9 * len(lines); self.ang = ang if ang is not None else rng.uniform(-9, 9)
        self.col = colors.Color(*ch([(.15, .2, .6), (.55, .1, .15), (.2, .2, .2)]), alpha=rng.uniform(.65, .9))
    def wrap(self, *a): return self.w, self.h + 10
    def draw(self):
        c = self.canv; c.saveState(); c.translate(self.w / 2 + rng.uniform(40, 160), self.h / 2); c.rotate(self.ang)
        c.setStrokeColor(self.col); c.setFillColor(self.col); c.setLineWidth(1.3)
        c.roundRect(-self.w / 2, -self.h / 2, self.w, self.h, 4); c.setFont("Helvetica-Bold", 7.2)
        for i, l in enumerate(self.lines): c.drawCentredString(0, self.h / 2 - 11 - 9 * i, l[:58])
        c.restoreState()

def esc_title(t): return escape(t)

def build_story(doc, st, c):
    out = []
    for b in doc["blocks"]:
        k = b[0]
        if k == "p": out.append(Paragraph(fmt(b[1], bold_start=True), st.p))
        elif k == "pn": out.append(Paragraph(fmt(b[1]), st.pn))
        elif k == "li": out.append(Paragraph(fmt(b[1]), st.li))
        elif k == "q": out.append(Paragraph(fmt(b[1]), st.q))
        elif k == "small": out.append(Paragraph(fmt(b[1]), st.small))
        elif k == "r": out.append(Paragraph(fmt(b[1]), st.r))
        elif k == "rbold": out.append(Paragraph("<b>" + escape(b[1]) + "</b>", st.r))
        elif k == "addr": out.append(Paragraph(escape(b[1]), st.addr))
        elif k == "title":
            if b[1]: out.append(Paragraph(esc_title(b[1]), st.title))
        elif k == "h":
            t = escape(b[1])
            if doc.get("h_underline"): t = f"<u>{t}</u>"
            out.append(Paragraph(t, st.h))
        elif k == "h2": out.append(Paragraph(escape(b[1]), st.h2))
        elif k == "sp": out.append(Spacer(1, b[1]))
        elif k == "pb": out.append(PageBreak())
        elif k == "box":
            t = Table([[Paragraph(fmt(b[1]), st.box)]], colWidths=[A4[0] - st.lm - st.rm - (rng.choice([0, 2]) * cm)])
            t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .8, colors.black) if rng.random() < .6 else ("LINEBEFORE", (0, 0), (0, -1), 2, colors.grey),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            t.hAlign = "RIGHT"; out += [t, Spacer(1, 8)]
        elif k == "kv":
            rows = [[Paragraph(escape(a) + ":", st.kv_k), Paragraph(escape(v), st.kv_v)] for a, v in b[1]]
            W = A4[0] - st.lm - st.rm
            t = Table(rows, colWidths=[W * .3, W * .7])
            sty = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("LEFTPADDING", (0, 0), (-1, -1), 2)]
            if rng.random() < .3: sty.append(("BOX", (0, 0), (-1, -1), .5, colors.grey))
            t.setStyle(TableStyle(sty)); out += [t, Spacer(1, 8)]
        elif k == "table":
            rows, widths = b[1], b[2]; fs = b[3] if len(b) > 3 else st.size - 2
            W = A4[0] - st.lm - st.rm; scale = W / sum(widths) if sum(widths) > W else 1
            ps = ParagraphStyle("tc", fontName=st.reg, fontSize=fs, leading=fs * 1.2)
            pb = ParagraphStyle("tb", fontName=st.bold, fontSize=fs, leading=fs * 1.2)
            data = [[Paragraph(escape(str(v)), pb if i == 0 else ps) for v in r] for i, r in enumerate(rows)]
            t = Table(data, colWidths=[w * scale for w in widths], repeatRows=1)
            hdr = colors.Color(*[rng.uniform(.82, .93)] * 3)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), hdr), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            out += [t, Spacer(1, 10)]
        elif k == "sig":
            lines = b[1]; parts = [Spacer(1, rng.choice([14, 22, 30]))]
            if doc.get("hand_all") or (doc["autor"] in ("perito",) and rng.random() < .3): parts.append(Scribble())
            elif rng.random() < .35 and doc["autor"] in ("adv_a", "adv_r"):
                parts.append(Paragraph("<i>(assinado digitalmente)</i>", st.sig))
            for i, l in enumerate(lines):
                if not l: parts.append(Spacer(1, 6)); continue
                if i == 0 and doc["autor"] not in ("juiz", "relator", "servidor") and len(lines) > 2 and l.endswith("."):
                    parts.append(Paragraph(escape(l), st.r if rng.random() < .5 else st.pn)); parts.append(Spacer(1, 20)); continue
                sty = ParagraphStyle("sg", parent=st.sig, fontName=st.bold if l.isupper() and i <= 2 else st.reg, fontSize=st.size - (2.5 if len(l) > 60 else 0))
                parts.append(Paragraph(escape(l), sty))
            out.append(KeepTogether(parts))
        elif k == "sigs":
            W = A4[0] - st.lm - st.rm; cols = b[1]; ncol = 2 if len(cols) > 1 else 1
            cells = []
            for col in cols:
                cel = [Spacer(1, 26)]
                if doc.get("hand_all") or rng.random() < .25: cel.append(Scribble(150, 30))
                cel.append(Paragraph("_" * 34, st.sig))
                for l in col:
                    if l: cel.append(Paragraph(escape(l), ParagraphStyle("sg2", parent=st.sig, fontSize=st.size - 1.5, leading=(st.size - 1.5) * 1.2)))
                cells.append(cel)
            rows = [cells[i:i + ncol] for i in range(0, len(cells), ncol)]
            if len(rows[-1]) < ncol: rows[-1].append("")
            t = Table(rows, colWidths=[W / ncol] * ncol); t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            out.append(KeepTogether([t]))
        elif k == "sign_hand":
            parts = [Spacer(1, 18), Scribble(220, 44), Paragraph("_" * 42, st.sig)] + [Paragraph(escape(l), st.sig) for l in b[1]]
            if doc.get("firma"):
                cart = ch(["2º TABELIÃO DE NOTAS", "OFICIAL DE REGISTRO CIVIL E TABELIÃO DE NOTAS", "1º TABELIONATO DE NOTAS E PROTESTO"])
                parts.append(Stamp([f"{cart} DE {c.cidade.upper()}", f"Reconheço por {ch(['SEMELHANÇA', 'AUTENTICIDADE'])} a firma de:", b[1][0][:44],
                                    f"{c.cidade}, {dfmt(doc['data'])}. Em test.º da verdade.", f"Selo digital: {rng.randint(100000,999999)}{ch(string.ascii_uppercase)}{ch(string.ascii_uppercase)}{rng.randint(1000,9999)}",
                                    "Escrevente autorizado"]))
            out.append(KeepTogether(parts))
        elif k == "letterhead_bank":
            pass  # desenhado no canvas
    return out

# ------------------------------------------------------------------ decoração de página
def make_decor(doc, st, c, total_ref):
    autor = doc["autor"]; sist = doc["sistema"]
    signer = doc["signer"]; dsig = doc["data"]; hsig = hora()
    code = "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(rng.choice([7, 8])))
    protocolo = f"W{c.cidade[:2].upper()}{rng.choice(['A','B','C'])}{str(dsig.year)[2:]}{rng.randint(70000000, 79999999)}"
    pje_id = f"{dsig.strftime('%y%m%d')}{rng.randint(10**12, 10**13)}{rng.randint(10**6, 10**7)}"
    pje_num = rng.randint(10**8, 10**9)
    jt_id = "".join(rng.choice("0123456789abcdef") for _ in range(7))
    fls0 = doc["fls"]
    projudi_mov = f"{rng.randint(1, 160)}.{rng.randint(1, 4)}"
    arq = doc.get("arq_label")
    escr = doc.get("escritorio"); head = doc["head"]
    jur = (c.vara, c.cidade)
    endereco_forum = f"{ch(['Rua', 'Avenida', 'Praça'])} {ch(['Dr. Rubião Júnior', 'Dom Pedro I', 'Barão de Mauá', 'XV de Novembro', 'Monsenhor João Filippo', 'Antônio Carlos'])}, {rng.randint(10,2500)} - {ch(['Centro', 'Jardim', 'Vila Nova'])} - CEP {rng.randint(11000,39999)}-{rng.randint(0,999):03d}, Fone: ({rng.randint(11,43)}) {rng.randint(3000,3999)}-{rng.randint(1000,9999)}"
    email_vara = f"{c.cidade.split()[0].lower()}{rng.randint(1,9)}cv@{c.sigla.lower()}.jus.br".replace("ã", "a").replace("é", "e").replace("ç", "c").replace("í", "i").replace("ó", "o").replace("á", "a").replace("ú", "u")
    adv_end = f"{ch(['Rua', 'Av.'])} {ch(['Marechal Deodoro', 'Bandeirantes', 'José Bonifácio', 'Paulista', 'Tiradentes', 'Santos Dumont'])}, {rng.randint(10,3000)}, {ch(['sala ', 'cj. ', ''])}{rng.randint(1,1500)} – {c.cidade}/{c.uf} – CEP {rng.randint(11000,39999)}-{rng.randint(0,999):03d} – Tel. ({rng.randint(11,43)}) {rng.randint(3000,3999)}-{rng.randint(1000,9999)}"
    emblem = rng.random() < .6

    def draw_emblem(cv, x, y, r):
        cv.saveState(); cv.setStrokeColor(colors.black); cv.setLineWidth(.8); cv.circle(x, y, r); cv.circle(x, y, r * .78)
        pts = [(x + r * .55 * math.cos(math.pi / 2 + i * 4 * math.pi / 5), y + r * .55 * math.sin(math.pi / 2 + i * 4 * math.pi / 5)) for i in range(5)]
        p = cv.beginPath(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        p.close(); cv.drawPath(p, stroke=1, fill=0); cv.restoreState()

    def decor(cv, page):
        W, H = A4; total = total_ref[0]
        cv.saveState()
        # cabeçalho institucional
        if head == "court" and (page == 1 or doc.get("head_all")):
            y = H - 1.3 * cm
            x0 = W / 2
            if emblem: draw_emblem(cv, W / 2, y - 10, 13); y -= 30
            lines = []
            if c.justica == "trab":
                lines = [("Helvetica-Bold", 9, "PODER JUDICIÁRIO"), ("Helvetica-Bold", 9, "JUSTIÇA DO TRABALHO"), ("Helvetica-Bold", 9, c.trib), ("Helvetica", 8.5, c.vara)]
                if doc.get("inst2"): lines[-1] = ("Helvetica", 8.5, f"Gabinete do(a) Desembargador(a) {c.relator}")
            elif doc.get("inst2"):
                lines = [("Helvetica-Bold", 9.5, "PODER JUDICIÁRIO"), ("Helvetica-Bold", 9.5, c.trib if c.justica != "jec" else f"COLÉGIO RECURSAL DA COMARCA DE {c.cidade.upper()}")]
                if c.justica == "civel": lines.append(("Helvetica", 8.5, c.camara if c.uf != "SP" else "Seção de Direito Privado – " + c.camara))
            elif c.sistema == "esaj":
                lines = [("Helvetica-Bold", 9.5, c.trib), ("Helvetica-Bold", 8.5, f"COMARCA DE {c.cidade.upper()}"), ("Helvetica-Bold", 8.5, f"FORO DE {c.cidade.upper()}" if c.cidade != "São Paulo" else "FORO CENTRAL CÍVEL"),
                         ("Helvetica-Bold", 8.5, c.vara.split(" da Comarca")[0].split(" do Foro")[0].upper()), ("Helvetica", 7.5, endereco_forum), ("Helvetica", 7.5, f"E-mail: {email_vara}"),
                         ("Helvetica", 7.5, "Horário de Atendimento ao Público: das 13h00min às 17h00min")]
            else:
                lines = [("Helvetica-Bold", 9.5, "PODER JUDICIÁRIO"), ("Helvetica-Bold", 9, c.trib), ("Helvetica", 8.5, "Justiça de Primeira Instância" if c.uf == "MG" else ""),
                         ("Helvetica", 8.5, c.vara)]
            for f, s, t in lines:
                if not t: continue
                cv.setFont(f, s); cv.drawCentredString(x0, y, t[:110]); y -= s + 2.5
            if rng.random() < .5: cv.setLineWidth(.5); cv.line(st.lm, y + 2, W - st.rm, y + 2)
        elif head == "adv" and (page == 1 or doc.get("head_all")):
            y = H - 1.6 * cm
            style = doc["lh_style"]
            if style == 0:
                cv.setFont(st.bold, 13); cv.drawCentredString(W / 2, y, escr.upper()); cv.setFont(st.reg, 8); cv.drawCentredString(W / 2, y - 12, "ADVOCACIA E CONSULTORIA JURÍDICA")
                cv.setLineWidth(1); cv.line(st.lm, y - 18, W - st.rm, y - 18)
            elif style == 1:
                cv.setFillColor(colors.Color(.1, .2, .35)); cv.rect(st.lm, y - 6, 26, 26, fill=1, stroke=0); cv.setFillColor(colors.white)
                cv.setFont("Helvetica-Bold", 13); cv.drawCentredString(st.lm + 13, y + 1, "".join(w[0] for w in escr.split() if w[0].isupper())[:2])
                cv.setFillColor(colors.Color(.1, .2, .35)); cv.setFont("Helvetica-Bold", 11); cv.drawString(st.lm + 34, y + 8, escr)
                cv.setFont("Helvetica", 7.5); cv.drawString(st.lm + 34, y - 3, "OAB/" + c.uf + " – Sociedade de Advogados")
            else:
                cv.setFont("Times-Italic", 14); cv.drawRightString(W - st.rm, y, escr)
                cv.setLineWidth(.4); cv.line(W / 2, y - 6, W - st.rm, y - 6)
            if style != 2 or rng.random() < .5:
                cv.setFillColor(colors.Color(.25, .25, .25)); cv.setFont("Helvetica", 7); cv.drawCentredString(W / 2, 1.2 * cm, adv_end)
        elif head == "perito" and page == 1:
            y = H - 1.6 * cm; cv.setFont(st.bold, 12); cv.drawString(st.lm, y, c.perito[0].upper()); cv.setFont(st.reg, 8.5)
            cv.drawString(st.lm, y - 11, ch(["Perícias Judiciais – Grafotécnica e Documentoscopia", "Perícias Contábeis e Financeiras", "Perito Judicial – Cadastro AJ/TJ"])); cv.line(st.lm, y - 16, W - st.rm, y - 16)
        elif head == "bank" and page == 1:
            y = H - 1.7 * cm; cv.setFillColor(colors.Color(.6, .05, .1)); cv.circle(st.lm + 10, y + 4, 10, fill=1, stroke=0)
            cv.setFillColor(colors.black); cv.setFont("Helvetica-Bold", 13); cv.drawString(st.lm + 26, y, doc["bank_name"].replace(" S.A.", ""))
            cv.setFont("Helvetica", 7.5); cv.drawString(st.lm + 26, y - 10, "Departamento Jurídico – Contencioso de Massa")
        # carimbo de sistema
        if sist == "esaj":
            cv.setFont("Helvetica", 9); cv.drawRightString(W - 1.2 * cm, H - 1 * cm, f"fls. {fls0 + page - 1}")
            cv.saveState(); cv.translate(W - .7 * cm, 1.2 * cm); cv.rotate(90); cv.setFont("Helvetica", 6.2); cv.setFillColor(colors.Color(.2, .2, .2))
            if autor in ("adv_a", "adv_r", "perito", "parte_a", "parte_r"):
                txt = f"Este documento é cópia do original, assinado digitalmente por {signer.upper()} e Tribunal de Justiça do Estado de São Paulo, protocolado em {dfmt(dsig)} às {hsig[:5]}, sob o número {protocolo}."
            else:
                txt = f"Este documento é cópia do original, assinado digitalmente por {signer.upper()}, liberado nos autos em {dfmt(dsig)} às {hsig[:5]}."
            cv.drawString(0, 8, txt[:170]); cv.drawString(0, 0, f"Para conferir o original, acesse o site https://esaj.tjsp.jus.br/pastadigital/pg/abrirConferenciaDocumento.do, informe o processo {c.numero} e código {code}.")
            cv.restoreState()
        elif sist == "pje":
            cv.setFont("Helvetica", 6.5); cv.setFillColor(colors.Color(.25, .25, .25)); y = .9 * cm
            dom = {"MG": "pje.tjmg.jus.br", "RJ": "tjrj.pje.jus.br", "SP": "pje.tjsp.jus.br", "PR": "pje.tjpr.jus.br"}.get(c.uf, "pje.jus.br")
            cv.drawString(st.lm, y + 16, f"Assinado eletronicamente por: {signer.upper()} - {dfmt(dsig)} {hsig}")
            cv.drawString(st.lm, y + 8, f"https://{dom}:443/pje/Processo/ConsultaDocumento/listView.seam?x={pje_id}")
            cv.drawString(st.lm, y, f"Número do documento: {pje_id}")
            cv.drawRightString(W - st.rm, y, f"Num. {pje_num} - Pág. {page}")
        elif sist == "pjejt":
            cv.setFont("Helvetica", 7); cv.setFillColor(colors.Color(.25, .25, .25))
            cv.drawRightString(W - 1.2 * cm, H - 1 * cm, f"Fls.: {fls0 + page - 1}")
            cv.drawString(st.lm, .9 * cm, f"Assinado eletronicamente por: {signer.upper()} - Juntado em: {dfmt(dsig)} {hsig} - {jt_id}")
            cv.drawRightString(W - st.rm, .55 * cm, f"ID. {jt_id} - Pág. {page}")
        elif sist == "projudi":
            cv.setFont("Helvetica", 6.5); cv.setFillColor(colors.Color(.25, .25, .25))
            top = f"PROJUDI - Processo: {c.numero} - Ref. mov. {projudi_mov} - Assinado digitalmente por {signer}"
            if arq: top += f" - {dfmt(dsig)}: {arq}"
            cv.drawString(st.lm, H - .8 * cm, top[:150])
            cv.drawString(st.lm, .9 * cm, "Documento assinado digitalmente, conforme MP nº 2.200-2/2001, Lei nº 11.419/2006, resolução do Projudi, do TJPR/OE")
            cv.drawString(st.lm, .6 * cm, f"Validação deste em https://projudi.tjpr.jus.br/projudi/ - Identificador: PJ{code[:3]} {code[3:6]}{rng.randint(10,99)} {rng.choice('ABCDEFGH')}{rng.randint(10,99)}{code[-2:]} {rng.randint(100,999)}{code[:2]}")
        # paginação própria
        if doc["pagenum"] and total > 1:
            cv.setFont(st.reg, 8.5); cv.setFillColor(colors.black)
            t = doc["pagenum"].format(p=page, t=total)
            if doc["pagenum_pos"] == "r": cv.drawRightString(W - st.rm, 1.7 * cm, t)
            else: cv.drawCentredString(W / 2, 1.7 * cm, t)
        if page > 1 and doc.get("running"):
            cv.setFont(st.reg, 8); cv.setFillColor(colors.Color(.3, .3, .3)); cv.drawString(st.lm, H - 1.5 * cm, doc["running"][:120])
        cv.restoreState()
    return decor

def render_pdf(doc, c, path_or_buf):
    st = Style(doc["autor"])
    total_ref = [1]
    top_extra = {"court": (3.6 if c.sistema == "esaj" and not doc.get("inst2") else 2.6) * cm, "adv": 1.3 * cm, "perito": 1.1 * cm, "bank": 1.3 * cm, "none": .4 * cm}[doc["head"]]
    decor = make_decor(doc, st, c, total_ref)

    class NumCanvas(rl_canvas.Canvas):
        def __init__(self, *a, **k):
            super().__init__(*a, **k); self._saved = []
        def showPage(self):
            self._saved.append(dict(self.__dict__)); self._startPage()
        def save(self):
            total_ref[0] = len(self._saved)
            for i, s in enumerate(self._saved):
                self.__dict__.update(s); decor(self, i + 1); super().showPage()
            super().save()

    def frames(first):
        tm = st.tm + (top_extra if first else (0.4 * cm if doc.get("running") else 0))
        return Frame(st.lm, st.bm + .5 * cm, A4[0] - st.lm - st.rm, A4[1] - tm - st.bm - .5 * cm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    bd = BaseDocTemplate(path_or_buf, pagesize=A4, title=doc.get("meta_title", ""), author=doc.get("meta_author", ""), creator=doc.get("creator", ""))
    bd.addPageTemplates([PageTemplate(id="first", frames=[frames(True)], autoNextPageTemplate="later"), PageTemplate(id="later", frames=[frames(False)])])
    story = build_story(doc, st, c)
    bd.build(story, canvasmaker=NumCanvas)
    return total_ref[0]

# ------------------------------------------------------------------ digitalização simulada
OCR_SWAPS = [("rn", "m"), ("m", "rn"), ("l", "1"), ("I", "l"), ("o", "0"), ("e", "c"), ("ã", "a"), ("ç", "c"), ("é", "e"), ("í", "i"), ("h", "b"), ("u", "n"), (",", "."), ("ó", "o"), ("S", "5"), ("§", "S")]
def ocr_noise(w, rate):
    if rng.random() > rate: return w
    a, b = ch(OCR_SWAPS)
    return w.replace(a, b, 1) if a in w else w

def scanify(pdf_bytes, level, ocr=False):
    import pymupdf, numpy as np
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
    src = pymupdf.open(stream=pdf_bytes, filetype="pdf"); out = pymupdf.open()
    ocr_rate = {1: .03, 2: .07, 3: .15}[level]
    dpi = rng.choice([110, 130, 150, 150, 200]) if level < 3 else rng.choice([90, 100, 110])
    gray = rng.random() < .75; bw = level >= 2 and rng.random() < .35
    tilt_base = rng.uniform(-1.8, 1.8) * (1 if level < 3 else 1.8)
    for pg in src:
        pix = pg.get_pixmap(dpi=dpi)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if gray: im = im.convert("L")
        # fundo amarelado/acinzentado
        arr = np.asarray(im).astype(np.float32)
        tint = rng.uniform(225, 250)
        arr = arr * (tint / 255.0) + rng.uniform(0, 8)
        # gradiente de iluminação
        h, w = arr.shape[:2]
        gx = np.linspace(rng.uniform(-18, 0), rng.uniform(-18, 0), w)[None, :]
        gy = np.linspace(rng.uniform(-10, 0), rng.uniform(-10, 0), h)[:, None]
        g = gx + gy
        arr = arr + (g if arr.ndim == 2 else g[..., None])
        # ruído
        sig = rng.uniform(3, 9) * (1 + level * .6)
        noise = np.random.default_rng(rng.randint(0, 10**9)).normal(0, sig, arr.shape)
        arr = np.clip(arr + noise, 0, 255)
        im = Image.fromarray(arr.astype(np.uint8))
        # manchas / pontos
        dr = ImageDraw.Draw(im)
        for _ in range(rng.randint(10, 80) * (1 + level)):
            x, y = rng.randint(0, w - 1), rng.randint(0, h - 1); r = rng.choice([1, 1, 1, 2, 3])
            dr.ellipse([x, y, x + r, y + r], fill=rng.randint(30, 120) if gray else (rng.randint(30, 120),) * 3)
        if rng.random() < .3 * level:  # faixa de toner
            x = rng.randint(0, w - 1); dr.line([x, 0, x + rng.randint(-20, 20), h], fill=rng.randint(150, 200) if gray else (170, 170, 170), width=rng.randint(1, 3))
        if rng.random() < .25:  # furos de perfurador
            for yy in (h * .38, h * .62):
                dr.ellipse([w * .03, yy - 18, w * .03 + 36, yy + 18], fill=rng.randint(20, 60) if gray else (40, 40, 40))
        # rotação
        ang = tilt_base + rng.uniform(-.4, .4)
        im = im.rotate(ang, resample=Image.BICUBIC, expand=False, fillcolor=rng.randint(20, 70) if gray else (40, 40, 40))
        # borda escura (sombra do scanner)
        if rng.random() < .4:
            dr = ImageDraw.Draw(im); bwid = rng.randint(4, 25)
            side = ch(["l", "t", "r"])
            box = {"l": [0, 0, bwid, h], "t": [0, 0, w, bwid], "r": [w - bwid, 0, w, h]}[side]
            dr.rectangle(box, fill=rng.randint(10, 60) if gray else (30, 30, 30))
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(.3, .9 + level * .3)))
        im = ImageEnhance.Contrast(im).enhance(rng.uniform(.8, 1.3))
        if bw: im = im.convert("L").point(lambda v: 255 if v > rng.randint(140, 175) else 0, "1").convert("L")
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=rng.randint(28, 70) if level >= 2 else rng.randint(45, 82)); buf.seek(0)
        npg = out.new_page(width=pg.rect.width, height=pg.rect.height)
        npg.insert_image(npg.rect, stream=buf.getvalue())
        if ocr:
            for x0, y0, x1, y1, wd, *_ in pg.get_text("words"):
                wd = ocr_noise(wd, ocr_rate)
                if rng.random() < ocr_rate / 3: continue
                fs = max(4, (y1 - y0) * .8)
                try: npg.insert_text((x0, y1 - (y1 - y0) * .2), wd, fontsize=fs, fontname="helv", render_mode=3)
                except Exception: pass
    if level >= 1 and rng.random() < .08:  # página em branco digitalizada
        npg = out.new_page(width=A4[0], height=A4[1])
        im = Image.fromarray(np.clip(np.random.default_rng().normal(240, 6, (int(A4[1] * 1.5), int(A4[0] * 1.5))), 0, 255).astype(np.uint8))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=40); npg.insert_image(npg.rect, stream=buf.getvalue())
    out.set_metadata({"producer": ch(["", "Canon iR-ADV C5535 PDF", "HP Digital Sending", "Brother MFC-L8900CDW", "Epson Scan 2", "CamScanner", "Adobe Scan"]), "creator": ""})
    b = out.tobytes(garbage=3, deflate=True); n = len(out); out.close(); src.close()
    return b, n
