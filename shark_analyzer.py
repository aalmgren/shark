import pandas as pd
import numpy as np
import os
from datetime import datetime
import multiprocessing as mp
from functools import partial

class SharkAnalyzer:
    """Parametrized shark detection analyzer for institutional accumulation patterns"""
    
    def __init__(self, 
                 min_volume_usd=10_000_000,
                 volume_ratio_min=1.5,
                 spike_multiplier=2.0,
                 min_price_90d=5.0,
                 min_current_price=10.0,
                 allow_negative_performance=False,
                 silent_sharks_threshold=5.0,
                 min_data_days=90,
                 filter_derivatives=True,
                 enable_pattern_detection=True):
        
        self.min_volume_usd = min_volume_usd
        self.volume_ratio_min = volume_ratio_min
        self.spike_multiplier = spike_multiplier
        self.min_price_90d = min_price_90d
        self.min_current_price = min_current_price
        self.allow_negative_performance = allow_negative_performance
        self.silent_sharks_threshold = silent_sharks_threshold
        self.min_data_days = min_data_days
        self.filter_derivatives = filter_derivatives
        self.enable_pattern_detection = enable_pattern_detection
        
        # Callbacks for progress tracking
        self.progress_callback = None
        self.status_callback = None
        self.log_callback = None
    
    def log(self, message):
        """Log message if callback is set"""
        if self.log_callback:
            self.log_callback(message)
    
    def set_status(self, status):
        """Update status if callback is set"""
        if self.status_callback:
            self.status_callback(status)
    
    def set_progress(self, progress):
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def process_file(self, file_info):
        """Process a single CSV file"""
        file_path, filename = file_info
        try:
            # Extract ticker from filename
            ticker = filename.split('_')[0] if '_' in filename else filename.replace('.csv', '')
            
            # Filter derivatives if enabled
            if self.filter_derivatives:
                if ticker.endswith(('W', 'WS', 'U', 'R', 'P', 'PR', 'X', 'L', 'Z')):
                    return None
            
            # Read only necessary columns
            df = pd.read_csv(file_path, usecols=['Date', 'Close', 'Volume'])
            if len(df) < self.min_data_days:
                return None
            
            df['ticker'] = ticker
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            return df
        except Exception as e:
            return None
    
    def detect_price_pattern(self, ticker_data):
        """Detect price patterns - reject declining prices after volume spikes"""
        if not self.enable_pattern_detection:
            return True
            
        try:
            ticker = ticker_data['ticker'].iloc[0]
            
            # Calculate volume in USD
            ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
            
            # Last 20 days for analysis
            recent_data = ticker_data.tail(20).copy()
            volume_mean = recent_data['volume_usd'].mean()
            
            # Check for declining prices after spike in recent days
            last_4_volumes = recent_data['volume_usd'].tail(4).values
            last_4_prices = recent_data['Close'].tail(4).values
            
            if len(last_4_volumes) >= 4 and len(last_4_prices) >= 4:
                # If there's a volume spike followed by 3 declining prices, reject
                if last_4_volumes[0] > (volume_mean * self.spike_multiplier):
                    if (last_4_prices[1] < last_4_prices[0] and 
                        last_4_prices[2] < last_4_prices[1] and 
                        last_4_prices[3] < last_4_prices[2]):
                        self.log(f"❌ {ticker}: Rejected for declining prices after volume spike")
                        return False
            return True
        except Exception as e:
            return True
    
    def analyze_ticker(self, ticker_data):
        """Analyze a single ticker for volume patterns"""
        try:
            # Sort by date
            ticker_data = ticker_data.sort_values('Date')
            ticker = ticker_data['ticker'].iloc[0]
            
            # Check minimum data requirement
            if len(ticker_data) < self.min_data_days:
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
            
            # Apply filters
            if volume_usd_90d < self.min_volume_usd:
                return None
            
            if price_90d_avg <= self.min_price_90d:
                return None
            
            # Calculate price changes
            current_price = ticker_data['Close'].iloc[-1]
            
            if current_price <= self.min_current_price:
                return None
            
            price_7d_ago = ticker_data['Close'].iloc[-7]
            price_30d_ago = ticker_data['Close'].iloc[-30]
            
            price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
            price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
            
            # Filter performance if not allowing negative
            if not self.allow_negative_performance:
                if price_change_7d <= 0 or price_change_30d <= 0:
                    return None
            
            # Volume ratio calculation
            volume_ratio = volume_usd_7d / volume_usd_90d if volume_usd_90d > 0 else 0
            
            # Check volume ratio and price pattern
            if volume_ratio >= self.volume_ratio_min and self.detect_price_pattern(ticker_data):
                # Calculate score
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
    
    def analyze(self, progress_callback=None, status_callback=None, log_callback=None):
        """Main analysis method"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.log_callback = log_callback
        
        self.log("🦈 STARTING SHARK DETECTION")
        self.set_status("Collecting data files...")
        self.set_progress(0.0)
        
        # 1. Collect all CSV files
        all_files = []
        for data_dir in ['nasdaq_database', 'additional_database']:
            if os.path.exists(data_dir):
                files = [(os.path.join(data_dir, f), f) for f in os.listdir(data_dir) if f.endswith('.csv')]
                all_files.extend(files)
        
        if not all_files:
            self.log("❌ No CSV files found")
            return None, None
        
        self.log(f"📊 Found {len(all_files)} data files")
        self.set_progress(0.1)
        
        # 2. Process files in parallel
        self.set_status("Processing data files...")
        
        # Use sequential processing in Streamlit to avoid pickle issues
        processed = []
        for i, file_info in enumerate(all_files):
            processed.append(self.process_file(file_info))
            if i % 100 == 0:  # Update progress every 100 files
                progress = 0.1 + 0.2 * i / len(all_files)
                self.set_progress(progress)
        
        all_data = [df for df in processed if df is not None]
        
        if not all_data:
            self.log("❌ No valid data found")
            return None, None
        
        self.set_progress(0.3)
        
        # 3. Consolidate data
        self.set_status("Consolidating data...")
        df = pd.concat(all_data, ignore_index=True)
        unique_tickers = df['ticker'].nunique()
        
        self.log(f"✅ Data loaded: {len(df):,} records from {unique_tickers} tickers")
        self.set_progress(0.4)
        
        # 4. Analyze each ticker
        self.set_status("Analyzing tickers for shark patterns...")
        
        ticker_groups = [group for _, group in df.groupby('ticker')]
        total_tickers = len(ticker_groups)
        
        # Process sequentially to avoid pickle issues in Streamlit
        analyzed = []
        
        for i, ticker_group in enumerate(ticker_groups):
            result = self.analyze_ticker(ticker_group)
            if result is not None:
                analyzed.append(result)
            
            # Update progress every 50 tickers
            if i % 50 == 0 or i == total_tickers - 1:
                progress = 0.4 + 0.5 * (i + 1) / total_tickers
                self.set_progress(min(progress, 0.9))
                self.set_status(f"Analyzed {i + 1}/{total_tickers} tickers...")
        
        if not analyzed:
            self.log("❌ No sharks detected with current parameters")
            return None, None
        
        self.set_progress(0.95)
        
        # 5. Create results DataFrames
        self.set_status("Generating results...")
        
        sharks_df = pd.DataFrame(analyzed)
        sharks_df = sharks_df.sort_values('score', ascending=False)
        
        # Create silent sharks subset
        silent_sharks_df = sharks_df[sharks_df['change_7d'] <= self.silent_sharks_threshold]
        
        # Save results to files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        sharks_df.to_csv('institutional_accumulation_candidates.csv', index=False)
        silent_sharks_df.to_csv('silent_sharks.csv', index=False)
        
        self.set_progress(1.0)
        
        # 6. Generate summary logs
        total_sharks = len(sharks_df)
        mega_sharks = len(sharks_df[sharks_df['ratio'] >= 3])
        big_sharks = len(sharks_df[(sharks_df['ratio'] >= 2) & (sharks_df['ratio'] < 3)])
        regular_sharks = len(sharks_df[(sharks_df['ratio'] >= 1.5) & (sharks_df['ratio'] < 2)])
        silent_count = len(silent_sharks_df)
        
        self.log("=" * 60)
        self.log("🦈 SHARK DETECTION COMPLETED!")
        self.log(f"📊 RESULTS SUMMARY:")
        self.log(f"   🦈 Total Sharks: {total_sharks}")
        self.log(f"   🔥 Mega Sharks (3x+): {mega_sharks}")
        self.log(f"   ⚡ Big Sharks (2-3x): {big_sharks}")
        self.log(f"   🦈 Regular Sharks (1.5-2x): {regular_sharks}")
        self.log(f"   🤫 Silent Sharks: {silent_count}")
        self.log("=" * 60)
        
        # Log top 10 sharks
        if total_sharks > 0:
            self.log("🏆 TOP 10 SHARKS:")
            for i, (_, shark) in enumerate(sharks_df.head(10).iterrows(), 1):
                self.log(f"{i:2d}. {shark['ticker']:<6} - {shark['ratio']:.1f}x volume, "
                        f"{shark['change_7d']:+.1f}% (7d), Score: {shark['score']:.1f}")
        
        self.log(f"💾 Files saved: institutional_accumulation_candidates.csv, silent_sharks.csv")
        self.set_status("✅ Analysis completed!")
        
        return sharks_df, silent_sharks_df 