Obrigado pelo inventário. Por enquanto quero só o ESQUELETO do projeto: código, estrutura e testes com mock. Os experimentos reais (rodadas, benchmark, rotulagem, medições de tempo e custo) ficam para quando eu tiver acesso à API.

Três mudanças na especificação:

A) TAXONOMIA: use prompts/taxonomia_benchmark_3c_v1.json (acordao, sentenca, peticao_inicial, outro; prompt_hash f96ed8ee75b1, mesmo cálculo da v1).
- A v1 de 22 classes fica disponível por parâmetro (prompt.versao), mas o padrão é a de 3.
- Grave a versão da taxonomia em execucoes e classificacoes e nunca misture taxonomias nas métricas.

B) JANELA DE TEXTO: os textos são grandes demais para ir inteiros. Implemente:
- remoção das linhas repetidas entre páginas (carimbos, rodapés, "Assinado eletronicamente"), mantendo a primeira ocorrência, antes do corte;
- prompt.janela = inicio | inicio_fim | inteiro, com janela_inicio_chars e janela_fim_chars (padrão inicio_fim, 4000 + 1500);
- separador entre trechos: "\n\n[... trecho omitido ...]\n\n". Grave a estratégia e os tamanhos usados em cada classificação;
- no laboratório, a opção de comparar várias janelas no mesmo dev (inicio 2000, inicio 4000, inicio_fim 3000+1000, 4000+1500, 8000+3000 e inteiro).

C) SEM CHAVE: modelo.cliente = mock.
- O mock tem que ser realista: maioria confiante, alguns casos com probabilidade dividida entre 2 classes, latência simulada (~0,55 s com cauda), alguns 429 e timeouts, tokens estimados pelo tamanho do texto.
- Execuções mock gravam provedor='mock' e nunca entram em benchmark, gate ou métrica de qualidade.
- Implemente o cliente real também, testado só com o JSON de referência.

Respostas que importam agora:

- Schema: use o schema do projeto, d4852s091_id_people. Não crie schema, volume nem catálogo. Como o schema é compartilhado com outros projetos:
  - todas as tabelas e views deste experimento usam o prefixo clf_anexos_ (ex.: clf_anexos_execucoes, clf_anexos_classificacoes);
  - antes de criar qualquer tabela, confira se o nome já existe; se existir, pare e me pergunte;
  - nunca faça DROP, TRUNCATE, ALTER ou escrita em tabela que não tenha esse prefixo. As tabelas da equipe (texto, saídas de regex e SVM) são só leitura;
  - se faltar permissão para criar tabela, me diga qual permissão falta e pare, sem tentar alternativas.
- MLflow: use um experimento dentro da minha pasta do workspace.
- Fonte: ac_texto_anexos_amostra, chave `arquivo`, só leitura.
- Classes do regex: proponha o mapeamento das 5 para as 3 + outro, só como configuração. A validação fica para depois.
- O resto (cota da API, rotulagem, cluster dos 5,8 min, valores de negócio, as 274 linhas a mais, os outros notebooks) fica como pendência no INVENTARIO.md, sem bloquear.

O que entregar:
- Etapas 2 a 4 completas: estrutura, setup, ingestão de uma amostra pequena e classificação com mock.
- O código das etapas 6 a 10 (métricas, benchmark, conflitos, laboratório, teste de vazão) escrito e rodando de ponta a ponta com mock numa amostra pequena, sem rodadas grandes.
- No fim, um checklist do que falta para ligar a API real: preencher o secret, mudar modelo.cliente para real e rodar a etapa 5.

Atualize o INVENTARIO.md com isso e siga. Pare ao fim de cada etapa e me mostre o resultado.
