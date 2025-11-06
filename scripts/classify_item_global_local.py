#!/usr/bin/env python3
"""
Classify items into Global, Regional, or Local based on distribution across DKI Jakarta wilayah.
"""

import argparse
import re
from pathlib import Path

import pandas as pd
import numpy as np


# Wilayah patterns for detection
WILAYAH_PATTERNS = {
    'Jakarta Pusat': r'JAKARTA\s*PUSAT',
    'Jakarta Timur': r'JAKARTA\s*TIMUR',
    'Jakarta Barat': r'JAKARTA\s*BARAT',
    'Jakarta Selatan': r'JAKARTA\s*SELATAN',
    'Jakarta Utara': r'JAKARTA\s*UTARA',
    'Kepulauan Seribu': r'KEP(?:ULAUAN)?\s*SERIBU',
}

# Classification thresholds
N_MIN = 30  # Minimum transaction count to classify
GLOBAL_PRESENCE_MIN = 4
GLOBAL_H_NORM_MIN = 0.70
GLOBAL_MAX_SHARE_MAX = 0.50
LOCAL_MAX_SHARE_MIN = 0.60
LOCAL_H_NORM_MAX = 0.40
LOCAL_LQ_MIN = 1.5


def parse_indonesian_number(value):
    """Parse Indonesian number format (e.g., '31.700,00' -> 31700.0)."""
    if pd.isna(value) or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and strip whitespace
    value_str = str(value).strip()
    if not value_str:
        return 0.0
    
    # Remove thousand separators (.) and replace decimal comma (,) with dot (.)
    value_str = value_str.replace('.', '').replace(',', '.')
    
    try:
        return float(value_str)
    except ValueError:
        return 0.0


def detect_wilayah(location: str) -> str:
    """Detect wilayah from LokasiAlamatToko using regex patterns."""
    if pd.isna(location):
        return 'Unknown'
    
    location_upper = str(location).upper()
    for wilayah, pattern in WILAYAH_PATTERNS.items():
        if re.search(pattern, location_upper, re.IGNORECASE):
            return wilayah
    
    return 'Unknown'


def load_data(csv_path: str, include_retur: bool = False) -> pd.DataFrame:
    """Load and preprocess CSV data with robust encoding."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            print(f"✓ Successfully loaded CSV with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"✗ Error loading CSV with {encoding}: {e}")
            continue
    
    if df is None:
        raise ValueError(f"Could not load CSV with any of the encodings: {encodings}")
    
    # Normalize column names (strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Print columns for debugging
    print(f"Columns found: {list(df.columns)}")
    
    # Filter by JenisTransaksi
    if not include_retur:
        df = df[df['JenisTransaksi'] == 'Pembelian'].copy()
        print(f"✓ Filtered to Pembelian only: {len(df)} rows")
    else:
        print(f"✓ Including all transaction types: {len(df)} rows")
    
    # Detect wilayah
    df['wilayah'] = df['LokasiAlamatToko'].apply(detect_wilayah)
    
    # Remove Unknown wilayah
    unknown_count = (df['wilayah'] == 'Unknown').sum()
    if unknown_count > 0:
        print(f"⚠ Removing {unknown_count} rows with Unknown wilayah")
    df = df[df['wilayah'] != 'Unknown'].copy()
    
    # Parse numeric fields
    df['Qty_parsed'] = df['Qty'].apply(parse_indonesian_number)
    df['Harga_parsed'] = df['Harga'].apply(parse_indonesian_number)
    
    # Handle Nilai column (may have leading space)
    nilai_col = None
    for col in df.columns:
        if 'nilai' in col.lower():
            nilai_col = col
            break
    
    if nilai_col:
        df['Nilai_parsed'] = df[nilai_col].apply(parse_indonesian_number)
    else:
        # Calculate Nilai from Harga × Qty
        df['Nilai_parsed'] = df['Harga_parsed'] * df['Qty_parsed']
        print("⚠ 'Nilai' column not found, calculated from Harga × Qty")
    
    print(f"✓ Data loaded: {len(df)} rows across {df['wilayah'].nunique()} wilayah")
    print(f"  Wilayah distribution: {df['wilayah'].value_counts().to_dict()}")
    
    return df


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-wilayah and per-item metrics."""
    
    # Group by item and wilayah
    wilayah_item_metrics = df.groupby(['Kodeitem', 'Deskripsi', 'wilayah']).agg({
        'idtransaksi': 'nunique',  # unique transaction count
        'Qty_parsed': 'sum',
        'Nilai_parsed': 'sum'
    }).reset_index()
    
    wilayah_item_metrics.columns = ['kodeitem', 'deskripsi', 'wilayah', 
                                     'transaksi_count', 'qty_total', 'nilai_total']
    
    # Pivot to get per-wilayah columns
    pivot_trx = wilayah_item_metrics.pivot_table(
        index=['kodeitem', 'deskripsi'],
        columns='wilayah',
        values='transaksi_count',
        fill_value=0
    ).reset_index()
    
    # Rename columns for transaction counts
    wilayah_cols = {}
    for col in pivot_trx.columns:
        if col in ['kodeitem', 'deskripsi']:
            continue
        wilayah_name = col.lower().replace(' ', '_').replace('jakarta_', '')
        wilayah_cols[col] = f'trx_{wilayah_name}'
    pivot_trx.rename(columns=wilayah_cols, inplace=True)
    
    # Compute item-level totals
    item_metrics = df.groupby(['Kodeitem', 'Deskripsi']).agg({
        'idtransaksi': 'nunique',
        'wilayah': lambda x: x.nunique()
    }).reset_index()
    
    item_metrics.columns = ['kodeitem', 'deskripsi', 'transaksi_count_total', 'presence_count']
    
    # Merge with pivot table
    result = item_metrics.merge(pivot_trx, on=['kodeitem', 'deskripsi'], how='left')
    
    # Fill NaN with 0 for wilayah columns
    trx_cols = [col for col in result.columns if col.startswith('trx_')]
    for col in trx_cols:
        result[col] = result[col].fillna(0).astype(int)
    
    return result, wilayah_item_metrics


