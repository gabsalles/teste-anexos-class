# Prompt para o Genie (Databricks): experimento de classificação de anexos jurídicos

> Como usar:
> 1. Preencha na seção 3 o caminho da sua pasta pessoal no repositório (`<<pasta_pessoal>>`). Ela pode estar vazia; o Genie cria tudo lá dentro.
> 2. Suba `taxonomia_v1.json` e `taxonomia_benchmark_3c_v1.json` para `<<pasta_pessoal>>/prompts/`.
> 3. Coloque os notebooks e os documentos de referência em `<<pasta_pessoal>>/referencias/`, ou anote os caminhos deles na seção 2c (podem estar fora da sua pasta).
> 4. Preencha os campos `<<...>>` que você já souber.
> 5. Cole tudo abaixo da linha no Genie.
>
> O Genie procura nos notebooks e documentos de referência o que estiver em branco e só pergunta o que não encontrar lá.

---

## 1. Seu papel e o objetivo

Você é um engenheiro de dados e ML montando, no Databricks, um **experimento reprodutível de classificação de anexos de processos judiciais brasileiros**. Cada anexo (texto já extraído por OCR na fonte) deve receber uma classe de uma taxonomia definida em arquivo. No benchmark atual são **3 classes: acórdão, sentença e petição inicial** (mais `outro`); a taxonomia completa do experimento original tem 22.

O modelo é o **Microsoft-Decision-1** (modelo de decisão da Microsoft, servido pela Azure). Ele não é um LLM de chat: recebe `state` (contexto) e `questions` (uma pergunta do tipo `choice` com instruções e a descrição de cada classe) e devolve `choice`, `confidence` (0–1) e `probabilities` (uma por classe, soma 1), mais `usage` (tokens). Ele não escreve texto livre, então não há resposta para interpretar.

O experimento já foi feito fora do Databricks com esse mesmo modelo, chamado pelo OpenRouter, e funcionou. Ele serve de **referência** (execução `microsoft v1`, versão `microsoft-decision-1-20261009`, 8 requisições simultâneas):

- 256 PDFs sintéticos rotulados, com 100% de acerto e confiança média de 0,998;
- só 1 anexo abaixo de 0,95 de confiança e 4 abaixo de 0,99;
- 3.886 tokens de entrada por anexo, dos quais 2.895 são a taxonomia fixa (cerca de 75%), e 1 token de saída;
- US$ 0,16 por mil anexos;
- 0,56 s por anexo na mediana, 0,69 s no p95 e 2,0 s no pior caso, cerca de 800 anexos/min. **Esses tempos incluem o OpenRouter no caminho**, então aqui podem ser diferentes: não trate como meta.
- As probabilidades vêm sem arredondamento (por exemplo, 0,99934…). Não arredonde ao gravar.
- Lá, o gargalo foi o **OCR** dos escaneados, não o modelo. **Aqui o texto já chega extraído por OCR na fonte**, então este pipeline não lê PDF nem faz OCR: o tempo e o custo medidos são só os da classificação.
- O valor está nas probabilidades: um corte de confiança decide entre classificar automaticamente e mandar para revisão humana. Mudar o corte não exige chamar o modelo de novo.

Seu objetivo é montar a mesma arquitetura no Databricks, com **prompt, parâmetros, execução e monitoramento separados**, para rodar em anexos reais e comparar execuções (modelo, versão do prompt, corte) ao longo do tempo.

**Há duas taxonomias, e a pipeline aceita qualquer uma pelo parâmetro `prompt.versao`:**

- **`taxonomia_benchmark_3c_v1.json`:** **acórdão, sentença e petição inicial**, mais `outro` como válvula de segurança. É a do **benchmark contra regex e SVM**, que só conhecem essas 3 classes, e é o foco agora.
  - É um rascunho derivado da v1, com ~1.000 tokens fixos estimados, contra 2.895 da v1.
  - As descrições foram reescritas para separar bem os três tipos. Ele vai ser melhorado no laboratório (seção 3.8).
- **`taxonomia_v1.json`:** as 22 classes do experimento original. Fica disponível para quando o escopo crescer. Não é usada no benchmark, porque comparar 22 classes contra classificadores de 3 desfavoreceria o Decision-1 e mediria outra coisa.

## 2. O que muda neste ambiente (e como tratar)

Duas coisas são diferentes aqui e **vão continuar mudando**. Isole as duas atrás de interfaces e não espalhe detalhes delas pelo código.

**a) A chamada da API do modelo.** Implemente uma interface `ClienteModelo` com uma implementação real e uma `ClienteMock` (respostas determinísticas, para testar sem custo):

```python
@dataclass
class RespostaModelo:
    classe: str | None
    confianca: float | None
    probabilidades: dict[str, float]   # todas as classes
    input_tokens: int | None
    output_tokens: int | None
    custo_usd: float | None            # cobrado, se a API informar; senão, tokens × preço
    custo_fonte: str                   # "cobrado" | "calculado"
    modelo: str | None                 # versão devolvida pela API
    request_id: str | None
    latencia_s: float
    erro: str | None

class ClienteModelo(Protocol):
    async def classificar(self, state: dict, pergunta: dict) -> RespostaModelo: ...
```

Dados da API do Microsoft-Decision-1 neste ambiente (pergunte o que estiver em branco antes de implementar):

- Caminho de acesso: `<<Azure AI Foundry direto (<recurso>/providers/microsoft/v1/systemone), endpoint externo no Model Serving / AI Gateway do Databricks, proxy interno...>>`
- Autenticação: `<<api-key, Entra ID / service principal, token do Databricks; secret scope e chave>>`. Use sempre `dbutils.secrets.get`, nunca a chave no código.
- Nome e versão do modelo / deployment: `<<...>>`. Grave a versão que a resposta devolver, não só a solicitada.
- Formato do corpo e da resposta: `<<igual ao de referência abaixo, ou o que o caminho escolhido exigir>>`
- Limites: até 32.768 tokens por requisição (a taxonomia ocupa cerca de 2.900); requisições por minuto: `<<cota do recurso/deployment>>`
- Preço: `<<US$ por milhão de tokens de entrada e de saída>>`. A referência era US$ 0,042 por milhão de entrada, com saída gratuita.

Formato de referência (o do experimento, igual para o Microsoft-Decision-1):

```json
// requisição
{"model": "<modelo>",
 "state": {"documento": {"texto": "...", "paginas": 2, "origem_texto": "OCR (pode conter erros)"}},
 "questions": {"tipo": {"type": "choice", "instructions": {...}, "criteria": {...}}}}
// resposta
{"model": "microsoft/microsoft-decision-1-20261009",
 "usage": {"input_tokens": 3717, "output_tokens": 1, "cost": 0.000156},
 "answers": {"tipo": {"type": "choice", "choice": "mandado", "confidence": 0.99931,
   "probabilities": {"mandado": 0.99935, "oficio": 0.0000848, "...": 0.0000123}}}}
```

- `usage.cost` vinha do OpenRouter e pode não existir no caminho daqui. Se existir, grave `custo_fonte = "cobrado"`; se não, calcule tokens × preço e grave `custo_fonte = "calculado"`.
- Grave também o identificador da requisição que a API devolver (header ou campo), para conciliar com a fatura e os logs da Azure.
- O endpoint de referência era alfa, então o formato pode mudar. Concentre o parsing num lugar só (`cliente_modelo.py`) e cubra com teste usando uma resposta real gravada.

Valide a resposta: se `choice` não for uma das classes da taxonomia ou faltar `probabilities`, grave como erro (`resposta inesperada: <300 primeiros caracteres>`) e não como classificação.

**b) A fonte dos anexos.** O texto já foi extraído por OCR antes de chegar aqui. Implemente uma interface `FonteAnexos` que entrega, para cada anexo:

- `anexo_id` e o `texto` vindo do OCR;
- metadados de origem: processo, data, sistema;
- se a fonte tiver: número de páginas, confiança ou qualidade do OCR e link para o documento original;
- o rótulo, se existir.

O `hash_texto` (sha256 do texto normalizado) é calculado por você. Não há PDF nem OCR neste pipeline. Pergunte:

- em que tabela e coluna está o texto;
- se há marcação de página;
- se há confiança do OCR;
- se o texto pode vir vazio ou parcial;
- se o OCR pode ser refeito na fonte (texto que muda).

- Fonte atual: `<<tabela ou visão com o texto de OCR; colunas>>`
- Gabarito (rótulos), se houver: `<<tabela/arquivo; colunas>>`

