# -*- coding: utf-8 -*-
"""Conteúdo material por assunto: fatos, teses, defesa, fundamentação, perícia."""
from casos import rng, ch, money, extenso, dfmt, dext, dt

def ctx(c):
    a, r = c.autor, c.reu
    trab, jec = c.justica == "trab", c.justica == "jec"
    oA = a.o(); fA = oA == "a"
    if trab:
        A, R, oR = "Reclamante", "Reclamada", "a"
    elif jec:
        A = "Requerente"; R = "Requerido" if r.g == "m" else "Requerida"; oR = r.o()
    else:
        A = "Autora" if fA else "Autor"; R = ("Réu" if r.g == "m" else "Ré"); oR = r.o()
    con = lambda art, m, f: m if art == "o" else f
    x = dict(
        A=A, R=R, oA=oA, oR=oR, OA=oA.upper(), OR=oR.upper(), sA=oA,
        dA=con(oA, "do", "da"), dR=con(oR, "do", "da"), aoA=con(oA, "ao", "à"), aoR=con(oR, "ao", "à"),
        pA=con(oA, "pelo", "pela"), pR=con(oR, "pelo", "pela"), nA=con(oA, "no", "na"),
        AUTOR=a.nome.upper(), REU=r.nome, autor=a.nome, reu=r.nome,
        numero=c.numero, vara=c.vara, cidade=c.cidade, uf=c.uf,
        contrato=c.contrato, protocolo=c.protocolo, debito=money(c.valor_debito),
        debito_ext=extenso(c.valor_debito), dobro=money(2 * c.valor_debito),
        dano_pedido=money(c.dano_moral_pedido), dano_pedido_ext=extenso(c.dano_moral_pedido),
        dano_fix=money(c.dano_moral_fix), dano_fix_ext=extenso(c.dano_moral_fix),
        valor_causa=money(c.valor_causa), valor_causa_ext=extenso(c.valor_causa),
        data_fato=dext(c.data_fato), data_fato_n=dfmt(c.data_fato),
        venc=dfmt(c.data_fato - dt.timedelta(days=rng.randint(40, 200))),
        data_contr=dfmt(c.data_fato - dt.timedelta(days=rng.randint(200, 700))),
        loja=ch(["Lojas Paraíso Móveis e Eletro", "Magazine Bom Preço", "Casa Real Eletrodomésticos",
                 "Loja Nova Era Calçados", "Ótica Visão Clara", "Comercial Mantiqueira Ltda."]),
        juiz=c.juiz, relator=c.relator, sigla=c.sigla, trib=c.trib,
        Juiz="Juíza" if c.juiz_g == "f" else "Juiz",
    )
    x["a_fem"] = "a" if fA else ""
    x["nA_conta"] = f"corrente nº {rng.randint(10000,99999)}-{rng.randint(0,9)}, agência {rng.randint(100,3999)}"
    x["hx1"] = money(round(c.valor_causa * rng.uniform(.45, .6), 2))
    x["hx2"] = money(round(c.valor_causa * rng.uniform(.1, .2), 2))
    if c.assunto == "fraude_pix":
        x["n_pix"] = len(c.pix); x["pix_list"] = "; ".join(money(v) for v in c.pix)
        x["hora_golpe"] = f"{rng.randint(9,20)}h{rng.randint(0,59):02d}"
        x["banco_dest"] = ch(["instituições de pagamento digitais", "contas mantidas em bancos digitais", "contas de titularidade de terceiros desconhecidos"])
    if c.assunto == "consignado":
        x.update(parcela=money(c.parcela), n_parc=c.n_parc, nb=c.nb,
                 total_contr=money(round(c.parcela * c.n_parc, 2)),
                 liberado=money(round(c.parcela * c.n_parc * rng.uniform(.42, .55), 2)))
    if c.assunto == "revisional":
        x.update(bem=c.bem, financiado=money(c.financiado), n_parc=c.n_parc, taxa=f"{c.taxa:.2f}".replace(".", ","),
                 media=f"{c.media:.2f}".replace(".", ","), parcela=money(c.parcela),
                 taxa_a=f"{((1 + c.taxa/100)**12 - 1)*100:.2f}".replace(".", ","),
                 tac=money(ch([590, 790, 990, 1290])), seguro=money(round(rng.uniform(900, 3200), 2)))
    if c.assunto == "tarifas":
        x.update(tarifa=money(c.tarifa), meses=c.meses, cesta=c.cesta)
    if trab:
        x.update(cargo=c.cargo, admissao=dfmt(c.admissao), dispensa=dfmt(c.dispensa), salario=money(c.salario),
                 paradigma=c.paradigma, agencia=c.agencia, ji=c.jornada_ini, jf=c.jornada_fim,
                 dif_sal=money(round(c.salario * rng.uniform(.12, .35), 2)))
    return x

def F(lst, x):
    out = []
    for it in lst:
        if isinstance(it, tuple): out.append(tuple(s.format(**x) for s in it))
        else: out.append(it.format(**x))
    return out

# ===================================================================== ASSUNTOS
A = {}

