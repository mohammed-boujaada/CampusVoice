

**# CampusVoice**



\<div align="center">



![Python]\(https\://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)

![Flask]\(https\://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)

![Azure]\(https\://img.shields.io/badge/Azure-Deployed-0078D4?logo=microsoftazure&logoColor=white)

![SQL]\(https\://img.shields.io/badge/Azure%20SQL-Database-CC2927?logo=microsoftsqlserver&logoColor=white)

![Security]\(https\://img.shields.io/badge/Security-CSRF%20%7C%20Rate%20Limit-green)

![License]\(https\://img.shields.io/badge/License-Educational-orange)

![Status]\(https\://img.shields.io/badge/Status-Active-brightgreen)



**\*\*Secure anonymous feedback platform for universities\*\***



*\*Cloud Computing mini-project — MIATE Master's — FPN Nador\**



[ Overview]\(#-vue-densemble) • [ Architecture]\(#-architecture) • [ Sécurité]\(#-sécurité) • [ Déploiement]\(#-déploiement-azure) • [ Team]\(#-équipe)



\</div>



\---



**## Table of Contents**



\- [ Overview]\(#-vue-densemble)

\- [ Key Features]\(#-fonctionnalités-clés)

\- [ Architecture]\(#-architecture)

\- [ Sécurité]\(#-sécurité)

\- [ Database]\(#-base-de-données)

\- [ User Roles]\(#-rôles-utilisateurs)

\- [ Installation]\(#-installation)

\- [ Azure Deployment]\(#-déploiement-azure)

\- [ Project Structure]\(#-structure-du-projet)

\- [ Tests]\(#-tests)

\- [ Roadmap]\(#-roadmap)

\- [ Team]\(#-équipe)

\- [ License]\(#-licence)



\---



**## Overview**



**\*\*CampusVoice\*\*** is a secure web platform that allows students to submit **\*\*anonymous evaluations\*\*** of their courses and professors. It provides teachers and administrators with a **\*\*secure dashboard\*\*** with actionable analytics.



\> **\*\*Objective\*\*** : Break down the barrier of fear by providing a 100% anonymous feedback channel while ensuring security, traceability, and scalability through the Microsoft Azure cloud.



**### Problem Addressed**



\| Problem | CampusVoice Solution |

\| :--- | :--- |

\| Students do not dare to provide honest feedback | Submission **\*\*100% anonyme\*\***, without an account |

\| Professors do not have a clear overview of feedback | Dashboard with filters, statistics, and CSV export |

\| Risks of spam and abuse | Rate limiting + 1 feedback/prof/jour/IP |

\| Complex deployment | PaaS architecture on Azure (App Service + SQL) |



\---



**## Key Features**



\| Category | Description |

\| :--- | :--- |

\| **\*\*Complete anonymity\*\*** | Submission without an account, sans tracking, sans cookies |

\| **\*\*RBAC\*\*** | Role-based access control (Student / Professor / Admin) |

\| **\*\*Real-time dashboard\*\*** | Filtering, statistics, and CSV export of feedback |

\| **\*\*Enhanced security\*\*** | CSRF, rate limiting, headers sécurisés, sessions HttpOnly |

\| **\*\*Cloud-Native\*\*** | Deployed on Azure App Service + Azure SQL Database |

\| **\*\*Export CSV\*\*** | Easy analysis in Excel / Google Sheets |

\| ⏱ **\*\*Anti-spam\*\*** | Limited to 1 feedback per professor per day per IP |



\---



**## Architecture**



**### Architecture Diagram**



\`\`\`mermaid

graph TD

    A[ Web Browser HTTPS] -->|TLS 1.2+| B[Azure App Service]

    B -->|Flask + Gunicorn| C[Presentation Layer]

    C -->|Jinja2 Templates| D[Application Layer]

    D -->|Business Logic| E[Data Layer]

    E -->|ODBC Encrypted| F[(Azure SQL Database)]



    subgraph "Azure App Service"

        B

        C

        D

        G[Flask-WTF CSRF]

        H[Flask-Limiter]

        I[Security Headers]

    end



    subgraph "Azure SQL"

        F

        J[Users Table]

        K[Professors Table]

        L[Feedbacks Table]

    end

\`\`\`



**### 3-Tier Architecture**



\| Layer | Technology | Role |

\| :--- | :--- | :--- |

\| **\*\*Présentation\*\*** | Flask + Jinja2 | User interface, HTML/CSS templates |

\| **\*\*Application\*\*** | Flask + Gunicorn | Business logic, authentication, rate limiting |

\| **\*\*Données\*\*** | Azure SQL Database | Persistent storage, encrypted connections |



\----



**## Sécurité**



**### Defense Mechanisms**



\| Feature | Objective | Technology |

\| :--- | :--- | :--- |

\| **\*\*CSRF Protection\*\*** | Prevent cross-site requests | Flask-WTF |

\| ⏱ **\*\*Rate Limiting\*\*** | Block brute-force attacks and spam | Flask-Limiter (5 tentatives / 60s) |

\| **\*\*Anti-Spam\*\*** | 1 feedback/prof/jour/IP | Custom logic |

\| **\*\*Secure Headers\*\*** | Protection against XSS, clickjacking, and MIME attacks | CSP, HSTS, X-Frame-Options |

\| **\*\*Session Security\*\*** | Secure cookies | HttpOnly + Secure + SameSite |

\| **\*\*Input Sanitization\*\*** | XSS prevention | \`markupsafe.escape()\` |



**### Azure-Level Security**



\- **\*\*TLS 1.2+\*\*** for all communications

\- **\*\*SQL Firewall\*\*** — Only the App Service can connect

\- **\*\*Credentials chiffrés\*\*** — Environment variables (no secrets in the code)

\- **\*\*Network isolation\*\*** — Private endpoints available in production



**### Role-Based Authentication**



\| Role | Authentification | Accès |

\| :--- | :--- | :--- |

\| **\*\*Student\*\*** | None (anonymous) | Submission de feedback uniquement |

\| **\*\*Professor\*\*** | Username + Password | Dashboard showing only their feedback |

\| **\*\*Admin\*\*** | Username + Password | Global access to all data |



\---



**## Database**



**### Relational Schema**



\`\`\`mermaid

erDiagram

    USERS ||--o| PROFESSORS : "has"

    PROFESSORS ||--o{ FEEDBACKS : "receives"



    USERS {

        int ID PK

        string Username

        string PasswordHash

        string Role

        datetime CreatedAt

    }



    PROFESSORS {

        int ID PK

        string Name

        string Email

        string Course

        int AppUserId FK

    }



    FEEDBACKS {

        int ID PK

        int ProfessorID FK

        int Rating

        string Comment

        string StudentIP

        datetime CreatedAt

        boolean IsSpam

    }

\`\`\`



\---



**## User Roles**



**### Student (Anonyme)**

1\. Visits the home page

2\. Accepts the privacy notice

3\. Selects a professor/course

4\. Rates (1–5 stars) + comment

5\. Submits the feedback

6\. **\*\*No account, no tracking\*\***



**### Professor (Authentifié)**

1\. Logs in with credentials

2\. Dashboard avec **\*\*their feedback only\*\***

3\. Filters by date, rating, and course

4\. Exports data to CSV

5\. Views averages and suggestions

6\. **\*\*Cannot view other professors' feedback\*\***



**### Admin / Coordinator (Authenticated)**

1\. Logs in with credentials

2\. Global dashboard (all feedback)

3\. Advanced filtering and analytics

4\. Professor management (add/remove)

5\. System export and reporting

6\. **\*\*Full access to all data\*\***



\---



**## Installation**



**### Prerequisites**



\- Python 3.9+

\- Azure SQL Database (ou SQL Server local)

\- ODBC Driver 18 for SQL Server

\- pip (Python package manager)



**### Local Installation**



**\*\*1. Clone the repository\*\***

\`\`\`bash

git clone https\://github.com/boujaadamohammed/campusvoice.git

cd campusvoice

\`\`\`



**\*\*2. Create a virtual environment\*\***

\`\`\`bash

python -m venv venv

source venv/bin/activate        # Linux/macOS

venv\Scripts\activate           # Windows

\`\`\`



**\*\*3. Install dependencies\*\***

\`\`\`bash

pip install -r requirements.txt

\`\`\`



**\*\*4. Configure environment variables\*\***

\`\`\`bash

cp .env.example .env

\# Edit .env with your Azure SQL credentials

\`\`\`



**\*\*5. Install the ODBC driver\*\*** (if necessary)

\`\`\`bash

\# Ubuntu/Debian:

sudo apt-get install odbc-msodbcsql18



\# macOS:

brew install msodbcsql18



\# Windows: Download from Microsoft

\`\`\`



**\*\*6. Run the application\*\***

\`\`\`bash

\# Development mode

flask run



\# Production mode

gunicorn -w 4 -b 0.0.0.0:8000 app:app

\`\`\`



 Access : \`http\://localhost:5000\`



**### Environment Variables**



Create a file \`.env\` in the root directory :



\`\`\`bash

\# Flask Configuration

FLASK_ENV=production

SECRET_KEY=your-super-secret-key-change-this



\# Azure SQL Database

DB_SERVER=your-server.database.windows.net

DB_USER=your-sql-username

DB_PASSWORD=your-sql-password

DB_NAME=campusvoice_db



\# Security Settings

SESSION_TIMEOUT=1800           # 30 minutes

MAX_LOGIN_ATTEMPTS=5           # Max login attempts

RATE_LIMIT_WINDOW=60           # Window in seconds

\`\`\`



\> **\*\*NEVER commit \`.env\` to version control!\*\***



\---



**## Azure Deployment**



**### Option 1 : Azure CLI (Recommended)**



\`\`\`bash

az login

az group create --name campusvoice-rg --location eastus

az appservice plan create --name campusvoice-plan \\

    --resource-group campusvoice-rg --sku B1 --is-linux

az webapp create --resource-group campusvoice-rg \\

    --plan campusvoice-plan --name campusvoice-app \\

    --runtime "PYTHON|3.11"

az webapp config appsettings set \\

    --resource-group campusvoice-rg --name campusvoice-app \\

    --settings @settings.json

az webapp up --resource-group campusvoice-rg --name campusvoice-app

\`\`\`



**### Option 2 : Azure Portal**

1\. Create an **\*\*App Service\*\*** (Python 3.11)

2\. Create ane **\*\*Azure SQL Database\*\***

3\. Upload the code via Git/ZIP

4\. Configure environment variables

5\. Configure the SQL firewall rules



**### Option 3 : GitHub Actions (CI/CD)**

Automatic deployment on every push via \`.github/workflows/deploy.yml\`



\---



**## Project Structure**



\`\`\`text

campusvoice/

│

├── app.py                      # Main Flask application

├── requirements.txt            # Python dependencies

├── .env.example               # Environment variables template

├── .gitignore                 # Files ignored by Git

├── Procfile                   # Deployment configuration

│

├── static/                    # Static resources

│   ├── style.css              # CSS styles

│  &#x20;

│

├── templates/                 # Jinja2 templates

│   ├── index.html             # Home page

│   ├── login.html             # Login page

│   ├── dashboard.html         # Admin/Professor dashboard

│   ├── feedback-form.html     # Anonymous feedback form

│   └── base.html              # Base template

│

├── deployments/               # Azure configurations

│   ├── azure-deploy.sh        # Deployment script

│   └── README_AZURE.md        # Azure guide

│

└── docs/                      # Documentation

    ├── architecture.md        # Technical architecture

    └── security.md            # Security documentation

\`\`\`



\---



**## Tests**



**### Test the database connection**

\`\`\`bash

\# Visit : http\://localhost:5000/test-db

\# Should return the connection status and the number of tables

\`\`\`



**### Test Rate Limiting**

\`\`\`bash

\# Try several rapid login attempts — access should be blocked after 5 attempts

\`\`\`



**### Test CSRF Protection**

\`\`\`bash

\# Try submitting a form without a CSRF token — it should fail

\`\`\`



\---



**## Roadmap**



**### Implemented**

\- [x] 3-tier Flask + Azure SQL architecture

\- [x] Anonymity system for students

\- [x] Dashboard with filters and CSV export

\- [x] CSRF protection and rate limiting

\- [x] Deployment on Azure App Service



**### In Progress / Upcoming**

\- [ ] Replace MD5 with **\*\*bcrypt/Argon2\*\***

\- [ ] Integrate **\*\*Azure Key Vault\*\*** for secrets

\- [ ] 🆔 Integrate **\*\*Microsoft Entra ID\*\*** (SSO)

\- [ ] **\*\*Multi-Factor Authentication\*\*** (MFA)

\- [ ] Dashboard analytique avec **\*\*Chart.js / D3.js\*\***

\- [ ] Mobile application **\*\*React Native\*\***

\- [ ] Real-time notifications

\- [ ] Report generation **\*\*PDF\*\***

\- [ ] **\*\*Sentiment analysis\*\*** of comments

\- [ ] Spam detection using **\*\*Machine Learning\*\***



\---



**## Team**



\<div align="center">



\<table>

  \<tr>

    \<td align="center">

      \<a href="https\://github.com/mohammed-boujaada">

        \<img src="https\://avatars.githubusercontent.com/mohammed-boujaada" width="120px;" alt="Mohammed Boujaada"/>

        \<br/>

        \<sub>\<b>Mohammed Boujaada\</b>\</sub>

      \</a>

      \<br/>

      MIATE Master's — FPN Nador

      \<br/>

      \<a href="https\://github.com/mohammed-boujaada">

        \<img src="https\://img.shields.io/badge/GitHub-\@mohammed-boujaada-black?logo=github"/>

      \</a>

      \<a href="https\://www\.linkedin.com/in/mohammed-boujaada-229a3333a/">

        \<img src="https\://img.shields.io/badge/LinkedIn-Boujaada%20Mohammed-blue?logo=linkedin"/>

      \</a>

    \</td>

    \<td align="center">

      \<a href="https\://github.com/moza369">

        \<img src="https\://avatars.githubusercontent.com/moza369" width="120px;" alt="Mohamed Zahir"/>

        \<br/>

        \<sub>\<b>Mohamed Zahir\</b>\</sub>

      \</a>

      \<br/>

      MIATE Master's — FPN Nador

      \<br/>

      \<a href="https\://github.com/moza369">

        \<img src="https\://img.shields.io/badge/GitHub-\@moza369-black?logo=github"/>

      \</a>

    \</td>

  \</tr>

\</table>



\</div>



**\*\* Institution\*\*** : FPN Nador — Master Intelligence Artificielle & Technologys Émergentes  

**\*\* Module\*\*** : Cloud Computing  

**\*\* Year\*\*** : 2025 - 2026



\</div>



\---



**## License**



This project is provided **\*\*as is\*\*** for educational purposes.  

Free to use, modify, and share in an academic context.



\---



**## Acknowledgments**



\- **\*\*Microsoft Azure\*\*** — $100 student credit for cloud infrastructure

\- **\*\*Flask\*\*** — Lightweight and high-performance web framework

\- **\*\*FPN Nador\*\*** — Academic supervision and project requirements

\- All contributors and testers



\---



**## Citation**



\`\`\`bibtex

@misc{boujaada2026campusvoice,

  author = {Boujaada Mohammed and Zahir Mohamed},

  title = {CampusVoice: Anonymous University Feedback Platform on Azure},

  year = {2026},

  publisher = {GitHub},

  journal = {GitHub repository},

  howpublished = {\url{https\://github.com/mohammed-boujaada/CampusVoice}}

}

\`\`\`



\---



\<div align="center">



**### ⭐ If you find this project useful, feel free to give it a star!**



**\*\*Developed with par Mohammed Boujaada & Mohamed Zahir\*\***



*\*Academic project — MIATE Master's — FPN Nador — 2026\**



\</div>
