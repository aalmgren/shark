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
    st.sidebar.caption("These affect HOW sharks are detected")
    
    # Parâmetros de análise
    min_volume_usd = st.sidebar.slider(
        "Min daily volume (USD)",
        min_value=1_000_000,
        max_value=50_000_000,
        value=10_000_000,
        step=1_000_000,
        format="$%dM",
        help="Minimum average daily volume in USD over 90 days"
    ) 
    
    volume_ratio_min = st.sidebar.slider(
        "Volume spike ratio",
        min_value=1.0,
        max_value=5.0,
        value=1.5,
        step=0.1,
        format="%.1fx",
        help="Minimum ratio of 7-day vs 90-day average volume"
    )
    
    spike_multiplier = st.sidebar.slider(
        "Spike detection multiplier",
        min_value=1.5,
        max_value=4.0,
        value=2.0,
        step=0.1,
        format="%.1fx",
        help="Volume multiplier to detect spikes for pattern analysis"
    )
    
    silent_sharks_threshold = st.sidebar.slider(
        "Silent sharks threshold",
        min_value=0.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
        format="%.1f%%",
        help="Maximum 7-day change for silent sharks category"
    )
    
    enable_pattern_detection = st.sidebar.checkbox(
        "Enable price pattern detection",
        value=True,
        help="Reject stocks with declining prices after volume spikes"
    )
    
    # Main content area
    if analyze_button:
        if not check_data_availability():
            st.error("❌ No data available. Please download data first.")
            return
            
        run_analysis(
            min_volume_usd=min_volume_usd,
            volume_ratio_min=volume_ratio_min,
            spike_multiplier=spike_multiplier,
            silent_sharks_threshold=silent_sharks_threshold,
            enable_pattern_detection=enable_pattern_detection
        )
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

def run_analysis(min_volume_usd, volume_ratio_min, spike_multiplier,
                silent_sharks_threshold, enable_pattern_detection):
    """Run shark analysis using analyze_sharks.py functions"""
    
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
            min_volume_usd, volume_ratio_min, silent_sharks_threshold,
            log_message, progress_bar, status_text
        )
    
    progress_bar.progress(1.0)
    status_text.text("✅ Analysis completed!")
    
    # Display results
    display_results(sharks_df, silent_sharks_df)

