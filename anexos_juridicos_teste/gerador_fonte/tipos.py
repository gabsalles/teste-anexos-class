# -*- coding: utf-8 -*-
"""Redação de cada tipo de peça/ato. Cada função devolve um dict com os blocos do documento."""
import re
from casos import rng, ch, money, extenso, dfmt, dext, dt, bizday, nome, cpf, rg, hora, novo_caso, ordinal
from assuntos import A, ctx, F, jurisp

ROM = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# ------------------------------------------------------------------ comuns
RESUMO = {
 "negativacao": ("que teve seu nome inscrito em cadastros de inadimplentes {pR} {R} por débito de {debito}, referente ao contrato nº {contrato}, que afirma desconhecer, pois jamais contratou com a instituição",
                 "declaração de inexistência do débito, a exclusão da anotação e indenização por danos morais"),
 "fraude_pix": ("que foi vítima do chamado golpe da falsa central de atendimento, sendo realizadas {n_pix} transferências via Pix, no total de {debito}, sem que a instituição bloqueasse as operações atípicas",
                "restituição dos valores e indenização por danos morais"),
 "consignado": ("que passou a sofrer descontos mensais de {parcela} em seu benefício previdenciário, decorrentes do contrato de empréstimo consignado nº {contrato}, que não celebrou",
                "declaração de nulidade do contrato, a repetição em dobro do indébito e indenização por danos morais"),
 "revisional": ("que celebrou Cédula de Crédito Bancário para financiamento de {bem}, com juros de {taxa}% ao mês, superiores à média de mercado, além de cobrança de seguro prestamista em venda casada",
                "revisão do contrato, a limitação dos juros à taxa média e a restituição dos valores pagos a maior"),
 "tarifas": ("que vem sofrendo descontos mensais da tarifa \"{cesta}\", no valor de {tarifa}, em conta destinada ao recebimento de salário, sem prévia contratação",
             "declaração de inexigibilidade, a repetição em dobro e indenização por danos morais"),
 "horas_extras": ("que, contratad{sA} em {admissao} e dispensad{sA} em {dispensa}, exercia a função de {cargo} sem fidúcia especial, cumprindo jornada superior à legal, e sofria cobrança abusiva de metas",
                  "pagamento de horas extras excedentes da sexta diária, intervalo intrajornada e indenização por danos morais"),
 "equiparacao": ("que exercia funções idênticas às do paradigma {paradigma}, percebendo salário inferior, e que não recebeu corretamente a PLR proporcional",
                 "diferenças salariais por equiparação e reflexos, além de diferenças de PLR"),
}
RES_DEF = {
 "negativacao": "a regularidade da contratação, por meio digital com validação biométrica, e o exercício regular de direito na inscrição",
 "fraude_pix": "a culpa exclusiva da vítima, que forneceu suas credenciais a terceiro, e a inexistência de falha na prestação do serviço",
 "consignado": "a regularidade da contratação, com crédito do valor em conta de titularidade da parte autora, e a impossibilidade de repetição em dobro",
 "revisional": "a legalidade dos encargos pactuados, a validade das tarifas e a contratação voluntária do seguro",
 "tarifas": "a adesão expressa ao pacote de serviços no ato de abertura da conta",
 "horas_extras": "o exercício de cargo de confiança bancário, a validade dos controles de ponto e a inexistência de assédio",
 "equiparacao": "a ausência de identidade funcional, a diferença de tempo na função e a quitação da PLR",
}
REPLICA = {
 "negativacao": ["As telas sistêmicas juntadas pelo réu são documentos unilaterais, produzidos pela própria instituição, e não comprovam a manifestação de vontade d{oA} {A}. Não há contrato assinado, gravação de atendimento ou relatório técnico da suposta biometria facial, nem comprovação de que valores tenham sido creditados em conta de sua titularidade.",
                 "Quanto à Súmula 385 do STJ, as anotações apontadas na contestação são posteriores à inscrição impugnada ou já se encontram baixadas, conforme extrato atualizado que ora se junta, não servindo para afastar o dano moral."],
 "fraude_pix": ["A alegação de culpa exclusiva não se sustenta. O golpista possuía dados que somente a instituição detinha, o que revela vazamento de informações sob sua guarda. Mais do que isso: as transferências, sequenciais e de valores elevados, destoavam de todo o histórico da conta e deveriam ter sido bloqueadas pelos mecanismos antifraude que o próprio réu afirma possuir.",
                "A Resolução BCB nº 1/2020 impõe aos participantes do arranjo Pix o dever de adotar mecanismos de prevenção a fraudes compatíveis com o perfil do usuário, o que não ocorreu. Trata-se de fortuito interno (Súmula 479 do STJ)."],
 "consignado": ["{OA} {A} impugna expressamente a assinatura lançada no contrato juntado, que diverge daquela constante de seus documentos pessoais. Nos termos do art. 429, II, do CPC e do Tema 1.061 do STJ, incumbe à instituição financeira provar a autenticidade da assinatura, requerendo-se, desde já, a realização de perícia grafotécnica, às expensas do réu.",
                "O comprovante de TED, por sua vez, não demonstra a titularidade da conta de destino, que não corresponde à conta em que {oA} {A} recebe seu benefício. Eventual crédito decorreu da própria fraude e não convalida o negócio inexistente."],
 "revisional": ["O fato de as taxas constarem do contrato não afasta a possibilidade de revisão, pois se trata de contrato de adesão, sem margem de negociação. A taxa contratada supera em muito a média de mercado divulgada pelo Banco Central, o que caracteriza a abusividade reconhecida pelo REsp 1.061.530/RS.",
                "Quanto ao seguro, o termo de adesão integra o mesmo instrumento do financiamento, sem indicação de alternativas de seguradoras, o que configura a venda casada vedada pelo Tema 972 do STJ."],
 "tarifas": ["O termo de adesão juntado pelo réu não contém assinatura d{oA} {A} no campo relativo à escolha do pacote, havendo apenas marcação pré-impressa. Ausente manifestação inequívoca de vontade, a cobrança é indevida, nos termos da Resolução CMN nº 3.919/2010.",
             "Ademais, a conta é utilizada exclusivamente para recebimento de salário, sendo vedada a cobrança de tarifas pelos serviços essenciais."],
 "horas_extras": ["A gratificação de função, por si só, não caracteriza o cargo de confiança (Súmula 102, I, do TST). {OA} {A} não tinha subordinados, alçada própria ou procuração, e a prova oral demonstrará que suas atribuições eram meramente técnicas e comerciais.",
                  "Os cartões de ponto são impugnados, pois não refletem a real jornada: havia orientação expressa da gerência para encerramento do registro antes da saída efetiva, fato que será comprovado pela prova testemunhal."],
 "equiparacao": ["O paradigma e {oA} {A} exerciam as mesmas atividades, atendiam o mesmo segmento de clientes e respondiam ao mesmo gestor, substituindo-se mutuamente. As avaliações de desempenho juntadas são documentos unilaterais e não demonstram diferença de produtividade ou perfeição técnica.",
                 "Quanto à PLR, o comprovante abrange apenas a parcela regra básica, deixando de considerar a parcela adicional prevista na CCT."],
}


DOUTRINA = [
 "Como ensina a melhor doutrina, a boa-fé objetiva impõe às partes deveres anexos de lealdade, informação e cooperação, que se projetam sobre todas as fases da relação contratual, desde as tratativas até a fase pós-contratual (art. 422 do Código Civil).",
 "O Código de Defesa do Consumidor, norma de ordem pública e interesse social (art. 1º), consagra a vulnerabilidade do consumidor no mercado de consumo (art. 4º, I) e assegura a efetiva prevenção e reparação de danos patrimoniais e morais (art. 6º, VI).",
 "A teoria do risco do empreendimento, adotada pelo legislador consumerista, estabelece que todo aquele que se disponha a exercer alguma atividade no mercado de consumo tem o dever de responder pelos eventuais vícios ou defeitos dos bens e serviços fornecidos, independentemente de culpa.",
 "A jurisprudência do Superior Tribunal de Justiça é firme no sentido de que a indenização por dano moral deve ser arbitrada com moderação, observando-se a extensão do dano, a capacidade econômica das partes e o caráter pedagógico da condenação, sem que represente fonte de enriquecimento indevido.",
 "O ônus da prova, nos termos do art. 373 do CPC, incumbe ao autor quanto ao fato constitutivo de seu direito e ao réu quanto à existência de fato impeditivo, modificativo ou extintivo do direito do autor, admitindo-se sua distribuição dinâmica nas hipóteses do § 1º do mesmo dispositivo.",
 "Não se pode olvidar que o princípio da força obrigatória dos contratos, embora mitigado pela função social do contrato (art. 421 do Código Civil), ainda constitui pilar da segurança jurídica, devendo a intervenção judicial ser excepcional e limitada (art. 421-A, III, do Código Civil, incluído pela Lei nº 13.874/2019).",
 "Ressalte-se que o tempo útil do consumidor, desperdiçado na tentativa frustrada de solucionar administrativamente o problema criado pelo fornecedor, constitui bem jurídico tutelado, cuja violação enseja reparação, conforme a teoria do desvio produtivo do consumidor, acolhida em diversos precedentes.",
 "A responsabilidade civil pressupõe a presença concomitante de conduta, dano e nexo de causalidade (arts. 186 e 927 do Código Civil). Ausente qualquer desses elementos, não há que se falar em dever de indenizar.",
]
DOUTRINA_TRAB = [
 "O princípio da primazia da realidade, basilar no Direito do Trabalho, determina que a verdade dos fatos prevaleça sobre a forma dos documentos, de modo que a nomenclatura atribuída ao cargo não é suficiente para afastar os direitos decorrentes das reais condições de trabalho.",
 "Nos termos do art. 818 da CLT, com redação dada pela Lei nº 13.467/2017, o ônus da prova incumbe ao reclamante quanto ao fato constitutivo de seu direito e à reclamada quanto aos fatos impeditivos, modificativos ou extintivos.",
 "O poder diretivo do empregador encontra limites na dignidade da pessoa humana e no valor social do trabalho (art. 1º, III e IV, da Constituição Federal), não podendo ser exercido de forma a expor o empregado a situações vexatórias ou humilhantes.",
 "A Convenção Coletiva de Trabalho dos bancários, reconhecida nos termos do art. 7º, XXVI, da Constituição Federal, deve ser observada em sua integralidade, conforme a tese fixada pelo STF no Tema 1.046 da repercussão geral.",
]
def doutrina(c, k=None):
    pool = DOUTRINA_TRAB if c.justica == "trab" else DOUTRINA
    k = rng.choice([0, 1, 1, 2, 3]) if k is None else k
    return rng.sample(pool, min(k, len(pool)))

def adv_sig(c, adv, x, d):
    return [f"{c.cidade}, {dext(d)}.", "", adv.nome.upper(), adv.oab]

def adv_sig2(c, x, d, lado="r"):
    a1 = c.adv_r if lado == "r" else c.adv_a
    out = f"{c.cidade}/{c.uf}, {dext(d)}."
    if lado == "r" and rng.random() < .5:
        return out, [[a1.nome.upper(), a1.oab], [c.adv_r2.nome.upper(), c.adv_r2.oab]]
    return out, [[a1.nome.upper(), a1.oab]]

def enderecamento(c, inst=1):
    if inst == 2:
        if c.justica == "trab": return f"EXCELENTÍSSIMO(A) SENHOR(A) DESEMBARGADOR(A) PRESIDENTE DO EGRÉGIO {c.trib}"
        if c.justica == "jec": return f"EXCELENTÍSSIMO(A) SENHOR(A) JUIZ(A) PRESIDENTE DO COLÉGIO RECURSAL DA COMARCA DE {c.cidade.upper()} – {c.uf}"
        if c.uf == "SP": return "EXCELENTÍSSIMO SENHOR DESEMBARGADOR PRESIDENTE DA SEÇÃO DE DIREITO PRIVADO DO EGRÉGIO TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO"
        return f"EXCELENTÍSSIMO SENHOR DESEMBARGADOR PRIMEIRO VICE-PRESIDENTE DO EGRÉGIO {c.trib}"
    if c.justica == "trab":
        return ch(["EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA ", "EXMO(A). SR(A). JUIZ(A) DO TRABALHO DA "]) + f"{c.vara.upper()} – {c.uf}"
    if c.justica == "jec":
        return ch(["EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DO ", "EXMO(A). SR(A). DR(A). JUIZ(A) DE DIREITO DO "]) + f"{c.vara.upper()} – {c.uf}"
    return ch(["EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA ", "EXMO. SR. DR. JUIZ DE DIREITO DA ", "AO JUÍZO DA "]) + f"{c.vara.upper()} – {c.uf}"

def proc_line(c):
    return ch(["Processo nº ", "Autos nº ", "Processo: ", "Proc. nº ", "Autos do processo nº "]) + c.numero

def capa_processo(c, x, extra=None):
    """Bloco de identificação usado por sentenças, despachos, decisões (estilo e-SAJ/PJe)."""
    rows = [("Processo Digital nº" if c.sistema == "esaj" else "Processo nº", c.numero),
            ("Classe - Assunto" if c.sistema == "esaj" else "Classe", f"{c.classe} - {A[c.assunto]['cnj']}" if c.sistema == "esaj" else c.classe)]
    if c.justica == "trab":
        rows = [("PROCESSO nº", f"{c.numero} (ATOrd)"), ("RECLAMANTE", x["AUTOR"]), ("RECLAMADO", x["REU"])]
    else:
        if c.sistema != "esaj": rows.append(("Assunto", A[c.assunto]["cnj"]))
        rows += [(ch(["Requerente", "Autor(a)", "Requerente"]) if c.sistema == "esaj" else "AUTOR", T(x["AUTOR"]) if c.sistema == "esaj" else x["AUTOR"]),
                 ("Requerido" if c.sistema == "esaj" else "RÉU", T(x["REU"]) if c.sistema == "esaj" else x["REU"])]
    if extra: rows += extra
    return ("kv", rows)

def juiz_sig(c, d, tit=None):
    if c.justica == "trab":
        t = tit or ("Juíza do Trabalho" if c.juiz_g == "f" else "Juiz do Trabalho")
        t = ch([t, t + " Substitut" + ("a" if c.juiz_g == "f" else "o"), t + " Titular"])
    else:
        t = tit or ("Juíza de Direito" if c.juiz_g == "f" else "Juiz de Direito")
    lines = [c.juiz.upper() if rng.random() < .6 else c.juiz, t]
    if c.sistema == "esaj" and rng.random() < .7:
        lines.append("DOCUMENTO ASSINADO DIGITALMENTE NOS TERMOS DA LEI 11.419/2006, CONFORME IMPRESSÃO À MARGEM DIREITA")
    return lines

def local_data(c, d):
    return ch([f"{c.cidade}, {dext(d)}.", f"{c.cidade}/{c.uf}, {dfmt(d)}.", f"{c.cidade}, {dfmt(d)}."])

def pedir_def():
    return ch(["Termos em que,\npede deferimento.", "Nestes termos,\npede deferimento.", "Termos em que, pede e espera deferimento.", "Pede deferimento."])

def lado_perdedor(c):
    if c.resultado == "improc": return "a"
    if c.resultado == "proc": return "r"
    return ch("ar")

def T(s):
    w = s.title().split(" ")
    return " ".join(x.lower() if x.lower() in ("de", "da", "do", "das", "dos", "e") and i else x for i, x in enumerate(w)).replace("S.a.", "S.A.")

def S(*parts): return " ".join(p for p in parts if p)

# ================================================================= PETIÇÃO INICIAL
def peticao_inicial(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"
    d = c.dist
    B.append(("addr", enderecamento(c)))
    if c.assunto == "consignado" and rng.random() < .7:
        B.append(("rbold", "PRIORIDADE DE TRAMITAÇÃO – PESSOA IDOSA (art. 1.048, I, do CPC)"))
    if a["tutela"] and rng.random() < .5:
        B.append(("rbold", "COM PEDIDO DE TUTELA DE URGÊNCIA"))
    B.append(("sp", 14))
    verbo = ch(["vem, respeitosamente, à presença de Vossa Excelência", "vem, mui respeitosamente, perante Vossa Excelência",
                "vem, com o devido respeito, à presença de Vossa Excelência"])
    por = ch(["por seu advogado que esta subscreve (instrumento de mandato anexo)", "por intermédio de seus procuradores infra-assinados (procuração anexa – doc. 01)",
              "por meio de sua advogada constituída (procuração em anexo)"])
    if trab:
        ab = f"{c.autor.qualif()}, CTPS nº {rng.randint(1000000,9999999)}, série {rng.randint(1,999):03d}-{c.uf}, PIS {rng.randint(100,199)}.{rng.randint(10000,99999)}.{rng.randint(10,99)}-{rng.randint(0,9)}, {verbo}, {por}, ajuizar a presente"
        B.append(("p", ab))
        B.append(("title", ch(["RECLAMAÇÃO TRABALHISTA", "RECLAMATÓRIA TRABALHISTA", "AÇÃO TRABALHISTA"]) + ch(["", " – RITO ORDINÁRIO", " PELO RITO ORDINÁRIO"])))
        B.append(("p", f"em face de {c.reu.qualif()}, pelos fatos e fundamentos jurídicos a seguir expostos."))
    else:
        B.append(("p", f"{c.autor.qualif()}, {verbo}, {por}, com fundamento nos arts. 319 e seguintes do Código de Processo Civil e no Código de Defesa do Consumidor, propor a presente"))
        B.append(("title", a["acao"]))
        B.append(("p", f"em face de {c.reu.qualif()}, pelas razões de fato e de direito a seguir aduzidas."))
    n = 0
    if c.gratuidade:
        B.append(("h", f"{ROM[n]} – {'DA JUSTIÇA GRATUITA' if trab else 'DA GRATUIDADE DA JUSTIÇA'}")); n += 1
        if trab:
            B.append(("p", f"{x['OA']} {x['A']} encontra-se desempregad{x['sA']} e não possui condições de arcar com as custas do processo sem prejuízo do próprio sustento e de sua família, razão pela qual requer a concessão dos benefícios da justiça gratuita, nos termos do art. 790, §§ 3º e 4º, da CLT, conforme declaração anexa."))
        else:
            B.append(("p", f"{x['OA']} {x['A']} não possui condições de arcar com as custas processuais e honorários advocatícios sem prejuízo do próprio sustento, conforme declaração de hipossuficiência e documentos anexos, fazendo jus ao benefício da gratuidade da justiça, nos termos dos arts. 98 e 99 do CPC. Ressalta-se que a declaração de insuficiência deduzida por pessoa natural goza de presunção de veracidade (art. 99, § 3º, do CPC)."))
    if c.justica == "civel" and rng.random() < .5:
        B.append(("h", f"{ROM[n]} – DA AUDIÊNCIA DE CONCILIAÇÃO")); n += 1
        B.append(("p", f"Em cumprimento ao art. 319, VII, do CPC, {x['oA']} {x['A']} manifesta " + ch(["interesse", "desinteresse"]) + " na realização de audiência de conciliação ou de mediação."))
    B.append(("h", f"{ROM[n]} – DOS FATOS")); n += 1
    for p in F(a["fatos"], x): B.append(("p", p))
    B.append(("h", f"{ROM[n]} – DO DIREITO" if rng.random() < .5 else f"{ROM[n]} – DOS FUNDAMENTOS JURÍDICOS")); n += 1
    for i, (t, p) in enumerate(F(a["direito"], x)):
        B.append(("h2", f"{ROM[n-1]}.{i+1} – {t.title() if rng.random()<.5 else t}")); B.append(("p", p))
        if i == 0 and rng.random() < .6: B.append(("q", jurisp(c, x)))
        for dp in doutrina(c, rng.choice([0, 0, 1])): B.append(("p", dp))
    if a["tutela"]:
        B.append(("h", f"{ROM[n]} – DA TUTELA DE URGÊNCIA")); n += 1
        B.append(("p", a["tutela"].format(**x)))
    B.append(("h", f"{ROM[n]} – DOS PEDIDOS" if rng.random() < .6 else f"{ROM[n]} – DOS REQUERIMENTOS")); n += 1
    B.append(("p", ch(["Diante do exposto, requer:", "Ante o exposto, requer a Vossa Excelência:", "Por todo o exposto, requer-se:"])))
    peds = []
    if c.gratuidade: peds.append("a concessão dos benefícios da gratuidade da justiça;")
    peds += F(a["pedidos"], x)
    if trab:
        peds.insert(0, "a notificação da Reclamada para, querendo, apresentar defesa em audiência, sob pena de revelia e confissão quanto à matéria de fato (art. 844 da CLT);")
    else:
        peds.insert(1 if c.gratuidade else 0, f"a citação {x['dR']} {x['R']}, por via postal, para, querendo, apresentar contestação no prazo legal, sob pena de revelia;")
        peds.append(f"a condenação {x['dR']} {x['R']} ao pagamento das custas processuais e honorários advocatícios, nos termos do art. 85, § 2º, do CPC;" if c.justica == "civel" else "na hipótese de recurso, a condenação do recorrente vencido em custas e honorários (art. 55 da Lei nº 9.099/95);")
    for i, p in enumerate(peds): B.append(("li", f"{chr(97+i)}) {p}"))
    B.append(("p", "Protesta provar o alegado por todos os meios de prova em direito admitidos, especialmente " + ch(["pela prova documental, testemunhal e pericial", "pelo depoimento pessoal do representante legal da parte contrária, oitiva de testemunhas e juntada de novos documentos", "pela prova documental anexa e demais que se fizerem necessárias"]) + "."))
    B.append(("p", f"Dá-se à causa o valor de {x['valor_causa']} ({x['valor_causa_ext']})."))
    B.append(("pn", pedir_def()))
    B.append(("sig", adv_sig(c, c.adv_a, x, d)))
    if rng.random() < .55:
        B.append(("h", "ROL DE DOCUMENTOS" if rng.random() < .5 else "DOCUMENTOS QUE INSTRUEM A INICIAL"))
        docs = ["Procuração e declaração de hipossuficiência", "Documentos pessoais (RG e CPF)", "Comprovante de residência"]
        docs += {"negativacao": ["Extrato Serasa Experian", "Extrato SCPC", "Protocolo de atendimento", "Reclamação consumidor.gov.br"],
                 "fraude_pix": ["Extratos bancários do período", "Comprovantes das transferências Pix", "Boletim de ocorrência", "Protocolo de contestação (MED)"],
                 "consignado": ["Histórico de créditos do INSS", "Extrato de empréstimos consignados", "Protocolo de reclamação"],
                 "revisional": ["Cédula de Crédito Bancário", "Planilha de cálculo", "Tabela de taxas médias – BACEN"],
                 "tarifas": ["Extratos bancários", "Planilha de valores descontados", "Protocolo de atendimento"],
                 "horas_extras": ["CTPS", "Termo de rescisão (TRCT)", "Holerites", "Prints de mensagens"],
                 "equiparacao": ["CTPS", "TRCT", "Holerites", "Convenção Coletiva de Trabalho"]}[c.assunto]
        B.append(("table", [["Doc.", "Descrição"]] + [[f"{i+1:02d}", t] for i, t in enumerate(docs)], [40, 380]))
    sub = {"trab": "reclamacao_trabalhista", "jec": "peticao_inicial_jec", "civel": "peticao_inicial"}[c.justica]
    return dict(blocks=B, autor="adv_a", data=d, sub=sub)

# ================================================================= CONTESTAÇÃO
def contestacao(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; d = c.data_contest
    B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c)))
    if not trab and rng.random() < .5: B.append(("pn", f"Ação: {a['acao'].split(' C/C')[0].title()}"))
    B.append(("sp", 10))
    nome_peca = ch(["CONTESTAÇÃO", "CONTESTAÇÃO", "DEFESA"]) if trab else "CONTESTAÇÃO"
    B.append(("p", f"{c.reu.nome}, {ch(['já qualificad'+x['oR']+' nos autos', 'pessoa jurídica de direito privado, inscrita no CNPJ sob o nº '+c.reu.cnpj])}, "
              f"{'na' if trab else 'nos autos da'} {'Reclamação Trabalhista' if trab else a['acao'].split(' C/C')[0].title()} que lhe move {x['AUTOR']}, "
              f"{ch(['vem, respeitosamente, à presença de Vossa Excelência', 'vem, por seus advogados infra-assinados'])}, apresentar sua"))
    B.append(("title", nome_peca))
    B.append(("p", "com fundamento " + ("no art. 847 da CLT" if trab else "nos arts. 335 e seguintes do Código de Processo Civil" if c.justica == "civel" else "no art. 30 da Lei nº 9.099/95") + ", pelas razões de fato e de direito a seguir expostas."))
    n = 0
    if rng.random() < .6:
        B.append(("h", f"{ROM[n]} – {ch(['DA TEMPESTIVIDADE', 'TEMPESTIVIDADE'])}")); n += 1
        B.append(("p", ch([f"A presente contestação é tempestiva, uma vez que a citação foi aperfeiçoada com a juntada do aviso de recebimento, iniciando-se o prazo de 15 (quinze) dias úteis previsto no art. 335 do CPC.",
                         f"Considerando a data da audiência de conciliação infrutífera, a defesa é apresentada dentro do prazo legal.",
                         "Tempestiva a presente defesa, apresentada no prazo legal."]) if not trab else "A defesa é apresentada até a audiência, nos termos do art. 847, parágrafo único, da CLT, sendo tempestiva."))
    if rng.random() < .55:
        B.append(("h", f"{ROM[n]} – DAS PUBLICAÇÕES")); n += 1
        B.append(("p", f"Requer que todas as intimações e publicações sejam realizadas exclusivamente em nome do advogado {c.adv_r.nome.upper()}, inscrito na {c.adv_r.oab}, sob pena de nulidade, nos termos do art. 272, § 5º, do CPC."))
    B.append(("h", f"{ROM[n]} – {ch(['SÍNTESE DA INICIAL', 'BREVE SÍNTESE DOS FATOS', 'RESUMO DA DEMANDA', 'DAS ALEGAÇÕES AUTORAIS'])}")); n += 1
    B.append(("p", f"Alega {x['oA']} {x['A']}, em síntese, " + RESUMO[c.assunto][0].format(**x) + ". Requer, ao final, a " + RESUMO[c.assunto][1].format(**x) + "."))
    B.append(("p", ch(["Todavia, como se demonstrará, a pretensão não merece prosperar.", "Contudo, razão alguma lhe assiste, conforme se passa a demonstrar.", "Sem razão, contudo."])))
    for t, p in F(a["preliminares"], x):
        B.append(("h", f"{ROM[n]} – {t}")); n += 1; B.append(("p", p))
    if c.gratuidade and rng.random() < .4:
        B.append(("h", f"{ROM[n]} – DA IMPUGNAÇÃO À GRATUIDADE DA JUSTIÇA")); n += 1
        B.append(("p", f"A presunção de hipossuficiência é relativa. {x['OA']} {x['A']} contratou advogado particular e não juntou declaração de imposto de renda ou extratos que demonstrem a alegada insuficiência de recursos, razão pela qual se impugna o benefício, nos termos do art. 100 do CPC."))
    B.append(("h", f"{ROM[n]} – DO MÉRITO")); n += 1
    for i, (t, p) in enumerate(F(a["defesa"], x)):
        B.append(("h2", f"{ROM[n-1]}.{i+1}. {t}")); B.append(("p", p))
        if rng.random() < .25: B.append(("q", jurisp(c, x).replace("Sentença mantida", "Sentença reformada").replace("Recurso desprovido", "Recurso provido")))
        for dp in doutrina(c, rng.choice([0, 0, 1])): B.append(("p", dp))
    if not trab:
        B.append(("h", f"{ROM[n]} – DA INAPLICABILIDADE DA INVERSÃO DO ÔNUS DA PROVA")); n += 1
        B.append(("p", "A inversão do ônus da prova não é automática, dependendo da verossimilhança das alegações ou da hipossuficiência do consumidor, requisitos ausentes no caso concreto. Ademais, não se pode impor ao fornecedor a produção de prova impossível."))
    B.append(("h", f"{ROM[n]} – {ch(['DOS PEDIDOS', 'DOS REQUERIMENTOS', 'CONCLUSÃO'])}")); n += 1
    pre = "o acolhimento da(s) preliminar(es) arguida(s), com a extinção do feito sem resolução do mérito; " if a["preliminares"] else ""
    B.append(("p", f"Diante do exposto, requer {pre}no mérito, sejam os pedidos julgados TOTALMENTE IMPROCEDENTES, condenando-se {x['oA']} {x['A']} ao pagamento das custas e honorários advocatícios."))
    B.append(("p", "Subsidiariamente, em caso de condenação, requer que eventual indenização seja fixada com moderação e que a correção monetária e os juros observem os parâmetros legais." if not trab else
              "Subsidiariamente, requer a compensação dos valores pagos sob o mesmo título, a observância da evolução salarial, dos dias efetivamente trabalhados, do divisor 220 e a aplicação do IPCA-E na fase pré-judicial e da taxa SELIC a partir do ajuizamento (ADC 58 do STF)."))
    B.append(("p", "Protesta provar o alegado por todos os meios de prova admitidos, especialmente pelo depoimento pessoal d" + x["oA"] + " " + x["A"] + ", sob pena de confissão, e juntada de novos documentos."))
    B.append(("pn", pedir_def()))
    loc, sigs = adv_sig2(c, x, d, "r")
    B.append(("pn", loc)); B.append(("sigs", sigs))
    return dict(blocks=B, autor="adv_r", data=d, sub="contestacao_trab" if trab else "contestacao")