A["negativacao"] = dict(
 acao="AÇÃO DECLARATÓRIA DE INEXISTÊNCIA DE DÉBITO C/C INDENIZAÇÃO POR DANOS MORAIS COM PEDIDO DE TUTELA DE URGÊNCIA",
 cnj="Indenização por Dano Moral - Inclusão Indevida em Cadastro de Inadimplentes",
 fatos=[
  "{OA} {A} foi surpreendid{sA} em {data_fato}, ao tentar realizar compra a prazo no estabelecimento {loja}, com a informação de que seu nome se encontrava inscrito nos órgãos de proteção ao crédito, o que impediu a conclusão do negócio e lhe causou constrangimento diante de funcionários e demais clientes.",
  "Em consulta realizada junto ao Serasa Experian e ao SCPC (docs. 03 e 04), constatou que a anotação fora promovida {pR} {R}, em razão do suposto contrato nº {contrato}, no valor de {debito}, com vencimento apontado em {venc}.",
  "Ocorre, Excelência, que {oA} {A} jamais celebrou o referido contrato, tampouco solicitou cartão, empréstimo ou qualquer outro produto junto {aoR} {R}, desconhecendo integralmente a origem da dívida. Tampouco recebeu a notificação prévia exigida pelo art. 43, § 2º, do Código de Defesa do Consumidor.",
  "Buscando solução amigável, {oA} {A} entrou em contato com a central de atendimento {dR} {R}, sendo gerado o protocolo nº {protocolo}, e registrou reclamação na plataforma consumidor.gov.br. A empresa, contudo, limitou-se a afirmar que a cobrança era devida, sem apresentar qualquer documento que comprovasse a contratação.",
  "Registre-se que não há outras anotações em nome {dA} {A} além daquela ora impugnada, conforme extrato atualizado anexo, o que afasta a incidência da Súmula 385 do Superior Tribunal de Justiça.",
 ],
 direito=[
  ("DA RELAÇÃO DE CONSUMO E DA INVERSÃO DO ÔNUS DA PROVA", "A relação estabelecida entre as partes é de consumo, ainda que por equiparação (art. 17 do CDC), na medida em que {oA} {A} é vítima de evento decorrente da atividade desenvolvida {pR} {R}. Incide, ademais, a Súmula 297 do STJ, segundo a qual o Código de Defesa do Consumidor é aplicável às instituições financeiras. Diante da verossimilhança das alegações e da evidente hipossuficiência técnica, impõe-se a inversão do ônus da prova (art. 6º, VIII, do CDC), cabendo {aoR} {R} demonstrar a regularidade da contratação, já que não se pode exigir {dA} consumidor{a_fem} prova de fato negativo."),
  ("DA RESPONSABILIDADE OBJETIVA E DO FORTUITO INTERNO", "Nos termos do art. 14 do CDC, o fornecedor responde, independentemente da existência de culpa, pela reparação dos danos causados aos consumidores por defeitos relativos à prestação dos serviços. A eventual atuação de fraudadores não exime a instituição de responsabilidade, por se tratar de fortuito interno, conforme orientação consolidada na Súmula 479 do STJ."),
  ("DO DANO MORAL IN RE IPSA", "A inscrição indevida do nome do consumidor em cadastros de inadimplentes configura dano moral presumido, dispensando prova do efetivo prejuízo, conforme pacífica jurisprudência do Superior Tribunal de Justiça. A restrição abalou o crédito {dA} {A}, impediu a realização de compras e expôs sua imagem perante o comércio local, devendo a indenização ser fixada em patamar que atenda ao caráter compensatório e pedagógico, sugerindo-se o montante de {dano_pedido} ({dano_pedido_ext})."),
 ],
 tutela="Estão presentes os requisitos do art. 300 do CPC. A probabilidade do direito decorre da negativa de contratação e da ausência de qualquer documento que vincule {oA} {A} ao débito. O perigo de dano é evidente, pois a manutenção da restrição impede o acesso ao crédito e prolonga a violação à honra objetiva, sendo a medida plenamente reversível (art. 300, § 3º, do CPC). Requer-se, portanto, a exclusão imediata do nome {dA} {A} dos cadastros de proteção ao crédito, sob pena de multa diária.",
 pedidos=[
  "a concessão da tutela de urgência para determinar {aoR} {R} que promova a exclusão do nome {dA} {A} dos cadastros de inadimplentes no prazo de 48 (quarenta e oito) horas, sob pena de multa diária de R$ 500,00;",
  "a inversão do ônus da prova, nos termos do art. 6º, VIII, do CDC;",
  "a declaração de inexistência do débito de {debito}, referente ao contrato nº {contrato}, tornando definitiva a tutela;",
  "a condenação {dR} {R} ao pagamento de indenização por danos morais no valor de {dano_pedido}, corrigido monetariamente e acrescido de juros de mora desde o evento danoso (Súmula 54 do STJ);",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA AUSÊNCIA DE INTERESSE DE AGIR", "{OA} {A} não comprovou ter buscado solução administrativa junto aos canais oficiais antes do ajuizamento da demanda. A ausência de pretensão resistida revela a desnecessidade da tutela jurisdicional, impondo-se a extinção do feito sem resolução do mérito, nos termos do art. 485, VI, do CPC."),
 ],
 defesa=[
  ("DA REGULARIDADE DA CONTRATAÇÃO", "Ao contrário do que sustenta a inicial, {oA} {A} contratou, em {data_contr}, o produto vinculado ao contrato nº {contrato}, por meio do aplicativo oficial, com validação por biometria facial, geolocalização e confirmação de token, conforme trilha de auditoria ora juntada. O débito decorre da utilização do crédito disponibilizado e do inadimplemento das faturas a partir de {venc}."),
  ("DO EXERCÍCIO REGULAR DE DIREITO", "Existindo débito vencido e não pago, a inscrição do nome do devedor nos cadastros de proteção ao crédito constitui exercício regular de direito, nos termos do art. 188, I, do Código Civil, inexistindo ato ilícito apto a ensejar reparação. A comunicação prévia, por sua vez, incumbe ao órgão mantenedor do cadastro, e não ao credor, conforme a Súmula 359 do STJ."),
  ("DA INCIDÊNCIA DA SÚMULA 385 DO STJ", "Ainda que se cogitasse de irregularidade, consulta atualizada aos órgãos de proteção ao crédito revela a existência de outras anotações em nome {dA} {A}, circunstância que afasta o dever de indenizar, nos termos da Súmula 385 do STJ."),
  ("DA INEXISTÊNCIA DE DANO MORAL E DO QUANTUM", "O mero dissabor cotidiano não se confunde com dano moral indenizável, e não há nos autos prova de repercussão concreta na esfera extrapatrimonial {dA} {A}. Subsidiariamente, eventual condenação deve observar os princípios da razoabilidade e da proporcionalidade, sob pena de enriquecimento sem causa (art. 884 do Código Civil)."),
 ],
 fund_proc=[
  "No mérito, a pretensão merece acolhimento. Negada a contratação, incumbia {aoR} {R}, nos termos do art. 373, II, do CPC e do art. 6º, VIII, do CDC, comprovar a existência de relação jurídica válida que justificasse a cobrança. Desse ônus, contudo, não se desincumbiu.",
  "Os documentos apresentados com a contestação consistem em telas de sistema interno, produzidas unilateralmente, sem assinatura {dA} {A} ou qualquer elemento seguro de autenticação. A alegada validação biométrica não veio acompanhada do respectivo relatório técnico, nem da fotografia supostamente capturada no ato da contratação.",
  "Tratando-se de fraude praticada por terceiro, a responsabilidade da instituição permanece, pois o risco é inerente à atividade desenvolvida, nos termos da Súmula 479 do STJ. Reconhecida a inexistência do débito, a inscrição revela-se indevida.",
  "O dano moral, na hipótese, é presumido e decorre da própria inscrição indevida. Considerando as circunstâncias do caso, a capacidade econômica das partes e o caráter pedagógico da medida, fixo a indenização em {dano_fix}, valor adequado aos parâmetros adotados em casos análogos.",
 ],
 fund_improc=[
  "A pretensão não comporta acolhimento. {OR} {R} trouxe aos autos o instrumento contratual com assinatura eletrônica {dA} {A}, acompanhado de relatório de autenticação contendo fotografia (selfie), geolocalização compatível com o endereço declarado na inicial e registro do dispositivo utilizado.",
  "Intimad{sA} a se manifestar, {oA} {A} limitou-se a impugnar genericamente os documentos, sem apontar vício concreto, e não requereu a produção de prova pericial. Demonstrado o crédito, inclusive com a disponibilização de valores em conta de sua titularidade, a inscrição constitui exercício regular de direito (art. 188, I, do Código Civil).",
  "Ainda que assim não fosse, os extratos dos órgãos de proteção revelam anotações preexistentes, a atrair a incidência da Súmula 385 do STJ.",
 ],
 disp_proc="a) DECLARAR a inexistência do débito de {debito}, referente ao contrato nº {contrato}; b) CONDENAR {oR} {R} ao pagamento de indenização por danos morais no valor de {dano_fix}, corrigido monetariamente a partir desta data (Súmula 362 do STJ) e acrescido de juros de mora desde o evento danoso (Súmula 54 do STJ); c) TORNAR DEFINITIVA a tutela de urgência anteriormente concedida.",
 ementa="APELAÇÃO CÍVEL. AÇÃO DECLARATÓRIA DE INEXISTÊNCIA DE DÉBITO C/C INDENIZAÇÃO POR DANOS MORAIS. NEGATIVAÇÃO INDEVIDA. Contratação negada pelo consumidor. Ausência de prova da relação jurídica. Ônus que incumbia à instituição (art. 373, II, do CPC). Fortuito interno. Súmula 479 do STJ. Dano moral in re ipsa. Quantum indenizatório",
 pericia="grafotécnica",
)

