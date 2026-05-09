# 🛡️ Sentinel Incident Portal

Sentinel Incident Portal is an enterprise-grade incident management system designed to track, secure, and report cybersecurity incidents. Built with Python and Streamlit, the application features a robust backend using Microsoft SQL Server, incorporating advanced security measures like AES-256 column encryption, dynamic data masking, role-based access control, and comprehensive audit logging.

---

## 🚀 Key Features

- **Role-Based Access Control (RBAC):** Granular permission levels for Admins, Analysts, and Viewers — enforced at both the application and SQL Server level.
- **Secure Authentication:** Password hashing using `bcrypt`. Login lockout after 5 failed attempts. Session timeout after 15 minutes of inactivity.
- **Encryption at Rest:** Sensitive incident details encrypted at the database level using SQL Server AES-256 Symmetric Keys and Certificates.
- **Dynamic Data Masking:** PII (contact numbers) masked for non-admin roles at the SQL Server level.
- **Dual Audit Logging:** Application-level `AUDIT_LOGS` table + SQL Server file-based audit trail (`SentinelAudit`).
- **SQL Injection Prevention:** All database queries use parameterized `?` placeholders via `pyodbc`.
- **XSS Prevention:** Input sanitization strips HTML tags and script injections before any data reaches the database.
- **Interactive SOC Dashboard:** Real-time visualizations — line chart, donut chart, bar chart, and KPI strip.

---

## 🔒 Security Architecture

Built with a **Security-by-Design** philosophy across multiple layers:

| Layer | Control | Implementation |
|---|---|---|
| Authentication | Password hashing | bcrypt |
| Authentication | Brute force guard | 5-attempt lockout |
| Authentication | Session management | 15-min timeout |
| Database | Least privilege | RBAC + DENY statements |
| Database | Encryption at rest | AES-256 column encryption |
| Database | PII protection | Dynamic Data Masking |
| Database | Audit trail | SQL Server Audit + AUDIT_LOGS table |
| Application | SQL injection | Parameterized queries |
| Application | XSS | Input sanitizer |
| Connection | Transport security | Encrypt=yes in pyodbc |

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit (Python) |
| Backend | Python + pyodbc |
| Database | Microsoft SQL Server 2022 |
| ODBC Driver | ODBC Driver 17 for SQL Server |
| Password Security | bcrypt |
| Data Visualization | Plotly, Pandas |
| DB Encryption | SQL Server ENCRYPTBYKEY / DECRYPTBYKEY |

---

## 📋 Prerequisites

Before running the application, make sure you have all of the following installed:

### 1. Microsoft SQL Server 2022
- Download from: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
- Choose **Developer** or **Express** edition (both free)
- During installation, enable **Mixed Mode Authentication** and set an SA password
- After installation, restart the SQL Server service

### 2. SQL Server Management Studio (SSMS)
- Download from: https://aka.ms/ssmsfullsetup
- Used to run the database setup script

### 3. ODBC Driver 17 for SQL Server
- Download from: https://aka.ms/downloadmsodbcsql
- Choose the **64-bit** `.msi` installer
- Run the installer and complete setup
- Verify installation by running in Python:
  ```python
  import pyodbc
  print(pyodbc.drivers())
  # Should show: 'ODBC Driver 17 for SQL Server'
  ```

### 4. Python 3.9 or higher
- Download from: https://www.python.org/downloads/
- **Important:** During installation, tick **"Add Python to PATH"**
- Verify: `python --version`

---

## ⚙️ Setup Instructions

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOURUSERNAME/sentinel-incident-portal.git
cd sentinel-incident-portal
```

### Step 2 — Install Python dependencies

```bash
pip install streamlit pyodbc bcrypt pandas plotly
```

All required packages:

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `pyodbc` | SQL Server connection |
| `bcrypt` | Password hashing |
| `pandas` | Data manipulation for charts |
| `plotly` | Interactive charts |

### Step 3 — Configure SQL Server

Open **SQL Server Management Studio (SSMS)** and connect to `localhost` using Windows Authentication.

Then open `db_setup.sql` in SSMS and execute it. This script will automatically:
- Create the `SentinelDB` database
- Create all 5 tables (USERS, ROLES, USER_LOGIN, INCIDENTS, AUDIT_LOGS)
- Create SQL Server logins for Alex, Amy, and Noah
- Assign RBAC roles and DENY permissions
- Set up Master Key, Certificate, and AES-256 Symmetric Key
- Apply Dynamic Data Masking to ContactNumber
- Enable SQL Server Audit writing to `C:\AuditLogs\`
- Seed initial users and sample incidents

> **Note:** The script creates the `C:\AuditLogs\` folder path — make sure to create this folder manually before running:
> ```cmd
> mkdir C:\AuditLogs
> ```

### Step 4 — Verify the database connection

Create a file called `test_connection.py` and run it:

```python
import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=SentinelDB;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM ROLES")
for row in cursor.fetchall():
    print(row)
