# Item Classification Script

## Overview

`classify_item_global_local.py` classifies items based on their geographic distribution across DKI Jakarta wilayah (regions).

## Classification Categories

### Global Items
Items widely distributed across Jakarta with:
- Present in 4+ wilayah
- High normalized entropy (H_norm ≥ 0.70)
- No single wilayah dominates (max_share ≤ 0.50)

### Regional Items
Items with intermediate distribution patterns:
- Present in 2-3 wilayah, OR
- Moderate concentration and entropy levels

### Local Items
Items concentrated in specific wilayah:
- Present in only 1 wilayah, OR
- Highly concentrated (max_share ≥ 0.60)
- Low entropy (H_norm ≤ 0.40)
- High Location Quotient (LQ ≥ 1.5)

### Low-Volume Items
Items with insufficient data for classification:
- Less than 30 unique transactions (configurable)

## Usage

### Basic Usage
```bash
python scripts/classify_item_global_local.py "Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv"
```

### Include Retur Transactions
```bash
python scripts/classify_item_global_local.py "Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv" --include-retur
```

### Custom Output Path
```bash
python scripts/classify_item_global_local.py "Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv" --output custom/path.csv
```

### Adjust Minimum Transaction Threshold
```bash
python scripts/classify_item_global_local.py "Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv" --n-min 50
```

## Output

The script generates a CSV file with the following columns:

- `kodeitem`: Item code
- `deskripsi`: Item description
- `transaksi_count_total`: Total unique transaction count
- `presence_count`: Number of wilayah where item appears
- `H_norm`: Normalized Shannon entropy (measure of distribution uniformity)
- `max_share`: Maximum share of transactions in any single wilayah
- `wilayah_dominan`: Wilayah with the highest transaction share
- `LQ_max`: Maximum Location Quotient across wilayah
- `label`: Classification (Global/Regional/Local/Low-Volume)
- `trx_*`: Transaction counts per wilayah (barat, pusat, selatan, timur, utara, kepulauan_seribu)

## Metrics

### Shannon Entropy (H_norm)
Measures distribution uniformity across wilayah:
- H_norm = 1.0: Perfectly uniform distribution
- H_norm = 0.0: Concentrated in single wilayah

### Location Quotient (LQ)
Measures relative concentration in a wilayah:
- LQ > 1.5: Item over-represented in that wilayah
- LQ = 1.0: Item has proportional representation
- LQ < 1.0: Item under-represented in that wilayah

## Wilayah Detection

The script detects the following Jakarta regions from transaction locations:
- Jakarta Pusat (Central Jakarta)
- Jakarta Timur (East Jakarta)
- Jakarta Barat (West Jakarta)
- Jakarta Selatan (South Jakarta)
- Jakarta Utara (North Jakarta)
- Kepulauan Seribu (Thousand Islands)

Detection uses case-insensitive regex patterns on the `LokasiAlamatToko` field.

## GitHub Workflow

The classification can be automatically run via GitHub Actions:

1. **Manual trigger**: Go to Actions → "Classify Items Global/Regional/Local" → "Run workflow"
2. **Automatic trigger**: Workflow runs on pushes to the branch when relevant files change

Results are automatically committed back to the repository.