**c) Material de referência.** Você vai receber dois tipos de material sobre os classificadores que a equipe já testou, o regex e o SVM (as metodologias A e B da seção 3.6):

- **Notebooks**, que mostram o que foi executado: fonte de dados, código e tabelas de resultado.
  - Onde estão: `<<caminhos no workspace ou pasta referencias/notebooks/>>`
  - O que cada um é: `<<ex.: leitura da fonte, classificador regex, classificador SVM, avaliação, resultados>>`
- **Documentos**, que explicam esses experimentos em mais detalhe: relatórios, apresentações, documentação de metodologia.
  - Onde estão: `<<caminhos ou pasta referencias/documentos/>>`
  - O que cada um é: `<<ex.: relatório do SVM, definição das classes, análise de erros do regex>>`

**Leia tudo antes de escrever código.** Os notebooks dizem **como** foi feito. Os documentos costumam dizer **por quê**, **com qual gabarito** e **o que deu errado**. Produza um `referencias/INVENTARIO.md` com o seguinte, citando em cada item de onde veio a informação (arquivo e seção ou célula):

- **Fonte de dados:** tabelas e visões lidas, coluna do texto de OCR, chaves (`anexo_id`, processo), filtros aplicados, volume e como os 130 mil anexos foram selecionados.
- **Rótulos:** de onde vêm, a taxonomia usada (classes e nomes) e um primeiro rascunho do `mapeamento_classes` para a v1.
- **Resultados dos experimentos:** tabelas e artefatos com as classificações de A e B, métricas reportadas, runs do MLflow e o que já se sabe sobre os erros.
- **Como o tempo e o custo foram medidos:** de onde saíram os 5,8 minutos (o que está dentro e fora do relógio), cluster e configuração, e como o custo foi contado.
- **Chamadas de API e autenticação:** endpoints, secret scopes e padrão de retry, se algum dos notebooks já chama um modelo.
- **Convenções da equipe:** catalog/schema, nomes de tabela, tags, bibliotecas e utilitários que valem a pena reaproveitar.
- **Metodologia de cada experimento** (principalmente dos documentos):
  - como o regex foi construído e quais classes ele cobre;
  - como o SVM foi treinado: features, dados de treino, separação treino/teste, validação;
  - em que conjunto e com qual gabarito os 88% e os 92% foram medidos;
  - métricas por classe, se houver.
- **Definições de classe e critérios de rotulagem** usados pela equipe: como a equipe decide, por exemplo, despacho × decisão. Compare com `taxonomia_v1.json` e liste onde as definições divergem. Essas diferenças explicam parte dos conflitos e alimentam o laboratório de prompts (seção 3.8).
- **Erros e limitações conhecidos:** classes em que regex e SVM erram, pares que confundem, tipos de texto problemáticos (OCR ruim, documentos longos, híbridos), casos de borda citados. Use isso para:
  - montar o `dev` do laboratório, sobreamostrando esses casos;
  - fazer as primeiras hipóteses de melhoria do prompt;
  - escolher as análises por classe do benchmark.
- **Decisões e premissas** já tomadas pela equipe: custo da revisão, volumes, metas, restrições do ambiente. Elas viram valores do `params.yaml` ou perguntas para mim.
- **Divergências:**
  - onde os notebooks e os documentos se contradizem (por exemplo, um documento diz 92% e a tabela de resultados dá outro número; ou o documento descreve um conjunto e o notebook usa outro);
  - onde o material contradiz este prompt.
  - Nas divergências entre material, **o que o notebook e as tabelas mostram vale como fato**, e o documento como intenção. Registre as duas versões e me pergunte.

Regras para o material de referência:

- Notebooks e documentos são **material de consulta**, não especificação. Se algo neles conflitar com este prompt, a arquitetura deste prompt vale, e o conflito vai no inventário para eu decidir.
- Não altere os notebooks, os documentos nem as tabelas que os notebooks escrevem. Leia e copie para o projeto só o que for reaproveitado, com a origem citada num comentário.
- Não copie chaves ou tokens que apareçam em qualquer um deles. Use o mesmo secret scope via `dbutils.secrets`.
- Use os resultados de A e B a partir das tabelas que eles já gravaram (`fonte_resultado = 'historico'`). Rodar A ou B de novo só se for necessário e eu aprovar.
- Definições de classe vindas dos documentos **não entram direto** na `taxonomia_v1.json`. Elas viram hipóteses de um desafiante no laboratório (seção 3.8) e só substituem a v1 se passarem no gate.
- Tudo o que o inventário responder sai da lista de perguntas da etapa 1.

**d) Ainda não há chave de API.** Ela está sendo pedida. Até chegar, trabalhe no **modo sem chave**:

- `modelo.cliente: mock` no `params.yaml`. Toda execução com mock grava `provedor = 'mock'`, e **nunca** entra no benchmark, no gate ou em métrica de qualidade. O dashboard as filtra por padrão.
- **O mock precisa ser realista**, senão fila de revisão, calibração e conflitos ficam vazios e não dá para validar nada:
  - confiança alta na maioria dos anexos e uma fração com probabilidade espalhada entre 2 classes;
  - latência simulada (~0,55 s, com cauda);
  - alguns 429 e timeouts aleatórios, para exercitar o retry;
  - tokens estimados pelo tamanho do texto.
  - Se houver resultados do SVM, uma opção boa é o mock seguir a classe do SVM com ruído, para que os conflitos tenham padrão real.
- **Implemente o cliente real mesmo assim:** monte a requisição e leia a resposta, com o teste de parsing usando o JSON de referência da seção 2a. Quando a chave chegar, a ativação é preencher o secret e mudar `modelo.cliente` para `real`.
- **Adiante tudo o que não depende da API**, principalmente o lado regex/SVM das seções 3.6 a 3.8:
  - resultados carregados;
  - calibração do SVM;
  - acurácia recalculada no holdout;
  - conflitos regex × SVM;
  - rotulagem do dev e do holdout;
  - primeiras versões do prompt.
- O que depende da API fica marcado como pendente no relatório de cada etapa, sem bloquear as outras.

## 3. Arquitetura (pasta pessoal no repositório)

**Tudo é criado dentro de uma pasta só minha no repositório:** `<<pasta_pessoal>>` (ex.: `usuarios/<meu_nome>/classificacao_anexos/`). Hoje ela está vazia.

- **Não crie, altere nem apague nada fora dela.** O repositório é compartilhado e o resto pertence a outras pessoas e projetos. Isso inclui arquivos na raiz, como `databricks.yml`, `requirements.txt`, `.gitignore` e configuração de CI.
- Se algo precisar ficar fora da pasta, pare e me pergunte antes.
- O material de referência fora da pasta (seção 2c) é só lido.
- Imports são relativos à pasta: use `sys.path` ou `%run` apontando para `<<pasta_pessoal>>/src`, sem instalar pacote no repositório nem mudar caminhos globais.
- O Asset Bundle (`databricks.yml` e `resources/`) fica **dentro** da pasta, como um bundle próprio.
- Tabelas, volumes e experimentos do MLflow também ficam num espaço só meu:
  - schema `<<catalog>>.<<schema_pessoal>>`;
  - experimento MLflow em `<<caminho do workspace>>/classificacao_anexos`.
  - Não grave em schemas compartilhados. Pergunte se o schema não existir ou se eu não tiver permissão para criá-lo.
- Não faça commit nem push por conta própria. Eu reviso e faço os commits.

```
<<pasta_pessoal>>/
├── config/
│   └── params.yaml            # TODOS os parâmetros; widgets só sobrescrevem
├── prompts/
│   ├── taxonomia_benchmark_3c_v1.json  # 3 classes + outro (fornecido; ponto de partida do benchmark)
│   └── taxonomia_v1.json      # instruções + 22 classes (fornecido, não reescrever)
├── src/
│   ├── config.py              # carrega yaml + widgets → dataclass imutável; calcula config_hash
│   ├── prompt.py              # carrega taxonomia, monta a pergunta, calcula prompt_hash
│   ├── fonte.py               # FonteAnexos + implementação atual
│   ├── texto.py               # normalização do texto da fonte, hash e corte de texto longo
│   ├── cliente_modelo.py      # ClienteModelo + implementação real + ClienteMock
│   ├── classificador.py       # orquestra async: semáforo, retry, lotes, idempotência
│   ├── metricas.py            # funções puras de métrica (testáveis sem Spark)
│   ├── laboratorio.py         # conjuntos de avaliação, scorecard, gate, campeão × desafiante
│   ├── benchmark.py           # normaliza resultados de cada metodologia e compara
│   └── conflitos.py           # detecta conflitos e baixa confiança, atribui motivos
├── notebooks/
│   ├── 00_setup.py
│   ├── 01_ingestao.py
│   ├── 02_classificacao.py
│   ├── 03_metricas.py
│   ├── 04_dashboard.sql       # consultas do AI/BI dashboard
│   ├── 05_benchmark.py        # Microsoft-Decision-1 × metodologias A e B da equipe
│   ├── 06_conflitos.py        # fila de análise, padrões de dúvida, retorno da revisão
│   ├── 07_laboratorio_prompts.py  # itera versões do prompt numa amostra; gate de promoção
│   └── 08_teste_vazao.py      # teste de carga e rodada total (130 mil anexos)
├── referencias/               # só leitura: notebooks/, documentos/ + INVENTARIO.md
├── tests/                     # pytest com ClienteMock e textos de exemplo
├── databricks.yml             # bundle próprio desta pasta
└── resources/job.yml          # jobs: 01 → 02 → 03 → 06; jobs do 05 e do 08
```

