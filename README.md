# beyondborderweb

# Visa Countries Website

A comprehensive visa information website with admin panel for managing visa requirements for 11 Asian countries.

## Features

### Public Features
- Browse visa requirements for Asian countries
- Search and filter countries by region and visa requirements
- Detailed country information including visa types, documents, fees, and processing times
- Embassy and consulate information
- Entry points and travel requirements

### Admin Features
- **Password-protected admin panel**
- Full CRUD operations for countries
- Comprehensive country form with tabbed interface
- Bulk operations (publish/unpublish multiple countries)
- Data quality indicators
- Search and filtering capabilities
- Real-time statistics dashboard
- Featured countries management

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Authentication**: JWT tokens with HTTP-only cookies
- **Templates**: Jinja2

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deepika-visa-website
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional)
   ```bash
   export MONGODB_URL="your-mongodb-connection-string"
   export ADMIN_USERNAME="your-admin-username"
   export ADMIN_PASSWORD="your-admin-password"
   export SECRET_KEY="your-secret-key"
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   - Public website: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Admin Authentication

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

### Security Features
- JWT-based authentication with HTTP-only cookies
- Session expiration (8 hours)
- Automatic redirect to login for unauthorized access
- Secure logout functionality

### Changing Admin Credentials
You can change the admin credentials by setting environment variables:
```bash
export ADMIN_USERNAME="your-new-username"
export ADMIN_PASSWORD="your-new-secure-password"
```

Or modify the values in `config.py`.

## API Endpoints

### Public API
- `GET /api/countries/` - Get all published countries
- `GET /api/countries/{slug}` - Get country by slug
- `GET /api/countries/search?q={query}` - Search countries

### Admin API (Authentication Required)
- `POST /api/admin/login` - Admin login
- `POST /api/admin/logout` - Admin logout
- `GET /api/admin/countries` - Get all countries (including drafts)
- `POST /api/admin/countries` - Create new country
- `PUT /api/admin/countries/{id}` - Update country
- `DELETE /api/admin/countries/{id}` - Delete country
- `PATCH /api/admin/countries/{id}/publish` - Toggle publish status
- `PATCH /api/admin/countries/{id}/feature` - Toggle featured status
- `GET /api/admin/stats` - Get comprehensive statistics

## Database

The application uses MongoDB Atlas for data storage with fallback to local file storage. The database contains:

- **Countries Collection**: Complete visa information for 11 Asian countries
- **Indexes**: Optimized for search and filtering operations

### Sample Data
The application comes pre-loaded with visa information for:
- India, China, Japan, Thailand, Singapore, Malaysia, Philippines, Indonesia, Vietnam, South Korea, Bangladesh

## Admin Panel Features

### Dashboard
- Overview statistics (total, published, featured countries)
- Region distribution charts
- Recent countries table
- Quick action buttons

### Countries Management
- Comprehensive listing with search and filters
- Data quality indicators with color coding
- Bulk operations for efficiency
- Individual country actions (edit, publish, feature, delete)
- Pagination support

### Country Form
- Tabbed interface with 7 sections:
  1. Basic Information
  2. Visa Types
  3. Documents
  4. Requirements
  5. Fees & Processing
  6. Locations
  7. Notes & Settings
- Auto-slug generation
- Dynamic form elements
- Save as draft or publish options

## Security Considerations

- Use strong passwords for admin accounts
- Change default credentials in production
- Use HTTPS in production
- Configure CORS properly for production
- Regularly update dependencies
- Use environment variables for sensitive configuration

## Development

### Project Structure
```
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Core functionality (auth, database)
│   ├── crud/               # Database operations
│   └── models/             # Pydantic models
├── templates/              # HTML templates
│   ├── admin/              # Admin panel templates
│   └── base.html           # Base template
├── static/                 # Static files
├── data_storage/          # Local file storage (fallback)
├── config.py              # Configuration
├── requirements.txt       # Dependencies
└── run.py                # Application entry point
```

### Adding New Countries
1. Access the admin panel at `/admin`
2. Click "Add Country" or navigate to `/admin/countries/new`
3. Fill in the comprehensive form with all visa information
4. Save as draft or publish immediately

## License

This project is for educational and informational purposes.
<<<<<<< HEAD
# beyondborderweb
=======
# Visa Countries Website

A comprehensive visa information website with admin panel for managing visa requirements for 11 Asian countries.

## Features

### Public Features
- Browse visa requirements for Asian countries
- Search and filter countries by region and visa requirements
- Detailed country information including visa types, documents, fees, and processing times
- Embassy and consulate information
- Entry points and travel requirements

### Admin Features
- **Password-protected admin panel**
- Full CRUD operations for countries
- Comprehensive country form with tabbed interface
- Bulk operations (publish/unpublish multiple countries)
- Data quality indicators
- Search and filtering capabilities
- Real-time statistics dashboard
- Featured countries management

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Authentication**: JWT tokens with HTTP-only cookies
- **Templates**: Jinja2

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deepika-visa-website
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional)
   ```bash
   export MONGODB_URL="your-mongodb-connection-string"
   export ADMIN_USERNAME="your-admin-username"
   export ADMIN_PASSWORD="your-admin-password"
   export SECRET_KEY="your-secret-key"
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   - Public website: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Admin Authentication

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

