"""Classifica os mesmos anexos com o Microsoft-Decision-1 (via OpenRouter) e registra métricas.

Envia exatamente a mesma pergunta `Choice` do Jev (taxonomia.py) e o mesmo texto extraído
(cache de extracao.py), para que a comparação isole o modelo.

Atenção: `t_modelo_s` mede o tempo até a resposta do OpenRouter, que repassa a requisição para a
Azure. Ele inclui esse intermediário e não é só o tempo do modelo; para medir o modelo, chame a
Azure direto (<recurso>/providers/microsoft/v1/systemone).

Uso:
    python classificar_microsoft.py anexos_juridicos_teste/pdfs \
        --gabarito anexos_juridicos_teste/manifest.csv [--limite 20] [--concorrencia 8]

Cada execução grava em execucoes/<run_id>/ os mesmos arquivos do classificar.py:
    resultados.jsonl  uma linha por documento (classe, probabilidades, tempos, tokens, custo)
    resumo.json       totais e médias da execução
"""

import argparse
import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from classificar import RAIZ, carregar_gabarito, preparar_texto, resumir
from extracao import extrair_texto
from taxonomia import CLASSES, INSTRUCOES, PROMPT_HASH

URL = "https://openrouter.ai/api/alpha/decisions"
MODELO_PADRAO = "microsoft/microsoft-decision-1"

# Preço público em openrouter.ai/microsoft/microsoft-decision-1 (consultado em 2026-10-19).
# Usado só quando a resposta não traz usage.cost.
USD_POR_TOKEN_ENTRADA = 0.042 / 1_000_000
USD_POR_TOKEN_SAIDA = 0.0

STATUS_RETENTAVEIS = {408, 429, 500, 502, 503, 504, 524, 529}


def _retentavel(erro: BaseException) -> bool:
    if isinstance(erro, httpx.HTTPStatusError):
        return erro.response.status_code in STATUS_RETENTAVEIS
    return isinstance(erro, httpx.TransportError)


async def chamar_modelo(cliente: httpx.AsyncClient, corpo: dict) -> tuple[dict, int]:
    tentativas = 0
    async for tentativa in AsyncRetrying(
        retry=retry_if_exception(_retentavel),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(multiplier=0.5, max=20),
        reraise=True,
    ):
        with tentativa:
            tentativas += 1
            resp = await cliente.post(URL, json=corpo)
            resp.raise_for_status()
            return resp.json(), tentativas
    raise RuntimeError("inalcançável")


async def classificar_documento(cliente, semaforo, modelo, run_id, caminho: Path, extraido: dict, gabarito: dict) -> dict:
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
    corpo = {
        "model": modelo,
        "state": {"documento": {"texto": texto, "paginas": extraido["paginas"], "origem_texto": origem}},
        "questions": {"tipo": {"type": "choice", "instructions": INSTRUCOES, "criteria": CLASSES}},
        "session_id": run_id,
    }
    async with semaforo:
        inicio = time.perf_counter()
        try:
            dados, tentativas = await chamar_modelo(cliente, corpo)
            erro = None
        except httpx.HTTPStatusError as e:
            dados, tentativas, erro = None, None, f"HTTP {e.response.status_code}: {e.response.text[:300]}"
        except httpx.HTTPError as e:
            dados, tentativas, erro = None, None, f"{type(e).__name__}: {e}"
        registro["t_modelo_s"] = round(time.perf_counter() - inicio, 3)
        registro["timestamp"] = datetime.now(timezone.utc).isoformat()

    resposta = (dados or {}).get("answers", {}).get("tipo")
    if erro is None and not (resposta and resposta.get("choice") in CLASSES):
        erro = f"resposta inesperada: {json.dumps(dados, ensure_ascii=False)[:300]}"

    if erro:
        registro.update(erro=erro, classe=None)
    else:
        probs = dict(sorted(resposta["probabilities"].items(), key=lambda kv: -kv[1]))
        uso = dados.get("usage", {})
        tokens_in, tokens_out = uso.get("input_tokens", 0), uso.get("output_tokens", 0)
        custo_calculado = tokens_in * USD_POR_TOKEN_ENTRADA + tokens_out * USD_POR_TOKEN_SAIDA
        registro.update(
            erro=None,
            modelo=dados.get("model"),
            provedor=dados.get("provider"),
            gen_id=dados.get("id"),
            tentativas=tentativas,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            custo_usd=uso["cost"] if uso.get("cost") is not None else custo_calculado,
            custo_fonte="openrouter" if uso.get("cost") is not None else "calculado",
            custo_calculado_usd=custo_calculado,
            classe=resposta["choice"],
            confianca=resposta["confidence"],
            prob_classe=probs[resposta["choice"]],
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


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", type=Path, help="pasta com os PDFs")
    ap.add_argument("--gabarito", type=Path, help="CSV com colunas arquivo,rotulo,... para medir acerto")
    ap.add_argument("--modelo", default=MODELO_PADRAO, help=f"modelo de decisão no OpenRouter (padrão: {MODELO_PADRAO})")
    ap.add_argument("--concorrencia", type=int, default=8, help="requisições simultâneas")
    ap.add_argument("--limite", type=int, default=None, help="classifica só os N primeiros PDFs")
    ap.add_argument("--sem-cache", action="store_true", help="refaz a extração/OCR")
    ap.add_argument("--rotulo", default="", help="anotação livre gravada no resumo (ex.: 'microsoft v1')")
    args = ap.parse_args()

    pdfs = sorted(args.pasta.glob("*.pdf"))[: args.limite]
    gabarito = carregar_gabarito(args.gabarito)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    saida = RAIZ / "execucoes" / run_id
    saida.mkdir(parents=True)
    inicio_execucao = time.perf_counter()

    print(f"[{run_id}] extraindo texto de {len(pdfs)} PDFs...")
    extraidos = {pdf: extrair_texto(pdf, usar_cache=not args.sem_cache) for pdf in pdfs}
    t_fase_extracao = time.perf_counter() - inicio_execucao

    print(f"[{run_id}] classificando com {args.modelo}, concorrência {args.concorrencia}...")
    inicio_classificacao = time.perf_counter()
    semaforo = asyncio.Semaphore(args.concorrencia)
    cabecalhos = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "HTTP-Referer": "https://github.com/gabsalles/teste-anexos-class",
        "X-Title": "teste-anexos-class",
    }
    registros = []
    async with httpx.AsyncClient(headers=cabecalhos, timeout=60.0) as cliente:
        tarefas = [classificar_documento(cliente, semaforo, args.modelo, run_id, p, extraidos[p], gabarito) for p in pdfs]
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
        "modelo_solicitado": args.modelo,
        "via": "openrouter /api/alpha/decisions",
        "prompt_hash": PROMPT_HASH,
        "concorrencia": args.concorrencia,
        "pasta": str(args.pasta),
        "t_fase_extracao_s": round(t_fase_extracao, 2),
        "t_fase_classificacao_s": round(t_fase_classificacao, 2),
        "t_total_s": round(time.perf_counter() - inicio_execucao, 2),
        "docs_por_minuto_classificacao": round(60 * len(pdfs) / t_fase_classificacao, 1) if pdfs else None,
    }
    resumo = resumir(registros, meta, campo_latencia="t_modelo_s")
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"\nResultados em {saida.relative_to(RAIZ)}/")


if __name__ == "__main__":
    asyncio.run(main())
