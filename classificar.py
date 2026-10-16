"""Classifica anexos jurídicos (PDF) com o Jev e registra métricas de cada documento.

Uso:
    python classificar.py anexos_juridicos_teste/pdfs \
        --gabarito anexos_juridicos_teste/manifest.csv [--limite 20] [--concorrencia 8]

Cada execução grava em execucoes/<run_id>/:
    resultados.jsonl  uma linha por documento (classe, probabilidades, tempos, tokens, custo)
    resumo.json       totais e médias da execução
"""

import argparse
import asyncio
import csv
import json
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy, TypeSafeError

from extracao import extrair_texto
from taxonomia import PERGUNTA_TIPO, PROMPT_HASH

RAIZ = Path(__file__).parent
load_dotenv(RAIZ / ".env")

# Preço público em docs.typesafe.ai/models (consultado em 2026-10-16). Saída é gratuita.
USD_POR_TOKEN_ENTRADA = 0.042 / 1_000_000
USD_POR_TOKEN_SAIDA = 0.0

# Limite de 32k tokens por pergunta. Documentos maiores mantêm o início e o fim,
# onde ficam título, partes, pedidos, dispositivo e assinatura.
LIMITE_CHARS = 60_000
FRACAO_INICIO = 0.7


def preparar_texto(texto: str) -> tuple[str, bool]:
    if len(texto) <= LIMITE_CHARS:
        return texto, False
    n_inicio = int(LIMITE_CHARS * FRACAO_INICIO)
    n_fim = LIMITE_CHARS - n_inicio
    return f"{texto[:n_inicio]}\n\n[... trecho omitido ...]\n\n{texto[-n_fim:]}", True


def carregar_gabarito(caminho: Path | None) -> dict[str, dict]:
    if not caminho:
        return {}
    with caminho.open(newline="") as f:
        return {linha["arquivo"]: linha for linha in csv.DictReader(f)}


async def classificar_documento(cliente, semaforo, caminho: Path, extraido: dict, gabarito: dict) -> dict:
    texto, truncado = preparar_texto(extraido["texto"])
    origem = "OCR (pode conter erros)" if extraido["metodo_extracao"] != "texto" else "camada de texto do PDF"
    registro = {
        "arquivo": caminho.name,
        "paginas": extraido["paginas"],
        "metodo_extracao": extraido["metodo_extracao"],
        "paginas_ocr": extraido["paginas_ocr"],
        "chars": len(extraido["texto"]),
        "truncado": truncado,
        "t_extracao_s": extraido["t_extracao_s"],
        "extracao_cache": extraido["extracao_cache"],
    }
    async with semaforo:
        inicio = time.perf_counter()
        try:
            resp = await cliente.system_one(
                state={"documento": {"texto": texto, "paginas": extraido["paginas"], "origem_texto": origem}},
                questions={"tipo": PERGUNTA_TIPO},
            )
            erro = None
        except TypeSafeError as e:
            resp, erro = None, f"{type(e).__name__}: {e}"
        registro["t_jev_s"] = round(time.perf_counter() - inicio, 3)
        registro["timestamp"] = datetime.now(timezone.utc).isoformat()

    if resp is None:
        registro.update(erro=erro, classe=None)
    else:
        resposta = resp.choices["tipo"]
        probs = dict(sorted(resposta.probabilities.items(), key=lambda kv: -kv[1]))
        tokens_in, tokens_out = resp.usage.input_tokens, resp.usage.output_tokens
        registro.update(
            erro=None,
            modelo=resp.model,
            request_id=resp.request_id,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            custo_usd=tokens_in * USD_POR_TOKEN_ENTRADA + tokens_out * USD_POR_TOKEN_SAIDA,
            classe=resposta.choice,
            confianca=resposta.confidence,
            prob_classe=probs[resposta.choice],
            top3=list(probs.items())[:3],
            probabilidades=probs,
        )

    if caminho.name in gabarito:
        esperado = gabarito[caminho.name]
        registro["gabarito"] = esperado["rotulo"]
        registro["acerto"] = registro["classe"] == esperado["rotulo"]
        for campo in ("subtipo", "justica", "sistema_carimbo", "escaneado", "nivel_ruido", "camada_texto"):
            registro[f"gab_{campo}"] = esperado[campo]
    return registro


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))]


