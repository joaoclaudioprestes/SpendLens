# SpendLens — Backlog de Implementação

## Fase 0 — Setup

- [X] Criar repositório `spendlens`
- [X] Estrutura de pastas (PyPA-compliant):
  
  ```txt
  spendlens/
  ├── src/
  │   ├── extractors/      # Parsers por schema (Nubank, Itaú, OFX)
  │   ├── transformers/    # Normalização para schema canônico
  │   ├── classifiers/     # Regras de categorização via YAML
  │   ├── loaders/         # Carga no SQLite
  │   ├── queries/         # SQL analítico puro
  │   ├── reporters/       # Geração de relatório CSV/Markdown
  │   ├── cli/             # Comandos CLI
  │   └── __init__.py
  ├── tests/
  ├── data/
  │   ├── samples/         # CSVs fictícios gerados manualmente
  │   └── rules.yaml       # Regras de classificação
  ├── pyproject.toml
  └── README.md
  ```

- [X] `pyproject.toml` com dependências: `click`, `rich`, `pyyaml`
- [X] Entrypoint CLI via `[project.scripts]`
- [X] Gerar dados fictícios: 2 arquivos CSV simulando Nubank e Itaú (≥ 50 transações cada, schemas diferentes)

---

## Fase 1 — Extractors

**Objetivo:** ler arquivos CSV brutos com validação e robustez.

- [X] Definir os dois schemas de entrada:
  - Nubank: `Data,Descrição,Valor` (valor negativo = despesa)
  - Itaú: `data_lancamento,historico,valor,tipo` (tipo: C/D)
- [X] `NubankExtractor`: lê CSV, retorna `ExtractionResult` com metadados
- [X] `ItauExtractor`: lê CSV, retorna `ExtractionResult` com metadados
- [X] Interface abstrata `BaseExtractor` com método `extract(filepath) -> ExtractionResult`
- [X] `GenericCSVExtractor`: implementação robusta com error handling, encoding detection, deduplication
- [X] Testes: 21 casos cobrindo validação, duplicatas, encoding, erros, edge cases
  - ✅ Testes básicos (leitura, campos, duplicatas)
  - ✅ Testes de encoding (UTF-8, Latin-1, BOM)
  - ✅ Testes de erro (arquivo não encontrado, permissão, malformado)
  - ✅ Testes de integração (ambos extractors)

---

## Fase 2 — Transformers

**Objetivo:** normalizar qualquer schema bruto para o schema canônico.

Schema canônico: `(date: date, description: str, value: float, type: str, source: str)`

- [X] `NubankTransformer`: converte dict bruto → schema canônico (inferir tipo pelo sinal do valor)
- [X] `ItauTransformer`: converte dict bruto → schema canônico (mapear C/D → receita/despesa)
- [X] Validações: rejeitar linhas com `value == 0`, data inválida, campos obrigatórios ausentes
- [X] Testes unitários — 24 casos:
  - [X] Linha válida Nubank → schema canônico correto (sign inference, normalization)
  - [X] Linha válida Itaú → schema canônico correto (DD/MM/YYYY parsing, C/D mapping)
  - [X] Linha com data inválida → exceção com mensagem clara
  - [X] Linha com valor zero → exceção com mensagem clara
  - [X] Campos faltantes → exceção listando campos obrigatórios
  - [X] Tipos inválidos → exceção apropriada
  - [X] Integração com Phase 1 ExtractionResult
  - [X] Edge cases: encoding, whitespace, invalid date values

---

## Fase 3 — Classifier

**Objetivo:** atribuir categoria a cada transação por regras de palavras-chave.

- [X] Criar `data/rules.yaml` com 8 categorias e 40+ palavras-chave:

  ```yaml
  alimentacao:
    keywords: [supermercado, ifood, restaurante, padaria, açaí, mercado, comida]
  transporte:
    keywords: [uber, 99, combustivel, estacionamento, taxi, ônibus, metrô]
  # ... 6 mais categorias (moradia, utilities, entretenimento, saude, compras, outros)
  ```

