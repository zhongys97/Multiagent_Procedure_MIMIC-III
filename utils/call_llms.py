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
        model = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = model.responses.create(
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
    
    elif model_name == "gpt-4o-mini":
        model = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = model.responses.create(
                    model="gpt-4o-mini",
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
    
    elif model_name == "gpt-4.1-nano":
        model = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = model.responses.create(
                    model="gpt-4.1-nano",
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
    elif model_name == "claude-3":
        model = model_info["model_instance"]
        for attempt in range(5):
            try:
                response = model.messages.create(
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
                
    elif model_name == "qwen2":
        import torch
        model = model_info["model_instance"]
        tokenizer = model_info["tokenizer_instance"]

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            input_ids = tokenizer(prompt + " Answer:", return_tensors="pt").input_ids.to(device)

            num_tokens = input_ids.shape[-1]
            if num_tokens > 30000:
                print(f"Input token number ({num_tokens} close to the context length)")

            with torch.no_grad():
                output_ids = model.generate(
                    input_ids=input_ids,
                    max_new_tokens=3000,
                    pad_token_id=tokenizer.eos_token_id,  # suppress warning
                )

            # Only decode the newly generated tokens
            generated_only = output_ids[0][input_ids.shape[-1]:]  # slice off prompt tokens
            response = tokenizer.decode(generated_only, skip_special_tokens=True)
            return response.strip()
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
    elif model_name == "medgemma":
        import torch
        torch.set_float32_matmul_precision('high')

        model = model_info["model_instance"]
        tokenizer = model_info["tokenizer_instance"]

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful medical assistant."
                },
                {
                    "role": "user",
                    "content": "Avoid preamble when answering the question" + "context: " + prompt + "\nAnswer: \n"
                }
            ]

            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(model.device)

            input_len = inputs["input_ids"].shape[-1]

            with torch.inference_mode():
                generation = model.generate(**inputs,
                                            max_new_tokens=2000,
                                            do_sample=True,
                                            top_p=1.0,
                                            top_k=50,
                                            temperature=0.5)
                generation = generation[0][input_len:]

            decoded = tokenizer.decode(generation, skip_special_tokens=True)
            return decoded.strip()
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
        
    elif model_name == "OpenBioLLM":

        model = model_info["model_instance"]
        tokenizer = model_info["tokenizer_instance"]

        try:
            # Tokenize input
            inputs = tokenizer(prompt + " Answer:\n", return_tensors="pt").to(model.device)
            input_len = inputs["input_ids"].shape[1]

            # Generate output
            outputs = model.generate(
                **inputs,
                max_new_tokens=2000,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

            # Slice to exclude the prompt tokens
            generated_tokens = outputs[0][input_len:]

            # Decode only the generated part
            response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

    else:
        raise ValueError(f"Unsupported model: {model_name}.")
