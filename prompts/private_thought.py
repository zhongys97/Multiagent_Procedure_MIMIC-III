
raise_questions_for_rag = """
    With this patient:
        {}
    and the following discussions of a few experts:
        {}
    You are an expert in {}.
    You are in the middle of a goal to propose the best procedure for this patient.
    Please raise two questions that you think are important to look up in the literature given the patient data and previous discussions.
    The questions shall answer unaddressed aspects of previous discussions.
    The questions shall relate to some specific observations or findings from the patient data.
"""

rag_prompt = """
        You are an expert in {}.
        Use the following literature to answer the user's question.
        --- Relevant Literature ---
        {}
        --- Question ---
        {}
        --- Answer ---
        Please provide an accurate and detailed response based on the provided literature.
        You must cite the relevant literature in your answer, using (Source: <title of the source>) format.

        Besides your answer, please also provide a rating of the relevance of the literature to the question.
        For example, if the question is about typical blood pressure for pulmonary hypertension, but the literature is about mental disorders, you should report a low relevance.
        However, if the question is about the psychological aspect of pulmonary hypertension, you should report a slightly higher relevance.
        Finally, if the question is directly addressed by the literature, you should report a high relevance.
        The relevance score is an integer between 0 and 10, where 0 means not relevant at all, and 10 means highly relevant.
        
        Format your response as a dictionary with the following keys:
        Answer: <your answer here>
        Relevance: <score>
    """

reflect_on_rag_response = """
        You are an expert in {}.
        During previous literature search, you found the following information:
        {}
        With the new round of literature search, you have the following new findings:
        {}
        Please reflect on the new findings and how they relate to your previous understanding.
        You should also consider how these findings might change your previous conclusions or recommendations.
        Consider the relevance of the new finding when formulating your response.
        Relevance is an integer between 0 and 10, where 0 means not relevant at all, and 10 means highly relevant.
        
        Write a summary (up to 300 words) of your updated understanding.
        You must cite the relevant literature in your answer, using (Source: <title of the source>) format.
        """

