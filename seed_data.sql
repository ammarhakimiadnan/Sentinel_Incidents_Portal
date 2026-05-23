-- ============================================================
-- seed_data.sql
-- Bulk Data Seeder
--
-- This script:
--   1. Clears all existing data (safe reset)
--   2. Reseeds identity counters to start from 1
--   3. Inserts users: alex, amy, noah (password: admin123)
--   4. Inserts 100 randomized incidents with encrypted details
--   5. Verifies the result
--
-- Run this in SSMS whenever you need to reset demo data.
-- Make sure SentinelDB already exists (run db_setup.sql first).
-- ============================================================

USE SentinelDB;
GO

-- ============================================================
-- SECTION 1: CLEAN EXISTING DATA
-- Order matters — delete child tables before parent tables
-- to avoid foreign key constraint errors
-- ============================================================

DELETE FROM AUDIT_LOGS;
DELETE FROM INCIDENTS;
DELETE FROM USER_LOGIN;
DELETE FROM USERS;
DELETE FROM ROLES;
GO

-- ============================================================
-- SECTION 2: RESET IDENTITY COUNTERS
-- Forces IDs to restart from 1 after cleanup
-- ============================================================

DBCC CHECKIDENT ('AUDIT_LOGS',  RESEED, 0);
DBCC CHECKIDENT ('INCIDENTS',   RESEED, 0);
DBCC CHECKIDENT ('USER_LOGIN',  RESEED, 0);
DBCC CHECKIDENT ('USERS',       RESEED, 0);
DBCC CHECKIDENT ('ROLES',       RESEED, 0);
GO

-- ============================================================
-- SECTION 3: INSERT ROLES
-- ============================================================

INSERT INTO ROLES (RoleName, PermissionLevel) VALUES
('Admin',   'Full'),
('Analyst', 'ReadWrite'),
('Viewer',  'ReadOnly');
GO

-- ============================================================
-- SECTION 4: INSERT USERS
-- alex  = Admin  (UserID 1)
-- amy   = Analyst (UserID 2)
-- noah  = Viewer  (UserID 3)
-- ============================================================

INSERT INTO USERS (Username, RoleID, ContactNumber) VALUES
('alex', 1, '0111000001'),
('amy',  2, '0111000002'),
('noah', 3, '0111000003');
GO

-- ============================================================
-- SECTION 5: INSERT USER LOGINS
-- All users share password: admin123
-- Hash generated with: 
--   python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
-- To use a different password, regenerate the hash above
-- and replace the value below before running this script.
-- ============================================================

INSERT INTO USER_LOGIN (UserID, PasswordHash, LastLogin) VALUES
(1, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE()),
(2, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE()),
(3, '$2b$12$qh7tHbvAyrIg2.wXjIEiwOBDAvbzq2l.wPs/GnwEa4ziHDpXzHarS', GETDATE());
GO

-- ============================================================
-- SECTION 6: INSERT 3 FIXED SAMPLE INCIDENTS
-- These 3 appear first and represent clear, readable examples
-- for the report screenshots
-- ============================================================

OPEN SYMMETRIC KEY SentinelSymKey
    DECRYPTION BY CERTIFICATE SentinelCert;

INSERT INTO INCIDENTS (Type, Severity, Details, DetailsEncrypted, ReporterID, Status, CreatedAt) VALUES
('Unauthorised Access', 'High',     '***ENCRYPTED***',
    ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'),
        'Detected login from unknown IP 192.168.99.1 at 2AM outside business hours'),
    1, 'Active', DATEADD(DAY, -5, GETDATE())),

('Data Leak',           'Critical', '***ENCRYPTED***',
    ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'),
        'Sensitive customer file accessed and downloaded without authorisation'),
    2, 'Active', DATEADD(DAY, -3, GETDATE())),

('Phishing Attempt',    'Medium',   '***ENCRYPTED***',
    ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'),
        'Staff member received suspicious email impersonating IT department'),
    3, 'Resolved', DATEADD(DAY, -10, GETDATE()));

CLOSE SYMMETRIC KEY SentinelSymKey;
GO

-- ============================================================
-- SECTION 7: INSERT 100 RANDOMIZED INCIDENTS
-- Each incident gets:
--   - Random type from 9 categories
--   - Random severity (Low / Medium / High / Critical)
--   - Random reporter (alex, amy, or noah)
--   - 80% Active, 20% Resolved
--   - Random timestamp spread over last 90 days
--   - Unique details per type (5 variants each)
-- All details are encrypted using AES-256 SentinelSymKey
-- ============================================================

