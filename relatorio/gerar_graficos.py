"""Gera os gráficos SVG do README a partir de uma execução do classificador.

Uso:
    python relatorio/gerar_graficos.py execucoes/<run_id> [--prompt-tokens 4182]

Os SVGs são estáticos (abrem em <img> no GitHub) e seguem o tema claro/escuro do sistema.
"""

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "graficos"
FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# Volume e preços de referência da projeção de produção.
VOLUMES_MES = [100_000, 300_000, 1_000_000]
USD_POR_TOKEN = 0.042 / 1_000_000
USD_OCR_NUVEM_POR_PAGINA = 1.50 / 1000  # faixa típica de OCR gerenciado (Textract, Document AI)

ESTILO = """
  .bg{fill:#fcfcfb} .borda{stroke:rgba(11,11,11,.10);fill:none}
  .t1{fill:#0b0b0b} .t2{fill:#52514e} .mut{fill:#898781}
  .grid{stroke:#e1e0d9;stroke-width:1} .base{stroke:#c3c2b7;stroke-width:1}
  .s1{fill:#2a78d6} .s2{fill:#eb6834} .gap{stroke:#fcfcfb;stroke-width:2}
  .s1s{stroke:#2a78d6} .s2s{stroke:#eb6834} .no{fill:#fcfcfb;stroke:#c3c2b7}
  text{font-family:%s}
  @media (prefers-color-scheme: dark){
    .bg{fill:#1a1a19} .borda{stroke:rgba(255,255,255,.10)}
    .t1{fill:#f0efec} .t2{fill:#c3c2b7}
    .grid{stroke:#2c2c2a} .base{stroke:#383835}
    .s1{fill:#3987e5} .s2{fill:#d95926} .gap{stroke:#1a1a19}
    .s1s{stroke:#3987e5} .s2s{stroke:#d95926} .no{fill:#1a1a19;stroke:#383835}
  }
""" % FONTE


def svg(largura: int, altura: int, titulo: str, corpo: str, extra_css: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" '
        f'width="{largura}" height="{altura}" role="img" aria-label="{titulo}">\n'
        f"<title>{titulo}</title>\n<style>{ESTILO}{extra_css}</style>\n"
        f'<rect class="bg" x="0" y="0" width="{largura}" height="{altura}" rx="12"/>\n'
        f'<rect class="borda" x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="12"/>\n'
        f"{corpo}\n</svg>\n"
    )


def texto(x, y, conteudo, classe="t2", tam=13, ancora="start", peso=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{classe}" font-size="{tam}" '
            f'text-anchor="{ancora}" font-weight="{peso}">{conteudo}</text>')


def barra_h(x, y, w, h, classe, arredonda_fim=False):
    """Segmento horizontal; o último segmento da pilha tem a ponta arredondada (4px)."""
    if w <= 0:
        return ""
    if not arredonda_fim or w < 4:
        return f'<rect class="{classe}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}"/>'
    r = 4
    return (f'<path class="{classe}" d="M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} '
            f'v{h - 2 * r:.1f} a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} z"/>')


def barra_v(x, y_base, w, h, classe, arredonda_topo=False):
    y = y_base - h
    if h <= 0:
        return ""
    if not arredonda_topo or h < 4:
        return f'<rect class="{classe}" x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h:.1f}"/>'
    r = 4
    return (f'<path class="{classe}" d="M{x:.1f},{y_base:.1f} v-{h - r:.1f} a{r},{r} 0 0 1 {r},-{r} '
            f'h{w - 2 * r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - r:.1f} z"/>')


def legenda(x, y, itens):
    partes, cx = [], x
    for classe, rotulo in itens:
        partes.append(f'<rect class="{classe}" x="{cx}" y="{y - 10}" width="12" height="12" rx="3"/>')
        partes.append(texto(cx + 18, y, rotulo, "t2", 13))
        cx += 18 + 7.2 * len(rotulo) + 24
    return "\n".join(partes)


