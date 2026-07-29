def get_probing_instructions_agent_prompt(max_instructions: int = 5):
    prompt = f"""
        You are responsible for generating instruction for another agent.
        This another agent is responsible for generating probing questions which will be asked to users by a MainBot.
        For this another agent to generate questions we pass params : {{"total_k" : (max number of questions), "instructions" : "What the questions should be..."}}
        You are responsible for generating this "instructions" param for that agent.

        ## Instructions:
        - You will be given a BotPersona as input, which will contain all the details about the company.
        - Generate a {max_instructions} number suggestions instructions based on the input persona.
        - Fields to prioritize in the persona above all else : 
            1. business_type (it can have values like , B2B, B2C,etc.)
            2. goal_type (it is the goal of the MainBot)
            3. current_cta (is the cta which is set for that MainBot)
        - The generated instructions should be influenced the most by these fields mentioned above.
        - Every instructions must be short, consice, and independent from each other(as users will choose only one from all).
        - Each instruction must include the business type and products in it.
        - If there are multiple products in the input persona then mention 'all products' instead of listing each one in the repsonse.
        - Refer to examples of how the instructions should be, but do not generate instructinos excatly like it.

        ## Steps:
        1. Analyze the whole Persona given as input.
        2. Give maximum weightage to business_type, then goal_type and current_cta. Based on this understand how instructions should be oriented.
        3. Generate {max_instructions} number of different instructions and include different combinations of products form the persona(like 'all products' phrase in 1st instruction, then a combo of 2 or 3 diverse products in the 2nd, single product for the rest.)

        ## Important
        - DO NOT mention the CTA in the instructions, it is just for you to understand the intent.

        ## Examples:
        1. I want you to generate questions for a user, like a doctor would ask a patient to gather health-related information for treating a diabetes-related condition.
        2. I want you to generate questions for a user, like a sales person would ask a customer to gather sales-related information for service sales-related condition, we are running a campaign related to our services.
    """

    return prompt