def compute_entropy_and_shares(result: pd.DataFrame, wilayah_item_metrics: pd.DataFrame) -> pd.DataFrame:
    """Compute Shannon entropy, max_share, and dominant wilayah."""
    
    # Get transaction count columns
    trx_cols = [col for col in result.columns if col.startswith('trx_')]
    
    # Compute shares (p_w)
    for col in trx_cols:
        share_col = col.replace('trx_', 'share_')
        result[share_col] = result[col] / result['transaksi_count_total']
        result[share_col] = result[share_col].fillna(0)
    
    # Compute Shannon entropy H and normalized H_norm
    share_cols = [col for col in result.columns if col.startswith('share_')]
    
    def shannon_entropy(row):
        shares = [row[col] for col in share_cols if row[col] > 0]
        if not shares:
            return 0.0
        H = -sum(p * np.log(p) for p in shares if p > 0)
        return H
    
    result['H'] = result.apply(shannon_entropy, axis=1)
    
    # Normalize entropy: H_norm = H / log(W) where W is number of wilayah
    W = len(trx_cols)
    result['H_norm'] = result['H'] / np.log(W) if W > 1 else 0
    
    # Compute max_share
    result['max_share'] = result[share_cols].max(axis=1)
    
    # Find dominant wilayah (wilayah with max share)
    def find_dominant_wilayah(row):
        max_val = row['max_share']
        for col in share_cols:
            if row[col] == max_val:
                return col.replace('share_', '').replace('_', ' ').title()
        return ''
    
    result['wilayah_dominan'] = result.apply(find_dominant_wilayah, axis=1)
    
    # Drop temporary share columns
    result.drop(columns=share_cols, inplace=True)
    
    return result


