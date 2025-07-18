# 🦈 Shark Detection - Streamlit App

Uma aplicação web interativa para detectar padrões de acumulação institucional através de análise de volume e preço.

## 🚀 Como Usar

### 1. Instalação das Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
streamlit run streamlit_sharks.py
```

A aplicação abrirá automaticamente no seu navegador em `http://localhost:8501`

### 3. Workflow da Aplicação

1. **Carregar Tickers**: A aplicação carrega automaticamente o arquivo `tickers.csv` ou você pode fazer upload de um novo
2. **Download dos Dados**: Clique em "📥 Download Today's Data" para baixar os dados mais recentes
3. **Configurar Parâmetros**: Ajuste os filtros na barra lateral conforme necessário
4. **Executar Análise**: Clique em "🔍 Run Shark Analysis" para detectar os sharks

## ⚙️ Parâmetros Configuráveis

### Volume & Liquidez
- **Min daily volume (USD)**: Volume mínimo diário em USD (padrão: $10M)
- **Volume spike ratio**: Razão mínima de volume 7d vs 90d (padrão: 1.5x)
- **Spike detection multiplier**: Multiplicador para detectar spikes de volume (padrão: 2.0x)

### Filtros de Preço
- **Min average price (90d)**: Preço médio mínimo em 90 dias (padrão: $5.00)
- **Min current price**: Preço atual mínimo (padrão: $10.00)

### Filtros de Performance
- **Allow negative performance**: Incluir ações com performance negativa (padrão: Não)
- **Silent sharks threshold**: Limite máximo de variação para silent sharks (padrão: 5%)

### Outros Filtros
- **Min data days**: Mínimo de dias de dados históricos (padrão: 90)
- **Filter derivatives**: Filtrar derivativos como warrants, units, etc. (padrão: Sim)
- **Enable pattern detection**: Rejeitar ações em queda após spikes de volume (padrão: Sim)

## 📊 Resultados

### Categorias de Sharks
- **🔥 Mega Sharks**: Volume 3x+ acima da média
- **⚡ Big Sharks**: Volume 2-3x acima da média  
- **🦈 Regular Sharks**: Volume 1.5-2x acima da média
- **🤫 Silent Sharks**: Volume elevado com variação de preço ≤ 5%

### Visualizações
- **Distribuição de Volume Ratio**: Histograma mostrando a distribuição dos ratios de volume
- **Volume vs Variação de Preço**: Scatter plot correlacionando volume e performance
- **Tabelas Interativas**: Rankings dos sharks detectados com métricas detalhadas

### Downloads
- **All Sharks CSV**: Todos os sharks detectados
- **Silent Sharks CSV**: Apenas os silent sharks

## 🏗️ Estrutura de Arquivos

```
IBKR/
├── streamlit_sharks.py          # Aplicação principal Streamlit
├── shark_analyzer.py            # Engine de análise parametrizada
├── download_all_data.py         # Script de download (existente)
├── analyze_sharks.py            # Script original (mantido)
├── requirements.txt             # Dependências Python
├── tickers.csv                  # Lista de tickers para análise
├── nasdaq_database/             # Dados baixados do NASDAQ
├── additional_database/         # Dados adicionais
└── README_STREAMLIT.md         # Esta documentação
```

## 🎯 Vantagens da Interface Streamlit

1. **Experimentação Rápida**: Teste diferentes parâmetros sem editar código
2. **Visualização em Tempo Real**: Veja o impacto dos filtros instantaneamente
3. **Interface Amigável**: Não precisa conhecer Python para usar
4. **Logs Interativos**: Acompanhe o progresso da análise em tempo real
5. **Exportação Fácil**: Download direto dos resultados em CSV
6. **Histórico de Execuções**: Compare resultados de diferentes configurações

## 🔧 Solução de Problemas

### Erro "No module named 'streamlit'"
```bash
pip install streamlit
```

### Erro "No data available"
1. Verifique se existe `tickers.csv` no diretório
2. Execute o download dos dados primeiro
3. Verifique se os diretórios `nasdaq_database` ou `additional_database` existem

### Análise muito lenta
1. Reduza o número de tickers em `tickers.csv`
2. Aumente os filtros de volume mínimo
3. Reduza o período de dados históricos

### Nenhum shark detectado
1. Reduza o `volume_ratio_min` (ex: 1.2x)
2. Diminua o `min_volume_usd` (ex: $5M)
3. Habilite "Allow negative performance"
4. Desabilite "Enable pattern detection"

## 💡 Dicas de Uso

1. **Comece com os padrões**: Os valores padrão são conservadores e funcionam bem
2. **Experimente gradualmente**: Mude um parâmetro por vez para entender o impacto
3. **Compare períodos**: Execute a análise em diferentes dias para identificar tendências
4. **Foque nos Silent Sharks**: Frequentemente são os mais interessantes para acumulação
5. **Use métricas combinadas**: Não olhe apenas o volume ratio, considere o score total

---

**🦈 Happy Shark Hunting! 🏊‍♂️** 