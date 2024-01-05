import os

import pandas as pd
from langchain.agents import AgentType, create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain_community.llms.ctransformers import CTransformers
from langchain_community.llms.openai import OpenAI
from langchain_community.chat_models import ChatOpenAI
# from langchain.agents import create_pandas_dataframe_agent
from langchain_experimental.agents.agent_toolkits import create_csv_agent, create_pandas_dataframe_agent

from dotenv import load_dotenv

load_dotenv()

project = os.environ.get("PROJECT") # "protected-00-349215"
dataset = os.environ.get("DATASET") # "interventions_output"
table = os.environ.get("TABLE") # "feed_prepared"
# service_account_file = os.environ.get("G_SERVICE_KEY")
# sqlalchemy_url = f'bigquery://{project}/{dataset}?credentials_path={service_account_file}'


# def data_test():
#     # file_path = '/Users/hopedion/Downloads/black_friday_sales/train.csv'
#     file_path = '/Users/hopedion/Downloads/loredatagpt_test2.csv'
#     df = pd.read_csv(file_path)
#     print(len(df))

if os.environ.get('ENVIRONMENT') == 'local':
    def load_llm():
        # Load the locally downloaded model here
        lm = CTransformers(
            model=os.environ.get('MODEL'),
            model_type="mistral",
            config={'context_length': 4028, 'max_new_tokens': 2028},
            # temperature=0,
            model_kwargs={"temperature": 0.1, "max_length": 512}
        )
        return lm
    llm = load_llm()
else:
    # Create an OpenAI object.
    # llm = OpenAI(temperature=0)
    llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview")


def get_dataframe(path_or_file):
    if type(path_or_file) == str:
        if path_or_file.endswith('.csv'):
            df = pd.read_csv(path_or_file)
        else:
            df = pd.read_excel(path_or_file)
        return df
    else:
        if path_or_file.content_type == 'text/csv':
            df = pd.read_csv(path_or_file)
        else:
            df = pd.read_excel(path_or_file)
        return df


def create_agent(filename):
    """
    Create an agent that can access and use a large language model (LLM).

    Args:
        filename: The path to the CSV file that contains the data.

    Returns:
        An agent that can access and use the LLM.
    """

    # Read the CSV file into a Pandas DataFrame.
    df = get_dataframe(filename)

    # Create a Pandas DataFrame agent.
    return create_pandas_dataframe_agent(
        llm, df, verbose=True, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors="Check your output and make sure it conforms! Do not output an action and a final answer at the same time."
    )


def query_agent(agent, query, msg=None):
    prompt = (
            f"""
                For the following query, you are to determine the best way to present the answer using the following:
                Answer the query and illustrate your answer with graph or plot.
                "answer": "answer to the query"
                
                Make sure to always use matplotlib in non-GUI mode.
                Generate graphs or plot to the "images/{msg.conversation.id}/{msg.id}" folder.
                
                Suggest 3 questions about the data. Include the 3 suggested question as a list in the response. for example:
                "question": ["how many rows are there", "how many columns are there", "what is this data about"]
               
                Example of the final output json. This is a combination of "answer", "questions" and "graphs":
                {{"answer": "The title with the highest rating is 'Gilead'", 
                "graphs": ["12354_bar.png", "e3422_line.png"], "questions": ["how many rows are there", "how manay columns are there', 'what is this data about"]}}
                   
                If you do not know the answer, reply as follows:
                {{"answer": "I do not know."}}
                                
                All strings in "questions" list and "graph" list, should be in double quotes,
                Lets think step by step.
    
                Below is the query.
                Query: 
                """
            + query
    )
    print(prompt)

    # Run the prompt through the agent.
    response = agent.run(prompt)

    # Convert the response to a string.
    return response.__str__()


def file_query(file_path, query, msg=None):
    agent = create_agent(file_path)

    response = query_agent(agent, query, msg)

    return response


def sql_query(query, table_name):
    project_id, dataset_id, table_name = table_name.split('.')
    service_account_file = os.environ.get("G_SERVICE_KEY")
    sqlalchemy_url = f'bigquery://{project_id}/{dataset_id}?credentials_path={service_account_file}'

    # Set up langchain
    db = SQLDatabase.from_uri(sqlalchemy_url)
    # llm = OpenAI(temperature=0, model="text-davinci-003")
    llm = ChatOpenAI(temperature=0, model="gpt-4-0613")

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        # agent_type=AgentType.OPENAI_FUNCTIONS,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        top_k=1000
    )

    response = agent_executor.run(query)
    # print(response)
    return response


def main():
    # file_path = '/Users/hopedion/Downloads/black_friday_sales/train.csv'
    # file_path = '/Users/hopedion/Downloads/loredatagpt_test2.csv'
    # file_path = '/Users/hopedion/Downloads/claims_jake_gpt_test.xlsx'
    file_path = '/home/dozie/Downloads/titanic.csv'

    agent = create_agent(file_path)

    # query = 'Divide the total admissions by the member years for each organization to get the admissions per member year? Also propose 3 questions about the data'
    # query = "write an sql query that lists the first column"
    # query = "what is the admissions per 1000 member years at each organization?"
    query = "Tell me something about this data. illustrate with graph"
    response = query_agent(agent, query)
    # agent.run("Divide the total admissions by the member years for each organization to get the admissions per member year, show a graph? Also propose 3 questions about the data")
    # agent.run("what is the average revenue for each year")
    # print(aa)
    # aa = agent.run("provide a json representation of aggregated data")
    # print(aa)
    # agent.run('What is the total revenue across each year')
    print(response)


if __name__ == '__main__':
    # data_test()
    main()
