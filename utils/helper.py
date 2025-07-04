import json
import time


def format_discussion_response(response):
    """
    Format the response from the agent into a structured dictionary.
    """
    begin_idx = response.find("{")
    end_idx = response.rfind("}") + 1
    if begin_idx == -1 or end_idx == -1:
        return {"Reasoning": response, "Proposed ICD9": "", "Proposed Text": "", "Confidence": 0}
    response_text = response[begin_idx:end_idx]
    try:
        response_dict = json.loads(response_text)
        return {
            "Reasoning": response_dict.get("Reasoning", ""),
            "Proposed ICD9": response_dict.get("Proposed ICD9", ""),
            "Proposed Text": response_dict.get("Proposed Text", ""),
            "Confidence": response_dict.get("Confidence", 0)
        }
    except json.JSONDecodeError:
        return {
            "Reasoning": "Invalid response format",
            "Proposed ICD9": "",
            "Proposed Text": "",
            "Confidence": 0
        }
    

def format_leader_response(response):
    """
    Format the response from the leader agent into a structured dictionary.
    """
    begin_idx = response.find("{")
    end_idx = response.rfind("}") + 1
    if begin_idx == -1 or end_idx == -1:
        return {"Reasoning": response, "Decision Made": False, "Decided ICD9": "", "Decided Text": "", "Confidence": 0}
    response_text = response[begin_idx:end_idx]
    try:
        response_dict = json.loads(response_text)
        return {
            "Reasoning": response_dict.get("Reasoning", ""),
            "Decision Made": response_dict.get("Decision Made", False),
            "Decided ICD9": response_dict.get("Decided ICD9", ""),
            "Decided Text": response_dict.get("Decided Text", ""),
            "Confidence": response_dict.get("Confidence", 0)
        }
    except json.JSONDecodeError:
        return {
            "Reasoning": "Invalid response format",
            "Decision Made": False,
            "Decided ICD9": "",
            "Decided Text": "",
            "Confidence": 0
        }

def format_rag_response(response):
    """
    Format the response from the agent into a structured dictionary.
    """
    begin_idx = response.find("{")
    end_idx = response.rfind("}") + 1
    if begin_idx == -1 or end_idx == -1:
        return {"Answer": response, "Relevance": 0}
    response_text = response[begin_idx:end_idx]
    try:
        response_dict = json.loads(response_text)
        return {
            "Answer": response_dict.get("Answer", ""),
            "Relevance": response_dict.get("Relevance", 0)
        }
    except json.JSONDecodeError:
        return {
            "Answer": "Invalid response format",
            "Relevance": 0
        }