#!/usr/bin/env python3
import sqlite3

# Connect to the database
conn = sqlite3.connect('./data/research.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables: {tables}")

# Check papers count
if 'papers' in tables:
    cursor.execute("SELECT COUNT(*) FROM papers")
    papers_count = cursor.fetchone()[0]
    print(f"Papers count: {papers_count}")

# Check key_terms table
if 'key_terms' in tables:
    cursor.execute("SELECT COUNT(*) FROM key_terms")
    key_terms_count = cursor.fetchone()[0]
    print(f"Key terms count: {key_terms_count}")
    
    if key_terms_count > 0:
        cursor.execute("SELECT term, frequency FROM key_terms ORDER BY frequency DESC LIMIT 5")
        top_terms = cursor.fetchall()
        print(f"Top 5 key terms: {top_terms}")
else:
    print("key_terms table does not exist")

# Check research_summaries table
if 'research_summaries' in tables:
    cursor.execute("SELECT COUNT(*) FROM research_summaries")
    summaries_count = cursor.fetchone()[0]
    print(f"Research summaries count: {summaries_count}")
else:
    print("research_summaries table does not exist")

conn.close()