- [X] `RuleClassifier`: carrega YAML, recebe description, retorna categoria (ou "outros" se sem match)
- [X] Match case-insensitive, busca substring
- [X] 25 testes:
  - [X] Carregamento YAML (válido, inválido, arquivo não encontrado)
  - [X] Descrição com keyword exata → categoria correta
  - [X] Descrição sem match → "outros"
  - [X] Descrição com keyword em caixa alta → match correto
  - [X] Substring matching (keyword parcial em descrição)
  - [X] Edge cases (vazio, whitespace, caracteres especiais, unicode, números, descrições longas)
  - [X] Integração com Phase 2 Transformers

---

## Fase 4 — Loaders e Schema SQL

**Objetivo:** modelagem relacional real e carga idempotente.

- [X] Escrever e documentar o schema SQL:

  ```sql
  -- origens: nubank, itau, etc.
  -- categorias: alimentacao, transporte, etc.
  -- transacoes: tabela principal com FKs
  ```

- [X] `SchemaManager`: cria as tabelas se não existirem
- [X] `TransactionLoader`: insere transações; usar hash `(data + descricao + valor + origem)` como chave de deduplicação
- [X] Teste de idempotência: ingerir o mesmo CSV duas vezes → mesmo número de registros no banco

---

## Fase 5 — CLI `ingest`

**Objetivo:** comando end-to-end de ingestão.

- [X] `spendlens ingest <arquivo> --banco nubank|itau`
  - Extrai → Transforma → Classifica → Carrega
  - Exibe com `rich`: total ingerido, duplicatas ignoradas, erros
- [X] Teste de integração: rodar `ingest` com CSV sample → verificar registros no banco

---

## Fase 6 — Queries Analíticas

**Objetivo:** SQL analítico puro, sem ORM.

Cada query em arquivo `.sql` separado **e** em `queries/analytics.py` como função que recebe `conn` e retorna `list[dict]`.

- [X] `total_por_categoria_mes.sql` — GROUP BY categoria, mês
- [X] `media_movel_3meses.sql` — média dos últimos 3 meses por categoria (window function ou subquery)
- [X] `top5_maiores_gastos.sql` — top 5 despesas do período filtrado
- [X] `mes_maior_variacao_saldo.sql` — receitas - despesas por mês, ordenado por variação absoluta
- [X] Testes: cada query executada contra banco populado com fixtures → assert nos valores esperados

---

## Fase 7 — Reporters

**Objetivo:** gerar relatório legível a partir das queries.

- [ ] `ReportService`: executa todas as queries analíticas e agrega resultados
- [ ] `CsvReporter`: exporta cada query como CSV separado em `output/`
- [ ] `MarkdownReporter`: gera `report.md` com tabelas formatadas e seção por query
- [ ] Teste: `MarkdownReporter` gera arquivo com conteúdo não vazio e estrutura correta

---

## Fase 8 — CLI `report`

- [ ] `spendlens report --month 2025-05 [--csv] [--output ./output]`
  - Sem `--month`: usa mês atual
  - Exibe resumo no terminal com `rich`
  - `--csv` exporta arquivos em `output/`
- [ ] Teste de integração: banco populado → `report` → verificar arquivos gerados

---

## Fase 9 — Testes e Cobertura

- [ ] Fixture global: banco SQLite temporário populado com 100 transações fictícias (spread em 3 meses, 3 origens, 5 categorias)
- [ ] Cobertura ≥ 85% em `transformers/`, `classifiers/`, `queries/`
- [ ] Rodar `pytest --cov` e corrigir lacunas

---

## Fase 10 — CI e Documentação

- [ ] GitHub Actions: lint (`ruff`) + `pytest --cov` a cada push/PR
- [ ] README:
  - Diagrama do pipeline (Mermaid): `CSV → Extractor → Transformer → Classifier → Loader → SQLite → Queries → Reporter`
  - Schema SQL documentado
  - Exemplos de uso dos dois comandos CLI
  - Instruções de instalação
  