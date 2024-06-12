import streamlit as st
from langchain_aws import BedrockLLM
from datetime import datetime
from chains.CWLogChain import CWLogChain

llm = BedrockLLM(
        credentials_profile_name="default",
        model_id="amazon.titan-text-premier-v1:0")

log_chain = CWLogChain(llm=llm)


def main():
    st.title("CloudWatch Logs Analysis")

    if "general_question_response" not in st.session_state:
        st.session_state["general_question_response"] = None  
    if "queryString" not in st.session_state:
        st.session_state["queryString"] = None   
    if "cw_logs" not in st.session_state:
        st.session_state["cw_logs"] = None   

    general_guidence_prompt = st.text_input("asking your question here")
    
    if st.button("Generate General Guidence"):
        with st.spinner("Processing"):
            try:
                general_guidence_response = log_chain.general_guidence(general_guidence_prompt)
                st.session_state['general_question_response'] = general_guidence_response
            except Exception as e:
                st.write(e)
    
    if st.session_state['general_question_response']:
        st.write(st.session_state['general_question_response'])
        prompt = st.text_input("Enter prompt to generate CloudWatch log insight query",
                               value=st.session_state['general_question_response'])
        if st.button("Generate Query String"):
            with st.spinner("Processing"):
                try: 
                    response = log_chain.generate_query_string(question=prompt)
                    st.write(response)
                    st.session_state['queryString'] = response['queryString']
                except Exception as e:
                    st.write(e)
            
    if st.session_state['queryString']:
        query_string = st.text_input("Enter query string", 
                                     value=st.session_state['queryString'])
        st.session_state['queryString'] = query_string
        log_group_name = st.text_input("Enter log group name")
        start_date = st.text_input("Enter start date (YYYY-MM-DD)")
        end_date = st.text_input("Enter end date (YYYY-MM-DD)")

        if st.button("Get Logs"):
            with st.spinner("Processing"):
                # TODO: need validate query string
                cw_logs = log_chain.query_cloudwatch_logs(
                    log_group_name=log_group_name,
                    query_string=st.session_state['queryString'],
                    start_time=datetime.strptime(start_date, "%Y-%m-%d"),
                    end_time=datetime.strptime(end_date, "%Y-%m-%d"),
                    )
                st.session_state['cw_logs'] = cw_logs

    if st.session_state['cw_logs']:
        st.write(st.session_state['cw_logs'])
        # TODO: allow user modify query string
        prompt = st.text_input("Enter prompt to ask what you interested about the log")
        if st.button("Generate Report"):
            with st.spinner("Processing"):
                response = log_chain.generate_cw_log_report(st.session_state['cw_logs'],
                                                            prompt)

                st.write(response)
    
    if st.button("Clear"):
        st.session_state['queryString'] = None
        st.session_state['cw_logs'] = None
    


if __name__ == "__main__":
    main()