# ================================================================= RÉPLICA
def replica(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; d = bizday(c.data_contest, rng.randint(15, 40))
    B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 10))
    nm = ch(["MANIFESTAÇÃO SOBRE A DEFESA E DOCUMENTOS", "RÉPLICA", "IMPUGNAÇÃO À CONTESTAÇÃO"]) if trab else ch(["RÉPLICA", "RÉPLICA À CONTESTAÇÃO", "IMPUGNAÇÃO À CONTESTAÇÃO", "MANIFESTAÇÃO À CONTESTAÇÃO"])
    B.append(("p", f"{x['AUTOR']}, já qualificad{x['oA']} nos autos da ação em epígrafe, que move em face de {c.reu.nome}, vem, respeitosamente, por seu advogado, "
              f"{ch(['em atenção ao r. despacho de fls. '+str(rng.randint(80,260)), 'no prazo legal', 'em cumprimento à intimação retro'])}, apresentar"))
    B.append(("title", nm))
    B.append(("p", ("nos termos dos arts. 350 e 351 do CPC, " if not trab else "") + "pelas razões a seguir expostas."))
    n = 0
    B.append(("h", f"{ROM[n]} – {ch(['BREVE RESUMO DA CONTESTAÇÃO', 'DA DEFESA APRESENTADA', 'SÍNTESE DA CONTESTAÇÃO'])}")); n += 1
    B.append(("p", f"Em sua defesa, {x['oR']} {x['R']} sustenta, em síntese, {RES_DEF[c.assunto]}. Contudo, os argumentos não se sustentam e apenas confirmam a pretensão deduzida na inicial."))
    for t, p in F(a["preliminares"], x):
        B.append(("h", f"{ROM[n]} – {t.replace('PRELIMINARMENTE – ', 'DA PRELIMINAR DE ').replace('DA DA', 'DA')}")); n += 1
        B.append(("p", ch(["A preliminar não merece acolhida.", "Rejeita-se a preliminar.", "Sem razão a parte contrária."]) + " " +
                  {"PRELIMINARMENTE – DA AUSÊNCIA DE INTERESSE DE AGIR": "O esgotamento da via administrativa não é condição para o exercício do direito de ação (art. 5º, XXXV, da Constituição Federal). Ademais, a própria contestação de mérito evidencia a resistência à pretensão.",
                   "PRELIMINARMENTE – DA ILEGITIMIDADE PASSIVA": "A causa de pedir é a falha no serviço prestado pela instituição em que a conta é mantida, a qual autorizou as transferências, sendo evidente sua legitimidade, segundo a teoria da asserção.",
                   "PRELIMINARMENTE – DA PRESCRIÇÃO": "Tratando-se de pretensão fundada em fato do serviço, aplica-se o prazo quinquenal do art. 27 do CDC, contado de cada desconto, não havendo que se falar em prescrição trienal.",
                   "PRELIMINARMENTE – DA INÉPCIA DA INICIAL": "A inicial especifica as cláusulas impugnadas e o valor incontroverso, atendendo integralmente ao art. 330, § 2º, do CPC.",
                   "PRELIMINARMENTE – DA PRESCRIÇÃO QUINQUENAL": "Não há pretensões anteriores ao quinquênio, ou, se houver, a prescrição deverá ser observada apenas quanto às parcelas, sem prejuízo do direito material.",
                   "PRELIMINARMENTE – DA INÉPCIA DOS PEDIDOS": "Os pedidos foram indicados com valores estimados, o que basta para o atendimento do art. 840, § 1º, da CLT, conforme art. 12, § 2º, da IN 41/2018 do TST."}.get(t, "")))
    B.append(("h", f"{ROM[n]} – DO MÉRITO")); n += 1
    for p in REPLICA[c.assunto]: B.append(("p", p.format(**x)))
    B.append(("p", ch(["No mais, reiteram-se integralmente os termos da petição inicial.", "Ratificam-se, no mais, todos os fundamentos e pedidos da exordial.", "Reitera, no mais, os termos da inicial, que ficam fazendo parte integrante desta manifestação."])))
    B.append(("h", f"{ROM[n]} – DAS PROVAS")); n += 1
    pr = {"consignado": "a produção de prova pericial grafotécnica, com a intimação do réu para apresentação da via original do contrato",
          "negativacao": "a intimação do réu para apresentar o contrato original e o relatório de autenticação biométrica, sob pena de presunção de veracidade (art. 400 do CPC)",
          "revisional": "a produção de prova pericial contábil",
          "horas_extras": "a produção de prova testemunhal e o depoimento pessoal do preposto",
          "equiparacao": "a produção de prova testemunhal e a juntada das fichas funcionais do paradigma"}.get(c.assunto, "o julgamento antecipado do mérito, nos termos do art. 355, I, do CPC, por se tratar de matéria eminentemente documental")
    B.append(("p", f"Requer {pr}."))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, c.adv_a, x, d)))
    return dict(blocks=B, autor="adv_a", data=d, sub="manifestacao_defesa_trab" if trab else "replica")

