import pandas as pd
import numpy as np
from pathlib import Path
import os
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple

def load_stock_data(ticker: str, db_path: str = "DB") -> pd.DataFrame:
    """Carrega os dados de uma ação específica"""
    file_path = Path(db_path) / f"{ticker}.csv"
    df = pd.DataFrame()
    
    if file_path.exists():
        df = pd.read_csv(file_path)
        df = df.dropna()
        if len(df) > 0:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
            # Pega os últimos 252 dias úteis (1 ano)
            df = df.tail(252)
            # Verifica se tem volume
            if 'Volume' not in df.columns or df['Volume'].isna().all():
                return pd.DataFrame()
    
    return df

def calculate_returns(df: pd.DataFrame) -> pd.Series:
    """Calcula retornos diários"""
    return df['Close'].pct_change()

def filter_stocks_by_liquidity(stocks: List[str], min_volume: float = 10000) -> List[str]:
    """Filtra ações por volume médio mínimo"""
    liquid_stocks = []
    total = len(stocks)
    
    print(f"\nAnalisando liquidez de {total} ações...")
    for i, stock in enumerate(stocks, 1):
        if i % 100 == 0:
            print(f"Progresso: {i}/{total} ações analisadas")
            
        df = load_stock_data(stock)
        if len(df) > 200:  # Pelo menos 200 dias de dados
            if 'Volume' in df.columns and not df['Volume'].isna().all():
                avg_volume = df['Volume'].mean()
                if avg_volume > min_volume:
                    liquid_stocks.append(stock)
    
    return liquid_stocks

def create_returns_matrix(stocks: List[str]) -> pd.DataFrame:
    """Cria matriz de retornos para todas as ações"""
    returns_dict = {}
    total = len(stocks)
    
    print(f"\nCalculando retornos para {total} ações...")
    for i, stock in enumerate(stocks, 1):
        if i % 100 == 0:
            print(f"Progresso: {i}/{total} ações processadas")
            
        df = load_stock_data(stock)
        if len(df) > 200:  # Pelo menos 200 dias de dados
            returns = calculate_returns(df)
            if not returns.empty and not returns.isna().all():
                returns_dict[stock] = returns
    
    # Cria DataFrame e alinha as datas
    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.ffill().bfill()  # Preenche valores faltantes
    
    # Remove ações com muitos dados faltantes
    min_periods = len(returns_df) * 0.9  # Pelo menos 90% dos dados
    returns_df = returns_df.dropna(axis=1, thresh=min_periods)
    
    return returns_df

def calculate_correlation_matrix(returns_matrix: pd.DataFrame) -> pd.DataFrame:
    """Calcula matriz de correlação entre os retornos"""
    return returns_matrix.corr()

def cluster_stocks(correlation_matrix: pd.DataFrame, n_clusters: int = 10) -> Dict:
    """
    Agrupa ações usando clusterização hierárquica
    """
    # Converte correlação em distância (1 - correlação absoluta)
    distance_matrix = 1 - np.abs(correlation_matrix)
    
    # Converte matriz de distância em vetor condensado
    distance_vector = squareform(distance_matrix)
    
    # Aplica clusterização hierárquica
    linkage_matrix = linkage(distance_vector, method='ward')
    
    # Determina os clusters
    labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
    
    # Organiza ações por cluster
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(correlation_matrix.index[i])
    
    return {'clusters': clusters, 'linkage': linkage_matrix}

def plot_correlation_matrix(correlation_matrix: pd.DataFrame, output_file: str = 'correlation_matrix.png'):
    """Plota mapa de calor da matriz de correlação"""
    if correlation_matrix.empty:
        print("Matriz de correlação vazia, pulando visualização...")
        return
        
    plt.figure(figsize=(20, 16))
    sns.heatmap(correlation_matrix, cmap='RdYlBu', center=0, annot=False)
    plt.title('Matriz de Correlação entre Ações')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def plot_dendrogram(linkage_matrix: np.ndarray, labels: List[str], output_file: str = 'dendrogram.png'):
    """Plota dendrograma dos clusters"""
    if len(labels) == 0:
        print("Sem dados para gerar dendrograma...")
        return
        
    plt.figure(figsize=(20, 10))
    dendrogram(
        linkage_matrix,
        labels=labels,
        leaf_rotation=90,
        leaf_font_size=8,
        truncate_mode='lastp',
        p=50  # mostra apenas os 50 últimos merges
    )
    plt.title('Dendrograma de Agrupamento das Ações')
    plt.xlabel('Ações')
    plt.ylabel('Distância')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def analyze_clusters(clusters: Dict, correlation_matrix: pd.DataFrame) -> Dict:
    """
    Analisa características de cada cluster
    """
    analysis = {}
    
    for cluster_id, stocks in clusters.items():
        # Matriz de correlação do cluster
        cluster_corr = correlation_matrix.loc[stocks, stocks]
        
        # Correlação média entre ações do cluster
        mean_corr = cluster_corr.values[np.triu_indices_from(cluster_corr.values, k=1)].mean()
        
        # Ação mais representativa (maior correlação média com outras)
        mean_correlations = cluster_corr.mean()
        representative_stock = mean_correlations.idxmax()
        
        # Encontra pares mais correlacionados
        upper_triangle = cluster_corr.where(np.triu(np.ones(cluster_corr.shape), k=1).astype(bool))
        highest_corr = upper_triangle.unstack()
        highest_corr = highest_corr.sort_values(ascending=False)
        top_pairs = highest_corr[highest_corr > 0.8][:5]  # Top 5 pares com correlação > 0.8
        
        analysis[cluster_id] = {
            'n_stocks': len(stocks),
            'mean_correlation': round(mean_corr, 3),
            'representative_stock': representative_stock,
            'stocks': stocks,
            'top_pairs': top_pairs
        }
    
    return analysis

