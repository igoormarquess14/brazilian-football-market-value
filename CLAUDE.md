# CLAUDE.md

## Projeto

TCC em Ciências Econômicas (UFSC), já defendido: **Mensuração de Determinantes de Valor no Mercado de Transferências do Futebol Brasileiro**.

Amostra: jogadores do Campeonato Brasileiro Série A 2025. Fontes: Transfermarkt e FBref. Estimação original feita no Gretl. Este repositório reproduz essa estimação em Python, documenta o pipeline e publica o resultado como projeto aberto.

O trabalho está concluído e aprovado. O objetivo aqui não é revisar a pesquisa, é torná-la reprodutível e legível por terceiros.

## Fonte de verdade

Ordem de autoridade, sem exceção:

1. A monografia final (PDF em `docs/`). As tabelas impressas nela são o resultado oficial.
2. Arquivos e saídas do Gretl.
3. Scripts Python existentes.

Se divergirem, a monografia decide e a divergência é documentada em `docs/divergencias.md`. Nenhum resultado da monografia é "corrigido" neste repositório.

## Regras invioláveis

- Não alterar nada em `data/raw/`.
- Não inventar especificação econométrica. A especificação é a que está na monografia.
- Não substituir resultado sem antes reproduzir e comparar.
- Nenhum `git push` sem minha autorização explícita, toda vez.
- Nenhum token, senha ou credencial em arquivo do repositório.
- Não apagar script antigo. Mover para `legacy/` e registrar o motivo no commit.
- Não afirmar que algo funciona sem ter executado.

## Critério de reprodução

Um modelo está reproduzido quando, contra a tabela da monografia:

- N idêntico (exato, não aproximado)
- coeficientes com erro relativo abaixo de 1e-4
- erros padrão com erro relativo abaixo de 1e-3
- R² e R² ajustado iguais até a 4ª casa

Fora disso é bug, não arredondamento. Ordem de investigação, nesta sequência: amostra efetiva após missing, transformação da variável, categoria base das dummies, tipo de erro padrão, presença de intercepto.

Nota sobre erros padrão: no Gretl, `--robust` em corte transversal usa HC1 por padrão, controlado por `set hc_version`. O equivalente em statsmodels é `.fit(cov_type="HC1")`. Confirmar no cabeçalho do output do Gretl antes de assumir.

## Padrões de código

- Python, pandas, statsmodels. Nada de scikit-learn se a monografia não usa.
- Caminhos via `pathlib` a partir de `PROJECT_ROOT`. Nenhum caminho absoluto.
- Recorte de amostra sempre explícito: `df.dropna(subset=vars_do_modelo)`. Nunca `df.dropna()`.
- Funções só quando eliminam repetição real. Sem classes, sem camada de config, sem abstração antecipada.
- Scripts numerados, executáveis em ordem, idempotentes.
- Todo script grava output em `outputs/`. Nada existe só no console.

## Language

Documentation, README, and comments in English. File names, variables, and commit messages in English. The exceptions: the thesis PDF stays in Portuguese (it's the original defended document, not a repository artifact to translate), and data column names (`Clube`, `Player`, `Value_Num`, `age_centered`, `fb_xG(+/-)`, etc.) are never translated — `session.inp` and the reproduction depend on them matching exactly. Content inside `legacy/` (frozen historical scripts) is not translated either — see `legacy/README.md`.

## Dados e publicação

Transfermarkt e FBref não licenciam redistribuição de dados raspados. Antes de versionar qualquer base, me perguntar.

Default: `data/raw/` fica no `.gitignore`. `data/processed/` é avaliado caso a caso. `docs/data_sources.md` explica origem, data de coleta e como reobter.

Os scripts de scraping provavelmente não rodam mais (estrutura das páginas muda). O README deve dizer isso explicitamente. O ponto de entrada reprodutível é a base processada, não a coleta.

## Protocolo

- Antes de mudança estrutural: diagnóstico, plano, minha aprovação, execução.
- Depois de refatorar: rodar de novo e mostrar que o output é idêntico ao anterior.
- Terminologia econométrica consistente com Stock & Watson e Gujarati & Porter.
- Progresso e pendências ficam em `PLAN.md`, nunca neste arquivo.
