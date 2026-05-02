import pyodbc
import re

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=SentinelDB;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return conn

def get_incidents(decrypt=False, status='Active'):
    conn = get_connection()
    cursor = conn.cursor()
    if decrypt:
        cursor.execute("OPEN SYMMETRIC KEY SentinelSymKey DECRYPTION BY CERTIFICATE SentinelCert")
        cursor.execute("""
            SELECT i.IncidentID, i.Type, i.Severity,
                CONVERT(NVARCHAR(MAX), DECRYPTBYKEY(i.DetailsEncrypted)) AS Details,
                u.Username, i.CreatedAt, i.Status
            FROM INCIDENTS i
            JOIN USERS u ON i.ReporterID = u.UserID
            WHERE i.Status = ?
            ORDER BY i.CreatedAt DESC
        """, (status,))
        rows = cursor.fetchall()
        cursor.execute("CLOSE SYMMETRIC KEY SentinelSymKey")
    else:
        cursor.execute("""
            SELECT i.IncidentID, i.Type, i.Severity,
                '*** ENCRYPTED ***' AS Details,
                u.Username, i.CreatedAt, i.Status
            FROM INCIDENTS i
            JOIN USERS u ON i.ReporterID = u.UserID
            WHERE i.Status = ?
            ORDER BY i.CreatedAt DESC
        """, (status,))
        rows = cursor.fetchall()
    conn.close()
    return rows

def get_incidents_over_time():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            CAST(CreatedAt AS DATE) AS IncidentDate,
            Type,
            COUNT(*) AS Count
        FROM INCIDENTS
        GROUP BY CAST(CreatedAt AS DATE), Type
        ORDER BY IncidentDate ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_active_incident_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IncidentID, Type FROM INCIDENTS WHERE Status = 'Active' ORDER BY IncidentID")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_resolved_incident_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IncidentID, Type FROM INCIDENTS WHERE Status = 'Resolved' ORDER BY IncidentID")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_incident(inc_type, severity, details, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("OPEN SYMMETRIC KEY SentinelSymKey DECRYPTION BY CERTIFICATE SentinelCert")
    cursor.execute("""
        INSERT INTO INCIDENTS (Type, Severity, Details, DetailsEncrypted, ReporterID, Status)
        VALUES (?, ?, ?, ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'), ?), ?, 'Active')
    """, (inc_type, severity, '***ENCRYPTED***', details, user_id))
    cursor.execute("CLOSE SYMMETRIC KEY SentinelSymKey")
    cursor.execute("""
        INSERT INTO AUDIT_LOGS (UserID, ActionType, Status)
        VALUES (?, 'INSERT_INCIDENT', 'Success')
    """, (user_id,))
    conn.commit()
    conn.close()

def resolve_incident(incident_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE INCIDENTS SET Status = 'Resolved' WHERE IncidentID = ?", (incident_id,))
    cursor.execute("""
        INSERT INTO AUDIT_LOGS (UserID, ActionType, Status)
        VALUES (?, 'RESOLVE_INCIDENT', 'Success')
    """, (user_id,))
    conn.commit()
    conn.close()

def delete_incident(incident_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM INCIDENTS WHERE IncidentID = ?", (incident_id,))
    cursor.execute("""
        INSERT INTO AUDIT_LOGS (UserID, ActionType, Status)
        VALUES (?, 'DELETE_INCIDENT', 'Success')
    """, (user_id,))
    conn.commit()
    conn.close()

def get_all_users(role):
    conn = get_connection()
    cursor = conn.cursor()
    if role == 'Admin':
        cursor.execute("""
            SELECT u.UserID, u.Username, r.RoleName, u.ContactNumber
            FROM USERS u JOIN ROLES r ON u.RoleID = r.RoleID
        """)
    else:
        cursor.execute("""
            SELECT u.UserID, u.Username, r.RoleName,
                LEFT(u.ContactNumber, 3) + 'XXXXXXX' AS ContactNumber
            FROM USERS u JOIN ROLES r ON u.RoleID = r.RoleID
        """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_db_stats():
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM INCIDENTS")
    stats['total_incidents'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INCIDENTS WHERE Status = 'Active'")
    stats['active'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INCIDENTS WHERE Status = 'Resolved'")
    stats['resolved'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM USERS")
    stats['total_users'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM AUDIT_LOGS")
    stats['total_audit'] = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM AUDIT_LOGS
        WHERE ActionTime >= CAST(GETDATE() AS DATE)
    """)
    stats['actions_today'] = cursor.fetchone()[0]
    conn.close()
    return stats

def get_audit_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 10
            a.ActionType,
            u.Username,
            a.ActionTime,
            a.Status
        FROM AUDIT_LOGS a
        LEFT JOIN USERS u ON a.UserID = u.UserID
        ORDER BY a.ActionTime DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_action_counts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ActionType, COUNT(*) as Count
        FROM AUDIT_LOGS
        GROUP BY ActionType
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_roles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT RoleID, RoleName FROM ROLES")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_user_role(user_id, role_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE USERS SET RoleID = ? WHERE UserID = ?", (role_id, user_id))
    conn.commit()
    conn.close()

def sanitize_input(text):
    if not text:
        return text
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove script-like content
    text = re.sub(r'(javascript:|on\w+=|<script)', '',
                  text, flags=re.IGNORECASE)
    # Strip leading/trailing whitespace
    return text.strip()

def insert_incident(inc_type, severity, details, user_id):
    # Sanitize inputs before inserting
    inc_type = sanitize_input(inc_type)
    details  = sanitize_input(details)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "OPEN SYMMETRIC KEY SentinelSymKey "
        "DECRYPTION BY CERTIFICATE SentinelCert")
    cursor.execute("""
        INSERT INTO INCIDENTS
            (Type, Severity, Details, DetailsEncrypted, ReporterID, Status)
        VALUES (?, ?, ?, ENCRYPTBYKEY(KEY_GUID('SentinelSymKey'), ?), ?, 'Active')
    """, (inc_type, severity, '***ENCRYPTED***', details, user_id))
    cursor.execute("CLOSE SYMMETRIC KEY SentinelSymKey")
    cursor.execute("""
        INSERT INTO AUDIT_LOGS (UserID, ActionType, Status)
        VALUES (?, 'INSERT_INCIDENT', 'Success')
    """, (user_id,))
    conn.commit()
    conn.close()