def main():
    print("\nIniciando análise de clusters de ações...")
    
    # Lista todas as ações
    stocks = [f.replace('.csv', '') for f in os.listdir('DB') if f.endswith('.csv')]
    print(f"Total de ações encontradas: {len(stocks)}")
    
    # Filtra por liquidez
    liquid_stocks = filter_stocks_by_liquidity(stocks)
    print(f"\nAções com liquidez adequada: {len(liquid_stocks)}")
    
    if not liquid_stocks:
        print("\nNenhuma ação com liquidez suficiente encontrada.")
        return
    
    # Cria matriz de retornos
    returns_matrix = create_returns_matrix(liquid_stocks)
    print(f"\nMatriz de retornos criada com {returns_matrix.shape[1]} ações")
    
    if returns_matrix.empty:
        print("\nNenhum dado válido para análise.")
        return
    
    # Calcula correlações
    print("\nCalculando matriz de correlação...")
    correlation_matrix = calculate_correlation_matrix(returns_matrix)
    
    # Plota matriz de correlação
    print("Gerando mapa de calor da correlação...")
    plot_correlation_matrix(correlation_matrix)
    
    # Aplica clusterização
    print("\nRealizando clusterização...")
    clustering_results = cluster_stocks(correlation_matrix)
    
    # Plota dendrograma
    print("Gerando dendrograma...")
    plot_dendrogram(
        clustering_results['linkage'],
        correlation_matrix.index.tolist()
    )
    
    # Analisa clusters
    print("\nAnalisando características dos clusters...")
    analysis = analyze_clusters(clustering_results['clusters'], correlation_matrix)
    
    # Imprime resultados
    print("\nResultados da Análise de Clusters:")
    print("-" * 80)
    
    for cluster_id, info in analysis.items():
        print(f"\nCluster {cluster_id}:")
        print(f"Número de ações: {info['n_stocks']}")
        print(f"Correlação média: {info['mean_correlation']:.3f}")
        print(f"Ação mais representativa: {info['representative_stock']}")
        
        print("\nPares mais correlacionados:")
        for (stock1, stock2), corr in info['top_pairs'].items():
            print(f"  {stock1} - {stock2}: {corr:.3f}")
        
        print("\nAções no cluster:")
        stocks_lines = [info['stocks'][i:i+5] for i in range(0, len(info['stocks']), 5)]
        for line in stocks_lines:
            print("  " + ", ".join(line))
    
    # Salva resultados em arquivo
    print("\nSalvando resultados detalhados...")
    with open('cluster_analysis.txt', 'w') as f:
        f.write("Análise Detalhada de Clusters de Ações\n")
        f.write("=" * 80 + "\n\n")
        
        for cluster_id, info in analysis.items():
            f.write(f"Cluster {cluster_id}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Número de ações: {info['n_stocks']}\n")
            f.write(f"Correlação média: {info['mean_correlation']:.3f}\n")
            f.write(f"Ação mais representativa: {info['representative_stock']}\n")
            
            f.write("\nPares mais correlacionados:\n")
            for (stock1, stock2), corr in info['top_pairs'].items():
                f.write(f"  {stock1} - {stock2}: {corr:.3f}\n")
            
            f.write("\nAções no cluster:\n")
            for stock in info['stocks']:
                f.write(f"  {stock}\n")
            f.write("\n")
    
    print("\nAnálise completa! Arquivos gerados:")
    print("- correlation_matrix.png: Mapa de calor das correlações")
    print("- dendrogram.png: Dendrograma dos clusters")
    print("- cluster_analysis.txt: Análise detalhada dos clusters")

if __name__ == "__main__":
    main() 