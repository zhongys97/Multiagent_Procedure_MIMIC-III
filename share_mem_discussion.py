
import os
import json
from openai import OpenAI
import time
import random
from utils.setup import setup_agents, procedure_text_to_icd
from utils.helper import get_response, format_discussion_response
from prompts.public_discussion import expert_without_query
from utils.get_patient_context import get_patient_context_per_admission


NUM_ROUNDS = 1  # Define the number of rounds for the discussion
END_CONDITION = "consensus" # "consensus" or "leader"
QUERY_LITERATURE = False


agents = setup_agents(internal_memory=QUERY_LITERATURE)

def run_by_subject_json(patient_ehr_json_path):
    """
    Run the multi-agent discussion for a given subject's EHR data.
    """

    # load patient ehr from json
    patient_name = os.path.basename(patient_ehr_json_path).replace(".db.json", "")

    with open(patient_ehr_json_path, "r") as f:
        patient_ehr = json.load(f)

    gender = patient_ehr["gender"]
    dob = patient_ehr["dob"]
    admissions = patient_ehr["admissions"]

    for i, admission in enumerate(admissions):
        
        admission_info = get_patient_context_per_admission(patient_ehr, i)

        if admission_info["skip"]:
            continue
        else:
            patient_context = admission_info["context"]
            ground_truth_procedures_icd9 = admission_info["ground_truth_procedures_icd9"]
            ground_truth_procedures_text = admission_info["ground_truth_procedures_text"]

        shared_memory = {
            "procedure_text_to_icd": procedure_text_to_icd,
            "patient_context": patient_context,
            "discussion": []
        }

        for round in range(NUM_ROUNDS):
            print("=" * 40)
            print(f"Round {round + 1} Discussion:\n")
            proposed_procedures_icd9_str = set() # hash with str
            
            list_proposed_procedures_icd9_str = []
            list_proposed_procedures_text_str = []

            agents_key_list = list(agents.keys())

            # randomly shuffle the agents for each round
            random.shuffle(agents_key_list)
            for chapter_idx in agents_key_list:
                agent_info = agents[chapter_idx]
                # print(f"Agent: {agent_info['expert_name']} (Domain: {agent_info['expert_domain_str']})")
                expert_domain_str = agent_info["expert_domain_str"]
                expert_name = agent_info["expert_name"]
                agent = agent_info["agent"]

                if not QUERY_LITERATURE and END_CONDITION == "consensus":
                    prompt = expert_without_query.format(
                        shared_memory['procedure_text_to_icd'],
                        shared_memory["patient_context"],
                        shared_memory['discussion'],
                        expert_domain_str
                    )

                response_text = get_response(agent, prompt)

                formatted_response = format_discussion_response(response_text)

                if len(formatted_response["Proposed ICD9"]) > 0:
                    proposed_procedures_icd9_str.add(str(formatted_response["Proposed ICD9"]))
                    list_proposed_procedures_icd9_str.append(str(formatted_response["Proposed ICD9"]))
                    list_proposed_procedures_text_str.append(str(formatted_response["Proposed Text"]))

                shared_memory["discussion"].append({
                    "round_idx": round,
                    "expert_idx": agent_info["expert_idx"],
                    "expert": expert_name,
                    "response": formatted_response
                })

            # decide consensus based on proposed procedures
            if len(proposed_procedures_icd9_str) == 0:
                print("No procedures proposed in this round. Ending discussion.")
                shared_memory["discussion"].append({
                    "round_idx": round,
                    "role": "system",
                    "number_of_proposed_sequences": len(proposed_procedures_icd9_str),
                    "consensus": True,
                    "content": "No procedures proposed in this round. Ending discussion.",
                    "proposed_procedures_icd9": [],
                    "proposed_procedures_text": []})
                break

            elif len(proposed_procedures_icd9_str) == 1:
                print("Consensus reached on the proposed procedures sequence.")
                shared_memory["discussion"].append({
                    "round_idx": round,
                    "role": "system",
                    "number_of_proposed_sequences": len(proposed_procedures_icd9_str),
                    "consensus": True,
                    "content": f"Consensus reached on the proposed procedures sequence. Proposed procedure sequences: {', '.join(list_proposed_procedures_text_str)}",
                    "proposed_procedures_icd9": list_proposed_procedures_icd9_str,
                    "proposed_procedures_text": list_proposed_procedures_text_str
                })
                break
            else:
                shared_memory["discussion"].append({
                    "round_idx": round,
                    "role": "system",
                    "number_of_proposed_sequences": len(proposed_procedures_icd9_str),
                    "consensus": False,
                    "content": f"Consensus not reached. Proposed procedure sequences: {', '.join(list_proposed_procedures_text_str)}",
                    "proposed_procedures_icd9": list_proposed_procedures_icd9_str,
                    "proposed_procedures_text": list_proposed_procedures_text_str
                })
            
        save_info = {
            "patient_name": patient_name,
            "admission_index": i,
            "end_condition": END_CONDITION,
            "query_literature": QUERY_LITERATURE,
            "ground_truth_procedures_icd9": ground_truth_procedures_icd9,
            "ground_truth_procedures_text": ground_truth_procedures_text,
            "final_discussion_results": shared_memory["discussion"][-1],  # Save the last round's discussion result
            "discussion": shared_memory["discussion"]
        }

        with open(f"{patient_name}_admission_{i}_discussion.json", "w") as f:
            json.dump(save_info, f, indent=4)
            

if __name__ == "__main__":
    run_by_subject_json("mimic_iii_subject_3097.db.json")