A["fraude_pix"] = dict(
 acao="AÇÃO DE RESTITUIÇÃO DE VALORES C/C INDENIZAÇÃO POR DANOS MORAIS",
 cnj="Responsabilidade do Fornecedor - Indenização por Dano Material",
 fatos=[
  "{OA} {A} é correntista {dR} {R} há vários anos, utilizando a conta para recebimento de seus proventos e pagamento de despesas ordinárias, com movimentação modesta e absolutamente regular.",
  "No dia {data_fato}, por volta das {hora_golpe}, recebeu ligação telefônica de pessoa que se identificou como funcionária do setor de segurança {dR} {R}. O número exibido no identificador de chamadas correspondia ao da central oficial da instituição, e a interlocutora tinha conhecimento de dados pessoais e bancários {dA} {A}, como número da agência, conta e últimas movimentações.",
  "Sob o pretexto de que a conta estaria sendo alvo de tentativas de invasão, {oA} {A} foi orientad{sA} a acessar o aplicativo para \"atualizar o dispositivo de segurança\". Na sequência, foram realizadas {n_pix} transferências via Pix, em intervalo inferior a quarenta minutos, nos valores de {pix_list}, totalizando {debito}, todas destinadas a {banco_dest}.",
  "Percebendo o golpe, {oA} {A} contatou imediatamente a central de atendimento, sendo gerado o protocolo nº {protocolo}, e lavrou boletim de ocorrência no mesmo dia. Requereu expressamente o acionamento do Mecanismo Especial de Devolução (MED), instituído pelo Banco Central, mas foi informad{sA}, dias depois, de que o pedido havia sido indeferido sob a justificativa de que as transações foram realizadas com senha pessoal.",
  "As transações destoam completamente do perfil de consumo {dA} {A}: nunca havia realizado transferências de valores semelhantes, as operações ocorreram em sequência e para destinatários jamais cadastrados, esgotando o saldo e parte do limite do cheque especial. Nenhum bloqueio preventivo, contudo, foi acionado.",
 ],
 direito=[
  ("DA FALHA NA PRESTAÇÃO DO SERVIÇO", "A segurança das operações é elemento essencial do serviço bancário. Ao permitir a realização de sucessivas transferências atípicas, sem qualquer mecanismo de validação adicional ou bloqueio preventivo, {oR} {R} falhou no dever de segurança que lhe é imposto, respondendo objetivamente pelos danos, nos termos do art. 14 do CDC e da Súmula 479 do STJ."),
  ("DA INAPLICABILIDADE DA EXCLUDENTE DE CULPA EXCLUSIVA", "Não há que se falar em culpa exclusiva da vítima. O golpe somente foi possível em razão do vazamento de dados sigilosos que estavam sob a guarda da instituição, o que evidencia defeito na prestação do serviço e atrai a responsabilidade do fornecedor, nos termos da Lei nº 13.709/2018 (LGPD) e da Resolução BCB nº 1/2020, que disciplina o arranjo Pix e impõe às instituições a adoção de mecanismos de prevenção a fraudes."),
  ("DOS DANOS MATERIAIS E MORAIS", "Os danos materiais correspondem ao montante subtraído, {debito}, que deve ser restituído com correção monetária desde cada desembolso. Os danos morais decorrem da angústia de ver suprimidas as economias de anos e da desídia da instituição no atendimento, que deixou {oA} consumidor{a_fem} desamparad{sA}. Sugere-se indenização de {dano_pedido}."),
 ],
 tutela=None,
 pedidos=[
  "a inversão do ônus da prova, determinando-se {aoR} {R} a apresentação dos registros completos das transações (logs, IP, dispositivo e geolocalização);",
  "a condenação {dR} {R} à restituição de {debito}, corrigidos monetariamente desde cada transferência e acrescidos de juros de mora desde a citação;",
  "a condenação {dR} {R} ao pagamento de indenização por danos morais no valor de {dano_pedido};",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA ILEGITIMIDADE PASSIVA", "Os valores foram creditados em contas de titularidade de terceiros mantidas em outras instituições, as quais, efetivamente, receberam e permitiram a movimentação dos recursos. Não tendo {oR} {R} se beneficiado das transações, carece de legitimidade para figurar no polo passivo, impondo-se a extinção do feito nos termos do art. 485, VI, do CPC."),
 ],
 defesa=[
  ("DA CULPA EXCLUSIVA DA VÍTIMA", "As transações impugnadas foram realizadas a partir do dispositivo habitualmente utilizado {pA} {A}, cadastrado e autenticado, mediante digitação de senha pessoal e intransferível. Foi {oA} própri{sA} {A} quem, voluntariamente, seguiu as instruções de terceiro desconhecido, rompendo o nexo causal, nos termos do art. 14, § 3º, II, do CDC."),
  ("DA AUSÊNCIA DE FALHA NA PRESTAÇÃO DO SERVIÇO", "O sistema da instituição funcionou corretamente. Não houve invasão, clonagem ou vazamento de dados, inexistindo nos autos qualquer prova de que as informações utilizadas pelos golpistas tenham sido obtidas a partir dos sistemas {dR} {R}. A instituição divulga reiteradamente, em seus canais oficiais, que jamais solicita senhas ou movimentações por telefone."),
  ("DO MECANISMO ESPECIAL DE DEVOLUÇÃO", "O MED foi devidamente acionado após a contestação {dA} {A}. Contudo, quando da análise, os recursos já haviam sido integralmente transferidos das contas recebedoras, inviabilizando a devolução. A instituição cumpriu, portanto, todas as obrigações regulamentares previstas na Resolução BCB nº 103/2021."),
  ("DA INEXISTÊNCIA DE DANO MORAL", "Ausente ato ilícito, não há dever de indenizar. Ainda que assim não fosse, eventual prejuízo material não implica, por si só, ofensa a direito da personalidade."),
 ],
 fund_proc=[
  "A controvérsia reside em definir se as transações impugnadas decorreram de falha na prestação do serviço ou de culpa exclusiva da vítima. Aplicável o Código de Defesa do Consumidor (Súmula 297 do STJ), a responsabilidade da instituição é objetiva e somente se afasta mediante prova de alguma das excludentes do art. 14, § 3º, do CDC.",
  "Os extratos juntados demonstram que, em menos de uma hora, foram realizadas {n_pix} transferências, em valores e para destinatários totalmente incompatíveis com o histórico da conta. O padrão é típico de fraude e deveria ter sido identificado pelos sistemas de monitoramento que a própria instituição afirma possuir. A Resolução BCB nº 1/2020 impõe aos participantes do arranjo Pix a adoção de mecanismos capazes de identificar transações atípicas, o que não ocorreu.",
  "O fato de o consumidor ter sido induzido a erro por terceiro não afasta a responsabilidade quando a instituição deixa de adotar as cautelas mínimas exigíveis, configurando-se o fortuito interno de que trata a Súmula 479 do STJ. Devida, assim, a restituição integral de {debito}.",
  "Quanto aos danos morais, a subtração de valores destinados à subsistência, somada à resistência injustificada da instituição em solucionar o problema administrativamente, ultrapassa o mero aborrecimento. Fixo a indenização em {dano_fix}.",
 ],
 fund_improc=[
  "A pretensão não procede. É incontroverso que {oA} {A}, após contato telefônico de terceiro, acessou o aplicativo e confirmou as operações mediante digitação de sua senha pessoal, conforme admitido na própria inicial.",
  "Embora lamentável a situação, não há nos autos elemento que indique falha de segurança no sistema da instituição ou vazamento de dados a partir de seus bancos. As operações foram realizadas no aparelho habitual, com autenticação regular, e a própria vítima forneceu as credenciais, rompendo o nexo de causalidade (art. 14, § 3º, II, do CDC).",
  "Ademais, a instituição comprovou ter acionado o Mecanismo Especial de Devolução tão logo comunicada, sem êxito pela inexistência de saldo nas contas recebedoras, o que afasta a alegada omissão.",
 ],
 disp_proc="a) CONDENAR {oR} {R} a restituir {aoA} {A} a quantia de {debito}, corrigida monetariamente desde cada desembolso e acrescida de juros de mora desde a citação; b) CONDENAR {oR} {R} ao pagamento de indenização por danos morais no valor de {dano_fix}, com correção monetária a partir desta data e juros de mora desde a citação.",
 ementa="RECURSO. AÇÃO DE RESTITUIÇÃO DE VALORES C/C DANOS MORAIS. GOLPE DA FALSA CENTRAL DE ATENDIMENTO. TRANSFERÊNCIAS VIA PIX. Sucessivas operações atípicas, incompatíveis com o perfil do correntista. Falha no dever de segurança. Fortuito interno. Súmula 479 do STJ",
 pericia=None,
)

