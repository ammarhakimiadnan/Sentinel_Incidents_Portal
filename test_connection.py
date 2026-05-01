import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=SentinelDB;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM ROLES")
for row in cursor.fetchall():
    print(row)

conn.close()
print("Connection successful!")