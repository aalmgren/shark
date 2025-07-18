import streamlit as st
import pandas as pd
import numpy as np
import os
import subprocess
import sys
from datetime import datetime
from analyze_sharks import process_nasdaq_data, analyze_ticker, process_file

# Configuração da página
st.set_page_config(
    page_title="🦈 Shark Detection - IBKR",
    page_icon="🦈",
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

def save_analysis_params(volume_period_long, volume_period_short, volume_ratio_min, silent_sharks_threshold):
    """Salva os parâmetros da análise em arquivo JSON"""
    try:
        import json
        params = {
            'volume_period_long': volume_period_long,
            'volume_period_short': volume_period_short,
            'volume_ratio_min': volume_ratio_min,
            'silent_sharks_threshold': silent_sharks_threshold,
            'timestamp': datetime.now().isoformat()
        }
        with open('analysis_params.json', 'w') as f:
            json.dump(params, f)
    except Exception as e:
        st.error(f"❌ Erro ao salvar parâmetros: {str(e)}")

def load_analysis_params():
    """Carrega os parâmetros da última análise"""
    try:
        import json
        if os.path.exists('analysis_params.json'):
            with open('analysis_params.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Parâmetros padrão se não conseguir carregar
    return {
        'volume_period_long': 60,
        'volume_period_short': 7,
        'volume_ratio_min': 1.5,
        'silent_sharks_threshold': 5.0
    }

def load_saved_results():
    """Carrega os resultados salvos dos arquivos CSV"""
    try:
        # Verificar se os arquivos existem
        sharks_file = "institutional_accumulation_candidates.csv"
        silent_sharks_file = "silent_sharks.csv"
        
        if os.path.exists(sharks_file):
            # Obter data de modificação do arquivo
            import time
            file_time = os.path.getmtime(sharks_file)
            file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M')
            
            # Carregar parâmetros da última análise
            params = load_analysis_params()
            
            # Mostrar informação na sidebar
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"📅 **Last Analysis:** {file_date}")
            st.sidebar.markdown(f"⚙️ **Parameters:** {params['volume_period_short']}D / {params['volume_period_long']}D")
            
            sharks_df = pd.read_csv(sharks_file)
            silent_sharks_df = None
            
            if os.path.exists(silent_sharks_file):
                silent_sharks_df = pd.read_csv(silent_sharks_file)
            else:
                # Criar silent sharks a partir dos dados principais
                silent_sharks_df = sharks_df[sharks_df['change_7d'] <= params['silent_sharks_threshold']]
            
            return sharks_df, silent_sharks_df, params
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados salvos: {str(e)}")
    
    return None, None, None

def main():
    st.title("🦈 SHARK DETECTION")
    
    # Botão de download
    if st.sidebar.button("📥 Download Today's Data", disabled=True):
        download_data()
    
    # Botão de análise
    analyze_button = st.sidebar.button(
        "🔍 Run Shark Analysis",
        type="primary"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Analysis Parameters")
    st.sidebar.caption("These affect HOW institutional accumulation is detected")
    
    # Parâmetros essenciais de período
    volume_period_long = st.sidebar.slider(
        "Volume baseline period (days)",
        min_value=0,
        max_value=90,
        value=60,
        step=5,
        help="Period for calculating average baseline volume"
    )
    
    volume_period_short = st.sidebar.slider(
        "Volume spike period (days)",
        min_value=0,
        max_value=10,
        value=7,
        step=1,
        help="Period for detecting volume increases"
    )
    

    
    # Main content area
    if analyze_button:
        if not check_data_availability():
            st.error("❌ No data available. Please download data first.")
            return
            
        run_analysis(
            volume_period_long=volume_period_long,
            volume_period_short=volume_period_short
        )
    else:
        # Carregar automaticamente os dados salvos quando a página abre
        sharks_df, silent_sharks_df, params = load_saved_results()
        if sharks_df is not None:
            display_results(sharks_df, silent_sharks_df, params, is_saved_data=True)
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
    data_dirs = ['nasdaq_database', 'additional_database']
    for data_dir in data_dirs:
        if os.path.exists(data_dir) and os.listdir(data_dir):
            return True
    return False

def run_analysis(volume_period_long, volume_period_short):
    """Run shark analysis using analyze_sharks.py functions"""
    
    # Fixed values for hidden parameters
    volume_ratio_min = 1.5
    silent_sharks_threshold = 5.0
    
    # Save analysis parameters
    save_analysis_params(volume_period_long, volume_period_short, volume_ratio_min, silent_sharks_threshold)
    
    st.info("🔍 Starting shark analysis...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    with log_container:
        log_placeholder = st.empty()
        logs = []
        
        def log_message(msg):
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            log_placeholder.text_area(
                "Analysis Log:",
                value="\n".join(logs[-15:]),
                height=300,
                disabled=True
            )
        
        # Call the process_nasdaq_data function directly
        log_message("🦈 DETECTANDO SMART MONEY - NADAR COM OS SHARKS")
        progress_bar.progress(0.1)
        status_text.text("Loading data files...")
        
        # Execute analysis (simplified version without the class)
        sharks_df, silent_sharks_df = run_sharks_analysis_simple(
            volume_period_long, volume_period_short, volume_ratio_min, silent_sharks_threshold,
            log_message, progress_bar, status_text
        )
    
    progress_bar.progress(1.0)
    status_text.text("✅ Analysis completed!")
    
    # Create params dict for display
    params = {
        'volume_period_long': volume_period_long,
        'volume_period_short': volume_period_short,
        'volume_ratio_min': volume_ratio_min,
        'silent_sharks_threshold': silent_sharks_threshold
    }
    
    # Display results
    display_results(sharks_df, silent_sharks_df, params)

def run_sharks_analysis_simple(volume_period_long, volume_period_short, volume_ratio_min, silent_sharks_threshold, 
                              log_func, progress_bar, status_text):
    """Simplified version of shark analysis for Streamlit"""
    import multiprocessing as mp
    
    # 1. Collect files
    all_files = []
    for data_dir in ['nasdaq_database', 'additional_database']:
        if os.path.exists(data_dir):
            files = [(os.path.join(data_dir, f), f) for f in os.listdir(data_dir) if f.endswith('.csv')]
            all_files.extend(files)
    
    if not all_files:
        log_func("❌ No CSV files found")
        return None, None
    
    log_func(f"📊 Processing {len(all_files)} files...")
    progress_bar.progress(0.2)
    
    # 2. Process files (simplified, sequential for Streamlit)
    processed = []
    for i, file_info in enumerate(all_files):
        result = process_file(file_info)
        if result is not None:
            processed.append(result)
        if i % 1000 == 0:
            progress = 0.2 + 0.4 * i / len(all_files)
            progress_bar.progress(progress)
    
    if not processed:
        log_func("❌ No valid data found")
        return None, None
    
    # 3. Consolidate data
    status_text.text("Consolidating data...")
    df = pd.concat(processed, ignore_index=True)
    log_func(f"✅ Data loaded: {len(df):,} records from {df['ticker'].nunique()} tickers")
    progress_bar.progress(0.6)
    
    # 4. Analyze each ticker
    status_text.text("Analyzing tickers for shark patterns...")
    ticker_groups = [group for _, group in df.groupby('ticker')]
    analyzed = []
    
    for i, ticker_group in enumerate(ticker_groups):
        result = analyze_ticker_simple(ticker_group, volume_period_long, volume_period_short, volume_ratio_min)
        if result is not None:
            analyzed.append(result)
        
        if i % 500 == 0:
            progress = 0.6 + 0.3 * i / len(ticker_groups)
            progress_bar.progress(progress)
    
    if not analyzed:
        log_func("❌ No sharks detected")
        return None, None
    
    # 5. Create results
    progress_bar.progress(0.95)
    sharks_df = pd.DataFrame(analyzed)
    sharks_df = sharks_df.sort_values('score', ascending=False)
    
    # Create silent sharks
    silent_sharks_df = sharks_df[sharks_df['change_7d'] <= silent_sharks_threshold]
    
    log_func(f"🦈 {len(sharks_df)} sharks detected!")
    log_func(f"🤫 {len(silent_sharks_df)} silent sharks detected!")
    
    return sharks_df, silent_sharks_df

def analyze_ticker_simple(ticker_data, volume_period_long, volume_period_short, volume_ratio_min):
    """Simplified ticker analysis for Streamlit"""
    try:
        ticker_data = ticker_data.sort_values('Date')
        ticker = ticker_data['ticker'].iloc[0]
        
        # Validate minimum data requirement
        min_required_data = max(volume_period_long + volume_period_short, 30)  # At least 30 days of data
        if len(ticker_data) < min_required_data:
            return None
            
        # Calculate volume in USD
        ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
            
        # Calculate averages using dynamic periods
        if volume_period_short > 0:
            last_short = ticker_data.tail(volume_period_short)
            total_long_period = volume_period_long + volume_period_short
            previous_long = ticker_data.iloc[-total_long_period:-volume_period_short] if len(ticker_data) >= total_long_period else ticker_data.iloc[:-volume_period_short]
        else:
            # If short period is 0, use last day as "spike" period
            last_short = ticker_data.tail(1)
            previous_long = ticker_data.tail(volume_period_long) if volume_period_long > 0 else ticker_data
        
        volume_usd_long = previous_long['volume_usd'].mean()
        volume_usd_short = last_short['volume_usd'].mean()
        volume_long = previous_long['Volume'].mean()
        volume_short = last_short['Volume'].mean()
        price_long_avg = ticker_data['Close'].tail(volume_period_long).mean() if volume_period_long > 0 else ticker_data['Close'].mean()
        
        # Apply basic filters - use fixed minimum volume filter of $10M for simplicity
        if volume_usd_long < 10_000_000:
            return None
            
        if price_long_avg <= 1.0:  # Very basic price filter
            return None
        
        # Calculate price changes
        current_price = ticker_data['Close'].iloc[-1]
        
        if current_price <= 1.0:
            return None
            
        if volume_period_short > 0:
            price_short_ago = ticker_data['Close'].iloc[-volume_period_short]
        else:
            price_short_ago = current_price  # If no short period, use current price
        
        price_30d_ago = ticker_data['Close'].iloc[-30] if len(ticker_data) >= 30 else ticker_data['Close'].iloc[0]
        
        price_change_short = ((current_price - price_short_ago) / price_short_ago) * 100 if price_short_ago > 0 else 0
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100 if price_30d_ago > 0 else 0
        
        # Filter negative performance
        if price_change_short <= 0 or price_change_30d <= 0:
            return None
        
        # Volume ratio calculation
        volume_ratio = volume_usd_short / volume_usd_long if volume_usd_long > 0 else 0
        
        # Check volume ratio
        if volume_ratio >= volume_ratio_min:
            score = volume_ratio * (1 + price_change_short / 100)
            
            return {
                'ticker': ticker,
                'ratio': volume_ratio,
                'volume_7d': volume_short,
                'volume_90d': volume_long,
                'volume_usd_7d': volume_usd_short,
                'volume_usd_90d': volume_usd_long,
                'price': current_price,
                'price_90d_avg': price_long_avg,
                'change_7d': price_change_short,
                'change_30d': price_change_30d,
                'score': score
            }
    except Exception as e:
        pass
    return None

def display_results(sharks_df, silent_sharks_df, params, is_saved_data=False):
    """Display analysis results with tables and charts"""
    
    
    if sharks_df is None or len(sharks_df) == 0:
        st.warning("🦈 No sharks detected with current parameters. Try adjusting the filters.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦈 Total Sharks", len(sharks_df))
    
    with col2:
        mega_sharks = len(sharks_df[sharks_df['ratio'] >= 3])
        st.metric("🔥 Mega Sharks (3x+)", mega_sharks)
    
    with col3:
        big_sharks = len(sharks_df[(sharks_df['ratio'] >= 2) & (sharks_df['ratio'] < 3)])
        st.metric("⚡ Big Sharks (2-3x)", big_sharks)
    
    with col4:
        silent_count = len(silent_sharks_df) if silent_sharks_df is not None else 0
        st.metric("🤫 Silent Sharks", silent_count)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        show_silent_only = st.checkbox("🤫 Only Silent Sharks", help="Show only stocks with price change ≤ 5%")
    
    with col2:
        display_min_ratio = st.slider("Min Ratio", 1.0, 10.0, 1.0, 0.1, format="%.1fx", help="Hide sharks below this ratio")
    
    with col3:
        display_min_volume = st.slider("Min Volume", 0, 1000, 80, 10, format="$%dM", help="Hide sharks below this daily volume (millions USD)")
    
    with col4:
        display_min_price = st.slider("Min Price", 1.0, 50.0, 10.0, 1.0, format="$%.0f", help="Hide stocks below this price")
    
    with col5:
        hide_derivatives = st.checkbox("Hide Derivatives", value=True, help="Hide warrants, units, rights, etc.")
    
    # Aplicar filtros de visualização
    filtered_df = sharks_df.copy()
    
    # Filtrar por volume ratio mínimo
    filtered_df = filtered_df[filtered_df['ratio'] >= display_min_ratio]
    
    # Filtrar por volume mínimo (converter de milhões para USD)
    min_volume_usd = display_min_volume * 1_000_000
    filtered_df = filtered_df[filtered_df['volume_usd_7d'] >= min_volume_usd]
    
    # Filtrar por preço mínimo
    filtered_df = filtered_df[filtered_df['price'] >= display_min_price]
    
    # Filtrar derivatives se marcado
    if hide_derivatives:
        filtered_df = filtered_df[~filtered_df['ticker'].str.endswith(('W', 'WS', 'U', 'R', 'P', 'PR', 'X', 'L', 'Z'))]
    
    # Filtrar apenas silent sharks se marcado
    if show_silent_only:
        filtered_df = filtered_df[filtered_df['change_7d'] <= 5.0]
    
    # Tabela de sharks filtrados
    st.subheader(f"🦈 Sharks Found ({len(filtered_df)} results)")
    
    if len(filtered_df) == 0:
        st.warning("No sharks match the current filters. Try adjusting the criteria.")
    else:
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['volume_usd_7d_M'] = display_df['volume_usd_7d'] / 1_000_000
        display_df['volume_usd_90d_M'] = display_df['volume_usd_90d'] / 1_000_000
        
        # Create dynamic column labels based on analysis parameters
        vol_short_label = f"Vol {params['volume_period_short']}D ($M)"
        vol_long_label = f"Vol {params['volume_period_long']}D ($M)"
        price_avg_label = f"Avg Price {params['volume_period_long']}D"
        change_short_label = f"{params['volume_period_short']}D Change"
        
        st.dataframe(
            display_df[['ticker', 'ratio', 'volume_usd_7d_M', 'volume_usd_90d_M', 
                       'price', 'price_90d_avg', 'change_7d', 'change_30d', 'score']].round(2),
            column_config={
                'ticker': 'Ticker',
                'ratio': st.column_config.NumberColumn('Volume Ratio', format="%.1fx"),
                'volume_usd_7d_M': st.column_config.NumberColumn(vol_short_label, format="$%.1fM"),
                'volume_usd_90d_M': st.column_config.NumberColumn(vol_long_label, format="$%.1fM"),
                'price': st.column_config.NumberColumn('Current Price', format="$%.2f"),
                'price_90d_avg': st.column_config.NumberColumn(price_avg_label, format="$%.2f"),
                'change_7d': st.column_config.NumberColumn(change_short_label, format="%.1f%%"),
                'change_30d': st.column_config.NumberColumn('30D Change', format="%.1f%%"),
                'score': st.column_config.NumberColumn('Score', format="%.1f")
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
                    file_name=f"sharks_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            csv_data_all = sharks_df.to_csv(index=False)
            st.download_button(
                label="📥 Download All Sharks",
                data=csv_data_all,
                file_name=f"sharks_all_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

def show_instructions():
    """Show initial instructions"""
    st.markdown("""
    ## 🆕 No saved results found
    
    **How to use:** Download data → Adjust filters (optional) → Run analysis
    
    Click **🔍 Run Shark Analysis** to start! 🏊‍♂️
    
    ---
    
    💡 **Tip:** After running an analysis, the results will be automatically displayed when you open the page next time.
    """)

if __name__ == "__main__":
    main() 