A["consignado"] = dict(
 acao="AÇÃO DECLARATÓRIA DE NULIDADE DE CONTRATO C/C REPETIÇÃO DE INDÉBITO E INDENIZAÇÃO POR DANOS MORAIS",
 cnj="Contratos Bancários - Empréstimo consignado",
 fatos=[
  "{OA} {A} é aposentad{sA} pelo Instituto Nacional do Seguro Social (INSS), titular do benefício nº {nb}, que constitui sua única fonte de renda.",
  "A partir de {data_fato_n}, passou a perceber descontos mensais de {parcela} em seu benefício, sob a rubrica \"EMPRÉSTIMO SOBRE A RMC/CONSIGNAÇÃO\", vinculados ao contrato nº {contrato}, firmado supostamente com {oR} {R}, para pagamento em {n_parc} parcelas, totalizando {total_contr}.",
  "Ocorre que {oA} {A} jamais solicitou, assinou ou autorizou a contratação de qualquer empréstimo junto {aoR} {R}, não tendo recebido o contrato, as cédulas de crédito ou qualquer comunicação acerca da operação. Pessoa simples, de pouca instrução, somente tomou conhecimento dos descontos ao consultar o extrato de pagamento do benefício.",
  "Diligenciou junto à agência e à ouvidoria {dR} {R} (protocolo nº {protocolo}), sem obter cópia do suposto contrato ou o cancelamento da consignação. Até o momento, já foram descontados indevidamente {debito}, valores que fazem falta à manutenção de sua subsistência.",
 ],
 direito=[
  ("DA NULIDADE DO NEGÓCIO JURÍDICO", "Inexistente a manifestação de vontade, não há negócio jurídico válido. A contratação de empréstimo consignado com desconto em benefício previdenciário exige autorização expressa do beneficiário, nos termos do art. 6º da Lei nº 10.820/2003 e da Instrução Normativa INSS/PRES nº 138/2022. A ausência de tal autorização impõe a declaração de nulidade do contrato e a cessação imediata dos descontos."),
  ("DA REPETIÇÃO DO INDÉBITO EM DOBRO", "Os valores indevidamente descontados devem ser restituídos em dobro, nos termos do art. 42, parágrafo único, do CDC, independentemente da natureza do elemento volitivo do fornecedor, bastando que a cobrança indevida consubstancie conduta contrária à boa-fé objetiva, conforme tese firmada pela Corte Especial do STJ no julgamento do EAREsp 676.608/RS."),
  ("DOS DANOS MORAIS", "O desconto indevido em verba de natureza alimentar de pessoa idosa ultrapassa o mero aborrecimento, comprometendo sua subsistência e violando sua dignidade, devendo ser fixada indenização em montante não inferior a {dano_pedido}."),
 ],
 tutela="A probabilidade do direito está evidenciada pela negativa de contratação e pelos extratos do INSS que comprovam os descontos. O perigo de dano é manifesto, pois os descontos recaem sobre verba alimentar de pessoa idosa. Requer-se a suspensão imediata dos descontos referentes ao contrato nº {contrato}, sob pena de multa por desconto indevido.",
 pedidos=[
  "a concessão de tutela de urgência para suspender imediatamente os descontos referentes ao contrato nº {contrato} no benefício nº {nb};",
  "a prioridade na tramitação, nos termos do art. 1.048, I, do CPC e do art. 71 do Estatuto da Pessoa Idosa;",
  "a declaração de nulidade/inexistência do contrato nº {contrato};",
  "a condenação {dR} {R} à restituição em dobro dos valores descontados, que somam até o momento {debito}, totalizando {dobro}, além das parcelas que se vencerem no curso da demanda;",
  "a condenação {dR} {R} ao pagamento de indenização por danos morais no valor de {dano_pedido};",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA PRESCRIÇÃO", "A pretensão de repetição de indébito relativa a parcelas descontadas há mais de três anos encontra-se fulminada pela prescrição, nos termos do art. 206, § 3º, IV e V, do Código Civil, devendo ser reconhecida na forma do art. 487, II, do CPC."),
 ],
 defesa=[
  ("DA REGULARIDADE DA CONTRATAÇÃO", "O contrato nº {contrato} foi celebrado em {data_contr}, com assinatura {dA} {A}, apresentação de documento de identidade e comprovante de residência, conforme cópias anexas. O valor líquido de {liberado} foi creditado por TED em conta de titularidade {dA} {A}, que dele se beneficiou, conforme comprovante de transferência ora juntado."),
  ("DA VEDAÇÃO AO COMPORTAMENTO CONTRADITÓRIO", "Tendo recebido e utilizado o crédito, {oA} {A} não pode agora alegar desconhecimento da contratação, sob pena de violação à boa-fé objetiva e ao princípio do venire contra factum proprium. Caso declarada a nulidade, impõe-se a compensação do valor creditado, sob pena de enriquecimento sem causa (art. 884 do Código Civil)."),
  ("DA IMPOSSIBILIDADE DE RESTITUIÇÃO EM DOBRO", "Não houve má-fé na cobrança, que decorreu de contrato formalmente válido. A restituição, se cabível, deve se dar na forma simples."),
  ("DA AUSÊNCIA DE DANO MORAL", "Os descontos, de pequena monta, não comprometeram a subsistência {dA} {A}, inexistindo prova de abalo extrapatrimonial."),
 ],
 fund_proc=[
  "Impugnada a assinatura lançada no contrato, incumbia à instituição financeira o ônus de comprovar sua autenticidade, nos termos do art. 429, II, do CPC e do Tema 1.061 dos recursos repetitivos do STJ.",
  "Realizada a perícia grafotécnica, o laudo concluiu de forma categórica que a assinatura aposta no instrumento não proveio do punho escritor {dA} {A}, apresentando divergências de valores formais e gráficos incompatíveis com os padrões colhidos em cartório. A conclusão não foi infirmada por qualquer outro elemento de prova.",
  "Comprovada a fraude, o contrato é nulo e os descontos indevidos. A restituição deve ocorrer em dobro, pois a cobrança sem lastro contratual viola a boa-fé objetiva (EAREsp 676.608/RS). Admite-se, todavia, a compensação com o valor efetivamente creditado em conta {dA} {A}, a fim de evitar enriquecimento sem causa.",
  "O desconto indevido em benefício previdenciário de pessoa idosa, verba de caráter alimentar, configura dano moral. Fixo a indenização em {dano_fix}.",
 ],
 fund_improc=[
  "A prova dos autos demonstra a regularidade da contratação. {OR} {R} juntou o contrato assinado, cópias dos documentos pessoais {dA} {A} e o comprovante de TED do valor líquido de {liberado} para conta de sua titularidade, não impugnado especificamente.",
  "A perícia grafotécnica concluiu que a assinatura lançada no instrumento proveio do punho escritor {dA} {A}, com convergência de elementos formais e de gênese gráfica. Não há, portanto, vício de consentimento ou fraude a ser reconhecida.",
 ],
 disp_proc="a) DECLARAR a nulidade do contrato nº {contrato} e determinar a cessação definitiva dos descontos; b) CONDENAR {oR} {R} a restituir, em dobro, os valores descontados do benefício {dA} {A}, autorizada a compensação com a quantia creditada em sua conta, com correção monetária desde cada desconto e juros de mora desde a citação; c) CONDENAR {oR} {R} ao pagamento de indenização por danos morais de {dano_fix}.",
 ementa="APELAÇÃO. EMPRÉSTIMO CONSIGNADO. BENEFÍCIO PREVIDENCIÁRIO. Contratação negada pela autora. Perícia grafotécnica conclusiva quanto à falsidade da assinatura. Nulidade do contrato. Repetição do indébito em dobro (EAREsp 676.608/RS). Compensação com o valor creditado. Dano moral configurado",
 pericia="grafotécnica",
)