Princípio: **notebooks só orquestram**, a lógica fica em `src/` (importável e testável). Nenhum valor fixo de negócio dentro de notebook.

### 3.1 Prompt (`prompts/` + `src/prompt.py`)

- Cada taxonomia tem `instrucoes` (pergunta, contexto, como decidir) e `classes` (cada uma com `o_que_e`, `sinais`, `nao_confundir`). Não altere os arquivos fornecidos. Para testar uma variante, crie um arquivo novo em `prompts/candidatos/` (ex.: `taxonomia_benchmark_3c_v2a.json`).
- `prompt_hash = sha256(json.dumps([instrucoes, classes], ensure_ascii=False, sort_keys=True))[:12]`. Tem que dar **`c4ffefc2e54f`** para a v1 e **`f96ed8ee75b1`** para a `benchmark_3c_v1`. Escreva um teste que confere as duas.
- As classes válidas de cada execução são as chaves de `classes` da taxonomia usada. Grave a versão da taxonomia em `execucoes` e `classificacoes`, para que nenhuma métrica misture execuções de 3 e de 22 classes.
- O `state` enviado é `{"documento": {"texto", "paginas", "origem_texto"}}`, com `origem_texto` = `"OCR (pode conter erros)"` (aqui todo texto vem de OCR). Mande `paginas` só se a fonte informar; não invente o valor.
- **Limpeza antes de cortar** (`texto.limpar_boilerplate`): remova as linhas que se repetem em várias páginas (carimbos e rodapés de sistema, numeração de folhas, "Assinado eletronicamente por..."). Mantenha a primeira ocorrência. Senão, uma janela curta gasta boa parte dos caracteres com carimbo. Grave `chars_antes` e `chars_depois`.
- **Janela de texto** (`prompt.janela`): quanto do anexo é enviado. É uma variável do experimento, e não só um limite técnico (ver "Janela de texto" na seção 3.8):
  - `inteiro`: tudo, respeitando `limite_chars` (60.000), que existe pelo limite de 32.768 tokens por requisição;
  - `inicio_fim`: os primeiros `janela_inicio_chars` e os últimos `janela_fim_chars`;
  - `inicio`: só os primeiros `janela_inicio_chars`.
  - Os trechos são separados por `\n\n[... trecho omitido ...]\n\n`, porque título, partes, pedidos, dispositivo e assinatura ficam no começo e no fim.
  - Marque `truncado = true` sempre que algo for omitido e grave a estratégia e os tamanhos usados.

### 3.2 Parâmetros (`config/params.yaml`)

```yaml
ambiente:
  pasta_pessoal: <<caminho da pasta no repositório>>
  catalog: <<catalog>>
  schema: <<schema_pessoal>>      # só meu; nada em schema compartilhado
  mlflow_experimento: <<caminho do experimento>>
fonte:
  tipo: <<volume|tabela|...>>
  local: <<caminho ou tabela>>
  gabarito: <<tabela ou null>>
texto:
  coluna_texto: <<coluna com o texto do OCR>>
  min_chars: 50                  # abaixo disso não chama o modelo: vira erro texto_insuficiente
  versao_normalizacao: 1
modelo:
  provedor: microsoft
  caminho: <<azure_foundry|databricks_serving|outro>>
  endpoint: <<...>>
  nome: <<microsoft-decision-1 / nome do deployment>>
  secret_scope: <<scope>>
  secret_key: <<key>>
  cliente: mock                  # mock até a chave chegar; depois real
  concorrencia: 8                # inicial; a rodada total usa a seção escala
  max_retries: 4
  timeout_s: 60
  backoff_max_s: 20
  usd_por_mtok_entrada: <<0.042?>>   # usado quando a resposta não traz o custo
  usd_por_mtok_saida: <<0.0?>>
prompt:
  versao: benchmark_3c_v1        # ou v1 (22 classes)
  limite_chars: 60000            # teto técnico (32.768 tokens por requisição)
  fracao_inicio: 0.7             # usado quando janela = inteiro e passa do teto
  janela: inicio_fim             # inteiro | inicio_fim | inicio
  janela_inicio_chars: 4000
  janela_fim_chars: 1500
  limpar_boilerplate: true
decisao:
  corte_confianca: 0.95          # acima: automático; abaixo: revisão humana
execucao:
  limite_docs: null              # amostra para smoke test
  tamanho_lote_escrita: 200
  reprocessar: false             # true ignora a idempotência
  rotulo: ""                     # anotação livre da execução
benchmark:
  amostra: <<tabela com os anexo_id do benchmark>>   # o mesmo conjunto para as 3 metodologias
  repeticoes: 2                  # execuções por metodologia, para medir variação
  volume_mensal_projecao: [100000, 300000, 1000000]
  usd_por_dbu: <<preço do DBU do contrato>>
  usd_por_hora_revisao_humana: <<custo/hora do revisor>>
  revisoes_por_hora: <<anexos revisados por hora>>
  usd_por_erro_nao_revisado: <<custo estimado de um anexo classificado errado que passa sem revisão>>
  faixa_sensibilidade_usd_erro: [0.1, 0.25, 0.5, 1, 2, 5, 10]
  faixa_sensibilidade_usd_revisao: [0.1, 0.25, 0.5, 1, 2]
  metodologias:
    decision1: {tipo: este_pipeline}
    metodo_a:
      nome: regex                # acurácia reportada: 88%
      manutencao_horas_mes: <<horas/mês ajustando regras>>
      resultados: <<tabela/notebook/job existente>>
      reexecutavel: <<true|false>>
    metodo_b:
      nome: svm                  # acurácia reportada: 92%
      manutencao_horas_mes: <<horas/mês: rotular, treinar de novo, publicar>>
      resultados: <<...>>
      reexecutavel: <<true|false>>
conflitos:
  corte_baixa_confianca: 0.95    # pode ser diferente do corte de decisão
  margem_minima: 0.20            # diferença mínima entre a 1ª e a 2ª classe
  delta_prob_instavel: 0.05      # variação entre execuções que conta como instável
  amostra_auditoria_pct: 2       # % dos casos confiantes e sem conflito revisados ao acaso
  max_fila_por_dia: <<capacidade de revisão>>
laboratorio:
  semente: 42
  tamanho_dev: 2000              # amostra de iteração (estratificada)
  tamanho_holdout: 1000          # só usada no gate; nunca para ajustar o prompt
  min_por_classe: 30             # classes raras entram com pelo menos isso
  sobreamostrar_conflitos_pct: 30   # % do dev vindo de anexos em que A e B discordam
  campeao: benchmark_3c_v1       # versão em uso; desafiantes ficam em prompts/candidatos/
  janelas_teste:                 # comparadas no dev contra 'inteiro'
    - {janela: inicio, inicio: 2000}
    - {janela: inicio, inicio: 4000}
    - {janela: inicio_fim, inicio: 3000, fim: 1000}
    - {janela: inicio_fim, inicio: 4000, fim: 1500}
    - {janela: inicio_fim, inicio: 8000, fim: 3000}
    - {janela: inteiro}
  gate:                          # "confiança suficiente" para a rodada total
    acuracia_min_ic95_inferior: <<ex.: 0.95>>   # limite inferior do IC 95% (Wilson), dev e holdout
    erro_confiante_max_pct: <<ex.: 0.5>>
    revisao_max_pct: <<ex.: 5>>   # % abaixo do corte de decisão
    f1_min_por_classe: <<ex.: 0.85>>
    ece_max: <<ex.: 0.03>>
    troca_classe_entre_repeticoes_max_pct: 0.5
    sem_piora_regressao: true
    tokens_fixos_max: <<ex.: 1500>>   # limite de tamanho do prompt (custo e vazão)
escala:
  meta_docs: 130000
  meta_minutos: 5.8              # tempo das outras metodologias (confirmar o escopo)
  concorrencia_inicial: 32
  concorrencia_max: 512
  degraus_teste_carga: [8, 32, 64, 128, 256, 384, 512]
  docs_por_degrau: 3000
  endpoints: [<<endpoint/deployment 1>>]   # vários deployments/regiões somam cota
  shards: 1                      # processos/tarefas paralelas, se um driver não der conta
  tamanho_lote_escrita: 10000    # lotes grandes na rodada total (evita arquivos pequenos no Delta)
```

