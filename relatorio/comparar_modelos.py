"""Compara duas execuções (Jev × Microsoft-Decision-1) sobre os mesmos anexos.

Uso:
    python relatorio/comparar_modelos.py execucoes/<run_jev> execucoes/<run_microsoft> \
        [--prompt-tokens-jev 4182] [--prompt-tokens-microsoft 2895]

Gera:
    execucoes/comparativo.json        números usados no README
    docs/graficos/comparativo_*.svg   gráficos (um deles animado)
"""

import argparse
import hashlib
import json
import math
import statistics as st
from pathlib import Path

from gerar_graficos import (
    RAIZ, SAIDA, VOLUMES_MES, Animacao, _trecho, barra_h, barra_v, br, css_animado, legenda, nome, svg, texto,
)

MODELOS = ("jev", "microsoft")
ROTULO = {"jev": "Jev", "microsoft": "Microsoft-Decision-1"}
COR = {"jev": "s1", "microsoft": "s2"}  # cor fixa por modelo em todos os gráficos de comparação
CORTE = 0.95

# Caminho de cada chamada. A latência medida inclui tudo entre o script e a resposta, então
# o tempo da Microsoft via OpenRouter não é só o tempo do modelo.
ACESSO = {"jev": "API da TypeSafe, direto", "microsoft": "OpenRouter → Azure"}
AVISO_LATENCIA = (
    "A latência da Microsoft foi medida pelo OpenRouter, que fica entre o script e a Azure; a do Jev "
    "foi medida na API da TypeSafe, direto. A diferença de tempo pode vir em parte desse caminho extra "
    "e não deve ser lida como tempo do modelo. Chamar a Microsoft direto na Azure "
    "(<recurso>/providers/microsoft/v1/systemone) daria a comparação justa."
)

CSS_AVISO = """
  .aviso{fill:#b5461b} .aviso-bg{fill:#b5461b} .aviso-tx{fill:#fcfcfb}
  @media (prefers-color-scheme: dark){ .aviso{fill:#e8814f} .aviso-bg{fill:#e8814f} .aviso-tx{fill:#1a1a19} }
"""

CSS_ESTATICO = """
  .trilho{fill:#e1e0d9} .ponto{fill:#52514e;fill-opacity:.55;stroke:#fcfcfb;stroke-width:1}
  .ref{stroke:#c3c2b7;stroke-dasharray:4 4;fill:none}
  @media (prefers-color-scheme: dark){
    .trilho{fill:#2c2c2a} .ponto{fill:#c3c2b7;stroke:#1a1a19} .ref{stroke:#383835}
  }
"""


def carregar(pasta: Path) -> tuple[dict, dict]:
    registros = {}
    for linha in (pasta / "resultados.jsonl").read_text().splitlines():
        r = json.loads(linha)
        r["t_s"] = r.get("t_modelo_s", r.get("t_jev_s"))
        registros[r["arquivo"]] = r
    return registros, json.loads((pasta / "resumo.json").read_text())


def pct(p: float) -> str:
    if p >= 0.9995:
        return "100%"
    if p < 0.0005:
        return "0%"
    return f"{p * 100:.1f}%".replace(".", ",")


def percentil(valores, p):
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))]


# ---------------------------------------------------------------- números


