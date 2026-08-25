# API de Cotações de Ações (grátis, hospedada 100% no GitHub)

Serviço gratuito que publica cotações de ~28 ações (B3 + EUA) como arquivos
JSON estáticos, atualizados automaticamente a cada 15 minutos por um
GitHub Action, e servidos pelo GitHub Pages. Não precisa de nenhum servidor,
conta em nuvem paga ou chave de API.

As cotações vêm do Yahoo Finance e têm um atraso natural de aproximadamente
15 a 20 minutos em relação ao mercado — o que já atende ao pedido de uma
cotação "com delay".

## Como funciona

1. `scripts/tickers.json` lista os tickers acompanhados (edite à vontade).
2. O workflow `.github/workflows/update-quotes.yml` roda a cada 15 minutos
   (e também pode ser disparado manualmente), executa `scripts/fetch_quotes.py`,
   e faz commit/push dos arquivos JSON atualizados em `docs/api/`.
3. O GitHub Pages serve a pasta `docs/` como um site estático — os arquivos
   `.json` dentro dela funcionam como endpoints de API somente-leitura.

## Passo a passo para colocar no ar

1. **Crie um repositório novo e vazio no GitHub** (público, para poder usar o
   Pages gratuito), por exemplo `stock-quotes-api`.
2. **Suba estes arquivos** para o repositório (extraia o zip e faça o commit
   inicial):
   ```bash
   cd stock-quotes-api
   git init
   git add .
   git commit -m "primeira versão da API de cotações"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/stock-quotes-api.git
   git push -u origin main
   ```
3. **Dê permissão de escrita para o Actions:** em *Settings → Actions →
   General → Workflow permissions*, selecione **"Read and write
   permissions"** e salve. Sem isso, o Action não consegue commitar as
   cotações atualizadas.
4. **Ative o GitHub Pages:** em *Settings → Pages*, em "Build and
   deployment" escolha **Source: Deploy from a branch**, branch **main**,
   pasta **/docs**, e salve.
5. **Rode o workflow uma primeira vez manualmente:** aba *Actions* → workflow
   "Atualizar cotações" → *Run workflow*. Isso popula `docs/api/` com dados
   reais antes mesmo do próximo agendamento automático.
6. Aguarde 1–2 minutos para o Pages publicar e acesse:
   - `https://SEU-USUARIO.github.io/stock-quotes-api/` (página de status)
   - `https://SEU-USUARIO.github.io/stock-quotes-api/api/quotes.json` (todas as ações)
   - `https://SEU-USUARIO.github.io/stock-quotes-api/api/quotes/PETR4.json` (uma ação)
   - `https://SEU-USUARIO.github.io/stock-quotes-api/api/tickers.json` (lista de tickers)

A partir daí, o Action roda sozinho a cada 15 minutos e mantém os arquivos
atualizados — não precisa fazer mais nada.

## Adicionar ou remover ações

Edite `scripts/tickers.json`. Para ações da B3, use o ticker com sufixo
`.SA` no campo `yahoo` (ex.: `"yahoo": "VALE3.SA"`). Para ações dos EUA (ou
de outras bolsas), use o ticker como aparece no Yahoo Finance, sem sufixo
(ex.: `"yahoo": "AAPL"`). O campo `symbol` é o nome usado no endpoint
(`/api/quotes/<symbol>.json`) — mantenha-o único.

## Limitações e avisos importantes

- **Não é dado em tempo real** — nem deveria ser, já que o pedido original é
  por cotação com atraso. O Yahoo Finance atrasa em torno de 15–20 minutos.
- **Fonte não oficial:** o Yahoo Finance não garante um SLA para esse uso;
  em caso de mudança no formato interno deles, o script pode passar a falhar
  para alguns ou todos os tickers. Os logs de cada execução ficam disponíveis
  na aba *Actions* do repositório — é o primeiro lugar para checar se algo
  parar de funcionar.
- **Falha isolada por ticker:** se um ticker específico falhar, o JSON dele
  mostra `"error"` preenchido e `"price": null`, mas os demais tickers
  continuam sendo publicados normalmente.
- **Não use para decisões de negociação em tempo real** — é um projeto
  informativo/hobby, não uma fonte de dados financeiros profissional.
- O GitHub desativa workflows agendados após 60 dias sem nenhuma atividade
  no repositório; como este workflow faz commits regularmente, ele deve
  continuar rodando indefinidamente enquanto estiver funcionando.

## Estrutura dos arquivos

```
.github/workflows/update-quotes.yml   → o agendador (roda a cada 15 min)
scripts/tickers.json                  → lista de ações acompanhadas (edite aqui)
scripts/fetch_quotes.py               → script que busca as cotações
docs/index.html                       → página de status simples
docs/api/quotes.json                  → todas as cotações (gerado automaticamente)
docs/api/quotes/<SYMBOL>.json         → cotação individual (gerado automaticamente)
docs/api/tickers.json                 → metadados dos tickers (gerado automaticamente)
```
