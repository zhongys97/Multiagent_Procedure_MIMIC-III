import sqlite3

# print tables of db
def print_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    

    for table in tables:
        print(table[0])
    
    conn.close()

# rename tables in the MIMIC-III database
def rename_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    rename_map = {}
    for table in tables:
        rename_map[table[0]] = table[0].replace('_subjects_chunk0', '')
    
    
    for old_name, new_name in rename_map.items():
        cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name};")
    
    conn.commit()
    conn.close()

# Print the tables in the MIMIC-III database

if __name__ == "__main__":
    db_path = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/mimic_iii_subject_chunk0.db"  # Adjust the path to your database file
    print("Before renaming:")
    print_tables(db_path)
    rename_tables(db_path)
    print("After renaming:")
    print_tables(db_path)