- Widgets do notebook podem sobrescrever qualquer chave (por exemplo, `modelo.nome`, `prompt.versao`, `execucao.limite_docs`, `execucao.rotulo`).
- A config final (yaml + widgets) é congelada, gravada inteira em `execucoes.params_json` e resumida em `config_hash`. A execução tem que poder ser reproduzida só com esse registro.

### 3.3 Modelo de dados (Delta no Unity Catalog, schema pessoal `<<catalog>>.<<schema_pessoal>>`)

| Tabela | Grão | Colunas principais |
|---|---|---|
| `anexos` | 1 por anexo | `anexo_id`, `origem`, metadados de origem, link do original (se houver), `ingerido_em` |
| `anexos_texto` | 1 por `anexo_id` + `hash_texto` | `texto` normalizado, `hash_texto`, `versao_normalizacao`, `chars`, `paginas` e `qualidade_ocr` (se a fonte tiver), `texto_insuficiente`, `lido_em`. É uma cópia congelada do texto usado, para o experimento continuar reproduzível mesmo se a fonte mudar. |
| `gabarito` | 1 por anexo | `anexo_id`, `rotulo`, recortes opcionais (justiça, sistema, qualidade do OCR) |
| `execucoes` | 1 por execução | `run_id`, `inicio`, `fim`, `status`, `rotulo`, `provedor`, `modelo_solicitado`, `prompt_versao`, `prompt_hash`, `config_hash`, `params_json`, `docs`, `docs_erro`, `t_fase_classificacao_s`, `docs_por_minuto`, `mlflow_run_id` |
| `classificacoes` | 1 por anexo × execução | `run_id`, `anexo_id`, `hash_texto`, `classe`, `confianca`, `prob_classe`, `probabilidades MAP<STRING,DOUBLE>`, `top3 ARRAY<STRUCT<classe,prob>>`, `truncado`, `input_tokens`, `output_tokens`, `custo_usd`, `custo_fonte`, `modelo`, `request_id`, `latencia_s`, `tentativas`, `erro`, `timestamp` |

- Particione ou faça liquid clustering de `classificacoes` por `run_id`.
- Grave as probabilidades de **todas** as classes. É isso que permite recalcular corte, juntar classes e medir calibração sem chamar o modelo de novo.

### 3.4 Notebooks de execução

**`00_setup`**: cria schema, volumes e tabelas com DDL explícito. É idempotente (`CREATE ... IF NOT EXISTS`).

**`01_ingestao`**
- Lê o texto de OCR da fonte via `FonteAnexos`, só com Spark/SQL e sem `collect`. Com 130 mil anexos isso leva segundos.
- Normaliza espaços e linhas em branco (sem alterar o conteúdo), calcula `hash_texto` e faz `MERGE` em `anexos` e `anexos_texto`.
  - Texto que não mudou não é regravado.
  - Se o OCR foi refeito na fonte, entra um novo `hash_texto`, e o anexo é reclassificado na próxima execução.
- Texto vazio ou com menos de `min_chars` caracteres fica com `texto_insuficiente = true` e não vai para o modelo. Ele entra na taxa de erro como `texto_insuficiente`.
- Reporte:
  - a distribuição de `chars`;
  - o % de textos insuficientes;
  - o % acima de `limite_chars` (os que serão cortados);
  - a qualidade do OCR, se houver.

**`02_classificacao`**
- Carrega a config, gera `run_id` (`AAAAMMDD-HHMMSS-xxxx`), grava a linha em `execucoes` com `status = 'rodando'` e abre um run no MLflow.
- Seleciona os anexos com texto. **Idempotência:** pula os que já têm classificação sem erro com o mesmo (`hash_texto`, `prompt_hash`, `modelo_solicitado`), a menos que `reprocessar = true`.
- Chama o modelo com **asyncio no driver** (`asyncio.Semaphore(concorrencia)` com cliente HTTP assíncrono). O gargalo é o limite de requisições da API, não a CPU, então distribuir as chamadas pelos workers só complica e dificulta controlar a concorrência total. Para a rodada de 130 mil anexos, veja a seção 3.9 (concorrência adaptativa e shards).
- Retry com backoff exponencial só para 429, 5xx e timeout, respeitando `Retry-After`. Grave o número de `tentativas`. Erro definitivo vira linha com `erro` preenchido.
- Mede `latencia_s` só em volta da chamada ao modelo.
- Escreve em lotes de `tamanho_lote_escrita` com append em Delta. Uma queda no meio não perde o que já foi feito, e a idempotência retoma de onde parou.
- Mostra progresso a cada lote: feitos, erros e latência p50.
- No fim, atualiza `execucoes` (`status`, totais e tempos) e chama `03_metricas` para o `run_id`.

### 3.5 Métricas e monitoramento (`src/metricas.py` + `03_metricas` + `04_dashboard`)

Calcule por `run_id` e grave no MLflow (params = config congelada + `prompt_hash`; metrics = números abaixo; artifacts = matriz de confusão, curva de corte e diagrama de confiabilidade em PNG/CSV). Crie também visões SQL (`vw_metricas_execucao`, `vw_metricas_classe`, `vw_fila_revisao`) para o dashboard.

**Operação, sempre:**
- docs, docs com erro (taxa e tipos de erro), docs truncados, docs com texto insuficiente;
- latência média, p50, p95 e máxima; vazão em docs/min;
- tokens de entrada e saída (total e por doc); custo total, por doc e por mil docs, com a origem do custo.

**Decisão, sempre (não precisa de rótulo):**
- distribuição da confiança;
- docs abaixo de 0,95 e de 0,99;
- **fila de revisão por corte:** % de docs que iriam para revisão com cortes de 0,80 a 0,99, com passo de 0,01;
- distribuição das classes previstas (para detectar drift entre execuções);
- os N anexos de menor confiança, com a 1ª e a 2ª classe e a diferença entre elas.

**Qualidade, quando houver gabarito:**
- acurácia geral, precisão, recall e F1 por classe, F1 macro;
- matriz de confusão, destacando os pares que já se sabe serem confundíveis:
  - no benchmark de 3 classes: acórdão × sentença (o acórdão transcreve a sentença), sentença × petição inicial (o relatório da sentença resume os pedidos) e qualquer classe × `outro` (decisão monocrática, contestação, recurso);
  - na v1 de 22 classes: despacho × decisão interlocutória, despacho × certidão, decisão monocrática × agravo de instrumento, ata de audiência × termo de acordo × sentença homologatória;
- acurácia e confiança por recorte (qualidade do OCR, se houver; faixa de tamanho do texto; justiça; sistema);
- **calibração:** ECE com 10 faixas e diagrama de confiabilidade;
- **acurácia × cobertura:** para cada corte, a acurácia dos que seriam classificados automaticamente e o % automatizado. Esse é o número que define o corte de produção.

**Comparação entre execuções** (função `comparar(run_a, run_b)`):
- concordância de classe entre as duas execuções;
- anexos que mudaram de classe;
- variação máxima e média da probabilidade da classe escolhida (mede estabilidade: rode a mesma config duas vezes para saber se o Microsoft-Decision-1 devolve sempre as mesmas probabilidades);
- correlação das incertezas (1 − confiança) e anexos em que só um dos dois hesitou;
- diferença de custo, latência e acurácia.
- Use isso para modelo A × B, `prompt_hash` v1 × v2 e a mesma config em dias diferentes.

**Dashboard (`04_dashboard.sql`, AI/BI):**
- tendência por execução: acurácia, % para revisão, custo por mil docs, p95 de latência, taxa de erro;
- fila de revisão por corte;
- matriz de confusão;
- tabela dos anexos de menor confiança;
- filtros por `run_id`, modelo e `prompt_hash`.

### 3.6 Benchmark de custo e tempo contra as metodologias da equipe (`src/benchmark.py` + `05_benchmark`)