def calcular(dados: dict, resumos: dict, prompt_tokens: dict) -> dict:
    comuns = sorted(set(dados["jev"]) & set(dados["microsoft"]))
    saida = {"docs": len(comuns), "modelos": {}}
    for m in MODELOS:
        regs = [dados[m][a] for a in comuns]
        ok = [r for r in regs if r["classe"] is not None]
        conf = [r["confianca"] for r in ok]
        lat = [r["t_s"] for r in ok]
        tokens = [r["input_tokens"] for r in ok]
        custo_doc = sum(r["custo_usd"] for r in ok) / len(ok)
        saida["modelos"][m] = {
            "run_id": resumos[m]["run_id"],
            "modelo": sorted({r["modelo"] for r in ok}),
            "acesso": ACESSO[m],
            "acertos": sum(r.get("acerto", False) for r in ok),
            "erros_api": len(regs) - len(ok),
            "confianca_media": round(st.mean(conf), 4),
            "confianca_min": round(min(conf), 3),
            "docs_conf_abaixo_095": sum(c < 0.95 for c in conf),
            "docs_conf_abaixo_099": sum(c < 0.99 for c in conf),
            "latencia_s": {"media": round(st.mean(lat), 3), "p50": round(st.median(lat), 3),
                           "p95": round(percentil(lat, 95), 3), "max": round(max(lat), 3)},
            "docs_por_minuto": resumos[m].get("docs_por_minuto_classificacao"),
            "tokens_media": round(st.mean(tokens)),
            "prompt_fixo_tokens": prompt_tokens[m],
            "custo_usd_total": round(sum(r["custo_usd"] for r in ok), 6),
            "custo_usd_por_1000_docs": round(1000 * custo_doc, 4),
            "custo_usd_mes": {str(v): round(v * custo_doc, 2) for v in VOLUMES_MES},
            "menor_confianca": [[a, round(dados[m][a]["confianca"], 3)]
                                for a in sorted(comuns, key=lambda a: dados[m][a]["confianca"])[:5]],
        }
    divergentes = [a for a in comuns if dados["jev"][a]["classe"] != dados["microsoft"][a]["classe"]]
    saida["divergencias"] = divergentes
    inc = {m: [1 - dados[m][a]["confianca"] for a in comuns] for m in MODELOS}
    mj, mm = st.mean(inc["jev"]), st.mean(inc["microsoft"])
    cov = sum((x - mj) * (y - mm) for x, y in zip(inc["jev"], inc["microsoft"]))
    var = math.sqrt(sum((x - mj) ** 2 for x in inc["jev"]) * sum((y - mm) ** 2 for y in inc["microsoft"]))
    saida["correlacao_incerteza"] = round(cov / var, 3) if var else None
    saida["ambos_conf_099"] = sum(dados["jev"][a]["confianca"] >= 0.99 and dados["microsoft"][a]["confianca"] >= 0.99
                                  for a in comuns)
    j, mi = saida["modelos"]["jev"], saida["modelos"]["microsoft"]
    saida["razao_tokens_microsoft_jev"] = round(mi["tokens_media"] / j["tokens_media"], 3)
    saida["aviso_latencia"] = AVISO_LATENCIA
    return saida


# ---------------------------------------------------------------- gráficos