# ================================================================= SENTENÇA
def sentenca(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; jec = c.justica == "jec"; d = c.data_sent
    tipo = rng.choices(["merito", "homolog", "extincao", "exec"], [70, 12, 10, 8])[0]
    if trab and tipo == "exec": tipo = "merito"
    B.append(capa_processo(c, x))
    if c.sistema == "esaj" and rng.random() < .7: B.append(("kv", [("Juiz(a) de Direito", f"Dr(a). {c.juiz}")]))
    B.append(("sp", 8))
    B.append(("title", ch(["SENTENÇA", "SENTENÇA", "S E N T E N Ç A"]) if rng.random() < .9 else None))
    if tipo == "homolog":
        B.append(("pn", "Vistos."))
        acordo = money(round(c.valor_causa * rng.uniform(.25, .6), 2))
        B.append(("p", ch([f"As partes noticiaram a celebração de acordo, conforme petição de fls. {rng.randint(90,300)}, pelo qual {x['oR']} {x['R']} se compromete ao pagamento de {acordo}, com plena quitação do objeto da ação.",
                         f"Trata-se de ação em que as partes, às fls. {rng.randint(90,300)}, informaram a composição amigável, nos termos ali descritos."])))
        B.append(("p", f"Ante o exposto, HOMOLOGO, para que produza seus jurídicos e legais efeitos, o acordo celebrado entre as partes e, em consequência, JULGO EXTINTO o processo, com resolução do mérito, nos termos do art. 487, III, \"b\", do Código de Processo Civil."
                       + (" Custas pelas partes, na forma acordada; dispensadas as remanescentes (art. 90, § 3º, do CPC)." if not jec else " Sem custas e honorários (art. 55 da Lei nº 9.099/95).")))
        B.append(("p", ch(["Homologo, ainda, a renúncia ao prazo recursal, certificando-se o trânsito em julgado nesta data.", "Considerando a renúncia ao prazo recursal, certifique-se o trânsito em julgado e arquivem-se os autos.", "Oportunamente, arquivem-se."])))
        B.append(("pn", ch(["P.R.I.", "Publique-se. Intimem-se.", "P.I.C."])))
    elif tipo == "extincao":
        B.append(("pn", "Vistos."))
        mot = rng.choice(["desist", "abandono", "inercia"])
        if mot == "desist":
            B.append(("p", f"{x['OA']} {x['A']} requereu a desistência da ação (fls. {rng.randint(60,200)}). Citad{x['oR']}, {x['oR']} {x['R']} manifestou concordância." if rng.random() < .5 else f"{x['OA']} {x['A']} manifestou desistência da ação antes da citação."))
            B.append(("p", "Ante o exposto, HOMOLOGO o pedido de desistência e JULGO EXTINTO o processo, sem resolução do mérito, com fundamento no art. 485, VIII, do Código de Processo Civil."))
        elif mot == "abandono":
            B.append(("p", f"Intimad{x['oA']} pessoalmente para dar andamento ao feito, nos termos do art. 485, § 1º, do CPC, {x['oA']} {x['A']} permaneceu inerte, conforme certidão de fls. {rng.randint(60,200)}."))
            B.append(("p", "Ante o exposto, JULGO EXTINTO o processo, sem resolução do mérito, nos termos do art. 485, III, do Código de Processo Civil."))
        else:
            B.append(("p", f"Determinada a emenda da petição inicial para {ch(['juntada de comprovante de residência atualizado em nome d'+x['oA']+' '+x['A'], 'regularização da representação processual', 'recolhimento das custas iniciais', 'esclarecimento do pedido e adequação do valor da causa'])}, {x['oA']} {x['A']} deixou transcorrer in albis o prazo concedido."))
            B.append(("p", "Assim, INDEFIRO a petição inicial e JULGO EXTINTO o processo, sem resolução do mérito, com fundamento nos arts. 321, parágrafo único, e 485, I, do Código de Processo Civil."))
        B.append(("p", ch(["Sem condenação em honorários.", "Custas na forma da lei, observada a gratuidade.", "Custas pelo autor, observada a gratuidade, se concedida."])))
        B.append(("p", "Com o trânsito em julgado, arquivem-se os autos, com as cautelas de praxe."))
        B.append(("pn", ch(["P.I.", "P.R.I.C.", "Publique-se. Intime-se."])))
    elif tipo == "exec":
        B.append(("pn", "Vistos."))
        B.append(("p", f"Trata-se de cumprimento de sentença promovido por {x['AUTOR']} em face de {c.reu.nome}. Intimad{x['oR']} {x['R']}, efetuou o depósito integral do débito, no valor de {money(round(c.valor_causa*rng.uniform(.3,.9),2))}, com o qual concordou {x['oA']} credor{x['a_fem']}, já expedido o respectivo mandado de levantamento."))
        B.append(("p", "Satisfeita a obrigação, JULGO EXTINTO o cumprimento de sentença, com fundamento nos arts. 924, II, e 925 do Código de Processo Civil."))
        B.append(("p", "Oportunamente, arquivem-se os autos."))
        B.append(("pn", "P.I."))
    else:
        B.append(("pn", "Vistos." if rng.random() < .8 else "Vistos etc."))
        if jec:
            B.append(("p", "Dispensado o relatório, nos termos do art. 38, caput, da Lei nº 9.099/95." + ch([" Fundamento e decido.", " Decido.", ""])))
        else:
            rel = (f"{x['AUTOR']} ajuizou {'reclamação trabalhista' if trab else 'a presente ' + a['acao'].split(' C/C')[0].lower()} em face de {c.reu.nome}, "
                   f"alegando, em síntese, {RESUMO[c.assunto][0].format(**x)}. Pleiteou a {RESUMO[c.assunto][1].format(**x)}. Juntou documentos.")
            B.append(("p", rel))
            if a["tutela"] and rng.random() < .5: B.append(("p", f"A tutela de urgência foi {ch(['deferida', 'indeferida'])} (fls. {rng.randint(40,90)})."))
            B.append(("p", f"{'Regularmente notificad' + x['oR'] if trab else 'Citad' + x['oR']}, {x['oR']} {x['R']} apresentou {'defesa escrita' if trab else 'contestação'} (fls. {rng.randint(60,180)}), sustentando {RES_DEF[c.assunto]}."
                      + (" Arguiu preliminar." if a["preliminares"] else "") + " Pugnou pela improcedência."))
            if not trab: B.append(("p", f"Houve réplica (fls. {rng.randint(180,260)})."))
            if a["pericia"] and rng.random() < .7:
                B.append(("p", f"Deferida a produção de prova pericial, o laudo foi juntado às fls. {rng.randint(260,400)}, com manifestação das partes."))
            if trab: B.append(("p", "Na audiência de instrução, foram colhidos os depoimentos pessoais e ouvida uma testemunha. Sem outras provas, encerrou-se a instrução processual. Razões finais remissivas. Rejeitadas as propostas conciliatórias."))
            B.append(("pn", ch(["É o relatório.", "É o relatório. Fundamento e decido.", "É o relatório. DECIDO.", "Relatados, decido."])))
        if trab: B.append(("h", "FUNDAMENTAÇÃO"))
        if not jec and not trab and rng.random() < .5 and not a["pericia"]:
            B.append(("p", "O feito comporta julgamento antecipado, nos termos do art. 355, I, do Código de Processo Civil, pois a questão de mérito, embora de direito e de fato, prescinde de outras provas além das já produzidas."))
        for t, p in F(a["preliminares"], x):
            if trab: B.append(("h2", t.replace("PRELIMINARMENTE – ", "")))
            t2 = t.replace("PRELIMINARMENTE – ", "").lower()
            if "prescri" in t2 and trab:
                B.append(("p", f"Ajuizada a ação em {dfmt(c.dist)}, pronuncio a prescrição das pretensões condenatórias anteriores a {dfmt(c.dist.replace(year=c.dist.year-5))}, extinguindo-as com resolução do mérito (art. 487, II, do CPC), exceto quanto ao FGTS, observada a modulação do Tema 608 do STF."))
            else:
                B.append(("p", f"Rejeito a preliminar de {re.sub(r'^(da|do|das|dos) ', '', t2)}. " + ch(["A matéria confunde-se com o mérito e com ele será apreciada.", "Presentes as condições da ação, analisadas segundo a teoria da asserção.", "A inicial preenche os requisitos legais e permitiu o pleno exercício do direito de defesa."])))
        if trab:
            B.append(("h2", t if (t := ch(["MÉRITO", "HORAS EXTRAS. CARGO DE CONFIANÇA" if c.assunto == "horas_extras" else "EQUIPARAÇÃO SALARIAL"])) else "MÉRITO"))
        elif not jec and rng.random() < .6:
            B.append(("p", "A relação jurídica entre as partes é de consumo, aplicando-se o Código de Defesa do Consumidor, conforme a Súmula 297 do Superior Tribunal de Justiça." if c.reu.nome.startswith("BANCO") else "A relação jurídica é de consumo (arts. 2º, 3º e 17 do CDC)."))
        procede = c.resultado != "improc"
        for p in F(a["fund_proc"] if procede else a["fund_improc"], x): B.append(("p", p))
        if c.resultado == "parc" and not trab:
            B.append(("p", ch(["Os demais pedidos não comportam acolhimento, pois não demonstrado o dano alegado.", "Indevida, contudo, a restituição em dobro, por ausência de prova de má-fé, sendo a devolução na forma simples.",
                             "Não comporta acolhimento, por fim, o pedido de indenização por danos morais, pois a situação não ultrapassou o mero aborrecimento."])))
        if trab and procede:
            B.append(("h2", "JUSTIÇA GRATUITA"))
            B.append(("p", f"Defiro {x['aoA']} {x['A']} os benefícios da justiça gratuita, nos termos do art. 790, §§ 3º e 4º, da CLT."))
            B.append(("h2", "HONORÁRIOS ADVOCATÍCIOS"))
            B.append(("p", "Considerando a sucumbência recíproca, condeno a reclamada ao pagamento de honorários de 10% sobre o valor líquido da condenação e o reclamante ao pagamento de 10% sobre os pedidos integralmente rejeitados, com suspensão de exigibilidade, nos termos da ADI 5.766."))
            B.append(("h2", "CORREÇÃO MONETÁRIA E JUROS"))
            B.append(("p", "Na fase pré-judicial, incidem o IPCA-E e os juros do art. 39, caput, da Lei nº 8.177/91; a partir do ajuizamento, a taxa SELIC, nos termos da decisão do STF nas ADCs 58 e 59, observadas as alterações da Lei nº 14.905/2024."))
        B.append(("h", "DISPOSITIVO") if trab or rng.random() < .3 else ("sp", 2))
        if trab:
            r = {"proc": "PROCEDENTES", "parc": "PROCEDENTES EM PARTE", "improc": "IMPROCEDENTES"}[c.resultado]
            if procede:
                B.append(("p", f"Ante o exposto, {'rejeito as preliminares e, no mérito, ' if a['preliminares'] else ''}julgo {r} os pedidos formulados por {x['AUTOR']} em face de {c.reu.nome} para condenar a reclamada a pagar, nos termos da fundamentação, que integra este dispositivo para todos os efeitos:"))
                B.append(("p", a["disp_proc"].format(**x)))
                cond = round(c.valor_causa * rng.uniform(.25, .55), -2)
                B.append(("p", f"Liquidação por cálculos. Contribuições previdenciárias e fiscais na forma da Súmula 368 do TST. Custas pela reclamada, no importe de {money(cond*0.02)}, calculadas sobre o valor provisoriamente arbitrado à condenação de {money(cond)}."))
            else:
                B.append(("p", f"Ante o exposto, julgo IMPROCEDENTES os pedidos formulados por {x['AUTOR']} em face de {c.reu.nome}. Custas pelo reclamante, no importe de {money(c.valor_causa*0.02)}, calculadas sobre o valor da causa, dispensadas em razão da gratuidade ora deferida."))
            B.append(("p", "Intimem-se as partes." if rng.random() < .5 else "Cientes as partes. Nada mais."))
        else:
            r = {"proc": "PROCEDENTE", "parc": "PARCIALMENTE PROCEDENTE", "improc": "IMPROCEDENTE"}[c.resultado]
            intro = ch(["Ante o exposto", "Diante do exposto", "Pelo exposto", "Isto posto"])
            if procede:
                B.append(("p", f"{intro}, JULGO {r} o pedido{'s' if rng.random()<.5 else ''}, com resolução do mérito, nos termos do art. 487, I, do Código de Processo Civil, para: " + a["disp_proc"].format(**x)))
            else:
                B.append(("p", f"{intro}, JULGO IMPROCEDENTE{'S os pedidos' if rng.random()<.5 else ' o pedido'}, com resolução do mérito, nos termos do art. 487, I, do Código de Processo Civil" + (", e REVOGO a tutela anteriormente concedida." if a["tutela"] and rng.random()<.4 else ".")))
            if jec:
                B.append(("p", "Sem custas e honorários advocatícios nesta fase, nos termos do art. 55 da Lei nº 9.099/95."))
            else:
                if c.resultado == "parc":
                    B.append(("p", f"Diante da sucumbência recíproca, as custas serão rateadas e cada parte arcará com os honorários do patrono da parte adversa, fixados em {ch(['10%', '12%', '15%'])} do valor da condenação, vedada a compensação (art. 85, § 14, do CPC), observada a gratuidade."))
                elif procede:
                    B.append(("p", f"Sucumbente, condeno {x['oR']} {x['R']} ao pagamento das custas, despesas processuais e honorários advocatícios, que fixo em {ch(['10%', '15%', '20%'])} do valor atualizado da condenação, nos termos do art. 85, § 2º, do CPC."))
                else:
                    B.append(("p", f"Sucumbente, arcará {x['oA']} {x['A']} com as custas, despesas processuais e honorários advocatícios, fixados em 10% do valor atualizado da causa, observada a gratuidade da justiça (art. 98, § 3º, do CPC)." ))
            if rng.random() < .5:
                B.append(("p", "Em caso de interposição de recurso de apelação, intime-se a parte contrária para contrarrazões e, após, remetam-se os autos ao Tribunal, independentemente de juízo de admissibilidade (art. 1.010, § 3º, do CPC)." if not jec else "Havendo recurso inominado, observe-se o prazo de 10 dias e o preparo previsto no art. 42, § 1º, da Lei nº 9.099/95."))
            B.append(("pn", ch(["P.R.I.C.", "P.I.", "Publique-se. Intimem-se.", "P.R.I."])))
    B = [b for b in B if b is None or (b[1] is not None if len(b) > 1 else True)]
    B.append(("pn", local_data(c, d))); B.append(("sig", juiz_sig(c, d)))
    return dict(blocks=B, autor="juiz", data=d, sub=f"sentenca_{tipo}")

# ================================================================= ACÓRDÃO
def acordao(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; jec = c.justica == "jec"; d = c.data_acord
    perd = lado_perdedor(c); provido = rng.random() < .3
    ap = c.autor.nome.upper() if perd == "a" else c.reu.nome; apd = c.reu.nome if perd == "a" else c.autor.nome.upper()
    rec = "Recurso Ordinário Trabalhista" if trab else "Recurso Inominado" if jec else "Apelação Cível"
    res_txt = ("DERAM PROVIMENTO ao recurso" if provido else "NEGARAM PROVIMENTO ao recurso") if not trab else ("DAR PROVIMENTO" if provido else "NEGAR PROVIMENTO")
    num2 = c.numero
    rel = c.relator; Rel = "Relatora" if c.relator_g == "f" else "Relator"
    des = "Desembargadora" if c.relator_g == "f" else "Desembargador"
    if jec: des = "Juíza" if c.relator_g == "f" else "Juiz"
    vu = ch(["V. U.", "v.u.", "Unânime", "Por votação unânime"])
    ementa = a["ementa"].format(**x) + (". Sentença reformada. Recurso provido." if provido else ". Sentença mantida. Recurso desprovido.")
    disp_sent = a["disp_proc"].format(**x).rstrip(".") if c.resultado != "improc" else "julgar improcedentes os pedidos iniciais"
    if trab:
        B.append(("kv", [("PROCESSO nº", f"{num2} (ROT)"), ("RECORRENTE", ap), ("RECORRIDO", apd), ("ORIGEM", c.vara.upper()), ("RELATOR(A)", rel.upper())]))
        B.append(("h", "EMENTA")); B.append(("box", ementa))
        B.append(("h", "RELATÓRIO"))
        B.append(("p", f"Inconformad{x['oA'] if perd=='a' else 'o'} com a r. sentença de Id. {rng.randint(1000000,9999999):x}, que julgou {'procedentes em parte' if c.resultado=='parc' else 'procedentes' if c.resultado=='proc' else 'improcedentes'} os pedidos, recorre ordinariamente {'o reclamante' if perd=='a' else 'a reclamada'}, pretendendo a reforma quanto " + ("ao enquadramento no art. 224, § 2º, da CLT, às horas extras e à indenização por danos morais." if c.assunto == "horas_extras" else "à equiparação salarial e às diferenças de PLR.")))
        B.append(("p", "Contrarrazões apresentadas. Dispensada a remessa ao Ministério Público do Trabalho, nos termos do art. 85 do Regimento Interno." if rng.random() < .7 else "Contrarrazões apresentadas. É o relatório."))
        B.append(("h", "FUNDAMENTAÇÃO")); B.append(("h2", "ADMISSIBILIDADE"))
        B.append(("p", "Conheço do recurso, porque preenchidos os pressupostos legais de admissibilidade." + (" Depósito recursal e custas regularmente comprovados." if perd == "r" else "")))
        B.append(("h2", "MÉRITO"))
        B.append(("p", ch(["Sem razão o(a) recorrente.", "Não prospera o inconformismo.", "Com razão o(a) recorrente."]) if not provido else "Com razão o(a) recorrente."))
        src = a["fund_proc"] if (c.resultado != "improc") != provido else a["fund_improc"]
        for p in F(src, x)[:3]: B.append(("p", p.replace("Defiro", "Correta a sentença que deferiu").replace("Afasto", "Correto o afastamento") if not provido else p))
        B.append(("q", jurisp(c, x)))
        B.append(("p", f"{'Dou' if provido else 'Nego'} provimento."))
        B.append(("h", "ACÓRDÃO"))
        B.append(("p", f"ACORDAM os Magistrados da {c.turma} do {c.trib.title().replace('Do Trabalho Da', 'do Trabalho da')}, em sessão {ch(['ordinária', 'virtual', 'telepresencial'])} realizada em {dfmt(d)}, por unanimidade, CONHECER do recurso ordinário e, no mérito, {res_txt}, nos termos da fundamentação do voto d{'a' if c.relator_g=='f' else 'o'} {Rel}." + (" Mantido o valor da condenação." if not provido else " Arbitra-se à condenação o novo valor de " + money(round(c.valor_causa*.3, -2)) + ", com custas de " + money(round(c.valor_causa*.3, -2)*.02) + ".")))
        B.append(("sig", [rel.upper(), f"{des} {Rel}"]))
        return dict(blocks=B, autor="relator", data=d, sub="acordao_trt")
    if jec:
        B.append(("title", "ACÓRDÃO" if rng.random() < .6 else "SÚMULA DE JULGAMENTO QUE SERVE DE ACÓRDÃO"))
        B.append(("kv", [("Recurso Inominado Cível nº", num2), ("Recorrente", ap), ("Recorrido", apd), ("Origem", c.vara), ("Juiz(a) Relator(a)", rel)]))
        B.append(("box", ementa))
        B.append(("p", f"Vistos, relatados e discutidos estes autos, ACORDAM os Juízes da {c.turma} do Colégio Recursal de {c.cidade}, em {res_txt.lower()}, {vu}, nos termos do voto d{'a' if c.relator_g=='f' else 'o'} {Rel}."))
        B.append(("h", "VOTO"))
        B.append(("p", "Dispensado o relatório, nos termos do art. 46 da Lei nº 9.099/95."))
        B.append(("p", f"Trata-se de recurso inominado interposto contra a r. sentença que julgou {'procedente' if c.resultado=='proc' else 'parcialmente procedente' if c.resultado=='parc' else 'improcedente'} o pedido{', para ' + disp_sent if c.resultado!='improc' else ''}."))
        src = a["fund_proc"] if (c.resultado != "improc") != provido else a["fund_improc"]
        for p in F(src, x)[:2]: B.append(("p", p))
        B.append(("p", ("A sentença deve ser confirmada pelos seus próprios fundamentos, o que se faz na forma do art. 46 da Lei nº 9.099/95. " if not provido else "") +
                  ("Recorrente vencido arcará com custas e honorários advocatícios de 15% do valor da condenação (art. 55 da Lei nº 9.099/95)." if not provido else "Sem condenação em custas e honorários, ante o provimento do recurso (art. 55 da Lei nº 9.099/95).")))
        B.append(("pn", local_data(c, d))); B.append(("sig", [rel.upper(), f"{des} {Rel}"]))
        return dict(blocks=B, autor="relator", data=d, sub="acordao_turma_recursal")
    # TJ
    if c.uf == "SP":
        B.append(("r", f"Registro: {d.year}.0000{rng.randint(100000,999999)}"))
        B.append(("title", "ACÓRDÃO"))
        B.append(("p", f"Vistos, relatados e discutidos estes autos de Apelação Cível nº {num2}, da Comarca de {c.cidade}, em que é apelante {ap}, é apelado {apd}."))
        o2, o3 = nome()[0], nome()[0]
        B.append(("p", f"ACORDAM, em sessão {ch(['permanente e virtual', 'ordinária'])} da {c.camara} do Tribunal de Justiça de São Paulo, proferir a seguinte decisão: {res_txt}. {vu}, de conformidade com o voto do relator, que integra este acórdão."))
        B.append(("p", f"O julgamento teve a participação dos Desembargadores {o2.upper()} (Presidente sem voto), {o3.upper()} E {nome()[0].upper()}."))
        B.append(("pn", f"São Paulo, {dext(d)}."))
        B.append(("sig", [rel.upper(), Rel, "Assinatura Eletrônica"]))
        B.append(("pb",))
        B.append(("kv", [("Apelação Cível nº", num2), ("Apelante", T(ap)), ("Apelado", T(apd)), ("Comarca", c.cidade), ("Juiz(a) de 1ª Instância", c.juiz), ("Voto nº", str(rng.randint(10000, 49999)))]))
    else:
        B.append(("kv", [("APELAÇÃO CÍVEL Nº", num2), ("COMARCA", c.cidade.upper()), ("APELANTE(S)", ap), ("APELADO(A)(S)", apd), ("RELATOR(A)", f"DES(A). {rel.upper()}")]))
        B.append(("title", "ACÓRDÃO"))
    B.append(("box", ementa))
    if c.uf != "SP":
        B.append(("p", f"Vistos etc., acorda, em Turma, a {c.camara} do {c.trib.title().replace('Do Estado De', 'do Estado de').replace('De Justiça','de Justiça')}, na conformidade da ata dos julgamentos, à unanimidade, em {res_txt.lower().replace('deram', 'dar').replace('negaram', 'negar')}."))
        B.append(("sig", [f"DES(A). {rel.upper()}", Rel])); B.append(("pb",)); B.append(("pn", f"{des.upper()} {rel.upper()} ({Rel.upper()})")); B.append(("title", "VOTO"))
    else:
        B.append(("title", "VOTO"))
    B.append(("p", f"Trata-se de apelação interposta contra a r. sentença de fls. {rng.randint(250,480)}/{rng.randint(481,520)}, cujo relatório se adota, que julgou {'procedente' if c.resultado=='proc' else 'parcialmente procedente' if c.resultado=='parc' else 'improcedente'} a ação{', para ' + disp_sent if c.resultado != 'improc' else ''}."))
    if perd == "r":
        B.append(("p", f"Apela {x['oR']} {x['R']}, sustentando, em síntese, {RES_DEF[c.assunto]}. Subsidiariamente, pede a redução do valor da indenização." ))
    else:
        B.append(("p", f"Apela {x['oA']} {x['A']}, reiterando {RESUMO[c.assunto][0].format(**x).split(',')[0]} e pugnando pela integral procedência dos pedidos."))
    B.append(("p", f"Recurso tempestivo{', preparado' if perd=='r' else ', isento de preparo em razão da gratuidade'} e respondido (fls. {rng.randint(530,600)})." + ch(["", " Não houve oposição ao julgamento virtual.", " Houve oposição ao julgamento virtual."])))
    B.append(("pn", "É o relatório."))
    B.append(("p", ch(["O recurso não comporta provimento.", "O inconformismo não prospera.", "A r. sentença deve ser mantida."]) if not provido else ch(["O recurso comporta provimento.", "Respeitado o entendimento do douto Magistrado, a r. sentença comporta reforma."])))
    src = a["fund_proc"] if (c.resultado != "improc") != provido else a["fund_improc"]
    for p in F(src, x): B.append(("p", p.replace("Fixo a indenização", "Adequada a indenização fixada").replace("fixo a indenização", "a indenização fixada")))
    B.append(("q", jurisp(c, x)))
    if not provido:
        B.append(("p", "Nos termos do art. 85, § 11, do CPC, majoro os honorários advocatícios devidos pel" + ("o apelante" if perd == "r" else "a parte apelante") + f" para {ch(['12%', '15%', '20%'])} sobre a base de cálculo fixada na sentença, observada a gratuidade, se o caso."))
    B.append(("p", f"Ante o exposto, {'DOU' if provido else 'NEGO'} PROVIMENTO ao recurso" + (", nos termos da fundamentação." if provido else ".")))
    if rng.random() < .5: B.append(("p", "Para fins de prequestionamento, considera-se que a matéria foi integralmente apreciada, sendo desnecessária a indicação expressa de todos os dispositivos legais invocados."))
    B.append(("sig", [rel.upper(), Rel]))
    return dict(blocks=B, autor="relator", data=d, sub="acordao_tj")

# ================================================================= DECISÃO INTERLOCUTÓRIA
def decisao_interlocutoria(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"
    opts = ["tutela", "saneamento", "gratuidade", "sisbajud", "impugnacao", "liminar_ai"]
    w = [5 if a["tutela"] else 0, 4 if c.justica != "jec" else 0, 2, 3, 2, 2 if c.justica == "civel" else 0]
    tipo = rng.choices(opts, w)[0]
    d = bizday(c.dist, rng.randint(3, 20)) if tipo in ("tutela", "gratuidade") else bizday(c.data_contest, rng.randint(30, 120)) if tipo == "saneamento" else bizday(c.data_sent, rng.randint(120, 400))
    if tipo == "liminar_ai":
        nai = c.numero[:16].replace(c.numero[:7], f"{rng.randint(2000000,2999999)}") + ".8.26.0000" if c.uf == "SP" else c.numero
        B.append(("kv", [("Agravo de Instrumento nº", nai), ("Agravante", c.autor.nome), ("Agravado", c.reu.nome), ("Comarca", c.cidade), ("Relator(a)", c.relator)]))
        B.append(("title", ch(["DECISÃO MONOCRÁTICA", "Vistos."])))
        B.append(("p", f"Trata-se de agravo de instrumento interposto contra a r. decisão que indeferiu a tutela de urgência {'para ' + ('exclusão da anotação restritiva' if c.assunto=='negativacao' else 'suspensão dos descontos' if c.assunto=='consignado' else 'depósito das parcelas incontroversas')}."))
        B.append(("p", f"Em cognição sumária, própria deste momento processual, vislumbro a presença dos requisitos do art. 1.019, I, c.c. o art. 300 do CPC. A negativa de contratação, aliada à {'natureza alimentar do benefício' if c.assunto=='consignado' else 'impossibilidade de exigir prova de fato negativo'}, torna plausível o direito invocado, e o perigo de dano é evidente."))
        B.append(("p", "Assim, DEFIRO a antecipação da tutela recursal, até o julgamento deste recurso pela Turma Julgadora. Comunique-se ao juízo de origem, dispensadas as informações. Intime-se a parte agravada para resposta, nos termos do art. 1.019, II, do CPC."))
        B.append(("pn", local_data(c, d))); B.append(("sig", [c.relator.upper(), "Relator" if c.relator_g == "m" else "Relatora"]))
        return dict(blocks=B, autor="relator", data=d, sub="decisao_monocratica_relator")
    B.append(capa_processo(c, x))
    titulo = ch(["DECISÃO", "DECISÃO", "DECISÃO INTERLOCUTÓRIA", None, None])
    if tipo == "saneamento" and rng.random() < .5: titulo = "DECISÃO SANEADORA"
    if titulo: B.append(("title", titulo))
    B.append(("pn", "Vistos."))
    if tipo == "tutela":
        defere = rng.random() < .65
        B.append(("p", f"Trata-se de {a['acao'].split(' C/C')[0].lower() if not trab else 'reclamação trabalhista'} ajuizada por {x['AUTOR']} em face de {c.reu.nome}, com pedido de tutela de urgência para " +
                  {"negativacao": "exclusão de seu nome dos cadastros de proteção ao crédito", "consignado": "suspensão dos descontos em seu benefício previdenciário", "revisional": "depósito das parcelas no valor incontroverso e manutenção na posse do bem"}[c.assunto] + "."))
        if defere:
            B.append(("p", ch(["Em análise sumária, típica deste momento processual, estão presentes os requisitos do art. 300 do Código de Processo Civil.", "Nos termos do art. 300 do CPC, a tutela de urgência será concedida quando houver elementos que evidenciem a probabilidade do direito e o perigo de dano. É o caso dos autos."])))
            B.append(("p", {"negativacao": f"A parte autora nega a contratação, não sendo possível exigir-lhe prova de fato negativo. O perigo de dano decorre da manutenção da restrição, que impede o acesso ao crédito. A medida, ademais, é reversível.",
                            "consignado": "Os descontos incidem sobre verba de natureza alimentar de pessoa idosa, e a parte autora nega veementemente a contratação, havendo indícios de fraude. A medida é reversível, pois, comprovada a regularidade, os descontos poderão ser retomados.",
                            "revisional": "A abusividade dos juros, à primeira vista, é verossímil, considerando a diferença expressiva em relação à taxa média de mercado. Contudo, a descaracterização da mora exige o depósito do valor incontroverso, nos termos do art. 330, § 3º, do CPC."}[c.assunto]))
            B.append(("p", "Ante o exposto, DEFIRO a tutela de urgência para " + {"negativacao": f"determinar que {x['oR']} {x['R']} promova a exclusão do nome d{x['oA']} {x['A']} dos cadastros de inadimplentes, relativamente ao débito discutido, no prazo de 5 (cinco) dias, sob pena de multa diária de R$ 300,00, limitada a R$ 10.000,00.",
                     "consignado": f"determinar a suspensão dos descontos referentes ao contrato nº {c.contrato}, no prazo de 10 (dez) dias, sob pena de multa de R$ 500,00 por desconto indevido. Oficie-se ao INSS.",
                     "revisional": f"autorizar o depósito judicial das parcelas vincendas no valor de {money(round(getattr(c,"parcela",0)*.78,2))}, e, enquanto efetuados os depósitos, determinar que {x['oR']} {x['R']} se abstenha de inscrever o nome d{x['oA']} {x['A']} nos cadastros de inadimplentes."}[c.assunto]))
        else:
            B.append(("p", "Não vislumbro, neste momento, a presença dos requisitos do art. 300 do CPC. " + ch(["As alegações demandam dilação probatória, sendo necessária a instauração do contraditório.", "A documentação que instrui a inicial não permite aferir, em cognição sumária, a probabilidade do direito.", "O perigo de dano não restou demonstrado, notadamente considerando o lapso temporal entre o fato e o ajuizamento."])))
            B.append(("p", "Ante o exposto, INDEFIRO a tutela de urgência."))
        B.append(("p", "Defiro a gratuidade da justiça." if c.gratuidade else "Anote-se o recolhimento das custas iniciais."))
        if c.justica == "civel":
            B.append(("p", ch(["Deixo de designar audiência de conciliação, diante das especificidades da causa e da baixa taxa de acordos em demandas desta natureza, sem prejuízo de sua realização a qualquer tempo.", f"Designo audiência de conciliação para o dia {dfmt(bizday(d, rng.randint(40,90)))}, às {rng.randint(9,16)}h{ch(['00','30'])}, a ser realizada por videoconferência pelo CEJUSC."]) ))
            B.append(("p", f"Cite-se e intime-se {x['oR']} {x['R']}, com as advertências legais. Inverto o ônus da prova, nos termos do art. 6º, VIII, do CDC." if rng.random() < .6 else f"Cite-se {x['oR']} {x['R']} para contestar no prazo de 15 dias."))
        else:
            B.append(("p", "Cite-se e intime-se para a audiência de conciliação, com as advertências do art. 20 da Lei nº 9.099/95."))
        B.append(("p", ch(["Servirá a presente decisão, por cópia digitada, como mandado/ofício.", "Intime-se.", "Int."])))
    elif tipo == "saneamento":
        B.append(("p", "Passo ao saneamento e à organização do processo, nos termos do art. 357 do Código de Processo Civil." if not trab else "Passo a sanear o feito."))
        for t, p in F(a["preliminares"], x):
            B.append(("p", f"Rejeito a preliminar de {re.sub(r'^(da|do|das|dos) ', '', t.replace('PRELIMINARMENTE – ', '').lower())}, " + ch(["pois a matéria se confunde com o mérito.", "uma vez que presentes as condições da ação, segundo a teoria da asserção.", "nos termos já expostos pelo autor em réplica, que ora adoto como razão de decidir."])))
        B.append(("p", "Não há outras questões processuais pendentes. Presentes os pressupostos processuais e as condições da ação, declaro saneado o processo."))
        pts = {"negativacao": ["a existência de relação jurídica entre as partes e a autenticidade da assinatura/validação biométrica", "a regularidade da inscrição", "a ocorrência e a extensão do dano moral"],
               "consignado": ["a autenticidade da assinatura lançada no contrato", "a efetiva disponibilização do crédito em conta do autor", "a ocorrência de dano moral"],
               "revisional": ["a abusividade da taxa de juros em relação à média de mercado", "a regularidade das tarifas e do seguro", "a existência de valores pagos a maior"],
               "fraude_pix": ["a atipicidade das transações em relação ao perfil do correntista", "a adoção de mecanismos de segurança pela instituição", "a ocorrência de dano moral"],
               "tarifas": ["a contratação do pacote de serviços", "a natureza da conta"],
               "horas_extras": ["as reais atribuições do reclamante e a existência de fidúcia especial", "a jornada efetivamente cumprida", "a cobrança abusiva de metas"],
               "equiparacao": ["a identidade de funções entre reclamante e paradigma", "a diferença de tempo na função", "a quitação da PLR"]}[c.assunto]
        B.append(("p", "Fixo como pontos controvertidos: " + "; ".join(f"({ROM[i].lower()}) {p}" for i, p in enumerate(pts)) + "."))
        if a["pericia"] in ("grafotécnica", "contabil"):
            per = c.perito[0]
            B.append(("p", f"Mantenho a distribuição do ônus da prova na forma do art. 6º, VIII, do CDC e do art. 429, II, do CPC, cabendo {x['aoR']} {x['R']} a prova da autenticidade da contratação." if a["pericia"] == "grafotécnica" else "Mantenho o ônus da prova conforme a regra do art. 373 do CPC."))
            B.append(("p", f"Defiro a produção de prova pericial {'grafotécnica' if a['pericia']=='grafotécnica' else 'contábil'} e nomeio perit{'a' if c.perito[1]=='f' else 'o'} {'a' if c.perito[1]=='f' else 'o'} Sr(a). {per}, que deverá ser intimad{'a' if c.perito[1]=='f' else 'o'} para apresentar proposta de honorários em 5 dias (art. 465, § 2º, do CPC). Os honorários periciais serão custeados {'pelo réu' if a['pericia']=='grafotécnica' else 'pela parte requerente'}."))
            B.append(("p", "Faculto às partes, no prazo de 15 dias, a arguição de impedimento ou suspeição, a indicação de assistentes técnicos e a apresentação de quesitos (art. 465, § 1º, do CPC)."))
        else:
            B.append(("p", f"Defiro a produção de prova oral, consistente no depoimento pessoal das partes e na oitiva de testemunhas, limitadas a {'três' if trab else 'três'} por parte. Designo audiência de instrução para o dia {dfmt(bizday(d, rng.randint(40,120)))}, às {rng.randint(9,16)}h{ch(['00','30'])}."))
        B.append(("p", "As partes têm o direito de pedir esclarecimentos ou solicitar ajustes no prazo comum de 5 dias, findo o qual a decisão se torna estável (art. 357, § 1º, do CPC)." if not trab else "Intimem-se."))
    elif tipo == "gratuidade":
        defere = rng.random() < .6
        B.append(("p", f"{x['OA']} {x['A']} requereu a concessão dos benefícios da gratuidade da justiça, juntando {ch(['declaração de hipossuficiência', 'declaração de hipossuficiência e extratos bancários', 'holerite e declaração de isento do imposto de renda'])}."))
        if defere:
            B.append(("p", "Os documentos juntados demonstram a insuficiência de recursos para arcar com as custas e despesas processuais sem prejuízo do próprio sustento. DEFIRO, pois, a gratuidade da justiça, nos termos do art. 98 do CPC. Anote-se."))
        else:
            B.append(("p", f"A presunção de veracidade da declaração de pobreza é relativa (art. 99, § 2º, do CPC). No caso, os elementos dos autos – {ch(['renda mensal declarada superior a três salários mínimos', 'movimentação bancária incompatível com a alegada hipossuficiência', 'contratação de financiamento de valor expressivo'])} – infirmam a alegação."))
            B.append(("p", f"Assim, INDEFIRO o pedido de gratuidade da justiça. Recolha {x['oA']} {x['A']} as custas iniciais, no prazo de 15 dias, sob pena de cancelamento da distribuição (art. 290 do CPC). Faculto, alternativamente, o parcelamento das custas, nos termos do art. 98, § 6º, do CPC."))
        B.append(("pn", "Intime-se."))
    elif tipo == "sisbajud":
        val = money(round(c.valor_causa * rng.uniform(.3, .9), 2))
        B.append(("p", f"Trata-se de cumprimento de sentença. Intimad{x['oR']} nos termos do art. 523 do CPC{' (ou art. 880 da CLT)' if trab and rng.random()<.2 else ''}, {x['oR']} {'executada' if trab else 'executad' + x['oR']} não efetuou o pagamento voluntário do débito, que, segundo a planilha de fls. {rng.randint(500,700)}, atualizada até {dfmt(d - dt.timedelta(days=20))}, perfaz {val}, já incluídos multa e honorários de 10% (art. 523, § 1º, do CPC)." if not trab else
                  f"Trata-se de execução trabalhista. Citada nos termos do art. 880 da CLT, a executada não pagou nem garantiu a execução, cujo valor, conforme cálculos homologados, perfaz {val}."))
        B.append(("p", f"Defiro o pedido de bloqueio de ativos financeiros por meio do sistema SISBAJUD, até o limite do débito, com fundamento no art. 854 do CPC" + (" e no art. 882 da CLT" if trab else "") + ". Determino a utilização da funcionalidade de reiteração automática (\"teimosinha\") pelo prazo de 30 dias."))
        B.append(("p", "Havendo bloqueio, intime-se o(a) executado(a) para, no prazo de 5 dias, comprovar eventual impenhorabilidade (art. 854, § 3º, do CPC). Decorrido o prazo sem manifestação, converta-se a indisponibilidade em penhora, com transferência para conta judicial."))
        B.append(("p", "Resultando negativa a diligência, manifeste-se o(a) exequente em termos de prosseguimento, em 15 dias, sob pena de suspensão (art. 921, III, do CPC)."))
        B.append(("pn", "Intimem-se."))
    else:  # impugnacao
        B.append(("p", f"Trata-se de impugnação ao cumprimento de sentença apresentada por {c.reu.nome}, alegando excesso de execução, ao argumento de que {ch(['a exequente aplicou índice de correção diverso do fixado no título', 'os juros de mora foram computados desde data anterior à fixada na sentença', 'houve incidência indevida da multa do art. 523, § 1º, do CPC sobre valor tempestivamente depositado'])}."))
        B.append(("p", f"Remetidos os autos à contadoria judicial, apurou-se como devido o valor de {money(round(c.valor_causa*rng.uniform(.3,.8),2))} (fls. {rng.randint(600,800)})."))
        ac = rng.random() < .5
        B.append(("p", ("Assiste razão parcial à impugnante. Os cálculos da contadoria, elaborados por órgão auxiliar equidistante das partes, observaram fielmente os parâmetros do título executivo e merecem ser acolhidos." if ac else
                        "Não assiste razão à impugnante. Os cálculos da exequente observaram o título executivo, conforme confirmado pela contadoria judicial.")))
        B.append(("p", ("ACOLHO PARCIALMENTE a impugnação, para fixar o débito no valor apurado pela contadoria. Diante da sucumbência recíproca, condeno as partes ao pagamento de honorários de 10% sobre o proveito econômico obtido por cada uma." if ac else
                        "REJEITO a impugnação ao cumprimento de sentença. Sem honorários nesta fase (Súmula 519 do STJ).") + " Preclusa esta decisão, expeça-se mandado de levantamento em favor da parte exequente."))
        B.append(("pn", "Intimem-se."))
    B.append(("pn", local_data(c, d))); B.append(("sig", juiz_sig(c, d)))
    return dict(blocks=B, autor="juiz", data=d, sub=f"decisao_{tipo}")

# ================================================================= DESPACHO
DESP = [
 "Cite-se {pR_art} {R}, por carta com aviso de recebimento, para contestar no prazo de 15 (quinze) dias, sob pena de revelia.",
 "Manifeste-se {oA} {A} sobre a contestação e documentos, no prazo de 15 (quinze) dias.",
 "Especifiquem as partes, no prazo de 5 (cinco) dias, as provas que pretendem produzir, justificando sua pertinência, sob pena de indeferimento.",
 "Intime-se o(a) perito(a) nomeado(a) para que informe se aceita o encargo e apresente proposta de honorários, no prazo de 5 (cinco) dias.",
 "Ciência às partes do retorno dos autos da Superior Instância. Requeira a parte interessada o que de direito, no prazo de 15 (quinze) dias. No silêncio, arquivem-se.",
 "Emende {oA} {A} a petição inicial, no prazo de 15 (quinze) dias, sob pena de indeferimento (art. 321 do CPC), para juntar comprovante de residência atualizado em seu nome.",
 "Recebo a apelação. Intime-se a parte apelada para apresentar contrarrazões, no prazo legal. Após, com ou sem resposta, remetam-se os autos ao Egrégio Tribunal de Justiça, com as homenagens deste Juízo (art. 1.010, § 3º, do CPC).",
 "Junte {oR} {R}, no prazo de 15 (quinze) dias, cópia integral do contrato nº {contrato} e do respectivo comprovante de disponibilização do crédito.",
 "Manifeste-se a parte contrária sobre os embargos de declaração opostos, no prazo de 5 (cinco) dias (art. 1.023, § 2º, do CPC).",
 "Fls. {fl}: defiro o prazo de 30 (trinta) dias, conforme requerido.",
 "Aguarde-se o cumprimento do mandado expedido.",
 "Diante do trânsito em julgado, requeira a parte vencedora o que de direito, no prazo de 30 (trinta) dias. Nada sendo requerido, arquivem-se os autos.",
 "Intimem-se as partes sobre o laudo pericial juntado, para manifestação no prazo comum de 15 (quinze) dias (art. 477, § 1º, do CPC).",
 "Considerando o depósito efetuado, manifeste-se {oA} credor{a_fem}, em 5 (cinco) dias. Havendo concordância, expeça-se mandado de levantamento eletrônico.",
 "Anote-se a habilitação do(a) novo(a) patrono(a). Intime-se.",
 "Tendo em vista a certidão do Oficial de Justiça, manifeste-se {oA} {A} sobre o prosseguimento do feito, indicando novo endereço para citação, no prazo de 15 (quinze) dias.",
 "Fls. {fl}: ciência à parte contrária.",
 "Vista ao Ministério Público.",
 "Remetam-se os autos à Contadoria Judicial para conferência dos cálculos apresentados.",
 "Aguarde-se a realização da audiência designada.",
]
DESP_TRAB = [
 "Notifique-se a reclamada para, querendo, manifestar-se sobre os cálculos apresentados pelo reclamante, no prazo de 8 (oito) dias, sob pena de preclusão (art. 879, § 2º, da CLT).",
 "Intime-se o reclamante para manifestação sobre a defesa e documentos, no prazo de 10 (dez) dias.",
 "Recebo o recurso ordinário interposto pela reclamada, porquanto tempestivo e preparado. Intime-se o reclamante para contrarrazões no prazo legal. Após, remetam-se os autos ao Egrégio Tribunal Regional do Trabalho.",
 "Retire-se o processo da pauta. Aguarde-se a devolução da carta precatória inquiritória.",
 "Intime-se a reclamada para comprovar o recolhimento das contribuições previdenciárias, no prazo de 15 (quinze) dias.",
 "Ciência às partes do retorno dos autos do E. TRT. Apresente o reclamante seus cálculos de liquidação, no prazo de 30 (trinta) dias.",
 "Libere-se ao reclamante o valor do depósito recursal, mediante alvará/transferência, após o trânsito em julgado.",
]
def despacho(c):
    x = ctx(c); x["pR_art"] = x["oR"]; B = []; trab = c.justica == "trab"
    d = bizday(c.dist, rng.randint(5, 900))
    B.append(capa_processo(c, x) if rng.random() < .85 else ("pn", proc_line(c)))
    t = ch(["DESPACHO", "DESPACHO", "DESPACHO", None, None, "Despacho"])
    if t: B.append(("title", t))
    if rng.random() < .6: B.append(("pn", ch(["Vistos.", "Vistos.", "Vistos etc.", "Vistos em correição."])))
    pool = DESP_TRAB + DESP[:4] if trab else DESP
    k = rng.choices([1, 2, 3], [6, 3, 1])[0]
    for s in rng.sample(pool, k):
        x["fl"] = f"{rng.randint(40,400)}"
        B.append(("p", s.format(**x)))
    B.append(("pn", ch(["Int.", "Intime-se.", "Intimem-se.", "Cumpra-se.", "Int. e cumpra-se.", ""])))
    B.append(("pn", local_data(c, d))); B.append(("sig", juiz_sig(c, d)))
    B = [b for b in B if not (b[0] == "pn" and b[1] == "")]
    return dict(blocks=B, autor="juiz", data=d, sub="despacho")

# ================================================================= EMBARGOS DE DECLARAÇÃO
def embargos_declaracao(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    contra = rng.choice(["sentença", "sentença", "acórdão"])
    lado = lado_perdedor(c) if rng.random() < .7 else ("a" if lado_perdedor(c) == "r" else "r")
    d = bizday(c.data_sent if contra == "sentença" else c.data_acord, rng.randint(3, 8))
    if contra == "acórdão":
        rel = "Relatora" if c.relator_g == "f" else "Relator"
        B.append(("addr", f"EXCELENTÍSSIMO(A) SENHOR(A) {'DESEMBARGADOR(A)' if c.justica!='jec' else 'JUIZ(A)'} {rel.upper()} {c.relator.upper()} DA {(c.turma if c.justica!='civel' else c.camara).upper()} DO {c.trib if c.justica!='jec' else 'COLÉGIO RECURSAL'}"))
    else:
        B.append(("addr", enderecamento(c)))
    B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 8))
    parte = f"{x['AUTOR']}" if lado == "a" else f"{c.reu.nome}"
    adv = c.adv_a if lado == "a" else c.adv_r
    vrb = ch(["opor", "opor", "interpor"])
    B.append(("p", f"{parte}, já qualificad{(x['oA'] if lado=='a' else x['oR'])} nos autos em epígrafe, {'em que contende com' if rng.random()<.5 else 'movidos por/em face de'} {c.reu.nome if lado=='a' else x['AUTOR']}, vem, respeitosamente, por seu advogado, com fundamento no {'art. 897-A da CLT c/c art. 1.022 do CPC' if trab else 'art. 1.022 do Código de Processo Civil' if c.justica=='civel' else 'art. 48 da Lei nº 9.099/95 c/c art. 1.022 do CPC'}, {vrb}"))
    B.append(("title", "EMBARGOS DE DECLARAÇÃO" + ch(["", "", " COM EFEITOS INFRINGENTES", " PARA FINS DE PREQUESTIONAMENTO" if contra == "acórdão" else ""])))
    B.append(("p", f"em face d{'a r. sentença' if contra=='sentença' else 'o v. acórdão'} de {ch(['fls. '+str(rng.randint(300,600)), 'Id. '+format(rng.randint(10**6,10**7),'x'), 'evento '+str(rng.randint(40,140))])}, pelas razões a seguir expostas."))
    B.append(("h", "I – DA TEMPESTIVIDADE"))
    B.append(("p", f"{'A' if contra=='sentença' else 'O'} {'r. sentença' if contra=='sentença' else 'v. acórdão'} foi disponibilizad{'a' if contra=='sentença' else 'o'} no Diário de Justiça Eletrônico em {dfmt(d - dt.timedelta(days=rng.randint(2,4)))}, considerando-se publicad{'a' if contra=='sentença' else 'o'} no primeiro dia útil subsequente. Opostos dentro do prazo de 5 (cinco) dias, os presentes embargos são tempestivos."))
    B.append(("h", "II – DO VÍCIO APONTADO" if rng.random() < .5 else "II – DA OMISSÃO / CONTRADIÇÃO"))
    vic = rng.choice(["juros", "compensacao", "honorarios", "gratuidade", "prova"])
    txt = {"juros": f"{'A' if contra=='sentença' else 'O'} decisão embargada condenou {'a parte ré' if lado=='a' else 'a embargante'} ao pagamento de indenização, mas foi omiss{'a' if contra=='sentença' else 'o'} quanto ao termo inicial dos juros de mora e ao índice de correção monetária a ser adotado, especialmente diante da entrada em vigor da Lei nº 14.905/2024, que alterou os arts. 389 e 406 do Código Civil.",
           "compensacao": "A embargante requereu expressamente, em sua defesa, a compensação dos valores efetivamente creditados em favor da parte contrária, a fim de evitar enriquecimento sem causa. Contudo, a decisão embargada não se pronunciou sobre o pedido, incorrendo em omissão que deve ser sanada.",
           "honorarios": "Há contradição na decisão embargada, que reconheceu a sucumbência mínima de uma das partes na fundamentação, mas, no dispositivo, distribuiu os ônus sucumbenciais de forma recíproca, em desacordo com o art. 86, parágrafo único, do CPC.",
           "gratuidade": f"A decisão embargada deixou de apreciar o pedido de gratuidade da justiça formulado na {'inicial' if lado=='a' else 'contestação'} e reiterado em {'réplica' if lado=='a' else 'memoriais'}, o que gera insegurança quanto à exigibilidade das verbas sucumbenciais.",
           "prova": "A decisão embargada fundamentou-se na ausência de prova da contratação, porém deixou de enfrentar os documentos juntados com a contestação, especialmente o relatório de autenticação digital e o comprovante de crédito, argumentos capazes de, em tese, infirmar a conclusão adotada (art. 489, § 1º, IV, do CPC)."}[vic]
    B.append(("p", txt))
    B.append(("p", "Nos termos do art. 1.022 do CPC, cabem embargos de declaração para esclarecer obscuridade ou eliminar contradição, suprir omissão de ponto ou questão sobre o qual devia se pronunciar o juiz de ofício ou a requerimento, e corrigir erro material."))
    if contra == "acórdão" or rng.random() < .3:
        B.append(("h", "III – DO PREQUESTIONAMENTO"))
        B.append(("p", "Ainda que assim não se entenda, os presentes embargos são opostos com o propósito de prequestionamento dos arts. 14 e 42 do CDC, 186 e 927 do Código Civil e 373 e 489 do CPC, nos termos da Súmula 98 do STJ, não possuindo caráter protelatório." if not trab else "Requer o prequestionamento da matéria, nos termos da Súmula 297 do TST, para fins de eventual recurso de revista."))
    B.append(("h", f"{'IV' if len([b for b in B if b[0]=='h'])>=3 else 'III'} – DO PEDIDO"))
    B.append(("p", f"Diante do exposto, requer o conhecimento e o provimento dos presentes embargos de declaração, a fim de que seja sanad{'a a omissão' if vic!='honorarios' else 'a contradição'} apontad{'a'}" + (", atribuindo-lhes efeitos infringentes, com a prévia intimação da parte embargada (art. 1.023, § 2º, do CPC)." if rng.random() < .5 else ".")))
    B.append(("pn", pedir_def()))
    B.append(("sig", adv_sig(c, adv, x, d)))
    return dict(blocks=B, autor="adv_a" if lado == "a" else "adv_r", data=d, sub=f"embargos_declaracao_{'sentenca' if contra=='sentença' else 'acordao'}")

# ================================================================= RECURSO (APELAÇÃO / RI / RO)
def recurso_apelacao(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; jec = c.justica == "jec"
    lado = lado_perdedor(c); d = bizday(c.data_sent, rng.randint(10, 22))
    adv = c.adv_a if lado == "a" else c.adv_r
    parte = x["AUTOR"] if lado == "a" else c.reu.nome
    nm = "RECURSO ORDINÁRIO" if trab else "RECURSO INOMINADO" if jec else "RECURSO DE APELAÇÃO"
    fund = "art. 895, I, da CLT" if trab else "arts. 41 e seguintes da Lei nº 9.099/95" if jec else "arts. 1.009 e seguintes do Código de Processo Civil"
    B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 8))
    B.append(("p", f"{parte}, já qualificad{x['oA'] if lado=='a' else x['oR']} nos autos da ação em epígrafe, que {'move em face de ' + c.reu.nome if lado=='a' else 'lhe move ' + x['AUTOR']}, inconformad{x['oA'] if lado=='a' else x['oR']} com a r. sentença de {ch(['fls. '+str(rng.randint(300,500)), 'Id. '+format(rng.randint(10**6,10**7),'x'), 'mov. '+str(rng.randint(60,140))])}, vem, respeitosamente, por seu advogado, com fundamento nos {fund}, interpor o presente"))
    B.append(("title", nm))
    B.append(("p", f"requerendo seja o recurso recebido e processado, com as inclusas razões, e remetido ao {'Egrégio Tribunal Regional do Trabalho' if trab else 'Colégio Recursal' if jec else 'Egrégio Tribunal de Justiça'}, após o cumprimento das formalidades legais."))
    if lado == "r":
        B.append(("p", f"Informa o recolhimento do preparo{' (custas e depósito recursal)' if trab else ''}, conforme guia{'s' if trab else ''} e comprovante{'s' if trab else ''} anexo{'s' if trab else ''}, no valor de {money(round(max(c.valor_causa*0.04, 250),2))}" + (" e " + money(ch([13133.46, 26266.92])) + " a título de depósito recursal." if trab else ".")))
    else:
        B.append(("p", "Deixa de recolher o preparo por ser beneficiári" + x["oA"] + " da gratuidade da justiça." if c.gratuidade else "Junta o comprovante de recolhimento do preparo."))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, adv, x, d)))
    B.append(("pb",))
    B.append(("title", "RAZÕES DO " + nm if trab or jec else "RAZÕES DE APELAÇÃO"))
    B.append(("kv", [("Recorrente" if trab or jec else "Apelante", parte), ("Recorrido" if trab or jec else "Apelado", c.reu.nome if lado == "a" else x["AUTOR"]), ("Origem", c.vara), ("Processo nº", c.numero)]))
    B.append(("pn", ch(["EGRÉGIO TRIBUNAL,", "COLENDA CÂMARA,", "EMÉRITOS JULGADORES,", "ÍNCLITOS DESEMBARGADORES,"]) if not (trab or jec) else ch(["EGRÉGIO TRIBUNAL,", "COLENDA TURMA,", "NOBRES JULGADORES,"])))
    B.append(("h", "I – DA TEMPESTIVIDADE E DO PREPARO"))
    B.append(("p", f"O recurso é tempestivo, pois interposto dentro do prazo de {'8 (oito)' if trab else '10 (dez)' if jec else '15 (quinze) dias úteis'}{'' if not trab else ' dias'} contado da intimação da sentença. " + ("O preparo foi regularmente recolhido." if lado == "r" else "Isento de preparo, em razão da gratuidade concedida.")))
    B.append(("h", "II – SÍNTESE DA DEMANDA"))
    B.append(("p", f"Cuida-se de ação em que {x['oA']} {x['A']} alega {RESUMO[c.assunto][0].format(**x)}. A r. sentença julgou {'procedente' if c.resultado=='proc' else 'parcialmente procedente' if c.resultado=='parc' else 'improcedente'} o pedido" + (", para " + a["disp_proc"].format(**x)[:400] + "..." if c.resultado != "improc" and rng.random() < .6 else ".")))
    B.append(("p", "Contudo, a decisão merece reforma, como se passa a demonstrar." if rng.random() < .5 else "Data maxima venia, a r. sentença não deu a melhor solução à lide."))
    B.append(("h", "III – DAS RAZÕES PARA A REFORMA"))
    if lado == "r":
        for i, (t, p) in enumerate(F(a["defesa"], x)):
            B.append(("h2", f"III.{i+1} – {t}")); B.append(("p", p))
        B.append(("p", "Subsidiariamente, caso mantida a condenação, impõe-se a redução do valor fixado a título de danos morais, que se mostra excessivo e destoa dos parâmetros adotados por este Tribunal em casos análogos." if c.assunto not in ("revisional", "equiparacao") else "Subsidiariamente, requer a revisão dos critérios de liquidação fixados."))
    else:
        for i, (t, p) in enumerate(F(a["direito"], x)):
            B.append(("h2", f"III.{i+1} – {t}")); B.append(("p", p))
        B.append(("p", f"O MM. Juízo a quo, ao {'julgar improcedente o pedido' if c.resultado=='improc' else 'afastar parte dos pedidos'}, deixou de considerar os elementos probatórios constantes dos autos, " + ch(["notadamente a impugnação específica aos documentos apresentados pela parte contrária.", "em evidente afronta ao art. 6º, VIII, do CDC.", "o que impõe a reforma da decisão."])))
    for dp in doutrina(c): B.append(("p", dp))
    B.append(("q", jurisp(c, x).replace("Sentença mantida. Recurso desprovido", "Sentença reformada. Recurso provido")))
    B.append(("h", "IV – DOS PEDIDOS"))
    B.append(("p", f"Diante do exposto, requer seja o presente recurso conhecido e PROVIDO, para reformar a r. sentença e {'julgar improcedentes os pedidos iniciais' if lado=='r' else 'julgar integralmente procedentes os pedidos formulados na inicial'}, invertendo-se os ônus da sucumbência" + (", com a majoração dos honorários advocatícios (art. 85, § 11, do CPC)." if not trab else ".")))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, adv, x, d)))
    return dict(blocks=B, autor="adv_a" if lado == "a" else "adv_r", data=d, sub="recurso_ordinario_trab" if trab else "recurso_inominado" if jec else "apelacao")

