#!/usr/bin/env python3
"""
PDF PSID Extractor
------------------
Extracts PSIDs from downloaded PDF bill files to identify which survey units
have actually been issued bills vs. those that are just in the biller list.

This helps distinguish between:
1. Pure survey units (never designated as billers)
2. Biller list units (designated for billing but no bill issued yet)
3. Issued bill units (actual PDF bills generated)

Usage:
    python pdf-psid-extractor.py
"""

import os
import pandas as pd
import glob
from datetime import datetime
import re

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_INPUT_DIR = os.path.join(BASE_DIR, "..", "inputs", "raw_pdfs")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "processed_pdfs")
LOG_FILE = os.path.join(OUTPUT_DIR, "psid_extraction_log.txt")

BATCH_SIZE = 100

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def extract_psid_from_pdf(pdf_path):
    """
    Extract PSID from PDF file content.
    Looks for patterns like "PSID: 1234567890" or "PSID 1234567890"
    """
    if not HAS_PYPDF2:
        return None
        
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Extract text from first few pages (PSID usually on first page)
            for page_num in range(min(3, len(reader.pages))):
                page = reader.pages[page_num]
                text += page.extract_text()
                
            # Look for PSID patterns
            # Pattern 1: PSID: 1234567890
            # Pattern 2: PSID 1234567890
            # Pattern 3: PSID:1234567890
            patterns = [
                r'PSID[:\s]+(\d{10,20})',
                r'PSID[:\s]*(\d{10,20})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
                    
            return None
    except Exception as e:
        print(f"❌ Error reading PDF {pdf_path}: {e}")
        return None

def process_pdf_batch(pdf_files, start_idx):
    """Process a batch of PDF files"""
    results = []
    
    for i, pdf_path in enumerate(pdf_files[start_idx:start_idx + BATCH_SIZE]):
        filename = os.path.basename(pdf_path)
        psid = extract_psid_from_pdf(pdf_path)
        
        results.append({
            'filename': filename,
            'full_path': pdf_path,
            'extracted_psid': psid,
            'status': 'SUCCESS' if psid else 'NOT_FOUND',
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        print(f"   [{start_idx + i + 1}/{len(pdf_files)}] {filename} -> {psid or 'NOT FOUND'}")
    
    return results

def main():
    print("=== PDF PSID Extractor v1.0 ===")
    
    if not HAS_PYPDF2:
        print("❌ PyPDF2 is required but not installed.")
        print("   Install it with: pip install PyPDF2")
        return
    
    # Ensure output directory exists
    ensure_dir(OUTPUT_DIR)
    
    # Find all PDF files
    pdf_pattern = os.path.join(PDF_INPUT_DIR, "**", "*.pdf")
    pdf_files = glob.glob(pdf_pattern, recursive=True)
    
    if not pdf_files:
        print(f"❌ No PDF files found in {PDF_INPUT_DIR}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files to process.")
    
    # Process in batches
    all_results = []
    
    for start_idx in range(0, len(pdf_files), BATCH_SIZE):
        batch_results = process_pdf_batch(pdf_files, start_idx)
        all_results.extend(batch_results)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(all_results)
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(OUTPUT_DIR, f"psid_extraction_results_{timestamp}.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Save summary
    success_count = len(df[df['status'] == 'SUCCESS'])
    summary_path = os.path.join(OUTPUT_DIR, f"psid_extraction_summary_{timestamp}.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("PDF PSID Extraction Summary\n")
        f.write("==========================\n")
        f.write(f"Total PDFs processed: {len(pdf_files)}\n")
        f.write(f"PSIDs extracted: {success_count}\n")
        f.write(f"Success rate: {success_count/len(pdf_files)*100:.1f}%\n")
        f.write(f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # List successful extractions
        f.write("Extracted PSIDs:\n")
        successful = df[df['status'] == 'SUCCESS']
        for _, row in successful.iterrows():
            f.write(f"  {row['extracted_psid']} <- {row['filename']}\n")
    
    print(f"\n✅ Processing complete!")
    print(f"   Results saved to: {csv_path}")
    print(f"   Summary saved to: {summary_path}")
    print(f"   Successfully extracted {success_count} PSIDs from {len(pdf_files)} PDFs.")

if __name__ == "__main__":
    main()