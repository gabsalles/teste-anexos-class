# -*- coding: utf-8 -*-
import csv, io, os, sys, traceback, collections
from casos import rng, ch, novo_caso, nome
from assuntos import A
from tipos import GERADORES
from render import render_pdf, scanify

OUT = os.environ.get("OUT", "/home/claude/out")
os.makedirs(f"{OUT}/pdfs", exist_ok=True)

PESOS = dict(despacho=22, certidao=22, decisao_interlocutoria=16, peticao_inicial=14, contestacao=14, sentenca=14, procuracao=12,
             mandado=10, ata_audiencia=10, replica=9, acordao=9, recurso_apelacao=9, contrarrazoes=8, embargos_declaracao=8, oficio=8,
             substabelecimento=7, agravo_instrumento=6, termo_acordo=6, laudo_pericial=6, calculos_liquidacao=6, alvara=6)
QTD = {k: max(6, round(v * 1.15 * rng.uniform(.65, 1.35))) for k, v in PESOS.items()}

ROTULO_ARQ = dict(despacho="Despacho", certidao="Certidão", decisao_interlocutoria="Decisão", peticao_inicial="Petição Inicial", contestacao="Contestação",
                  sentenca="Sentença", procuracao="Procuração", mandado="Mandado", ata_audiencia="Termo de Audiência", replica="Impugnação à Contestação",
                  acordao="Acórdão", recurso_apelacao="Apelação", contrarrazoes="Contrarrazões", embargos_declaracao="Embargos de Declaração",
                  oficio="Ofício", substabelecimento="Substabelecimento", agravo_instrumento="Agravo de Instrumento", termo_acordo="Acordo",
                  laudo_pericial="Laudo Pericial", calculos_liquidacao="Cálculos", alvara="Alvará")

def caso_para(tipo):
    for _ in range(200):
        c = novo_caso()
        if tipo == "agravo_instrumento" and c.justica != "civel": continue
        if tipo == "laudo_pericial" and (not A[c.assunto]["pericia"] or c.justica == "jec"): continue
        if tipo == "replica" and c.justica == "jec" and rng.random() < .8: continue
        if tipo == "decisao_interlocutoria" and c.justica == "jec" and rng.random() < .5: continue
        return c
    raise RuntimeError(tipo)

def meta(doc, c, tipo):
    autor = doc["autor"]
    doc["sistema"] = c.sistema if rng.random() < .87 else "nenhum"
    if c.sistema == "esaj" and autor in ("adv_a", "adv_r") and rng.random() < .1: doc["sistema"] = "nenhum"
    signer = {"adv_a": c.adv_a.nome, "adv_r": c.adv_r.nome, "juiz": c.juiz, "relator": c.relator, "perito": c.perito[0],
              "parte_a": c.adv_a.nome, "parte_r": c.adv_r.nome, "servidor": nome()[0]}[autor]
    doc["signer"] = doc.get("signer") or signer
    doc["head"] = {"adv_a": "adv" if rng.random() < .75 else "none", "adv_r": "adv" if rng.random() < .8 else "none",
                   "juiz": "court" if rng.random() < .85 else "none", "relator": "court" if rng.random() < .8 else "none",
                   "servidor": "court" if rng.random() < .75 else "none", "perito": "perito" if rng.random() < .8 else "none",
                   "parte_a": "none", "parte_r": "bank" if doc["sub"] == "oficio_resposta" else "none"}[autor]
    doc["escritorio"] = c.adv_a.escr if autor == "adv_a" else c.adv_r.escr
    doc["lh_style"] = rng.randint(0, 2); doc["head_all"] = rng.random() < .35
    doc["inst2"] = doc["sub"] in ("acordao_tj", "acordao_trt", "acordao_turma_recursal", "decisao_monocratica_relator")
    doc["bank_name"] = c.reu.nome if c.reu.nome.startswith("BANCO") else "BANCO MERIDIONAL S.A."
    doc["fls"] = c.fls_base + rng.randint(0, 600)
    r = rng.random()
    doc["arq_label"] = ROTULO_ARQ[tipo] if r < .3 else ch(["Petição", "Outros documentos", "Documento", "Petição intermediária", "Anexo", "Documento Diverso"]) if r < .75 else None
    doc["pagenum"] = ch([None, None, "Página {p} de {t}", "{p}", "- {p} -", "Pág. {p}/{t}"])
    doc["pagenum_pos"] = ch(["c", "r"])
    doc["running"] = f"Processo nº {c.numero}" if rng.random() < .25 else None
    doc["h_underline"] = rng.random() < .12
    doc["firma"] = tipo == "procuracao" and rng.random() < .4
    doc["meta_title"] = ch(["", "", "Documento", "Microsoft Word - Documento1", "untitled"]); doc["meta_author"] = ""
    doc["creator"] = ch(["", "Microsoft® Word para Microsoft 365", "LibreOffice Writer", "PJe", "SAJ/PG5"])

def run(QTD):
  rows = []; idx = 0
  ordem = [t for t, n in QTD.items() for _ in range(n)]; rng.shuffle(ordem)
  cont = collections.Counter()
  for tipo in ordem:
      idx += 1
      for tent in range(5):
          try:
              c = caso_para(tipo)
              doc = GERADORES[tipo](c)
              meta(doc, c, tipo)
              buf = io.BytesIO(); n = render_pdf(doc, c, buf); pdf = buf.getvalue()
              p_scan = .14 + doc.get("scan_bias", 0)
              scan = rng.random() < p_scan
              nivel = 0; camada = "texto"
              if scan:
                  nivel = rng.choices([1, 2, 3], [55, 32, 13])[0]
                  ocr = rng.random() < .3
                  pdf, n = scanify(pdf, nivel, ocr=ocr)
                  camada = "ocr_com_erros" if ocr else "nenhuma (imagem)"
              break
          except Exception:
              traceback.print_exc(); print("retry", tipo, file=sys.stderr)
      fn = f"doc_{idx:04d}.pdf"
      open(f"{OUT}/pdfs/{fn}", "wb").write(pdf)
      cont[tipo] += 1
      rows.append(dict(arquivo=fn, rotulo=tipo, subtipo=doc["sub"], justica={"civel": "estadual_civel", "jec": "juizado_especial_civel", "trab": "trabalho"}[c.justica],
                       tribunal=c.sigla, sistema_carimbo=doc["sistema"], assunto=c.assunto, paginas=n, escaneado="sim" if scan else "nao",
                       nivel_ruido=nivel, camada_texto=camada, processo=c.numero))
      if idx % 25 == 0: print(idx, "ok", flush=True)

  with open(f"{OUT}/manifest.csv", "w", newline="", encoding="utf-8") as f:
      w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
  print("TOTAL", len(rows)); print(dict(cont))

if __name__ == "__main__":
  run(QTD)