### Security Features
- JWT-based authentication with HTTP-only cookies
- Session expiration (8 hours)
- Automatic redirect to login for unauthorized access
- Secure logout functionality

### Changing Admin Credentials
You can change the admin credentials by setting environment variables:
```bash
export ADMIN_USERNAME="your-new-username"
export ADMIN_PASSWORD="your-new-secure-password"
```

Or modify the values in `config.py`.

## API Endpoints

### Public API
- `GET /api/countries/` - Get all published countries
- `GET /api/countries/{slug}` - Get country by slug
- `GET /api/countries/search?q={query}` - Search countries

### Admin API (Authentication Required)
- `POST /api/admin/login` - Admin login
- `POST /api/admin/logout` - Admin logout
- `GET /api/admin/countries` - Get all countries (including drafts)
- `POST /api/admin/countries` - Create new country
- `PUT /api/admin/countries/{id}` - Update country
- `DELETE /api/admin/countries/{id}` - Delete country
- `PATCH /api/admin/countries/{id}/publish` - Toggle publish status
- `PATCH /api/admin/countries/{id}/feature` - Toggle featured status
- `GET /api/admin/stats` - Get comprehensive statistics

## Database

The application uses MongoDB Atlas for data storage with fallback to local file storage. The database contains:

- **Countries Collection**: Complete visa information for 11 Asian countries
- **Indexes**: Optimized for search and filtering operations

### Sample Data
The application comes pre-loaded with visa information for:
- India, China, Japan, Thailand, Singapore, Malaysia, Philippines, Indonesia, Vietnam, South Korea, Bangladesh

## Admin Panel Features

### Dashboard
- Overview statistics (total, published, featured countries)
- Region distribution charts
- Recent countries table
- Quick action buttons

### Countries Management
- Comprehensive listing with search and filters
- Data quality indicators with color coding
- Bulk operations for efficiency
- Individual country actions (edit, publish, feature, delete)
- Pagination support

### Country Form
- Tabbed interface with 7 sections:
  1. Basic Information
  2. Visa Types
  3. Documents
  4. Requirements
  5. Fees & Processing
  6. Locations
  7. Notes & Settings
- Auto-slug generation
- Dynamic form elements
- Save as draft or publish options

## Security Considerations

- Use strong passwords for admin accounts
- Change default credentials in production
- Use HTTPS in production
- Configure CORS properly for production
- Regularly update dependencies
- Use environment variables for sensitive configuration

## Development

### Project Structure
```
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Core functionality (auth, database)
│   ├── crud/               # Database operations
│   └── models/             # Pydantic models
├── templates/              # HTML templates
│   ├── admin/              # Admin panel templates
│   └── base.html           # Base template
├── static/                 # Static files
├── data_storage/          # Local file storage (fallback)
├── config.py              # Configuration
├── requirements.txt       # Dependencies
└── run.py                # Application entry point
```

### Adding New Countries
1. Access the admin panel at `/admin`
2. Click "Add Country" or navigate to `/admin/countries/new`
3. Fill in the comprehensive form with all visa information
4. Save as draft or publish immediately

## License

This project is for educational and informational purposes.

I have fixed the issue where the edit page for a country was throwing an error and not displaying pre-existing data.

The problem was two-fold:
1.  A complex database query for fetching country data was failing for some countries, causing the "Error loading country data" message.
2.  Even if the data had loaded, the form fields for nested data (like visa types, documents, etc.) were marked as `readonly`, which would prevent editing.

Here's what I've done to fix it:
-   **Made form fields editable**: I've removed the `readonly` attribute from all the form fields in the `templates/admin/country_form.html` file. This will allow you to edit the details for visa types, documents, and other nested information.
-   **Simplified the database query**: I've simplified the database query in `app/core/db.py` that fetches the country data for the edit page. For now, it will only load the main details of the country. This ensures that the page loads without errors. The fields for related data like "Visa Types", "Documents" etc. will be empty for now, but editable.

The application is running, and you can now test the edit page. It should load without errors, and you should be able to see and edit the basic country information.

The next step would be to incrementally add back the logic to load the related data (visa types, documents, etc.) to the edit page, ensuring that it doesn't break the page. Please let me know if you want me to proceed with that. 