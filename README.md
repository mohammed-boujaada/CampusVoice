# CampusVoice 
## Anonymous University Feedback & Evaluation Platform

**Cloud Computing Mini-Project** | Master's in AI & Emerging Technologies | FPN Nador

----

## Project Overview

**CampusVoice** is a secure, anonymized feedback collection platform built for universities. It allows students to submit honest evaluations of courses and instructors, while providing professors and administrators with actionable insights through a protected dashboard.

### Key Features

- **Anonymous Student Submissions** - No login required for feedback submission
- **Role-Based Access Control** - Separate interfaces for students, professors, and administrators
- **Real-time Dashboard** - Filter, analyze, and export feedback data
- **Security First** - Rate limiting, CSRF protection, SQL injection prevention
- **Cloud-Native** - Deployed on Microsoft Azure (PaaS architecture)
- **CSV Export** - Easy data analysis in Excel/Google Sheets
- **One Feedback Per Day** - Anti-spam rate limiting per IP/Professor

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│             Web Browser (HTTPS)                 │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│    Azure App Service (Flask + Gunicorn)        │
│  - CSRF Protection (Flask-WTF)                 │
│  - Rate Limiting (Flask-Limiter)               │
│  - Security Headers                            │
│  - Session Management (HttpOnly + Secure)      │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────▼───────────┐
        │  TLS/Encrypted Channel │
        └────────────┬───────────┘
                     │
┌────────────────────▼────────────────────────────┐
│     Azure SQL Database                         │
│  - Tables: Users, Professors, Feedbacks       │
│  - Firewall Rules (App Service only)          │
│  - Encrypted connections                      │
│  - Managed backups & HA                        │
└─────────────────────────────────────────────────┘
```

### 3-Tier Design
1. **Presentation Layer** - Flask web app with Jinja2 templates
2. **Application Layer** - Business logic, authentication, rate limiting
3. **Data Layer** - Azure SQL Database with encrypted connections

---

## Security Features

### Authentication & Authorization
- **Students**: No authentication required (anonymity-first)
- **Professors/Admins**: Username + password (MD5 hashing - upgrade to bcrypt recommended)
- **Role-Based Access**: Professors see only their feedback; Admins see all

### Defense Mechanisms
| Feature | Purpose | Technology |
|---------|---------|-----------|
| CSRF Protection | Prevent cross-site requests | Flask-WTF |
| Rate Limiting | Block brute force & spam | Flask-Limiter (5 attempts / 60s) |
| Anti-Spam | 1 feedback per professor per day per IP | Custom logic |
| Secure Headers | XSS, clickjacking, MIME-sniffing protection | CSP, HSTS, X-Frame-Options |
| Session Security | HttpOnly + Secure + SameSite cookies | Flask session config |
| Input Sanitization | XSS prevention | markupsafe.escape() |

### Azure-Level Security
- **TLS 1.2+** for all communications
- **SQL Firewall** - Only App Service can connect to database
- **Encrypted Credentials** - No secrets in code (stored in App Service environment variables)
- **Network Isolation** - Private endpoints available for production

---

## Database Schema

### Users Table
```sql
ID (PK) | Username | PasswordHash | Role | CreatedAt
```

### Professors Table
```sql
ID (PK) | Name | Email | Course | AppUserId (FK)
```

### Feedbacks Table
```sql
ID (PK) | ProfessorID (FK) | Rating | Comment | StudentIP | CreatedAt | IsSpam
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- Azure SQL Database (or local SQL Server)
- ODBC Driver 18 for SQL Server
- pip (Python package manager)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/campusvoice.git
   cd campusvoice
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure SQL credentials
   ```

5. **Install ODBC Driver** (if not present)
   ```bash
   # Ubuntu/Debian:
   sudo apt-get install odbc-msodbcsql18
   
   # macOS:
   brew install msodbcsql18
   
   # Windows: Download from Microsoft
   ```

6. **Run the application**
   ```bash
   flask run
   # or for production:
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

Access at: `http://localhost:5000`

---

## Project Structure