# ================================================================= CONTRARRAZÕES
def contrarrazoes(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"; jec = c.justica == "jec"
    perd = lado_perdedor(c); lado = "r" if perd == "a" else "a"; d = bizday(c.data_sent, rng.randint(30, 70))
    adv = c.adv_a if lado == "a" else c.adv_r
    parte = x["AUTOR"] if lado == "a" else c.reu.nome; outro = c.reu.nome if lado == "a" else x["AUTOR"]
    rec = "recurso ordinário" if trab else "recurso inominado" if jec else "recurso de apelação"
    B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 8))
    B.append(("p", f"{parte}, já qualificad{x['oA'] if lado=='a' else x['oR']} nos autos em epígrafe, vem, respeitosamente, por seu advogado, no prazo legal, apresentar"))
    B.append(("title", f"CONTRARRAZÕES AO {rec.upper()}" if rng.random() < .7 else "CONTRARRAZÕES"))
    B.append(("p", f"interposto por {outro}, requerendo sejam recebidas e encaminhadas ao {'E. Tribunal Regional do Trabalho' if trab else 'Colégio Recursal' if jec else 'E. Tribunal de Justiça'}."))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, adv, x, d))); B.append(("pb",))
    B.append(("title", "CONTRARRAZÕES DE " + rec.upper().replace("RECURSO DE ", "")))
    B.append(("kv", [("Recorrente" if trab or jec else "Apelante", outro), ("Recorrido" if trab or jec else "Apelado", parte), ("Processo de origem", c.numero)]))
    B.append(("pn", ch(["EGRÉGIO TRIBUNAL,", "COLENDA CÂMARA,", "COLENDA TURMA,", "NOBRES JULGADORES,"])))
    n = 0
    if rng.random() < .5:
        B.append(("h", f"{ROM[n]} – PRELIMINARMENTE: DO NÃO CONHECIMENTO DO RECURSO")); n += 1
        B.append(("p", "O recurso não merece ser conhecido, pois a parte recorrente limitou-se a reproduzir os argumentos da " + ("contestação" if lado == "a" else "petição inicial") + ", sem impugnar especificamente os fundamentos da sentença, em afronta ao princípio da dialeticidade (art. 1.010, II e III, do CPC e Súmula 422 do TST, por analogia)." if True else ""))
    B.append(("h", f"{ROM[n]} – {ch(['DA MANUTENÇÃO DA R. SENTENÇA', 'DO MÉRITO RECURSAL', 'DAS RAZÕES PARA MANUTENÇÃO DA SENTENÇA'])}")); n += 1
    B.append(("p", "A r. sentença não merece qualquer reparo, tendo apreciado com acerto as provas produzidas e aplicado corretamente o direito à espécie. Como bem consignou o MM. Juízo de origem:"))
    src = a["fund_proc"] if c.resultado != "improc" else a["fund_improc"]
    B.append(("q", "\"" + " ".join(F(src, x)[:2]) + "\""))
    if lado == "a":
        for p in REPLICA[c.assunto]: B.append(("p", p.format(**x)))
    else:
        for t, p in F(a["defesa"], x)[:2]: B.append(("p", p))
    for dp in doutrina(c): B.append(("p", dp))
    if lado == "a" and c.assunto not in ("revisional", "equiparacao"):
        B.append(("h", f"{ROM[n]} – DO VALOR DA INDENIZAÇÃO")); n += 1
        B.append(("p", "O valor fixado a título de danos morais é razoável e proporcional, atendendo às funções compensatória e pedagógica da indenização, não comportando redução."))
    B.append(("h", f"{ROM[n]} – DO PEDIDO")); n += 1
    B.append(("p", f"Diante do exposto, requer {'o não conhecimento do recurso ou, no mérito, ' if any('NÃO CONHECIMENTO' in str(b[1]) for b in B if len(b)>1) else ''}seja NEGADO PROVIMENTO ao {rec}, mantendo-se a r. sentença por seus próprios e jurídicos fundamentos" + (", com a majoração dos honorários advocatícios, nos termos do art. 85, § 11, do CPC." if not trab else ".")))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, adv, x, d)))
    return dict(blocks=B, autor="adv_a" if lado == "a" else "adv_r", data=d, sub="contrarrazoes_" + ("ro" if trab else "ri" if jec else "apelacao"))

