# Conjunto sintético de anexos jurídicos para teste de classificador

São 256 PDFs fictícios em `pdfs/` (nomes neutros, `doc_0001.pdf` a `doc_0256.pdf`) e o gabarito em `manifest.csv`.

## Classes (`rotulo`) e quantidades

| rótulo | qtd | o que inclui (`subtipo`) |
|---|---|---|
| certidao | 26 | publicação (com teor do ato), decurso de prazo, trânsito em julgado, oficial de justiça positiva/negativa, juntada, remessa, **ato ordinatório** |
| decisao_interlocutoria | 21 | tutela de urgência (deferida/indeferida), saneadora, gratuidade, SISBAJUD, impugnação ao cumprimento, **decisão monocrática do relator em agravo** |
| despacho | 19 | despachos de expediente (1 a 3 ordens), com ou sem título |
| procuracao | 16 | pessoa física, pessoa jurídica (banco), **procuração + declaração de hipossuficiência no mesmo PDF** |
| peticao_inicial | 15 | inicial cível, inicial JEC, reclamação trabalhista |
| mandado | 15 | citação, intimação, penhora e avaliação, citação/penhora trabalhista |
| contestacao | 14 | cível, JEC, defesa trabalhista |
| recurso_apelacao | 12 | apelação, **recurso inominado (JEC)**, **recurso ordinário (trabalho)** |
| sentenca | 12 | mérito, homologatória de acordo, extinção sem mérito, extinção da execução |
| ata_audiencia | 12 | conciliação, CEJUSC, instrução cível, instrução trabalhista com depoimentos, **termo de audiência com acordo homologado** |
| replica | 11 | réplica, impugnação à contestação, manifestação sobre defesa (trabalho) |
| oficio | 11 | INSS, Serasa, banco, transferência e **ofício-resposta do banco** |
| contrarrazoes | 11 | à apelação, ao recurso inominado, ao recurso ordinário |
| embargos_declaracao | 10 | contra sentença e contra acórdão |
| substabelecimento | 9 | com e sem reserva de poderes |
| laudo_pericial | 9 | grafotécnico, contábil (revisional e trabalhista) |
| acordao | 7 | TJ (com folha de acórdão e voto), Turma Recursal, TRT |
| alvara | 7 | alvará de levantamento e **Mandado de Levantamento Eletrônico (TJSP)** |
| calculos_liquidacao | 7 | planilha cível (art. 524 do CPC) e resumo no estilo PJe-Calc |
| agravo_instrumento | 6 | contra indeferimento de tutela e de gratuidade |
| termo_acordo | 6 | petição de acordo, termo de acordo, instrumento particular de transação |

A coluna `subtipo` permite separar classes que alguém pode querer tratar à parte, por exemplo recurso inominado × apelação ou ato ordinatório × certidão.

## Colunas do `manifest.csv`

`arquivo`, `rotulo`, `subtipo`, `justica` (estadual_civel / juizado_especial_civel / trabalho), `tribunal`, `sistema_carimbo` (esaj, pje, pjejt, projudi, nenhum), `assunto`, `paginas`, `escaneado`, `nivel_ruido` (0 a 3), `camada_texto` (texto / ocr_com_erros / nenhuma (imagem)), `processo`.

## Ruído e dificuldade

- **Escaneados:** 65 PDFs são imagem, com inclinação, ruído, manchas, furos de perfurador, sombra de borda, faixas de toner, JPEG de baixa qualidade e às vezes binarização. Destes, 47 não têm texto nenhum (exigem OCR) e 18 têm camada OCR invisível com erros de reconhecimento. Procurações e substabelecimentos são escaneados com mais frequência, como na vida real, e trazem assinatura manuscrita e, às vezes, carimbo de reconhecimento de firma.
- **Carimbos de sistema** em todas as páginas: tarja vertical e "fls." do e-SAJ, rodapé do PJe com hash, "Fls."/ID do PJe-JT e cabeçalho/rodapé do Projudi. Cerca de 12% vêm sem carimbo.
- **Pares confundíveis de propósito:**
  - acórdão que transcreve o dispositivo da sentença;
  - ata de audiência com acordo e homologação × termo de acordo × sentença homologatória;
  - certidão de publicação que contém o teor de um despacho;
  - certidão do oficial × mandado;
  - decisão × despacho, ambos podendo vir sem título;
  - embargos × recurso;
  - contrarrazões que citam a sentença;
  - Mandado de Levantamento Eletrônico (rótulo alvara);
  - ofício-resposta escrito pelo banco.
- **Variação de layout:** cinco famílias de fonte, margens, recuos, espaçamentos, timbres de escritório, tribunal, perito e banco, e paginação própria opcional.

## Atenção

- **Vazamento realista no Projudi:** o cabeçalho do Projudi traz o nome que o usuário deu ao arquivo. Em cerca de 30% dos documentos com carimbo Projudi esse nome é o próprio tipo; nos demais é genérico ("Petição", "Outros documentos") ou ausente. Se quiser medir o classificador sem essa pista, filtre `sistema_carimbo == "projudi"`.
- **Tudo é fictício:** partes, CPFs/CNPJs (com dígito verificador válido, mas inventados), números CNJ (com DV válido), bancos e escritórios.
- **Jurisprudência:** as **ementas citadas, com seus números de processo, são inventadas**. Súmulas, temas repetitivos e dispositivos legais são reais.
- Os textos foram gerados por combinação de blocos redigidos por tipo de peça e assunto (negativação, fraude Pix, consignado, revisional, tarifas, horas extras de bancário, equiparação salarial), com sorteio de partes, valores e datas.
