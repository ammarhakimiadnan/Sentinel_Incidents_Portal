USE master;
GO

-- ============================================================
-- SECTION 1: CREATE DATABASE
-- ============================================================

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'SentinelDB')
    DROP DATABASE SentinelDB;
GO

CREATE DATABASE SentinelDB;
GO

USE SentinelDB;
GO

-- ============================================================
-- SECTION 2: CREATE TABLES
-- ============================================================

CREATE TABLE ROLES (
    RoleID INT PRIMARY KEY IDENTITY(1,1),
    RoleName NVARCHAR(50) NOT NULL,
    PermissionLevel NVARCHAR(50) NOT NULL
);

CREATE TABLE USERS (
    UserID INT PRIMARY KEY IDENTITY(1,1),
    Username NVARCHAR(100) NOT NULL UNIQUE,
    RoleID INT NOT NULL,
    ContactNumber NVARCHAR(20),
    FOREIGN KEY (RoleID) REFERENCES ROLES(RoleID)
);

CREATE TABLE USER_LOGIN (
    LoginID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT NOT NULL UNIQUE,
    PasswordHash NVARCHAR(256) NOT NULL,
    LastLogin DATETIME,
    FOREIGN KEY (UserID) REFERENCES USERS(UserID)
);

CREATE TABLE INCIDENTS (
    IncidentID INT PRIMARY KEY IDENTITY(1,1),
    Type NVARCHAR(100) NOT NULL,
    Severity NVARCHAR(20) NOT NULL,
    Details NVARCHAR(MAX),
    DetailsEncrypted VARBINARY(MAX),
    ReporterID INT NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ReporterID) REFERENCES USERS(UserID)
);

CREATE TABLE AUDIT_LOGS (
    AuditID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT,
    ActionType NVARCHAR(100) NOT NULL,
    ActionTime DATETIME DEFAULT GETDATE(),
    Status NVARCHAR(50),
    FOREIGN KEY (UserID) REFERENCES USERS(UserID)
);
GO

-- ============================================================
-- SECTION 3: SEED DATA
-- ============================================================

INSERT INTO ROLES (RoleName, PermissionLevel) VALUES
('Admin', 'Full'),
('Analyst', 'ReadWrite'),
('Viewer', 'ReadOnly');

INSERT INTO USERS (Username, RoleID, ContactNumber) VALUES
('alex', 1, '0111000001'),
('amy', 2, '0111000002'),
('noah', 3, '0111000003');

-- Password for all users: admin123
-- To regenerate: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
INSERT INTO USER_LOGIN (UserID, PasswordHash, LastLogin) VALUES
(1, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE()),
(2, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE()),
(3, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE());

INSERT INTO INCIDENTS (Type, Severity, Details, ReporterID) VALUES
('Unauthorised Access', 'High', 'Detected login from unknown IP at 2AM', 1),
('Data Leak', 'Critical', 'Sensitive file accessed without permission', 2),
('Phishing Attempt', 'Medium', 'Staff received suspicious email', 3);
GO

-- ============================================================
-- SECTION 4: SQL LOGINS & RBAC (run as sa or sysadmin)
-- ============================================================

USE master;
GO

-- Enable mixed mode authentication
EXEC xp_instance_regwrite
    N'HKEY_LOCAL_MACHINE',
    N'Software\Microsoft\MSSQLServer\MSSQLServer',
    N'LoginMode',
    REG_DWORD,
    2;
GO

-- Create SQL Server logins
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'Alex')
    CREATE LOGIN Alex WITH PASSWORD = 'Alex@Sentinel123';

IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'Amy')
    CREATE LOGIN Amy WITH PASSWORD = 'Amy@Sentinel123';

IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'Noah')
    CREATE LOGIN Noah WITH PASSWORD = 'Noah@Sentinel123';
GO

USE SentinelDB;
GO

-- Create database users mapped to logins
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'Alex')
    CREATE USER Alex FOR LOGIN Alex;

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'Amy')
    CREATE USER Amy FOR LOGIN Amy;

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'Noah')
    CREATE USER Noah FOR LOGIN Noah;
GO

-- Assign roles (Least Privilege)
ALTER ROLE db_owner ADD MEMBER Alex;
ALTER ROLE db_datareader ADD MEMBER Amy;
ALTER ROLE db_datawriter ADD MEMBER Amy;
ALTER ROLE db_datareader ADD MEMBER Noah;
GO

-- Deny specific permissions
DENY DELETE ON dbo.INCIDENTS TO Amy;
DENY INSERT ON dbo.INCIDENTS TO Noah;
DENY UPDATE ON dbo.INCIDENTS TO Noah;
DENY DELETE ON dbo.INCIDENTS TO Noah;
DENY INSERT ON dbo.AUDIT_LOGS TO Noah;
DENY UPDATE ON dbo.AUDIT_LOGS TO Noah;
DENY DELETE ON dbo.AUDIT_LOGS TO Noah;
GO

-- ============================================================
-- SECTION 5: ENCRYPTION (Master Key, Certificate, Symmetric Key)
-- ============================================================

USE SentinelDB;
GO

CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Sentinel@MasterKey123';
GO

CREATE CERTIFICATE SentinelCert
    WITH SUBJECT = 'Sentinel Incident Portal Certificate';
GO

CREATE SYMMETRIC KEY SentinelSymKey
    WITH ALGORITHM = AES_256
    ENCRYPTION BY CERTIFICATE SentinelCert;
GO

-- Encrypt existing Details into DetailsEncrypted column
OPEN SYMMETRIC KEY SentinelSymKey
    DECRYPTION BY CERTIFICATE SentinelCert;

UPDATE INCIDENTS
SET DetailsEncrypted = ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'), Details);

CLOSE SYMMETRIC KEY SentinelSymKey;
GO

-- ============================================================
-- SECTION 6: DYNAMIC DATA MASKING
-- ============================================================

USE SentinelDB;
GO

ALTER TABLE USERS
ALTER COLUMN ContactNumber
ADD MASKED WITH (FUNCTION = 'partial(0, "XXXXXXX", 3)');

GRANT UNMASK TO Alex;
GO

-- ============================================================
-- SECTION 7: VERIFICATION QUERIES
-- ============================================================

USE SentinelDB;
GO

-- Check users and roles
SELECT u.UserID, u.Username, r.RoleName, u.ContactNumber
FROM USERS u
JOIN ROLES r ON u.RoleID = r.RoleID;

-- Check incidents
SELECT i.IncidentID, i.Type, i.Severity, u.Username, i.CreatedAt
FROM INCIDENTS i
JOIN USERS u ON i.ReporterID = u.UserID;

-- Check encryption
OPEN SYMMETRIC KEY SentinelSymKey
    DECRYPTION BY CERTIFICATE SentinelCert;

SELECT
    IncidentID,
    Type,
    DetailsEncrypted,
    CONVERT(NVARCHAR(MAX), DECRYPTBYKEY(DetailsEncrypted)) AS DetailsDecrypted
FROM INCIDENTS;

CLOSE SYMMETRIC KEY SentinelSymKey;

-- Check RBAC assignments
SELECT
    u.name AS UserName,
    r.name AS RoleName
FROM sys.database_role_members rm
JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
JOIN sys.database_principals u ON rm.member_principal_id = u.principal_id
WHERE u.name IN ('Alex', 'Amy', 'Noah');
GO