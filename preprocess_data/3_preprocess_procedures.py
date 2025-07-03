import sqlite3
import json
from datetime import datetime
import os
from openai import OpenAI
from tqdm import tqdm
import time

database_dir = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/patient_db"
json_save_dir = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/patient_procedures_json"

class MIMIC3PatientEHRSerializer:
    def __init__(self, db_path, openai_api_token_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT HADM_ID, ADMITTIME, DISCHTIME, INSURANCE, LANGUAGE FROM ADMISSIONS ORDER BY ADMITTIME ASC;")
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            print("No admission IDs found in the ADMISSIONS table.")

        self.admission_ids = [row[0] for row in rows]
        self.admission_times = [row[1] for row in rows]
        self.discharge_times = [row[2] for row in rows]
        self.insurances = [row[3] for row in rows]

        language = [row[4] for row in rows if row[4] is not None]
        if language:
            self.language = language[0]
        else:
            self.language = "Unknown"
        
        

        self.cursor.execute("SELECT SUBJECT_ID, GENDER, DOB FROM PATIENTS LIMIT 1;")
        patient_info = self.cursor.fetchone()
        if patient_info:
            self.subject_id = patient_info[0]
            self.gender = patient_info[1]
            self.dob = patient_info[2]
        else:
            print("No patient information found in the PATIENTS table.")

        
        self.cursor.execute("SELECT ETHNICITY FROM ADMISSIONS LIMIT 1;")
        admission_info = self.cursor.fetchone()
        if admission_info:
            self.ethnicity = admission_info[0]
        else:
            print("No admission information found in the ADMISSIONS table.")

        with open(openai_api_token_path, 'r') as f:
            api_keys = json.load(f)

        os.environ["OPENAI_API_KEY"] = api_keys["openai_api_key"]


    def get_ground_truth_procedures(self, admission_id):
        query = f"""
            SELECT PROCEDURES_ICD.ICD9_CODE, LONG_TITLE FROM PROCEDURES_ICD
            JOIN D_ICD_PROCEDURES ON PROCEDURES_ICD.ICD9_CODE = D_ICD_PROCEDURES.ICD9_CODE
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY SEQ_NUM ASC;
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        procedures_icd9 = [row[0] for row in rows if row[0] is not None]
        procedures_text = [row[1] for row in rows if row[1] is not None]
        return procedures_icd9, procedures_text


    def serialize_chartevents(self, admission_id, end_each_window):
        query = f"""
            SELECT CHARTTIME, LABEL, VALUE, VALUEUOM FROM CHARTEVENTS
            JOIN D_ITEMS ON CHARTEVENTS.ITEMID = D_ITEMS.ITEMID
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY CHARTTIME ASC;
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        chartevents = []
        chartevents_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            chartevent = f"{row[0][:-3]}: {row[1]}: {row[2]} {row[3]}"
            chartevents.append(chartevent)

            # check if charttime is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                chartevents_windows[window_idx].append(chartevent)
            else:
                window_idx += 1
        return chartevents, chartevents_windows


    def serialize_diagnoses(self, admission_id):
        query = f"""
            SELECT LONG_TITLE, SEQ_NUM FROM DIAGNOSES_ICD
            JOIN D_ICD_DIAGNOSES ON DIAGNOSES_ICD.ICD9_CODE = D_ICD_DIAGNOSES.ICD9_CODE
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY CAST(SEQ_NUM AS FLOAT);
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        diagnoses = []
        for row in rows:
            if any(x is None for x in row):
                continue
            diagnosis = row[0]

            diagnoses.append(diagnosis)
        return diagnoses

    def serialize_inputevents(self, admission_id, end_each_window):
        # join the two tables
        query = f"""
            SELECT iec.charttime AS time, d.label, iec.amount, iec.amountuom AS unit
            FROM inputevents_cv iec
            JOIN d_items d ON iec.itemid = d.itemid
            WHERE iec.hadm_id LIKE '{admission_id}%'

            UNION ALL

            SELECT iem.starttime AS time, d.label, iem.amount, iem.amountuom AS unit
            FROM inputevents_mv iem
            JOIN d_items d ON iem.itemid = d.itemid
            WHERE iem.hadm_id LIKE '{admission_id}%'

            ORDER BY time;
            """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        inputevents = []
        inputevents_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            inputevent = f"{row[0][:-3]}: {row[1]}: {row[2]} {row[3]}"
            inputevents.append(inputevent)

            # check if charttime is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                inputevents_windows[window_idx].append(inputevent)
            else:
                window_idx += 1
        return inputevents, inputevents_windows

    def serialize_labevents(self, admission_id, end_each_window):
        query = f"""
            SELECT CHARTTIME, LABEL, VALUE, VALUEUOM FROM LABEVENTS
            JOIN D_LABITEMS ON LABEVENTS.ITEMID = D_LABITEMS.ITEMID
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY CHARTTIME ASC;
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        labevents = []
        labevents_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            labevent = f"{row[0][:-3]}: {row[1]}: {row[2]} {row[3]}"
            labevents.append(labevent)

            # check if charttime is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                labevents_windows[window_idx].append(labevent)
            else:
                window_idx += 1
        return labevents, labevents_windows

    def serialize_microbiologyevents(self, admission_id, end_each_window):
        query = f"""
            SELECT CHARTTIME, SPEC_TYPE_DESC, ORG_NAME, AB_NAME, DILUTION_TEXT, INTERPRETATION FROM MICROBIOLOGYEVENTS
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY CHARTTIME ASC;
        """
        interpret_text = {
            "S": "susceptible",
            "R": "resistant",
            "I": "intermediate",
        }
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        microbiologyevents = []
        microbiologyevents_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            microbiologyevent = f"{row[0][:-3]}: Culture {row[2]} from {row[1]}, {interpret_text[row[5]]} to {row[3]} at {row[4]}"
            microbiologyevents.append(microbiologyevent)

            # check if charttime is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                microbiologyevents_windows[window_idx].append(microbiologyevent)
            else:
                window_idx += 1
        return microbiologyevents, microbiologyevents_windows


    def serialize_outputevents(self, admission_id, end_each_window):
        query = f"""
            SELECT CHARTTIME, LABEL, VALUE, VALUEUOM FROM OUTPUTEVENTS
            JOIN D_ITEMS ON OUTPUTEVENTS.ITEMID = D_ITEMS.ITEMID
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY CHARTTIME ASC;
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        outputevents = []
        outputevents_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            outputevent = f"{row[0][:-3]}: {row[1]}: {row[2]} {row[3]}"
            outputevents.append(outputevent)

            # check if charttime is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                outputevents_windows[window_idx].append(outputevent)
            else:
                window_idx += 1
        return outputevents, outputevents_windows

    def serialize_prescriptions(self, admission_id, end_each_window):
        query = f"""
            SELECT STARTDATE, DRUG, DOSE_VAL_RX, DOSE_UNIT_RX FROM PRESCRIPTIONS
            WHERE HADM_ID LIKE '{admission_id}%'
            ORDER BY STARTDATE ASC;
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        prescriptions = []
        prescriptions_windows = [[] for _ in range(len(end_each_window))]  # Initialize a list for each window
        window_idx = 0
        for row in rows:
            if any(x is None for x in row):
                continue
            prescription = f"{row[0][:-3]}: {row[1]}: {row[2]} {row[3]}"
            prescriptions.append(prescription)

            # check if startdate is before the end of the current window
            if window_idx < len(end_each_window) and row[0] <= end_each_window[window_idx]:
                prescriptions_windows[window_idx].append(prescription)
            else:
                window_idx += 1
        return prescriptions, prescriptions_windows


    @staticmethod
    def summarize_ehr(ehr_data):

        prompt = f"""
                    Summarize the following EHR with the following constraints:
                    1. Within 300 words, the more concise the better.
                    2. Prioritize the most important information
                    3. You can skip keys if the associated information is less important.
                    4. Directly jump into the content of the EHR, do not include any preamble.
                    5. Do not have a summary at the end.
                    EHR: {str(ehr_data)}
                    """
        try:

            client = OpenAI()
            response = client.responses.create(
                model="gpt-4o-mini",
                input=prompt
            )

            return response.output_text
        except Exception as e:

            if "rate limit" in str(e).lower():
                print("Hitting rate limit, retrying after 30 seconds...")
                time.sleep(30)
                
                try:
                    client = OpenAI()
                    response = client.responses.create(
                        model="gpt-4o-mini",
                        input=prompt
                    )
                    return response.output_text
                except Exception as e:
                    print(f"An error occurred after retrying: {e}")
                    return ""

            else:
                print(f"An error occurred: {e}")
                return ""



    def process_admission(self, admission_cnt_idx):

        procedures_icd9, procedures_text = self.get_ground_truth_procedures(self.admission_ids[admission_cnt_idx])

        admission_time = self.admission_times[admission_cnt_idx]
        discharge_time = self.discharge_times[admission_cnt_idx]
        insurance = self.insurances[admission_cnt_idx]

        admission_time_dt = datetime.strptime(admission_time, "%Y-%m-%d %H:%M:%S")
        dob = datetime.strptime(self.dob, "%Y-%m-%d %H:%M:%S")

        age_at_admission = round((admission_time_dt - dob).days / 365.25, 1)  # using 365.25 to account for leap years

        discharge_time_dt = datetime.strptime(discharge_time, "%Y-%m-%d %H:%M:%S")
        time_diff = discharge_time_dt - admission_time_dt

        N = len(procedures_icd9) if procedures_icd9 else 1  # Number of windows based on procedures, at least 1

        window_duration = time_diff / N

        start_each_window = [
            (admission_time_dt + i * window_duration).strftime("%Y-%m-%d %H:%M")
            for i in range(N)
        ]

        end_each_window = [
            (admission_time_dt + (i + 1) * window_duration).strftime("%Y-%m-%d %H:%M")
            for i in range(N)
        ]

        diagnoses = self.serialize_diagnoses(self.admission_ids[admission_cnt_idx])
        chartevents, chartevents_windows = self.serialize_chartevents(self.admission_ids[admission_cnt_idx], end_each_window)
        inputevents, inputevents_windows = self.serialize_inputevents(self.admission_ids[admission_cnt_idx], end_each_window)
        labevents, labevents_windows = self.serialize_labevents(self.admission_ids[admission_cnt_idx], end_each_window)
        microbiologyevents, microbiologyevents_windows = self.serialize_microbiologyevents(self.admission_ids[admission_cnt_idx], end_each_window)
        outputevents, outputevents_windows = self.serialize_outputevents(self.admission_ids[admission_cnt_idx], end_each_window)
        prescriptions, prescriptions_windows = self.serialize_prescriptions(self.admission_ids[admission_cnt_idx], end_each_window)

        procedure_text_windows = [[""]]
        if len(procedures_text) > 0:
            for i in range(len(end_each_window)):
                procedure_text_windows.append([procedures_text[i]])
        else:
            procedure_text_windows.append([""])

        current_admission_ehr = {
            "chartevents": chartevents,
            "diagnoses": diagnoses,
            "inputevents": inputevents,
            "labevents": labevents,
            "microbiologyevents": microbiologyevents,
            "outputevents": outputevents,
            "prescriptions": prescriptions
        }

        windowed_current_admission_ehr = []
        for i in range(len(end_each_window)):
            windowed_ehr = {
                "chartevents": chartevents_windows[i],
                "diagnoses": diagnoses,
                "inputevents": inputevents_windows[i],
                "labevents": labevents_windows[i],
                "microbiologyevents": microbiologyevents_windows[i],
                "outputevents": outputevents_windows[i],
                "prescriptions": prescriptions_windows[i],
                "procedures": procedure_text_windows[i]
            }

            window_info = {
                "window_idx": i,
                "window_start_time": start_each_window[i],
                "window_end_time": end_each_window[i],
                "ground_truth_procedures_icd9": procedures_icd9[i] if i < len(procedures_text) else "",
                "ground_truth_procedures_text": procedures_text[i] if i < len(procedures_text) else "",
                "windowed_ehr": windowed_ehr
            }
            windowed_current_admission_ehr.append(window_info)


        admission_info = {
            "admission_id": self.admission_ids[admission_cnt_idx],
            "admission_time": admission_time,
            "discharge_time": discharge_time,
            "insurance": insurance,
            "age_at_admission": age_at_admission,
            "procedures_icd9": procedures_icd9,
            "procedures_text": procedures_text,
            "current_admission_ehr": current_admission_ehr,
            "windowed_current_admission_ehr": windowed_current_admission_ehr,
        }

        # Summarize the EHR data
        ehr_summary = self.summarize_ehr(current_admission_ehr)
        admission_info["ehr_summary"] = ehr_summary

        return admission_info


    def process_patient(self):
        
        admissions_ehr = []
        for i, admission_id in enumerate(self.admission_ids):
            # print("=" * 20)
            
            admissions_ehr.append(self.process_admission(i))
        self.conn.close()
        
        patient_data = {
            "subject_id": self.subject_id,
            "gender": self.gender,
            "dob": self.dob,
            "ethnicity": self.ethnicity,
            "language": self.language,
            "admissions": admissions_ehr,
        }

        return patient_data



if __name__ == "__main__":
    
    db_paths = [os.path.join(database_dir, f) for f in os.listdir(database_dir) if f.endswith('.db')]

    for patient_db_path in tqdm(db_paths):

        try:

            print(f"Processing patient database: {os.path.basename(patient_db_path)}")

            processor = MIMIC3PatientEHRSerializer(patient_db_path, "./../api_keys.json")
            serialized_patient_ehr = processor.process_patient()

            json_save_path = os.path.join(json_save_dir, f"{os.path.basename(patient_db_path)}.json")

            with open(json_save_path, "w") as f:
                json.dump(serialized_patient_ehr, f, indent=4)

        except Exception as e:
            print(f"An error occurred while processing {os.path.basename(patient_db_path)}: {e}")


    # processor = MIMIC3PatientEHRSerializer("mimic_iii_subject_24263.db", "./../api_keys.json")
    # serialized_patient_ehr = processor.process_patient()

    # json_save_path = os.path.join("./", "mimic_iii_subject_24263.json")

    # with open(json_save_path, "w") as f:
    #     json.dump(serialized_patient_ehr, f, indent=4)