OPEN SYMMETRIC KEY SentinelSymKey
    DECRYPTION BY CERTIFICATE SentinelCert;

DECLARE @i INT = 1;

-- Temporary variables for each incident
DECLARE @type     NVARCHAR(100)
DECLARE @severity NVARCHAR(20)
DECLARE @details  NVARCHAR(MAX)
DECLARE @reporter INT
DECLARE @status   NVARCHAR(20)
DECLARE @created  DATETIME

WHILE @i <= 100
BEGIN
    -- Random incident type (9 categories)
    SET @type = CASE (ABS(CHECKSUM(NEWID())) % 9)
        WHEN 0 THEN 'Phishing'
        WHEN 1 THEN 'Unauthorised Access'
        WHEN 2 THEN 'Data Leak'
        WHEN 3 THEN 'Malware'
        WHEN 4 THEN 'Ransomware'
        WHEN 5 THEN 'Brute Force'
        WHEN 6 THEN 'DDoS'
        WHEN 7 THEN 'Insider Threat'
        ELSE         'Social Engineering'
    END

    -- Random severity level
    SET @severity = CASE (ABS(CHECKSUM(NEWID())) % 4)
        WHEN 0 THEN 'Low'
        WHEN 1 THEN 'Medium'
        WHEN 2 THEN 'High'
        ELSE         'Critical'
    END

    -- Random reporter: alex(1), amy(2), or noah(3)
    SET @reporter = (ABS(CHECKSUM(NEWID())) % 3) + 1

    -- 80% Active, 20% Resolved
    SET @status = CASE (ABS(CHECKSUM(NEWID())) % 5)
        WHEN 0 THEN 'Resolved'
        ELSE        'Active'
    END

    -- Random timestamp within last 90 days (in minutes: 90 days * 24h * 60min = 129600)
    SET @created = DATEADD(MINUTE, -(ABS(CHECKSUM(NEWID())) % 129600), GETDATE())

    -- Unique details based on incident type — 5 variants per type
    SET @details = CASE @type
        WHEN 'Phishing' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Employee received email impersonating IT department requesting password reset. Ticket #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Suspicious email with malicious link targeting HR staff detected. Ref #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Mass phishing campaign detected targeting finance team members. Case #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Spear phishing attempt targeting CEO email account intercepted. Log #' + CAST(@i AS NVARCHAR)
                ELSE        'Fake invoice email with embedded macro attachment found. Ticket #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Unauthorised Access' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Login detected from unrecognised IP 192.168.' + CAST((ABS(CHECKSUM(NEWID())) % 255) AS NVARCHAR) + '.1 at odd hours. Case #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Former employee account still active and used to access payroll system. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Multiple failed logins followed by successful access from new device. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Admin panel accessed outside business hours without prior approval. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'VPN credentials shared between employees, unauthorised session detected. Ticket #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Data Leak' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Customer PII found uploaded to public GitHub repository. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Sensitive financial report emailed to wrong external recipient. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Database backup file found on unsecured cloud storage bucket. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Employee screenshot of confidential data shared on personal messaging app. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'API endpoint returning unmasked customer records to unauthenticated requests. Ticket #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Malware' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Keylogger detected on workstation WS-' + CAST(@i AS NVARCHAR) + ' in finance department'
                WHEN 1 THEN 'Trojan horse found in downloaded software package on developer machine. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Spyware detected transmitting data to external IP address. Case #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Rootkit installed via USB device on server room terminal. Log #' + CAST(@i AS NVARCHAR)
                ELSE        'Adware bundle installed alongside legitimate software, affecting ' + CAST((ABS(CHECKSUM(NEWID())) % 20 + 1) AS NVARCHAR) + ' machines. Ref #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Ransomware' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Ransomware encrypted shared drive files, ransom note left demanding BTC payment. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'LockBit variant detected on ' + CAST((ABS(CHECKSUM(NEWID())) % 10 + 1) AS NVARCHAR) + ' endpoints, containment in progress. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Backup files targeted and encrypted before main ransomware attack launched. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Ransomware spread via phishing email attachment affecting accounting department. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'Double extortion ransomware detected — data exfiltrated before encryption. Ticket #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Brute Force' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN CAST((ABS(CHECKSUM(NEWID())) % 900 + 100) AS NVARCHAR) + ' failed login attempts on admin account within 10 minutes. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Credential stuffing attack using leaked password database detected. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'SSH brute force attack on DB-Server-' + CAST(@i AS NVARCHAR) + ' from external IP blocked'
                WHEN 3 THEN 'Dictionary attack detected on RDP port, source IP blocked by firewall. Log #' + CAST(@i AS NVARCHAR)
                ELSE        'Brute force attempt on API authentication endpoint rate-limited. Ref #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'DDoS' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'UDP flood attack generating ' + CAST((ABS(CHECKSUM(NEWID())) % 900 + 100) AS NVARCHAR) + 'Gbps traffic detected. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'HTTP layer 7 DDoS targeting login endpoint causing slow response. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'DNS amplification attack causing service degradation for users. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Botnet of ' + CAST((ABS(CHECKSUM(NEWID())) % 9000 + 1000) AS NVARCHAR) + ' nodes targeting main web server. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'SYN flood attack overwhelming network firewall, traffic scrubbing activated. Ticket #' + CAST(@i AS NVARCHAR)
            END

        WHEN 'Insider Threat' THEN
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Employee downloaded bulk customer records the day before submitting resignation. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Staff member accessed files outside their department scope repeatedly. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Contractor installed remote access tool on internal server without authorisation. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Employee found sharing login credentials with external party via email. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'Disgruntled staff member attempted to delete critical database records. Ticket #' + CAST(@i AS NVARCHAR)
            END

        ELSE -- Social Engineering
            CASE (ABS(CHECKSUM(NEWID())) % 5)
                WHEN 0 THEN 'Attacker impersonated IT support over phone and obtained staff credentials. Incident #' + CAST(@i AS NVARCHAR)
                WHEN 1 THEN 'Vishing call tricked employee into revealing one-time password. Case #' + CAST(@i AS NVARCHAR)
                WHEN 2 THEN 'Fake IT helpdesk email convinced user to install remote access tool. Log #' + CAST(@i AS NVARCHAR)
                WHEN 3 THEN 'Physical tailgating into server room by unauthorised visitor detected. Ref #' + CAST(@i AS NVARCHAR)
                ELSE        'Baiting attack using infected USB drive left in company car park. Ticket #' + CAST(@i AS NVARCHAR)
            END
    END

    -- Insert incident with encrypted details
    INSERT INTO INCIDENTS (
        Type, Severity, Details, DetailsEncrypted,
        ReporterID, Status, CreatedAt
    )
    VALUES (
        @type,
        @severity,
        '***ENCRYPTED***',                                            -- Plain Details masked
        ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'), @details),           -- AES-256 encrypted
        @reporter,
        @status,
        @created
    )

    SET @i = @i + 1
