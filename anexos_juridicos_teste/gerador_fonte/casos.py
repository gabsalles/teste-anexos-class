# -*- coding: utf-8 -*-
"""Geração de casos fictícios (partes, juízo, números CNJ, datas, valores)."""
import random, datetime as dt

rng = random.Random(20261016)
def ch(x): return rng.choice(x)

MESES = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto",
         "setembro","outubro","novembro","dezembro"]

NOMES_M = ["José","João","Antônio","Francisco","Carlos","Paulo","Pedro","Lucas","Luiz","Marcos",
  "Luís","Gabriel","Rafael","Daniel","Marcelo","Bruno","Eduardo","Felipe","Raimundo","Rodrigo",
  "Sebastião","Benedito","Geraldo","Valdir","Reginaldo","Anderson","Thiago","Leandro","Vinícius","Gustavo",
  "Otávio","Wellington","Edson","Rogério","Cláudio","Joaquim","Renato","Fábio","Matheus","Alexandre"]
NOMES_F = ["Maria","Ana","Francisca","Antônia","Adriana","Juliana","Márcia","Fernanda","Patrícia","Aline",
  "Sandra","Camila","Amanda","Bruna","Jéssica","Letícia","Júlia","Luciana","Vanessa","Mariana",
  "Aparecida","Benedita","Rosângela","Cleusa","Simone","Tatiane","Priscila","Débora","Renata","Cristiane",
  "Larissa","Elaine","Viviane","Isabela","Natália","Raquel","Sueli","Heloísa","Carolina","Gabriela"]
SOBRENOMES = ["Silva","Santos","Oliveira","Souza","Rodrigues","Ferreira","Alves","Pereira","Lima","Gomes",
  "Costa","Ribeiro","Martins","Carvalho","Almeida","Lopes","Soares","Fernandes","Vieira","Barbosa",
  "Rocha","Dias","Nascimento","Andrade","Moreira","Nunes","Marques","Machado","Mendes","Freitas",
  "Cardoso","Ramos","Gonçalves","Santana","Teixeira","Moraes","Bueno","Prado","Siqueira","Toledo",
  "Monteiro","Franco","Arantes","Guimarães","Cunha","Pires","Camargo","Brandão","Rezende","Leme"]
PROFISSOES_M = ["aposentado","motorista","pedreiro","comerciante","auxiliar administrativo","eletricista",
  "professor","vendedor","técnico em enfermagem","mecânico","autônomo","servidor público municipal",
  "agricultor","operador de máquinas","analista de sistemas"]
PROFISSOES_F = ["aposentada","professora","do lar","auxiliar de enfermagem","comerciante","vendedora",
  "cabeleireira","costureira","auxiliar administrativa","servidora pública estadual","diarista",
  "recepcionista","pensionista","confeiteira","assistente social"]
RUAS = ["Rua Coronel Marcondes","Rua Dr. Gama Rodrigues","Avenida Nossa Senhora do Bom Sucesso",
  "Rua Benedito Fernandes","Rua Sete de Setembro","Rua Treze de Maio","Avenida Independência",
  "Rua das Palmeiras","Rua José Bonifácio","Rua Santa Cruz","Avenida Brasil","Rua Quinze de Novembro",
  "Rua Tiradentes","Rua Expedicionário Ernesto Pereira","Rua dos Ipês","Rua Padre Anchieta",
  "Avenida Getúlio Vargas","Rua Dom Pedro II","Rua Bahia","Rua Paraná","Rua Minas Gerais",
  "Travessa São Benedito","Rua Floriano Peixoto","Rua Rui Barbosa","Rua Major José dos Santos Moreira"]
BAIRROS = ["Centro","Vila São Benedito","Jardim Santa Cecília","Parque São Domingos","Vila Rica",
  "Jardim das Flores","Bela Vista","Santa Luzia","Jardim Primavera","Vila Nova","Boa Vista",
  "Jardim América","Cidade Nova","Parque Industrial","Vila Esperança","Alto do Cardoso"]

