# 🚀 Bulk Veo Affiliate Video Batch Engine

Automated batch generator designed to process 50 to 100+ Meesho products in a single run using your daily/monthly Google Flow tokens.

---

## 📁 Files in this folder:
- **`batch_flow_generator.py`**: The master batch execution engine.
- **`sample_products.csv`**: Put your Meesho product links here (one per line).
- **`batch_progress.json`**: Auto-saved progress log to resume interrupted batches without wasting tokens.

---

## ⚡ How to Run:

### 1. Put links in CSV
Open `sample_products.csv` or create your own CSV file with Meesho links:
```csv
url
https://www.meesho.com/trendy-halter-neck-stylish-top-pink/p/cld4vg
https://www.meesho.com/search?q=wine+red+satin+corset+slit+gown+dress
```

### 2. Run the Batch Command
```bash
python batch_engine/batch_flow_generator.py --csv batch_engine/sample_products.csv
```

### Optional Flags:
- `--delay 15`: Delay in seconds between queueing each video (default: 10s).
- `--max 20`: Only process the first 20 products.