# ================================================================= AGRAVO DE INSTRUMENTO
def agravo_instrumento(c):
    x = ctx(c); a = A[c.assunto]; B = []
    d = bizday(c.dist, rng.randint(15, 60))
    obj = rng.choice(["tutela_indef", "gratuidade"] if a["tutela"] else ["gratuidade"])
    B.append(("addr", enderecamento(c, 2))); B.append(("sp", 10))
    B.append(("kv", [("Processo de origem", c.numero), ("Juízo de origem", c.vara), ("Agravante", x["AUTOR"]), ("Agravado(a)", c.reu.nome)]))
    B.append(("sp", 6))
    B.append(("p", f"{c.autor.qualif()}, vem, respeitosamente, por seus advogados, com fundamento nos arts. 1.015, {'I' if obj=='tutela_indef' else 'V'}, e seguintes do Código de Processo Civil, interpor"))
    B.append(("title", "AGRAVO DE INSTRUMENTO " + ch(["COM PEDIDO DE ANTECIPAÇÃO DA TUTELA RECURSAL", "COM PEDIDO DE EFEITO ATIVO", "COM PEDIDO LIMINAR"]) if obj == "tutela_indef" else "AGRAVO DE INSTRUMENTO COM PEDIDO DE EFEITO SUSPENSIVO"))
    B.append(("p", f"contra a r. decisão interlocutória proferida pelo MM. Juízo da {c.vara}, que {'indeferiu a tutela de urgência' if obj=='tutela_indef' else 'indeferiu o pedido de gratuidade da justiça'}, em face de {c.reu.qualif()}, pelas razões a seguir expostas."))
    B.append(("h", "I – DO CABIMENTO E DA TEMPESTIVIDADE"))
    B.append(("p", f"O recurso é cabível, pois a decisão agravada versa sobre {'tutela provisória' if obj=='tutela_indef' else 'rejeição do pedido de gratuidade da justiça'}, hipótese expressamente prevista no art. 1.015, {'I' if obj=='tutela_indef' else 'V'}, do CPC. É também tempestivo, interposto dentro do prazo de 15 (quinze) dias úteis previsto no art. 1.003, § 5º, do CPC."))
    B.append(("h", "II – DA FORMAÇÃO DO INSTRUMENTO"))
    B.append(("p", "Tratando-se de processo eletrônico, dispensa-se a juntada das peças obrigatórias, nos termos do art. 1.017, § 5º, do CPC. Não obstante, o agravante junta cópia da petição inicial, da decisão agravada e da procuração. Em atenção ao art. 1.016, IV, do CPC, informa os nomes e endereços dos advogados constantes do processo: pelo agravante, " + f"{c.adv_a.nome}, {c.adv_a.oab}; pelo agravado, ainda não constituído nos autos." ))
    B.append(("h", "III – DA DECISÃO AGRAVADA"))
    B.append(("q", "\"" + ("Não vislumbro, neste momento, a presença dos requisitos do art. 300 do CPC. As alegações demandam dilação probatória, sendo necessária a instauração do contraditório. Ante o exposto, INDEFIRO a tutela de urgência.\"" if obj == "tutela_indef" else "A presunção de veracidade da declaração de pobreza é relativa. Assim, INDEFIRO o pedido de gratuidade da justiça. Recolha o autor as custas iniciais, no prazo de 15 dias, sob pena de cancelamento da distribuição.\"")))
    B.append(("h", "IV – DAS RAZÕES DE REFORMA"))
    if obj == "tutela_indef":
        B.append(("p", a["tutela"].format(**x)))
        B.append(("p", "Exigir do consumidor, nesta fase, prova cabal da inexistência da contratação equivale a impor-lhe prova diabólica, incompatível com a sistemática protetiva do CDC. A decisão agravada, com a devida vênia, desconsiderou que a medida pleiteada é plenamente reversível."))
    else:
        B.append(("p", f"{x['OA']} agravante é {c.autor.prof}, com renda mensal inferior a três salários mínimos, conforme documentos juntados. A contratação de advogado particular não afasta o direito à gratuidade (art. 99, § 4º, do CPC), e a presunção do art. 99, § 3º, somente pode ser afastada mediante elementos concretos, inexistentes nos autos."))
    B.append(("q", jurisp(c, x).replace("APELAÇÃO", "AGRAVO DE INSTRUMENTO").replace("Sentença mantida. Recurso desprovido", "Decisão reformada. Recurso provido")))
    B.append(("h", "V – DO PEDIDO DE " + ("ANTECIPAÇÃO DA TUTELA RECURSAL" if obj == "tutela_indef" else "EFEITO SUSPENSIVO")))
    B.append(("p", "Presentes a probabilidade de provimento do recurso e o risco de dano grave ou de difícil reparação, requer, nos termos do art. 1.019, I, do CPC, " + ("a antecipação da tutela recursal, para deferir a medida pleiteada na origem." if obj == "tutela_indef" else "a atribuição de efeito suspensivo, para sustar a exigência de recolhimento das custas até o julgamento do recurso.")))
    B.append(("h", "VI – DOS PEDIDOS"))
    for i, p in enumerate(["o recebimento e processamento do presente agravo, com a concessão da medida liminar requerida;",
                           "a intimação do agravado para, querendo, apresentar contraminuta (art. 1.019, II, do CPC);",
                           "a comunicação ao juízo de origem;",
                           "ao final, o provimento do recurso, reformando-se a r. decisão agravada" + (" para conceder a tutela de urgência." if obj == "tutela_indef" else " para conceder a gratuidade da justiça.")]):
        B.append(("li", f"{chr(97+i)}) {p}"))
    B.append(("pn", pedir_def())); B.append(("sig", adv_sig(c, c.adv_a, x, d)))
    return dict(blocks=B, autor="adv_a", data=d, sub="agravo_instrumento")

