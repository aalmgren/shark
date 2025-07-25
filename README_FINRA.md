# 📊 Análise de Volume FINRA vs Dark Pool

Este script Python baixa dados do FINRA (Financial Industry Regulatory Authority) para comparar o volume negociado de uma ação específica com o volume de vendas a descoberto (dark pool) ao longo dos últimos dias.

## 🚀 Funcionalidades

- **Baixa dados do FINRA**: Volume de vendas a descoberto por ação
- **Dados do Yahoo Finance**: Volume de mercado para comparação
- **Análise comparativa**: Calcula ratios e percentuais
- **Visualizações**: Gráficos detalhados da análise
- **Exportação**: Salva dados em CSV e gráficos em PNG

## 📋 Pré-requisitos

Certifique-se de ter Python 3.8+ instalado.

## 🔧 Instalação

1. Clone ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## 💻 Como Usar

### Uso Básico

Para analisar uma ação específica (ex: AAPL):

```bash
python finra_volume_comparison.py AAPL
```

### Uso Avançado

Para especificar número de dias:

```bash
python finra_volume_comparison.py AAPL --days 60
```

### Modo Exemplo

Execute sem argumentos para ver exemplo com AAPL:

```bash
python finra_volume_comparison.py
```

## 📊 O que o Script Faz

1. **Baixa dados do FINRA**:
   - Volume de vendas a descoberto
   - Volume total reportado ao FINRA
   - Volume de vendas a descoberto isentas

2. **Baixa dados do Yahoo Finance**:
   - Volume de mercado oficial
   - Preços de fechamento

3. **Combina e analisa**:
   - Calcula percentual de vendas a descoberto
   - Compara volume FINRA vs volume de mercado
   - Calcula ratio de dark pool

4. **Gera visualizações**:
   - Comparação de volumes ao longo do tempo
   - Percentual de vendas a descoberto
   - Correlação entre volumes
   - Ratio dark pool vs mercado

5. **Salva resultados**:
   - Arquivo CSV com dados detalhados
   - Gráfico PNG com visualizações

## 📈 Interpretação dos Resultados

### Métricas Principais

- **Volume de Vendas a Descoberto**: Ações vendidas sem posse (short selling)
- **Dark Pool Ratio**: Percentual do volume de mercado que passou por dark pools
- **Volume FINRA vs Yahoo**: Comparação entre dados reportados

### Indicadores Importantes

- **Alto percentual de vendas a descoberto**: Possível pressão de venda
- **Discrepância entre volumes**: Pode indicar atividade em dark pools
- **Correlação forte**: Volumes seguem padrões similares

## 🔍 Exemplo de Saída

```
🚀 INICIANDO ANÁLISE DE AAPL
============================================================

🔍 Buscando dados do FINRA para AAPL...
  ✓ Dados encontrados para 2025-01-14
  ✓ Dados encontrados para 2025-01-15
  ...
✓ 20 dias de dados processados para AAPL

📊 Buscando dados do Yahoo Finance para AAPL...
✓ 25 dias de dados do Yahoo Finance obtidos

🔄 Combinando e analisando dados...

📈 ANÁLISE DE VOLUME PARA AAPL
==================================================
Período analisado: 2024-12-20 a 2025-01-14
Dias com dados: 18

VOLUME MÉDIO:
  • Volume de mercado (Yahoo): 45,232,841
  • Volume FINRA total: 23,891,234
  • Volume de vendas a descoberto: 12,456,789

PERCENTUAIS MÉDIOS:
  • Vendas a descoberto do total: 52.1%
  • Dark pool vs mercado: 27.5%
  • Volume FINRA vs Yahoo: 52.8%
```

## 📁 Arquivos Gerados

- `finra_data_aapl_20250114_1430.csv`: Dados detalhados
- `finra_analysis_aapl_20250114_1430.png`: Gráficos de análise

## ⚠️ Limitações

1. **Dados do FINRA**: Podem ter atraso ou não estar disponíveis para todos os dias
2. **API Rate Limiting**: Script inclui delays para evitar limitações
3. **Dark Pools**: Nem todo volume off-exchange é necessariamente dark pool
4. **Fins de semana**: Dados não estão disponíveis para sábados e domingos

## 🛠️ Solução de Problemas

### Erro "Nenhum dado encontrado"
- Verifique se o símbolo da ação está correto
- Alguns símbolos podem não ter dados FINRA disponíveis
- Tente com um período menor de dias

### Erro de conexão
- Verifique sua conexão com a internet
- A API do FINRA pode estar temporariamente indisponível

### Erro de dependências
- Execute: `pip install -r requirements.txt --upgrade`

## 📝 Notas Importantes

- **Uso Educacional**: Este script é para fins educacionais e de pesquisa
- **Não é Conselho Financeiro**: Os dados não devem ser usados como única base para decisões de investimento
- **Conformidade**: Respeite os termos de uso das APIs do FINRA e Yahoo Finance

## 🤝 Contribuições

Sinta-se à vontade para contribuir com melhorias, correções de bugs ou novas funcionalidades!

## 📄 Licença

Este projeto é de código aberto. Use com responsabilidade.