import pickle
import numpy as np
import sqlite3
from tqdm import tqdm
import os
from multiprocessing import Pool

with open('/home/hice1/yzhong307/scratch/mimic_iii_1.4/subject_id_chunks.pkl', 'rb') as f:
    patient_list = pickle.load(f, encoding='latin1')


patients = patient_list["subject_id_chunk_0"][1000:]

print(len(patients))


patient_db_dir = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/patient_db"
db_path = '/home/hice1/yzhong307/scratch/mimic_iii_1.4/mimic_iii_subject_chunk0.db'


EXTRACT_PATIENTS = True
EXTRACT_DICTIONARY = False


def save_dictionary_db():
    # dictionary tables are the ones that do not have SUBJECT_ID as col names
    new_db_path = f'mimic_iii_dictionary.db'
    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]

        cursor.execute(f'PRAGMA table_info("{table_name}");')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "SUBJECT_ID" not in column_names:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()

            new_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
            )
            if new_cursor.fetchone():
                print(f"Table {table_name} already exists in dictionary DB. Skipping creation.")
            else:
                # Fetch the CREATE TABLE statement from the original DB
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
                )
                create_table_sql = cursor.fetchone()
                if create_table_sql:
                    new_cursor.execute(create_table_sql[0])
                else:
                    print(f"Warning: No CREATE TABLE SQL found for {table_name}")
                    continue

            if rows:
                placeholders = ",".join("?" * len(rows[0]))
                new_cursor.executemany(
                    f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows
                )
            else:
                print(f"No rows in table {table_name}")
        else:
            print(f"Table {table_name} is not a dictionary table. Skipping.")

    new_conn.commit()
    new_conn.close()


def split_into_patient(patient_id):

    # connect to database
    conn = sqlite3.connect(db_path)
    # create a cursor object
    cursor = conn.cursor()


    patient_id = str(patient_id)
    new_db_path = f'{patient_db_dir}/mimic_iii_subject_{patient_id}.db'

    if os.path.exists(new_db_path):
        print(f"Database for patient {patient_id} already exists. Skipping creation.")
        return

    new_conn = sqlite3.connect(new_db_path)
    new_cursor = new_conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]

        cursor.execute(f'PRAGMA table_info("{table_name}");')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "SUBJECT_ID" in column_names:
            cursor.execute(f'SELECT * FROM "{table_name}" WHERE SUBJECT_ID = ?', (patient_id,))
            rows = cursor.fetchall()

            new_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
            )
            if new_cursor.fetchone():
                print(f"Table {table_name} already exists. Skipping creation.")
            else:
                # Fetch the CREATE TABLE statement from the original DB
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
                )
                create_table_sql = cursor.fetchone()
                if create_table_sql:
                    new_cursor.execute(create_table_sql[0])
                else:
                    print(f"Warning: No CREATE TABLE SQL found for {table_name}")
                    continue

            if rows:
                placeholders = ",".join("?" * len(rows[0]))
                new_cursor.executemany(
                    f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows
                )
            else:
                # print(f"No rows for patient {patient_id} in table {table_name}")
                pass
        else:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()

            new_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
            )
            if new_cursor.fetchone():
                print(f"Table {table_name} already exists in dictionary DB. Skipping creation.")
            else:
                # Fetch the CREATE TABLE statement from the original DB
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
                )
                create_table_sql = cursor.fetchone()
                if create_table_sql:
                    new_cursor.execute(create_table_sql[0])
                else:
                    print(f"Warning: No CREATE TABLE SQL found for {table_name}")
                    continue

            if rows:
                placeholders = ",".join("?" * len(rows[0]))
                new_cursor.executemany(
                    f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows
                )
            else:
                # print(f"No rows in table {table_name}")
                pass

    new_conn.commit()
    new_conn.close()
    conn.close()


if __name__ == "__main__":
    if EXTRACT_PATIENTS:

        # use multiprocessing to speed up the process

        
        # with Pool(processes=10) as pool:
        #     for _ in tqdm(pool.imap_unordered(split_into_patient, patients[:10]), total=len(patients[:10])):
        #         pass

        # with Pool(processes=10) as pool:
        #     pool.map(split_into_patient, patients)

        for i in tqdm(range(len(patients))):
            print(f"Processing patient {patients[i]}")
            try:
                split_into_patient(patients[i])
            except Exception as e:
                print(f"Error processing patient {patients[i]}: {e}")

    if EXTRACT_DICTIONARY:
        save_dictionary_db()