A["revisional"] = dict(
 acao="AÇÃO REVISIONAL DE CONTRATO BANCÁRIO C/C REPETIÇÃO DE INDÉBITO",
 cnj="Contratos Bancários - Revisão de juros",
 fatos=[
  "Em {data_contr}, {oA} {A} celebrou com {oR} {R} Cédula de Crédito Bancário nº {contrato}, destinada ao financiamento do {bem}, no valor de {financiado}, a ser pago em {n_parc} parcelas mensais de {parcela}.",
  "O instrumento prevê taxa de juros remuneratórios de {taxa}% ao mês ({taxa_a}% ao ano), muito superior à taxa média de mercado divulgada pelo Banco Central do Brasil para operações da mesma espécie no mês da contratação, que era de {media}% ao mês.",
  "Além disso, foram embutidas no financiamento tarifas de cadastro e avaliação do bem, no montante de {tac}, e seguro prestamista de {seguro}, contratado com seguradora integrante do mesmo grupo econômico, sem que fosse oferecida ao consumidor a possibilidade de escolha, configurando venda casada.",
  "{OA} {A} vem honrando as parcelas, mas a onerosidade excessiva do contrato compromete sua renda familiar, razão pela qual busca a revisão das cláusulas abusivas e a restituição do que foi pago a maior.",
 ],
 direito=[
  ("DOS JUROS REMUNERATÓRIOS ABUSIVOS", "Embora as instituições financeiras não se sujeitem à limitação de juros prevista na Lei de Usura (Súmula 596 do STF), a revisão é admitida quando cabalmente demonstrada a abusividade, em relação à taxa média de mercado, conforme orientação firmada no REsp 1.061.530/RS, julgado sob o rito dos recursos repetitivos. No caso, a taxa contratada supera em mais de uma vez e meia a média praticada, evidenciando a desvantagem exagerada vedada pelo art. 51, IV, do CDC."),
  ("DA VENDA CASADA DO SEGURO PRESTAMISTA", "Nos termos do Tema 972 do STJ, nos contratos bancários em geral, o consumidor não pode ser compelido a contratar seguro com a instituição financeira ou com seguradora por ela indicada. A imposição configura venda casada, prática abusiva vedada pelo art. 39, I, do CDC."),
  ("DA REPETIÇÃO DO INDÉBITO", "Os valores pagos a maior devem ser restituídos ou compensados com o saldo devedor, em dobro, nos termos do art. 42, parágrafo único, do CDC."),
 ],
 tutela="Requer-se, em tutela de urgência, autorização para o depósito em juízo das parcelas no valor que entende incontroverso, bem como a abstenção de inscrição do nome {dA} {A} nos cadastros de inadimplentes e a manutenção na posse do bem enquanto pendente a discussão, nos termos do art. 330, §§ 2º e 3º, do CPC.",
 pedidos=[
  "a revisão da Cédula de Crédito Bancário nº {contrato}, com a limitação dos juros remuneratórios à taxa média de mercado de {media}% ao mês;",
  "a declaração de abusividade da cobrança do seguro prestamista e das tarifas de avaliação do bem, com a restituição dos respectivos valores;",
  "a condenação {dR} {R} à restituição em dobro dos valores pagos a maior, a serem apurados em liquidação de sentença, ou sua compensação com o saldo devedor;",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA INÉPCIA DA INICIAL", "A petição inicial não discrimina, dentre as obrigações contratuais, aquelas que pretende controverter, nem quantifica o valor incontroverso, em desatenção ao art. 330, § 2º, do CPC, impondo-se seu indeferimento."),
 ],
 defesa=[
  ("DO PACTA SUNT SERVANDA E DA LIBERDADE CONTRATUAL", "{OA} {A} teve prévio e pleno conhecimento das condições do financiamento, inclusive do Custo Efetivo Total (CET), expressamente informado no quadro-resumo da cédula, nos termos da Resolução CMN nº 3.517/2007. Aderiu livremente às condições pactuadas, que devem ser respeitadas."),
  ("DA LEGALIDADE DOS JUROS PACTUADOS", "A estipulação de juros remuneratórios superiores a 12% ao ano, por si só, não indica abusividade (Súmula 382 do STJ). A taxa média divulgada pelo Banco Central é mero referencial, não um teto, devendo ser consideradas as peculiaridades da operação, como o perfil de risco do cliente, o prazo e as garantias oferecidas."),
  ("DA CAPITALIZAÇÃO E DAS TARIFAS", "A capitalização de juros em periodicidade inferior à anual é permitida em contratos celebrados após 31/03/2000, desde que expressamente pactuada (Súmulas 539 e 541 do STJ), bastando que a taxa anual seja superior ao duodécuplo da mensal. A tarifa de cadastro é válida (Súmula 566 do STJ), e a de avaliação do bem foi efetivamente prestada, conforme laudo de vistoria anexo (Tema 958 do STJ)."),
  ("DO SEGURO PRESTAMISTA", "O seguro foi contratado em instrumento apartado, com termo de adesão específico assinado {pA} {A}, que optou pela cobertura em seu próprio benefício, inexistindo venda casada."),
 ],
 fund_proc=[
  "A relação entre as partes submete-se ao Código de Defesa do Consumidor (Súmula 297 do STJ), o que autoriza a revisão de cláusulas que estabeleçam prestações desproporcionais, ainda que pactuadas.",
  "Quanto aos juros remuneratórios, consoante o entendimento firmado no REsp 1.061.530/RS, sua revisão é admitida em situações excepcionais, quando caracterizada a relação de consumo e demonstrada a abusividade. A perícia contábil apurou que a taxa contratada de {taxa}% ao mês supera em muito a média de mercado para a modalidade ({media}% ao mês), discrepância que, à míngua de justificativa concreta, revela-se abusiva. A taxa deve ser limitada à média.",
  "A capitalização mensal é lícita, pois expressamente pactuada (Súmula 541 do STJ). Do mesmo modo, válida a tarifa de cadastro (Súmula 566 do STJ).",
  "No tocante ao seguro prestamista, não houve oportunidade de escolha da seguradora, que integra o mesmo grupo econômico da instituição, configurando-se a venda casada reconhecida no Tema 972 do STJ.",
 ],
 fund_improc=[
  "A taxa contratada, de {taxa}% ao mês, embora superior à média de mercado divulgada pelo Banco Central, não discrepa dela em proporção que permita reputá-la abusiva, consideradas as peculiaridades da operação e o perfil de risco do contratante. A média é referencial, não limite.",
  "A capitalização mensal foi expressamente pactuada, sendo a taxa anual superior ao duodécuplo da mensal (Súmulas 539 e 541 do STJ). A tarifa de cadastro é válida (Súmula 566 do STJ), e a de avaliação do bem foi comprovadamente prestada.",
  "O seguro prestamista foi contratado em termo apartado e com possibilidade de recusa, não havendo prova de imposição. Ausente abusividade, prevalece o pactuado.",
 ],
 disp_proc="a) LIMITAR os juros remuneratórios da Cédula de Crédito Bancário nº {contrato} à taxa média de mercado de {media}% ao mês, com recálculo das parcelas; b) DECLARAR a nulidade da contratação do seguro prestamista, condenando {oR} {R} à restituição simples do valor de {seguro}; c) DETERMINAR a compensação dos valores pagos a maior com o saldo devedor, restituindo-se eventual excedente, com correção monetária desde cada pagamento e juros de mora desde a citação, a serem apurados em liquidação de sentença.",
 ementa="APELAÇÃO. AÇÃO REVISIONAL. CÉDULA DE CRÉDITO BANCÁRIO. FINANCIAMENTO DE VEÍCULO. Juros remuneratórios. Abusividade verificada em comparação com a taxa média de mercado (REsp 1.061.530/RS). Capitalização mensal expressamente pactuada. Súmula 541 do STJ. Seguro prestamista. Venda casada. Tema 972 do STJ",
 pericia="contabil",
)