O benchmark tem **3 classes: acórdão, sentença e petição inicial**. O Decision-1 usa a `taxonomia_benchmark_3c` (seção 1).

A equipe já classificou esses anexos com duas outras metodologias: **regex** (A, 88% de acurácia reportada) e **SVM** (B, 92%). As duas rodam só no cluster, então **custam menos para executar** que uma chamada de API. Por isso o benchmark não pode parar em "quem é mais barato para rodar". Ele precisa responder **quem é mais barato por anexo classificado corretamente**, somando execução, revisão humana, erros que passam e manutenção (ver "Caso de negócio" abaixo). Monte desde já um benchmark que compare as três em **custo**, **tempo** e qualidade, porque custo e tempo só significam algo para uma qualidade conhecida.

As duas metodologias (preencha a partir dos notebooks e documentos de referência, seção 2c, e pergunte o que continuar em branco):

| | Metodologia A | Metodologia B |
|---|---|---|
| O que é | Regras / regex | SVM (modelo supervisionado) |
| Acurácia reportada | 88% | 92% |
| Como os 88% e 92% foram medidos | `<<gabarito, conjunto, classes; havia separação treino/teste?>>` | `<<...>>` |
| Onde estão código e resultados | `<<notebook, job, tabela>>` | `<<...>>` |
| Dá para rodar de novo agora? | `<<sim/não>>` | `<<sim/não>>` |
| Classes | acórdão, sentença e petição inicial: `<<nomes usados; o que faz com outros tipos?>>` | `<<...>>` |
| Devolve confiança/probabilidade? | Em geral não (casou/não casou, ou ordem das regras) | Score de decisão por classe, que precisa ser calibrado |
| De onde vem o custo | `<<tokens de API, DBU de cluster, GPU, licença>>` | `<<...>>` |

**Protocolo para a comparação ser justa:**

1. **Mesmo conjunto.** As três rodam sobre a mesma lista de `anexo_id` (`benchmark.amostra`). Se houver gabarito, use a amostra rotulada. Se uma metodologia não puder rodar de novo, use os resultados que já existem só na interseção de anexos e marque `fonte_resultado = 'historico'`.
2. **Mesmo texto.** Todas as metodologias recebem o mesmo texto de OCR da fonte (`anexos_texto`). Nenhuma conta tempo ou custo de OCR, porque ele já foi feito antes. Se alguma metodologia fizer pré-processamento próprio, ele entra no tempo e no custo dela.
3. **Mesmo lugar e mesma janela.** As que forem reexecutáveis rodam no mesmo tipo de cluster e próximas no tempo, com `repeticoes` execuções cada. Reporte a média e a variação entre as repetições.
4. **Taxonomia alinhada.** As três metodologias usam as mesmas 3 classes. Confirme pelo material de referência:
   - os nomes que regex e SVM usam, e crie `mapeamento_classes` para `acordao`, `sentenca` e `peticao_inicial`;
   - se os 130 mil anexos **só contêm** esses 3 tipos (corpus filtrado antes) ou se há outros tipos misturados, e como regex e SVM tratam um documento que não é nenhum dos três;
   - se o corpus só tem os 3 tipos, `outro` do Decision-1 conta como erro, mas é reportado à parte, porque costuma indicar OCR ilegível ou um rótulo errado no gabarito;
   - se há outros tipos e regex/SVM são forçados a escolher entre 3, compare também a versão do Decision-1 sem `outro` (usando a maior probabilidade entre as 3), para a comparação ficar nas mesmas condições.
5. **Mesma regra de decisão.** Para quem devolve confiança, compare no mesmo nível de qualidade: escolha o corte de cada metodologia que atinge a mesma acurácia nos casos automáticos (por exemplo, 99%) e compare o % automatizado. Quem não devolve confiança entra com 100% automatizado e a sua acurácia bruta.
   - **SVM:** calibre os scores (Platt ou isotônica) no `dev` e avalie no `holdout`, para que a confiança dele seja comparável com a do Decision-1. Não compare o SVM sem calibração, porque isso o desfavorece injustamente.
   - **Regex:** se as regras tiverem prioridade ou mais de uma casar, use "uma regra só, sem conflito" como sinal de confiança, e documente.
6. **Mesmo gabarito.** Recalcule os 88% e os 92% no **mesmo** holdout rotulado em que o Decision-1 é avaliado. Os números reportados ficam só como referência. Se o SVM foi treinado com anexos que estão no holdout, retire esses anexos ou, com minha aprovação, treine de novo sem eles, senão a acurácia dele fica inflada.

**O que medir por metodologia e execução:**

- **Tempo:**
  - latência por anexo (p50, p95 e máxima);
  - vazão (anexos/min);
  - tempo total de parede do lote, separando leitura do texto, classificação e gravação;
  - tempo até o primeiro resultado.
- **Custo, separado por componente:**
  - API (tokens × preço, ou o valor cobrado);
  - compute do Databricks: DBUs de `system.billing.usage`, filtrando pelo `job_run_id` ou por uma tag `benchmark_run_id` que você coloca em cada execução, vezes `usd_por_dbu`;
  - custo fixo, se houver (treino, licença, GPU dedicada), rateado por mês;
  - total por anexo e por mil anexos.
- **Custo de operação:** anexos que vão para revisão humana × custo da revisão (`usd_por_hora_revisao_humana / revisoes_por_hora`). Esse custo costuma superar o do modelo e é onde a confiança calibrada faz diferença.
- **Qualidade** (com gabarito): acurácia, F1 macro e acurácia nos pares confundíveis.
- **Projeção mensal:** custo total e horas de processamento para cada volume de `volume_mensal_projecao`.

**Caso de negócio** (a pergunta principal do benchmark):

Custo total por mil anexos de cada metodologia, separado em:

- **execução:** API + DBU;
- **revisão:** anexos enviados à revisão × custo de uma revisão;
- **erros:** erros que passam sem revisão × `usd_por_erro_nao_revisado`;
- **manutenção:** `manutencao_horas_mes` × custo/hora, rateado pelo volume mensal. No Decision-1, a manutenção é o tempo gasto no laboratório de prompts.

Com esse custo total:

- **Ponto de equilíbrio:** quantos erros ou revisões evitados por mil anexos o Decision-1 precisa para empatar com o regex e com o SVM. Como referência, com a taxonomia de 3 classes (~1.000 tokens fixos) e janela de ~5.500 caracteres, a API custa cerca de US$ 14 a 18 pelos 130 mil anexos. Se um erro evitado valer US$ 1, bastam de 14 a 18 erros evitados nos 130 mil (≈ +0,01 ponto percentual de acurácia). Mostre o número real, com DBU e preços daqui.
- **Erros absolutos nos 130 mil:** regex com 88% são cerca de 15.600 erros; SVM com 92%, cerca de 10.400. Mostre os erros do Decision-1 na mesma escala, com intervalo de confiança vindo do holdout.
- **Sensibilidade:** um mapa de calor da metodologia vencedora para cada combinação de `faixa_sensibilidade_usd_erro` × `faixa_sensibilidade_usd_revisao`. Mostra a partir de que custo de erro o Decision-1 compensa, e se existe alguma faixa em que o SVM ou o regex vencem.
- **Onde cada um ganha:** F1 por classe das três lado a lado. É comum o SVM ir bem nas classes frequentes e mal nas raras, e o regex falhar em textos sem título ou com OCR ruim. Destaque as classes em que o Decision-1 ganha ou perde.
- **Cenários de uso:** compare não só "um substitui o outro", mas:
  1. Decision-1 sozinho;
  2. SVM sozinho;
  3. **SVM como principal e Decision-1 só nos casos em que o SVM tem confiança baixa** (custo de API só numa fração dos anexos);
  4. **automático só quando o SVM e o Decision-1 concordam**, com o resto indo para revisão;
  5. regex como filtro rápido para as classes em que ele acerta quase sempre, e Decision-1 no resto.
  - Para cada cenário, mostre a acurácia nos automáticos, o % automatizado, os erros que passam, o custo total e o tempo.
- **Conclusão honesta:** se o SVM calibrado empatar em acurácia e em % automatizado, diga isso. Nesse caso, a vantagem do Decision-1 fica na manutenção e nos cenários 3 ou 4, e o relatório deve dizer exatamente isso.

**Tabelas:**

