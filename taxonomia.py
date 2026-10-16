"""Pergunta e descrição das classes de anexo enviadas ao Jev.

Cada classe tem: o que é, sinais típicos no texto e com o que não confundir.
Alterar este arquivo muda o `prompt_hash` gravado em cada execução, o que permite
comparar variantes do prompt nas estatísticas.
"""

import hashlib
import json

from typesafe_sdk import Choice

INSTRUCOES = {
    "pergunta": "Que tipo de peça ou ato processual é o documento em `documento.texto`?",
    "contexto": (
        "Anexo de processo judicial brasileiro (Justiça Estadual cível, Juizado Especial "
        "Cível ou Justiça do Trabalho), com texto extraído de PDF. O texto pode conter "
        "carimbos e rodapés de sistema (e-SAJ, PJe, PJe-JT, Projudi), numeração de folhas, "
        "timbres e, quando `documento.origem_texto` indicar OCR, erros de reconhecimento."
    ),
    "como_decidir": [
        "Classifique pelo que o documento É, ou seja, quem o produz e qual ato ele "
        "pratica, e não pelo que ele cita, transcreve ou responde.",
        "Um documento que transcreve sentença, decisão ou despacho continua sendo do tipo "
        "de quem o assina: acórdão que transcreve a sentença é acórdão; certidão de "
        "publicação com o teor de um despacho é certidão; contrarrazões que citam a "
        "sentença são contrarrazões.",
        "O título pode faltar. Use o autor (juiz, relator, colegiado, advogado, servidor, "
        "oficial de justiça, perito, banco), o pedido e o dispositivo.",
        "Rótulos de sistema no cabeçalho (como o nome dado ao arquivo no Projudi) são "
        "pistas fracas; o conteúdo prevalece.",
    ],
}

