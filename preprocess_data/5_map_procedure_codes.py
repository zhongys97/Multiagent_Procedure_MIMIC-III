import sqlite3
import json

db_path = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/mimic_iii_dictionary.db"
mapping_json_save_dir = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/icd9_procedure_mapping.json"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


query = "SELECT ICD9_CODE, LONG_TITLE FROM D_ICD_PROCEDURES"
cursor.execute(query)
results = cursor.fetchall()

icd_to_procedure_text = {}
procedure_text_to_icd = {}
for icd_code, long_title in results:
    icd_to_procedure_text[icd_code] = long_title
    procedure_text_to_icd[long_title] = icd_code

res = {
    "icd_to_procedure_text": icd_to_procedure_text,
    "procedure_text_to_icd": procedure_text_to_icd,}

with open(mapping_json_save_dir, "w") as f:
    json.dump(res, f, indent=4)