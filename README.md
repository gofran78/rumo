# Rumo

**Seu dinheiro, do passado ao futuro.**

O Rumo é um simulador de patrimônio que funciona inteiro no navegador. Ele junta, numa mesma linha do tempo:

- **Investimentos em fases**, amarradas umas às outras, com subfases, consolidação e comparação lado a lado.
- **Datas reais**: cada aporte rende a partir do dia em que entra, e o IR regressivo conta os dias de cada aporte.
- **Taxas reais do Banco Central** dia a dia (CDI, Selic, IPCA e poupança) para o passado, e a sua projeção para o futuro.
- **Gastos** à vista, financiados (Price ou SAC) ou recorrentes, com o custo de oportunidade de cada um.
- **Realizado × planejado**: o saldo do extrato comparado com o plano, e a projeção recomeçando do valor real.
- **Balanço**: todos os investimentos e gastos juntos, ano a ano.

Os cálculos de cada pessoa ficam salvos só no navegador dela. Nada é enviado para servidores.

> Simulação educativa, não é recomendação de investimento.

## Como o site é publicado

O site inteiro é o arquivo `index.html`. A automação em `.github/workflows/publicar.yml`:

1. publica a página no GitHub Pages sempre que algo muda no repositório;
2. nos dias úteis, às 19h23 (horário de Brasília), roda `scripts/atualizar_taxas.py`, que busca as séries no Banco Central, troca só o bloco de dados dentro do `index.html`, guarda a mudança no repositório e publica de novo.

Para atualizar as taxas na hora: aba **Actions** > **Publicar o Rumo** > **Run workflow**.

### Configuração (uma vez só)

1. **Settings** > **Pages** > em **Build and deployment**, escolha **Source: GitHub Actions**.
2. Para usar um domínio próprio: **Settings** > **Pages** > **Custom domain**, e no registro do domínio aponte o DNS para o GitHub Pages, conforme as instruções que aparecem nessa tela.

## Fontes de dados

Banco Central do Brasil, Sistema Gerenciador de Séries Temporais (SGS):

| Série | O que é |
|---|---|
| 12 | CDI diário |
| 11 | Selic diária |
| 433 | IPCA mensal |
| 195 | Rendimento da poupança por data de aniversário |
| 432 | Meta da Selic |

O script usa só a biblioteca padrão do Python e não mexe no arquivo se alguma série falhar ou vier com menos dados do que já havia.
