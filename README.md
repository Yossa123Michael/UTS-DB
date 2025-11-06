"# UTS-DB

## Bantex Transaction Database Management System

A comprehensive database management project analyzing PT. Bantex transaction data (2007-2024) using MongoDB distributed architecture across Jakarta regions.

## 📊 Project Overview

This project implements a distributed MongoDB database system for a stationery and art supplies distributor with three strategic locations:
- **HQ (Pusat):** Jakarta Pusat - Main headquarters
- **Branch 1:** Jakarta Utara - Northern distribution center  
- **Branch 2:** Jakarta Timur - Eastern distribution center

## 📁 Repository Structure

```
UTS-DB/
├── Data 1/                  # Excel data files (2007-2012)
├── Data 2/                  # Excel data files (2013-2018)
├── Data 3/                  # Excel data files (2019-2024)
├── Hasil/                   # Processed CSV outputs
│   ├── top5_item_per_wilayah.csv
│   └── classifikasi_item_global_lokal.csv
├── docs/                    # Documentation
│   └── UTS_Report.md       # Comprehensive analysis report
├── scripts/                 # Data processing scripts
│   ├── process_data.py     # Generate CSV outputs from transaction data
│   ├── render_report.py    # Render Markdown tables from CSV
│   └── README.md           # Scripts documentation
├── Data UTS Transaksi Bantex 2019 - 2024.xlsx - DATA TRANSAKSI.csv
├── Referensi.pdf           # Reference documentation
├── Soal.pdf                # Assignment brief
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Process Transaction Data

Generate analysis CSV files from the transaction data:

```bash
python3 scripts/process_data.py
```

This creates:
- `Hasil/top5_item_per_wilayah.csv` - Top 5 items per region
- `Hasil/classifikasi_item_global_lokal.csv` - Item classification (Global/Regional/Lokal)

### 2. View Report

Open the comprehensive report:

```bash
cat docs/UTS_Report.md
# Or view on GitHub for proper rendering
```

### 3. Verify Data Processing

Test the report rendering script:

```bash
python3 scripts/render_report.py
```

## 📈 Key Features

### Data Analysis
- **Top 5 Items per Region:** Identifies best-performing products by unique transaction count
- **Item Classification:** Categorizes items as Global, Regional, or Lokal based on distribution
- **Transaction Metrics:** Analyzes quantity, price, and total value across regions

### Database Design
- **MongoDB Architecture:** Distributed document-oriented database
- **3NF ERD:** Normalized entity relationship diagram with 9 core entities
- **Sharding Strategy:** Geographic sharding by `WilayahID` for optimal performance

### Business Insights
- **Order-to-Cash Cycle:** Complete process flow visualization
- **Inventory Optimization:** Data-driven recommendations for stock distribution
- **Regional Performance:** Comparative analysis across Jakarta locations

## 📊 Report Contents

The main report ([docs/UTS_Report.md](docs/UTS_Report.md)) includes:

1. **Executive Summary** - Business context and objectives
2. **Top 5 Items per Region** - Performance tables for all locations
3. **Item Classification** - Global/Regional/Lokal distribution strategy
4. **ERD Diagrams** - Conceptual schema with Mermaid visualization
5. **O2C Process Flow** - Sequence diagram for order-to-cash cycle
6. **Appendix** - Additional regional data (Jakarta Barat, Selatan)
7. **Recommendations** - Strategic insights for inventory and distribution

## 🛠️ Technologies

- **Database:** MongoDB (distributed, document-oriented)
- **Language:** Python 3.6+
- **Format:** CSV, Markdown, Mermaid diagrams
- **Architecture:** 3-node distributed system with geographic sharding

## 📝 Data Summary

**Analysis Period:** 2007-2024 (18 years)

**Regions Analyzed:**
- Jakarta Pusat: 1,145 unique items
- Jakarta Timur: 784 unique items
- Jakarta Utara: 970 unique items
- Jakarta Barat: 32 unique items
- Jakarta Selatan: 119 unique items

**Item Classification:**
- Global: 15 items (0.8%)
- Regional: 761 items (41.7%)
- Lokal: 1,048 items (57.5%)

## 🎯 Business Objectives

1. ✅ Identify top-performing items per location
2. ✅ Classify items for optimized inventory distribution
3. ✅ Support data-driven decision making
4. ✅ Leverage distributed architecture for scalability
5. ✅ Provide comprehensive business intelligence

## 📚 Documentation

- **Main Report:** [docs/UTS_Report.md](docs/UTS_Report.md)
- **Scripts Guide:** [scripts/README.md](scripts/README.md)
- **Assignment Brief:** Soal.pdf
- **Reference Materials:** Referensi.pdf

## 🤝 Contributing

This is an academic project for database management coursework. For questions or suggestions, please open an issue.

## 📄 License

Educational project - PT. Bantex transaction data analysis

---

**Last Updated:** November 2024  
**Course:** Database Management Systems (UTS Project)  
**Institution:** [Your Institution Name]
