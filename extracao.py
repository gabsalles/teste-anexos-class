"""Extração de texto dos PDFs: camada de texto quando existe, OCR (Apple Vision) quando não.

O resultado fica em cache por arquivo para que novas execuções do classificador não
refaçam o OCR. O tempo de extração original é guardado no cache e reaproveitado.
"""

import hashlib
import json
import re
import time
from pathlib import Path

import pymupdf
from ocrmac import ocrmac
from PIL import Image

MIN_CHARS_POR_PAGINA = 100  # abaixo disso a página é tratada como imagem
DPI_OCR = 200
CACHE_DIR = Path(__file__).parent / "cache_texto"


def _ocr_pagina(pagina) -> str:
    pix = pagina.get_pixmap(dpi=DPI_OCR)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    linhas = ocrmac.OCR(img, language_preference=["pt-BR"], recognition_level="accurate").recognize()
    return "\n".join(texto for texto, _conf, _bbox in linhas)


def _extrair(caminho: Path) -> dict:
    inicio = time.perf_counter()
    paginas_texto, paginas_ocr = [], 0
    with pymupdf.open(caminho) as doc:
        n_paginas = doc.page_count
        for pagina in doc:
            texto = pagina.get_text()
            if len(texto.strip()) < MIN_CHARS_POR_PAGINA:
                texto = _ocr_pagina(pagina)
                paginas_ocr += 1
            paginas_texto.append(texto)
    texto = re.sub(r"[ \t]+", " ", "\n".join(paginas_texto))
    texto = re.sub(r"\n\s*\n+", "\n\n", texto).strip()
    if paginas_ocr == 0:
        metodo = "texto"
    elif paginas_ocr == n_paginas:
        metodo = "ocr"
    else:
        metodo = "misto"
    return {
        "texto": texto,
        "paginas": n_paginas,
        "paginas_ocr": paginas_ocr,
        "metodo_extracao": metodo,
        "t_extracao_s": round(time.perf_counter() - inicio, 3),
    }


def extrair_texto(caminho: Path, usar_cache: bool = True) -> dict:
    conteudo = caminho.read_bytes()
    chave = hashlib.sha256(conteudo).hexdigest()[:16]
    arquivo_cache = CACHE_DIR / f"{caminho.stem}_{chave}.json"
    if usar_cache and arquivo_cache.exists():
        dados = json.loads(arquivo_cache.read_text())
        dados["extracao_cache"] = True
        return dados
    dados = _extrair(caminho)
    CACHE_DIR.mkdir(exist_ok=True)
    arquivo_cache.write_text(json.dumps(dados, ensure_ascii=False))
    dados["extracao_cache"] = False
    return dados