- `benchmark_execucoes`: uma linha por metodologia × execução, com `benchmark_run_id`, `metodologia`, `fonte_resultado` (`reexecutado`/`historico`), cluster, início, fim, docs, docs com erro, tempos, custo por componente, `params_json`.
- `benchmark_resultados`: uma linha por anexo × metodologia × execução, com `classe_original`, `classe_mapeada` (nas 3 classes do benchmark), `confianca` (pode ser nula), `latencia_s`, `custo_usd` (se houver por anexo), `erro`.
- `vw_benchmark_resumo`: uma linha por metodologia, com médias entre repetições, custo por mil, custo mensal projetado, p50/p95, vazão, acurácia, % automatizado no corte equivalente e custo de revisão.

**Organização do código:**

- Em `src/benchmark.py`, cada metodologia é um adaptador `Metodologia` com dois métodos:
  - `executar(anexo_ids) -> DataFrame`, só para as reexecutáveis;
  - `carregar_resultados(origem) -> DataFrame`, para as que têm resultado histórico.
- Os dois métodos devolvem o schema de `benchmark_resultados`. O Microsoft-Decision-1 reaproveita o `02_classificacao`.
- O `05_benchmark`:
  - roda ou carrega as três metodologias;
  - grava as tabelas;
  - loga no MLflow um run pai com três runs filhos, um por metodologia;
  - gera os gráficos.

**Gráficos e saída:**

- custo por mil anexos, em barras empilhadas por componente;
- latência por anexo, em boxplot ou pontos;
- acurácia × custo por mil, um ponto por metodologia;
- custo total por mil, empilhado em execução, revisão, erros e manutenção;
- mapa de calor de sensibilidade (custo do erro × custo da revisão → vencedor);
- curva % automatizado × acurácia nos automáticos, uma linha por metodologia e por cenário;
- custo mensal projetado por volume;
- tabela-resumo final;
- um parágrafo de conclusão escrito a partir dos números, dizendo quem vence em quê e com quais ressalvas (amostra, resultados históricos, classes não mapeadas).

### 3.7 Monitoramento de conflitos e baixa confiança (`src/conflitos.py` + `06_conflitos`)

Os casos em que o modelo hesita, ou em que as metodologias discordam, são o material mais valioso do experimento. Eles mostram onde a taxonomia é ambígua, onde o OCR atrapalha e onde falta uma classe. No experimento de referência, as dúvidas caíram justamente nos pares que um advogado também pararia para pensar: despacho × decisão interlocutória, despacho × certidão e decisão monocrática × agravo de instrumento. Também apareceu que **modelos diferentes duvidam de anexos diferentes**: a correlação entre as incertezas de dois modelos foi de só 0,19. Por isso, conflito entre métodos é um sinal separado de baixa confiança e precisa ser monitorado à parte.

**Sinais que marcam um anexo** (um anexo pode ter vários; grave todos):

| Sinal | Regra |
|---|---|
| `baixa_confianca` | `confianca < corte_baixa_confianca` |
| `margem_estreita` | 1ª classe − 2ª classe `< margem_minima`, mesmo com confiança alta |
| `conflito_metodologias` | Microsoft-Decision-1, A e B não escolhem a mesma classe (já mapeada para as classes do benchmark) |
| `conflito_execucoes` | o mesmo anexo, com o mesmo `prompt_hash` e o mesmo modelo, mudou de classe entre execuções |
| `instavel` | mesma classe, mas a probabilidade variou mais que `delta_prob_instavel` |
| `conflito_prompt` | a classe mudou entre `prompt_hash` diferentes (mostra o efeito da mudança de prompt) |
| `erro_gabarito` | errou contra o gabarito ou contra a revisão humana |
| `erro_confiante` | errou com confiança ≥ corte. É o pior caso, porque passaria sem revisão. |
| `provavel_outro` | `outro` como 1ª ou 2ª classe com probabilidade relevante (possível lacuna na taxonomia) |
| `auditoria` | caso confiante e sem conflito, sorteado (`amostra_auditoria_pct`) para medir o erro que não aparece |

**Contexto gravado em cada caso**, para dar para diagnosticar a causa sem reabrir nada:
- top-3 com probabilidades e as classes de cada metodologia;
- `chars`, `truncado`, e `paginas` e qualidade do OCR, se a fonte tiver;
- recortes de origem (justiça, sistema, carimbo);
- trecho inicial e final do texto enviado.

**Tabelas:**

- `casos_analise`: uma linha por anexo × `run_id` sinalizado, com:
  - `sinais ARRAY<STRING>`, `prioridade` e o contexto acima;
  - `status` (`pendente`, `revisado`, `descartado`);
  - `causa_raiz`, preenchida na revisão: `taxonomia_ambigua`, `classe_faltante`, `ocr_ruim`, `truncamento`, `documento_hibrido`, `gabarito_errado`, `erro_modelo`, `outro`.
- `revisoes`: uma linha por revisão humana, com `anexo_id`, `run_id`, `classe_correta`, `causa_raiz`, `comentario`, `revisor`, `revisado_em`.
  - A revisão volta para `gabarito` com `origem = 'revisao'`. Assim, cada ciclo aumenta o conjunto rotulado.
- Prioridade da fila:
  - primeiro `erro_confiante`;
  - depois `conflito_metodologias` com confiança alta do Decision-1;
  - depois `baixa_confianca` por ordem de menor margem;
  - por último `auditoria`.
  - A fila respeita `max_fila_por_dia`.
- A revisão pode ser feita direto na tabela, por um app simples (Databricks Apps) ou por uma planilha importada. Pergunte qual a equipe prefere e não construa uma interface sem confirmar.

**Visões para achar padrões** (`vw_conflitos_*`):

- **pares de confusão:** para cada par (1ª classe, 2ª classe), a contagem de casos de baixa confiança, a margem média e a taxa de erro. É o mapa de onde a taxonomia precisa de `nao_confundir` melhor;
- **conflitos entre metodologias:** matriz Decision-1 × A × B, e quem estava certo quando houve revisão;
- **por recorte:** taxa de baixa confiança e de conflito por qualidade do OCR, tamanho do texto, truncado, justiça e sistema. Mostra se o problema está no texto e não no prompt;
- **por causa raiz:** distribuição das causas revisadas, por classe;
- **evolução:** % sinalizado, % de erro confiante e % de conflito por `run_id` e `prompt_hash` ao longo do tempo;
- **calibração por sinal:** a acurácia real nos casos `auditoria` (confiantes) contra a dos `baixa_confianca`, para validar se a confiança separa mesmo acerto de erro.

**Ciclo de melhoria do prompt** (o objetivo principal desta seção):

1. Os pares de confusão mais frequentes e as causas `taxonomia_ambigua` / `classe_faltante` geram um relatório com exemplos reais (trechos) por par.
2. A partir dele, a equipe escreve `taxonomia_v2.json`. Por exemplo: um `nao_confundir` mais preciso, um sinal novo, uma classe nova ou classes juntadas. O Genie pode **sugerir** o texto, mas a nova versão sai sempre num arquivo novo e com revisão humana.
3. Monte um **conjunto de regressão** fixo (`conjunto_regressao`): todos os casos revisados, mais uma amostra estratificada dos fáceis, para detectar piora.
4. A v2 roda só nesse conjunto. Compare com a v1 usando a função `comparar` (seção 3.5):
   - acurácia;
   - erros confiantes;
   - % para revisão;
   - tokens e custo (um prompt maior custa mais em toda requisição);
   - os anexos que mudaram de classe, um por um.
5. A v2 só substitui a v1 se melhorar os casos difíceis sem piorar os fáceis. A decisão fica registrada no MLflow.

**Outros usos dos mesmos sinais** (deixe as visões prontas para isso):
- OCR: se `baixa_confianca` estiver concentrada em textos de OCR ruim (qualidade baixa, muito ruído, poucos caracteres), o problema está no OCR da fonte e não no prompt. Reporte isso para quem mantém o OCR;
- truncamento: se houver erros em `truncado = true`, revise `limite_chars` e `fracao_inicio`;
- corte de decisão: com os rótulos de `revisoes` e de `auditoria`, recalibre `corte_confianca`;
- ensemble: se as metodologias erram em anexos diferentes, avalie a regra "automático só se o Decision-1 estiver confiante **e** concordar com A/B", e meça quanto isso reduz o erro confiante e quanto aumenta a fila;
- drift: aumento repentino de `provavel_outro` ou de uma classe sinaliza documentos novos na fonte.

**Dashboard:** uma página "Conflitos" no AI/BI com:
- tamanho e composição da fila;
- top pares de confusão;
- matriz de conflito entre metodologias;
- a evolução por `prompt_hash`;
- a lista priorizada com link para o documento original, se a fonte tiver.

### 3.8 Laboratório de prompts: amostra primeiro, rodada total só depois do gate (`src/laboratorio.py` + `07_laboratorio_prompts`)

