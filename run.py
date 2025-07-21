import streamlit as st
import pandas as pd
import numpy as np
import os
import subprocess
import sys
from datetime import datetime
from shared_params import save_analysis_params, load_analysis_params

# Configuração da página
st.set_page_config(
    page_title="⚡ Momentum Analysis - IBKR",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para reduzir espaço no topo
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_ticker_data():
    """Carrega e armazena em cache os dados dos tickers com setores e indústrias."""
    file_path = 'tick/tickers.csv' # Corrigido para o arquivo correto
    if os.path.exists(file_path):
        # As colunas já estão corretas no CSV, não precisa nomear
        df = pd.read_csv(file_path)
        return df
    st.sidebar.warning(f"Ticker info file not found at {file_path}")
    return None

def load_saved_results():
    """Carrega os resultados salvos dos arquivos CSV"""
    try:
        # Verificar se os arquivos existem
        candidates_file = "institutional_accumulation_candidates.csv" # Nome de arquivo correto
        
        if os.path.exists(candidates_file):
            # Obter data de modificação do arquivo
            import time
            file_time = os.path.getmtime(candidates_file)
            file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M')
            
            # Carregar parâmetros da última análise
            params = load_analysis_params()
            
            # Mostrar informação na sidebar
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"📅 **Last Analysis:** {file_date}")
            st.sidebar.markdown(f"⚙️ **Parameters:** {params.get('volume_period_short', 'N/A')}D / {params.get('volume_period_long', 'N/A')}D")
            
            momentum_df = pd.read_csv(candidates_file)
            
            # Não existe mais um arquivo separado para latent, então removemos a lógica de carregamento
            latent_momentum_df = momentum_df[momentum_df[f'change_{params.get("volume_period_short", 7)}d'] <= params.get('silent_sharks_threshold', 5.0)]
            
            return momentum_df, latent_momentum_df, params
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados salvos: {str(e)}")
    
    return None, None, None

