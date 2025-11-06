#!/usr/bin/env python3
"""
Process transaction data to generate:
1. Top 5 items per wilayah (region)
2. Item classification (Global/Regional/Lokal)
"""

import csv
import os
from collections import defaultdict, Counter
from math import log

def extract_region(lokasi):
    """Extract Jakarta region from location string."""
    lokasi_upper = lokasi.upper()
    if 'JAKARTA PUSAT' in lokasi_upper:
        return 'Jakarta Pusat'
    elif 'JAKARTA UTARA' in lokasi_upper:
        return 'Jakarta Utara'
    elif 'JAKARTA TIMUR' in lokasi_upper:
        return 'Jakarta Timur'
    elif 'JAKARTA BARAT' in lokasi_upper:
        return 'Jakarta Barat'
    elif 'JAKARTA SELATAN' in lokasi_upper:
        return 'Jakarta Selatan'
    elif 'KEPULAUAN SERIBU' in lokasi_upper:
        return 'Kepulauan Seribu'
    return None

def parse_number(value):
    """Parse Indonesian number format to float."""
    if not value or not isinstance(value, str):
        return 0.0
    try:
        # Remove thousands separator (.) and replace decimal comma with period
        cleaned = value.replace('.', '').replace(',', '.').strip()
        return float(cleaned) if cleaned else 0.0
    except (ValueError, AttributeError):
        return 0.0