O benchmark completo tem mais de 130 mil anexos. Antes dele, a equipe precisa de um espaço para melhorar as descrições das classes rápido e barato, numa amostra. A rodada total só acontece quando uma versão do prompt passa um **gate** definido antes. Rodar 2.000 anexos custa cerca de US$ 0,25 (taxonomia de 3 classes) e poucos minutos, então dá para iterar muitas vezes. Com 3 classes, o dev de 2.000 dá centenas de anexos por classe, o que é suficiente para medir diferenças por classe com precisão razoável.

**Conjuntos de avaliação** (tabela `conjuntos_avaliacao`: `conjunto`, `versao_conjunto`, `anexo_id`, `estrato`), sorteados uma vez com `semente` fixa e congelados:

- **`dev`** (`tamanho_dev`): onde se itera. É estratificado por classe (pela classe de A/B, ou pelo gabarito se houver), com pelo menos `min_por_classe` anexos por classe. Também entram, de propósito, `sobreamostrar_conflitos_pct` anexos em que A e B discordam e os recortes difíceis (OCR de baixa qualidade, textos longos ou cortados, cada justiça e sistema).
- **`holdout`** (`tamanho_holdout`): mesma estratificação, sem interseção com o dev. **Ninguém olha os erros dele.** Só é avaliado no gate. Se for consultado muitas vezes, sorteie um novo e registre.
- **`regressao`**: o conjunto da seção 3.7, que cresce com os casos revisados.
- Todos saem do universo dos 130 mil, para que a amostra represente a rodada total. Mostre a distribuição de classes e de recortes da amostra ao lado da do universo.

**Rótulos:** o gate precisa de gabarito no dev e no holdout.
- Se os 130 mil não tiverem rótulo, a equipe rotula essas amostras, priorizando o holdout.
- Onde A e B concordam, a classe deles pode servir de **rótulo fraco** para triagem, marcado como `origem = 'concordancia_ab'`. O gate nunca usa só rótulo fraco.
- Pergunte qual é a disponibilidade de rotulagem antes de definir os tamanhos.

**Ciclo de iteração:**

1. Escreva uma hipótese ("despacho × decisão: o `nao_confundir` do despacho não cita o ato que só recebe recurso").
2. Crie um desafiante em `prompts/candidatos/taxonomia_v2a.json` e registre a hipótese em `prompts/CHANGELOG.md`.
3. Rode o `07_laboratorio_prompts` com o widget `versao = v2a` sobre o `dev`. Ele reaproveita o `02_classificacao` (mesmo cliente, mesmas tabelas, com `rotulo = 'lab'`).
4. Leia o **scorecard desafiante × campeão**, no mesmo dev e no mesmo momento:
   - acurácia com IC 95% (Wilson);
   - F1 por classe;
   - erros confiantes;
   - % para revisão;
   - ECE;
   - tokens fixos e custo por mil;
   - teste de McNemar pareado para saber se a diferença é real ou ruído;
   - a lista dos anexos que **mudaram** de classe (ganhos e perdas), com trechos;
   - os pares de confusão (seção 3.7) do desafiante.
5. Repita. Cada versão é um run no MLflow (experimento `laboratorio_prompts`), com o JSON da taxonomia como artefato, o `prompt_hash` e a hipótese. Se o workspace tiver o MLflow Prompt Registry, registre as versões lá também.
6. Quando um desafiante parecer pronto, rode o **gate** (`laboratorio.gate`):
   - o dev e o holdout com 2 repetições cada;
   - o conjunto de regressão.
   - O gate passa só se **todos** os critérios forem atendidos: limite inferior do IC da acurácia, erros confiantes, % de revisão, F1 mínimo por classe, ECE, estabilidade entre repetições, nenhuma piora na regressão e tokens fixos dentro do limite.
   - O relatório do gate lista cada critério como aprovado ou reprovado, com o valor obtido.
7. Se passar, o desafiante vira o novo `campeao` (registro em `promocoes_prompt`: versão, data, métricas, quem aprovou) e fica liberado para a rodada total (seção 3.9). Se não passar, o relatório diz qual critério falhou.

**Referência de tamanho de amostra**, para os critérios fazerem sentido:

| Anexos | Meia-largura do IC 95% com acurácia de 95% | Com acurácia de 90% |
|---:|---:|---:|
| 500 | ±1,9 pp | ±2,6 pp |
| 1.000 | ±1,4 pp | ±1,9 pp |
| 2.000 | ±1,0 pp | ±1,3 pp |

Por classe, a incerteza é muito maior. Com 30 anexos por classe, só diferenças grandes são detectáveis. Por isso o gate usa o F1 por classe como piso e não como ranking.

**Janela de texto: quanto do anexo é preciso ler?**

Provavelmente não é preciso ler o anexo inteiro. As pistas das 3 classes ficam nas pontas:
- **início:** "ACÓRDÃO", "EMENTA", "Relator", "Vistos, relatados e discutidos" / "SENTENÇA", "Vistos" / "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ", "vem propor AÇÃO";
- **fim:** "acordam... por unanimidade", "negar provimento" / "JULGO PROCEDENTE", "P.R.I." / "dos pedidos", "dá-se à causa o valor", "OAB".

O meio (fundamentação, transcrições) é justamente onde está a confusão: um acórdão que transcreve a sentença, uma sentença que resume a inicial. Cortar o meio pode até ajudar. Cortar também reduz tokens, custo e TPM, que é o que limita a meta da seção 3.9.

O teste fica assim:
1. Com o campeão do prompt fixo, rode cada item de `laboratorio.janelas_teste` no mesmo `dev`, com `limpar_boilerplate` ligado e desligado em pelo menos uma janela.
2. Compare cada janela com `inteiro`:
   - acurácia e F1 **por classe**;
   - erros confiantes e confiança média;
   - tokens por anexo e latência;
   - a lista dos anexos que mudaram de classe.
3. Cruze com o tamanho do texto: anexos longos podem precisar de janela maior. Se for o caso, avalie uma janela proporcional ao tamanho.
4. Escolha a **menor janela que não piora nenhuma classe** dentro do IC.
5. A janela escolhida vira parte do campeão (`prompt_hash` + estratégia de janela) e passa pelo mesmo gate.

Antes do teste, use a distribuição de `chars` da etapa 3 para estimar a economia: com ~2,7 caracteres por token no OCR, um anexo de 30 mil caracteres tem ~11 mil tokens, e uma janela de 5.500 caracteres tem ~2 mil.

**O que não fazer:**
- ajustar o prompt olhando o holdout;
- comparar versões rodadas em dias diferentes sem rodar o campeão junto;
- aceitar ganho de acurácia que venha com aumento de erro confiante;
- deixar o prompt crescer sem olhar os tokens: cada token fixo se repete 130 mil vezes e reduz a vazão (seção 3.9).

### 3.9 Rodada total e meta de vazão: 130 mil anexos em até 5,8 minutos (`08_teste_vazao`)

As outras metodologias processaram cerca de 130 mil anexos em cerca de 5,8 minutos. **Primeiro confirme o que esse tempo inclui:** a leitura do texto, só a classificação, a gravação, o tamanho do cluster. O OCR já está feito antes, nos dois lados. O Decision-1 deve ser medido no **mesmo escopo**.

**Conta da meta**, com os números de referência:
- 130 mil / 5,8 min = **≈ 22.400 anexos/min ≈ 374 por segundo**;
- na referência, cada requisição simultânea rendeu cerca de 100 anexos/min (802/min com 8). Para a meta são precisas **≈ 210 a 260 requisições simultâneas** (latência de 0,55 a 0,69 s; aqui pode ser diferente);
- tokens, com a taxonomia de 3 classes (~1.000 fixos) e janela de ~4.000 a 6.000 caracteres: **≈ 2.500 a 3.200 por anexo, ≈ 325 a 420 milhões no total, ≈ 56 a 73 milhões por minuto** para a meta. Com a v1 de 22 classes e o texto inteiro, seriam ≈ 87 milhões por minuto ou mais. Provavelmente o limite que decide é a cota de tokens e requisições por minuto do deployment na Azure, não o código. Use os números medidos no laboratório, não estes;
- custo da rodada, no preço de referência: **≈ US$ 14 a 18**;
- extração: não entra na conta, porque o texto já vem do OCR. Ler 130 mil textos de uma tabela Delta leva segundos, então o relógio é praticamente só o da API.

**O que fazer para chegar lá:**

