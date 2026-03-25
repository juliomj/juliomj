# Pokémon Card Price Comparator (Liga Pokémon x MYP Cards)

Projeto profissional para comparar preços de cartas Pokémon entre Liga Pokémon e MYP Cards com integração ao Google Sheets.

## 1) Resumo executivo da solução escolhida

### Decisão arquitetural
**Escolha:** **Arquitetura híbrida** com **backend Python (FastAPI)** para scraping/matching/comparação e **Google Apps Script** como cliente/orquestrador no Sheets.

### Por que essa foi a melhor opção
- **Confiabilidade:** scraping e lógica crítica fora do Apps Script (menos timeout por célula).
- **Manutenção:** conectores separados por fonte + camadas coesas.
- **Facilidade para usuário final:** função customizada `=COMPARAR_CARTA(...)` + menu de lote.
- **Resiliência:** retry/backoff, cache TTL, rate limit, parsers defensivos.
- **Escala futura:** endpoint batch, métricas estendidas, fallback headless futuro.

## 2) Arquitetura proposta

```text
Google Sheets
  └─ Apps Script
      ├─ COMPARAR_CARTA(nome, condicao, edicao)
      └─ Menu: processamento em lote
            ↓
         FastAPI Backend
            ├─ API layer (/compare, /compare/batch)
            ├─ Service layer (comparação e decisão)
            ├─ Matching layer (fuzzy + edição + condição + número)
            ├─ Connector: Liga Pokémon
            ├─ Connector: MYP Cards
            ├─ Core: config, logging, cache, rate limit
            └─ Tests (unit + integração simulada)
```

## 3) Estrutura de pastas

```text
app/
  connectors/
    base.py
    liga.py
    myp.py
  core/
    cache.py
    logging.py
    rate_limit.py
    settings.py
  models/
    schemas.py
  parsers/
    normalization.py
  services/
    comparator.py
    matching.py
  sheets/
    apps_script.gs
  main.py
scripts/
  example_sheet_rows.csv
tests/
  unit/
    test_matching.py
    test_normalization.py
  integration/
    test_comparator_service.py
.env.example
requirements.txt
README.md
```

## 4) Código completo dos arquivos

Todos os arquivos já foram gerados no repositório local com implementação real (sem pseudocódigo).

### Principais decisões técnicas implementadas
- **Preço de referência por fonte:** menor preço válido da carta correta e condição correta.
- **Matching:** score ponderado (nome + edição + número + condição) com fuzzy controlado.
- **Status padronizados:** AMBÍGUO, EDIÇÃO NÃO ENCONTRADA, CONDIÇÃO NÃO ENCONTRADA, ERRO TEMPORÁRIO, CARTA NÃO ENCONTRADA.
- **Regra de decisão atual + futura:**
  - Atual: MYP < Liga => SIM; senão NÃO; faltando preço => DADOS INSUFICIENTES.
  - Futuro: threshold mínimo de economia (%), via parâmetro/ENV.
- **Resiliência:** retry com backoff, cache TTL por chave `(nome+condicao+edicao+threshold)`, rate limit por minuto.

## 5) Instruções de instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verificação:
```bash
curl http://localhost:8000/health
```

## 6) Instruções de uso no Google Sheets

### Opção escolhida: combinação função + lote
- **Função customizada:** `=COMPARAR_CARTA(A2;B2;C2)` (retorna colunas D:L)
- **Menu customizado:** “Pokémon Price”
  - Processar linha atual
  - Processar lote (linhas selecionadas)

### Passo a passo
1. Abra o Google Sheets e vá em **Extensões > Apps Script**.
2. Cole o conteúdo de `app/sheets/apps_script.gs`.
3. Em **Project Settings > Script Properties**, configure:
   - `API_BASE_URL` (ex: `https://seu-backend.com`)
   - `API_TOKEN` (opcional, placeholder de segurança)
4. Na planilha:
   - A: NOME DA CARTA
   - B: CONDIÇÃO DA CARTA
   - C: EDIÇÃO DA CARTA
5. Use fórmula ou menu para preencher D:L.

### Saídas (D:L)
- D `preco_liga`
- E `preco_myp`
- F `diferenca_reais`
- G `diferenca_percentual`
- H `melhor_opcao`
- I `vale_a_pena_comprar_no_myp`
- J `status_log`
- K `url_liga`
- L `url_myp`

## 7) Testes

### Unitários
- normalização de texto/condição/preço
- regra de matching e escolha do melhor resultado

### Integração simulada
- cenário MYP mais barato
- condição não encontrada
- edição não encontrada

Rodar:
```bash
pytest -q
```

## 8) QA e critérios de aceite (cobertos)

- ✅ cenário MYP mais barato
- ✅ cenário de condição inválida/não encontrada
- ✅ cenário de edição divergente
- ✅ status claros por fonte
- ✅ cálculo de diferença em R$ e %
- ✅ decisão “vale a pena comprar no MYP?”
- ✅ estrutura modular, tipada e testável
- ✅ integração Google Sheets pronta

## 9) Estratégia de logs e observabilidade

- `structlog` com saída JSON (timestamp + nível + evento).
- logs de falha de fonte (`search_error`) com origem e erro.
- `status_log` por linha para auditoria funcional na planilha.

## 10) Pontos frágeis de scraping e mitigação

Como não há API oficial pública garantida para os marketplaces, foi implementado scraping defensivo com múltiplos seletores CSS por campo.

Mitigações:
1. seletores alternativos para nome/preço/edição/condição;
2. fallback por parsing de texto quando condição não estiver explícita;
3. retry com backoff para indisponibilidade temporária;
4. cache para reduzir chamadas repetidas;
5. camada de conector isolada por fonte para atualização rápida.

## 11) Melhorias futuras

- fallback opcional com Playwright quando HTML estático falhar;
- autenticação forte da API (JWT/API Gateway);
- Redis para cache distribuído;
- filas assíncronas para lotes grandes;
- métricas avançadas: mediana, dispersão, número de anúncios válidos, confiança de match;
- exclusão mais robusta de produtos fora de escopo (lote/deck/acessórios).

## Exemplo de chamada da API

### Linha única
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{"nome":"Pikachu 001/025","condicao":"NM","edicao":"Celebrations"}'
```

### Lote
```bash
curl -X POST http://localhost:8000/compare/batch \
  -H "Content-Type: application/json" \
  -d '{"items":[{"nome":"Pikachu 001/025","condicao":"NM","edicao":"Celebrations"}]}'
```
