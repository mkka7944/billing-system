# Database Schema Reference

## Overview

This document provides a detailed reference of the Supabase database schema for the Suthra Punjab Billing System.

---

## Table 1: `survey_units`

**Purpose:** Master table containing all surveyed consumer units/assets (physical properties)

**Primary Key:** `survey_id` (string)

**Estimated Records:** ~70,000 (target: 300,000)

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `survey_id` | string (PK) | Unique survey identifier | Primary key, alphanumeric |
| `surveyor_name` | string | Name of surveyor | Who collected the data |
| `survey_timestamp` | timestamp | When survey was conducted | ISO format |
| `city_district` | string | Tehsil/City name | e.g., "Bhalwal", "Khushab" |
| `uc_name` | string | Union Council name | e.g., "UC-1", "UC-2" |
| `uc_type` | string | Type of Union Council | Classification |
| `image_portal_url` | string | Image URL (legacy) | To be migrated to Google Drive |
| `image_drive_id` | string | Google Drive file ID | **NEW** - For Google Drive images |
| `unit_specific_type` | string | Business/unit type | e.g., "Barber", "Bakery" |
| `survey_category` | string | Size category | e.g., "Small", "Medium", "Large" |
| `survey_consumer_name` | string | Name from survey | Original survey name |
| `billing_consumer_name` | string | Active billing name | Current/active name |
| `survey_mobile` | string | Mobile from survey | Original phone number |
| `billing_mobile` | string | Active billing mobile | Current phone number |
| `survey_address` | string | Address from survey | Original address |
| `billing_address` | string | Active billing address | Current address |
| `house_type` | string | Type of house/building | Classification |
| `water_connection` | string | Water connection status | Yes/No/Unknown |
| `size_marla` | string/number | Property size in marlas | Area measurement |
| `gps_lat` | float | GPS latitude | Decimal degrees |
| `gps_long` | float | GPS longitude | Decimal degrees |
| `gps_full_string` | string | Full GPS string | Original format |
| `is_active_portal` | boolean | Active status | True/False |

### Indexes (Recommended)

```sql
CREATE INDEX idx_survey_units_city ON survey_units(city_district);
CREATE INDEX idx_survey_units_uc ON survey_units(uc_name);
CREATE INDEX idx_survey_units_active ON survey_units(is_active_portal);
CREATE INDEX idx_survey_units_id ON survey_units(survey_id);
```

### Relationships

- One-to-Many with `bills` (via `survey_id_fk`)

---

## Table 2: `bills`

**Purpose:** Monthly billing records and payment tracking

**Primary Key:** Composite (`psid`, `bill_month`)

**Estimated Records:** ~70,000+ (multiple bills per consumer)

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `psid` | string (PK) | Portal System ID | Part of composite key |
| `bill_month` | string (PK) | Billing month | Format: "Nov-2025", "Oct-2025" |
| `survey_id_fk` | string (FK) | Foreign key to survey_units | Links to consumer unit |
| `monthly_fee` | integer | Monthly charge amount | In PKR (Pakistani Rupees) |
| `arrears` | integer | Outstanding balance | Previous unpaid amounts |
| `amount_due` | integer | Total payable | monthly_fee + arrears |
| `payment_status` | string | Payment status | PAID/UNPAID/ARREARS |
| `paid_date` | timestamp | Date of payment | NULL if unpaid |
| `paid_amount` | integer | Amount paid | Actual payment amount |
| `fine` | integer | Fine/penalty amount | Late payment fine |
| `channel` | string | Payment channel | "1Bill", "BOP OTC", "OTC/Cash" |
| `uploaded_at` | timestamp | When record was uploaded | ISO format |
| `created_at` | timestamp | Record creation time | Auto-generated |
| `updated_at` | timestamp | Last update time | Auto-updated |

### Indexes (Recommended)

```sql
CREATE INDEX idx_bills_survey_fk ON bills(survey_id_fk);
CREATE INDEX idx_bills_month ON bills(bill_month);
CREATE INDEX idx_bills_status ON bills(payment_status);
CREATE INDEX idx_bills_uploaded ON bills(uploaded_at);
CREATE INDEX idx_bills_composite ON bills(psid, bill_month);
```

### Relationships

- Many-to-One with `survey_units` (via `survey_id_fk`)

### Notes