```
campusvoice/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── Procfile               # Heroku/Azure deployment
├── static/                # CSS, JS, images
│   ├── style.css          # Application styling
│   └── logo.png           # CampusVoice logo
├── templates/             # Jinja2 HTML templates
│   ├── index.html         # Landing page
│   ├── login.html         # Staff login
│   ├── dashboard.html     # Admin/Prof dashboard
│   ├── feedback-form.html # Anonymous feedback
│   └── base.html          # Base template
├── deployments/           # Azure deployment configs
│   ├── azure-deploy.sh    # Deployment script
│   └── README_AZURE.md    # Azure setup guide
└── docs/                  # Documentation
    ├── architecture.md    # Technical architecture
    └── security.md        # Security documentation
```

---

## User Roles & Workflows

### Student Role (Anonymous)
1. Visit homepage
2. Accept privacy notice
3. Select professor/course
4. Rate (1-5 stars) and add comment
5. Submit feedback
6. **Completely anonymous** - no account tracking

### Professor Role (Authenticated)
1. Login with credentials
2. View dashboard with own feedback only
3. Filter by date range, rating
4. Export feedback as CSV
5. View average rating and student suggestions
6. **Cannot see other professors' feedback**

### Admin/Coordinator Role (Authenticated)
1. Login with credentials
2. Access global dashboard (all feedback)
3. Advanced filtering & analytics
4. Manage professors (add/remove accounts)
5. System-wide export and reporting
6. **Full access to all data**

---

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this

# Azure SQL Database
DB_SERVER=your-server.database.windows.net
DB_USER=your-sql-username
DB_PASSWORD=your-sql-password
DB_NAME=campusvoice_db

# Security Settings
SESSION_TIMEOUT=1800           # 30 minutes
MAX_LOGIN_ATTEMPTS=5           # Max login tries
RATE_LIMIT_WINDOW=60           # Seconds
```

**NEVER commit `.env` to version control!**

---

## Testing

### Test Database Connectivity
```bash
# Visit: http://localhost:5000/test-db
# Should return connection status and table count
```

### Test Rate Limiting
```bash
# Try rapid login attempts - should be blocked after 5 tries
```

### Test CSRF Protection
```bash
# Attempt form submission without CSRF token - should fail
```

---

## Deployment to Azure

### Option 1: Using Azure CLI (Recommended)
```bash
# See deployments/azure-deploy.sh for full setup
az login
az group create --name campusvoice-rg --location eastus
az appservice plan create --name campusvoice-plan --resource-group campusvoice-rg --sku B1 --is-linux
az webapp create --resource-group campusvoice-rg --plan campusvoice-plan --name campusvoice-app --runtime "PYTHON|3.11"
az webapp config appsettings set --resource-group campusvoice-rg --name campusvoice-app --settings @settings.json
az webapp up --resource-group campusvoice-rg --name campusvoice-app
```

### Option 2: Using Azure Portal
1. Create **App Service** (Python 3.11)
2. Create **Azure SQL Database**
3. Upload code via Git/ZIP
4. Configure environment variables in App Service settings
5. Set SQL firewall rules to allow App Service

### Option 3: GitHub Actions (CI/CD)
See `.github/workflows/deploy.yml` for automated deployment on every push

---

## 📧 Support & Contact

**Project Team:**
- Mohamed Zahir
- Mohammed Boujaada

**Institution:** FPN Nador - Master's Program (AI & Emerging Technologies)

**Questions or Issues?** Open an issue on GitHub or contact the team.

---

## 📜 License

This project is provided as-is for educational purposes. 

---

## 🙏 Acknowledgments

- Microsoft Azure for cloud infrastructure
- Flask framework and community
- FPN Nador for project requirements
- All contributors and testers


---

## 🔄 Future Enhancements

- [ ] Replace MD5 with bcrypt/Argon2 password hashing
- [ ] Integrate Azure Key Vault for secrets management
- [ ] Add Microsoft Entra ID (Azure AD) SSO
- [ ] Implement Multi-Factor Authentication (MFA)
- [ ] Add analytics dashboard with charts (Chart.js/D3.js)
- [ ] Mobile app (React Native)
- [ ] Real-time notifications
- [ ] PDF report generation
- [ ] Sentiment analysis on feedback comments
- [ ] Machine learning-based spam detection

---
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-2.3-red)
![Azure](https://img.shields.io/badge/Azure-Deployed-blue)

**Last Updated:** May 2026
