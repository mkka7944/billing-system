# Suthra Punjab Billing System

A comprehensive billing system for managing consumer units, bills, staff, and field operations with support for 50+ field agents and office administrators.

## Features

### Security Enhancements
- 🔐 Password hashing using bcrypt
- ⏰ Session timeout management (30 minutes)
- ✅ Input validation and sanitization
- 🛡️ Role-based access control

### Performance Optimizations
- 📄 Pagination for large datasets
- ⚡ Database query optimization
- 🧠 Caching mechanisms
- 🗃️ Data archiving strategies

### Reporting & Analytics
- 📊 Interactive dashboards with KPIs
- 📈 Data visualization with Plotly
- 📥 Export to CSV and Excel formats
- 📅 Custom date range filtering

### Mobile Optimization
- 📱 Responsive design for all devices
- 👆 Touch-friendly interface
- 🖼️ Optimized layouts for mobile and tablet
- 🌗 Dark mode support

### Notification System
- 🔔 In-app notifications
- 📧 Email notifications (planned)
- 📋 Activity feed
- 🎯 Entity-specific notifications

### Bulk Operations
- 🚀 Bulk data import/export
- 🔄 Bulk status updates
- 🗑️ Bulk record deletion
- ✅ Data validation

## System Architecture

### Frontend
- **Framework**: Streamlit
- **Components**: Custom UI components with pagination
- **Styling**: CSS with mobile optimization

### Backend
- **Language**: Python 3.8+
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Custom with bcrypt hashing
- **Storage**: Google Drive integration (planned)

### Data Model

#### Core Tables
1. **survey_units** - Consumer units/assets
2. **bills** - Monthly billing records
3. **staff** - User accounts and roles
4. **tickets** - Support ticket system
5. **compliance_visits** - Field visit records
6. **notifications** - User notifications

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
4. Run the application:
   ```bash
   streamlit run Home.py
   ```

## Usage

### For Field Agents
- View assigned consumer units
- Log compliance visits
- Update consumer information
- Submit tickets

### For Office Administrators
- Manage staff accounts
- Oversee billing operations
- Generate reports
- Handle ticket resolution

### For Managers/Head Admins
- System configuration
- Bulk operations
- Performance analytics
- User management

## Security

### Authentication
- Passwords hashed with bcrypt
- Session management with timeout
- Role-based access control

### Data Protection
- Input validation
- SQL injection prevention
- Secure database connections

## Performance

### Optimization Techniques
- Database indexing
- Query result caching
- Pagination for large datasets
- Lazy loading of images

### Scalability
- Supports 300k+ records
- Handles 50+ concurrent users
- Data archiving strategies
- Bandwidth optimization

## API Integration

### Supabase
- Real-time database operations
- Authentication (custom implementation)
- File storage (Google Drive planned)

### Google Drive (Planned)
- Image storage and retrieval
- Document management
- Backup storage

## Development

### Project Structure
```
02_Cloud_App/
├── Home.py                 # Main entry point
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── assets/                 # Static assets
│   ├── style.css           # Main stylesheet
│   └── mobile.css          # Mobile optimization
├── components/             # Reusable UI components
│   ├── auth.py            # Authentication
│   ├── sidebar.py         # Navigation sidebar
│   ├── pagination.py      # Pagination component
│   └── metrics.py         # Metric cards
├── pages/                 # Application pages
│   ├── 01_Dashboard.py    # Executive dashboard
│   ├── 02_Bills_Browser.py # Bill management
│   ├── 03_Staff_Manager.py # Staff management
│   ├── 04_Survey_Units.py # Consumer units
│   ├── 05_Ticket_Center.py # Ticket system
│   ├── 06_Locations.py    # Location management
│   ├── 07_Reports.py      # Reporting module
│   ├── 08_Bulk_Operations.py # Bulk operations
│   └── 09_Notifications.py # Notification center
├── services/              # Business logic
│   ├── auth.py            # Authentication service
│   ├── db.py              # Database connection
│   └── repository.py      # Data access layer
├── utils/                 # Utility functions
│   ├── security.py        # Security utilities
│   ├── session.py         # Session management
│   ├── exporters.py       # Data export
│   ├── bulk_operations.py # Bulk operations
│   └── notifications.py   # Notification system
└── database/              # Database schemas
    └── notifications_schema.sql
```

### Adding New Features
1. Create new page in `pages/` directory
2. Implement business logic in `services/`
3. Add UI components to `components/`
4. Create utility functions in `utils/`
5. Update sidebar navigation in `components/sidebar.py`

## Testing

### Unit Tests
- Authentication functions
- Database operations
- Utility functions
- Validation logic

### Integration Tests
- End-to-end workflows
- Database connectivity
- API integrations
- Error handling

## Deployment

### Streamlit Cloud
- Recommended hosting platform
- Easy deployment process
- Automatic SSL certificates

### Self-Hosting
- Docker support (planned)
- VPS deployment
- Custom domain configuration

## Maintenance

### Regular Tasks
- Database backups
- Password resets
- User provisioning
- System monitoring

### Updates
- Dependency updates
- Security patches
- Feature enhancements
- Performance tuning

## Troubleshooting

### Common Issues
- **Login failures**: Check credentials and database connectivity
- **Slow performance**: Verify database indexes and caching
- **Export errors**: Check file permissions and disk space
- **Mobile issues**: Test responsive design on actual devices

### Support
For issues and feature requests, please contact the system administrator.

## License

This project is proprietary software developed for Suthra Punjab operations.

## Authors

- Development Team

## Version History

- **2.0.0** - Major enhancement release with security, performance, and mobile optimizations
- **1.0.0** - Initial release with basic functionality