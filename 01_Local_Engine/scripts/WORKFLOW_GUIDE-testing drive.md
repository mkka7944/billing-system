# SGWMC Billing System Workflow Guide

## Updated Three-Tier Workflow (v4.8+)

The system now properly handles the three legitimate states of survey units:

1. **Pure Survey Units**: Data collected by field staff but not yet designated for billing by PITB
2. **Biller List Units**: Survey units selected by PITB for billing but not yet issued bills
3. **Issued Bill Units**: Biller list units that have actual PDF bills generated

## File Naming Conventions

To make files more meaningful and easier to remember, we use descriptive naming patterns:

### Survey Data Files
- `MASTER_ASSETS_SARGODHA_YYYYMMDD_HHMMSS.csv`
- `MASTER_ASSETS_KHUSHAB_YYYYMMDD_HHMMSS.csv`
- `MASTER_ASSETS_BHALWAL_YYYYMMDD_HHMMSS.csv`

### Bill Data Files
- `MASTER_FINANCIALS_SARGODHA_PAID_YYYYMMDD_HHMMSS.csv`
- `MASTER_FINANCIALS_SARGODHA_UNPAID_YYYYMMDD_HHMMSS.csv`
- `MASTER_FINANCIALS_KHUSHAB_PAID_YYYYMMDD_HHMMSS.csv`
- `MASTER_FINANCIALS_BHALWAL_PAID_YYYYMMDD_HHMMSS.csv`

### PDF Processing Files
- `psid_extraction_results_YYYYMMDD_HHMMSS.csv`
- `psid_extraction_summary_YYYYMMDD_HHMMSS.txt`

## Updated Workflow Steps

### 1. Collect Survey Data
```bash
python survey_filtered.py
```
This creates `MASTER_ASSETS_*.csv` files in the `outputs/master_db_ready` directory.

### 2. Upload Survey Data to Database
```bash
python db-uploader-1.py
# Select option 1: Upload ASSETS (Survey Units)
```

### 3. Extract Bill Data from Portal
```bash
python bill-extractor-v4.py
```
This creates `MASTER_FINANCIALS_*.csv` files in the `outputs/master_db_ready` directory.

### 4. Download PDF Bills (Manual Step)
Download PDF bills from the portal to the `inputs/raw_pdfs` directory.

### 5. Extract PSIDs from PDFs
```bash
python pdf-psid-extractor.py
```
This creates:
- `psid_extraction_results_YYYYMMDD_HHMMSS.csv`
- `psid_extraction_summary_YYYYMMDD_HHMMSS.txt`

### 6. Upload Bill Data to Database
```bash
python db-uploader-1.py
# Select option 2: Upload BILLS (Three-Tier Workflow)
```

### 7. Check Database Statistics
```bash
python db-uploader-1.py
# Select option 3: Show Database Statistics
```

## Understanding the New Data States

### Previous Approach (Problematic)
All records with missing survey IDs were classified as "orphans" and logged to `orphaned_bills_log.txt`.

### New Approach (Correct)
Records are now properly categorized:

1. **Valid Records** (`synced`): 
   - `survey_id_fk` exists in `survey_units` table
   - Uploaded normally to `bills` table

2. **Pending Sync Records** (`pending_sync`):
   - `survey_id_fk` doesn't exist in database
   - Logged to `pending_sync_log.txt` (NOT treated as errors)
   - Represents legitimate survey units that may not yet be in the biller list or haven't had bills issued yet

## Key Benefits of the Updated Workflow

1. **Accurate Data Representation**: 
   - No longer misclassifies legitimate pending units as "orphans"
   - Properly distinguishes between data states

2. **Better Logging**:
   - Separate logs for different data states
   - Clear distinction between actual errors and pending data

3. **Improved Decision Making**:
   - Can identify which survey units have been issued bills vs. just being in the biller list
   - Better understanding of the complete billing pipeline

## Next Steps

1. Run `survey_filtered.py` to collect latest survey data
2. Upload survey data using `db-uploader-1.py` option 1
3. Run `bill-extractor-v4.py` to get biller list data
4. Download PDF bills manually
5. Run `pdf-psid-extractor.py` to identify issued bills
6. Upload bill data using `db-uploader-1.py` option 2
7. Check statistics with `db-uploader-1.py` option 3