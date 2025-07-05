

def retain_most_recent_info(item_for_prompt, retain_last_fraction: float, retain_last_num_items: int = float("inf")):

    if retain_last_fraction == 1:
        return str(item_for_prompt)

    if isinstance(item_for_prompt, list) or isinstance(item_for_prompt, str):
        length = len(item_for_prompt)
        start_idx = max(length - retain_last_num_items, int(length * (1 - retain_last_fraction)))
        return str(item_for_prompt[start_idx:])
    
    elif isinstance(item_for_prompt, int) or isinstance(item_for_prompt, float):
        return str(item_for_prompt)
    
    elif isinstance(item_for_prompt, dict):
        for k, v in item_for_prompt.items():
            item_for_prompt[k] = retain_most_recent_info(v, retain_last_fraction, retain_last_num_items)
        return str(item_for_prompt)
    else:
        return ""
    

if __name__ == "__main__":

    pass