# ================================================================= PROCURAÇÃO
def procuracao(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    banco = rng.random() < .3 and c.justica != "trab"
    d = c.dist - dt.timedelta(days=rng.randint(2, 60))
    B.append(("title", ch(["PROCURAÇÃO AD JUDICIA ET EXTRA", "PROCURAÇÃO", "PROCURAÇÃO \"AD JUDICIA\"", "INSTRUMENTO PARTICULAR DE PROCURAÇÃO", "PROCURAÇÃO AD JUDICIA"])))
    B.append(("sp", 6))
    if banco:
        d1, d2 = nome()[0], nome()[0]
        B.append(("p", f"OUTORGANTE: {c.reu.qualif()}, neste ato representada por seus Diretores, Srs. {d1} e {d2}, na forma de seu Estatuto Social."))
        adv = [c.adv_r, c.adv_r2] + [type(c.adv_r)(c.uf, c.adv_r.escr) for _ in range(rng.randint(1, 4))]
        B.append(("p", f"OUTORGADOS: " + "; ".join(f"{v.nome}, {v.oab}" for v in adv) + f", todos integrantes da sociedade {c.adv_r.escr}, inscrita na OAB/{c.uf} sob o nº {rng.randint(1000,29999)}, com escritório na {ch(['Rua Líbero Badaró, nº 425, 18º andar, Centro, São Paulo/SP', 'Avenida Engenheiro Luís Carlos Berrini, nº 1.140, 8º andar, São Paulo/SP', 'Rua da Bahia, nº 1.148, sala 1.204, Belo Horizonte/MG'])}."))
        B.append(("p", "PODERES: os da cláusula ad judicia et extra, para o foro em geral, em qualquer Juízo, Instância ou Tribunal, podendo propor contra quem de direito as ações competentes e defender a outorgante nas contrárias, seguindo umas e outras até final decisão, usando os recursos legais e acompanhando-os, conferindo-lhes, ainda, poderes especiais para receber citação, confessar, reconhecer a procedência do pedido, transigir, desistir, renunciar ao direito sobre o qual se funda a ação, receber, dar quitação, firmar compromisso e substabelecer, com ou sem reservas de poderes, especialmente para atuar nas demandas de natureza cível e consumerista em que a outorgante figure como parte no Estado de " + {"SP": "São Paulo", "MG": "Minas Gerais", "RJ": "Rio de Janeiro", "PR": "Paraná"}[c.uf] + "."))
        B.append(("p", f"VALIDADE: {ch(['até 31 de dezembro de '+str(d.year+1), 'por prazo indeterminado, até revogação expressa', '1 (um) ano a contar desta data'])}."))
        B.append(("pn", f"São Paulo, {dext(d)}."))
        B.append(("sigs", [[f"{c.reu.nome}", f"{d1} – Diretor"], ["", f"{d2} – Diretor"]]))
        return dict(blocks=B, autor="parte_r", data=d, sub="procuracao_pj", scan_bias=.45)
    B.append(("p", f"OUTORGANTE: {c.autor.qualif()}."))
    advs = [c.adv_a] + ([type(c.adv_a)(c.uf, c.adv_a.escr)] if rng.random() < .5 else [])
    B.append(("p", "OUTORGADO(S): " + "; ".join(f"{v.nome}, advogad{'a' if v.g=='f' else 'o'}, inscrit{'a' if v.g=='f' else 'o'} na {v.oab}" for v in advs) + f", com escritório profissional na {ch(['Rua Coronel Marcondes', 'Avenida Nove de Julho', 'Rua Barão de Itapetininga', 'Avenida Afonso Pena'])}, nº {rng.randint(10,2000)}, {ch(['sala '+str(rng.randint(1,30)), 'conjunto '+str(rng.randint(11,99)), ''])}, {c.cidade}/{c.uf}, endereço eletrônico contato@{c.adv_a.escr.split()[0].lower().replace(',','').replace('&','')}adv.com.br."))
    B.append(("p", "PODERES: Pelo presente instrumento particular de procuração, a(o) outorgante nomeia e constitui seu(s) bastante(s) procurador(es) o(s) outorgado(s), a quem confere amplos poderes para o foro em geral, com a cláusula ad judicia et extra, em qualquer Juízo, Instância ou Tribunal, podendo propor contra quem de direito as ações competentes e defendê-la(o) nas contrárias, seguindo umas e outras até final decisão, usando os recursos legais e acompanhando-os, conferindo-lhe(s) ainda poderes especiais para confessar, desistir, transigir, firmar compromissos ou acordos, receber e dar quitação, levantar alvarás e mandados de levantamento, renunciar ao direito sobre o qual se funda a ação, assinar declaração de hipossuficiência econômica (art. 105 do CPC), agindo em conjunto ou separadamente, podendo ainda substabelecer esta a outrem, com ou sem reservas de iguais poderes."))
    alvo = "ajuizar reclamação trabalhista em face de " + c.reu.nome if trab else "propor " + A[c.assunto]["acao"].split(" C/C")[0].lower() + " em face de " + c.reu.nome
    B.append(("p", f"ESPECIALMENTE para {alvo}."))
    B.append(("pn", f"{c.cidade}, {ch([dext(d), dfmt(d), '____ de ______________ de ' + str(d.year)])}."))
    B.append(("sign_hand", [c.autor.nome.upper(), "Outorgante"]))
    if rng.random() < .35:
        B.append(("pb",))
        B.append(("title", "DECLARAÇÃO DE HIPOSSUFICIÊNCIA" if rng.random() < .6 else "DECLARAÇÃO DE POBREZA"))
        B.append(("p", f"{c.autor.qualif()}, DECLARA, para os devidos fins e sob as penas da lei, que não possui condições de arcar com as custas processuais e honorários advocatícios sem prejuízo do próprio sustento e de sua família, razão pela qual faz jus aos benefícios da gratuidade da justiça, nos termos do art. 98 e seguintes do Código de Processo Civil{' e do art. 790, § 3º, da CLT' if trab else ''}."))
        B.append(("p", "Por ser expressão da verdade, firma a presente declaração, ciente de que a falsidade da declaração sujeita o declarante às sanções civis, administrativas e criminais previstas na legislação aplicável."))
        B.append(("pn", f"{c.cidade}, {dext(d)}."))
        B.append(("sign_hand", [c.autor.nome.upper(), "Declarante"]))
        sub = "procuracao_com_declaracao"
    else:
        sub = "procuracao_pf"
    return dict(blocks=B, autor="parte_a", data=d, sub=sub, scan_bias=.6)

# ================================================================= SUBSTABELECIMENTO
def substabelecimento(c):
    x = ctx(c); B = []
    lado = ch("ar"); adv = c.adv_a if lado == "a" else c.adv_r
    novo = type(adv)(c.uf, adv.escr if rng.random() < .5 else ch(["Correspondente Jurídico " + nome()[0].split()[0] + " Ltda.", "Advocacia Autônoma"]))
    reserva = rng.random() < .7
    d = bizday(c.dist, rng.randint(40, 700))
    B.append(("title", "SUBSTABELECIMENTO" + ch(["", " COM RESERVA DE PODERES" if reserva else " SEM RESERVA DE PODERES", ""])))
    if rng.random() < .6:
        B.append(("kv", [("Processo nº", c.numero), ("Juízo", c.vara), ("Partes", f"{x['AUTOR']} x {c.reu.nome}")]))
    parte = x["AUTOR"] if lado == "a" else c.reu.nome
    espec = ""
    if rng.random() < .4:
        espec = f", especificamente para o fim de {ch(['comparecer à audiência designada para o dia '+dfmt(bizday(d,rng.randint(3,20)))+', podendo transigir', 'realizar carga dos autos e extração de cópias', 'efetuar o levantamento de valores depositados nos autos', 'acompanhar a diligência de perícia designada'])}"
    B.append(("p", f"Pelo presente instrumento, {adv.nome.upper()}, advogad{'a' if adv.g=='f' else 'o'} inscrit{'a' if adv.g=='f' else 'o'} na {adv.oab}, SUBSTABELECE, {'COM' if reserva else 'SEM'} RESERVA DE IGUAIS PODERES, na pessoa de {novo.nome.upper()}, advogad{'a' if novo.g=='f' else 'o'} inscrit{'a' if novo.g=='f' else 'o'} na {novo.oab}, os poderes que lhe foram conferidos por {parte}, nos autos {'acima mencionados' if len(B)>1 and B[-1][0]=='kv' else 'do processo nº ' + c.numero + ', em trâmite perante a ' + c.vara}{espec}."))
    if not reserva:
        B.append(("p", "Requer, outrossim, que as futuras intimações sejam realizadas exclusivamente em nome do(a) substabelecido(a), sob pena de nulidade."))
    B.append(("pn", local_data(c, d)))
    B.append(("sig", [adv.nome.upper(), adv.oab]))
    if rng.random() < .3: B.append(("sig", ["De acordo:", novo.nome.upper(), novo.oab]))
    return dict(blocks=B, autor="adv_a" if lado == "a" else "adv_r", data=d, sub="substabelecimento_" + ("com" if reserva else "sem") + "_reserva", scan_bias=.35)

# ================================================================= CERTIDÃO
def certidao(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    tipo = rng.choices(["publicacao", "decurso", "transito", "oficial_pos", "oficial_neg", "juntada", "ato_ordinatorio", "remessa"], [5, 4, 4, 3, 3, 2, 4, 2])[0]
    d = bizday(c.dist, rng.randint(10, 900))
    servidor = nome(); cargo = ch(["Escrevente Técnico Judiciário", "Chefe de Seção Judiciário", "Escrivão Judicial", "Diretor de Secretaria", "Técnico Judiciário"])
    if trab: cargo = ch(["Diretor de Secretaria", "Técnico Judiciário", "Analista Judiciário"])
    if tipo != "publicacao" and rng.random() < .7: B.append(capa_processo(c, x))
    elif tipo == "publicacao": B.append(("kv", [("Processo", c.numero), ("Classe", c.classe)]))
    if tipo == "publicacao":
        B.append(("title", ch(["CERTIDÃO DE PUBLICAÇÃO DE RELAÇÃO", "CERTIDÃO DE PUBLICAÇÃO", "CERTIDÃO"])))
        rel = f"{rng.randint(1,999):04d}/{d.year}"
        B.append(("p", f"Certifico e dou fé que o ato abaixo foi disponibilizado no Diário da Justiça Eletrônico Nacional (DJEN) em {dfmt(d)}, considerando-se publicado no primeiro dia útil subsequente, nos termos do art. 4º, § 3º, da Lei nº 11.419/2006. Relação nº {rel}."))
        x["pR_art"] = x["oR"]; x["fl"] = str(rng.randint(40, 400))
        teor = rng.choice(DESP).format(**x)
        B.append(("pn", "Teor do ato: \"" + teor + "\""))
        B.append(("pn", f"Advogados(s): {c.adv_a.nome} ({c.adv_a.oab}), {c.adv_r.nome} ({c.adv_r.oab})"))
        B.append(("pn", f"Prazo: {ch(['15 dias', '5 dias', '30 dias', '10 dias'])} – início em {dfmt(bizday(d, 2))}."))
    elif tipo == "decurso":
        B.append(("title", ch(["CERTIDÃO", "CERTIDÃO DE DECURSO DE PRAZO", "CERTIDÃO – DECURSO DE PRAZO"])))
        B.append(("p", f"CERTIFICO e dou fé que decorreu o prazo legal sem que {ch([x['oR']+' '+x['R'], x['oA']+' '+x['A'], 'as partes'])} se manifestasse{'m' if rng.random()<.3 else ''} acerca do(a) {ch(['r. despacho de fls. '+str(rng.randint(80,400)), 'contestação e documentos', 'laudo pericial', 'decisão de fls. '+str(rng.randint(80,400)), 'intimação para pagamento voluntário (art. 523 do CPC)'])}. {ch(['Nada mais.', 'O referido é verdade e dou fé.', ''])}"))
    elif tipo == "transito":
        B.append(("title", "CERTIDÃO DE TRÂNSITO EM JULGADO"))
        dt_t = bizday(c.data_sent, rng.randint(20, 60))
        B.append(("p", f"CERTIFICO que a r. {ch(['sentença', 'sentença', 'decisão'])} de fls. {rng.randint(200,500)} transitou em julgado em {dfmt(dt_t)}, {ch(['sem interposição de recurso pelas partes', 'tendo as partes renunciado ao prazo recursal', 'após o julgamento do recurso pela Superior Instância'])}. {ch(['Certifico, ainda, que não há custas pendentes de recolhimento.', 'Certifico, mais, que foram recolhidas as custas finais.', ''])}"))
    elif tipo in ("oficial_pos", "oficial_neg"):
        B.append(("title", ch(["CERTIDÃO", "CERTIDÃO DO OFICIAL DE JUSTIÇA", "CERTIDÃO – MANDADO CUMPRIDO" + (" POSITIVO" if tipo=='oficial_pos' else " NEGATIVO")])))
        of = c.oficial; mand = f"{rng.randint(100,999)}.{d.year}/{rng.randint(1000,99999):06d}-{rng.randint(0,9)}"
        dest = ch(["citação", "intimação", "penhora e avaliação"]) if not trab else ch(["citação", "penhora"])
        alvo = c.reu.nome if dest != "intimação" else ch([c.reu.nome, x["AUTOR"]])
        end = c.reu.end if alvo == c.reu.nome else c.autor.end
        if tipo == "oficial_pos":
            rep = nome()[0]
            B.append(("p", f"CERTIFICO eu, Oficial{'a' if of[1]=='f' else ''} de Justiça, que em cumprimento ao mandado nº {mand}, dirigi-me ao endereço indicado, {end}, e, aí sendo, às {rng.randint(9,17)}h{rng.randint(0,59):02d} do dia {dfmt(d)}, procedi à {dest.upper()} de {alvo}" + (f", na pessoa de seu representante legal/gerente, Sr(a). {rep}" if alvo == c.reu.nome else "") + f", que, após a leitura do mandado, ficou ciente de todo o seu conteúdo, aceitou a contrafé e exarou sua assinatura. {ch(['O referido é verdade e dou fé.', 'Dou fé.', 'Nada mais.'])}"))
        else:
            mot = ch(["fui informado pelos moradores atuais de que a pessoa procurada mudou-se há cerca de um ano, para local ignorado", "o imóvel encontra-se fechado e desocupado, não tendo os vizinhos sabido informar o paradeiro do destinatário", "o número indicado não existe na referida via, conforme constatado no local e confirmado por moradores", f"o estabelecimento encontra-se desativado, funcionando no local outra empresa, que desconhece {alvo}"])
            B.append(("p", f"CERTIFICO eu, Oficial{'a' if of[1]=='f' else ''} de Justiça, que em cumprimento ao mandado nº {mand}, nos dias {dfmt(d - dt.timedelta(days=rng.randint(3,9)))} e {dfmt(d)}, em horários distintos, dirigi-me ao endereço {end} e ali DEIXEI DE PROCEDER à {dest} de {alvo}, tendo em vista que {mot}. Diante do exposto, devolvo o mandado ao cartório para as providências cabíveis. {ch(['O referido é verdade e dou fé.', 'Dou fé.'])}"))
        B.append(("pn", local_data(c, d)))
        B.append(("sig", [of[0].upper(), f"Oficial{'a' if of[1]=='f' else ''} de Justiça" + ch(["", " – Matrícula " + str(rng.randint(100000, 999999)), " Avaliador" + ("a" if of[1]=='f' else "")])]))
        return dict(blocks=B, autor="servidor", data=d, sub=f"certidao_{tipo}", scan_bias=.2, signer=of[0])
    elif tipo == "juntada":
        B.append(("title", ch(["CERTIDÃO DE JUNTADA", "CERTIDÃO", "TERMO DE JUNTADA"])))
        B.append(("p", f"Certifico e dou fé que, nesta data, juntei aos autos {ch(['o aviso de recebimento (AR) da carta de citação, devidamente cumprido', 'o ofício-resposta do INSS', 'a guia de depósito judicial apresentada pela parte ré', 'o laudo pericial encaminhado pelo perito nomeado', 'a carta precatória devolvida devidamente cumprida'])}, que segue{'m' if rng.random()<.2 else ''}. {ch(['Nada mais.', 'Dou fé.', ''])}"))
    elif tipo == "ato_ordinatorio":
        B.append(("title", ch(["ATO ORDINATÓRIO", "CERTIDÃO – ATO ORDINATÓRIO", "CERTIDÃO"])))
        B.append(("p", f"Certifico e dou fé que, nos termos do art. 203, § 4º, do CPC{' e do Provimento CG nº 3/2025' if c.uf=='SP' else ''}, pratiquei o seguinte ato ordinatório: " + ch([f"Fica {x['oA']} {x['A']} intimad{x['oA']} a se manifestar sobre a contestação e documentos, no prazo de 15 (quinze) dias.",
                    "Ficam as partes intimadas a especificar as provas que pretendem produzir, no prazo de 5 (cinco) dias.",
                    f"Manifeste-se {x['oA']} {x['A']} sobre a certidão negativa do Oficial de Justiça, no prazo de 5 (cinco) dias.",
                    f"Fica {x['oR']} {x['R']} intimad{x['oR']} a recolher as custas de diligência do Oficial de Justiça, no prazo de 5 (cinco) dias.",
                    "Ficam as partes intimadas do retorno dos autos da Superior Instância, para requererem o que de direito em 15 (quinze) dias."])))
    else:
        B.append(("title", ch(["CERTIDÃO DE REMESSA", "CERTIDÃO"])))
        B.append(("p", f"Certifico que, nesta data, {ch(['remeti os autos ao Egrégio Tribunal, para processamento do recurso interposto', 'remeti os autos à Contadoria Judicial', 'remeti os autos ao Centro Judiciário de Solução de Conflitos (CEJUSC)', 'encaminhei o ofício expedido ao destinatário por meio eletrônico'])}. Dou fé."))
    B.append(("pn", local_data(c, d)))
    B.append(("sig", [servidor[0].upper() if rng.random() < .5 else servidor[0], cargo]))
    return dict(blocks=B, autor="servidor", data=d, sub=f"certidao_{tipo}")

# ================================================================= MANDADO
def mandado(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    tipo = rng.choices(["citacao", "intimacao", "penhora", "citacao_penhora_trab"], [5, 3, 2, 2 if trab else 0])[0]
    if trab and tipo == "citacao": tipo = "citacao_penhora_trab"
    d = bizday(c.dist, rng.randint(5, 700)); of = c.oficial
    mand = f"{rng.randint(100,999)}.{d.year}/{rng.randint(1000,99999):06d}-{rng.randint(0,9)}"
    titulo = {"citacao": ch(["MANDADO DE CITAÇÃO", "MANDADO DE CITAÇÃO E INTIMAÇÃO", "MANDADO DE CITAÇÃO - PROCEDIMENTO COMUM"]),
              "intimacao": ch(["MANDADO DE INTIMAÇÃO", "MANDADO DE INTIMAÇÃO PESSOAL"]),
              "penhora": ch(["MANDADO DE PENHORA E AVALIAÇÃO", "MANDADO DE PENHORA, AVALIAÇÃO E INTIMAÇÃO"]),
              "citacao_penhora_trab": "MANDADO DE CITAÇÃO, PENHORA E AVALIAÇÃO"}[tipo]
    B.append(capa_processo(c, x, [("Mandado nº", mand), ("Oficial de Justiça", of[0])]))
    B.append(("title", titulo))
    pess = f"Dr{'a' if c.juiz_g=='f' else ''}. {c.juiz}"
    B.append(("p", f"{'A' if c.juiz_g=='f' else 'O'} MM. {x['Juiz']} {'do Trabalho' if trab else 'de Direito'} da {c.vara}, {pess}, na forma da lei, MANDA a qualquer Oficial de Justiça deste Juízo a quem este for apresentado que, em cumprimento ao presente mandado, expedido nos autos da ação em epígrafe, proceda:"))
    if tipo == "citacao":
        B.append(("p", f"à CITAÇÃO de {c.reu.nome}, {c.reu.qualif().split(', ', 1)[1]}, para os termos da ação proposta, cuja cópia da petição inicial segue em anexo e fica fazendo parte integrante deste, e para, querendo, oferecer contestação no prazo de 15 (quinze) dias úteis" + (", contado da audiência de conciliação, à qual deverá comparecer, a realizar-se em " + dfmt(bizday(d, rng.randint(30, 60))) + ", às " + str(rng.randint(9, 16)) + "h00, por videoconferência" if rng.random() < .5 else "") + "."))
        B.append(("p", "ADVERTÊNCIA: Não sendo contestada a ação, presumir-se-ão verdadeiras as alegações de fato formuladas pela parte autora (art. 344 do CPC). O prazo para contestação será contado nos termos do art. 231 do CPC."))
    elif tipo == "intimacao":
        alvo = ch([x["AUTOR"], c.reu.nome])
        B.append(("p", f"à INTIMAÇÃO de {alvo}, no endereço {c.autor.end if alvo==x['AUTOR'] else c.reu.end}, para " + ch(["que dê andamento ao feito, no prazo de 5 (cinco) dias, sob pena de extinção (art. 485, § 1º, do CPC).", f"comparecer à audiência de instrução e julgamento designada para o dia {dfmt(bizday(d,rng.randint(20,60)))}, às {rng.randint(9,16)}h30, para prestar depoimento pessoal, sob pena de confissão (art. 385, § 1º, do CPC).", f"cumprir a decisão que deferiu a tutela de urgência, cuja cópia segue anexa, no prazo de 5 (cinco) dias, sob pena de multa diária."])))
    elif tipo == "penhora":
        val = money(round(c.valor_causa * rng.uniform(.3, .9), 2))
        B.append(("p", f"à PENHORA de bens de propriedade d{x['oR']} executad{x['oR']} {c.reu.nome}, tantos quantos bastem para a garantia da execução, cujo débito importa em {val}, atualizado até {dfmt(d - dt.timedelta(days=15))}, observada a ordem do art. 835 do CPC; à AVALIAÇÃO dos bens penhorados; e à INTIMAÇÃO d{x['oR']} executad{x['oR']} acerca da penhora, para, querendo, apresentar impugnação no prazo de 15 (quinze) dias."))
    else:
        val = money(round(c.valor_causa * rng.uniform(.3, .9), 2))
        B.append(("p", f"à CITAÇÃO da executada {c.reu.nome}, na pessoa de seu representante legal, para que, no prazo de 48 (quarenta e oito) horas, pague ou garanta a execução, no valor de {val}, sob pena de penhora (art. 880 da CLT); não havendo pagamento nem garantia, proceda à PENHORA de tantos bens quantos bastem para o pagamento da importância da condenação, acrescida de custas e juros de mora, e à respectiva AVALIAÇÃO (art. 883 da CLT)."))
    B.append(("p", ch(["CUMPRA-SE, na forma e sob as penas da lei.", "CUMPRA-SE.", "Cumpra-se, observadas as formalidades legais."])))
    if rng.random() < .6:
        B.append(("small", "OBSERVAÇÕES: O Oficial de Justiça poderá proceder às diligências fora do horário de expediente, nos termos do art. 212, § 2º, do CPC. Os documentos do processo podem ser consultados no site do Tribunal, mediante senha de acesso que acompanha este mandado. Este mandado foi impresso em papel reciclável."))
    if rng.random() < .5:
        B.append(("small", f"Guia de diligência nº {rng.randint(10**8, 10**9)} – valor recolhido: {money(ch([84.02, 103.47, 128.90, 156.33]))}."))
    serv = nome()[0]
    B.append(("pn", local_data(c, d)))
    B.append(("pn", f"Eu, {serv}, {ch(['Escrevente Técnico Judiciário', 'Técnico Judiciário', 'Servidor'])}, digitei. Eu, {nome()[0]}, {ch(['Escrivão Judicial', 'Diretor de Secretaria', 'Coordenador'])}, conferi."))
    B.append(("sig", juiz_sig(c, d)))
    return dict(blocks=B, autor="juiz", data=d, sub=f"mandado_{tipo}")

# ================================================================= OFÍCIO
def oficio(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    tipo = rng.choices(["inss", "serasa", "banco", "resposta", "transferencia"], [3 if c.assunto == "consignado" else 0, 3 if c.assunto == "negativacao" else 1, 3, 3, 2])[0]
    d = bizday(c.dist, rng.randint(10, 700))
    num = f"{rng.randint(1,2999)}/{d.year}"
    if tipo == "resposta":
        B.append(("letterhead_bank", c.reu.nome if c.reu.nome.startswith("BANCO") else "BANCO MERIDIONAL S.A."))
        B.append(("r", f"São Paulo, {dext(d)}."))
        B.append(("pn", f"Ref.: Ofício nº {num} – Processo nº {c.numero}"))
        B.append(("pn", f"Ao(À) Excelentíssimo(a) Senhor(a) Doutor(a) {c.juiz}\nMM. {x['Juiz']} {'do Trabalho' if trab else 'de Direito'} da {c.vara}"))
        B.append(("title", ch(["OFÍCIO-RESPOSTA", "RESPOSTA A OFÍCIO", None])))
        B.append(("pn", "Excelentíssimo(a) Senhor(a) Juiz(a),"))
        B.append(("p", f"Em atenção ao ofício em referência, recebido em {dfmt(d - dt.timedelta(days=rng.randint(5,20)))}, {c.reu.nome} vem, respeitosamente, informar a Vossa Excelência que " + ch([
            f"foram cumpridas as determinações judiciais, com a {'suspensão dos descontos referentes ao contrato nº '+c.contrato if c.assunto=='consignado' else 'exclusão das anotações restritivas vinculadas ao contrato nº '+c.contrato}, em {dfmt(d - dt.timedelta(days=2))}.",
            f"não foram localizadas contas ou aplicações financeiras em nome de {x['AUTOR']}, CPF {c.autor.cpf}, na data da pesquisa.",
            f"segue anexo o extrato da conta {rng.randint(10000,99999)}-{rng.randint(0,9)}, agência {rng.randint(100,3999)}, de titularidade de {x['AUTOR']}, referente ao período de {dfmt(c.data_fato - dt.timedelta(days=30))} a {dfmt(c.data_fato + dt.timedelta(days=30))}, conforme solicitado."])))
        B.append(("p", "Sendo o que nos cumpria para o momento, colocamo-nos à disposição para eventuais esclarecimentos, por meio do e-mail oficiosjudiciais@" + c.reu.nome.split()[1].lower().replace("ã","a").replace("í","i").replace("ç","c") + ".com.br."))
        B.append(("pn", "Atenciosamente,"))
        B.append(("sig", [c.reu.nome, "Departamento Jurídico – Atendimento a Ofícios Judiciais", nome()[0]]))
        return dict(blocks=B, autor="parte_r", data=d, sub="oficio_resposta", scan_bias=.3)
    B.append(capa_processo(c, x) if rng.random() < .6 else ("pn", proc_line(c)))
    B.append(("title", f"OFÍCIO nº {num}" if rng.random() < .7 else "OFÍCIO"))
    dest = {"inss": "Ao Senhor Gerente Executivo do Instituto Nacional do Seguro Social – INSS\nSetor de Atendimento a Demandas Judiciais",
            "serasa": "À SERASA EXPERIAN S.A.\nAo Departamento de Atendimento a Ofícios Judiciais\nAlameda dos Quinimuras, nº 187 – Planalto Paulista – São Paulo/SP",
            "banco": f"Ao {c.reu.nome}\nA/C Departamento Jurídico – Ofícios Judiciais\n{c.reu.end}",
            "transferencia": "Ao BANCO DO BRASIL S.A.\nAgência Setor Público – Depósitos Judiciais"}[tipo]
    B.append(("pn", dest))
    B.append(("pn", ch(["Senhor(a) Gerente,", "Prezado(a) Senhor(a),", "Senhor(a) Responsável,"])))
    txt = {"inss": f"Pelo presente, extraído dos autos da ação em epígrafe, solicito a Vossa Senhoria que providencie, no prazo de 10 (dez) dias, a SUSPENSÃO dos descontos relativos ao contrato de empréstimo consignado nº {c.contrato}, averbado em favor de {c.reu.nome}, no benefício nº {c.nb if hasattr(c,'nb') else '000.000.000-0'}, de titularidade de {x['AUTOR']}, CPF {c.autor.cpf}, conforme decisão cuja cópia segue anexa.",
           "serasa": f"Pelo presente, extraído dos autos da ação em epígrafe, determino a Vossa Senhoria que proceda, no prazo de 5 (cinco) dias, à EXCLUSÃO de anotação restritiva em nome de {x['AUTOR']}, CPF {c.autor.cpf}, incluída por {c.reu.nome}, referente ao contrato nº {c.contrato}, no valor de {x['debito']}, informando a este Juízo o cumprimento.",
           "banco": f"Pelo presente, extraído dos autos da ação em epígrafe, requisito a Vossa Senhoria que encaminhe a este Juízo, no prazo de 15 (quinze) dias, {ch(['cópia do contrato nº '+c.contrato+' e dos documentos apresentados na contratação', 'os registros de acesso (logs, IP, geolocalização e identificação do dispositivo) das transações realizadas em '+x['data_fato_n'], 'extrato da conta de titularidade de '+x['AUTOR']+' referente aos últimos 12 meses'])}, sob as penas da lei.",
           "transferencia": f"Pelo presente, extraído dos autos da ação em epígrafe, solicito a Vossa Senhoria que proceda à TRANSFERÊNCIA do saldo integral da conta judicial nº {rng.randint(10**12, 10**13)}, vinculada a este processo, para a conta corrente de titularidade de {c.adv_a.nome}, {c.adv_a.oab}, CPF {cpf()}, Banco {rng.randint(1,756):03d}, agência {rng.randint(100,9999)}, conta {rng.randint(10000,999999)}-{rng.randint(0,9)}, com os acréscimos legais, devendo comprovar a operação nos autos."}[tipo]
    B.append(("p", txt))
    B.append(("p", ch(["A resposta deverá ser encaminhada exclusivamente por meio eletrônico, ao e-mail institucional desta unidade, com referência ao número do processo.", "Solicito que a resposta mencione o número do processo em referência.", "Aproveito a oportunidade para renovar a Vossa Senhoria protestos de estima e consideração."])))
    B.append(("pn", local_data(c, d)))
    B.append(("pn", "Atenciosamente,"))
    if rng.random() < .5:
        B.append(("sig", juiz_sig(c, d)))
    else:
        s = nome(); B.append(("sig", [s[0], ch(["Escrivão Judicial", "Diretor de Secretaria", "Chefe de Seção"]) + " – por ordem do(a) MM. Juiz(a)"]))
    return dict(blocks=B, autor="juiz", data=d, sub=f"oficio_{tipo}")

# ================================================================= ATA / TERMO DE AUDIÊNCIA
def ata_audiencia(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    d = c.data_aud; h = f"{rng.randint(9,16)}h{ch(['00','15','30','45'])}"
    preposto = nome(); test = nome()
    virtual = rng.random() < .5
    acordo = rng.random() < .25
    if trab:
        tipo = "instrucao_trab" if not acordo else "acordo_trab"
        B.append(("kv", [("PROCESSO", c.numero), ("RECLAMANTE", x["AUTOR"]), ("RECLAMADO", c.reu.nome)]))
        B.append(("title", ch(["ATA DE AUDIÊNCIA", "ATA DE AUDIÊNCIA", "ATA DE AUDIÊNCIA DE INSTRUÇÃO"])))
        B.append(("p", f"Em {dfmt(d)}, na sala de sessões da {c.vara}, {'por meio de videoconferência (plataforma Zoom), ' if virtual else ''}sob a direção d{'a' if c.juiz_g=='f' else 'o'} Exm{'a' if c.juiz_g=='f' else 'o'}. {'Juíza' if c.juiz_g=='f' else 'Juiz'} do Trabalho {c.juiz.upper()}, realizou-se audiência relativa ao processo identificado em epígrafe."))
        B.append(("p", f"Às {h}, aberta a audiência, foram, de ordem d{'a' if c.juiz_g=='f' else 'o'} {'Juíza' if c.juiz_g=='f' else 'Juiz'} do Trabalho, apregoadas as partes."))
        B.append(("p", f"Presente {x['oA']} reclamante, acompanhad{x['oA']} de seu(sua) advogado(a), Dr(a). {c.adv_a.nome}, {c.adv_a.oab}."))
        B.append(("p", f"Presente o preposto da reclamada, Sr(a). {preposto[0]}, acompanhado(a) de seu(sua) advogado(a), Dr(a). {c.adv_r.nome}, {c.adv_r.oab}."))
        if acordo:
            val = round(c.valor_causa * rng.uniform(.18, .45), 2)
            B.append(("h2", "CONCILIAÇÃO"))
            B.append(("p", f"As partes conciliaram-se nos seguintes termos: a reclamada pagará ao reclamante a importância líquida de {money(val)} ({extenso(val)}), em {ch(['parcela única, até '+dfmt(bizday(d,10)), str(rng.randint(2,6))+' parcelas mensais e sucessivas, vencendo-se a primeira em '+dfmt(bizday(d,15))])}, mediante depósito na conta bancária de titularidade do reclamante indicada nos autos."))
            B.append(("p", "Em caso de inadimplemento, incidirá multa de 50% sobre o saldo devedor, com vencimento antecipado das parcelas vincendas. O reclamante dá plena e geral quitação pelo objeto do pedido e pelo extinto contrato de trabalho."))
            B.append(("p", f"As parcelas objeto do acordo possuem natureza indenizatória, a título de {ch(['indenização por danos morais', 'multa do art. 477 da CLT e FGTS + 40%', 'indenização por danos morais e reflexos de FGTS'])}, nos termos do art. 832, § 3º, da CLT. Custas pela reclamada, no importe de {money(val*.02)}, calculadas sobre o valor do acordo."))
            B.append(("p", "HOMOLOGO o acordo para que surta seus jurídicos e legais efeitos, extinguindo o processo com resolução do mérito (art. 487, III, \"b\", do CPC). Cumprido o acordo, arquivem-se."))
        else:
            B.append(("p", "Conciliação recusada." + ch(["", " Recebida a defesa escrita, com documentos, dela tendo vista a parte reclamante."])))
            if rng.random() < .5:
                B.append(("p", f"O reclamante manifesta-se sobre a defesa e documentos nos seguintes termos: impugna os controles de jornada, por não refletirem a jornada efetivamente cumprida; impugna as avaliações de desempenho, por serem documentos unilaterais. No mais, reitera a inicial."))
            B.append(("h2", "DEPOIMENTO PESSOAL D" + x["OA"] + " RECLAMANTE"))
            dep = ({"horas_extras": [f"trabalhava das {x['ji']} às {x['jf']}, de segunda a sexta-feira", "tinha 30 minutos de intervalo para refeição", "não possuía subordinados", "as propostas de crédito eram aprovadas pelo sistema ou pelo gerente geral", "não tinha procuração do banco", "o ponto era encerrado às 17h por orientação do gerente geral, mas continuava trabalhando", "havia ranking diário no grupo de mensagens da agência"],
                    "equiparacao": [f"trabalhava na mesma agência que o paradigma {c.paradigma}", "ambos atendiam clientes do segmento varejo alta renda", "tinham as mesmas metas", "substituíam-se nas férias", "respondiam ao mesmo gerente geral", "o paradigma ingressou na função cerca de um ano antes"]})[c.assunto]
            B.append(("p", "Que " + "; que ".join(rng.sample(dep, min(len(dep), rng.randint(4, 6)))) + ". Nada mais."))
            B.append(("h2", "DEPOIMENTO DO PREPOSTO DA RECLAMADA"))
            dep2 = (["o reclamante possuía alçada para concessão de limites até determinado valor", "não sabe informar se o reclamante possuía procuração", "o registro de ponto é livre", "as horas extras registradas são pagas", "o reclamante participava do comitê de crédito da agência", "não há ranking individual exposto publicamente"] if c.assunto == "horas_extras"
                    else ["o paradigma atendia carteira de clientes de segmento superior", "o paradigma tinha maior volume de negócios", "não sabe informar a data de ingresso do paradigma na função", "a PLR foi paga conforme a convenção coletiva"])
            B.append(("p", "Que " + "; que ".join(rng.sample(dep2, min(len(dep2), rng.randint(3, 5)))) + ". Nada mais."))
            B.append(("h2", "PRIMEIRA TESTEMUNHA D" + x["OA"] + " RECLAMANTE"))
            B.append(("p", f"{test[0].upper()}, identidade nº {rg()}, {ch(['bancário', 'ex-empregado da reclamada', 'gerente de relacionamento'])}, residente em {c.cidade}/{c.uf}. Advertida e compromissada. Depoimento: que trabalhou com {x['oA']} reclamante na agência {x['agencia']} de {dfmt(c.admissao + dt.timedelta(days=rng.randint(300,1500)))} a {dfmt(c.dispensa - dt.timedelta(days=rng.randint(30,300)))}; que " + "; que ".join(rng.sample(dep, 3)) + ". Nada mais."))
            B.append(("p", "Sem outras provas, encerra-se a instrução processual." + ch([" Razões finais remissivas pelas partes.", " Razões finais orais pelas partes, em 10 minutos cada, remissivas."]) + " Rejeitada a última proposta conciliatória."))
            B.append(("p", f"Julgamento designado para {dfmt(bizday(d, rng.randint(20,60)))}, às 17h00, do que ficam as partes cientes, nos termos da Súmula 197 do TST."))
        B.append(("p", f"Audiência encerrada às {rng.randint(int(h.split('h')[0]), int(h.split('h')[0])+1)}h{rng.randint(0,59):02d}. Nada mais."))
        B.append(("sig", [c.juiz.upper(), ("Juíza" if c.juiz_g == "f" else "Juiz") + " do Trabalho"]))
        if not virtual and rng.random() < .5:
            B.append(("sigs", [["Reclamante", ""], ["Adv. Reclamante", ""], ["Preposto", ""], ["Adv. Reclamada", ""]]))
        return dict(blocks=B, autor="juiz", data=d, sub="ata_" + tipo, scan_bias=.25)
    # cível / JEC
    jec = c.justica == "jec"
    tipo = ch(["conciliacao", "conciliacao", "instrucao"]) if jec else ch(["conciliacao_cejusc", "instrucao"])
    B.append(capa_processo(c, x))
    B.append(("title", {"conciliacao": ch(["TERMO DE AUDIÊNCIA DE CONCILIAÇÃO", "TERMO DE AUDIÊNCIA", "ATA DE AUDIÊNCIA DE CONCILIAÇÃO"]),
                        "conciliacao_cejusc": ch(["TERMO DE SESSÃO DE CONCILIAÇÃO – CEJUSC", "TERMO DE AUDIÊNCIA DE CONCILIAÇÃO/MEDIAÇÃO"]),
                        "instrucao": ch(["TERMO DE AUDIÊNCIA DE INSTRUÇÃO E JULGAMENTO", "ATA DE AUDIÊNCIA DE INSTRUÇÃO"])}[tipo]))
    cond = nome()
    pres = (f"{'a' if c.juiz_g=='f' else 'o'} MM. {x['Juiz']} de Direito, Dr{'a' if c.juiz_g=='f' else ''}. {c.juiz}" if tipo == "instrucao" else f"{'a' if cond[1]=='f' else 'o'} Concilia{'dora' if cond[1]=='f' else 'dor'} {cond[0]}")
    B.append(("p", f"Aos {extenso(d.day).replace(' reais','').replace(' real','')} dias do mês de {['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][d.month-1]} do ano de {d.year}, às {h}, {'por videoconferência, via plataforma Microsoft Teams' if virtual else 'na sala de audiências deste Juízo'}, sob a presidência d{pres}, foi aberta a audiência nos autos da ação em epígrafe."))
    B.append(("p", f"Apregoadas as partes, compareceram: {x['oA']} {x['A']}, {x['AUTOR']}, acompanhad{x['oA']} de seu advogado, Dr(a). {c.adv_a.nome}, {c.adv_a.oab}; {x['oR']} {x['R']}, {c.reu.nome}, representad{x['oR']} pelo(a) preposto(a) {preposto[0]}, conforme carta de preposição, acompanhado(a) do(a) advogado(a) Dr(a). {c.adv_r.nome}, {c.adv_r.oab}." if rng.random() < .85 else
              f"Apregoadas as partes, compareceu {x['oA']} {x['A']}, acompanhad{x['oA']} de seu advogado. Ausente {x['oR']} {x['R']}, embora regularmente citad{x['oR']} e intimad{x['oR']}, conforme AR de fls. {rng.randint(40,120)}."))
    if acordo:
        val = round(c.valor_causa * rng.uniform(.2, .55), 2)
        B.append(("p", f"Iniciados os trabalhos, as partes celebraram ACORDO nos seguintes termos: 1) {x['oR']} {x['R']} pagará {x['aoA']} {x['A']} a quantia de {money(val)} ({extenso(val)}), em parcela única, até {dfmt(bizday(d,15))}, mediante depósito judicial ou transferência para a conta indicada pelo patrono; 2) {ch(['o réu promoverá a baixa definitiva da anotação restritiva e o cancelamento do contrato nº '+c.contrato+', no prazo de 10 dias', 'cada parte arcará com os honorários de seus patronos', 'em caso de descumprimento, incidirá multa de 20% sobre o valor devido'])}; 3) com o cumprimento, {x['oA']} {x['A']} dá plena quitação do objeto da ação."))
        B.append(("p", ("Pel" + ("a" if c.juiz_g == "f" else "o") + f" MM. {x['Juiz']} foi proferida a seguinte decisão: \"HOMOLOGO o acordo celebrado entre as partes para que produza seus efeitos jurídicos e legais e JULGO EXTINTO o processo, com resolução do mérito, nos termos do art. 487, III, 'b', do CPC. Partes renunciam ao prazo recursal. Arquivem-se oportunamente.\"" if tipo == "instrucao" or rng.random() < .5 else
                        "O acordo será submetido à homologação do(a) MM. Juiz(a) de Direito. Saem os presentes intimados.")))
        sub = "termo_audiencia_com_acordo"
    elif tipo == "instrucao":
        B.append(("p", "Proposta a conciliação, restou infrutífera."))
        B.append(("p", f"Em seguida, passou-se à colheita da prova oral. Foi tomado o depoimento pessoal d{x['oA']} {x['A']}, " + ch(["registrado em sistema de gravação audiovisual, cujo arquivo encontra-se disponível nos autos digitais", "que, às perguntas formuladas, respondeu: que não reconhece a contratação; que nunca esteve na agência indicada pelo réu; que tomou conhecimento da restrição ao tentar realizar compra a prazo"]) + "."))
        if rng.random() < .6:
            B.append(("p", f"Ouvida a testemunha arrolada pel{x['oA']} {x['A']}, {test[0]}, RG {rg()}, compromissada na forma da lei, conforme gravação audiovisual."))
        B.append(("p", "Encerrada a instrução. " + ch(["As partes apresentaram alegações finais remissivas.", "Concedido o prazo de 15 dias para apresentação de memoriais escritos, sucessivamente, iniciando-se pelo autor.", "Alegações finais orais, conforme gravação."])))
        B.append(("p", ch(["Pel" + ("a" if c.juiz_g == "f" else "o") + " MM. " + x["Juiz"] + " foi dito: \"Venham os autos conclusos para sentença.\"", "Pel" + ("a" if c.juiz_g == "f" else "o") + " MM. " + x["Juiz"] + " foi proferida sentença em audiência, que segue em termo apartado.", "Saem os presentes intimados."])))
        sub = "termo_audiencia_instrucao"
    else:
        B.append(("p", "Proposta a conciliação, a mesma restou infrutífera, " + ch([f"tendo {x['oR']} {x['R']} informado não possuir proposta de acordo para o caso.", f"pois as partes não chegaram a um consenso quanto ao valor. Proposta do réu: {money(round(c.valor_causa*.12,-1))}; contraproposta do autor: {money(round(c.valor_causa*.5,-1))}.", "uma vez que as partes não chegaram a um acordo."])))
        if jec:
            B.append(("p", ch([f"Pel{x['oR']} {x['R']} foi apresentada contestação escrita, com documentos, da qual teve vista {x['oA']} {x['A']}, que se manifestará no prazo de 10 dias.", "As partes declararam não ter outras provas a produzir, requerendo o julgamento antecipado. Venham conclusos para sentença.", f"Designa-se audiência de instrução e julgamento para o dia {dfmt(bizday(d,rng.randint(30,90)))}, às {rng.randint(9,16)}h00, saindo os presentes intimados."])))
        else:
            B.append(("p", f"Fica {x['oR']} {x['R']} ciente de que o prazo para contestação, de 15 (quinze) dias úteis, inicia-se a partir desta data, nos termos do art. 335, I, do CPC. Devolvam-se os autos à Vara de origem."))
        sub = "termo_audiencia_conciliacao"
    B.append(("p", "Nada mais havendo, foi encerrado o presente termo, que, lido e achado conforme, vai devidamente assinado." if not virtual else "Nada mais havendo, encerrou-se a audiência, dispensadas as assinaturas das partes em razão da realização por videoconferência (Resolução CNJ nº 354/2020)."))
    B.append(("sig", [c.juiz.upper() if tipo == "instrucao" else cond[0].upper(), (x["Juiz"] + " de Direito") if tipo == "instrucao" else ("Conciliadora" if cond[1] == "f" else "Conciliador")]))
    if not virtual:
        B.append(("sigs", [[x["A"], ""], [f"Adv. {x['A']}", ""], ["Preposto(a)", ""], [f"Adv. {x['R']}", ""]]))
    return dict(blocks=B, autor="juiz", data=d, sub=sub, scan_bias=.35 if not virtual else .1)

# ================================================================= TERMO DE ACORDO
def termo_acordo(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    d = bizday(c.dist, rng.randint(60, 600)); val = round(c.valor_causa * rng.uniform(.2, .6), 2)
    estilo = rng.choice(["peticao", "termo", "instrumento"])
    if estilo == "peticao":
        B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 8))
        B.append(("p", f"{x['AUTOR']} e {c.reu.nome}, já qualificados nos autos da ação em epígrafe, vêm, respeitosamente, por seus advogados infra-assinados, informar que se compuseram amigavelmente, requerendo a homologação do presente"))
        B.append(("title", ch(["ACORDO", "TERMO DE ACORDO", "PETIÇÃO DE ACORDO", "ACORDO JUDICIAL"])))
        B.append(("p", "nos termos das cláusulas e condições a seguir:"))
    elif estilo == "termo":
        B.append(("title", ch(["TERMO DE ACORDO", "TERMO DE TRANSAÇÃO", "TERMO DE ACORDO JUDICIAL"])))
        B.append(("kv", [("Processo nº", c.numero), ("Juízo", c.vara)]))
        B.append(("p", f"Pelo presente instrumento, de um lado, {x['AUTOR']}, doravante denominad{x['oA']} {'RECLAMANTE' if trab else 'AUTOR' + ('A' if x['oA']=='a' else '')}, e, de outro lado, {c.reu.nome}, doravante denominad{x['oR']} {'RECLAMADA' if trab else 'RÉ' if x['oR']=='a' else 'RÉU'}, ambos por seus advogados, têm entre si justo e acordado o seguinte:"))
    else:
        B.append(("title", "INSTRUMENTO PARTICULAR DE TRANSAÇÃO"))
        B.append(("p", f"PARTES: {c.autor.qualif()}; e {c.reu.qualif()}."))
        B.append(("p", f"OBJETO: composição amigável da lide objeto do processo nº {c.numero}, em trâmite perante a {c.vara}."))
    cl = ["PRIMEIRA", "SEGUNDA", "TERCEIRA", "QUARTA", "QUINTA", "SEXTA", "SÉTIMA"]
    cls = [f"{x['oR'].upper()} {('RECLAMADA' if trab else x['R'].upper())} pagará {x['aoA']} {('RECLAMANTE' if trab else x['A'].upper())} a importância de {money(val)} ({extenso(val)}), " + ch([f"em parcela única, até o dia {dfmt(bizday(d,15))}", f"em {rng.randint(2,5)} parcelas mensais e sucessivas, vencendo-se a primeira em {dfmt(bizday(d,15))}", f"no prazo de 15 (quinze) dias úteis contados da homologação"]) + ", mediante " + ch(["depósito judicial vinculado aos presentes autos", f"transferência para a conta bancária de titularidade do patrono {c.adv_a.nome}, Banco {rng.randint(1,756):03d}, agência {rng.randint(100,9999)}, conta {rng.randint(10000,999999)}-{rng.randint(0,9)}, que possui poderes para receber e dar quitação"]) + ".",
           f"O inadimplemento, total ou parcial, acarretará a incidência de multa de {ch(['10%', '20%', '50%'])} sobre o saldo devedor, além do vencimento antecipado das parcelas vincendas, prosseguindo-se a execução pelo valor total.",
           ]
    if not trab:
        cls.append(ch([f"{x['oR'].upper()} {x['R'].upper()} compromete-se a promover o cancelamento do contrato nº {c.contrato} e a baixa de eventuais restrições em nome d{x['oA']} {x['A']}, relativas ao objeto da ação, no prazo de 10 (dez) dias.",
                       f"{x['oR'].upper()} {x['R'].upper()} cessará definitivamente os descontos objeto da ação, a partir da próxima competência."]))
    else:
        cls.append(f"As parcelas objeto do presente acordo possuem natureza exclusivamente indenizatória, referindo-se a {ch(['indenização por danos morais', 'FGTS + 40% e multa do art. 477 da CLT', 'indenização substitutiva do intervalo intrajornada (art. 71, § 4º, da CLT)'])}, não havendo incidência de contribuição previdenciária, nos termos do art. 832, § 3º, da CLT.")
    cls.append(f"Com o cumprimento integral do acordo, {x['oA']} {('RECLAMANTE' if trab else x['A'].upper())} dará plena, geral e irrevogável quitação quanto ao objeto da ação{' e ao extinto contrato de trabalho' if trab and rng.random()<.6 else ''}, para nada mais reclamar, seja a que título for.")
    cls.append(ch(["Cada parte arcará com os honorários de seus respectivos advogados. As custas processuais remanescentes, se houver, serão suportadas pela parte ré.", "As custas processuais serão rateadas entre as partes, observada a gratuidade concedida, e cada parte arcará com os honorários de seus patronos.", f"Custas pela {'reclamada' if trab else 'parte ré'}, calculadas sobre o valor do acordo."]))
    for i, t in enumerate(cls): B.append(("p", f"CLÁUSULA {cl[i]} – {t}"))
    B.append(("p", f"Diante do exposto, as partes requerem a homologação do presente acordo, com a consequente extinção do processo, com resolução do mérito, nos termos do art. 487, III, \"b\", do Código de Processo Civil{', e art. 831, parágrafo único, da CLT' if trab else ''}, renunciando expressamente ao prazo recursal."))
    if estilo == "peticao": B.append(("pn", pedir_def()))
    B.append(("pn", local_data(c, d)))
    B.append(("sigs", [[c.adv_a.nome.upper(), c.adv_a.oab, f"Advogad{'a' if c.adv_a.g=='f' else 'o'} d{x['oA']} {'Reclamante' if trab else x['A']}"], [c.adv_r.nome.upper(), c.adv_r.oab, f"Advogad{'a' if c.adv_r.g=='f' else 'o'} d{'a Reclamada' if trab else x['oR']+' '+x['R']}"]]))
    if estilo != "peticao" and rng.random() < .5:
        B.append(("sigs", [[x["AUTOR"], "Parte"], [c.reu.nome, "Parte"]]))
    return dict(blocks=B, autor="adv_a", data=d, sub=f"termo_acordo_{estilo}", scan_bias=.2)

# ================================================================= LAUDO PERICIAL
def laudo_pericial(c):
    x = ctx(c); a = A[c.assunto]; B = []; trab = c.justica == "trab"
    per = c.perito; tit = "Perita" if per[1] == "f" else "Perito"
    d = bizday(c.data_contest, rng.randint(90, 250))
    tipo = a["pericia"]
    if tipo == "grafotécnica": tipo = "grafo"
    B.append(("addr", enderecamento(c))); B.append(("sp", 6)); B.append(("pn", proc_line(c))); B.append(("sp", 6))
    cred = {"grafo": ch(["Perito Grafotécnico e Documentoscópico", "Perita Grafotécnica – Especialista em Documentoscopia"]), "contabil": "Contador(a) – CRC/" + c.uf + " nº " + f"1{c.uf}{rng.randint(100000,399999)}/O-{rng.randint(1,9)}", "contabil_trab": "Contador(a) – CRC/" + c.uf + " nº " + f"1{c.uf}{rng.randint(100000,399999)}/O-{rng.randint(1,9)}"}[tipo]
    B.append(("p", f"{per[0].upper()}, {cred.replace('Perito', tit) if tipo=='grafo' else cred}, {tit.lower()} nomead{'a' if per[1]=='f' else 'o'} nos autos da ação em epígrafe, movida por {x['AUTOR']} em face de {c.reu.nome}, tendo concluído os trabalhos que lhe foram confiados, vem, respeitosamente, apresentar o"))
    titulo = {"grafo": "LAUDO PERICIAL GRAFOTÉCNICO", "contabil": "LAUDO PERICIAL CONTÁBIL", "contabil_trab": "LAUDO PERICIAL CONTÁBIL"}[tipo]
    B.append(("title", titulo)); B.append(("pb",))
    sec = 1
    def H(t):
        nonlocal sec; B.append(("h", f"{sec}. {t}")); sec += 1
    H("CONSIDERAÇÕES PRELIMINARES")
    B.append(("p", f"Por r. decisão de fls. {rng.randint(150,300)}, {'a' if per[1]=='f' else 'o'} signatári{'a' if per[1]=='f' else 'o'} foi nomead{'a' if per[1]=='f' else 'o'} para a realização de perícia {'grafotécnica' if tipo=='grafo' else 'contábil'}, tendo aceitado o encargo e apresentado proposta de honorários, devidamente depositados. As partes foram intimadas do início dos trabalhos, nos termos do art. 474 do CPC, que se deu em {dfmt(d - dt.timedelta(days=rng.randint(30,60)))}."))
    if rng.random() < .6:
        B.append(("p", f"{'Indicou assistente técnico apenas a parte ré' if rng.random()<.5 else 'Não foram indicados assistentes técnicos pelas partes'}, {'sendo-lhe franqueado o acompanhamento das diligências' if rng.random()<.5 else 'não havendo divergências a registrar'}."))
    H("OBJETIVO DA PERÍCIA")
    if tipo == "grafo":
        B.append(("p", f"O presente exame tem por objetivo verificar a autenticidade ou falsidade da(s) assinatura(s) atribuída(s) a {x['AUTOR']}, lançada(s) no {'Contrato de Empréstimo Consignado' if c.assunto=='consignado' else 'Instrumento Particular de Contratação de Cartão de Crédito'} nº {c.contrato}, datado de {x['data_contr']}, juntado pel{x['oR']} {x['R']} às fls. {rng.randint(90,180)}."))
        H("PEÇAS DE EXAME")
        B.append(("h2", "Peça questionada"))
        B.append(("p", f"Via original do contrato nº {c.contrato}, composto por {rng.randint(3,9)} folhas, apresentado em cartório pel{x['oR']} {x['R']} em {dfmt(d - dt.timedelta(days=rng.randint(40,90)))}, contendo {rng.randint(2,5)} lançamentos de assinatura no campo \"Cliente/Emitente\"." if rng.random() < .7 else f"Cópia digitalizada do contrato nº {c.contrato}, de fls. {rng.randint(90,180)}, uma vez que a parte ré informou não dispor da via original. Registra-se que o exame de cópias apresenta limitações quanto à análise de elementos de ordem dinâmica, como pressão e sulcos."))
        B.append(("h2", "Padrões de confronto"))
        B.append(("p", f"(i) Padrões colhidos em cartório, em {dfmt(d - dt.timedelta(days=rng.randint(30,60)))}, na presença {'da' if per[1]=='f' else 'do'} {tit.lower()}, consistentes em {rng.randint(15,30)} assinaturas lançadas em folhas avulsas, em diferentes posições e velocidades; (ii) padrões não produzidos para fins periciais (padrões de época): cédula de identidade, procuração ad judicia, declaração de hipossuficiência e ficha de cadastro bancário anterior à data do contrato."))
        H("METODOLOGIA")
        B.append(("p", "Os exames foram realizados com o emprego do método grafoscópico, com abordagem grafocinética, consistente no confronto entre os lançamentos questionados e os padrões, sob análise dos elementos de ordem geral (calibre, espaçamento, alinhamento gráfico, comportamento de base, inclinação axial e dimensionamento) e dos elementos de ordem genética (pressão, progressão, ataques, remates, mínimos gráficos e momentos gráficos)."))
        B.append(("p", "Foram utilizados os seguintes equipamentos: lupa estereoscópica com aumento de até 40x, luz rasante, luz ultravioleta (UV 365 nm), scanner de alta resolução (1.200 dpi) e software de tratamento de imagens para ampliação e sobreposição."))
        H("EXAMES")
        falso = c.resultado != "improc"
        rows = [["Elemento", "Peça questionada", "Padrões", "Resultado"]]
        els = [("Calibre", "médio", "pequeno a médio"), ("Inclinação axial", "dextrogira acentuada", "vertical a levemente dextrogira"), ("Pressão", "uniforme, sem variação", "variável, com ênfase nos traços descendentes"),
               ("Velocidade/andamento", "lento, com hesitações", "rápido e espontâneo"), ("Ataques", "rombudos, com retoques", "afilados"), ("Remates", "abruptos", "em gancho, voltados à esquerda"),
               ("Espaçamento interletras", "regular, artificial", "irregular, natural"), ("Morfologia do \"" + c.autor.nome[0] + "\" inicial", "laçada simples", "laçada dupla com prolongamento")]
        for e, q, p in els:
            if falso: rows.append([e, q, p, "Divergente"])
            else: rows.append([e, p, p, "Convergente"])
        B.append(("table", rows, [110, 120, 120, 70]))
        if falso:
            B.append(("p", "Verificou-se, nas assinaturas questionadas, a presença de tremores de imitação, paradas bruscas da caneta e retoques, características típicas de lançamentos produzidos de forma lenta e desenhada, com o propósito de reproduzir a morfologia de uma assinatura autêntica, sem, contudo, alcançar seus elementos de gênese gráfica."))
            B.append(("p", "As divergências encontradas são de natureza qualitativa e se manifestam de forma constante em todos os lançamentos questionados, não podendo ser atribuídas à variação natural da escrita, a fatores ocasionais (posição, suporte, instrumento escritor) ou à idade do punho escritor."))
        else:
            B.append(("p", "Os lançamentos questionados apresentam fluência, espontaneidade e dinamismo compatíveis com os padrões, com convergência dos elementos de ordem geral e, sobretudo, dos elementos genéticos, inclusive de idiotismos gráficos de difícil percepção e reprodução por terceiros."))
            B.append(("p", "As pequenas diferenças observadas situam-se dentro da faixa de variação natural da escrita do punho fornecedor dos padrões, não indicando qualquer tentativa de imitação ou disfarce."))
        H("CONCLUSÃO")
        B.append(("box", ("Com base nos exames realizados, conclui-se que as assinaturas questionadas, atribuídas a " + x["AUTOR"] + ", lançadas no contrato nº " + c.contrato + ", NÃO PROVIERAM do punho escritor do(a) autor(a), sendo, portanto, FALSAS.") if falso else
                          ("Com base nos exames realizados, conclui-se que as assinaturas questionadas, atribuídas a " + x["AUTOR"] + ", lançadas no contrato nº " + c.contrato + ", PROVIERAM do punho escritor do(a) autor(a), sendo, portanto, AUTÊNTICAS.")))
        quesitos = [("Do Juízo", ["A assinatura lançada no contrato é autêntica?", "Há indícios de montagem ou adulteração do documento?"]),
                    (f"D{x['oA']} {x['A']}", ["Os padrões colhidos são suficientes para o exame?", "Foram constatados sinais de imitação servil ou livre?", "O documento questionado é original ou cópia?"]),
                    (f"D{x['oR']} {x['R']}", ["É possível que as divergências decorram da idade ou do estado de saúde do punho escritor?", "A assinatura questionada é compatível com a constante do documento de identidade apresentado na contratação?"])]
        resp = {True: ["Não. Vide conclusão.", "Não foram constatados sinais de montagem; a falsidade é restrita aos lançamentos de assinatura.", "Sim, os padrões são suficientes e adequados, em quantidade e qualidade.", "Sim. Foram constatados sinais de imitação lenta (servil), conforme item 5.", "Original, conforme item 3.", "Não. As divergências são qualitativas e constantes, incompatíveis com a variação natural.", "A assinatura questionada apresenta semelhança morfológica superficial, mas diverge nos elementos genéticos."],
                False: ["Sim. Vide conclusão.", "Não.", "Sim.", "Não.", "Original, conforme item 3.", "Prejudicado, diante da conclusão pela autenticidade.", "Sim, há plena compatibilidade."]}[falso]
        H("RESPOSTAS AOS QUESITOS")
        k = 0
        for quem, qs in quesitos:
            B.append(("h2", f"Quesitos {quem}"))
            for i, q in enumerate(qs):
                B.append(("pn", f"{i+1}) {q}")); B.append(("pn", f"Resposta: {resp[k] if k < len(resp) else 'Vide item 5.'}")); k += 1
    else:
        if tipo == "contabil":
            B.append(("p", f"Apurar a taxa de juros remuneratórios efetivamente praticada na Cédula de Crédito Bancário nº {c.contrato}, compará-la com a taxa média de mercado divulgada pelo Banco Central do Brasil para a modalidade \"aquisição de veículos – pessoa física\" no mês da contratação, verificar a forma de capitalização e recalcular as prestações, com a apuração de eventuais diferenças pagas a maior."))
            H("DOCUMENTOS ANALISADOS")
            B.append(("p", f"Cédula de Crédito Bancário nº {c.contrato} (fls. {rng.randint(30,60)}); demonstrativo de evolução do débito (fls. {rng.randint(120,180)}); comprovantes de pagamento das parcelas; série histórica de taxas médias de juros – SGS/BACEN, código 20749; tabela de taxas por instituição financeira."))
            H("DADOS DO CONTRATO")
            B.append(("table", [["Item", "Valor"], ["Valor financiado", x["financiado"]], ["Prazo", f"{x['n_parc']} meses"], ["Taxa mensal contratada", f"{x['taxa']}% a.m."], ["Taxa anual contratada", f"{x['taxa_a']}% a.a."], ["Valor da parcela", x["parcela"]], ["Tarifa de cadastro / avaliação", x["tac"]], ["Seguro prestamista", x["seguro"]], ["Taxa média BACEN no mês", f"{x['media']}% a.m."]], [200, 200]))
            H("ANÁLISE TÉCNICA")
            B.append(("p", f"A taxa contratada ({x['taxa']}% a.m.) corresponde a {c.taxa/c.media:.2f}".replace(".", ",") + f" vezes a taxa média de mercado apurada para a modalidade no mês da contratação ({x['media']}% a.m.). A taxa anual é superior ao duodécuplo da mensal, o que evidencia a pactuação de capitalização mensal, adotada a Tabela Price como sistema de amortização."))
            B.append(("p", "Procedeu-se ao recálculo do contrato substituindo-se a taxa contratada pela taxa média de mercado, mantidos o valor financiado, o prazo e o sistema de amortização, com exclusão do seguro prestamista, conforme parâmetros fixados na decisão saneadora."))
            i1 = c.taxa / 100; i2 = c.media / 100; pv = c.financiado; n = c.n_parc
            p1 = pv * i1 / (1 - (1 + i1) ** -n); p2 = pv * i2 / (1 - (1 + i2) ** -n)
            rows = [["Parc.", "Venc.", "Parcela contratada", "Parcela recalculada", "Diferença"]]
            v0 = c.data_fato
            for k in range(1, min(n, rng.randint(12, 18)) + 1):
                vd = (v0 + dt.timedelta(days=30 * k))
                rows.append([str(k), dfmt(vd), money(p1), money(p2), money(p1 - p2)])
            rows.append(["", "", "", "Subtotal", money((p1 - p2) * (len(rows) - 1))])
            B.append(("h2", "Demonstrativo de recálculo (parcelas pagas)")); B.append(("table", rows, [40, 75, 105, 105, 95]))
            H("CONCLUSÃO")
            B.append(("box", f"Considerando a substituição da taxa contratada pela taxa média de mercado, apurou-se diferença de {money(p1-p2)} por parcela, totalizando, até a data-base do laudo, {money((p1-p2)*(len(rows)-2))} em valores históricos, ou {money((p1-p2)*(len(rows)-2)*1.11)} em valores atualizados pelo índice oficial adotado pelo {c.sigla} e acrescidos de juros de mora, além de {x['seguro']} referentes ao seguro prestamista."))
        else:
            B.append(("p", f"Apurar os valores devidos a {x['AUTOR']} em razão da condenação, nos termos do título executivo judicial, compreendendo {'horas extras excedentes da sexta diária e reflexos e intervalo intrajornada' if c.assunto=='horas_extras' else 'diferenças salariais por equiparação e reflexos e diferenças de PLR'}, com a incidência de correção monetária, juros, contribuições previdenciárias e imposto de renda."))
            H("CRITÉRIOS ADOTADOS")
            B.append(("p", "Período: " + f"{dfmt(c.dist.replace(year=c.dist.year-5))} a {x['dispensa']}" + f". Base de cálculo: evolução salarial conforme fichas financeiras. Divisor: 180. Adicional: 50%. Correção monetária: IPCA-E na fase pré-judicial e SELIC a partir do ajuizamento (ADCs 58 e 59 do STF), observada a Lei nº 14.905/2024. Contribuições previdenciárias: Súmula 368 do TST. IRPF: art. 12-A da Lei nº 7.713/88 (RRA)."))
            H("RESUMO DO CÁLCULO")
            base = c.valor_causa * rng.uniform(.25, .5)
            verbas = (["Horas extras (7ª e 8ª)", "Reflexos em DSR", "Reflexos em férias + 1/3", "Reflexos em 13º salário", "Reflexos em aviso prévio", "Intervalo intrajornada", "FGTS + 40%"] if c.assunto == "horas_extras"
                      else ["Diferenças salariais", "Reflexos em férias + 1/3", "Reflexos em 13º salário", "Reflexos em gratificação semestral", "Diferenças de PLR", "FGTS + 40%"])
            ws = [rng.uniform(.5, 1.5) for _ in verbas]; ws[0] *= 6; s = sum(ws)
            rows = [["Verba", "Valor corrigido", "Juros", "Total"]]; tot = 0
            for v, w in zip(verbas, ws):
                vc = base * w / s; j = vc * rng.uniform(.18, .32); tot += vc + j
                rows.append([v, money(vc), money(j), money(vc + j)])
            rows.append(["TOTAL BRUTO DEVIDO AO RECLAMANTE", "", "", money(tot)])
            B.append(("table", rows, [180, 85, 75, 85]))
            B.append(("table", [["Descontos / Encargos", "Valor"], ["INSS – cota do reclamante", money(tot*.08)], ["IRPF", money(tot*.06)], ["INSS – cota da reclamada", money(tot*.2)], ["Honorários advocatícios (10%)", money(tot*.1)], ["Custas processuais", money(tot*.02)]], [250, 150]))
            H("CONCLUSÃO")
            B.append(("box", f"O valor líquido devido ao reclamante, atualizado até {dfmt(d)}, é de {money(tot*.86)}, perfazendo o total da execução, incluídos encargos, honorários e custas, {money(tot*1.32)}."))
        H("QUESITOS")
        B.append(("p", "Os quesitos formulados pelas partes foram integralmente respondidos no corpo do laudo, conforme correspondência a seguir:"))
        for i in range(rng.randint(3, 6)):
            B.append(("pn", f"Quesito {i+1}: {ch(['Vide item 4.', 'Vide item 5 e demonstrativo anexo.', 'Sim, conforme item 5.', 'Não. Vide item 6.', 'Prejudicado.', 'Vide conclusão.'])}"))
    H("ENCERRAMENTO")
    B.append(("p", f"Nada mais havendo a esclarecer, {'a' if per[1]=='f' else 'o'} {tit.lower()} dá por encerrado o presente laudo, composto por {rng.randint(9,24)} folhas, {'incluindo anexos fotográficos' if tipo=='grafo' else 'incluindo planilhas de cálculo'}, colocando-se à disposição deste Juízo para quaisquer esclarecimentos. Requer, ainda, o levantamento dos honorários periciais depositados."))
    B.append(("pn", local_data(c, d)))
    B.append(("sig", [per[0].upper(), cred.replace("Perito", tit) if tipo == "grafo" else cred]))
    return dict(blocks=B, autor="perito", data=d, sub=f"laudo_{'grafotecnico' if tipo=='grafo' else 'contabil'}")

# ================================================================= CÁLCULOS DE LIQUIDAÇÃO
def calculos_liquidacao(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    d = bizday(c.data_sent, rng.randint(90, 400))
    estilo = rng.choice(["planilha", "planilha", "memoria"])
    if trab:
        B.append(("title", ch(["PLANILHA DE CÁLCULOS", "CÁLCULOS DE LIQUIDAÇÃO", "RESUMO DE CÁLCULO – PJe-Calc"])))
        B.append(("kv", [("Processo", c.numero), ("Reclamante", x["AUTOR"]), ("Reclamado", c.reu.nome), ("Data de ajuizamento", dfmt(c.dist)), ("Data da liquidação", dfmt(d)), ("Período", f"{dfmt(max(c.admissao, c.dist.replace(year=c.dist.year-5)))} a {x['dispensa']}")]))
        B.append(("h2", "Critério de cálculo e fundamentação legal"))
        B.append(("small", "Correção monetária: IPCA-E até a véspera do ajuizamento; SELIC a partir do ajuizamento até 29/08/2024 e IPCA + juros (taxa legal, Lei nº 14.905/2024) a partir de 30/08/2024, nos termos da decisão do TST-E-ED-RR-713-03.2010.5.04.0029. Contribuição social: Lei nº 8.212/91. Imposto de renda: art. 12-A da Lei nº 7.713/88, IN RFB nº 1.500/2014. Juros de mora na fase pré-judicial: art. 39 da Lei nº 8.177/91."))
        base = c.valor_causa * rng.uniform(.25, .5)
        verbas = (["HORAS EXTRAS 50%", "REFLEXO EM DSR (HORAS EXTRAS)", "REFLEXO EM FÉRIAS + 1/3", "REFLEXO EM 13º SALÁRIO", "REFLEXO EM AVISO PRÉVIO", "INTERVALO INTRAJORNADA", "FGTS 8%", "MULTA 40% FGTS"] if c.assunto == "horas_extras"
                  else ["DIFERENÇA SALARIAL – EQUIPARAÇÃO", "REFLEXO EM FÉRIAS + 1/3", "REFLEXO EM 13º SALÁRIO", "REFLEXO EM GRATIFICAÇÃO SEMESTRAL", "DIFERENÇA DE PLR", "FGTS 8%", "MULTA 40% FGTS"])
        rows = [["Descrição de créditos e descontos do reclamante", "Valor corrigido", "Juros", "Total"]]; tot = 0
        for v in verbas:
            vc = base * rng.uniform(.03, .35); j = vc * rng.uniform(.15, .3); tot += vc + j
            rows.append([v, money(vc), money(j), money(vc + j)])
        rows += [["Total devido pelo reclamado", "", "", money(tot)], ["DEDUÇÃO DE CONTRIBUIÇÃO SOCIAL", "", "", "(" + money(tot*.09) + ")"], ["DEDUÇÃO DE IRPF", "", "", "(" + money(tot*.05) + ")"], ["LÍQUIDO DEVIDO AO RECLAMANTE", "", "", money(tot*.86)]]
        B.append(("table", rows, [210, 75, 65, 75]))
        B.append(("table", [["Descrição de débitos do reclamado", "Valor"], ["Líquido devido ao reclamante", money(tot*.86)], ["Contribuição social sobre salários devidos", money(tot*.29)], ["IRPF devido pelo reclamante", money(tot*.05)], ["Honorários líquidos para patrono do reclamante", money(tot*.1)], ["Custas judiciais devidas pelo reclamado", money(tot*.02)], ["Total devido pelo reclamado", money(tot*1.32)]], [280, 120]))
        B.append(("small", f"Cálculo liquidado por offline na versão {ch(['2.12.1', '2.13.0', '2.11.4'])} em {dfmt(d)} às {hora()}."))
        quem = ch(["adv_a", "perito"])
        if quem == "perito":
            B.append(("sig", [c.perito[0].upper(), "Perito(a) Contábil"]))
        else:
            B.append(("sig", [c.adv_a.nome.upper(), c.adv_a.oab]))
        return dict(blocks=B, autor=quem, data=d, sub="calculos_trab_pjecalc")
    B.append(("title", ch(["DEMONSTRATIVO DE ATUALIZAÇÃO DO DÉBITO", "PLANILHA DE CÁLCULO – CUMPRIMENTO DE SENTENÇA", "MEMÓRIA DE CÁLCULO (art. 524 do CPC)", "CÁLCULO DE LIQUIDAÇÃO DE SENTENÇA"])))
    B.append(("kv", [("Processo", c.numero), ("Exequente", x["AUTOR"]), ("Executado", c.reu.nome), ("Data-base do cálculo", dfmt(d))]))
    B.append(("small", "Critérios: correção monetária pela Tabela Prática para Cálculo de Atualização Monetária dos Débitos Judiciais do TJSP até 29/08/2024 e pelo IPCA a partir de 30/08/2024 (Lei nº 14.905/2024); juros de mora de 1% ao mês até 29/08/2024 e, a partir de então, pela taxa legal (SELIC deduzido o IPCA – art. 406, § 1º, do CC)." if c.uf == "SP" else "Critérios: correção monetária pelo índice da Corregedoria-Geral de Justiça (ICGJ/INPC) até 29/08/2024 e pelo IPCA a partir de 30/08/2024; juros de mora de 1% a.m. e, após, pela taxa legal (art. 406 do CC)."))
    rows = [["Descrição", "Data-base", "Valor original", "Fator correção", "Valor corrigido", "Juros", "Subtotal"]]
    tot = 0
    itens = []
    if c.assunto in ("negativacao", "fraude_pix", "consignado", "tarifas"):
        itens.append(("Danos morais", c.data_sent, c.dano_moral_fix))
    if c.assunto == "fraude_pix":
        for i, v in enumerate(c.pix): itens.append((f"Restituição Pix {i+1}", c.data_fato, v))
    if c.assunto in ("consignado", "tarifas"):
        k = rng.randint(6, 14); val = c.parcela if c.assunto == "consignado" else c.tarifa
        for i in range(k): itens.append((f"Desconto {i+1:02d} (em dobro)", c.data_fato + dt.timedelta(days=30 * i), val * 2))
    if c.assunto == "revisional":
        for i in range(rng.randint(10, 16)): itens.append((f"Diferença parc. {i+1:02d}", c.data_fato + dt.timedelta(days=30 * i), round(c.parcela - c.parcela / (1 + (c.taxa - c.media) / 10), 2)))
    for desc, db, v in itens:
        meses = max(1, (d - db).days // 30); f = round((1.0045) ** meses, 6); vc = v * f
        j = vc * (0.01 * (meses if desc != "Danos morais" else max(1, (d - c.data_sent).days // 30)))
        tot += vc + j
        rows.append([desc, dfmt(db), money(v), f"{f:.6f}".replace(".", ","), money(vc), money(j), money(vc + j)])
    B.append(("table", rows, [92, 58, 62, 52, 62, 55, 62], 7))
    mult = tot * .1; hon = tot * .1; hs = tot * rng.choice([.1, .15])
    B.append(("table", [["Resumo", "Valor"], ["Principal atualizado + juros", money(tot)], ["Honorários sucumbenciais fixados na sentença", money(hs)], ["Multa de 10% (art. 523, § 1º, do CPC)", money(mult)], ["Honorários de 10% (art. 523, § 1º, do CPC)", money(hon)], ["Custas e despesas reembolsáveis", money(rng.uniform(80, 900))], ["TOTAL DO DÉBITO", money(tot + mult + hon + hs)]], [280, 120]))
    if estilo == "memoria":
        B.append(("p", f"Valor total do débito em {dfmt(d)}: {money(tot + mult + hon + hs)} ({extenso(round(tot + mult + hon + hs, 2))})."))
    B.append(("pn", local_data(c, d))); B.append(("sig", [c.adv_a.nome.upper(), c.adv_a.oab]))
    return dict(blocks=B, autor="adv_a", data=d, sub="calculos_civel")

# ================================================================= ALVARÁ
def alvara(c):
    x = ctx(c); B = []; trab = c.justica == "trab"
    d = bizday(c.data_sent, rng.randint(120, 500)); val = round(c.valor_causa * rng.uniform(.2, .9), 2)
    estilo = "mle" if c.uf == "SP" and not trab and rng.random() < .6 else "alvara"
    numero = f"{rng.randint(1,9999):04d}/{d.year}"
    benef = rng.choice(["autor", "adv", "perito"])
    if benef == "autor": bn, bcpf = x["AUTOR"], c.autor.cpf
    elif benef == "adv": bn, bcpf = c.adv_a.nome.upper(), cpf()
    else: bn, bcpf = c.perito[0].upper(), cpf()
    B.append(capa_processo(c, x))
    if estilo == "mle":
        B.append(("title", "MANDADO DE LEVANTAMENTO ELETRÔNICO" + ch(["", " – MLE", " Nº " + numero])))
        B.append(("p", f"{'A' if c.juiz_g=='f' else 'O'} MM. {x['Juiz']} de Direito da {c.vara}, Dr{'a' if c.juiz_g=='f' else ''}. {c.juiz}, AUTORIZA o Banco do Brasil S.A. a efetuar o pagamento/transferência ao beneficiário abaixo indicado, do valor depositado nos autos, com os acréscimos legais."))
    else:
        B.append(("title", ch(["ALVARÁ JUDICIAL", "ALVARÁ DE LEVANTAMENTO", "ALVARÁ JUDICIAL DE LEVANTAMENTO"]) + f" Nº {numero}" + (" – SIF" if trab and rng.random() < .5 else "")))
        B.append(("p", f"{'A' if c.juiz_g=='f' else 'O'} Doutor{'a' if c.juiz_g=='f' else ''} {c.juiz}, MM. {x['Juiz']} {'do Trabalho' if trab else 'de Direito'} da {c.vara}, na forma da lei, AUTORIZA {'o(a) beneficiário(a) abaixo qualificado(a)' if rng.random()<.5 else bn} a levantar, junto ao {ch(['Banco do Brasil S.A.', 'Caixa Econômica Federal'])}, a importância depositada na conta judicial abaixo indicada."))
    rows = [("Beneficiário(a)", bn), ("CPF", bcpf), ("Qualidade", {"autor": "Parte autora" if not trab else "Reclamante", "adv": "Advogado(a) – " + c.adv_a.oab + " – com poderes para receber e dar quitação", "perito": "Perito(a) judicial – honorários periciais"}[benef]),
            ("Conta judicial / ID depósito", f"{rng.randint(10**12, 10**13)} / ID {rng.randint(10**15, 10**16)}"), ("Valor", money(val) + " (" + extenso(val) + ")" + ch([", acrescido de correção monetária e juros", " – levantamento integral do saldo", ""])),
            ("Forma", ch(["Transferência para conta de titularidade do beneficiário", "Saque em espécie / crédito em conta", "Transferência – Banco " + f"{rng.randint(1,756):03d}" + f", Ag. {rng.randint(100,9999)}, C/C {rng.randint(10000,999999)}-{rng.randint(0,9)}"])),
            ("Incidência de IR", ch(["Isento", "Retenção na fonte, se cabível", "Não há retenção"]))]
    B.append(("kv", rows))
    B.append(("p", f"Prazo de validade: {ch(['30 (trinta)', '60 (sessenta)', '90 (noventa)'])} dias, contados da data de expedição. " + ch(["O presente alvará é expedido eletronicamente e sua autenticidade pode ser verificada no sítio do Tribunal.", "Cumpra-se na forma e sob as penas da lei.", "Após o levantamento, a instituição financeira deverá comunicar o cumprimento a este Juízo."])))
    B.append(("pn", local_data(c, d)))
    B.append(("sig", juiz_sig(c, d)))
    return dict(blocks=B, autor="juiz", data=d, sub="mandado_levantamento_eletronico" if estilo == "mle" else "alvara")

GERADORES = dict(peticao_inicial=peticao_inicial, contestacao=contestacao, replica=replica, sentenca=sentenca, acordao=acordao,
                 decisao_interlocutoria=decisao_interlocutoria, despacho=despacho, embargos_declaracao=embargos_declaracao,
                 recurso_apelacao=recurso_apelacao, contrarrazoes=contrarrazoes, agravo_instrumento=agravo_instrumento,
                 procuracao=procuracao, substabelecimento=substabelecimento, certidao=certidao, mandado=mandado, oficio=oficio,
                 ata_audiencia=ata_audiencia, termo_acordo=termo_acordo, laudo_pericial=laudo_pericial,
                 calculos_liquidacao=calculos_liquidacao, alvara=alvara)