CLASSES = {
    "certidao": {
        "o_que_e": "Ato de servidor da secretaria/cartório ou do oficial de justiça que "
        "certifica um fato processual: publicação, decurso de prazo, trânsito em julgado, "
        "juntada, remessa, resultado de diligência do oficial (positiva ou negativa). "
        "Inclui ato ordinatório praticado pelo servidor.",
        "sinais": ["CERTIFICO", "dou fé", "ATO ORDINATÓRIO", "assinado por escrevente, "
                   "analista, diretor de secretaria ou oficial de justiça"],
        "nao_confundir": "Certidão de publicação pode reproduzir o teor de um despacho ou "
        "decisão e continua sendo certidão. A certidão do oficial relata como cumpriu o "
        "mandado; o mandado é a ordem a ser cumprida.",
    },
    "decisao_interlocutoria": {
        "o_que_e": "Pronunciamento do juiz que resolve uma questão no curso do processo sem "
        "encerrá-lo: tutela de urgência, saneamento, gratuidade da justiça, bloqueio via "
        "SISBAJUD, impugnação ao cumprimento de sentença. Inclui decisão monocrática do "
        "relator em agravo.",
        "sinais": ["fundamentação seguida de DEFIRO / INDEFIRO / REJEITO / ACOLHO",
                   "Decido", "art. 300 ou art. 357 do CPC", "pontos controvertidos"],
        "nao_confundir": "Despacho só dá andamento, sem decidir questão. Sentença encerra "
        "a fase de conhecimento ou a execução. Acórdão é decisão de colegiado.",
    },
    "despacho": {
        "o_que_e": "Pronunciamento do juiz de mero expediente, sem conteúdo decisório: "
        "intime-se, cite-se, manifeste-se em X dias, especifiquem provas, aguarde-se. "
        "Curto, com uma a três ordens e pouca ou nenhuma fundamentação.",
        "sinais": ["Vistos.", "Intime-se", "Manifeste-se a parte", "no prazo de"],
        "nao_confundir": "Decisão interlocutória fundamenta e defere ou indefere algo. "
        "Certidão de publicação que traz o texto de um despacho é certidão.",
    },
    "procuracao": {
        "o_que_e": "Instrumento em que a parte (outorgante, pessoa física ou jurídica) "
        "nomeia advogado (outorgado) e lhe confere poderes, como a cláusula ad judicia et "
        "extra. Pode vir com declaração de hipossuficiência no mesmo arquivo.",
        "sinais": ["OUTORGANTE", "OUTORGADO", "confere poderes", "ad judicia",
                   "assinatura e reconhecimento de firma"],
        "nao_confundir": "No substabelecimento é o advogado, e não a parte, que transfere "
        "poderes que já recebeu.",
    },
    "substabelecimento": {
        "o_que_e": "Advogado já constituído transfere a outro advogado, com ou sem reserva, "
        "os poderes que recebeu na procuração.",
        "sinais": ["SUBSTABELEÇO", "com reserva de iguais poderes", "sem reserva de poderes"],
        "nao_confundir": "Na procuração quem outorga os poderes é a própria parte.",
    },
    "peticao_inicial": {
        "o_que_e": "Peça do advogado do autor ou reclamante que inaugura o processo: "
        "qualificação das partes, fatos, fundamentos jurídicos, pedidos e valor da causa. "
        "Inclui inicial no Juizado Especial e reclamação trabalhista.",
        "sinais": ["vem propor AÇÃO", "RECLAMAÇÃO TRABALHISTA", "dos pedidos",
                   "requer a citação", "dá-se à causa o valor"],
        "nao_confundir": "Contestação, réplica e recursos respondem a algo já existente no "
        "processo; a inicial pede a citação do réu.",
    },
    "mandado": {
        "o_que_e": "Ordem judicial expedida pela secretaria para que o oficial de justiça "
        "cumpra uma diligência: citar, intimar, penhorar e avaliar bens.",
        "sinais": ["MANDADO DE CITAÇÃO / INTIMAÇÃO / PENHORA", "Oficial de Justiça a quem "
                   "este for apresentado", "CUMPRA-SE", "finalidade"],
        "nao_confundir": "A certidão do oficial relata o cumprimento e é certidão. O "
        "Mandado de Levantamento Eletrônico autoriza saque de valores e é alvará.",
    },
    "contestacao": {
        "o_que_e": "Defesa do réu ou reclamado em resposta à petição inicial: "
        "preliminares, impugnação dos fatos e pedido de improcedência. Inclui defesa "
        "trabalhista e contestação no Juizado Especial.",
        "sinais": ["CONTESTAÇÃO", "DEFESA", "preliminarmente", "requer a improcedência"],
        "nao_confundir": "Réplica é do autor respondendo à contestação. Contrarrazões "
        "respondem a recurso.",
    },
    "recurso_apelacao": {
        "o_que_e": "Recurso contra sentença dirigido ao tribunal ou turma recursal, pedindo "
        "a reforma: apelação (CPC art. 1.009), recurso inominado no Juizado (Lei 9.099, "
        "art. 41) e recurso ordinário trabalhista (CLT art. 895).",
        "sinais": ["razões de apelação", "RECURSO INOMINADO", "RECURSO ORDINÁRIO",
                   "requer o provimento para reformar a sentença", "preparo"],
        "nao_confundir": "Embargos de declaração vão ao próprio juízo apontando omissão ou "
        "contradição. Agravo de instrumento ataca decisão interlocutória. Contrarrazões "
        "defendem a sentença.",
    },
    "sentenca": {
        "o_que_e": "Pronunciamento do juiz de primeiro grau que encerra a fase de "
        "conhecimento ou a execução: julgamento de mérito, homologação de acordo, extinção "
        "sem resolução de mérito, extinção da execução.",
        "sinais": ["JULGO PROCEDENTE / IMPROCEDENTE", "HOMOLOGO o acordo", "julgo extinto",
                   "art. 485, 487 ou 924 do CPC", "Publique-se. Registre-se. Intimem-se."],
        "nao_confundir": "Acórdão é decisão de colegiado. Ata de audiência em que o acordo "
        "é homologado na própria ata é ata de audiência. Decisão interlocutória não encerra "
        "o processo.",
    },
    "ata_audiencia": {
        "o_que_e": "Registro do que ocorreu em audiência (conciliação, CEJUSC, instrução, "
        "audiência trabalhista): presentes, propostas, depoimentos e ocorrências. Inclui "
        "termo de audiência em que o acordo é celebrado e homologado na própria ata.",
        "sinais": ["ATA DE AUDIÊNCIA", "TERMO DE AUDIÊNCIA", "aberta a audiência",
                   "apregoadas as partes", "Nada mais havendo"],
        "nao_confundir": "Termo de acordo é documento das partes fora da audiência. "
        "Sentença homologatória é pronunciamento separado do juiz.",
    },
    "replica": {
        "o_que_e": "Manifestação do autor ou reclamante sobre a contestação e os documentos "
        "do réu: réplica, impugnação à contestação, manifestação sobre a defesa trabalhista.",
        "sinais": ["RÉPLICA", "IMPUGNAÇÃO À CONTESTAÇÃO", "manifestar-se sobre a defesa"],
        "nao_confundir": "Contestação é do réu. Contrarrazões respondem a recurso.",
    },
    "oficio": {
        "o_que_e": "Comunicação oficial entre o juízo e órgão ou entidade externa (INSS, "
        "Serasa, banco, outro juízo) requisitando informação, providência ou transferência "
        "de valores. Inclui ofício-resposta enviado pelo banco ou órgão ao juízo.",
        "sinais": ["Ofício nº", "Senhor(a) Gerente", "Ao Juízo da", "Em resposta ao ofício"],
        "nao_confundir": "Mandado é dirigido ao oficial de justiça. Alvará autoriza o "
        "beneficiário a levantar valores.",
    },
    "contrarrazoes": {
        "o_que_e": "Resposta da parte recorrida a um recurso (apelação, recurso inominado, "
        "recurso ordinário), defendendo a manutenção da sentença. Costuma citar a sentença "
        "e pedir o não provimento.",
        "sinais": ["CONTRARRAZÕES", "recorrido", "requer o não provimento",
                   "manutenção da sentença"],
        "nao_confundir": "O recurso pede a reforma da sentença. A réplica responde à "
        "contestação.",
    },
    "embargos_declaracao": {
        "o_que_e": "Peça dirigida ao mesmo juízo ou tribunal que proferiu a sentença ou o "
        "acórdão, apontando omissão, contradição, obscuridade ou erro material (CPC art. "
        "1.022; CLT art. 897-A).",
        "sinais": ["EMBARGOS DE DECLARAÇÃO", "omissão", "contradição", "obscuridade",
                   "efeitos infringentes", "prequestionamento"],
        "nao_confundir": "Apelação, recurso inominado e recurso ordinário pedem a reforma "
        "a outro órgão.",
    },
    "laudo_pericial": {
        "o_que_e": "Trabalho técnico do perito nomeado pelo juízo (grafotécnico, contábil, "
        "trabalhista): objeto, metodologia, análise, respostas aos quesitos e conclusão.",
        "sinais": ["LAUDO PERICIAL", "perito nomeado", "quesitos", "metodologia", "conclusão"],
        "nao_confundir": "Cálculos de liquidação são planilha de valores sem análise "
        "pericial nem quesitos.",
    },
    "acordao": {
        "o_que_e": "Decisão colegiada de tribunal ou turma recursal (TJ, Turma Recursal, "
        "TRT): ementa, relatório, voto e resultado por unanimidade ou maioria. Pode "
        "transcrever trechos ou o dispositivo da sentença.",
        "sinais": ["ACÓRDÃO", "EMENTA", "Relator", "VOTO", "acordam os integrantes",
                   "por unanimidade"],
        "nao_confundir": "Decisão monocrática do relator é decisão interlocutória. "
        "Sentença é de juiz singular.",
    },
    "alvara": {
        "o_que_e": "Autorização judicial para o beneficiário ou seu advogado levantar "
        "valores depositados em conta judicial. Inclui o Mandado de Levantamento "
        "Eletrônico do TJSP.",
        "sinais": ["ALVARÁ DE LEVANTAMENTO", "MANDADO DE LEVANTAMENTO ELETRÔNICO",
                   "beneficiário", "conta judicial", "valor a levantar"],
        "nao_confundir": "Ofício ao banco pede providência ou transferência. Mandado de "
        "penhora constringe bens.",
    },
    "calculos_liquidacao": {
        "o_que_e": "Demonstrativo ou planilha do valor devido: principal, correção "
        "monetária, juros, honorários e multa. Inclui memória de cálculo do art. 524 do "
        "CPC e resumo no estilo PJe-Calc.",
        "sinais": ["planilha", "memória de cálculo", "índice de correção", "juros de mora",
                   "total devido", "PJe-Calc"],
        "nao_confundir": "Laudo pericial contábil traz análise técnica e respostas a "
        "quesitos.",
    },
    "agravo_instrumento": {
        "o_que_e": "Recurso dirigido diretamente ao tribunal contra decisão interlocutória, "
        "como o indeferimento de tutela de urgência ou de gratuidade (CPC art. 1.015), em "
        "geral pedindo efeito suspensivo ou antecipação da tutela recursal.",
        "sinais": ["AGRAVO DE INSTRUMENTO", "agravante", "agravado", "decisão agravada",
                   "art. 1.015"],
        "nao_confundir": "A decisão monocrática do relator no agravo é decisão "
        "interlocutória. A apelação ataca sentença.",
    },
    "termo_acordo": {
        "o_que_e": "Documento das partes que formaliza transação fora de audiência: "
        "petição conjunta de acordo, termo de acordo ou instrumento particular de "
        "transação, com cláusulas, valor, parcelas e pedido de homologação.",
        "sinais": ["TERMO DE ACORDO", "INSTRUMENTO PARTICULAR DE TRANSAÇÃO", "cláusula",
                   "requerem a homologação"],
        "nao_confundir": "Ata de audiência registra acordo feito em audiência. Sentença "
        "homologatória é do juiz.",
    },
    "outro": {
        "o_que_e": "Nenhum dos tipos acima, como documento pessoal, comprovante, contrato "
        "juntado como prova ou petição intermediária sem relação com as classes listadas.",
    },
}

PERGUNTA_TIPO = Choice(instructions=INSTRUCOES, criteria=CLASSES)

PROMPT_HASH = hashlib.sha256(
    json.dumps([INSTRUCOES, CLASSES], ensure_ascii=False, sort_keys=True).encode()
).hexdigest()[:12]