def _jitter(arquivo: str, amplitude: float) -> float:
    h = int(hashlib.md5(arquivo.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return (h - 0.5) * 2 * amplitude


def grafico_latencia(dados, numeros) -> str:
    L, A = 760, 310
    x0, x1 = 210, 720
    g0, g1 = 116, 264  # faixa vertical do gráfico
    lat_max = max(r["t_s"] for m in MODELOS for r in dados[m].values())
    escala = math.ceil(lat_max * 2) / 2  # arredonda para o 0,5 s acima
    px = lambda s: x0 + (x1 - x0) * s / escala
    corpo = [
        texto(24, 34, "Tempo de resposta por anexo (segundos)", "t1", 16, peso=600),
        texto(24, 54, "Cada ponto é um anexo; o traço marca a mediana.", "t2", 12),
        # Aviso: o caminho da Microsoft passa pelo OpenRouter.
        '<circle class="aviso-bg" cx="32" cy="76" r="8"/>',
        texto(32, 80.5, "!", "aviso-tx", 12, "middle", 700),
        texto(46, 80, "Atenção: o tempo da Microsoft inclui a passagem pelo OpenRouter até a Azure; o Jev foi chamado direto.", "aviso", 12, peso=600),
        texto(46, 97, "Parte da diferença pode ser esse caminho extra. Não leia como tempo do modelo.", "t2", 12),
    ]
    passo = 0.5
    for i in range(int(escala / passo) + 1):
        s = i * passo
        corpo.append(f'<line class="grid" x1="{px(s):.1f}" y1="{g0}" x2="{px(s):.1f}" y2="{g1}"/>')
        corpo.append(texto(px(s), g1 + 20, br(s, 1), "mut", 11, "middle"))
    for k, m in enumerate(MODELOS):
        yc = g0 + 34 + k * 70
        n = numeros["modelos"][m]["latencia_s"]
        corpo.append(texto(24, yc - 8, ROTULO[m], "t1", 13, peso=600))
        classe_acesso = "aviso" if m == "microsoft" else "mut"
        corpo.append(texto(24, yc + 8, ACESSO[m], classe_acesso, 11, peso=600 if m == "microsoft" else 400))
        corpo.append(texto(24, yc + 23, f"mediana {br(n['p50'])} s · p95 {br(n['p95'])} s", "mut", 11))
        for a, r in dados[m].items():
            corpo.append(f'<circle class="{COR[m]}" cx="{px(r["t_s"]):.1f}" cy="{yc + _jitter(a, 16):.1f}" r="3.2" '
                         f'fill-opacity=".55"/>')
        xm = px(n["p50"])
        corpo.append(f'<rect class="t1" x="{xm - 1:.1f}" y="{yc - 24}" width="2" height="48"/>')
    corpo.append(f'<line class="base" x1="{x0}" y1="{g0}" x2="{x0}" y2="{g1}"/>')
    return svg(L, A, "Tempo de resposta por anexo: Jev e Microsoft-Decision-1 (via OpenRouter)", "\n".join(corpo), CSS_AVISO)


def grafico_confianca(dados, numeros) -> str:
    L, A = 760, 520
    x0, x1, y0, y1 = 110, 700, 450, 100  # y0 é a base (valor mínimo)
    lo = math.floor(min(min(r["confianca"] for r in dados[m].values()) for m in MODELOS) * 20) / 20
    px = lambda c: x0 + (x1 - x0) * (c - lo) / (1 - lo)
    py = lambda c: y0 - (y0 - y1) * (c - lo) / (1 - lo)
    corpo = [
        texto(24, 34, "Onde cada modelo hesitou", "t1", 16, peso=600),
        texto(24, 54, f"Cada ponto é um anexo: confiança do Jev (horizontal) × da Microsoft (vertical). Os dois acertaram todos.", "t2", 12),
        texto(24, 72, f"Correlação entre as incertezas: {br(numeros['correlacao_incerteza'])}. Na maioria dos casos difíceis, só um dos dois teve dúvida.", "t2", 12),
    ]
    passo = 0.05
    n_passos = round((1 - lo) / passo)
    for i in range(n_passos + 1):
        c = lo + i * passo
        corpo.append(f'<line class="grid" x1="{px(c):.1f}" y1="{y1}" x2="{px(c):.1f}" y2="{y0}"/>')
        corpo.append(f'<line class="grid" x1="{x0}" y1="{py(c):.1f}" x2="{x1}" y2="{py(c):.1f}"/>')
        corpo.append(texto(px(c), y0 + 18, br(c), "mut", 11, "middle"))
        corpo.append(texto(x0 - 10, py(c) + 4, br(c), "mut", 11, "end"))
    corpo.append(f'<line class="ref" x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(1):.1f}" y2="{py(1):.1f}"/>')
    corpo.append(texto(px(lo + 0.012), py(lo + 0.004) - 6, "mesma confiança", "mut", 10))
    corpo.append(texto((x0 + x1) / 2, y0 + 40, "confiança do Jev", "t1", 12, "middle", 500))
    corpo.append(f'<text x="34" y="{(y0 + y1) / 2:.1f}" class="t1" font-size="12" font-weight="500" text-anchor="middle" '
                 f'transform="rotate(-90 34 {(y0 + y1) / 2:.1f})">confiança da Microsoft</text>')
    # Faixas de corte: abaixo de 0,95 iria para revisão.
    corpo.append(f'<line class="base" x1="{px(CORTE):.1f}" y1="{y1}" x2="{px(CORTE):.1f}" y2="{y0}" stroke-dasharray="2 3"/>')
    corpo.append(f'<line class="base" x1="{x0}" y1="{py(CORTE):.1f}" x2="{x1}" y2="{py(CORTE):.1f}" stroke-dasharray="2 3"/>')
    corpo.append(texto(px(CORTE) + 6, y0 - 8, f"corte {br(CORTE)}", "mut", 10))
    comuns = sorted(set(dados["jev"]) & set(dados["microsoft"]))
    rotulados = []
    for a in comuns:
        cj, cm = dados["jev"][a]["confianca"], dados["microsoft"][a]["confianca"]
        corpo.append(f'<circle class="ponto" cx="{px(cj):.1f}" cy="{py(cm):.1f}" r="5"/>')
        if min(cj, cm) < CORTE:
            rotulados.append((a, cj, cm))
    # Pontos colados no topo ganham rótulo abaixo, alternando a altura para não se sobreporem.
    no_topo = 0
    for a, cj, cm in sorted(rotulados, key=lambda t: t[1]):
        rotulo = f"{a[:-4]} · {nome(dados['jev'][a]['gabarito'])}"
        if cm >= 0.99:
            dy = 20 + 15 * (no_topo % 2)
            no_topo += 1
            corpo.append(texto(px(cj), py(cm) + dy, a[:-4], "t2", 11, "middle"))
        elif px(cj) > x1 - 150:
            corpo.append(texto(px(cj) - 10, py(cm) + 4, rotulo, "t2", 11, "end"))
        else:
            corpo.append(texto(px(cj) + 10, py(cm) + 4, rotulo, "t2", 11))
    corpo.append(texto(px(1) - 12, py(0.978), f"{numeros['ambos_conf_099']} anexos no canto", "t1", 12, "end", 600))
    corpo.append(texto(px(1) - 12, py(0.978) + 16, "(os dois com confiança ≥ 0,99)", "mut", 11, "end"))
    corpo.append(f'<line class="base" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    return svg(L, A, "Confiança do Jev versus da Microsoft por anexo", "\n".join(corpo), CSS_ESTATICO)


def grafico_menor_confianca(dados, limite=0.97) -> str:
    comuns = sorted(set(dados["jev"]) & set(dados["microsoft"]))
    docs = [a for a in comuns if min(dados[m][a]["confianca"] for m in MODELOS) < limite]
    docs.sort(key=lambda a: min(dados[m][a]["confianca"] for m in MODELOS))
    L = 760
    A = 110 + len(docs) * 58 + 16
    x0, bw = 220, 260
    corpo = [
        texto(24, 34, "Os anexos em que algum modelo ficou abaixo de 97%", "t1", 16, peso=600),
        texto(24, 54, "Probabilidade que cada modelo deu à classe escolhida (correta em todos) e a segunda opção dele.", "t2", 12),
        legenda(24, 84, [(COR[m], ROTULO[m]) for m in MODELOS]),
    ]
    for i, a in enumerate(docs):
        y = 104 + i * 58
        corpo.append(texto(24, y + 14, a[:-4], "t1", 13, peso=500))
        corpo.append(texto(24, y + 30, "gabarito: " + nome(dados["jev"][a]["gabarito"]), "mut", 11))
        for k, m in enumerate(MODELOS):
            r = dados[m][a]
            yb = y + 2 + k * 22
            p1 = r["top3"][0][1]
            c2, p2 = r["top3"][1]
            corpo.append(f'<rect class="trilho" x="{x0}" y="{yb}" width="{bw}" height="16" rx="3"/>')
            corpo.append(barra_h(x0, yb, bw * p1, 16, COR[m], arredonda_fim=True))
            corpo.append(texto(x0 + bw + 10, yb + 12.5, f"{pct(p1)}", "t1", 12, peso=600))
            corpo.append(texto(x0 + bw + 62, yb + 12.5, f"2ª: {nome(c2)} {pct(p2)}", "t2", 11))
    return svg(L, A, "Anexos de menor confiança em cada modelo", "\n".join(corpo), CSS_ESTATICO)


def grafico_custo(numeros) -> str:
    L, A = 760, 340
    y_base, y_topo = 270, 110
    valores = {m: numeros["modelos"][m]["custo_usd_mes"] for m in MODELOS}
    escala = math.ceil(max(max(v.values()) for v in valores.values()) / 50) * 50
    py = lambda usd: (y_base - y_topo) * usd / escala
    tok = numeros["modelos"]
    corpo = [
        texto(24, 34, "Custo mensal do modelo por volume (US$)", "t1", 16, peso=600),
        texto(24, 54, f"Mesmo preço por token (US$ 0,042/milhão). A Microsoft conta {round((1 - numeros['razao_tokens_microsoft_jev']) * 100)}% menos tokens para o mesmo texto e a mesma taxonomia.", "t2", 12),
        legenda(24, 84, [(COR[m], ROTULO[m]) for m in MODELOS]),
    ]
    x_ini = 90
    for usd in range(0, escala + 1, 50):
        y = y_base - py(usd)
        corpo.append(f'<line class="grid" x1="{x_ini - 10}" y1="{y:.1f}" x2="730" y2="{y:.1f}"/>')
        corpo.append(texto(x_ini - 16, y + 4, f"{usd}", "mut", 11, "end"))
    largura, gap, passo = 64, 4, 210
    for i, vol in enumerate(VOLUMES_MES):
        xg = x_ini + 40 + i * passo
        for k, m in enumerate(MODELOS):
            v = valores[m][str(vol)]
            x = xg + k * (largura + gap)
            corpo.append(barra_v(x, y_base, largura, py(v), COR[m], arredonda_topo=True))
            corpo.append(texto(x + largura / 2, y_base - py(v) - 8, br(v, 0), "t1", 12, "middle", 600))
        rotulo = f"{vol // 1000} mil/mês" if vol < 1_000_000 else f"{vol // 1_000_000} milhão/mês"
        corpo.append(texto(xg + largura + gap / 2, y_base + 20, rotulo, "t1", 13, "middle", 700 if vol == 300_000 else 500))
    corpo.append(f'<line class="base" x1="{x_ini - 10}" y1="{y_base}" x2="730" y2="{y_base}"/>')
    corpo.append(texto(24, A - 18, f"Tokens por anexo: Jev {br(tok['jev']['tokens_media'], 0)} (prompt fixo {br(tok['jev']['prompt_fixo_tokens'], 0)}) · "
                                   f"Microsoft {br(tok['microsoft']['tokens_media'], 0)} (prompt fixo {br(tok['microsoft']['prompt_fixo_tokens'], 0)})", "mut", 11))
    return svg(L, A, "Custo mensal por volume: Jev e Microsoft-Decision-1", "\n".join(corpo))


def grafico_duelo(dados, arquivos) -> str:
    """Animação: o mesmo anexo lido pelos dois modelos; as 22 probabilidades de cada um partem
    do uniforme e convergem lado a lado, e a confiança de cada modelo decide o destino."""
    docs = [{m: dados[m][a] for m in MODELOS} for a in arquivos]
    n_opcoes = len(docs[0]["jev"]["probabilidades"])
    uniforme = 1 / n_opcoes
    linhas = []
    for d in docs:
        for m in MODELOS:
            linhas += [c for c, p in d[m]["probabilidades"].items() if p >= 0.005 and c not in linhas]
    for c in ("sentenca", "ata_audiencia", "oficio", "mandado"):
        if len(linhas) < 5 and c not in linhas:
            linhas.append(c)

    T = 16
    L, A = 860, 500
    bx, bw = 500, 170
    css = [css_animado(T)]
    animacao = Animacao(css)
    anima, fases, visivel = animacao.anima, Animacao.fases, Animacao.visivel_na_fase

    corpo = [
        texto(24, 34, "Mesmo anexo, dois modelos", "t1", 16, peso=600),
        texto(24, 54, "As 22 opções partem de chance igual. Os dois escolhem a mesma classe, mas hesitam em anexos diferentes.", "t2", 12),
        legenda(bx - 146, 84, [(COR[m], ROTULO[m]) for m in MODELOS]),
    ]

    cx, cy, cw, ch = 24, 78, 300, 318
    corpo.append(f'<rect class="doc" x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="8"/>')
    for i, d in enumerate(docs):
        r = d["jev"]
        k = anima(visivel(i), "opacity:1" if i == 0 else "opacity:0")
        origem = "lido por OCR, com erros" if r["metodo_extracao"] != "texto" else "texto do PDF"
        grupo = [texto(cx + 14, cy + 24, r["arquivo"][:-4], "t1", 12, peso=600),
                 texto(cx + 14, cy + 40, f"gabarito: {nome(r['gabarito'])} · {origem}", "mut", 11)]
        for j, linha in enumerate(_trecho(r["arquivo"])):
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
    corpo.append(f'<path class="fio base" d="M{cx + cw + 8},{cy + ch / 2} L{bx - 152},{cy + ch / 2}" stroke-width="2"/>')

    y0 = 104
    passo = 46
    for j, classe in enumerate(linhas):
        y = y0 + j * passo
        corpo.append(texto(bx - 146, y + 18, nome(classe), "t1", 12, peso=500))
        for k, m in enumerate(MODELOS):
            yb = y + 4 + k * 16
            finais = [d[m]["probabilidades"].get(classe, 0.0) for d in docs]
            corpo.append(f'<rect class="trilho" x="{bx}" y="{yb}" width="{bw}" height="11" rx="3"/>')
            k_cinza = anima(fases(f"transform:scaleX({uniforme:.4f})", ["transform:scaleX(0)"] * len(docs)), "transform:scaleX(0)")
            corpo.append(f'<rect class="cinza anim {k_cinza}" x="{bx}" y="{yb}" width="{bw}" height="11" rx="3"/>')
            k_cor = anima(fases("transform:scaleX(0)", [f"transform:scaleX({max(p, 0.0001):.4f})" for p in finais]),
                          f"transform:scaleX({max(finais[0], 0.0001):.4f})")
            corpo.append(f'<rect class="{COR[m]} anim {k_cor}" x="{bx}" y="{yb}" width="{bw}" height="11" rx="3"/>')
            for i, p in enumerate(finais):
                kt = anima(visivel(i, 24, 47), "opacity:1" if i == 0 else "opacity:0")
                corpo.append(f'<g class="anim {kt}">{texto(bx + bw + 10, yb + 10, pct(p), "t1" if p >= 0.005 else "mut", 11, peso=600 if p >= 0.005 else 400)}</g>')
    y_fim = y0 + len(linhas) * passo
    corpo.append(texto(bx - 146, y_fim + 4, f"+ {n_opcoes - len(linhas)} outras opções com menos de 0,5% nos dois modelos", "mut", 11))

    # Confiança de cada modelo e destino com o corte de 0,95.
    ym = y_fim + 28
    xc = bx + bw * CORTE
    for k, m in enumerate(MODELOS):
        yb = ym + k * 34
        corpo.append(texto(bx - 146, yb + 11, f"confiança {ROTULO[m].split('-')[0]}", "t1", 12, peso=500))
        corpo.append(f'<rect class="trilho" x="{bx}" y="{yb + 1}" width="{bw}" height="12" rx="3"/>')
        k_conf = anima(fases("transform:scaleX(0)", [f"transform:scaleX({d[m]['confianca']:.3f})" for d in docs], chegada=(25, 30)),
                       f"transform:scaleX({docs[0][m]['confianca']:.3f})")
        corpo.append(f'<rect class="{COR[m]} anim {k_conf}" x="{bx}" y="{yb + 1}" width="{bw}" height="12" rx="3"/>')
        corpo.append(f'<line class="base" x1="{xc:.1f}" y1="{yb - 3}" x2="{xc:.1f}" y2="{yb + 17}" stroke-width="2"/>')
        for i, d in enumerate(docs):
            kt = anima(visivel(i, 30, 47), "opacity:1" if i == 0 else "opacity:0")
            auto = d[m]["confianca"] >= CORTE
            destino = "automático" if auto else "revisão humana"
            classe_txt = "okt" if auto else "revt"
            simbolo = "✓" if auto else "!"
            corpo.append(f'<g class="anim {kt}">{texto(bx + bw + 10, yb + 11, br(d[m]["confianca"]), "t1", 12, peso=600)}'
                         f'{texto(bx + bw + 52, yb + 11, f"{simbolo} {destino}", classe_txt, 12, peso=600)}</g>')
    corpo.append(texto(xc, ym + 82, f"corte {br(CORTE)}", "mut", 10, "middle"))
    return svg(L, A, "Mesmo anexo, dois modelos: Jev e Microsoft-Decision-1", "\n".join(corpo), "\n".join(css))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("execucao_jev", type=Path)
    ap.add_argument("execucao_microsoft", type=Path)
    ap.add_argument("--prompt-tokens-jev", type=int, default=4182,
                    help="tokens da requisição com documento vazio no Jev")
    ap.add_argument("--prompt-tokens-microsoft", type=int, default=2895,
                    help="tokens da requisição com documento vazio na Microsoft")
    ap.add_argument("--duelo", nargs=2, default=None, metavar="ARQUIVO",
                    help="anexos da animação (padrão: o de menor confiança de cada modelo)")
    args = ap.parse_args()

    dados, resumos = {}, {}
    for m, pasta in zip(MODELOS, (args.execucao_jev, args.execucao_microsoft)):
        dados[m], resumos[m] = carregar(pasta)
    numeros = calcular(dados, resumos, {"jev": args.prompt_tokens_jev, "microsoft": args.prompt_tokens_microsoft})
    duelo = args.duelo or [numeros["modelos"][m]["menor_confianca"][0][0] for m in MODELOS]

    SAIDA.mkdir(parents=True, exist_ok=True)
    graficos = {
        "comparativo_duelo.svg": grafico_duelo(dados, duelo),
        "comparativo_latencia.svg": grafico_latencia(dados, numeros),
        "comparativo_confianca.svg": grafico_confianca(dados, numeros),
        "comparativo_menor_confianca.svg": grafico_menor_confianca(dados),
        "comparativo_custo.svg": grafico_custo(numeros),
    }
    for nome_arquivo, conteudo in graficos.items():
        (SAIDA / nome_arquivo).write_text(conteudo)
    (RAIZ / "execucoes" / "comparativo.json").write_text(json.dumps(numeros, ensure_ascii=False, indent=2))
    print(json.dumps(numeros, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
