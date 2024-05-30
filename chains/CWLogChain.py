import boto3
import json


class CWLogChain:

    def __init__(self, llm):
        session = boto3.Session(profile_name='EKSLogAccess')
        self.cloudwatch_logs = session.client('logs')
        self.llm = llm

    def generate_query_string(self, prompt):
        """
        Generate a query string based on the prompt
        """
        # Template for the prompt
        PROMPT_TEMPLATE = """
        PROMPT_TEXT : {prompt}

        The query should:
        - Generate a CloudWatch Logs Insights query
        - Filter the logs to only include messages based on PROMPT_TEXT.
        - the query must start with "fields"
        - Sort the results in descending order by timestamp


        The response should follow below format:

        Query string: put your response here
        extra note: put your extra note here(option prefer not to include)
       
        """
        
        # Generate the query string
        response = self.llm(PROMPT_TEMPLATE.format(prompt=prompt))
        # Split the response into lines
        query_lines = response.split("\n")
        # Filter out lines that start with "fields" or "|"
        query = " ".join([line for line in query_lines if line.startswith("fields") or line.startswith("|")])
        # Check if the query string is empty
        if not query:
            raise ValueError("Unable to extract query string from response, try more precise prompt")
        return query

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

        Please provide the explanation and solution for the given log entry.
        """

        response = self.llm(PROMPT_TEMPLATE.format(log_entry=cw_logs_string, 
                                                   prompt=prompt))

        return response