# Instituições fictícias
BANCOS = [
  ("BANCO MERIDIONAL S.A.", "Avenida Brigadeiro Faria Lima, nº 3.900, 11º andar, Itaim Bibi, São Paulo/SP, CEP 04538-132"),
  ("BANCO ATLÂNTIDA S.A.", "Avenida Paulista, nº 2.064, 14º andar, Bela Vista, São Paulo/SP, CEP 01310-928"),
  ("BANCO HORIZONTE DO BRASIL S.A.", "Rua Boa Vista, nº 254, 9º andar, Centro, São Paulo/SP, CEP 01014-907"),
  ("BANCO CORDILHEIRA S.A.", "Avenida do Contorno, nº 7.962, Lourdes, Belo Horizonte/MG, CEP 30110-056"),
  ("BANCO VALE DO PARAÍBA S.A.", "Avenida São João, nº 1.215, Jardim Esplanada, São José dos Campos/SP, CEP 12242-000"),
]
OUTRAS_RES = [
  ("PAINEIRA S.A. CRÉDITO, FINANCIAMENTO E INVESTIMENTO", "Alameda Santos, nº 1.800, 6º andar, Cerqueira César, São Paulo/SP, CEP 01418-102", "f"),
  ("AURORA SEGUROS S.A.", "Rua Funchal, nº 418, 20º andar, Vila Olímpia, São Paulo/SP, CEP 04551-060", "f"),
  ("NOVAPAG INSTITUIÇÃO DE PAGAMENTO S.A.", "Rua Fidêncio Ramos, nº 308, Vila Olímpia, São Paulo/SP, CEP 04551-010", "f"),
]
ESCRITORIOS = ["Moraes Franco Advogados Associados","Siqueira & Leme Sociedade de Advogados",
  "Prado, Arantes e Cunha Advogados","Toledo Bueno Advocacia","Rezende Camargo Advogados",
  "Andrade & Brandão Advocacia Consumerista","Guimarães Pires Sociedade de Advogados",
  "Escritório de Advocacia Monteiro Ramos","Machado & Freitas Advogados Associados"]
ESCRIT_BANCO = ["Albuquerque Pinheiro & Lacerda Advogados","Queiroz Vasconcelos Sociedade de Advogados",
  "Barros, Tavares e Dantas Advogados","Coimbra Werneck Advogados Associados"]

ESTADUAL = {
 "SP": dict(trib="TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO", sigla="TJSP", tr="26", sistema="esaj",
     comarcas=["São Paulo","Campinas","Taubaté","São José dos Campos","Pindamonhangaba","Ribeirão Preto",
               "Sorocaba","Santos","Guarulhos","Jundiaí","Bauru","Campos do Jordão","Guaratinguetá","Jacareí"],
     camaras=["11ª Câmara de Direito Privado","12ª Câmara de Direito Privado","13ª Câmara de Direito Privado",
              "14ª Câmara de Direito Privado","17ª Câmara de Direito Privado","22ª Câmara de Direito Privado",
              "23ª Câmara de Direito Privado","24ª Câmara de Direito Privado","37ª Câmara de Direito Privado",
              "38ª Câmara de Direito Privado"]),
 "MG": dict(trib="TRIBUNAL DE JUSTIÇA DO ESTADO DE MINAS GERAIS", sigla="TJMG", tr="13", sistema="pje",
     comarcas=["Belo Horizonte","Pouso Alegre","Itajubá","Juiz de Fora","Uberlândia","Varginha",
               "Poços de Caldas","Lavras","Três Corações"],
     camaras=["9ª Câmara Cível","11ª Câmara Cível","12ª Câmara Cível","13ª Câmara Cível","14ª Câmara Cível",
              "15ª Câmara Cível","16ª Câmara Cível","17ª Câmara Cível","18ª Câmara Cível","20ª Câmara Cível"]),
 "RJ": dict(trib="TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO", sigla="TJRJ", tr="19", sistema="pje",
     comarcas=["Rio de Janeiro","Niterói","Petrópolis","Volta Redonda","Nova Iguaçu","Resende"],
     camaras=["3ª Câmara de Direito Privado","5ª Câmara de Direito Privado","7ª Câmara de Direito Privado",
              "10ª Câmara de Direito Privado","19ª Câmara de Direito Privado"]),
 "PR": dict(trib="TRIBUNAL DE JUSTIÇA DO ESTADO DO PARANÁ", sigla="TJPR", tr="16", sistema="projudi",
     comarcas=["Curitiba","Londrina","Maringá","Ponta Grossa","Cascavel","Foz do Iguaçu"],
     camaras=["13ª Câmara Cível","14ª Câmara Cível","15ª Câmara Cível","16ª Câmara Cível"]),
}
TRABALHO = {
 "02": dict(trib="TRIBUNAL REGIONAL DO TRABALHO DA 2ª REGIÃO", sigla="TRT2", uf="SP",
            cidades=["São Paulo","Guarulhos","Osasco","Santo André","São Bernardo do Campo"]),
 "15": dict(trib="TRIBUNAL REGIONAL DO TRABALHO DA 15ª REGIÃO", sigla="TRT15", uf="SP",
            cidades=["Campinas","Taubaté","São José dos Campos","Ribeirão Preto","Sorocaba","Pindamonhangaba","Jundiaí"]),
 "03": dict(trib="TRIBUNAL REGIONAL DO TRABALHO DA 3ª REGIÃO", sigla="TRT3", uf="MG",
            cidades=["Belo Horizonte","Pouso Alegre","Juiz de Fora","Uberlândia","Varginha"]),
 "01": dict(trib="TRIBUNAL REGIONAL DO TRABALHO DA 1ª REGIÃO", sigla="TRT1", uf="RJ",
            cidades=["Rio de Janeiro","Niterói","Duque de Caxias"]),
 "09": dict(trib="TRIBUNAL REGIONAL DO TRABALHO DA 9ª REGIÃO", sigla="TRT9", uf="PR",
            cidades=["Curitiba","Londrina","Maringá"]),
}

