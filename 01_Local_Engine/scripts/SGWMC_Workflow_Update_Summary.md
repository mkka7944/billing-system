# SGWMC Billing System Workflow Update Summary

## Date: December 14, 2025

## Overview
This document summarizes the updates made to the SGWMC Billing System to implement a proper three-tier workflow that correctly handles the different states of survey units in the billing process.

## Problem Addressed
The previous system incorrectly classified all records with missing survey IDs as "orphans." However, based on the actual workflow:
1. Survey units are collected by field staff via Android app
2. PITB determines which survey IDs are added to the biller list
3. Only a subset of biller list units receive PDF bills

Records should not be classified as "orphaned" solely due to lack of billing—they may be in a legitimate pre-billing state.

## Files Created and Modified

### 1. New PDF Processing Script
**File**: `pdf-psid-extractor.py`
- Extracts PSIDs from downloaded PDF bill files
- Identifies which survey units have actually been issued bills
- Distinguishes between biller list units and issued bill units

### 2. Updated Database Uploader
**File**: `db-uploader-1.py` (updated to v4.8)
- Changed "orphan" classification to "pending_sync" for proper data state handling
- Added new logging for pending sync records (separate from error logs)
- Added database statistics feature
- Maintained backward compatibility with existing upsert logic

### 3. Updated Dependencies
**File**: `requirements.txt`
- Added PyPDF2 library for PDF processing capabilities

### 4. Workflow Documentation
**File**: `WORKFLOW_GUIDE.md`
- Comprehensive guide to the new three-tier workflow
- Detailed file naming conventions
- Step-by-step workflow instructions

### 5. Workflow Demonstration
**File**: `demonstrate-workflow.py`
- Script showing workflow steps with meaningful file names
- Timestamp-based file naming examples

## Three-Tier Workflow Implementation

### Data States Now Properly Handled:
1. **Pure Survey Units**: Data collected by field staff but not yet designated for billing by PITB
2. **Biller List Units**: Survey units selected by PITB for billing but not yet issued bills
3. **Issued Bill Units**: Biller list units that have actual PDF bills generated

### Key Improvements:
1. **Proper Data Categorization**: 
   - Records previously classified as "orphans" are now properly categorized as "pending_sync"
   - Pending sync records represent legitimate survey units in various stages of the billing workflow

2. **Better Logging**:
   - Pending sync records are logged separately from true errors in `pending_sync_log.txt`
   - Actual errors continue to be logged in `orphaned_bills_log.txt`
   - Clear distinction between data issues and legitimate workflow states

3. **Enhanced Visibility**:
   - Added database statistics feature to monitor data growth
   - Meaningful file naming conventions for easy identification
   - Database statistics option in the uploader interface

## Next Steps for Implementation

1. Run `survey_filtered.py` to collect latest survey data for all three locations
2. Upload survey data using `db-uploader-1.py` option 1 (Upload ASSETS)
3. Run `bill-extractor-v4.py` to get biller list data from the portal
4. Download PDF bills manually to the `inputs/raw_pdfs/` directory
5. Run `pdf-psid-extractor.py` to identify which survey units have actually been issued bills
6. Upload bill data using `db-uploader-1.py` option 2 (Upload BILLS with Three-Tier Workflow)
7. Check database statistics with `db-uploader-1.py` option 3 to verify successful upload

## Benefits of Updated Workflow

1. **Accurate Data Representation**: 
   - No longer misclassifies legitimate pending units as "orphans"
   - Properly distinguishes between different data states in the billing pipeline

2. **Better Decision Making**:
   - Can identify which survey units have been issued bills vs. just being in the biller list
   - Better understanding of the complete billing pipeline and data flow

3. **Improved Maintainability**:
   - Clear separation of concerns in logging
   - More intuitive file naming conventions
   - Enhanced monitoring capabilities

## Technical Notes

- All changes maintain backward compatibility with existing systems
- The upsert operations in the database uploader preserve existing data while adding new information
- No deletions are performed on the database, ensuring data integrity and audit trail preservation
- The system continues to use the established Python-based tech stack (Pandas, Supabase, etc.)

This update resolves the data state confusion that was causing legitimate records to be flagged as errors, providing a more accurate representation of the billing workflow.