A["tarifas"] = dict(
 acao="AÇÃO DE REPETIÇÃO DE INDÉBITO C/C INDENIZAÇÃO POR DANOS MORAIS",
 cnj="Tarifas Bancárias - Cesta de serviços",
 fatos=[
  "{OA} {A} é titular de conta {nA_conta} junto {aoR} {R}, aberta exclusivamente para o recebimento de seus vencimentos.",
  "Ao analisar os extratos, verificou a cobrança mensal de tarifa denominada \"{cesta}\", no valor atual de {tarifa}, por pacote de serviços que jamais solicitou ou utilizou, uma vez que realiza apenas o saque de seus proventos e poucas transferências mensais, todas abrangidas pelos serviços essenciais gratuitos.",
  "Os descontos perduram há aproximadamente {meses} meses e já somam {debito}, conforme planilha anexa. Questionado administrativamente (protocolo nº {protocolo}), {oR} {R} recusou-se a cancelar a cobrança e a devolver os valores.",
 ],
 direito=[
  ("DA ILEGALIDADE DA COBRANÇA", "A Resolução CMN nº 3.919/2010 veda a cobrança de tarifas pela prestação de serviços essenciais a pessoas naturais, assim como a cobrança de pacotes de serviços sem prévia e expressa contratação pelo cliente. A cobrança de tarifa não pactuada configura prática abusiva (art. 39, III, do CDC)."),
  ("DA REPETIÇÃO EM DOBRO", "Comprovada a cobrança indevida, impõe-se a restituição em dobro dos valores pagos, nos termos do art. 42, parágrafo único, do CDC e do entendimento firmado no EAREsp 676.608/RS."),
  ("DOS DANOS MORAIS", "A retenção indevida de parcela de verba salarial, com recusa reiterada de solução administrativa, impõe ao consumidor perda de tempo útil e desgaste que ultrapassam o mero dissabor, sendo devida indenização de {dano_pedido}."),
 ],
 tutela=None,
 pedidos=[
  "a declaração de inexigibilidade da tarifa \"{cesta}\", com a determinação de cessação imediata da cobrança;",
  "a condenação {dR} {R} à restituição em dobro dos valores cobrados, que totalizam {dobro}, além das parcelas vencidas no curso da demanda;",
  "a condenação {dR} {R} ao pagamento de indenização por danos morais de {dano_pedido};",
 ],
 preliminares=[],
 defesa=[
  ("DA CONTRATAÇÃO DO PACOTE DE SERVIÇOS", "No ato de abertura da conta, {oA} {A} aderiu expressamente ao pacote \"{cesta}\", conforme termo de adesão e proposta de abertura de conta assinados, ora juntados. Foi informad{sA} da possibilidade de optar pelos serviços essenciais gratuitos e escolheu o pacote por ser mais vantajoso ao seu perfil."),
  ("DA LEGALIDADE DA TARIFA", "A cobrança de pacotes de serviços é autorizada pela Resolução CMN nº 3.919/2010, desde que contratada, o que se verifica no caso. A conta não é do tipo conta-salário, modalidade regida pela Resolução CMN nº 3.402/2006."),
  ("DA AUSÊNCIA DE DANO MORAL", "A cobrança de tarifa, ainda que eventualmente indevida, não é apta a gerar dano moral, configurando, no máximo, mero aborrecimento."),
 ],
 fund_proc=[
  "Cabia à instituição financeira demonstrar a contratação do pacote de serviços, ônus do qual não se desincumbiu, pois o termo juntado não contém assinatura {dA} {A} nem indicação do pacote escolhido. Ausente prova da contratação, a cobrança é indevida, impondo-se a restituição em dobro dos valores descontados, observada a prescrição quinquenal.",
  "Os danos morais, por outro lado, não se presumem na hipótese de mera cobrança indevida de tarifa, sem negativação ou outro reflexo. Contudo, a recusa reiterada de solução administrativa, com descontos que se prolongaram por anos sobre verba salarial, justifica a reparação, que fixo em {dano_fix}.",
 ],
 fund_improc=[
  "A instituição juntou o termo de adesão ao pacote \"{cesta}\", devidamente assinado {pA} {A}, com indicação expressa do valor da tarifa e da faculdade de opção pelos serviços essenciais gratuitos. A assinatura não foi impugnada especificamente.",
  "Demonstrada a contratação, a cobrança encontra respaldo na Resolução CMN nº 3.919/2010, inexistindo ilícito a justificar repetição ou indenização. Nada impede, contudo, que {oA} {A} solicite administrativamente a migração para os serviços essenciais.",
 ],
 disp_proc="a) DECLARAR a inexigibilidade da tarifa \"{cesta}\" e determinar a cessação dos descontos; b) CONDENAR {oR} {R} à restituição, em dobro, dos valores descontados, observada a prescrição quinquenal, com correção monetária desde cada desconto e juros de mora desde a citação; c) CONDENAR {oR} {R} ao pagamento de indenização por danos morais de {dano_fix}.",
 ementa="RECURSO INOMINADO. CONSUMIDOR. TARIFA BANCÁRIA. CESTA DE SERVIÇOS. Ausência de prova da contratação. Cobrança indevida. Resolução CMN nº 3.919/2010. Repetição do indébito em dobro",
 pericia=None,
)

