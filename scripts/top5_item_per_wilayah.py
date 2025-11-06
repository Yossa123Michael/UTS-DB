#!/usr/bin/env python3
"""
Compute Top 5 items with the most transactions per DKI Jakarta wilayah.

This script analyzes transaction data from a CSV file and computes:
- Top 5 items by transaction count for each DKI Jakarta wilayah
- Aggregations per wilayah + item: transaksi_count, qty_total, harga_first, nilai_total
"""

import pandas as pd
import re
import sys
from pathlib import Path


def parse_indonesian_number(value):
    """
    Parse Indonesian number format (e.g., "31.700,00" -> 31700.0)
    Handles thousands separator (.) and decimal comma (,)
    Returns None for empty/invalid values
    """
    if pd.isna(value) or value == '':
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    if not value_str:
        return None
    
    try:
        # Remove thousands separator (.) and replace decimal comma (,) with dot (.)
        cleaned = value_str.replace('.', '').replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def normalize_column_name(col):
    """Normalize column names by stripping spaces and converting to lowercase"""
    return col.strip().lower()


def detect_wilayah(lokasi_alamat):
    """
    Detect DKI Jakarta wilayah from location string using regex patterns.
    Returns wilayah name or 'Lainnya/Unknown' if not matched.
    """
    if pd.isna(lokasi_alamat):
        return 'Lainnya/Unknown'
    
    lokasi_upper = str(lokasi_alamat).upper()
    
    # Patterns for each wilayah (case-insensitive)
    patterns = {
        'Jakarta Pusat': r'JAKARTA\s*PUSAT',
        'Jakarta Timur': r'JAKARTA\s*TIMUR',
        'Jakarta Barat': r'JAKARTA\s*BARAT',
        'Jakarta Selatan': r'JAKARTA\s*SELATAN',
        'Jakarta Utara': r'JAKARTA\s*UTARA',
        'Kepulauan Seribu': r'KEP(?:ULAUAN)?\s*SERIBU',
    }
    
    for wilayah, pattern in patterns.items():
        if re.search(pattern, lokasi_upper):
            return wilayah
    
    return 'Lainnya/Unknown'