def resumir(registros: list[dict], meta: dict) -> dict:
    ok = [r for r in registros if r["classe"] is not None]
    lat = [r["t_jev_s"] for r in ok]
    ext = [r["t_extracao_s"] for r in registros]
    custo = sum(r["custo_usd"] for r in ok)
    resumo = {
        **meta,
        "docs": len(registros),
        "docs_ok": len(ok),
        "docs_erro": len(registros) - len(ok),
        "docs_ocr": sum(r["metodo_extracao"] != "texto" for r in registros),
        "docs_truncados": sum(r["truncado"] for r in registros),
        "modelos": sorted({r["modelo"] for r in ok}),
        "tokens_entrada": sum(r["input_tokens"] for r in ok),
        "tokens_saida": sum(r["output_tokens"] for r in ok),
        "custo_usd_total": round(custo, 6),
        "custo_usd_por_doc": round(custo / len(ok), 8) if ok else None,
        "custo_usd_por_1000_docs": round(1000 * custo / len(ok), 4) if ok else None,
        "t_extracao_s": {"total": round(sum(ext), 2), "media": round(statistics.mean(ext), 3) if ext else None},
        "t_jev_s": {
            "media": round(statistics.mean(lat), 3) if lat else None,
            "p50": percentil(lat, 50),
            "p95": percentil(lat, 95),
            "max": max(lat, default=None),
        },
        "confianca_media": round(statistics.mean(r["confianca"] for r in ok), 3) if ok else None,
    }
    avaliados = [r for r in ok if "acerto" in r]
    if avaliados:
        resumo["acuracia"] = round(sum(r["acerto"] for r in avaliados) / len(avaliados), 4)
        resumo["docs_avaliados"] = len(avaliados)
    return resumo


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", type=Path, help="pasta com os PDFs")
    ap.add_argument("--gabarito", type=Path, help="CSV com colunas arquivo,rotulo,... para medir acerto")
    ap.add_argument("--modelo", default=None, help="modelo Jev (padrão: jev-latest)")
    ap.add_argument("--concorrencia", type=int, default=8, help="requisições simultâneas ao Jev")
    ap.add_argument("--limite", type=int, default=None, help="classifica só os N primeiros PDFs")
    ap.add_argument("--sem-cache", action="store_true", help="refaz a extração/OCR")
    ap.add_argument("--rotulo", default="", help="anotação livre gravada no resumo (ex.: 'prompt v2')")
    args = ap.parse_args()

    pdfs = sorted(args.pasta.glob("*.pdf"))[: args.limite]
    gabarito = carregar_gabarito(args.gabarito)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    saida = RAIZ / "execucoes" / run_id
    saida.mkdir(parents=True)
    inicio_execucao = time.perf_counter()

    # Fase 1: extração sequencial (OCR usa CPU/GPU local).
    print(f"[{run_id}] extraindo texto de {len(pdfs)} PDFs...")
    extraidos = {}
    for i, pdf in enumerate(pdfs, 1):
        extraidos[pdf] = extrair_texto(pdf, usar_cache=not args.sem_cache)
        if i % 25 == 0 or i == len(pdfs):
            print(f"  {i}/{len(pdfs)}")
    t_fase_extracao = time.perf_counter() - inicio_execucao

    # Fase 2: classificação concorrente.
    print(f"[{run_id}] classificando com concorrência {args.concorrencia}...")
    inicio_classificacao = time.perf_counter()
    semaforo = asyncio.Semaphore(args.concorrencia)
    retry = RetryPolicy(max_retries=4, backoff_max=20.0, timeout=60.0)
    registros = []
    async with AsyncTypeSafeClient(model=args.modelo, retry=retry) as cliente:
        tarefas = [classificar_documento(cliente, semaforo, p, extraidos[p], gabarito) for p in pdfs]
        with (saida / "resultados.jsonl").open("w") as f:
            for i, tarefa in enumerate(asyncio.as_completed(tarefas), 1):
                registro = await tarefa
                registro["run_id"] = run_id
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                f.flush()
                registros.append(registro)
                if i % 25 == 0 or i == len(pdfs):
                    print(f"  {i}/{len(pdfs)}")
    t_fase_classificacao = time.perf_counter() - inicio_classificacao

    meta = {
        "run_id": run_id,
        "rotulo": args.rotulo,
        "inicio": datetime.now(timezone.utc).isoformat(),
        "modelo_solicitado": args.modelo or "jev-latest",
        "prompt_hash": PROMPT_HASH,
        "concorrencia": args.concorrencia,
        "pasta": str(args.pasta),
        "t_fase_extracao_s": round(t_fase_extracao, 2),
        "t_fase_classificacao_s": round(t_fase_classificacao, 2),
        "t_total_s": round(time.perf_counter() - inicio_execucao, 2),
        "docs_por_minuto_classificacao": round(60 * len(pdfs) / t_fase_classificacao, 1) if pdfs else None,
    }
    resumo = resumir(registros, meta)
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"\nResultados em {saida.relative_to(RAIZ)}/")


if __name__ == "__main__":
    asyncio.run(main())
