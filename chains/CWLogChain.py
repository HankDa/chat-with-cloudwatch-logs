import boto3


class CWLogChain:

    def __init__(self, llm, log_group):
        self.cloudwatch_logs = boto3.client('logs')
        self.llm = llm

    def generate_query_string(self, prompt):
        PROMPT_TEMPLATE = """
        {prompt}

        The query should:
        - Filter the logs to only include messages with the keyword in question
        - Sort the results in descending order by timestamp
        - The generated query string should be used for cloudwatch console.


        The response should follow below format:

        Query string: put your response here
        extra note: put your extra note here(option prefer not to include)
       
        """

        response = self.llm(PROMPT_TEMPLATE.format(prompt=prompt))

        query_lines = response.split("\n")
    
        query = " ".join([line for line in query_lines if line.startswith("fields") or line.startswith("|")])
    
        if not query:
            raise ValueError("Unable to extract query string from response, try more precise prompt")
    
        return query

    def query_cloudwatch_logs(self, log_group_name, query_string, start_time, end_time):
        
        cw_logs_query = f"""{query_string}"""
        
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
     
    def run(self, log_group_name, start_time, end_time, prompt):
        query_string = self.generate_query_string(prompt)
        print(query_string)
        cw_logs = self.query_cloudwatch_logs(log_group_name, query_string, start_time, end_time)
        print(
            """
            Question: {0}
            
            Query string: {1}

            number of Log: {2}
            """.format(prompt, query_string, len(cw_logs))
)
        return {"Question":prompt, "query_string": query_string, "logs":cw_logs}