A["horas_extras"] = dict(
 acao="RECLAMAÇÃO TRABALHISTA",
 cnj="Horas Extras - Bancário - Cargo de Confiança",
 fatos=[
  "{OA} {A} foi admitid{sA} pela Reclamada em {admissao}, para exercer a função de escriturário, sendo posteriormente promovid{sA} ao cargo de {cargo}, função que exerceu até a dispensa sem justa causa, ocorrida em {dispensa}, com última remuneração de {salario}.",
  "Embora formalmente enquadrad{sA} na hipótese do art. 224, § 2º, da CLT, com jornada contratual de oito horas, {oA} {A} jamais exerceu atribuições de efetiva fidúcia: não possuía subordinados, não detinha alçada para aprovação de crédito, não tinha procuração para representar o banco e suas atividades eram integralmente controladas por sistemas e pela gerência geral da agência {agencia}.",
  "Sua rotina consistia no atendimento de clientes da carteira, na venda de produtos (seguros, consórcios, capitalização e cartões) e no cumprimento de metas comerciais diárias, sob intensa cobrança. Laborava, em média, das {ji} às {jf}, de segunda a sexta-feira, com intervalo intrajornada de apenas 30 minutos, sendo que o registro de ponto era orientado a não refletir a jornada efetivamente cumprida.",
  "Além disso, nas reuniões diárias e no grupo de mensagens da agência, o desempenho individual era exposto em ranking, com advertências públicas àqueles que não atingiam as metas, situação que lhe causou intenso desgaste emocional.",
 ],
 direito=[
  ("DO ENQUADRAMENTO NO CAPUT DO ART. 224 DA CLT – 7ª E 8ª HORAS", "A configuração do cargo de confiança bancário depende da prova das reais atribuições do empregado, não bastando o pagamento de gratificação de função igual ou superior a um terço do salário (Súmula 102, I, do TST). Ausente a fidúcia especial, {oA} {A} faz jus à jornada de seis horas, sendo devidas como extras a 7ª e a 8ª horas diárias, bem como as excedentes, com adicional convencional de 50% e divisor 180, além dos reflexos em DSR (inclusive sábados e feriados, conforme norma coletiva), férias acrescidas de 1/3, 13º salários, aviso prévio e FGTS com indenização de 40%."),
  ("DO INTERVALO INTRAJORNADA", "A supressão parcial do intervalo intrajornada impõe o pagamento do período suprimido, com acréscimo de 50% sobre o valor da remuneração da hora normal, nos termos do art. 71, § 4º, da CLT."),
  ("DO DANO MORAL – COBRANÇA ABUSIVA DE METAS", "A exposição do desempenho individual em rankings públicos e as cobranças com ameaças veladas de dispensa extrapolam o poder diretivo do empregador e configuram assédio moral organizacional, atraindo o dever de indenizar (arts. 223-B e seguintes da CLT e art. 5º, X, da Constituição Federal)."),
 ],
 tutela=None,
 pedidos=[
  "pagamento de horas extras excedentes da 6ª diária, com adicional de 50% e divisor 180, e reflexos em DSR, férias + 1/3, 13º salários, aviso prévio e FGTS + 40% — estimativa: {hx1};",
  "pagamento do intervalo intrajornada suprimido, com adicional de 50% — estimativa: {hx2};",
  "indenização por danos morais decorrentes de assédio moral organizacional — {dano_pedido};",
  "honorários advocatícios de sucumbência de 15% sobre o valor líquido da condenação (art. 791-A da CLT);",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA PRESCRIÇÃO QUINQUENAL", "Requer a Reclamada a declaração da prescrição das pretensões anteriores aos cinco anos que antecedem o ajuizamento da ação, nos termos do art. 7º, XXIX, da Constituição Federal e da Súmula 308, I, do TST."),
 ],
 defesa=[
  ("DO EXERCÍCIO DE CARGO DE CONFIANÇA", "{OA} {A} exercia o cargo de {cargo}, percebendo gratificação de função superior a 1/3 do salário do cargo efetivo, e detinha atribuições diferenciadas: geria carteira própria de clientes de alta renda, tinha acesso a informações sigilosas, participava do comitê de crédito da agência e possuía alçada para concessão de limites. Enquadra-se, portanto, na exceção do art. 224, § 2º, da CLT, sendo indevidas as 7ª e 8ª horas."),
  ("DA VALIDADE DOS CONTROLES DE PONTO", "A jornada era integralmente registrada em sistema eletrônico, com possibilidade de marcação livre, inclusive de horas extras, que, quando prestadas, foram pagas ou compensadas, conforme demonstrativos anexos. Os cartões de ponto possuem presunção de veracidade, cabendo {aoA} {A} o ônus de desconstituí-los (art. 818, I, da CLT)."),
  ("DA COMPENSAÇÃO DA GRATIFICAÇÃO DE FUNÇÃO", "Caso afastado o enquadramento no § 2º do art. 224 da CLT, deve ser determinada a compensação do valor das horas extras com a gratificação de função percebida, nos termos da cláusula 11ª da Convenção Coletiva de Trabalho dos bancários."),
  ("DA INEXISTÊNCIA DE ASSÉDIO MORAL", "O estabelecimento de metas é inerente à atividade comercial e decorre do legítimo poder diretivo do empregador. Não houve exposição vexatória ou tratamento desrespeitoso, sendo os resultados divulgados de forma institucional, sem qualquer caráter humilhante."),
 ],
 fund_proc=[
  "A prova oral produzida revelou que {oA} {A} não possuía subordinados, não detinha alçada para aprovação de operações sem a chancela do gerente geral e que suas atividades eram eminentemente comerciais. A testemunha ouvida a rogo {dA} {A} confirmou que as propostas de crédito eram aprovadas pelo sistema ou pela gerência regional, e o próprio preposto admitiu desconhecer se {oA} {A} tinha procuração.",
  "Nos termos da Súmula 102, I, do TST, a configuração do cargo de confiança depende da prova das reais atribuições, ônus da Reclamada (art. 818, II, da CLT), do qual não se desincumbiu. Afasto, pois, o enquadramento no § 2º do art. 224 da CLT e defiro as 7ª e 8ª horas como extras, com adicional de 50%, divisor 180 e reflexos, observada a evolução salarial. Indevida a compensação da gratificação de função, por se tratar de cargo técnico (Súmula 109 do TST), ressalvada a aplicação da cláusula convencional nos limites do Tema 1.046 do STF.",
  "Quanto à jornada, a testemunha confirmou a prestação de labor em horário superior ao registrado e a orientação para que o ponto fosse encerrado antes da saída efetiva, o que afasta a presunção de veracidade dos controles. Fixo a jornada das {ji} às {jf}, com 30 minutos de intervalo.",
  "A exposição de rankings individuais com advertências públicas restou comprovada pela prova oral e pelas mensagens juntadas, configurando abuso do poder diretivo. Defiro indenização por danos morais de {dano_fix}, considerando os parâmetros do art. 223-G da CLT.",
 ],
 fund_improc=[
  "A prova oral confirmou que {oA} {A} geria carteira de clientes de alta renda, participava do comitê de crédito e possuía alçada própria para concessão de limites, além de coordenar dois assistentes. Tais atribuições evidenciam fidúcia diferenciada, compatível com o art. 224, § 2º, da CLT, sendo regular a jornada de oito horas.",
  "Os controles de ponto apresentam horários variáveis e registro de horas extras, que foram pagas conforme demonstrativos, e {oA} {A} não apontou diferenças, nem produziu prova capaz de infirmá-los.",
  "Quanto ao alegado assédio, a testemunha não confirmou a exposição vexatória, limitando-se a relatar a existência de metas e reuniões de acompanhamento, inerentes à atividade bancária. Improcedente o pedido.",
 ],
 disp_proc="a) horas extras excedentes da 6ª diária, com adicional de 50%, divisor 180 e reflexos em DSR (sábados e feriados), férias + 1/3, 13º salários, aviso prévio e FGTS + 40%; b) uma hora diária pela supressão parcial do intervalo intrajornada, com adicional de 50%, de natureza indenizatória (art. 71, § 4º, da CLT); c) indenização por danos morais de {dano_fix}.",
 ementa="RECURSO ORDINÁRIO. BANCÁRIO. CARGO DE CONFIANÇA. ART. 224, § 2º, DA CLT. NÃO CONFIGURAÇÃO. Ausência de prova de fidúcia especial. Súmula 102, I, do TST. Horas extras excedentes da sexta diária devidas. Cobrança abusiva de metas. Dano moral configurado",
 pericia="contabil_trab",
)