NOMES = {
    "certidao": "certidão", "decisao_interlocutoria": "decisão interlocutória", "despacho": "despacho",
    "agravo_instrumento": "agravo de instrumento", "procuracao": "procuração", "oficio": "ofício",
    "ata_audiencia": "ata de audiência", "calculos_liquidacao": "cálculos", "sentenca": "sentença", "termo_acordo": "termo de acordo",
    "recurso_apelacao": "recurso de apelação", "acordao": "acórdão", "peticao_inicial": "petição inicial",
    "contestacao": "contestação", "replica": "réplica", "contrarrazoes": "contrarrazões",
    "embargos_declaracao": "embargos de declaração", "alvara": "alvará", "laudo_pericial": "laudo pericial",
}


def nome(classe: str) -> str:
    return NOMES.get(classe, classe.replace("_", " "))


def br(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- gráficos


def grafico_tempo(registros) -> str:
    grupos = [
        ("PDF com texto", [r for r in registros if r["metodo_extracao"] == "texto"]),
        ("PDF escaneado (OCR)", [r for r in registros if r["metodo_extracao"] != "texto"]),
    ]
    L, A = 760, 250
    x0, x1, escala_max = 190, 700, 1.4
    px = lambda s: (x1 - x0) * s / escala_max
    corpo = [
        texto(24, 34, "Tempo por documento (mediana, segundos)", "t1", 16, peso=600),
        texto(24, 54, "Com OCR, a extração local passa a ser a etapa mais lenta; o Jev fica estável em ~0,27 s", "t2", 12),
        legenda(24, 84, [("s2", "extração do texto"), ("s1", "classificação no Jev")]),
    ]
    for i in range(0, 6):
        s = i * 0.25
        x = x0 + px(s)
        corpo.append(f'<line class="grid" x1="{x:.1f}" y1="100" x2="{x:.1f}" y2="206"/>')
        corpo.append(texto(x, 226, br(s, 2), "mut", 11, "middle"))
    for i, (rotulo, grupo) in enumerate(grupos):
        y = 116 + i * 48
        ext = st.median(r["t_extracao_s"] for r in grupo)
        jev = st.median(r["t_jev_s"] for r in grupo)
        corpo.append(texto(24, y + 17, f"{rotulo}", "t1", 13, peso=500))
        corpo.append(texto(24, y + 33, f"{len(grupo)} documentos", "mut", 11))
        corpo.append(barra_h(x0, y, px(ext), 26, "s2"))
        corpo.append(barra_h(x0 + px(ext), y, px(jev), 26, "s1", arredonda_fim=True))
        if px(ext) > 2:
            corpo.append(f'<line class="gap" x1="{x0 + px(ext):.1f}" y1="{y}" x2="{x0 + px(ext):.1f}" y2="{y + 26}"/>')
        if px(ext) > 90:
            corpo.append(f'<text x="{x0 + 8:.1f}" y="{y + 17.5:.1f}" font-size="12" fill="#fff">OCR {br(ext)} s</text>')
        corpo.append(texto(x0 + px(ext + jev) + 8, y + 17.5, f"{br(ext + jev)} s", "t1", 13, peso=600))
    corpo.append(f'<line class="base" x1="{x0}" y1="100" x2="{x0}" y2="206"/>')
    return svg(L, A, "Tempo por documento: extração e classificação", "\n".join(corpo))


def grafico_tokens(registros, prompt_tokens) -> str:
    por_pag = defaultdict(list)
    for r in registros:
        por_pag[r["paginas"]].append(r["input_tokens"])
    L, A = 760, 330
    y_base, y_topo, escala_max = 270, 110, 8000
    py = lambda t: (y_base - y_topo) * t / escala_max
    corpo = [
        texto(24, 34, "Tokens de entrada por requisição, por nº de páginas", "t1", 16, peso=600),
        texto(24, 54, f"A descrição das 22 classes custa {br(prompt_tokens, 0)} tokens fixos; o texto do documento é a menor parte", "t2", 12),
        legenda(24, 84, [("s2", "prompt fixo (taxonomia)"), ("s1", "texto do documento")]),
    ]
    x_ini = 110
    for t in range(0, escala_max + 1, 2000):
        y = y_base - py(t)
        corpo.append(f'<line class="grid" x1="{x_ini - 10}" y1="{y:.1f}" x2="730" y2="{y:.1f}"/>')
        corpo.append(texto(x_ini - 16, y + 4, br(t, 0), "mut", 11, "end"))
    largura_barra, passo = 84, 150
    for i, pag in enumerate(sorted(por_pag)):
        media = st.mean(por_pag[pag])
        doc = media - prompt_tokens
        x = x_ini + 30 + i * passo
        corpo.append(barra_v(x, y_base, largura_barra, py(prompt_tokens), "s2"))
        corpo.append(barra_v(x, y_base - py(prompt_tokens), largura_barra, py(doc), "s1", arredonda_topo=True))
        yg = y_base - py(prompt_tokens)
        corpo.append(f'<line class="gap" x1="{x}" y1="{yg:.1f}" x2="{x + largura_barra}" y2="{yg:.1f}"/>')
        corpo.append(texto(x + largura_barra / 2, y_base - py(media) - 8, br(media, 0), "t1", 13, "middle", 600))
        corpo.append(texto(x + largura_barra / 2, y_base + 20, f"{pag} pág.", "t1", 12, "middle", 500))
        corpo.append(texto(x + largura_barra / 2, y_base + 36, f"{len(por_pag[pag])} docs", "mut", 11, "middle"))
    corpo.append(f'<line class="base" x1="{x_ini - 10}" y1="{y_base}" x2="730" y2="{y_base}"/>')
    return svg(L, A, "Tokens por requisição por número de páginas", "\n".join(corpo))


def grafico_hesitacao(registros, n=6) -> str:
    piores = sorted(registros, key=lambda r: r["confianca"])[:n]
    L = 760
    A = 120 + n * 44 + 30
    x0, x1 = 200, 560
    px = lambda p: (x1 - x0) * p
    corpo = [
        texto(24, 34, f"Os {n} documentos em que o Jev mais hesitou", "t1", 16, peso=600),
        texto(24, 54, "Probabilidade da classe escolhida × segunda colocada. Todos foram classificados corretamente.", "t2", 12),
        legenda(24, 84, [("s1", "classe escolhida (correta)"), ("s2", "segunda opção")]),
    ]
    for i, r in enumerate(piores):
        y = 106 + i * 44
        (c1, p1), (c2, p2) = r["top3"][0], r["top3"][1]
        corpo.append(texto(24, y + 13, r["arquivo"].replace(".pdf", ""), "t1", 13, peso=500))
        corpo.append(texto(24, y + 29, "gabarito: " + nome(r.get("gabarito", "")), "mut", 11))
        corpo.append(barra_h(x0, y, px(p1), 24, "s1"))
        corpo.append(barra_h(x0 + px(p1), y, px(p2), 24, "s2", arredonda_fim=True))
        corpo.append(f'<line class="gap" x1="{x0 + px(p1):.1f}" y1="{y}" x2="{x0 + px(p1):.1f}" y2="{y + 24}"/>')
        corpo.append(f'<text x="{x0 + 8}" y="{y + 16.5}" font-size="12" fill="#fff">{nome(c1)} {p1:.0%}</text>')
        rotulo2 = f"{nome(c2)} {p2:.0%}"
        if px(p2) > 7.2 * len(rotulo2) + 12:
            corpo.append(f'<text x="{x0 + px(p1) + 6:.1f}" y="{y + 16.5}" font-size="12" fill="#fff">{rotulo2}</text>')
        else:
            corpo.append(texto(x0 + px(p1 + p2) + 6, y + 16.5, rotulo2, "t2", 12))
    corpo.append(f'<line class="base" x1="{x0}" y1="100" x2="{x0}" y2="{106 + n * 44 - 14}"/>')
    corpo.append(texto(x0, A - 18, "0%", "mut", 11, "middle"))
    corpo.append(texto(x1, A - 18, "100%", "mut", 11, "middle"))
    return svg(L, A, "Documentos com menor confiança", "\n".join(corpo))


def projecao(registros) -> dict:
    n = len(registros)
    tokens_doc = st.mean(r["input_tokens"] for r in registros)
    paginas_doc = sum(r["paginas"] for r in registros) / n
    paginas_ocr_doc = sum(r["paginas_ocr"] for r in registros) / n
    return {
        "tokens_por_doc": tokens_doc,
        "paginas_por_doc": paginas_doc,
        "paginas_ocr_por_doc": paginas_ocr_doc,
        "jev_usd_por_doc": tokens_doc * USD_POR_TOKEN,
        "ocr_nuvem_usd_por_doc": paginas_ocr_doc * USD_OCR_NUVEM_POR_PAGINA,
    }


def grafico_custo(proj) -> str:
    L, A = 760, 340
    y_base, y_topo = 270, 110
    totais = [(v, v * proj["jev_usd_por_doc"], v * proj["ocr_nuvem_usd_por_doc"]) for v in VOLUMES_MES]
    escala_max = 700
    py = lambda usd: (y_base - y_topo) * usd / escala_max
    corpo = [
        texto(24, 34, "Custo mensal projetado (US$)", "t1", 16, peso=600),
        texto(24, 54, "Jev pelo preço público; OCR em nuvem por preço de referência. OCR local custa só a máquina.", "t2", 12),
        legenda(24, 84, [("s1", "Jev"), ("s2", "OCR em nuvem (se usado)")]),
    ]
    x_ini = 100
    for usd in range(0, escala_max + 1, 100):
        y = y_base - py(usd)
        corpo.append(f'<line class="grid" x1="{x_ini - 10}" y1="{y:.1f}" x2="730" y2="{y:.1f}"/>')
        corpo.append(texto(x_ini - 16, y + 4, f"{usd}", "mut", 11, "end"))
    largura_barra, passo = 110, 200
    for i, (vol, jev, ocr) in enumerate(totais):
        x = x_ini + 50 + i * passo
        corpo.append(barra_v(x, y_base, largura_barra, py(jev), "s1"))
        corpo.append(barra_v(x, y_base - py(jev), largura_barra, py(ocr), "s2", arredonda_topo=True))
        yg = y_base - py(jev)
        corpo.append(f'<line class="gap" x1="{x}" y1="{yg:.1f}" x2="{x + largura_barra}" y2="{yg:.1f}"/>')
        destaque = vol == 300_000
        corpo.append(texto(x + largura_barra / 2, y_base - py(jev + ocr) - 26, f"Jev {br(jev, 0)}", "t1", 12, "middle", 600))
        corpo.append(texto(x + largura_barra / 2, y_base - py(jev + ocr) - 10, f"+ OCR {br(ocr, 0)}", "t2", 12, "middle"))
        rotulo = f"{vol // 1000} mil/mês" if vol < 1_000_000 else f"{vol // 1_000_000} milhão/mês"
        corpo.append(texto(x + largura_barra / 2, y_base + 20, rotulo, "t1", 13, "middle", 700 if destaque else 500))
    corpo.append(f'<line class="base" x1="{x_ini - 10}" y1="{y_base}" x2="730" y2="{y_base}"/>')
    return svg(L, A, "Custo mensal projetado por volume", "\n".join(corpo))


def grafico_pipeline(registros) -> str:
    """Diagrama animado do fluxo: os pontos percorrem o caminho de cada tipo de PDF."""
    texto_med = st.median(r["t_extracao_s"] for r in registros if r["metodo_extracao"] == "texto")
    ocr_med = st.median(r["t_extracao_s"] for r in registros if r["metodo_extracao"] != "texto")
    jev_med = st.median(r["t_jev_s"] for r in registros)
    L, A = 860, 300
    caminho_texto = "M120,150 C170,150 180,92 240,92 L420,92 C480,92 490,150 540,150 L660,150"
    caminho_ocr = "M120,150 C170,150 180,208 240,208 L420,208 C480,208 490,150 540,150 L660,150"
    css = """
      .fio{fill:none;stroke-width:2;stroke-dasharray:4 5}
      .ponto-texto{fill:#2a78d6} .ponto-ocr{fill:#eb6834}
      @media (prefers-color-scheme: dark){.ponto-texto{fill:#3987e5} .ponto-ocr{fill:#d95926}}
      @media (prefers-reduced-motion: reduce){.mov{display:none}}
    """
    pontos = []
    # PDFs com texto atravessam rápido; escaneados param na caixa de OCR.
    for i in range(6):
        pontos.append(
            f'<circle class="mov ponto-texto" r="6"><animateMotion dur="2.4s" begin="-{i * 0.8:.1f}s" '
            f'repeatCount="indefinite" path="{caminho_texto}" keyPoints="0;1" keyTimes="0;1" calcMode="linear"/></circle>'
        )
    for i in range(2):
        pontos.append(
            f'<circle class="mov ponto-ocr" r="6"><animateMotion dur="4.8s" begin="-{0.4 + i * 2.4:.1f}s" '
            f'repeatCount="indefinite" path="{caminho_ocr}" keyPoints="0;0.3;0.55;1" keyTimes="0;0.15;0.75;1" '
            f'calcMode="linear"/></circle>'
        )
    caixa = lambda x, y, w, h: f'<rect class="no" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>'
    corpo = [
        texto(24, 34, "Como cada anexo é processado", "t1", 16, peso=600),
        texto(24, 54, "Azul: PDF com camada de texto. Laranja: PDF escaneado, que passa pelo OCR antes.", "t2", 12),
        f'<path class="fio s1s" d="{caminho_texto}"/>',
        f'<path class="fio s2s" d="{caminho_ocr}"/>',
        *pontos,
        caixa(24, 120, 96, 60), texto(72, 146, "PDF", "t1", 14, "middle", 600),
        texto(72, 164, f"{len(registros)} anexos", "mut", 11, "middle"),
        caixa(240, 66, 180, 52), texto(330, 89, "PyMuPDF", "t1", 13, "middle", 600),
        texto(330, 106, f"lê o texto · {br(texto_med, 3)} s", "t2", 11, "middle"),
        caixa(240, 182, 180, 52), texto(330, 205, "OCR Apple Vision", "t1", 13, "middle", 600),
        texto(330, 222, f"imagem → texto · {br(ocr_med, 2)} s", "t2", 11, "middle"),
        caixa(540, 116, 120, 68), texto(600, 143, "Jev", "t1", 15, "middle", 700),
        texto(600, 161, f"{br(jev_med, 2)} s · ~5,2 mil tokens", "t2", 11, "middle"),
        f'<path class="fio base" d="M660,150 L700,150"/>',
        caixa(700, 104, 136, 92), texto(768, 130, "classe", "t1", 13, "middle", 600),
        texto(768, 148, "+ probabilidades", "t2", 11, "middle"),
        texto(768, 164, "+ tempo, tokens", "t2", 11, "middle"),
        texto(768, 180, "+ custo", "t2", 11, "middle"),
        texto(24, 276, "Cada execução grava uma linha por anexo em execucoes/&lt;run_id&gt;/resultados.jsonl", "mut", 11),
    ]
    return svg(L, A, "Fluxo de processamento dos anexos", "\n".join(corpo), css)


def _trecho(arquivo: str, n_linhas=13, largura=40) -> list[str]:
    cache = next((RAIZ / "cache_texto").glob(f"{Path(arquivo).stem}_*.json"))
    linhas = [l.strip() for l in json.loads(cache.read_text())["texto"].splitlines() if l.strip()]
    saida = [l if len(l) <= largura else l[: largura - 1] + "…" for l in linhas[:n_linhas]]
    return [l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for l in saida]


def css_animado(T: int) -> str:
    """CSS base das animações: cartão do documento, trilhos, linha de leitura e selos."""
    return f"""
      .doc{{fill:#f3f2ee;stroke:#c3c2b7}} .mono{{font-family:ui-monospace,Menlo,monospace}}
      .scan{{fill:#2a78d6}} .cinza{{fill:#c3c2b7}} .trilho{{fill:#e1e0d9}}
      .ok{{stroke:#006300;fill:none}} .okt{{fill:#006300}} .rev{{stroke:#eb6834;fill:none}} .revt{{fill:#b5461b}}
      .anim{{transform-box:fill-box;transform-origin:left center;animation-duration:{T}s;
             animation-iteration-count:infinite;animation-timing-function:ease-in-out}}
      @media (prefers-color-scheme: dark){{
        .doc{{fill:#242423;stroke:#383835}} .scan{{fill:#3987e5}} .cinza{{fill:#52514e}}
        .trilho{{fill:#2c2c2a}} .ok{{stroke:#0ca30c}} .okt{{fill:#0ca30c}} .rev{{stroke:#d95926}} .revt{{fill:#e8814f}}
      }}
      @media (prefers-reduced-motion: reduce){{.anim{{animation:none}}}}
    """


class Animacao:
    """Keyframes CSS para animações em loop de dois documentos (cada um ocupa metade do ciclo).

    Os SVGs animados usam CSS (e não SMIL) para respeitar `prefers-reduced-motion`; o estado
    estático de cada elemento (`padrao`) é o fim da fase do primeiro documento.
    """

    def __init__(self, css: list[str]):
        self.css = css
        self.n = 0

    def anima(self, propriedade_por_fase, padrao):
        """Cria keyframes para um elemento. propriedade_por_fase: lista de (percentual, css)."""
        self.n += 1
        nome = f"k{self.n}"
        quadros = " ".join(f"{p}%{{{v}}}" for p, v in propriedade_por_fase)
        self.css.append(f"@keyframes {nome}{{{quadros}}} .{nome}{{animation-name:{nome};{padrao}}}")
        return nome

    @staticmethod
    def fases(valor_inicio, valor_fim_por_doc, chegada=(12, 25), saida=(46, 50)):
        """Gera quadros para os dois documentos: começa em valor_inicio, vai ao valor final
        do documento entre `chegada`, segura e volta ao início entre `saida`."""
        quadros = []
        for i, fim in enumerate(valor_fim_por_doc):
            o = 50 * i
            quadros += [(o, valor_inicio), (o + chegada[0], valor_inicio), (o + chegada[1], fim),
                        (o + saida[0], fim), (o + saida[1] - (0.01 if i else 0), valor_inicio)]
        return quadros

    @staticmethod
    def visivel_na_fase(i, de=0, ate=49):
        """Opacidade 1 só durante a fase do documento i (entre `de` e `ate` % da fase)."""
        o = 50 * i
        q = [(0, "opacity:0"), (100, "opacity:0")]
        q += [(o + de, "opacity:0"), (o + de + 1, "opacity:1"), (o + ate - 1, "opacity:1"), (o + ate, "opacity:0")]
        if i == 0 and de == 0:  # o primeiro documento já aparece no quadro inicial
            q = [(0, "opacity:1")] + [x for x in q if x[0] != 0 and x[0] != 1]
        return sorted(set(q), key=lambda x: x[0])


def grafico_jev(registros, arquivos=("doc_0023.pdf", "doc_0028.pdf"), corte=0.95) -> str:
    """Animação em loop: para cada documento, as 22 probabilidades partem do uniforme e
    convergem para a resposta real do Jev; a confiança decide entre automático e revisão."""
    por_arquivo = {r["arquivo"]: r for r in registros}
    docs = [por_arquivo[a] for a in arquivos]
    n_opcoes = len(docs[0]["probabilidades"])
    uniforme = 1 / n_opcoes

    # Linhas mostradas: as classes com probabilidade em algum dos documentos, completadas
    # com vizinhas plausíveis até 6.
    linhas = []
    for d in docs:
        linhas += [c for c, p in d["probabilidades"].items() if p > 0 and c not in linhas]
    for c in ("decisao_interlocutoria", "ata_audiencia", "termo_acordo", "acordao"):
        if len(linhas) < 6 and c not in linhas:
            linhas.append(c)
    vencedoras = {d["classe"] for d in docs}

    T = 16  # segundos por ciclo; cada documento ocupa metade
    L, A = 860, 430
    bx, bw = 600, 190  # barras: x inicial e largura de 100%
    css = [css_animado(T)]
    animacao = Animacao(css)
    anima, fases, visivel_na_fase = animacao.anima, Animacao.fases, Animacao.visivel_na_fase

    corpo = [
        texto(24, 34, "Como o Jev decide", "t1", 16, peso=600),
        texto(24, 54, f"Antes de ler, as {n_opcoes} opções têm chance igual ({uniforme:.1%}). Depois, a probabilidade se concentra e a confiança decide o destino.".replace(".", ",", 1), "t2", 12),
    ]

    # Documento (cartão com o trecho real, um por fase) e linha de leitura.
    cx, cy, cw, ch = 24, 78, 300, 318
    corpo.append(f'<rect class="doc" x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="8"/>')
    for i, d in enumerate(docs):
        k = anima(visivel_na_fase(i), "opacity:1" if i == 0 else "opacity:0")
        origem = "lido por OCR, com erros" if d["metodo_extracao"] != "texto" else "texto do PDF"
        grupo = [texto(cx + 14, cy + 24, d["arquivo"].replace(".pdf", ""), "t1", 12, peso=600),
                 texto(cx + 14, cy + 40, f"gabarito: {nome(d['gabarito'])} · {origem}", "mut", 11)]
        for j, linha in enumerate(_trecho(d["arquivo"])):
            grupo.append(f'<text x="{cx + 14}" y="{cy + 68 + j * 18}" class="t2 mono" font-size="11">{linha}</text>')
        corpo.append(f'<g class="anim {k}">{"".join(grupo)}</g>')
    k_scan = anima(
        [(0, "transform:translateY(0);opacity:0"), (1, "opacity:.2"), (12, f"transform:translateY({ch - 70}px);opacity:.2"),
         (13, f"transform:translateY({ch - 70}px);opacity:0"),
         (50, "transform:translateY(0);opacity:0"), (51, "opacity:.2"), (62, f"transform:translateY({ch - 70}px);opacity:.2"),
         (63, f"transform:translateY({ch - 70}px);opacity:0"), (100, "opacity:0")],
        "opacity:0",
    )
    corpo.append(f'<rect class="scan anim {k_scan}" x="{cx + 6}" y="{cy + 52}" width="{cw - 12}" height="18" rx="3"/>')

    # Seta e caixa do Jev.
    corpo.append(f'<path class="fio base" d="M{cx + cw + 6},228 L{cx + cw + 30},228" stroke-width="2"/>')
    corpo.append(f'<rect class="no" x="{cx + cw + 30}" y="206" width="72" height="44" rx="10"/>')
    corpo.append(texto(cx + cw + 66, 233, "Jev", "t1", 15, "middle", 700))
    corpo.append(f'<path class="fio base" d="M{cx + cw + 102},228 L{cx + cw + 126},228" stroke-width="2"/>')

    # Barras de probabilidade.
    y0 = 92
    corpo.append(texto(bx - 160, y0 - 6, "probabilidade por classe", "mut", 11))
    for j, classe in enumerate(linhas):
        y = y0 + j * 34
        finais = [d["probabilidades"].get(classe, 0.0) for d in docs]
        corpo.append(texto(bx - 160, y + 15, nome(classe), "t1", 12, peso=500))
        corpo.append(f'<rect class="trilho" x="{bx}" y="{y + 4}" width="{bw}" height="14" rx="3"/>')
        k_cinza = anima(fases(f"transform:scaleX({uniforme:.4f})", ["transform:scaleX(0)"] * len(docs)), "transform:scaleX(0)")
        corpo.append(f'<rect class="cinza anim {k_cinza}" x="{bx}" y="{y + 4}" width="{bw}" height="14" rx="3"/>')
        cor = "s1" if classe in vencedoras else "s2"
        k_cor = anima(fases("transform:scaleX(0)", [f"transform:scaleX({max(p, 0.0001):.4f})" for p in finais]),
                      f"transform:scaleX({max(finais[0], 0.0001):.4f})")
        corpo.append(f'<rect class="{cor} anim {k_cor}" x="{bx}" y="{y + 4}" width="{bw}" height="14" rx="3"/>')
        for i, p in enumerate(finais):
            k = anima(visivel_na_fase(i, 24, 47), "opacity:1" if i == 0 else "opacity:0")
            corpo.append(f'<g class="anim {k}">{texto(bx + bw + 10, y + 15, f"{p:.0%}", "t1" if p else "mut", 12, peso=600 if p else 400)}</g>')
    y_fim = y0 + len(linhas) * 34
    corpo.append(texto(bx - 160, y_fim + 6, f"+ {n_opcoes - len(linhas)} outras opções: 0% nos dois documentos", "mut", 11))

    # Confiança e destino.
    ym = y_fim + 34
    corpo.append(texto(bx - 160, ym + 12, "confiança", "t1", 12, peso=500))
    corpo.append(f'<rect class="trilho" x="{bx}" y="{ym + 2}" width="{bw}" height="12" rx="3"/>')
    xc = bx + bw * corte
    k_conf = anima(fases("transform:scaleX(0)", [f"transform:scaleX({d['confianca']:.3f})" for d in docs], chegada=(25, 30)),
                   f"transform:scaleX({docs[0]['confianca']:.3f})")
    corpo.append(f'<rect class="s1 anim {k_conf}" x="{bx}" y="{ym + 2}" width="{bw}" height="12" rx="3"/>')
    corpo.append(f'<line class="base" x1="{xc:.1f}" y1="{ym - 4}" x2="{xc:.1f}" y2="{ym + 20}" stroke-width="2"/>')
    corpo.append(texto(xc, ym + 34, f"corte {br(corte)}", "mut", 10, "middle"))
    for i, d in enumerate(docs):
        k = anima(visivel_na_fase(i, 30, 47), "opacity:1" if i == 0 else "opacity:0")
        auto = d["confianca"] >= corte
        rotulo = "classificado automaticamente" if auto else "vai para revisão humana"
        caixa = "ok" if auto else "rev"
        simbolo = "✓" if auto else "!"
        grupo = (texto(bx + bw + 10, ym + 12, br(d["confianca"]), "t1", 12, peso=600)
                 + f'<rect class="{caixa}" x="{bx - 160}" y="{ym + 44}" width="{bw + 160}" height="30" rx="15" stroke-width="1.5"/>'
                 + texto(bx - 144, ym + 64, f"{simbolo}  {nome(d['classe'])} · {rotulo}", f"{caixa}t", 13, peso=600))
        corpo.append(f'<g class="anim {k}">{grupo}</g>')

    return svg(L, A, "Como o Jev decide: probabilidades por classe e confiança", "\n".join(corpo), "\n".join(css))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("execucao", type=Path)
    ap.add_argument("--prompt-tokens", type=int, default=4182,
                    help="tokens da requisição com documento vazio (custo fixo do prompt)")
    args = ap.parse_args()
    registros = [json.loads(l) for l in (args.execucao / "resultados.jsonl").read_text().splitlines()]
    registros = [r for r in registros if r["classe"] is not None]

    SAIDA.mkdir(parents=True, exist_ok=True)
    proj = projecao(registros)
    arquivos = {
        "pipeline.svg": grafico_pipeline(registros),
        "como_o_jev_decide.svg": grafico_jev(registros),
        "tempo_por_documento.svg": grafico_tempo(registros),
        "tokens_por_paginas.svg": grafico_tokens(registros, args.prompt_tokens),
        "menor_confianca.svg": grafico_hesitacao(registros),
        "custo_mensal.svg": grafico_custo(proj),
    }
    for nome, conteudo in arquivos.items():
        (SAIDA / nome).write_text(conteudo)
    print(json.dumps(proj, indent=2))
    for v in VOLUMES_MES:
        print(v, "jev", round(v * proj["jev_usd_por_doc"], 2), "ocr", round(v * proj["ocr_nuvem_usd_por_doc"], 2))


if __name__ == "__main__":
    main()