conn.close()
print("Connection successful!")
```

```bash
python test_connection.py
```

Expected output:
```
(1, 'Admin', 'Full')
(2, 'Analyst', 'ReadWrite')
(3, 'Viewer', 'ReadOnly')
Connection successful!
```

### Step 5 — Run the application

Navigate to the `sentinel_portal` folder and run:

```bash
cd sentinel_portal
streamlit run Login.py
```

The app will open automatically at `http://localhost:8501`

---

## 👤 Default Login Credentials

All users share the same default password for testing:

| Username | Password | Role | Permissions |
|---|---|---|---|
| `alex` | `admin123` | Admin | Full access — view, insert, resolve, delete, admin panel |
| `amy` | `admin123` | Analyst | Can view and insert/resolve incidents — cannot delete |
| `noah` | `admin123` | Viewer | Read-only — can only view incidents |

> **Security Note:** Change these passwords in production. To generate a new bcrypt hash:
> ```bash
> python -c "import bcrypt; print(bcrypt.hashpw(b'yournewpassword', bcrypt.gensalt()).decode())"
> ```
> Then update the hash in SSMS:
> ```sql
> USE SentinelDB;
> UPDATE USER_LOGIN SET PasswordHash = 'PASTE_NEW_HASH' WHERE UserID = 1;
> ```

---

## 📂 Project Structure

```
sentinel_portal/
├── .streamlit/
│   └── config.toml          # Dark theme configuration
├── pages/
│   ├── 01_Incidents.py      # Main SOC dashboard with charts and incident management
│   ├── 02_Admin.py          # Admin panel — user management, stats, audit overview
│   └── 03_Audit_Logs.py     # Full audit trail with expandable log entries
├── Login.py                 # Application entry point — login form + auth logic
├── db.py                    # All database functions — queries, encryption, sanitization
├── styles.py                # Global CSS + sidebar component
├── db_setup.sql             # Complete database schema + security setup script
└── security_test.sql        # 20 security test queries for SSMS verification
```

---

## 🔬 Security Testing

A full security test suite is provided in `security_test.sql`. Run each test in SSMS.

Tests covered:

| # | Test | Expected Result |
|---|---|---|
| 1 | Password policy | Amy + Noah: expiration=1, policy=1 |
| 2 | RBAC role assignments | Alex=db_owner, Amy=reader+writer, Noah=reader |
| 3 | DENY permissions | Full list of denied actions |
| 4 | Noah DELETE denied | Permission denied error |
| 5 | Amy DELETE denied | Permission denied error |
| 6 | Noah INSERT denied | Permission denied error |
| 7 | Noah USER_LOGIN access denied | Permission denied error |
| 8 | Amy USER_LOGIN access denied | Permission denied error |
| 9 | Raw encrypted data | Binary blob in DetailsEncrypted |
| 10 | Decrypt with key | Original readable text restored |
| 11 | DDM — Noah sees masked | XXXXXXX001, XXXXXXX002, XXXXXXX003 |
| 12 | DDM — Alex sees full | 0111000001, 0111000002, 0111000003 |
| 13 | Encryption keys exist | AES_256, 256-bit key confirmed |
| 14 | SQL Server Audit running | is_state_enabled = 1 |
| 15 | Audit spec active | is_state_enabled = 1 |
| 16 | Amy's access in audit file | SL action recorded |
| 17 | App AUDIT_LOGS table | All action types logged |
| 18A | Before delete | Incident exists in DB |
| 18B | After delete | Incident gone, audit confirms deletion |
| 19 | After insert | New incident at top of results |
| 20 | Full security summary | All controls active in one view |

For app-level security tests (SQL injection, brute force):
- **SQL Injection:** Enter `' OR '1'='1` as username → should show "User not found"
- **Brute Force:** Enter wrong password 5 times → account locks out

---

## ⚠️ Troubleshooting

**Cannot connect to SQL Server in SSMS:**
- Search for `Services` in Start Menu
- Find `SQL Server (MSSQLSERVER)` and make sure it is Running
- Try server name `localhost` or just `.` in SSMS

**pyodbc connection error:**
- Run `python -c "import pyodbc; print(pyodbc.drivers())"` to check installed drivers
- Make sure `ODBC Driver 17 for SQL Server` appears in the list
- If not, download and install it from https://aka.ms/downloadmsodbcsql

**Streamlit not found:**
- Run `pip install streamlit` and try again
- Make sure you are in the `sentinel_portal` directory when running `streamlit run Login.py`

**Audit log folder error:**
- Make sure `C:\AuditLogs\` exists before running `db_setup.sql`
- Run `mkdir C:\AuditLogs` in Command Prompt as Administrator

---

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.