ASSUNTOS_CIVEL = ["negativacao","fraude_pix","consignado","revisional","tarifas"]
ASSUNTOS_JEC = ["negativacao","fraude_pix","consignado","tarifas"]
ASSUNTOS_TRAB = ["horas_extras","equiparacao"]

# ---------------------------------------------------------------- utilidades
def money(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s

_U = ["","um","dois","três","quatro","cinco","seis","sete","oito","nove","dez","onze","doze","treze",
      "quatorze","quinze","dezesseis","dezessete","dezoito","dezenove"]
_D = ["","","vinte","trinta","quarenta","cinquenta","sessenta","setenta","oitenta","noventa"]
_C = ["","cento","duzentos","trezentos","quatrocentos","quinhentos","seiscentos","setecentos","oitocentos","novecentos"]
def _ate999(n):
    if n == 0: return ""
    if n == 100: return "cem"
    c, r = divmod(n, 100); parts = []
    if c: parts.append(_C[c])
    if r:
        if r < 20: parts.append(_U[r])
        else:
            d, u = divmod(r, 10); parts.append(_D[d] + (" e " + _U[u] if u else ""))
    return " e ".join(parts)
def extenso(v):
    reais = int(v); cent = int(round((v - reais) * 100))
    mi, resto = divmod(reais, 1_000_000); mil, uni = divmod(resto, 1000); parts = []
    if mi: parts.append(_ate999(mi) + (" milhão" if mi == 1 else " milhões"))
    if mil: parts.append("mil" if mil == 1 else _ate999(mil) + " mil")
    if uni: parts.append(_ate999(uni))
    txt = (", ".join(parts[:-1]) + " e " + parts[-1]) if len(parts) > 1 else (parts[0] if parts else "zero")
    if mi and not mil and not uni: txt += " de"
    txt += " real" if reais == 1 else " reais"
    if cent: txt += " e " + _ate999(cent) + (" centavo" if cent == 1 else " centavos")
    return txt

def dfmt(d): return d.strftime("%d/%m/%Y")
def dext(d): return f"{d.day} de {MESES[d.month-1]} de {d.year}"
def rand_date(a, b):
    return a + dt.timedelta(days=rng.randint(0, max(0, (b - a).days)))
LIMITE = dt.date(2026, 10, 9)
def bizday(d, add):
    d = d + dt.timedelta(days=add)
    if d > LIMITE: d = LIMITE - dt.timedelta(days=rng.randint(0, 75))
    while d.weekday() >= 5: d += dt.timedelta(days=1)
    return d
def hora(): return f"{rng.randint(8,19):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}"

def cpf():
    n = [rng.randint(0, 9) for _ in range(9)]
    for k in (10, 11):
        s = sum(a*b for a, b in zip(n, range(k, 1, -1))); d = (s*10) % 11; n.append(0 if d == 10 else d)
    s = "".join(map(str, n)); return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"
def cnpj():
    n = [rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    for w in ([5,4,3,2,9,8,7,6,5,4,3,2], [6,5,4,3,2,9,8,7,6,5,4,3,2]):
        s = sum(a*b for a, b in zip(n, w)); d = s % 11; n.append(0 if d < 2 else 11 - d)
    s = "".join(map(str, n)); return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"
def rg(): return f"{rng.randint(10,59)}.{rng.randint(100,999)}.{rng.randint(100,999)}-{rng.choice('0123456789X')}"
def cep(): return f"{rng.randint(11000,39999)}-{rng.randint(0,999):03d}"

def cnj(ano, j, tr, orig):
    seq = f"{rng.randint(1, 9999999):07d}"
    base = int(seq + str(ano) + j + tr + orig + "00")
    dd = 98 - (base % 97)
    return f"{seq}-{dd:02d}.{ano}.{j}.{tr}.{orig}"

def nome(gen=None):
    gen = gen or ch("mf")
    n = ch(NOMES_M if gen == "m" else NOMES_F)
    if rng.random() < .45: n += " " + ch(NOMES_M if gen == "m" else NOMES_F)
    sob = rng.sample(SOBRENOMES, rng.choice([2, 2, 3]))
    PART = {"Santos": "dos", "Silva": "da", "Costa": "da", "Rocha": "da", "Cunha": "da", "Oliveira": "de", "Souza": "de",
            "Almeida": "de", "Andrade": "de", "Freitas": "de", "Moraes": "de", "Carvalho": "de", "Toledo": "de", "Camargo": "de", "Nascimento": "do", "Prado": "do"}
    if rng.random() < .35 and sob[-1] in PART: sob.insert(-1, PART[sob[-1]])
    return n + " " + " ".join(sob), gen

def ordinal(n): return f"{n}ª"

class Pessoa:
    def __init__(self, cidade, uf, idoso=False):
        self.nome, self.g = nome()
        m = self.g == "m"
        self.cpf, self.rg = cpf(), rg()
        if idoso: self.prof = "aposentado" if m else "aposentada"
        else: self.prof = ch(PROFISSOES_M if m else PROFISSOES_F)
        self.civil = ch(["casado","solteiro","divorciado","viúvo","convivente em união estável"])
        if not m: self.civil = self.civil.replace("casado","casada").replace("solteiro","solteira").replace("divorciado","divorciada").replace("viúvo","viúva")
        self.end = f"{ch(RUAS)}, nº {rng.randint(12, 2400)}, {ch(BAIRROS)}, {cidade}/{uf}, CEP {cep()}"
        self.email = (self.nome.split()[0] + "." + self.nome.split()[-1]).lower()
        for a, b in zip("áàâãéêíóôõúç", "aaaaeeiooouc"): self.email = self.email.replace(a, b)
        self.email += rng.choice(["@gmail.com", "@hotmail.com", "@outlook.com", "@yahoo.com.br"])
    def o(self): return "o" if self.g == "m" else "a"
    def qualif(self):
        o = self.o()
        return (f"{self.nome.upper()}, brasileir{o}, {self.civil}, {self.prof}, portador{'' if o=='o' else 'a'} da cédula de "
                f"identidade RG nº {self.rg} e inscrit{o} no CPF/MF sob o nº {self.cpf}, endereço eletrônico {self.email}, "
                f"residente e domiciliad{o} na {self.end}")

class Empresa:
    def __init__(self, nome_, end, g="m"):
        self.nome, self.end, self.g, self.cnpj = nome_, end, g, cnpj()
    def o(self): return self.g == "m" and "o" or "a"
    def qualif(self):
        return (f"{self.nome}, pessoa jurídica de direito privado, inscrita no CNPJ/MF sob o nº {self.cnpj}, "
                f"com sede na {self.end}")

class Advogado:
    def __init__(self, uf, escritorio):
        self.nome, self.g = nome(); self.oab = f"OAB/{uf} nº {rng.randint(98000, 489999):,}".replace(",", ".")
        self.escr = escritorio

class Caso:
    pass

def novo_caso(justica=None):
    c = Caso()
    c.justica = justica or rng.choices(["civel", "jec", "trab"], [5, 3, 2.2])[0]
    hoje = dt.date(2026, 10, 10)
    c.dist = rand_date(dt.date(2021, 6, 1), dt.date(2025, 6, 30))
    if c.justica == "trab":
        reg = ch(list(TRABALHO)); T = TRABALHO[reg]
        c.uf, c.trib, c.sigla, c.sistema = T["uf"], T["trib"], T["sigla"], "pjejt"
        c.cidade = ch(T["cidades"]); n = rng.randint(1, 12 if c.cidade in ("São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Campinas") else 3)
        c.vara = f"{n}ª Vara do Trabalho de {c.cidade}"
        c.numero = cnj(c.dist.year, "5", reg, f"{rng.randint(1,999):04d}")
        c.assunto = ch(ASSUNTOS_TRAB)
        c.classe = "Ação Trabalhista - Rito Ordinário"
        c.turma = f"{rng.randint(1, 11)}ª Turma"
    else:
        uf = rng.choices(list(ESTADUAL), [6, 2.5, 1.2, 1.2])[0]; E = ESTADUAL[uf]
        c.uf, c.trib, c.sigla, c.sistema = uf, E["trib"], E["sigla"], E["sistema"]
        c.cidade = ch(E["comarcas"])
        if c.justica == "jec":
            c.vara = ch([f"Juizado Especial Cível da Comarca de {c.cidade}", f"{rng.randint(1,3)}ª Vara do Juizado Especial Cível da Comarca de {c.cidade}"])
            c.classe = "Procedimento do Juizado Especial Cível"; c.assunto = ch(ASSUNTOS_JEC)
            c.turma = f"{rng.randint(1,6)}ª Turma Recursal Cível"
        else:
            nv = rng.randint(1, 9 if c.cidade in ("São Paulo","Belo Horizonte","Rio de Janeiro","Curitiba","Campinas") else 4)
            c.vara = f"{nv}ª Vara Cível da Comarca de {c.cidade}"
            if c.cidade == "São Paulo": c.vara = f"{nv}ª Vara Cível do Foro Central da Comarca de São Paulo"
            c.classe = "Procedimento Comum Cível"; c.assunto = ch(ASSUNTOS_CIVEL)
            c.camara = ch(E["camaras"])
        c.numero = cnj(c.dist.year, "8", E["tr"], f"{rng.randint(1,700):04d}")
    # partes
    if c.justica == "trab":
        c.autor = Pessoa(c.cidade, c.uf)
        b = ch(BANCOS); c.reu = Empresa(*b)
    else:
        c.autor = Pessoa(c.cidade, c.uf, idoso=(c.assunto == "consignado"))
        if c.assunto in ("negativacao",) and rng.random() < .3:
            o = ch(OUTRAS_RES); c.reu = Empresa(o[0], o[1], o[2])
        else:
            b = ch(BANCOS); c.reu = Empresa(*b)
    c.adv_a = Advogado(c.uf, ch(ESCRITORIOS)); c.adv_r = Advogado(c.uf, ch(ESCRIT_BANCO))
    c.adv_r2 = Advogado(c.uf, c.adv_r.escr)
    jn, jg = nome(); c.juiz, c.juiz_g = jn, jg
    rn, rg_ = nome(); c.relator, c.relator_g = rn, rg_
    c.diretor = nome()[0]; c.oficial = nome()
    c.perito = nome()
    # valores e datas
    c.valor_debito = round(rng.uniform(180, 9800), 2)
    c.dano_moral_pedido = ch([10000, 15000, 20000, 25000, 30000, 40000])
    c.dano_moral_fix = ch([3000, 4000, 5000, 6000, 8000, 10000])
    c.contrato = f"{rng.randint(100000000, 999999999)}"
    c.protocolo = f"{rng.randint(2022,2025)}{rng.randint(10**9, 10**10-1)}"
    c.data_fato = c.dist - dt.timedelta(days=rng.randint(20, 400))
    c.data_contest = bizday(c.dist, rng.randint(40, 120))
    c.data_aud = bizday(c.dist, rng.randint(30, 160))
    c.data_sent = bizday(c.dist, rng.randint(150, 520))
    c.data_acord = bizday(c.data_sent, rng.randint(160, 400))
    c.resultado = rng.choices(["proc", "parc", "improc"], [4, 4, 2])[0]
    c.gratuidade = rng.random() < .7
    c.fls_base = rng.randint(1, 60)
    # específicos
    if c.assunto == "fraude_pix":
        n = rng.randint(2, 6); c.pix = [round(rng.uniform(380, 4999), 2) for _ in range(n)]
        c.valor_debito = round(sum(c.pix), 2)
    if c.assunto == "consignado":
        c.parcela = round(rng.uniform(45, 420), 2); c.n_parc = ch([72, 84, 96])
        c.nb = f"{rng.randint(100,199)}.{rng.randint(100,999)}.{rng.randint(100,999)}-{rng.randint(0,9)}"
        c.valor_debito = round(c.parcela * rng.randint(6, 30), 2)
    if c.assunto == "revisional":
        c.bem = ch(["veículo Volkswagen Gol 1.0, ano 2019", "veículo Fiat Argo Drive 1.0, ano 2021",
                    "veículo Chevrolet Onix LT, ano 2020", "motocicleta Honda CG 160 Fan, ano 2022",
                    "veículo Hyundai HB20 Comfort, ano 2021", "veículo Renault Kwid Zen, ano 2022"])
        c.financiado = round(rng.uniform(22000, 78000), 2); c.n_parc = ch([36, 48, 60])
        c.taxa = round(rng.uniform(2.4, 4.3), 2); c.media = round(rng.uniform(1.35, 2.05), 2)
        i = c.taxa / 100; c.parcela = round(c.financiado * i / (1 - (1 + i) ** -c.n_parc), 2)
        c.valor_debito = c.financiado
    if c.assunto == "tarifas":
        c.tarifa = round(rng.uniform(19.9, 64.9), 2); c.meses = rng.randint(14, 60)
        c.cesta = ch(["Cesta Fácil Plus", "Pacote Essencial Ampliado", "Cesta Exclusiva I", "Pacote Padronizado II", "Cesta Super Mais"])
        c.valor_debito = round(c.tarifa * c.meses, 2)
    if c.justica == "trab":
        m = c.autor.g == "m"
        c.cargo = ch(["Gerente de Relacionamento", "Assistente de Negócios", "Gerente Administrativo",
                      "Supervisor Administrativo", "Gerente de Contas Pessoa Física", "Analista de Crédito"])
        c.admissao = rand_date(dt.date(2009, 1, 1), dt.date(2019, 12, 31))
        c.dispensa = c.dist - dt.timedelta(days=rng.randint(30, 600))
        c.salario = round(rng.uniform(3800, 11800), 2)
        c.paradigma = nome()[0]
        c.agencia = f"{rng.randint(100, 3999)}"
        c.jornada_ini = ch(["08h00", "08h30", "09h00"]); c.jornada_fim = ch(["18h30", "19h00", "19h30", "20h00"])
        c.valor_causa = round(rng.uniform(85000, 420000), 2)
        c.autor.prof = ch(["bancário", "bancário", "economiário"]) if m else ch(["bancária", "bancária"])
    else:
        base = c.valor_debito * (2 if c.assunto in ("consignado", "tarifas") else 1)
        c.valor_causa = round(base + (c.dano_moral_pedido if c.assunto != "revisional" else 0), 2)
        if c.justica == "jec": c.valor_causa = min(c.valor_causa, 40 * 1412)
    return c
