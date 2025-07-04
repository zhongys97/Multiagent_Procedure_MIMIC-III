from openai import OpenAI
import os
import json
import time
import anthropic


with open("./api_keys.json", "r") as f:
    os.environ["OPENAI_API_KEY"] = json.load(f)["openai_api_key"]


def get_response(prompt: str, model_info: dict):

    model_name = model_info["model_name"]

    if model_name == "gpt-4o":
        agent = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = agent.responses.create(
                    model="gpt-4o",
                    input=prompt
                )
                return response.output_text.strip()

            except Exception as e:
                if "rate limit" in str(e).lower():
                    print(f"[Attempt {attempt + 1}] Rate limit hit. Retrying in 30 seconds...")
                    time.sleep(30)
                else:
                    print(f"[Attempt {attempt + 1}] Unhandled error: {repr(e)}")
                    return ""

        print("Exceeded maximum retry attempts for GPT-4o.")
        return ""
    
    elif model_name == "gpt-4.1-mini":
        agent = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = agent.responses.create(
                    model="gpt-4.1-mini-2025-04-14",
                    input=prompt
                )
                return response.output_text.strip()

            except Exception as e:
                if "rate limit" in str(e).lower():
                    print(f"[Attempt {attempt + 1}] Rate limit hit. Retrying in 30 seconds...")
                    time.sleep(30)
                else:
                    print(f"[Attempt {attempt + 1}] Unhandled error: {repr(e)}")
                    return ""

        print("Exceeded maximum retry attempts for GPT-4.1 mini.")
        return ""
    
    elif model_name == "medllama":
        agent = model_info["model_instance"]
        tokenizer = model_info["tokenizer_instance"]

        try:
            # Tokenize the input prompt
            inputs = tokenizer(prompt, return_tensors="pt").to(agent.device)

            # Generate output
            outputs = agent.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.6,
                top_p=0.9,
                do_sample=True,
                eos_token_id=[
                    tokenizer.eos_token_id,
                    tokenizer.convert_tokens_to_ids("<|eot_id|>")  # Optional if model uses this
                ]
            )
            input_length = inputs["input_ids"].shape[1]
            generated_tokens = outputs[0][input_length:]
            # Decode and print the result
            generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            return generated_text
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
        
    elif model_name == "claude-3":
        agent = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = agent.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                if response.content:
                    return response.content[0].text.strip()
                else:
                    print("Empty Claude response.")
                    return ""
            except anthropic.RateLimitError as e:
                print("Rate limited. Retrying...")
                time.sleep(10)

            except anthropic.APIStatusError as e:
                if "Overloaded" in str(e):
                    print("Claude overloaded. Retrying in 15s...")
                    time.sleep(15)
                else:
                    print(f"An error occurred: {repr(e)}")
                    return ""
    
    else:
        raise ValueError(f"Unsupported model: {model_name}.")