def main():
    
    # Botão de download (desabilitado)
    if st.sidebar.button("📥 Download Today's Data", disabled=True):
        st.info("Download functionality is currently disabled.")
    
    # Botão de análise
    analyze_button = st.sidebar.button(
        "🔍 Run Momentum Analysis",
        type="primary"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Analysis Parameters")
    st.sidebar.caption("These affect HOW institutional accumulation is detected")
    
    # Carregar parâmetros salvos para definir os valores padrão dos sliders
    saved_params = load_analysis_params()
    
    # Parâmetros essenciais de período
    volume_period_long = st.sidebar.slider(
        "Volume baseline period (days)",
        min_value=1, # Mínimo de 1 para evitar divisão por zero
        max_value=90,
        value=saved_params.get('volume_period_long', 60),
        step=1,
        help="Period for calculating average baseline volume"
    )
    
    volume_period_short = st.sidebar.slider(
        "Volume spike period (days)",
        min_value=1, # Mínimo de 1 para evitar divisão por zero
        max_value=10,
        value=saved_params.get('volume_period_short', 7),
        step=1,
        help="Period for detecting volume increases"
    )
    
    # Main content area
    if analyze_button:
        run_analysis(
            volume_period_long=volume_period_long,
            volume_period_short=volume_period_short
        )
    else:
        # Carregar automaticamente os dados salvos quando a página abre
        momentum_df, latent_momentum_df, params = load_saved_results()
        if momentum_df is not None:
            display_results(momentum_df, latent_momentum_df, params, is_saved_data=True)
        else:
            show_instructions()

def download_data():
    """Execute download script and show progress"""
    st.info("📥 Starting data download...")
    
    # Create progress placeholder
    progress_placeholder = st.empty()
    log_placeholder = st.empty()
    
    try:
        # Execute download script
        process = subprocess.Popen(
            [sys.executable, "download_all_data.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logs = []
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                logs.append(line.strip())
                # Show last 10 lines
                log_placeholder.text_area(
                    "Download Log:",
                    value="\n".join(logs[-10:]),
                    height=200,
                    disabled=True
                )
        
        process.wait()
        
        if process.returncode == 0:
            st.success("✅ Data download completed successfully!")
        else:
            st.error("❌ Data download failed. Check logs above.")
            
    except Exception as e:
        st.error(f"❌ Error during download: {str(e)}")

def check_data_availability():
    """Check if data directories exist and have recent data"""
    data_dirs = ['DB', 'additional_database']
    for data_dir in data_dirs:
        if os.path.exists(data_dir) and os.listdir(data_dir):
            return True
    return False

def run_analysis(volume_period_long, volume_period_short):
    """Run momentum analysis by calling analyze.py"""
    
    # Salva os parâmetros para que analyze.py possa lê-los
    save_analysis_params(volume_period_long, volume_period_short)
    
    st.info("🔍 Starting momentum analysis... This may take a few minutes.")
    
    # Placeholder for logs and spinner
    log_container = st.empty()
    
    try:
        # Use a spinner to indicate processing
        with st.spinner("Processing..."):
            # Execute analyze.py as a separate process to avoid conflicts
            process = subprocess.Popen(
                [sys.executable, "analyze.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8' # Adicionado para evitar problemas de codificação
            )
            
            # Display logs in real-time
            logs = []
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    logs.append(line.strip())
                    log_container.text_area(
                        "Analysis Log:",
                        value="\n".join(logs),
                        height=300,
                        disabled=True
                    )
            
            process.wait()

        if process.returncode == 0:
            st.success("✅ Analysis completed successfully!")
            # Force a rerun to load the new data
            st.rerun()
        else:
            st.error("❌ Analysis failed. Check the logs above for details.")
            
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}")


def display_results(momentum_df, latent_momentum_df, params, is_saved_data=False):
    """Display analysis results with tables and charts"""
    
    if momentum_df is None or len(momentum_df) == 0:
        st.warning("⚡ No momentum candidates detected with current parameters. Try adjusting the filters.")
        return

    # Garante que os dados de setor/indústria existam, carregando-os se necessário.
    if 'sector' not in momentum_df.columns or 'industry' not in momentum_df.columns:
        ticker_data = load_ticker_data()
        if ticker_data is not None:
            # Clean merge keys for robustness
            momentum_df['ticker'] = momentum_df['ticker'].astype(str).str.strip()
            ticker_data['ticker'] = ticker_data['ticker'].astype(str).str.strip()

            momentum_df = pd.merge(momentum_df, ticker_data[['ticker', 'sector', 'industry']], on='ticker', how='left')
            momentum_df['industry'].fillna('Unknown', inplace=True)
            momentum_df['sector'].fillna('Unknown', inplace=True)
        else:
            momentum_df['industry'] = 'Unknown'
            momentum_df['sector'] = 'Unknown'
    
    st.markdown("---")
    
    # --- Linha de Filtros 1 ---
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        display_min_ratio = st.slider("Min Ratio", 1.0, 10.0, 1.0, 0.1, format="%.1fx", help="Hide candidates below this ratio")
    
    with filter_col2:
        display_min_volume = st.slider("Min Spike Volume ($M)", 0, 100, 10, 5, format="$%dM", help="Hide candidates below this daily volume (millions USD)")
    
    with filter_col3:
        display_min_price = st.slider("Min Price", 0.0, 50.0, 5.0, 1.0, format="$%.0f", help="Hide stocks below this price")

    # --- Linha de Filtros 2 (Sector & Industry) ---
    filter_col_sector, filter_col_industry = st.columns(2)

    with filter_col_sector:
        if 'sector' in momentum_df.columns:
            all_sectors = sorted(momentum_df['sector'].dropna().unique())
            if len(all_sectors) > 1:
                selected_sectors = st.multiselect("Filter by Sector", options=all_sectors, help="Select one or more sectors to display")
            else:
                selected_sectors = []
        else:
            selected_sectors = []

    with filter_col_industry:
        if 'industry' in momentum_df.columns:
            # Filtra as indústrias com base nos setores selecionados
            if selected_sectors:
                available_industries = sorted(momentum_df[momentum_df['sector'].isin(selected_sectors)]['industry'].dropna().unique())
            else:
                available_industries = sorted(momentum_df['industry'].dropna().unique())
            
            if len(available_industries) > 1:
                selected_industries = st.multiselect("Filter by Industry", options=available_industries, help="Select one or more industries to display")
            else:
                selected_industries = []
        else:
            selected_industries = []
    
    # --- Linha de Filtros 3 ---
    hide_derivatives = st.checkbox("Hide Derivatives", value=True, help="Hide warrants, units, rights, etc.")
    
    # Aplicar filtros de visualização
    filtered_df = momentum_df.copy()
    
    # Nome da coluna de volume para o filtro (dinâmico)
    vol_short_col_usd = f'volume_usd_{params.get("volume_period_short", 7)}d'

    # Filtrar por setor
    if selected_sectors:
        filtered_df = filtered_df[filtered_df['sector'].isin(selected_sectors)]
        
    # Filtrar por indústria
    if selected_industries:
        filtered_df = filtered_df[filtered_df['industry'].isin(selected_industries)]

    # Filtrar por volume ratio mínimo
    filtered_df = filtered_df[filtered_df['ratio'] >= display_min_ratio]
    
    # Filtrar por volume mínimo (converter de milhões para USD)
    min_volume_usd = display_min_volume * 1_000_000
    if vol_short_col_usd in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[vol_short_col_usd] >= min_volume_usd]
    
    # Filtrar por preço mínimo
    filtered_df = filtered_df[filtered_df['price'] >= display_min_price]
    
    # Filtrar derivatives se marcado
    if hide_derivatives:
        filtered_df = filtered_df[~filtered_df['ticker'].str.endswith(('.WT', '.U', '.R', '.P', 'W', 'WS', 'PR', 'X', 'L', 'Z'))]
    
    # Tabela de candidatos filtrados
    st.subheader(f"⚡ Momentum Candidates Found ({len(filtered_df)} results)")
    
    if len(filtered_df) == 0:
        st.warning("No momentum candidates match the current filters. Try adjusting the criteria.")
    else:
        # Format the dataframe for display
        display_df = filtered_df.copy()
        
        # Nomes de coluna dinâmicos para exibição
        vol_short_col_usd_name = f'volume_usd_{params.get("volume_period_short", 7)}d'
        vol_long_col_usd_name = f'volume_usd_{params.get("volume_period_long", 60)}d'
        avg_price_long_col_name = f'avg_price_{params.get("volume_period_long", 60)}d'
        
        display_df[f'vol_usd_short_M'] = display_df[vol_short_col_usd_name] / 1_000_000 if vol_short_col_usd_name in display_df else 0
        display_df[f'vol_usd_long_M'] = display_df[vol_long_col_usd_name] / 1_000_000 if vol_long_col_usd_name in display_df else 0
        
        # Create dynamic column labels based on analysis parameters
        vol_short_label = f"Vol {params.get('volume_period_short', 7)}D ($M)"
        vol_long_label = f"Vol {params.get('volume_period_long', 60)}D ($M)"
        avg_price_long_label = f"Avg Price {params.get('volume_period_long', 60)}D"
        price_change_label = "Avg Price Change (%)"

        # Colunas a serem exibidas e seus nomes amigáveis
        display_columns = {
            'ticker': 'Ticker',
            'sector': 'Sector',
            'industry': 'Industry',
            'ratio': 'Ratio',
            'vol_usd_short_M': vol_short_label,
            'vol_usd_long_M': vol_long_label,
            'price': 'Price',
            avg_price_long_col_name: avg_price_long_label,
            'avg_price_change_pct': price_change_label,
            'score': 'Score'
        }
        
        # Garantir que todas as colunas necessárias existam no dataframe
        final_display_cols = []
        for col in display_columns.keys():
            if col in display_df.columns:
                final_display_cols.append(col)
        
        # Renomeia as colunas do DataFrame para corresponder às chaves do column_config
        rename_map = {key: val for key, val in display_columns.items() if key in final_display_cols}
        
        st.dataframe(
            display_df[final_display_cols].rename(columns=rename_map),
            # A configuração de colunas usa os nomes amigáveis como chaves
            column_config={
                'Ticker': st.column_config.Column(width="small"),
                'Sector': st.column_config.Column(width="medium"),
                'Industry': st.column_config.Column(width="medium"),
                'Ratio': st.column_config.NumberColumn(format="%.1fx"),
                vol_short_label: st.column_config.NumberColumn(format="$%.1fM"),
                vol_long_label: st.column_config.NumberColumn(format="$%.1fM"),
                'Price': st.column_config.NumberColumn(format="$%.2f"),
                avg_price_long_label: st.column_config.NumberColumn(format="$%.2f"),
                price_change_label: st.column_config.NumberColumn(format="%.1f%%"),
                'Score': st.column_config.NumberColumn(format="%.1f")
            },
            use_container_width=True,
            height=600
        )
    
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if len(filtered_df) > 0:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Results",
                    data=csv_data,
                    file_name=f"momentum_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            csv_data_all = momentum_df.to_csv(index=False)
            st.download_button(
                label="📥 Download All Candidates",
                data=csv_data_all,
                file_name=f"momentum_all_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

def show_instructions():
    """Show initial instructions"""
    st.markdown("""
    ## 🆕 No saved results found
    
    **How to use:** Adjust filters → Click **Run Momentum Analysis** to start! 🚀
    
    ---
    
    💡 **Tip:** After running an analysis, the results will be automatically displayed when you open the page next time.
    """)

if __name__ == "__main__":
    main() 