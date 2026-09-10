import oracledb

conn = oracledb.connect(
    user='monitoring_user',
    password='MonitorTest123',
    dsn='172.16.16.169:1521/XEPDB1'
)

cursor = conn.cursor()
cursor.execute("""
    SELECT column_name, data_type, data_length
    FROM all_tab_columns
    WHERE table_name='CDR_EVENTS_V2'
    AND owner='DWH_CTI_TEST'
    ORDER BY column_id
""")

print("Colonnes de CDR_EVENTS_V2:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<15} ({row[2]})")

conn.close()
