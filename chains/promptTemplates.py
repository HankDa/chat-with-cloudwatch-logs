PROMPT_TEMPLATE_GENERAL_GUIDENCE = """

Provide investigated instructions for the given USER INPUT. 

The instructions should be:
- at least one instruction use cloudwatch log.
- provide log filter base on USER INPUT.

Provide detailed instructions for investigating the given USER INPUT, including:
"instruction": "A concise explaintion of the issue and a set of instructions on how to investigate the issue, using Amazon CloudWatch Logs or other tools",
"tool": "The AWS service to use for the investigation (either 'aws cloudwatch' or 'aws cloudtrail')",
"fetch_log_instruction": "Detailed steps on how to fetch the relevant log or information",
"investigate_log_instruction": "Detailed steps on how to analyze the fetched log information to investigate the issue"


% USER INPUT: {user_input}
    
{format_instructions}
"""