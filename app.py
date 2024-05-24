import streamlit as st
import json

from langchain_aws import BedrockLLM
from datetime import datetime, timedelta
from chains.CWLogChain import CWLogChain

llm = BedrockLLM(
        credentials_profile_name="default",
        model_id="amazon.titan-text-premier-v1:0")

log_chain = CWLogChain(llm=llm, log_group="test")

cw_logs = log_chain.run(
    log_group_name="/aws/lambda/500Error", 
    start_time=datetime.now() - timedelta(days=7), 
    end_time=datetime.now(), 
    prompt="Generate a CloudWatch Logs Insights query to get most recent 100 Error logs.")

cw_logs_string = json.dumps(cw_logs['logs'])

PROMPT_TEMPLATE = """
Analyze the CloudWatch log entry and provide an explanation and solution.

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

response = llm(PROMPT_TEMPLATE.format(log_entry=cw_logs_string))

print(response)