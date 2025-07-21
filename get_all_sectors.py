import pandas as pd
import yfinance as yf
import time
import os

# --- Configuration ---
INPUT_FILE = 'tick/tickers.csv'
OUTPUT_FILE = 'tick/tickers_with_sectors.csv'
BATCH_SIZE = 50  # Save progress every 50 tickers
# ---------------------

def save_to_csv(data, file_path):
    """Appends a list of dicts to a CSV file."""
    df_to_save = pd.DataFrame(data)
    # Append to the file. Write header only if the file doesn't exist yet.
    header = not os.path.exists(file_path)
    df_to_save.to_csv(file_path, mode='a', header=header, index=False)

# Read the original list of tickers
try:
    df_all_tickers = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"Error: The input file {INPUT_FILE} was not found.")
    exit()

# Check for already processed tickers to allow resuming
processed_tickers = set()
if os.path.exists(OUTPUT_FILE):
    try:
        df_processed = pd.read_csv(OUTPUT_FILE)
        processed_tickers = set(df_processed['ticker'])
        print(f"Resuming. Found {len(processed_tickers)} already processed tickers in {OUTPUT_FILE}.")
    except pd.errors.EmptyDataError:
        print(f"Output file {OUTPUT_FILE} is empty. Starting from scratch.")
    except Exception as e:
        print(f"Could not read the existing output file. Error: {e}. Starting fresh.")


results_batch = []
tickers_to_process = df_all_tickers[~df_all_tickers['ticker'].isin(processed_tickers)]

if tickers_to_process.empty:
    print("All tickers have already been processed. Nothing to do.")
    exit()

print(f"Starting to fetch info for {len(tickers_to_process)} remaining tickers...")
print("-" * 60)

# Iterate over the tickers that have not been processed yet
for index, row in tickers_to_process.iterrows():
    ticker_symbol = row['ticker']
    exchange = row['exchange']

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # --- Define fields to extract and their corresponding keys in the info dict ---
        fields_to_extract = {
            'sector': 'sector',
            'industry': 'industry',
            'market_cap': 'marketCap',
            'enterprise_value': 'enterpriseValue',
            'name': 'displayName'
        }
        
        extracted_data = {}
        all_fields_found = True
        
        for key, yahoo_key in fields_to_extract.items():
            value = info.get(yahoo_key)
            if value is None:
                all_fields_found = False
                break
            extracted_data[key] = value

        if all_fields_found:
            # Add the ticker and exchange info
            extracted_data['ticker'] = ticker_symbol
            extracted_data['exchange'] = exchange
            
            results_batch.append(extracted_data)
            print(f"SUCCESS: {ticker_symbol: <8} | Name: {extracted_data['name']: <25} | Market Cap: {extracted_data['market_cap']}")
        else:
            raise ValueError("One or more required fields not found")

    except Exception as e:
        error_message = str(e).replace('\n', ' ').replace('\r', '')
        print(f"   FAIL: {ticker_symbol: <8} | Reason: {error_message[:60]}")

    # Save the batch to CSV if it reaches the desired size
    if len(results_batch) >= BATCH_SIZE:
        save_to_csv(results_batch, OUTPUT_FILE)
        print(f"\n--- Progress saved for {len(results_batch)} tickers ---\n")
        results_batch = [] # Reset the batch

    time.sleep(0.05)

# Save any remaining results in the last batch
if results_batch:
    save_to_csv(results_batch, OUTPUT_FILE)
    print(f"\n--- Final batch of {len(results_batch)} tickers saved ---\n")

print("-" * 60)
print(f"Processing complete. All data saved to {OUTPUT_FILE}") 