# 🛡️ Sentinel Incident Portal

Sentinel Incident Portal is an enterprise-grade incident management system designed to track, secure, and report cybersecurity incidents. Built with Python and Streamlit, the application features a robust backend using SQL Server, incorporating advanced security measures like encryption-at-rest and dynamic data masking.

## 🚀 Key Features

* **Role-Based Access Control (RBAC):** Granular permission levels for Admins, Analysts, and Viewers.
* **Secure Authentication:** Password hashing using `bcrypt` to ensure credentials are never stored in plain text.
* **Encryption at Rest:** Sensitive incident details are encrypted at the database level using SQL Server Symmetric Keys and Certificates.
* **Dynamic Data Masking:** PII (Personally Identifiable Information) such as contact numbers are masked for non-admin roles.
* **Audit Logging:** Comprehensive tracking of all database modifications and user activities for compliance and monitoring.
* **Interactive Dashboard:** Visualizations of incident severity, audit activity, and system statistics.

## 🔒 Security Architecture
The application is built with a **_Security-by-Design_** philosophy:
- **Encryption**: Incident details are encrypted using AES-256 via `SentinelSymKey`. The application requires proper privileges to perform decryption.
- **Database Security**: The SQL script enforces the principle of least privilege, explicitly denying permissions (e.g., `DENY` `DELETE` to Analysts) via RBAC.
- **Auditability**: Every transaction is written to the `AUDIT_LOGS` table, creating an immutable trail for forensic analysis.

## 🛠️ Technology Stack

* **Frontend:** [Streamlit](https://streamlit.io/)
* **Database:** [Microsoft SQL Server](https://www.microsoft.com/en-us/sql-server/)
* **Drivers:** `pyodbc` (ODBC Driver 17 for SQL Server)
* **Security:** `bcrypt`, SQL Server `ENCRYPTBYKEY` / `DECRYPTBYKEY`, Dynamic Data Masking.
* **Data Analysis:** `pandas`

## 📋 Prerequisites

Before running the application, ensure you have the following installed:
1. **SQL Server**: Ensure an instance is running and mixed-mode authentication is enabled.
2. **ODBC Driver**: Install "ODBC Driver 17 for SQL Server".
3. **Python 3.x**: Recommended version 3.9 or higher.

## 📂 Project Structure
.
├── .streamlit/            # Configuration folder
├── pages/                 # Streamlit multi-page application
│   ├── Admin.py           # Admin panel & user management
│   ├── Audit_Logs.py      # System audit trail & monitoring
│   └── Incidents.py       # Main incident tracking dashboard
├── app.py                 # Application entry point & login
├── db.py                  # Database connection & backend logic
├── db_setup.sql           # Database schema & security setup
├── styles.py              # UI/UX, CSS, and styling components
└── README.md              # Project documentation

## ⚙️ Setup Instructions

### 1. Database Configuration
1. Open SQL Server Management Studio (SSMS).
2. Execute the provided `db_setup.sql` script. This will:
   - Create the `SentinelDB` database.
   - Set up tables and relationships.
   - Configure SQL Logins and Roles.
   - Set up the Master Key, Certificate, and Symmetric Keys for encryption.
   - Implement Dynamic Data Masking.

### 2. Environment Setup
Clone this repository and install the necessary dependencies:

```bash
pip install streamlit pyodbc bcrypt pandas
```

### 3. Running the App
Navigate to the root directory and run the following command:
```bash
streamlit run app.py
```
The portal will launch in your default web browser (typically http://localhost:8501).