def compute_location_quotient(result: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Compute Location Quotient (LQ) per wilayah for each item."""
    
    # Total transactions per wilayah across all items
    wilayah_totals = df.groupby('wilayah')['idtransaksi'].nunique().to_dict()
    total_all = df['idtransaksi'].nunique()
    
    # Compute LQ for each wilayah
    trx_cols = [col for col in result.columns if col.startswith('trx_')]
    lq_values = {}
    
    for col in trx_cols:
        wilayah_name = col.replace('trx_', '').replace('_', ' ').title()
        wilayah_key = None
        
        # Map back to original wilayah names
        for key in wilayah_totals.keys():
            if key.lower().replace(' ', '_').replace('jakarta_', '') == col.replace('trx_', ''):
                wilayah_key = key
                break
        
        if wilayah_key and wilayah_key in wilayah_totals:
            wilayah_total = wilayah_totals[wilayah_key]
            lq_col = col.replace('trx_', 'lq_')
            
            # LQ = (item_trx_in_wilayah / item_trx_total) / (wilayah_total / total_all)
            result[lq_col] = (result[col] / result['transaksi_count_total']) / (wilayah_total / total_all)
            result[lq_col] = result[lq_col].fillna(0)
            
            lq_values[wilayah_name] = lq_col
    
    # Find max LQ across all wilayah
    lq_cols = [col for col in result.columns if col.startswith('lq_')]
    if lq_cols:
        result['LQ_max'] = result[lq_cols].max(axis=1)
    else:
        result['LQ_max'] = 0
    
    # Drop intermediate LQ columns
    result.drop(columns=lq_cols, inplace=True, errors='ignore')
    
    return result


def classify_items(result: pd.DataFrame, n_min: int = N_MIN) -> pd.DataFrame:
    """Apply classification rules to label items."""
    
    def classify_item(row):
        # Low-Volume items
        if row['transaksi_count_total'] < n_min:
            return 'Low-Volume'
        
        # Global items
        if (row['presence_count'] >= GLOBAL_PRESENCE_MIN and 
            row['H_norm'] >= GLOBAL_H_NORM_MIN and 
            row['max_share'] <= GLOBAL_MAX_SHARE_MAX):
            return 'Global'
        
        # Local items
        if (row['presence_count'] == 1 or 
            (row['max_share'] >= LOCAL_MAX_SHARE_MIN and 
             row['H_norm'] <= LOCAL_H_NORM_MAX and 
             row['LQ_max'] >= LOCAL_LQ_MIN)):
            return 'Local'
        
        # Regional (everything else)
        return 'Regional'
    
    result['label'] = result.apply(classify_item, axis=1)
    
    return result


def print_summary(result: pd.DataFrame):
    """Print console summary of top 10 global and local items."""
    
    print("\n" + "="*80)
    print("CLASSIFICATION SUMMARY")
    print("="*80)
    
    # Overall statistics
    label_counts = result['label'].value_counts()
    print(f"\nOverall Distribution:")
    for label, count in label_counts.items():
        print(f"  {label:12s}: {count:5d} items")
    
    # Top 10 Global items
    global_items = result[result['label'] == 'Global'].nlargest(10, 'transaksi_count_total')
    if len(global_items) > 0:
        print(f"\n{'Top 10 Global Items':-^80}")
        print(f"{'Kode':<12} {'Description':<40} {'Trx Count':>10} {'H_norm':>8}")
        print("-" * 80)
        for _, row in global_items.iterrows():
            desc = row['deskripsi'][:38] + '..' if len(str(row['deskripsi'])) > 40 else row['deskripsi']
            print(f"{row['kodeitem']:<12} {desc:<40} {row['transaksi_count_total']:>10} {row['H_norm']:>8.3f}")
    
    # Top 10 Local items
    local_items = result[result['label'] == 'Local'].nlargest(10, 'transaksi_count_total')
    if len(local_items) > 0:
        print(f"\n{'Top 10 Local Items':-^80}")
        print(f"{'Kode':<12} {'Description':<40} {'Trx Count':>10} {'Max Share':>10}")
        print("-" * 80)
        for _, row in local_items.iterrows():
            desc = row['deskripsi'][:38] + '..' if len(str(row['deskripsi'])) > 40 else row['deskripsi']
            print(f"{row['kodeitem']:<12} {desc:<40} {row['transaksi_count_total']:>10} {row['max_share']:>10.3f}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Classify items into Global, Regional, or Local based on geographic distribution.'
    )
    parser.add_argument(
        'csv_path',
        type=str,
        help='Path to the transaction CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='Hasil/classifikasi_item_global_lokal.csv',
        help='Output CSV file path (default: Hasil/classifikasi_item_global_lokal.csv)'
    )
    parser.add_argument(
        '--include-retur',
        action='store_true',
        help='Include Retur transactions (default: Pembelian only)'
    )
    parser.add_argument(
        '--n-min',
        type=int,
        default=N_MIN,
        help=f'Minimum transaction count to classify (default: {N_MIN})'
    )
    
    args = parser.parse_args()
    
    print(f"Starting item classification...")
    print(f"  CSV: {args.csv_path}")
    print(f"  Output: {args.output}")
    print(f"  Include Retur: {args.include_retur}")
    print(f"  N_min: {args.n_min}")
    
    # Load data
    df = load_data(args.csv_path, args.include_retur)
    
    # Compute metrics
    result, wilayah_item_metrics = compute_metrics(df)
    
    # Compute entropy and shares
    result = compute_entropy_and_shares(result, wilayah_item_metrics)
    
    # Compute Location Quotient
    result = compute_location_quotient(result, df)
    
    # Classify items
    result = classify_items(result, args.n_min)
    
    # Sort by transaction count descending
    result = result.sort_values('transaksi_count_total', ascending=False)
    
    # Select and order output columns
    output_cols = ['kodeitem', 'deskripsi', 'transaksi_count_total', 'presence_count', 
                   'H_norm', 'max_share', 'wilayah_dominan', 'LQ_max', 'label']
    
    # Add per-wilayah transaction count columns
    trx_cols = sorted([col for col in result.columns if col.startswith('trx_')])
    output_cols.extend(trx_cols)
    
    # Filter columns that exist
    output_cols = [col for col in output_cols if col in result.columns]
    
    result_output = result[output_cols].copy()
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result_output.to_csv(args.output, index=False)
    print(f"\n✓ Classification complete! Output saved to: {args.output}")
    print(f"  Total items classified: {len(result_output)}")
    
    # Print summary
    print_summary(result)


if __name__ == '__main__':
    main()