- Multiple bills per consumer (one per month)
- Payment status updates should preserve `survey_id_fk`
- Use upsert for payment updates (based on PSID + month)

---

## Table 3: `staff`

**Purpose:** Staff accounts and authentication

**Primary Key:** `id` (integer, auto-increment)

**Estimated Records:** ~50

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `id` | integer (PK) | Unique staff ID | Auto-increment |
| `username` | string | Login username | Unique, required |
| `password` | string | Password hash | **SECURITY:** Should be bcrypt hash |
| `full_name` | string | Staff member name | Display name |
| `role` | string | Staff role | AGENT/SUPERVISOR/MANAGER/HEAD |
| `assigned_city` | string | City/Tehsil assignment | Can be NULL |
| `assigned_ucs` | array[string] | Assigned Union Councils | Array of UC names |
| `is_active` | boolean | Account status | True = active, False = locked |
| `created_at` | timestamp | Account creation time | Auto-generated |
| `updated_at` | timestamp | Last update time | Auto-updated |

### Indexes (Recommended)

```sql
CREATE INDEX idx_staff_username ON staff(username);
CREATE INDEX idx_staff_role ON staff(role);
CREATE INDEX idx_staff_active ON staff(is_active);
```

### Relationships

- One-to-Many with `tickets` (via `reported_by_staff_id`)
- One-to-Many with `compliance_visits` (via `staff_id`)

### Security Notes

- **CRITICAL:** Passwords should be hashed using bcrypt
- Never store plain text passwords
- Implement password reset functionality
- Add session management

---

## Table 4: `tickets`

**Purpose:** Issue tracking and resolution system

**Primary Key:** `ticket_id` (integer, auto-increment)

**Estimated Records:** Variable (growing with usage)

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `ticket_id` | integer (PK) | Unique ticket ID | Auto-increment |
| `reported_by_staff_id` | integer (FK) | Staff who created ticket | Foreign key to staff |
| `status` | string | Ticket status | PENDING/APPROVED/REJECTED |
| `title` | string | Ticket title | Brief description |
| `description` | text | Detailed description | Full ticket details |
| `priority` | string | Priority level | LOW/MEDIUM/HIGH/URGENT |
| `category` | string | Ticket category | BILLING/DATA/COMPLIANCE/OTHER |
| `created_at` | timestamp | Creation time | Auto-generated |
| `updated_at` | timestamp | Last update time | Auto-updated |
| `resolved_at` | timestamp | Resolution time | NULL if pending |
| `resolved_by_staff_id` | integer (FK) | Staff who resolved | Foreign key to staff |

### Indexes (Recommended)

```sql
CREATE INDEX idx_tickets_staff ON tickets(reported_by_staff_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created ON tickets(created_at);
```

### Relationships

- Many-to-One with `staff` (via `reported_by_staff_id`)
- Many-to-One with `staff` (via `resolved_by_staff_id`)

---

## Table 5: `compliance_visits`

**Purpose:** Field staff visit records with proof

**Primary Key:** `id` (integer, auto-increment)

**Estimated Records:** Variable (growing with field activity)

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `id` | integer (PK) | Unique visit ID | Auto-increment |
| `staff_id` | integer (FK) | Staff who made visit | Foreign key to staff |
| `survey_id_fk` | string (FK) | Consumer unit visited | Foreign key to survey_units |
| `image_drive_id` | string | Google Drive image ID | **NEW** - For proof image |
| `visit_date` | date | Date of visit | Date only |
| `visit_time` | time | Time of visit | Time only |
| `visit_type` | string | Type of visit | ROUTINE/COMPLAINT/FOLLOWUP |
| `notes` | text | Visit notes | Field staff notes |
| `gps_lat` | float | GPS latitude | If captured |
| `gps_long` | float | GPS longitude | If captured |
| `created_at` | timestamp | Record creation time | Auto-generated |

### Indexes (Recommended)

```sql
CREATE INDEX idx_visits_staff ON compliance_visits(staff_id);
CREATE INDEX idx_visits_survey ON compliance_visits(survey_id_fk);
CREATE INDEX idx_visits_date ON compliance_visits(visit_date);
```

### Relationships

- Many-to-One with `staff` (via `staff_id`)
- Many-to-One with `survey_units` (via `survey_id_fk`)

---

## Table 6: `unique_locations`

**Purpose:** Location lookup/reference table (may be a view)

**Primary Key:** Composite or auto-increment ID