def read_csv_with_encoding(filepath):
    """
    Read CSV file with robust encoding detection.
    Tries utf-8, utf-8-sig, and latin-1 encodings.
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            print(f"Successfully read CSV with encoding: {encoding}")
            return df
        except (UnicodeDecodeError, Exception) as e:
            print(f"Failed to read with {encoding}: {e}")
            continue
    
    raise ValueError(f"Could not read CSV file with any of the tried encodings: {encodings}")


def normalize_dataframe_columns(df):
    """
    Normalize DataFrame column names to handle variations.
    Creates a mapping from normalized names to actual column names.
    """
    column_mapping = {}
    for col in df.columns:
        normalized = normalize_column_name(col)
        column_mapping[normalized] = col
    
    return column_mapping


def compute_top5_per_wilayah(csv_path, output_path):
    """
    Main function to compute top 5 items per wilayah.
    """
    print(f"Reading CSV from: {csv_path}")
    
    # Read CSV with encoding detection
    df = read_csv_with_encoding(csv_path)
    print(f"Total rows read: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Normalize column names
    col_map = normalize_dataframe_columns(df)
    
    # Identify required columns
    required_cols = {
        'idtransaksi': col_map.get('idtransaksi'),
        'lokasialamattoko': col_map.get('lokasialamattoko'),
        'kodeitem': col_map.get('kodeitem'),
        'deskripsi': col_map.get('deskripsi'),
        'qty': col_map.get('qty'),
        'harga': col_map.get('harga'),
        'nilai': col_map.get('nilai'),
    }
    
    # Check for missing columns
    missing = [k for k, v in required_cols.items() if v is None]
    if missing:
        print(f"Warning: Missing columns: {missing}")
        # Try to find them anyway
        for col in missing:
            for actual_col in df.columns:
                if col in normalize_column_name(actual_col):
                    required_cols[col] = actual_col
                    print(f"Found {col} as {actual_col}")
                    break
    
    # Detect wilayah
    df['wilayah'] = df[required_cols['lokasialamattoko']].apply(detect_wilayah)
    
    # Parse numeric columns
    print("Parsing numeric values...")
    df['qty_parsed'] = df[required_cols['qty']].apply(parse_indonesian_number)
    df['qty_parsed'] = df['qty_parsed'].fillna(0.0)  # Empty Qty -> 0
    
    df['harga_parsed'] = df[required_cols['harga']].apply(parse_indonesian_number)
    
    # Handle Nilai column - prefer CSV column if present, otherwise compute
    if required_cols['nilai'] and required_cols['nilai'] in df.columns:
        df['nilai_parsed'] = df[required_cols['nilai']].apply(parse_indonesian_number)
    else:
        print("Nilai column not found, computing from Harga * Qty")
        df['nilai_parsed'] = None
    
    # Compute nilai_per_row: use parsed Nilai if available, otherwise Harga * Qty
    def compute_nilai_row(row):
        if pd.notna(row['nilai_parsed']):
            return row['nilai_parsed']
        else:
            harga = row['harga_parsed'] if pd.notna(row['harga_parsed']) else 0.0
            qty = row['qty_parsed'] if pd.notna(row['qty_parsed']) else 0.0
            return harga * qty
    
    df['nilai_per_row'] = df.apply(compute_nilai_row, axis=1)
    
    # Filter only the 6 DKI Jakarta wilayah
    dki_wilayah = ['Jakarta Pusat', 'Jakarta Timur', 'Jakarta Barat', 
                   'Jakarta Selatan', 'Jakarta Utara', 'Kepulauan Seribu']
    
    df_dki = df[df['wilayah'].isin(dki_wilayah)].copy()
    print(f"Rows after filtering for DKI Jakarta wilayah: {len(df_dki)}")
    
    # Group by [wilayah, kodeitem, deskripsi]
    print("Grouping and aggregating...")
    grouped = df_dki.groupby(['wilayah', required_cols['kodeitem'], required_cols['deskripsi']]).agg(
        transaksi_count=(required_cols['idtransaksi'], 'nunique'),
        qty_total=('qty_parsed', 'sum'),
        harga_first=('harga_parsed', lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None),
        nilai_total=('nilai_per_row', 'sum')
    ).reset_index()
    
    # Rename columns to match expected output
    grouped = grouped.rename(columns={
        required_cols['kodeitem']: 'kodeitem',
        required_cols['deskripsi']: 'deskripsi'
    })
    
    # Sort within each wilayah and select top 5
    print("Selecting top 5 per wilayah...")
    top5_list = []
    
    for wilayah in dki_wilayah:
        wilayah_data = grouped[grouped['wilayah'] == wilayah].copy()
        
        # Sort by transaksi_count desc, qty_total desc, nilai_total desc
        wilayah_data = wilayah_data.sort_values(
            by=['transaksi_count', 'qty_total', 'nilai_total'],
            ascending=[False, False, False]
        ).head(5)
        
        top5_list.append(wilayah_data)
    
    result = pd.concat(top5_list, ignore_index=True)
    
    # Create output directory if needed
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    print(f"\nWriting results to: {output_path}")
    result.to_csv(output_path, index=False)
    
    # Print summary
    print("\n" + "="*80)
    print("TOP 5 ITEMS PER WILAYAH - SUMMARY")
    print("="*80)
    
    for wilayah in dki_wilayah:
        wilayah_data = result[result['wilayah'] == wilayah]
        print(f"\n{wilayah} ({len(wilayah_data)} items):")
        print("-" * 80)
        
        for idx, row in wilayah_data.iterrows():
            print(f"  {row['kodeitem']}: {row['deskripsi'][:50]}")
            harga_str = f"{row['harga_first']:.2f}" if pd.notna(row['harga_first']) else 'N/A'
            print(f"    Transaksi: {row['transaksi_count']}, "
                  f"Qty Total: {row['qty_total']:.2f}, "
                  f"Harga First: {harga_str}, "
                  f"Nilai Total: {row['nilai_total']:.2f}")
    
    print("\n" + "="*80)
    print(f"Results written to: {output_path}")
    print("="*80)


def main():
    # Default paths
    csv_path = "Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv"
    output_path = "Hasil/top5_item_per_wilayah.csv"
    
    # Allow command-line overrides
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    try:
        compute_top5_per_wilayah(csv_path, output_path)
        print("\nScript completed successfully!")
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
