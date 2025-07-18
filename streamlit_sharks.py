import streamlit as st
import pandas as pd
import numpy as np
import os
import subprocess
import sys
from datetime import datetime
from shark_analyzer import SharkAnalyzer

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
    """Run shark analysis with custom parameters"""
    
    st.info("🔍 Starting shark analysis...")
    
    # Create analyzer with custom parameters
    analyzer = SharkAnalyzer(
        min_volume_usd=min_volume_usd,
        volume_ratio_min=volume_ratio_min,
        spike_multiplier=spike_multiplier,
        min_price_90d=1.0,  # Fixed - now handled in display filters
        min_current_price=1.0,  # Fixed - now handled in display filters
        allow_negative_performance=False,
        silent_sharks_threshold=silent_sharks_threshold,
        min_data_days=90,
        filter_derivatives=False,  # Fixed - now handled in display filters
        enable_pattern_detection=enable_pattern_detection
    )
    
    # Run analysis with progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    with log_container:
        log_placeholder = st.empty()
        
        # Capture logs
        logs = []
        
        def log_callback(message):
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            log_placeholder.text_area(
                "Analysis Log:",
                value="\n".join(logs[-15:]),
                height=300,
                disabled=True
            )
        
        def progress_callback(p):
            progress_bar.progress(p)
            
        def status_callback(s):
            status_text.text(s)
        
        # Run analysis
        sharks_df, silent_sharks_df = analyzer.analyze(
            progress_callback=progress_callback,
            status_callback=status_callback,
            log_callback=log_callback
        )
    
    progress_bar.progress(1.0)
    status_text.text("✅ Analysis completed!")
    
    # Display results
    display_results(sharks_df, silent_sharks_df)

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
    
    # Aplicar filtros de visualização
    filtered_df = sharks_df.copy()
    
    # Filtrar por volume ratio mínimo
    filtered_df = filtered_df[filtered_df['ratio'] >= display_min_ratio]
    
    # Filtrar por mudança de preço máxima
    filtered_df = filtered_df[filtered_df['change_7d'] <= display_max_change]
    
    # Filtrar por preço mínimo
    filtered_df = filtered_df[filtered_df['price'] >= display_min_price]
    
    # Filtrar derivatives se marcado
    if hide_derivatives:
        # Filtrar tickers que terminam com sufixos de derivatives
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