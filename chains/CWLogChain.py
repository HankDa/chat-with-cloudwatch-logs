import boto3
import json
from langchain.output_parsers import StructuredOutputParser, ResponseSchema, PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional

class Instruction(BaseModel):
    instruction: str
    tool: str
    fetch_log_instruction: str
    investigate_log_instruction: str

class Instructions(BaseModel):
    question: str
    instructions: List[Instruction]

class CWLogChain:

    def __init__(self, llm):
        session = boto3.Session(profile_name='EKSLogAccess')
        self.cloudwatch_logs = session.client('logs')
        self.llm = llm

    def general_guidence(self, question):

        output_parser = PydanticOutputParser(pydantic_object=Instructions)
        format_instructions = output_parser.get_format_instructions()

        PROMPT_TEMPLATE = """

        Provide investigated instructions for the given USER INPUT. 
        
        Provide at least one instruction use cloudwatch log.

        Provide detailed step-by-step instructions for investigating the given USER INPUT, including:
            "instruction": "A concise instruction on how to investigate the issue, using Amazon CloudWatch Logs or other tools",
            "tool": "The AWS service to use for the investigation (either 'aws cloudwatch' or 'aws cloudtrail')",
            "fetch_log_instruction": "Detailed steps on how to fetch the relevant log information from Amazon CloudWatch",
            "investigate_log_instruction": "Detailed steps on how to analyze the fetched log information to investigate the issue"


        % USER INPUT: {user_input}
                
        {format_instructions}

        """
        prompt = PromptTemplate(
            input_variables=["user_input"],
            partial_variables={"format_instructions": format_instructions},
            template=PROMPT_TEMPLATE
        )

        promptValue = prompt.format(user_input=question)
        print(promptValue)
        response = self.llm(promptValue)
        # TODO: what is the output type of output_parser? 
        parsed_response = json.loads(output_parser.parse(response).model_dump_json())
        
        return parsed_response


    def generate_query_string(self, question):
        """
        Generate a query string based on the prompt
        """

        response_schemas = [
            ResponseSchema(name="question", description="put user's prompt here"),
            ResponseSchema(name="queryString", description="put cloudwatch insight query string here"),
        ]

        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        # Template for the prompt
        PROMPT_TEMPLATE = """

        Provide cloudwatch insight query string for the given USER INPUT.

        % USER INPUT: {user_input}

        The query should:
        - Generate a CloudWatch Logs Insights query
        - Filter the logs to only include messages based on PROMPT_TEXT.
        - the query must start with "fields"
        - Sort the results in descending order by timestamp


        The response should follow below format:

        {format_instructions}
       
        """

        prompt = PromptTemplate(
            input_variables=["user_input"],
            partial_variables={"format_instructions": format_instructions},
            template=PROMPT_TEMPLATE
        )
        # Generate the query string
        promptValue = prompt.format(user_input=question)
        print(promptValue)
        response = self.llm(promptValue)
        parsed_response = output_parser.parse(response)
        return parsed_response


    def query_cloudwatch_logs(self, log_group_name, query_string, start_time, end_time):
        """
        Query CloudWatch logs using the provided query string
        """
        # Construct the query
        cw_logs_query = f"""{query_string}"""
        
        print("query_cloudwatch_logs", log_group_name, start_time, end_time, cw_logs_query)

        response = self.cloudwatch_logs.start_query(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=cw_logs_query,
        )

        # Get the query ID
        query_id = response['queryId']

        # Wait for the query to complete
        while True:
            query_status = self.cloudwatch_logs.get_query_results(queryId=query_id)
            if query_status['status'] == 'Complete':
                break

        # Get the query results
        return query_status['results']
    
    def generate_cw_log_report(self, cw_logs, prompt):
        # Convert the log entries to JSON strings (it was JSON format)
        cw_logs_string = json.dumps(cw_logs)

        # TODO: read from upload file? based on services to change template
        PROMPT_TEMPLATE = """
        {prompt}

        Log entry:
        {log_entry}

        The response should follow below format:

        - Log message: 
            put original log message here

        - Explanation: 
            explain the log entry in detail

        - Solution: 
            provide a solution to the log entry to fix the issue if needed

        - Timestamps: 
            list related log with request IDs

        Avoid duplicate explanations and solutions, if there are multiple similar log list the Timestamps.

        if there are different log messages, use above format to list them.

        Please provide response base on prompt for the given log entry.
        """

        response = self.llm(PROMPT_TEMPLATE.format(log_entry=cw_logs_string, 
                                                   prompt=prompt))

        return response