def process_transactions(csv_file):
    """Process transaction data and return aggregated results."""
    # Data structures
    items_by_region = defaultdict(lambda: defaultdict(lambda: {
        'qty': 0,
        'nilai': 0,
        'transactions': set(),
        'harga': None,
        'deskripsi': None
    }))
    
    item_presence = defaultdict(set)  # Track which regions have each item
    item_totals = defaultdict(lambda: {'transactions': 0, 'qty': 0, 'nilai': 0})
    
    print(f"Processing {csv_file}...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            lokasi = row.get('LokasiAlamatToko', '')
            wilayah = extract_region(lokasi)
            
            if not wilayah:
                continue
            
            kode_item = row.get('Kodeitem', '').strip()
            deskripsi = row.get('Deskripsi', '').strip()
            
            if not kode_item:
                continue
            
            # Parse quantities
            qty_str = row.get('Qty', '0').strip()
            try:
                qty = int(qty_str) if qty_str else 0
            except (ValueError, TypeError):
                qty = 0
            
            nilai = parse_number(row.get(' Nilai', '0'))
            harga = parse_number(row.get('Harga', '0'))
            idtransaksi = row.get('idtransaksi', '')
            
            # Update regional data
            items_by_region[wilayah][kode_item]['qty'] += qty
            items_by_region[wilayah][kode_item]['nilai'] += nilai
            items_by_region[wilayah][kode_item]['transactions'].add(idtransaksi)
            if items_by_region[wilayah][kode_item]['harga'] is None:
                items_by_region[wilayah][kode_item]['harga'] = harga
            items_by_region[wilayah][kode_item]['deskripsi'] = deskripsi
            
            # Track item presence across regions
            item_presence[kode_item].add(wilayah)
            
            # Track item totals
            item_totals[kode_item]['transactions'] += 1
            item_totals[kode_item]['qty'] += qty
            item_totals[kode_item]['nilai'] += nilai
    
    return items_by_region, item_presence, item_totals

def generate_top5_per_wilayah(items_by_region, output_file):
    """Generate CSV with top 5 items per region."""
    print(f"Generating {output_file}...")
    
    # Priority regions
    priority_regions = ['Jakarta Pusat', 'Jakarta Utara', 'Jakarta Timur']
    other_regions = ['Jakarta Barat', 'Jakarta Selatan', 'Kepulauan Seribu']
    
    all_regions = priority_regions + [r for r in other_regions if r in items_by_region]
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Wilayah', 'Rank', 'Kode Item', 'Deskripsi', 'Transaksi (unik)', 'Qty Total', 'Harga (first)', 'Nilai Total'])
        
        for wilayah in all_regions:
            if wilayah not in items_by_region:
                continue
            
            # Sort by number of unique transactions
            sorted_items = sorted(
                items_by_region[wilayah].items(),
                key=lambda x: len(x[1]['transactions']),
                reverse=True
            )[:5]
            
            for rank, (kode, data) in enumerate(sorted_items, 1):
                writer.writerow([
                    wilayah,
                    rank,
                    kode,
                    data['deskripsi'],
                    len(data['transactions']),
                    data['qty'],
                    f"{data['harga']:.2f}" if data['harga'] else "0.00",
                    f"{data['nilai']:.2f}"
                ])
    
    print(f"✓ Generated {output_file}")

def classify_items(items_by_region, item_presence, output_file):
    """Classify items as Global, Regional, or Lokal."""
    print(f"Generating {output_file}...")
    
    total_regions = len(items_by_region)
    
    # Collect all items with their regional data
    all_items = {}
    for wilayah, items in items_by_region.items():
        for kode, data in items.items():
            if kode not in all_items:
                all_items[kode] = {
                    'deskripsi': data['deskripsi'],
                    'regional_data': {}
                }
            all_items[kode]['regional_data'][wilayah] = len(data['transactions'])
    
    classifications = []
    
    for kode, info in all_items.items():
        presence_count = len(item_presence[kode])
        regional_data = info['regional_data']
        
        # Calculate H_norm (entropy-based diversity)
        total_trans = sum(regional_data.values())
        h_norm = 0.0
        if total_trans > 0 and presence_count > 1:
            for trans in regional_data.values():
                if trans > 0:
                    p = trans / total_trans
                    h_norm -= p * log(p, presence_count)
        
        # Find dominant region
        max_trans = max(regional_data.values()) if regional_data else 0
        max_share = max_trans / total_trans if total_trans > 0 else 0
        dominant_regions = [w for w, t in regional_data.items() if t == max_trans]
        wilayah_dominan = ', '.join(sorted(dominant_regions))
        
        # Classification logic
        if presence_count >= total_regions:
            label = 'Global'
        elif presence_count >= 2:
            label = 'Regional'
        else:
            label = 'Lokal'
        
        classifications.append({
            'kode': kode,
            'deskripsi': info['deskripsi'],
            'presence_count': presence_count,
            'h_norm': h_norm,
            'max_share': max_share,
            'wilayah_dominan': wilayah_dominan,
            'label': label
        })
    
    # Sort by presence count (descending), then by label
    classifications.sort(key=lambda x: (-x['presence_count'], x['label'], x['kode']))
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Kode Item', 'Deskripsi', 'Presence Count', 'H_norm', 'Max Share', 'Wilayah Dominan', 'Label'])
        
        for item in classifications:
            writer.writerow([
                item['kode'],
                item['deskripsi'],
                item['presence_count'],
                f"{item['h_norm']:.4f}",
                f"{item['max_share']:.4f}",
                item['wilayah_dominan'],
                item['label']
            ])
    
    print(f"✓ Generated {output_file}")
    
    # Print summary
    label_counts = Counter(item['label'] for item in classifications)
    print(f"\nClassification Summary:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count} items")

def main():
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(base_dir, 'Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv')
    hasil_dir = os.path.join(base_dir, 'Hasil')
    
    # Create output directory
    os.makedirs(hasil_dir, exist_ok=True)
    
    # Process data
    items_by_region, item_presence, item_totals = process_transactions(csv_file)
    
    print(f"\nFound {len(items_by_region)} regions:")
    for region in sorted(items_by_region.keys()):
        print(f"  - {region}: {len(items_by_region[region])} unique items")
    
    # Generate outputs
    top5_file = os.path.join(hasil_dir, 'top5_item_per_wilayah.csv')
    classification_file = os.path.join(hasil_dir, 'classifikasi_item_global_lokal.csv')
    
    generate_top5_per_wilayah(items_by_region, top5_file)
    classify_items(items_by_region, item_presence, classification_file)
    
    print("\n✓ All files generated successfully!")

if __name__ == '__main__':
    main()