A["equiparacao"] = dict(
 acao="RECLAMAÇÃO TRABALHISTA",
 cnj="Salário / Diferença Salarial - Equiparação Salarial",
 fatos=[
  "{OA} {A} foi admitid{sA} pela Reclamada em {admissao} e dispensad{sA} sem justa causa em {dispensa}, tendo exercido por último a função de {cargo} na agência {agencia}, com salário de {salario}.",
  "Durante todo o período imprescrito, {oA} {A} desempenhou funções idênticas às do colega {paradigma}, lotado na mesma agência, com igual produtividade e perfeição técnica, ambos atendendo carteiras de clientes do mesmo segmento e respondendo ao mesmo gestor.",
  "Não obstante, o paradigma percebia salário superior em aproximadamente {dif_sal}, sem que houvesse diferença de tempo na função superior a dois anos ou de tempo de serviço para o empregador superior a quatro anos, tampouco quadro de carreira homologado.",
  "Além disso, a Reclamada deixou de pagar corretamente a Participação nos Lucros e Resultados (PLR) proporcional do ano da dispensa, prevista na Convenção Coletiva de Trabalho da categoria.",
 ],
 direito=[
  ("DA EQUIPARAÇÃO SALARIAL", "Nos termos do art. 461 da CLT, sendo idêntica a função, a todo trabalho de igual valor, prestado ao mesmo empregador, no mesmo estabelecimento empresarial, corresponderá igual salário. Presentes os requisitos legais e ausente fato impeditivo, cujo ônus é da Reclamada (Súmula 6, VIII, do TST), são devidas as diferenças salariais e reflexos."),
  ("DA PLR PROPORCIONAL", "A Súmula 451 do TST assegura ao empregado dispensado antes da data de distribuição dos lucros o pagamento proporcional da PLR, em respeito ao princípio da isonomia, sendo nula cláusula que condicione o pagamento à vigência do contrato na data da distribuição."),
 ],
 tutela=None,
 pedidos=[
  "diferenças salariais decorrentes da equiparação com o paradigma {paradigma}, parcelas vencidas e vincendas até a dispensa, com reflexos em férias + 1/3, 13º salários, horas extras pagas, gratificação semestral, aviso prévio e FGTS + 40% — estimativa: {hx1};",
  "PLR proporcional do ano da dispensa, inclusive parcela adicional, nos termos da CCT — estimativa: {hx2};",
  "honorários advocatícios de sucumbência de 15% (art. 791-A da CLT);",
 ],
 preliminares=[
  ("PRELIMINARMENTE – DA INÉPCIA DOS PEDIDOS", "Os pedidos não estão devidamente liquidados, em afronta ao art. 840, § 1º, da CLT, com redação dada pela Lei nº 13.467/2017, impondo-se a extinção sem resolução do mérito."),
 ],
 defesa=[
  ("DA AUSÊNCIA DE IDENTIDADE DE FUNÇÕES", "O paradigma indicado exercia atribuições distintas e mais complexas, atendendo carteira de clientes de segmento superior, com maior volume de negócios e responsabilidade por operações de maior valor. Ademais, possuía tempo na função superior a dois anos em relação {aoA} {A}, fato impeditivo previsto no art. 461, § 1º, da CLT."),
  ("DA DIFERENÇA DE PERFEIÇÃO TÉCNICA E PRODUTIVIDADE", "As avaliações de desempenho anexas demonstram que o paradigma apresentava produtividade superior, com atingimento de metas significativamente maior em todos os semestres do período imprescrito."),
  ("DA PLR", "A PLR proporcional foi paga na forma da CCT, conforme comprovante anexo, inexistindo diferenças a serem deferidas."),
 ],
 fund_proc=[
  "Admitida a identidade de cargos, incumbia à Reclamada a prova de fato impeditivo, modificativo ou extintivo da equiparação (Súmula 6, VIII, do TST). A prova oral, contudo, revelou que {oA} {A} e o paradigma atendiam clientes do mesmo segmento, cumpriam as mesmas metas e substituíam-se mutuamente nas férias, não se confirmando a alegada diferença de complexidade.",
  "A diferença de tempo na função entre ambos é inferior a dois anos, conforme fichas de registro juntadas, não havendo quadro de carreira homologado. Defiro as diferenças salariais e reflexos.",
  "Quanto à PLR, o comprovante juntado refere-se apenas à parcela regra básica, não abrangendo a parcela adicional prevista na CCT. Defiro a diferença, nos termos da Súmula 451 do TST.",
 ],
 fund_improc=[
  "A prova testemunhal demonstrou que o paradigma atendia carteira de clientes de segmento superior, com operações de maior complexidade, e possuía tempo na função superior a dois anos em relação {aoA} {A}, fatos impeditivos que afastam a equiparação, nos termos do art. 461, § 1º, da CLT.",
  "A PLR proporcional foi quitada conforme a norma coletiva, não tendo {oA} {A} apontado diferenças em réplica. Improcedentes os pedidos.",
 ],
 disp_proc="a) diferenças salariais decorrentes da equiparação com o paradigma {paradigma}, com reflexos em férias + 1/3, 13º salários, gratificações semestrais, aviso prévio e FGTS + 40%; b) diferenças de PLR proporcional do ano da dispensa, nos termos da CCT.",
 ementa="RECURSO ORDINÁRIO. EQUIPARAÇÃO SALARIAL. Identidade de funções demonstrada. Fato impeditivo não comprovado pela reclamada. Súmula 6, VIII, do TST. PLR proporcional. Súmula 451 do TST",
 pericia="contabil_trab",
)

# Jurisprudência ilustrativa (números fictícios)
def jurisp(c, x):
    from casos import cnj as _cnj, nome as _nome
    trab = c.justica == "trab"
    ano = rng.randint(2021, 2025)
    if trab:
        num = _cnj(ano, "5", rng.choice(["02", "15", "03", "09"]), f"{rng.randint(1,99):04d}")
        orgao = f"{rng.randint(1,11)}ª Turma"; tipo = "ROT"
        tri = rng.choice(["TRT da 2ª Região", "TRT da 15ª Região", "TRT da 3ª Região"])
    else:
        num = _cnj(ano, "8", "26", f"{rng.randint(1,700):04d}")
        orgao = c.camara if hasattr(c, "camara") else "Turma Recursal Cível"; tipo = "Apelação Cível"
        tri = c.sigla
    em = A[c.assunto]["ementa"].format(**x)
    return (f"\"{em}. Sentença mantida. Recurso desprovido.\" ({tri}; {tipo} {num}; Relator(a): {_nome()[0]}; "
            f"Órgão Julgador: {orgao}; Data do Julgamento: {dfmt(dt.date(ano, rng.randint(1,12), rng.randint(1,28)))})")
