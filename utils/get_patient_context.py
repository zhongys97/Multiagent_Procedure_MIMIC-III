

def get_patient_context_per_admission(patient_ehr, admission_idx):
    gender = patient_ehr["gender"]
    dob = patient_ehr["dob"]
    admissions = patient_ehr["admissions"]

    assert admission_idx < len(admissions), f"Admission index {admission_idx} out of range for patient with {len(admissions)} admissions."
    admission = admissions[admission_idx]
    i = admission_idx
    
    age_at_admission = admission["age_at_admission"]
    admission_time = admission["admission_time"]
    insurance_type = admission["insurance"]

    ground_truth_procedures_icd9 = admission["procedures_icd9"]
    ground_truth_procedures_text = admission["procedures_text"]

    if len(ground_truth_procedures_icd9) == 0:
        # print(f"No ground truth procedures for admission {i}. Skipping.")
        return {"skip": True,
                "context": None,
                "ground_truth_procedures_icd9": None,
                "ground_truth_procedures_text": None
            }

    summary_prev_admissions = ""
    if i > 0:
        for j in range(i):
            prev_admission = admissions[j]
            prev_admission_admission_time = prev_admission["admission_time"]
            prev_admission_discharge_time = prev_admission["discharge_time"]
            summary_prev_admissions += f"Admission from {prev_admission_admission_time} to {prev_admission_discharge_time}: {prev_admission['ehr_summary']}\n"

    windowed_current_admission_ehr = admission["windowed_current_admission_ehr"]

    
    ground_truth_procedures_icd9 = admission["procedures_icd9"]
    ground_truth_procedures_text = admission["procedures_text"]


    patient_context = f"""
    Patient Information:
    - Gender: {gender}
    - Date of Birth: {dob}
    - Age at Admission: {age_at_admission}
    - Admission Time: {admission_time}
    - Previous Admissions:
    {summary_prev_admissions}
    """

    return {
        "skip": False,
        "context": patient_context,
        "age_at_admission": age_at_admission,
        "insurance_type": insurance_type,
        "ground_truth_procedures_icd9": ground_truth_procedures_icd9,
        "ground_truth_procedures_text": ground_truth_procedures_text,
        "windowed_ehr_list": windowed_current_admission_ehr, #list
        }
