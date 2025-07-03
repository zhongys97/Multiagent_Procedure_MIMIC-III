import json
import time

def get_response(agent, prompt):
    try:
        response = agent.responses.create(
                model="gpt-4o",
                input=prompt
            )
    except Exception as e:
        if "Rate limit" in str(e):
            print("Rate limit exceeded. Waiting for 60 seconds...")
            time.sleep(30)

            response = agent.responses.create(
                model="gpt-4o",
                input=prompt,
                temperature=0.5
            )
        else:
            # print(f"An error occurred: {e}")
            return ""
    return response.output_text


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