1. **Perguntar a cota** do deployment (RPM/TPM) e se dá para aumentar ou usar vários deployments/regiões (`escala.endpoints`, com distribuição entre eles).
2. **Teste de carga** em degraus (`degraus_teste_carga`, `docs_por_degrau` anexos cada). Em cada degrau, meça:
   - vazão;
   - p50, p95 e p99 da latência;
   - taxa de 429 e de erro.
   - Ache o joelho da curva, onde a vazão para de subir ou os 429 começam, e grave tudo em `teste_carga`, com gráfico de vazão × concorrência.
3. **Concorrência adaptativa** (AIMD):
   - começa em `concorrencia_inicial`;
   - sobe enquanto não houver 429;
   - corta pela metade quando houver 429, respeitando `Retry-After`;
   - nunca passa de `concorrencia_max`.
4. **Cliente enxuto:**
   - pool de conexões do tamanho da concorrência, com keep-alive (HTTP/2 se o endpoint aceitar);
   - a parte fixa da pergunta (taxonomia) serializada uma vez só;
   - JSON rápido (`orjson`);
   - textos lidos de `anexos_texto` em blocos, sem tudo na memória;
   - gravação em lotes de `escala.tamanho_lote_escrita` numa fila separada, para não travar as chamadas.
5. **Se um processo não der conta** (CPU do driver no limite antes da cota): divida os `anexo_id` em `shards` por hash e rode como tarefas paralelas do Job ou processos no driver, com a concorrência total dividida entre elas.
6. **Ensaio com `ClienteMock`** no volume total (130 mil, latência simulada de 0,55 s), para provar que o pipeline aguenta 374/s antes de gastar na API.
7. **Rodada total** com o campeão aprovado no gate (seção 3.8):
   - grava o tempo de parede do primeiro envio ao último registro gravado;
   - vazão por minuto ao longo da rodada;
   - 429, erros, custo e DBUs;
   - comparação com os 5,8 min no mesmo escopo.
   - A idempotência garante que uma queda no meio retoma sem refazer nada.
8. **Se a cota não permitir a meta**, o relatório diz qual cota seria necessária e quanto tempo levou com a cota atual. Encurtar a taxonomia (menos tokens fixos, medido no laboratório) também aumenta a vazão quando o limite é de TPM.

## 4. Regras

1. Prompt, parâmetros, execução e métricas ficam em lugares separados, como na seção 3. Nada de valor fixo de negócio em notebook.
2. A taxonomia não muda sem uma versão nova de arquivo. Toda classificação grava o `prompt_hash`.
3. Segredos só via `dbutils.secrets`.
4. Toda execução é reproduzível a partir de `execucoes.params_json`.
5. Erro de um anexo nunca derruba a execução: ele é gravado e entra na taxa de erro.
6. `src/metricas.py` usa funções puras (pandas/numpy) com testes, e os notebooks só as chamam.
7. Prefira o que o Databricks já oferece (Delta, MLflow, Jobs/Asset Bundles, AI/BI dashboard, Volumes) antes de criar infraestrutura própria.
8. Não invente detalhes da API ou da fonte. Procure primeiro nos notebooks e documentos de referência; se faltar informação, pergunte.
9. O material de referência não é alterado. O que for reaproveitado é copiado para `src/` com a origem citada.
10. Nada é criado ou alterado fora de `<<pasta_pessoal>>` e do schema pessoal. Na dúvida, pergunte.
11. Sem commit nem push automático.

## 5. Ordem de entrega (pare e mostre o resultado ao fim de cada etapa)

1. **Leitura do material de referência + perguntas.**
   - Leia os notebooks e documentos da seção 2c e entregue o `referencias/INVENTARIO.md`, com a fonte de cada informação e as divergências encontradas.
   - Depois liste só o que continuar faltando e espere as respostas:
     - da seção 2: API e fonte (tabela e colunas do texto de OCR);
     - da seção 3: caminho da pasta pessoal, schema pessoal e experimento do MLflow, se não estiverem preenchidos;
     - da seção 3.6: as metodologias A e B, os nomes das 3 classes nelas e se o corpus tem só esses 3 tipos;
     - da seção 3.8: rótulos disponíveis e critérios do gate;
     - da seção 3.9: o que os 5,8 min incluem e a cota do deployment.
2. **Estrutura + setup** dentro de `<<pasta_pessoal>>`: pastas, `params.yaml`, `src/config.py`, `src/prompt.py` (com o teste dos hashes `c4ffefc2e54f` e `f96ed8ee75b1`) e `00_setup` rodado.
   - Aceite:
     - tabelas criadas no schema pessoal;
     - o teste do hash passando;
     - `git status` mostrando mudanças só dentro de `<<pasta_pessoal>>`.
3. **Ingestão** do texto de OCR numa amostra de cerca de 50 anexos.
   - Aceite:
     - `anexos_texto` preenchida;
     - reportados a distribuição de tamanho (antes e depois da limpeza de boilerplate, por classe se houver rótulo) e o % de textos insuficientes;
     - a estimativa de tokens por anexo para cada janela de `janelas_teste`;
     - a segunda rodada não regrava nada.
4. **Classificação com `ClienteMock`** (realista, seção 2d) na mesma amostra.
   - Aceite: `classificacoes` e `execucoes` preenchidas; rodar de novo não duplica; derrubar no meio e retomar funciona.
5. **Classificação com a API real** na amostra de 50 (o conjunto todo fica para a etapa 10). **Depende da chave.** Enquanto ela não chega, deixe esta etapa pendente e siga para as próximas no modo sem chave (seção 2d), voltando aqui quando o secret existir.
   - Aceite:
     - zero erros não tratados;
     - tokens fixos medidos da `benchmark_3c_v1` (estimativa de ~1.000) + janela;
     - custo por mil anexos coerente com o preço;
     - a latência medida neste caminho reportada, sem compará-la com a da referência.
6. **Métricas + MLflow + dashboard.**
   - Aceite: todas as métricas da seção 3.5 calculadas para o `run_id` e uma comparação entre duas execuções funcionando.
7. **Benchmark** (seção 3.6) no `dev` do laboratório: valida a comparação com A e B antes da rodada total.
   - Aceite:
     - as três metodologias aparecem em `vw_benchmark_resumo` sobre o mesmo conjunto de anexos;
     - o custo está separado por componente, com o DBU vindo de `system.billing.usage`;
     - as repetições têm a variação reportada;
     - o mapeamento de classes está documentado;
     - os gráficos e o parágrafo de conclusão foram gerados.
8. **Conflitos e baixa confiança** (seção 3.7).
   - Aceite:
     - `casos_analise` é preenchida automaticamente a cada execução, com todos os sinais e a prioridade;
     - uma revisão simulada volta para `gabarito` e aparece nas visões;
     - o relatório de pares de confusão sai com exemplos;
     - uma `taxonomia_v2.json` de teste roda no `conjunto_regressao` e é comparada com a v1.
9. **Laboratório de prompts** (seção 3.8).
   - Aceite:
     - `dev`, `holdout` e `regressao` congelados, com a distribuição comparada à do universo;
     - o scorecard campeão × desafiante sai com IC, McNemar e a lista de anexos que mudaram;
     - o gate gera o relatório de aprovado/reprovado por critério;
     - uma promoção fica registrada.
   - Inclui o teste de janela de texto, com a janela escolhida.
   - A partir daqui, a equipe itera nas descrições e na janela. A etapa 10 só começa quando houver um campeão (prompt + janela) aprovado no gate. Sem chave, a infraestrutura fica pronta e validada com mock, e as rodadas reais ficam pendentes.
10. **Vazão e rodada total** (seção 3.9).
    - Primeiro o teste de carga e o ensaio com mock no volume total; depois os 130 mil anexos com o campeão.
    - Aceite: curva de vazão × concorrência, tempo de parede no mesmo escopo das outras metodologias, custo e erros. Ao fim, o benchmark (05) é atualizado com o resultado completo.
11. **Jobs** (Asset Bundle), parametrizados: 01 → 02 → 03 → 06; um job do 05; um job do 08.

## Anexo: taxonomia

Duas taxonomias fornecidas em `prompts/`, cada uma com as instruções e as classes (o que é, sinais típicos e com o que não confundir):

- `taxonomia_benchmark_3c_v1.json` (`prompt_hash` `f96ed8ee75b1`): `acordao`, `sentenca`, `peticao_inicial`, `outro`. É usada no benchmark.
- `taxonomia_v1.json` (`prompt_hash` `c4ffefc2e54f`): 22 classes (por exemplo `peticao_inicial`, `despacho`, `certidao`, `outro`).

Use exatamente as chaves de `classes` da taxonomia escolhida como valores válidos de `classe`.