END

CLOSE SYMMETRIC KEY SentinelSymKey;
GO

-- ============================================================
-- SECTION 8: VERIFICATION
-- Run after seeding to confirm data looks correct
-- ============================================================

-- Summary counts
SELECT
    COUNT(*)                                                    AS TotalIncidents,
    SUM(CASE WHEN Status = 'Active'   THEN 1 ELSE 0 END)       AS Active,
    SUM(CASE WHEN Status = 'Resolved' THEN 1 ELSE 0 END)       AS Resolved
FROM INCIDENTS;

-- Breakdown by type
SELECT Type, COUNT(*) AS Count
FROM INCIDENTS
GROUP BY Type
ORDER BY Count DESC;

-- Confirm users exist
SELECT u.UserID, u.Username, r.RoleName, u.ContactNumber
FROM USERS u
JOIN ROLES r ON u.RoleID = r.RoleID;

-- Confirm encryption is working (show raw encrypted blob)
SELECT TOP 3
    IncidentID, Type, Details, DetailsEncrypted
FROM INCIDENTS
ORDER BY IncidentID ASC;

-- Confirm decryption works
OPEN SYMMETRIC KEY SentinelSymKey
    DECRYPTION BY CERTIFICATE SentinelCert;

SELECT TOP 3
    IncidentID,
    Type,
    CONVERT(NVARCHAR(MAX), DECRYPTBYKEY(DetailsEncrypted)) AS DecryptedDetails
FROM INCIDENTS
ORDER BY IncidentID ASC;

CLOSE SYMMETRIC KEY SentinelSymKey;
GO

-- ============================================================
-- DONE — Database has been reset and seeded with fresh data
-- Total incidents: ~103 (3 fixed + 100 random)
-- Users: alex (Admin), amy (Analyst), noah (Viewer)
-- All passwords: admin123
-- ============================================================
PRINT '=== Seed complete. SentinelDB is ready. ==='