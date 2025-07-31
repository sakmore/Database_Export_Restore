# Database Export/Restore Tool 🛠️

A PostgreSQL database backup and migration utility for exporting and restoring database schemas and data with integrity checks.

## Table of Contents

- [Script Usage Instructions](#script-usage-instructions)
- [Library Dependencies](#library-dependencies)
- [Assumptions](#assumptions)
- [Notes on Restore Integrity](#notes-on-restore-integrity)
- [Setup and Installation](#setup-and-installation)
- [Project Files](#project-files)
- [Verification](#verification)

## Script Usage Instructions

### Prerequisites
Ensure you have Python 3.x installed and all dependencies from `requirements.txt`.

### Environment Setup
Create a `.env` file with your database credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

### Initial Database Setup
Populate your database with sample data:

```bash
python setup_db.py
```

### Export Database 📤
Export schema and data to the `exports/` folder:

```bash
python export_restore.py export --env-file .env
```

This creates:
- `exports/schema.sql` - Database structure
- `exports/agents.csv` - Agents table data
- `exports/leads.csv` - Leads table data
- `exports/feedback.csv` - Feedback table data

### Restore Database 📥
Restore schema and data from exports:

```bash
python export_restore.py restore --env-file .env
```

### Cross-Environment Migration 🚀
To migrate to a different database (e.g., Supabase):

1. Create target environment file:
```env
# supabase.env
DB_HOST=db.your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_password
```

2. Run restore with target environment:
```bash
python export_restore.py restore --env-file supabase.env
```

## Library Dependencies

Install the following Python packages:

```bash
pip install psycopg2-binary python-dotenv faker
```

**Required Libraries:**
- `psycopg2-binary` - PostgreSQL database adapter for Python
- `python-dotenv` - Load environment variables from .env files
- `faker` - Generate sample data (used in setup_db.py)

**System Requirements:**
- Python 3.x
- PostgreSQL database access
- Network connectivity to target database

## Assumptions

The script operates under these assumptions:

- **Schema File Location**: `schema.sql` is located in the project root directory
- **Environment Files**: `.env` files contain `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` variables
- **Database Access**: User has sufficient privileges for DDL operations (CREATE/DROP tables, types)
- **Table Structure**: Tables `agents`, `leads`, `feedback` exist with `id` as SERIAL PRIMARY KEY
- **Custom Types**: `lead_status` ENUM type is defined in the schema
- **Foreign Keys**: Tables have proper foreign key relationships (agents ← leads ← feedback)

## Notes on Restore Integrity

### How Sequences Are Handled
After importing data via `COPY FROM`, PostgreSQL's SERIAL sequences don't automatically update. The script fixes this by:

```sql
SELECT setval('table_name_id_seq', COALESCE(MAX(id), 1)) FROM table_name;
```

This prevents "duplicate key" errors when inserting new records after restore.

### Enum Types Management
The script handles custom ENUM types by:
- Dropping existing types before schema recreation: `DROP TYPE IF EXISTS lead_status`
- Recreating types as defined in `schema.sql`
- Ensuring data compatibility during import

### Idempotent Operations ✅
The restore process is repeatable through:
- **Clean Slate Approach**: DROP statements in `schema.sql` remove existing objects
- **Dependency Order**: Tables restored in correct sequence (agents → leads → feedback)
- **Constraint Handling**: Foreign keys and constraints properly managed

### Schema Requirements
Your `schema.sql` must include these DROP statements at the top:

```sql
-- Clean slate for idempotent restores
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TYPE IF EXISTS lead_status;
```

### Data Integrity Features
- **NULL Handling**: Empty CSV cells properly converted to NULL values
- **Foreign Key Management**: Tables restored in dependency order
- **Transaction Safety**: Operations wrapped in transactions where applicable
- **Error Handling**: Comprehensive error checking and reporting

## Setup and Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd database-export-restore
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy and modify the sample `.env` file with your database credentials.

### 4. Initialize Database
```bash
python setup_db.py
```

### 5. Test Export/Restore
```bash
# Export
python export_restore.py export --env-file .env

# Restore  
python export_restore.py restore --env-file .env
```

## Project Files

```
├── setup_db.py         # Database initialization script
├── export_restore.py   # Main export/restore functionality  
├── schema.sql          # Database schema definition
├── .env               # Database credentials (sample with obfuscated values)
├── requirements.txt   # Python dependencies
├── README.md          # This documentation
└── exports/           # Generated backup files (sample export included)
    ├── schema.sql
    ├── agents.csv
    ├── leads.csv
    └── feedback.csv
```

## Verification

### Testing Complete Workflow
1. **Baseline**: Run `python setup_db.py` for fresh data
2. **Export**: Run export command and verify `exports/` folder contents
3. **Modify**: Delete or update records in your database
4. **Restore**: Run restore command  
5. **Validate**: Confirm original data is restored
6. **Test Sequences**: Insert new records to verify auto-incrementing works

### Common Issues and Solutions ⚠️
- **Authentication failures**: Verify credentials in `.env` file
- **Table exists errors**: Ensure DROP statements are in `schema.sql`
- **Duplicate key errors**: Indicates sequence adjustment issues
- **Foreign key violations**: Check table restore order and data consistency

### Screenshot Of Deliverables
<img width="613" height="246" alt="image" src="https://github.com/user-attachments/assets/14525c34-26a6-4c63-b2c5-6aca647bb902" />

<img width="949" height="671" alt="image" src="https://github.com/user-attachments/assets/d34d2571-4a2a-4c36-81ad-18fc7c36c1a9" />

<img width="1515" height="765" alt="image" src="https://github.com/user-attachments/assets/18a84ab3-ce0c-41af-bc67-e7d1096953a1" />

<img width="1879" height="583" alt="image" src="https://github.com/user-attachments/assets/5efe1e7b-1a1d-43bf-81fa-90a9d7174af1" />




