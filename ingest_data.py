import pandas as pd
import os

RAW_DIR = "raw_data"
OUTPUT_PATH = "data/training_data.csv"

def process_file(filename, text_col, label_col):
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠️ Missing: {filename}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        
        # --- FIX 1: AUTO-CLEAN COLUMN NAMES ---
        # This fixes issues like "Label", "label ", " TEXT", etc.
        df.columns = df.columns.str.strip().str.lower()
        
        # Normalize user input to match our clean columns
        text_col = text_col.strip().lower()
        label_col = label_col.strip().lower()

        # Debug: Check if columns actually exist now
        if text_col not in df.columns or label_col not in df.columns:
            print(f"Error in {filename}: Could not find columns '{text_col}' or '{label_col}'")
            print(f"   (Found these instead: {list(df.columns)})")
            return pd.DataFrame()

        # Rename to standard 'text' and 'label'
        df = df.rename(columns={text_col: 'text', label_col: 'label'})
        df = df[['text', 'label']]
        
        # Clean Labels: Convert everything (toxic, 1, hate) -> 1, (safe, 0) -> 0
        def clean_label(val):
            s = str(val).lower().strip()
            if s in ['1', 'toxic', 'hate', 'offensive', 'bad', 'yes']: return 1
            return 0 

        df['label'] = df['label'].apply(clean_label)
        print(f"Loaded {filename}: {len(df)} rows")
        return df

    except Exception as e:
        print(f"Critical Error reading {filename}: {e}")
        return pd.DataFrame()

if not os.path.exists("data"): os.makedirs("data")

print("⚙️ Processing Datasets...")

# 1. Map your specific CSVs (The script will now auto-lowercase these keys)
df1 = process_file("english.csv", "tweet", "class")       
df2 = process_file("hindi.csv", "text", "label")          
df3 = process_file("hinglish.csv", "text", "hate_label")  

# 2. Combine & Save
master = pd.concat([df1, df2, df3], ignore_index=True).dropna().drop_duplicates()
master.to_csv(OUTPUT_PATH, index=False)

if len(master) > 0:
    print(f" MASTER DATASET READY: {len(master)} total examples.")
else:
    print(" Failed to create dataset. Check the errors above.")
    