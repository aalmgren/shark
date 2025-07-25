# 🕵️ Detector de Acumulação Silenciosa

Este script identifica **acumulação/distribuição institucional silenciosa** - quando grandes players estão comprando ou vendendo sem mover significativamente o preço. **Isso é crucial para timing de entrada e saída!**

## 🎯 O Que Ele Detecta

### ✅ SINAIS DE ACUMULAÇÃO (BUY)
- **Volume alto + preço estável** = Instituições comprando sem pressionar o preço
- **Dark pools ativos + shorts declinando** = Redução da pressão vendedora
- **Volume ineficiente** = Muito volume gerando pouco movimento de preço
- **Correlação baixa** = Volume desconectado do movimento de preço

### ❌ SINAIS DE DISTRIBUIÇÃO (SELL)
- **Volume alto + preço volátil** = Instituições vendendo
- **Aumento de shorts em dark pools** = Pressão vendedora crescente
- **Volume eficiente** = Volume movendo o preço significativamente

## 🚀 Como Usar

### Instalação
```bash
pip install -r requirements.txt
```

### Análise Individual
```bash
# Analisar uma ação específica
python silent_accumulation_detector.py --symbol AAPL

# Com período personalizado (dias)
python silent_accumulation_detector.py --symbol TSLA --days 90
```

### Scan de Múltiplas Ações
```bash
# Escanear ações populares (exemplo padrão)
python silent_accumulation_detector.py

# Usar arquivo com lista de símbolos
python silent_accumulation_detector.py --scan minha_lista.txt
```

**Formato do arquivo de símbolos (`minha_lista.txt`):**
```
AAPL
MSFT
GOOGL
TSLA
AMZN
```

## 📊 Interpretação dos Resultados

### Score de Acumulação (0-10)
- **7-10**: 🚨 **FORTE ACUMULAÇÃO** → BUY com alta confiança
- **4-6**: 📈 **ACUMULAÇÃO MODERADA** → BUY com confiança média
- **0-3**: ⚠️ **POSSÍVEL DISTRIBUIÇÃO** → HOLD ou REDUCE

### Métricas Chave

| Métrica | Descrição | Interpretação |
|---------|-----------|---------------|
| **Accumulation Score** | Pontuação geral (0-10) | Maior = mais acumulação |
| **Volume Efficiency** | Movimento de preço por unidade de volume | Baixo = acumulação silenciosa |
| **Dark Pool Ratio** | % do volume em dark pools | Alto + shorts declinando = bullish |
| **Volume Trend** | Tendência de volume vs média | Alto = atividade institucional |
| **Volume-Price Correlation** | Correlação entre volume e movimento | Baixa = volume "silencioso" |

### Sinais de Ação

| Sinal | Ação | Significado |
|-------|------|-------------|
| **STRONG_ACCUMULATION** | 🟢 **BUY** | Forte evidência de acumulação institucional |
| **ACCUMULATION** | 🟢 **BUY** | Evidência moderada de acumulação |
| **NEUTRAL** | 🟡 **HOLD** | Sem padrão claro |
| **WEAK_DISTRIBUTION** | 🟠 **REDUCE** | Possível início de distribuição |
| **DISTRIBUTION** | 🔴 **SELL** | Evidência de distribuição institucional |

## 📈 Exemplo de Saída

```
🕵️ DETECTANDO ACUMULAÇÃO SILENCIOSA EM AAPL

📈 ANÁLISE DE ACUMULAÇÃO SILENCIOSA - AAPL
============================================================

🎯 SINAL PRINCIPAL: STRONG_ACCUMULATION
📊 AÇÃO RECOMENDADA: BUY
🎲 CONFIANÇA: HIGH
⚠️  RISCO: LOW

📊 MÉTRICAS CHAVE:
  • Score de Acumulação: 8.2/10
  • Dias com Alta Atividade: 12
  • Eficiência de Volume: 0.31
  • Tendência de Volume: 1.8x
  • Ratio Dark Pool: 42.3%
  • Tendência Shorts: Declining

💹 DADOS DE PREÇO:
  • Preço Atual: $185.64
  • Variação 20 dias: +2.1%

🔍 RAZÕES DA ANÁLISE:
  • Alto score de acumulação (8.2)
  • 12 dias com alta atividade silenciosa
  • Volume alto com baixa correlação de preço
  • Alto volume dark pool com shorts declinando

🚨 ALERTA DE OPORTUNIDADE!
   Possível acumulação institucional detectada.
   Considere posição longa com stop loss.
```