**Estimated Records:** Small (reference data, ~100-500)

### Columns

| Column Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `city_district` | string | City/Tehsil name | e.g., "Bhalwal" |
| `uc_name` | string | Union Council name | e.g., "UC-1" |
| Additional location metadata | various | Location details | As needed |

### Notes

- This may be a materialized view or a regular table
- Used for location filtering and dropdowns
- Should be cached in application

---

## Database Constraints

### Foreign Key Constraints

```sql
-- Bills reference survey units
ALTER TABLE bills 
ADD CONSTRAINT fk_bills_survey 
FOREIGN KEY (survey_id_fk) 
REFERENCES survey_units(survey_id);

-- Tickets reference staff
ALTER TABLE tickets 
ADD CONSTRAINT fk_tickets_reporter 
FOREIGN KEY (reported_by_staff_id) 
REFERENCES staff(id);

ALTER TABLE tickets 
ADD CONSTRAINT fk_tickets_resolver 
FOREIGN KEY (resolved_by_staff_id) 
REFERENCES staff(id);

-- Compliance visits reference staff and survey units
ALTER TABLE compliance_visits 
ADD CONSTRAINT fk_visits_staff 
FOREIGN KEY (staff_id) 
REFERENCES staff(id);

ALTER TABLE compliance_visits 
ADD CONSTRAINT fk_visits_survey 
FOREIGN KEY (survey_id_fk) 
REFERENCES survey_units(survey_id);
```

### Check Constraints

```sql
-- Payment status validation
ALTER TABLE bills 
ADD CONSTRAINT chk_payment_status 
CHECK (payment_status IN ('PAID', 'UNPAID', 'ARREARS'));

-- Staff role validation
ALTER TABLE staff 
ADD CONSTRAINT chk_staff_role 
CHECK (role IN ('AGENT', 'SUPERVISOR', 'MANAGER', 'HEAD'));

-- Ticket status validation
ALTER TABLE tickets 
ADD CONSTRAINT chk_ticket_status 
CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED'));
```

---

## Data Archiving Strategy

### Bills Archiving

**Rule:** Archive bills older than 12 months

**Process:**
1. Export to CSV/Excel
2. Store in Google Drive or local backup
3. Delete from Supabase (or move to archive table)
4. Keep summary statistics in main database

**Implementation:**
- Monthly cron job
- Keep only last 12 months in active `bills` table
- Archive table structure: `bills_archive` (optional)

---

## Storage Estimates

### Current (70k records)

| Table | Records | Avg Size/Record | Total Size |
|-------|---------|----------------|------------|
| survey_units | 70,000 | ~2 KB | ~140 MB |
| bills | 70,000 | ~1 KB | ~70 MB |
| staff | 50 | ~0.5 KB | ~25 KB |
| tickets | Variable | ~0.5 KB | ~5 MB |
| compliance_visits | Variable | ~1 KB | ~10 MB |
| **Total** | | | **~225 MB** |

### At 300k records (without archiving)

| Table | Records | Avg Size/Record | Total Size |
|-------|---------|----------------|------------|
| survey_units | 300,000 | ~2 KB | ~600 MB ❌ |
| bills | 300,000 | ~1 KB | ~300 MB |
| **Total** | | | **~900 MB** ❌ |

**Solution:** Archive old bills, optimize schema, use data compression

---

## Query Optimization Tips

1. **Always use specific columns:** `select('id, name')` not `select('*')`
2. **Use pagination:** Limit results to 100-500 per page
3. **Add filters early:** Filter before joining
4. **Use indexes:** Ensure indexes on frequently queried columns
5. **Cache reference data:** Cache location lists, staff lists
6. **Batch operations:** Group multiple updates into batches

---

## Migration Notes

### Password Hashing Migration

**Current State:** Passwords stored in plain text

**Migration Steps:**
1. Add `password_hash` column to `staff` table
2. Create migration script to hash existing passwords
3. Update login function to check hashed passwords
4. Remove old `password` column (or keep for transition)

### Google Drive Migration

**Current State:** Images stored as portal URLs

**Migration Steps:**
1. Add `image_drive_id` column to `survey_units`
2. Create migration script to upload images to Google Drive
3. Update image display logic to use Google Drive
4. Keep `image_portal_url` for backward compatibility (optional)

---

**Last Updated:** December 2024  
**Next Review:** Post-implementation

