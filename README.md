# SGWMC Billing System

A comprehensive billing and survey management system for Punjab Waste Management Company, featuring data extraction, cloud-based management, and analytics.

## 🚀 Quick Start

```powershell
# Start the Cloud Application
cd 02_Cloud_App
streamlit run Home.py

# Run Data Extraction
cd 01_Local_Engine\scripts
py bill-extractor-v4.py

# Upload to Database
py db-uploader.py
```

For detailed instructions, see [Quick Start Guide](docs/20251211_2037_Quick_Start_Guide.txt)

## 📋 Project Overview

The SGWMC Billing System consists of two main components:

### 1. Local Engine (Data Extraction)
Located in `01_Local_Engine/`
- Extracts billing data from Punjab Suthra portal
- Processes survey submissions
- Uploads data to Supabase database
- Batch processing with progress tracking

### 2. Cloud App (Management Dashboard)
Located in `02_Cloud_App/`
- Web-based Streamlit application
- Real-time analytics and reporting
- Staff and ticket management
- Bill browser and payment tracking
- Bulk operations and notifications

## 🏗️ Project Structure

```
billing-system/
├── 01_Local_Engine/          # Data extraction & processing
│   ├── inputs/                # Configuration files and raw data
│   ├── outputs/               # Generated CSV files and logs
│   ├── scripts/               # Python extraction scripts
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── 02_Cloud_App/             # Streamlit web application
│   ├── pages/                 # Multi-page app sections
│   ├── components/            # Reusable UI components
│   ├── services/              # Backend services
│   ├── utils/                 # Utility functions
│   ├── assets/                # CSS and static files
│   ├── Home.py               # Main entry point
│   ├── requirements.txt      # Python dependencies
│   └── README.md             # Cloud app documentation
│
├── docs/                     # 📚 Project documentation
│   ├── README.md             # Documentation index
│   ├── 20251211_2037_Quick_Start_Guide.txt
│   ├── 20251211_2035_Installation_Complete.md
│   ├── 20251211_2028_Dependencies_Installed.md
│   ├── 20251211_1909_Comprehensive_Analysis_Report.md
│   ├── 20251211_1909_Database_Schema_Reference.md
│   ├── 20251211_1909_Implementation_Checklist.md
│   └── 20251211_1909_Test_Plan.md
│
├── Backups/                  # Archived files
│   ├── pages_archive/        # Legacy page implementations
│   └── [other backups]
│
├── verify_dependencies.py    # Dependency checker
└── README.md                 # This file
```

## 🛠️ Technology Stack

### Backend
- **Python 3.14.0** - Primary language
- **Supabase** - PostgreSQL database & authentication
- **Pandas & NumPy** - Data processing
- **Requests** - HTTP client for API calls

### Frontend (Cloud App)
- **Streamlit** - Web framework
- **Plotly** - Interactive visualizations
- **AG Grid** - Advanced data tables
- **Custom CSS** - Responsive design

### Data Processing
- **OpenPyXL** - Excel file handling
- **tqdm** - Progress bars
- **python-dotenv** - Configuration management

## 📦 Installation

### Prerequisites
- Python 3.14.0 or higher
- pip (Python package manager)
- Git (for version control)

### Setup

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd billing-system
   ```

2. **Install dependencies**
   ```powershell
   # Cloud App
   py -m pip install -r 02_Cloud_App\requirements.txt
   
   # Local Engine
   py -m pip install -r 01_Local_Engine\requirements.txt
   ```

3. **Configure environment**
   - Update `.env` files in both `01_Local_Engine/` and `02_Cloud_App/`
   - Set `SUPABASE_URL` and `SUPABASE_KEY`

4. **Verify installation**
   ```powershell
   py verify_dependencies.py
   ```

For complete installation instructions, see [Installation Guide](docs/20251211_2035_Installation_Complete.md)

## 🎯 Features

### Cloud Application
- **📊 Executive Dashboard** - Real-time analytics and KPIs
- **💳 Bills Browser** - Search, filter, and manage bills
- **👥 Staff Manager** - User account management
- **📋 Survey Units** - Household survey tracking
- **🎫 Ticket Center** - Issue tracking system
- **📍 Locations** - Geographic data management
- **📈 Reports** - Comprehensive reporting tools
- **⚡ Bulk Operations** - Mass updates and imports
- **🔔 Notifications** - System alerts and messages

### Local Engine
- **Bill Extraction** - Automated data scraping from portal
- **Survey Processing** - Household survey data extraction
- **Database Upload** - Batch upload with validation
- **Data Auditing** - Quality checks and validation
- **Progress Tracking** - Real-time processing status

## 🔐 Security

- **Password Hashing** - Argon2 encryption for user passwords
- **Session Management** - Automatic timeout and activity tracking
- **Role-Based Access** - Admin, Manager, Surveyor roles
- **Environment Variables** - Secure credential storage
- **Input Validation** - Pydantic models for data validation

## 📊 Database Schema

The system uses Supabase (PostgreSQL) with the following main tables:
- `bills` - Billing records
- `survey_units` - Household survey data
- `staff` - User accounts
- `tickets` - Issue tracking
- `unique_locations` - Geographic data
- `notifications` - System alerts

For detailed schema, see [Database Reference](docs/20251211_1909_Database_Schema_Reference.md)

## 🧪 Testing

```powershell
# Verify all dependencies
py verify_dependencies.py

