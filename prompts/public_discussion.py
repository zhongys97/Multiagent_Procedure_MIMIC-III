

expert_without_query_consensus = """
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts:
            {}
        You are an expert in {}.
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to reach a consensus on the best procedure sequence.
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.
        
        Response consists of:
        1. Your reasoning
        2. Your proposed a sequence of procedure (with proper ordering) in ICD9 codes according to the mapping
        3. Your proposed a sequence of procedure (with proper ordering) as text description according to the mapping
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a dictionary with the following keys:
        Reasoning: <your reasoning here>
        Proposed ICD9: <your proposed procedure in ICD9 codes here>
        Proposed Text: <your proposed procedure as text description here>
        Confidence: <your confidence score here>

        """                

expert_with_query_consensus = """
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts:
            {}
        You are an expert in {}.
        You query the literature and have the following finding:
            {}
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to reach a consensus on the best procedure sequence.
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.

        Response consists of:
        1. Your reasoning
        2. Your proposed a sequence of procedure (with proper ordering) in ICD9 codes according to the mapping
        3. Your proposed a sequence of procedure (with proper ordering) as text description according to the mapping
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a dictionary with the following keys:
        Reasoning: <your reasoning here>
        Proposed ICD9: <your proposed procedure in ICD9 codes here>
        Proposed Text: <your proposed procedure as text description here>
        Confidence: <your confidence score here>

        """       