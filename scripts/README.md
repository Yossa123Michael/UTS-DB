# Scripts Directory

This directory contains Python scripts for processing transaction data and generating reports.

## Scripts

### 1. process_data.py

**Purpose:** Process raw transaction data and generate analysis CSV files.

**Inputs:**
- `Data UTS Transaksi Bantex  2019 - 2024.xlsx - DATA TRANSAKSI.csv` (root directory)

**Outputs:**
- `Hasil/top5_item_per_wilayah.csv` - Top 5 items per region by transaction count
- `Hasil/classifikasi_item_global_lokal.csv` - Item classification (Global/Regional/Lokal)

**Usage:**
```bash
python3 scripts/process_data.py
```

**Features:**
- Extracts Jakarta region information from location strings
- Aggregates transaction data by item and region
- Ranks items by unique transaction count
- Classifies items based on regional presence and distribution patterns
- Calculates H_norm (normalized entropy) and max share metrics

### 2. render_report.py

**Purpose:** Render Markdown tables from CSV data for report automation.

**Inputs:**
- `Hasil/top5_item_per_wilayah.csv`
- `Hasil/classifikasi_item_global_lokal.csv`

**Outputs:**
- Console output with formatted Markdown tables
- (Future: automatic update of `docs/UTS_Report.md`)

**Usage:**
```bash
python3 scripts/render_report.py
```

**Features:**
- Reads and validates CSV data
- Formats numbers with Indonesian Rupiah currency
- Generates Markdown table syntax
- Provides summary statistics
- Can be extended for automated report updates

## Workflow

1. **Initial Processing:**
   ```bash
   python3 scripts/process_data.py
   ```
   This generates the CSV files in the `Hasil/` directory.

2. **Verify Data:**
   ```bash
   python3 scripts/render_report.py
   ```
   This validates the CSV files and shows sample tables.

3. **View Report:**
   Open `docs/UTS_Report.md` in a Markdown viewer or on GitHub.

## Future Enhancements

- [ ] Automate report update via `render_report.py` (replace manual tables)
- [ ] Add GitHub Actions workflow for automatic processing on data updates
- [ ] Implement incremental processing for large datasets
- [ ] Add data validation and quality checks
- [ ] Generate visualizations (charts, graphs) from CSV data
- [ ] Support for multiple date ranges and comparative analysis

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)
- CSV files with proper encoding (UTF-8)

## Notes

- Scripts assume data files are in standard locations relative to repository root
- Region extraction logic looks for "JAKARTA PUSAT", "JAKARTA UTARA", etc. in location strings
- Classification thresholds:
  - **Global:** Present in all 5 regions
  - **Regional:** Present in 2-4 regions  
  - **Lokal:** Present in only 1 region
