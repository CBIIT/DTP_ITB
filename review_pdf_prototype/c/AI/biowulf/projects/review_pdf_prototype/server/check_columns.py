
from dotenv import load_dotenv
import os

# Load environment variables from .env.local
load_dotenv('../.env.local')

from oracle_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Query to see all columns in the table
cursor.execute("""
    SELECT column_name 
    FROM user_tab_columns 
    WHERE table_name = 'REPORT_ROWS_SUBSET'
    ORDER BY column_id
""")

print("Available columns:")
for row in cursor:
    print(f"  - {row[0]}")

cursor.close()
conn.close()