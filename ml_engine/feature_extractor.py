import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

INPUT_FILE = "ml_engine/dataset.csv"
OUTPUT_FILE = "ml_engine/features.csv"

def process_data():
    print("🔄 Loading raw dataset...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("❌ Error: dataset.csv not found. Run the harvester first!")
        return

    print(f"📊 Raw data shape: {df.shape}")

    # --- FEATURE ENGINEERING ---

    # 1. Feature: Path Length (Longer paths = potential overflow/SQLi)
    df['path_length'] = df['path'].apply(len)

    # 2. Feature: Count of Digits in Path (High count = potential BOLA/ID enumeration)
    # Example: /user/12345 has 5 digits
    df['digit_count'] = df['path'].apply(lambda x: sum(c.isdigit() for c in x))

    # 3. Feature: Count of Special Characters (High count = potential Injection)
    # We look for dangerous chars: ' " - < > ; %
    special_chars = set(['\'', '"', '-', '<', '>', ';', '%', '(', ')'])
    df['special_char_count'] = df['path'].apply(lambda x: sum(1 for c in x if c in special_chars))

    # 4. Feature: Body Length (Already exists, just ensuring it's numeric)
    df['body_length'] = pd.to_numeric(df['body_length'], errors='coerce').fillna(0)

    # 5. Feature: HTTP Method (Convert GET/POST to 0/1)
    # GET=0, POST=1, DELETE=2, etc.
    le = LabelEncoder()
    df['method_code'] = le.fit_transform(df['method'])

    # --- CLEANUP ---

    # Select only the numerical columns for the AI
    feature_cols = ['path_length', 'digit_count', 'special_char_count', 'body_length', 'method_code']
    final_df = df[feature_cols]

    print("\n--- Processed Features Sample ---")
    print(final_df.head())

    # Save to CSV
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Features saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_data()