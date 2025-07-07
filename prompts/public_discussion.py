

expert_without_query_consensus = """
        You are an expert in {}.
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts:
            {}
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to reach a consensus on the best procedure sequence.
        It is now in round {} of the discussion, decisions are prefereably made by round {}
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.
        
        Response consists of:
        1. Your reasoning (without reiterating every details)
        2. Your proposed sequence of procedures (with proper ordering) in ICD9 codes according to the mapping, as a list of strings
        3. Your proposed sequence of procedures (with proper ordering) as text description according to the mapping, as a list of strings
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a serialized JSON with the following keys, explcicitly include the curly braces, double quotes, and colons:
         "Reasoning": <your reasoning here up to 250 words>,
         "Proposed ICD9": <your proposed procedures in ICD9 codes here>,
         "Proposed Text": <your proposed procedures as text description here>,
         "Confidence": <your confidence score here>

        """                

expert_with_query_consensus = """
        You are an expert in {}.
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts:
            {}
        You query the literature and have the following finding:
            {}
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to reach a consensus on the best procedure sequence.
        It is now in round {} of the discussion, decisions are prefereably made by round {}
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.
        
        Response consists of:
        1. Your reasoning
        2. Your proposed sequence of procedures (with proper ordering) in ICD9 codes according to the mapping, as a list of strings
        3. Your proposed sequence of procedures (with proper ordering) as text description according to the mapping, as a list of strings
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a serialized JSON with the following keys, explcicitly include the curly braces, double quotes, and colons:
         "Reasoning": <your reasoning here up to 250 words>,
         "Proposed ICD9": <your proposed procedures in ICD9 codes here>,
         "Proposed Text": <your proposed procedures as text description here>,
         "Confidence": <your confidence score here>

        """       


expert_without_query_leader = """
        You are an expert in {}.
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts and a team lead:
            {}
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to convince the team lead on the best procedure sequence.
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.
        
        Response consists of:
        1. Your concise reasoning up to 250 words (without reiterating every detail)
        2. Your proposed sequence of procedures (with proper ordering) in ICD9 codes according to the mapping, as a list of strings
        3. Your proposed sequence of procedures (with proper ordering) as text description according to the mapping, as a list of strings
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a serialized JSON with the following keys, explcicitly include the curly braces, double quotes, and colons:
         "Reasoning": <your reasoning here>,
         "Proposed ICD9": <your proposed procedures in ICD9 codes here>,
         "Proposed Text": <your proposed procedures as text description here>,
         "Confidence": <your confidence score here>
         
        """                

expert_with_query_leader = """
        You are an expert in {}.
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        and the following discussions of a few experts and a team lead:
            {}
        You query the literature and have the following finding:
            {}
        Please contribute to propose the best procedure for this patient.
        You may agree or disagree with the previous experts' opinions, and in this case explicitly respond to them.
        The final goal is to convince the team lead on the best procedure sequence.
        Despite that, to ensure diversified opinions, disagreements at initial stages are encouraged.

        Response consists of:
        1. Your reasoning
        2. Your proposed sequence of procedures (with proper ordering) in ICD9 codes according to the mapping, as a list of strings
        3. Your proposed sequence of procedures (with proper ordering) as text description according to the mapping, as a list of strings
        4. The confidence to your proposal from 0 to 10, where 0 means not confident at all, and 10 means highly confident.
        
        Format your response as a serialized JSON with the following keys, explcicitly include the curly braces, double quotes, and colons:
         "Reasoning": <your reasoning here up to 250 words>,
         "Proposed ICD9": <your proposed procedures in ICD9 codes here>,
         "Proposed Text": <your proposed procedures as text description here>,
         "Confidence": <your confidence score here>
         
        """

team_lead_decision = """
        You are leading discussion among a team of medical experts in deciding the best sequence of procedure for a patient.
        Given the following procedure text to ICD mapping:
            {}
        With this patient:
            {}
        Previous discussions are as follows:
            {}
        Think carefully about the previous experts' opinions, and decide whether to agree or disagree with them.
        You are expected to make the decision at round {} of the discussion. You are now at round {}.
        Rushing the decision at the initial rounds is discouraged.

        Response consists of:
        1. Your reasoning
        2. Whether the final decision is made ("true" or "false")
        3. Your decided sequence of procedure (with proper ordering) in ICD9 codes according to the mapping, as a list of strings
        4. Your decided sequence of procedure (with proper ordering) as text description according to the mapping, as a list of strings
        5. The confidence of your decision.
        
        Format your response as a serialized JSON with the following keys, explcicitly include the curly braces, double quotes, and colons:
         "Reasoning": <your reasoning here up to 250 words>,
         "Decision Made": <"true" or "false">,
         "Decided ICD9": <your proposed procedures in ICD9 codes here>,
         "Decided Text": <your proposed procedures as text description here>,
         "Confidence": <your confidence score here>

        """