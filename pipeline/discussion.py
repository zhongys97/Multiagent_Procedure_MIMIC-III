import os
import json
import random
from prompts.public_discussion import (
    expert_without_query_consensus,
    expert_with_query_consensus,
    expert_without_query_leader,
    expert_with_query_leader,
    team_lead_decision,
)
from utils.helper import format_discussion_response, format_leader_response
from utils.call_llms import get_response
from utils.get_patient_context import get_patient_context_per_admission
from pipeline.update_private_memory import update_agent_private_thinking


def run_by_subject_json(config_run_dir: str,
                        patient_ehr_json_path: str,
                        agents: dict,
                        model_info: dict,
                        num_rounds: int,
                        end_condition: str,
                        query_literature: bool,
                        rag_data_dir: str,
                        procedure_text_to_icd: dict):
    """
    Run the multi-agent discussion for a given subject's EHR data.
    """

    # load patient ehr from json
    patient_name = os.path.basename(patient_ehr_json_path).replace(".db.json", "")

    with open(patient_ehr_json_path, "r") as f:
        patient_ehr = json.load(f)

    gender = patient_ehr["gender"]
    dob = patient_ehr["dob"]
    ethnicity = patient_ehr["ethnicity"]
    language = patient_ehr["language"]
    admissions = patient_ehr["admissions"]

    for i, admission in enumerate(admissions):

        discussion_save_path = os.path.join(config_run_dir, f"{patient_name}_admission_{i}_discussion.json")

        if os.path.exists(discussion_save_path):
            print(f"Discussion file {discussion_save_path} already exists. Skipping this admission.")
            return

        admission_info = get_patient_context_per_admission(patient_ehr, i)

        if admission_info["skip"]:
            continue
        else:
            patient_context = admission_info["context"]
            ground_truth_procedures_icd9 = admission_info["ground_truth_procedures_icd9"]
            ground_truth_procedures_text = admission_info["ground_truth_procedures_text"]
            age_at_admission = admission_info["age_at_admission"]
            insurance_type = admission_info["insurance_type"]

        shared_memory = {
            "procedure_text_to_icd": procedure_text_to_icd,
            "patient_context": patient_context,
            "discussion": []
        }

        for round in range(num_rounds):
            print("=" * 40)
            print(f"Round {round + 1} Discussion:\n")
            proposed_procedures_icd9_str = set() # hash with str
            
            list_proposed_procedures_icd9_str = []
            list_proposed_procedures_text_str = []

            agents_key_list = list(agents.keys())

            # randomly shuffle the agents for each round
            random.shuffle(agents_key_list)
            for chapter_idx in agents_key_list:
                print(f"Chapter Index: {chapter_idx}")
                agent_info = agents[chapter_idx]
                # print(f"Agent: {agent_info['expert_name']} (Domain: {agent_info['expert_domain_str']})")
                expert_domain_str = agent_info["expert_domain_str"]
                expert_name = agent_info["expert_name"]

                if not query_literature and end_condition == "consensus":
                    prompt = expert_without_query_consensus.format(
                        expert_domain_str,
                        shared_memory['procedure_text_to_icd'],
                        shared_memory["patient_context"],
                        shared_memory['discussion'],
                    )
                elif query_literature and end_condition == "consensus":

                    updated_private_memory = update_agent_private_thinking(
                        round,
                        chapter_idx,
                        shared_memory["patient_context"],
                        shared_memory["discussion"],
                        agent_info["memory"],
                        model_info,
                        rag_data_dir,
                    )

                    agent_info["memory"] = updated_private_memory

                    prompt = expert_with_query_consensus.format(
                        expert_domain_str,
                        shared_memory['procedure_text_to_icd'],
                        shared_memory["patient_context"],
                        shared_memory['discussion'],
                        agent_info["memory"][-1]["new_insight"],
                    )

                elif not query_literature and end_condition == "leader":

                    prompt = expert_without_query_leader.format(
                        expert_domain_str,
                        shared_memory['procedure_text_to_icd'],
                        shared_memory["patient_context"],
                        shared_memory['discussion'],
                    )
                elif query_literature and end_condition == "leader":

                    updated_private_memory = update_agent_private_thinking(
                        round,
                        chapter_idx,
                        shared_memory["patient_context"],
                        shared_memory["discussion"],
                        agent_info["memory"],
                        model_info,
                        rag_data_dir
                    )

                    agent_info["memory"] = updated_private_memory

                    prompt = expert_with_query_leader.format(
                        expert_domain_str,
                        shared_memory['procedure_text_to_icd'],
                        shared_memory["patient_context"],
                        shared_memory['discussion'],
                        agent_info["memory"][-1]["new_insight"]
                    )

                response_text = get_response(prompt, model_info)

                if response_text is None or response_text.strip() == "":
                    print(f"Empty response from {expert_name}. Skipping this agent.")
                    continue

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

            if end_condition == "consensus":
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
            else: # based on leader decision

                leader_prompt = team_lead_decision.format(
                    shared_memory['procedure_text_to_icd'],
                    shared_memory["patient_context"],
                    shared_memory['discussion'],
                )

                leader_response_text = get_response(leader_prompt, model_info)

                if response_text is None or response_text.strip() == "":
                    print(f"Empty response from the leader. Continue.")
                
                    shared_memory["discussion"].append({
                        "round_idx": round,
                        "role": "leader",
                        "number_of_proposed_sequences": 0,
                        "decision": False,
                        "content": "Leader not responding.",
                        "proposed_procedures_icd9": [],
                        "proposed_procedures_text": []
                    })
                    break
                else:
                    formatted_leader_response = format_leader_response(leader_response_text)

                    bool_decision_made = formatted_leader_response["Decision Made"]
                    reasoning = formatted_leader_response["Reasoning"]

                    if not bool_decision_made and len(reasoning) > 0:
                        print("Leader did not make a decision. Continuing discussion.")
                        shared_memory["discussion"].append({
                            "round_idx": round,
                            "role": "leader",
                            "number_of_proposed_sequences": 0,
                            "decision": False,
                            "content": reasoning,
                            "proposed_procedures_icd9": [],
                            "proposed_procedures_text": []
                        })
                    else:
                        print("Leader made a decision")
                        shared_memory["discussion"].append({
                            "round_idx": round,
                            "role": "leader",
                            "number_of_proposed_sequences": len(proposed_procedures_icd9_str),
                            "decision": True,
                            "content": reasoning,
                            "proposed_procedures_icd9": str(formatted_leader_response["Decided ICD9"]),
                            "proposed_procedures_text": str(formatted_leader_response["Decided Text"])
                        })
                        break
            
        save_info = {
            "patient_name": patient_name,
            "gender": gender,
            "ethnicity": ethnicity,
            "language": language,
            "admission_index": i,
            "end_condition": end_condition,
            "query_literature": query_literature,
            "age_at_admission": age_at_admission,
            "insurance_type": insurance_type,
            "ground_truth_procedures_icd9": ground_truth_procedures_icd9,
            "ground_truth_procedures_text": ground_truth_procedures_text,
            "num_rounds": round + 1,  # Save the number of rounds completed
            "final_discussion_results": shared_memory["discussion"][-1],  # Save the last round's discussion result
            "discussion": shared_memory["discussion"]
        }

        with open(discussion_save_path, "w") as f:
            json.dump(save_info, f, indent=4)

        if query_literature:
            # save agents' memory
            for chapter_idx in agents_key_list:
                agent_info = agents[chapter_idx]
                agent_memory_save_path = os.path.join(config_run_dir, f"{patient_name}_admission_{i}_agent_{agent_info['expert_idx']}_memory.json")
                with open(agent_memory_save_path, "w") as f:
                    json.dump(agent_info["memory"], f, indent=4)
            