def run_sharks_analysis_simple(min_volume_usd, volume_ratio_min, silent_sharks_threshold, 
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
        result = analyze_ticker_simple(ticker_group, min_volume_usd, volume_ratio_min)
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

def analyze_ticker_simple(ticker_data, min_volume_usd, volume_ratio_min):
    """Simplified ticker analysis for Streamlit"""
    try:
        ticker_data = ticker_data.sort_values('Date')
        ticker = ticker_data['ticker'].iloc[0]
        
        if len(ticker_data) < 90:
            return None
            
        # Calculate volume in USD
        ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
            
        # Calculate averages
        last_7d = ticker_data.tail(7)
        previous_90d = ticker_data.iloc[-97:-7] if len(ticker_data) >= 97 else ticker_data.iloc[:-7]
        
        volume_usd_90d = previous_90d['volume_usd'].mean()
        volume_usd_7d = last_7d['volume_usd'].mean()
        volume_90d = previous_90d['Volume'].mean()
        volume_7d = last_7d['Volume'].mean()
        price_90d_avg = ticker_data['Close'].tail(90).mean()
        
        # Apply basic filters
        if volume_usd_90d < min_volume_usd:
            return None
            
        if price_90d_avg <= 1.0:  # Very basic price filter
            return None
        
        # Calculate price changes
        current_price = ticker_data['Close'].iloc[-1]
        
        if current_price <= 1.0:
            return None
            
        price_7d_ago = ticker_data['Close'].iloc[-7]
        price_30d_ago = ticker_data['Close'].iloc[-30]
        
        price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
        
        # Filter negative performance
        if price_change_7d <= 0 or price_change_30d <= 0:
            return None
        
        # Volume ratio calculation
        volume_ratio = volume_usd_7d / volume_usd_90d if volume_usd_90d > 0 else 0
        
        # Check volume ratio
        if volume_ratio >= volume_ratio_min:
            score = volume_ratio * (1 + price_change_7d / 100)
            
            return {
                'ticker': ticker,
                'ratio': volume_ratio,
                'volume_7d': volume_7d,
                'volume_90d': volume_90d,
                'volume_usd_7d': volume_usd_7d,
                'volume_usd_90d': volume_usd_90d,
                'price': current_price,
                'price_90d_avg': price_90d_avg,
                'change_7d': price_change_7d,
                'change_30d': price_change_30d,
                'score': score
            }
    except Exception as e:
        pass
    return None

def display_results(sharks_df, silent_sharks_df):
    """Display analysis results with tables and charts"""
    st.header("📊 Results")
    
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
    
    # Filtros de visualização (só aparecem quando há dados)
    st.subheader("🔍 Display Filters")
    st.caption("Filter the results below (does not re-run analysis)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        show_silent_only = st.checkbox("🤫 Only Silent Sharks", help="Show only stocks with price change ≤ 5%")
    
    with col2:
        display_min_ratio = st.slider("Min Ratio", 1.0, 10.0, 1.0, 0.1, format="%.1fx", help="Hide sharks below this ratio")
    
    with col3:
        display_max_change = st.slider("Max Change", 0.0, 100.0, 100.0, 1.0, format="%.0f%%", help="Hide sharks above this change")
    
    with col4:
        display_min_price = st.slider("Min Price", 1.0, 50.0, 1.0, 1.0, format="$%.0f", help="Hide stocks below this price")
    
    with col5:
        hide_derivatives = st.checkbox("Hide Derivatives", value=False, help="Hide warrants, units, rights, etc.")
    
    # Aplicar filtros de visualização (com debug)
    filtered_df = sharks_df.copy()
    st.write(f"🐛 Debug: Starting with {len(filtered_df)} sharks")
    
    # Filtrar por volume ratio mínimo
    filtered_df = filtered_df[filtered_df['ratio'] >= display_min_ratio]
    st.write(f"🐛 Debug: After ratio filter (>={display_min_ratio}): {len(filtered_df)} sharks")
    
    # Filtrar por mudança de preço máxima
    filtered_df = filtered_df[filtered_df['change_7d'] <= display_max_change]
    st.write(f"🐛 Debug: After max change filter (<={display_max_change}%): {len(filtered_df)} sharks")
    
    # Filtrar por preço mínimo
    filtered_df = filtered_df[filtered_df['price'] >= display_min_price]
    st.write(f"🐛 Debug: After min price filter (>=${display_min_price}): {len(filtered_df)} sharks")
    
    # Filtrar derivatives se marcado
    if hide_derivatives:
        filtered_df = filtered_df[~filtered_df['ticker'].str.endswith(('W', 'WS', 'U', 'R', 'P', 'PR', 'X', 'L', 'Z'))]
        st.write(f"🐛 Debug: After derivatives filter: {len(filtered_df)} sharks")
    
    # Filtrar apenas silent sharks se marcado
    if show_silent_only:
        filtered_df = filtered_df[filtered_df['change_7d'] <= 5.0]
        st.write(f"🐛 Debug: After silent sharks filter (<=5%): {len(filtered_df)} sharks")
    
    # Tabela de sharks filtrados
    st.subheader(f"🦈 Sharks Found ({len(filtered_df)} results)")
    
    if len(filtered_df) == 0:
        st.warning("No sharks match the current filters. Try adjusting the criteria.")
    else:
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['volume_usd_7d_M'] = display_df['volume_usd_7d'] / 1_000_000
        display_df['volume_usd_90d_M'] = display_df['volume_usd_90d'] / 1_000_000
        
        st.dataframe(
            display_df[['ticker', 'ratio', 'volume_usd_7d_M', 'volume_usd_90d_M', 
                       'price', 'price_90d_avg', 'change_7d', 'change_30d', 'score']].round(2),
            column_config={
                'ticker': 'Ticker',
                'ratio': st.column_config.NumberColumn('Volume Ratio', format="%.1fx"),
                'volume_usd_7d_M': st.column_config.NumberColumn('Vol 7D ($M)', format="$%.1fM"),
                'volume_usd_90d_M': st.column_config.NumberColumn('Vol 90D ($M)', format="$%.1fM"),
                'price': st.column_config.NumberColumn('Current Price', format="$%.2f"),
                'price_90d_avg': st.column_config.NumberColumn('Avg Price 90D', format="$%.2f"),
                'change_7d': st.column_config.NumberColumn('7D Change', format="%.1f%%"),
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
    **How to use:** Download data → Adjust filters (optional) → Run analysis
    
    Click **Run Analysis** to start! 🏊‍♂️
    """)

if __name__ == "__main__":
    main() 