## 📊 Gráficos Gerados

O script cria 4 gráficos automaticamente:

1. **Preço vs Volume**: Mostra relação entre preço e volume (dark pools em vermelho)
2. **Score de Acumulação**: Score diário colorido por intensidade
3. **Eficiência de Volume**: Quanto movimento de preço cada volume gera
4. **Volume vs Movimento**: Scatter plot mostrando correlação

## 🔍 Algoritmo de Detecção

### Volume Efficiency Index (VEI)
```
VEI = |Mudança de Preço %| / Volume Relativo
```
- **Baixo VEI** = Volume alto gerando pouco movimento = ACUMULAÇÃO
- **Alto VEI** = Volume movendo muito o preço = DISTRIBUIÇÃO

### Silent Accumulation Score (SAS)
Combina 5 fatores:
1. Volume acima da média (2 pontos)
2. Baixa eficiência de volume (2 pontos) 
3. Alto volume em dark pools (3 pontos)
4. Volume muito alto (2 pontos extra)
5. Baixo movimento de preço (1 ponto)

### Dark Pool Analysis
- **Dark Pool Ratio > 35%** + **Shorts Declinando** = BULLISH
- **Dark Pool Ratio > 30%** + **Shorts Aumentando** = BEARISH

## 🎯 Estratégias de Trading

### Para ACUMULAÇÃO Detectada:
1. **Entry**: Próximo ao preço atual ou em pullbacks menores
2. **Stop Loss**: Abaixo do suporte recente ou -5-8%
3. **Target**: Baseado em resistências técnicas ou +15-25%
4. **Timing**: Melhor entrar cedo no processo de acumulação

### Para DISTRIBUIÇÃO Detectada:
1. **Exit**: Reduzir posições longas gradualmente
2. **Short Entry**: Considerar vendas a descoberto
3. **Stop**: Acima da resistência recente
4. **Timing**: Sair antes da aceleração da distribuição

## ⚠️ Limitações e Cuidados

1. **Dados FINRA**: Nem sempre disponíveis para todas as ações
2. **Lag de dados**: FINRA pode ter 1-2 dias de atraso
3. **Confirmação**: Use com análise técnica e fundamentalista
4. **Market cap**: Mais efetivo em ações de grande/média capitalização
5. **Volatilidade**: Menos confiável em mercados muito voláteis

## 🏆 Melhores Práticas

1. **Combine com volume tradicional**: Confirme com análise de volume normal
2. **Use múltiplos timeframes**: Análise semanal + diária
3. **Monitore notícias**: Acumulação pode preceder anúncios
4. **Risk management**: Sempre use stop loss
5. **Paper trading**: Teste antes de usar dinheiro real

## 📁 Arquivos Gerados

- `accumulation_analysis_[symbol]_[timestamp].png`: Gráficos de análise
- `accumulation_scan_[timestamp].csv`: Resultados do scan de múltiplas ações

## 🤖 Automação

Para monitoramento contínuo, você pode:

1. **Criar watchlist**: Lista de ações para monitorar
2. **Agendar execução**: Rodar diariamente após fechamento
3. **Alertas**: Configurar notificações para scores altos
4. **Database**: Armazenar histórico de scores

## 💡 Exemplo de Uso Prático

```bash
# 1. Scan inicial para encontrar oportunidades
python silent_accumulation_detector.py

# 2. Análise detalhada das top 3
python silent_accumulation_detector.py --symbol AAPL
python silent_accumulation_detector.py --symbol MSFT
python silent_accumulation_detector.py --symbol GOOGL

# 3. Monitoramento semanal
python silent_accumulation_detector.py --symbol AAPL --days 90
```

---

## ⚖️ Disclaimer

Este script é para fins educacionais e de pesquisa. Não constitui conselho de investimento. Sempre:

- ✅ Faça sua própria pesquisa
- ✅ Use gestão de risco adequada
- ✅ Diversifique seus investimentos
- ✅ Consulte um consultor financeiro qualificado

**O volume institucional pode prever movimentos, mas não há garantias no mercado de ações!**