# Test Cloud App locally
cd 02_Cloud_App
streamlit run Home.py

# Test data extraction (dry run)
cd 01_Local_Engine\scripts
py bill-extractor-v4.py --help
```

For complete test plan, see [Test Documentation](docs/20251211_1909_Test_Plan.md)

## 📚 Documentation

### Quick References
- [Quick Start Guide](docs/20251211_2037_Quick_Start_Guide.txt) - Command reference
- [Installation Complete](docs/20251211_2035_Installation_Complete.md) - Setup guide

### Technical Documentation
- [Comprehensive Analysis](docs/20251211_1909_Comprehensive_Analysis_Report.md) - System architecture
- [Database Schema](docs/20251211_1909_Database_Schema_Reference.md) - Database design
- [Implementation Checklist](docs/20251211_1909_Implementation_Checklist.md) - Development tracking

### Component Documentation
- [Cloud App README](02_Cloud_App/README.md) - Web application details
- [Docs Index](docs/README.md) - Complete documentation index

## 🔄 Workflow

### Data Collection Flow
1. **Extract** - Run `bill-extractor-v4.py` to scrape portal data
2. **Process** - Data is cleaned and validated automatically
3. **Upload** - Run `db-uploader.py` to push to database
4. **Review** - Use Cloud App to view and manage data

### Management Flow
1. **Login** - Access Cloud App via Streamlit
2. **Dashboard** - View real-time analytics
3. **Browse** - Search bills, surveys, locations
4. **Manage** - Update records, create tickets, manage staff
5. **Report** - Generate and export reports

## 🛠️ Maintenance

### Regular Tasks
- Monitor logs in `01_Local_Engine/outputs/logs/`
- Review orphaned records in `orphaned_bills_log.txt`
- Update staff accounts as needed
- Archive old data periodically

### Updates
- Keep dependencies updated: `py -m pip install --upgrade -r requirements.txt`
- Review and test before deploying updates
- Backup database before major changes

## 🤝 Contributing

### Code Standards
- Follow Python PEP 8 style guide
- Use type hints where applicable
- Document functions and classes
- Add comments for complex logic

### Git Workflow
1. Create feature branch
2. Make changes and test
3. Commit with descriptive messages
4. Submit pull request for review

## 📝 Changelog

### December 11, 2025
- ✅ Installed all dependencies (17 core packages)
- ✅ Reorganized documentation into `docs/` folder
- ✅ Archived duplicate page files
- ✅ Created comprehensive documentation
- ✅ Cleaned up project structure

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```powershell
# Reinstall dependencies
py -m pip install -r requirements.txt --force-reinstall
```

**Database Connection Errors**
- Check `.env` file configuration
- Verify Supabase credentials
- Test internet connection

**Streamlit Not Starting**
```powershell
# Check Streamlit installation
streamlit --version

# Reinstall if needed
py -m pip install streamlit --upgrade
```

For more help, see [Installation Complete](docs/20251211_2035_Installation_Complete.md)

## 📞 Support

- **Documentation**: Check `docs/` folder first
- **Issues**: Create GitHub issue with details
- **Questions**: Review existing documentation

## 📄 License

[Specify license here]

## 👏 Acknowledgments

- Punjab Waste Management Company
- Suthra Punjab Portal
- Supabase Team
- Streamlit Community

---

**Version:** 1.0.0  
**Last Updated:** December 11, 2025  
**Status:** ✅ Production Ready

For more information, visit the [documentation index](docs/README.md)
