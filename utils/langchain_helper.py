import os

import pandas as pd
from django.conf import settings
from langchain.agents import AgentType, create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.memory import ConversationBufferMemory
from langchain.sql_database import SQLDatabase
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.llms.ctransformers import CTransformers
from langchain_community.llms.ollama import Ollama
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
        # lm = CTransformers(
        #     model=os.environ.get('MODEL'),
        #     model_type="mistral",
        #     config={'context_length': 4028, 'max_new_tokens': 2028},
        #     # temperature=0,
        #     model_kwargs={"temperature": 0.1, "max_length": 512}
        # )
        olla = Ollama(model='mistral')
        return olla
    llm = load_llm()
else:
    # Create an OpenAI object.
    # llm = OpenAI(temperature=0)
    llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview")


def get_memory(conversation_id):
    chat_message_history = SQLChatMessageHistory(
        session_id=conversation_id, connection_string=f"sqlite:///{settings.BASE_DIR / 'chat_history' / 'chat.db'}"

    )

    memory = ConversationBufferMemory(
        memory_key="chat_history", chat_memory=chat_message_history
    )
    return memory


def pd_agent_with_memory(llm_code, df, msg):
    memory = get_memory(str(msg.conversation.id))
    path_to_image = f"images/{msg.conversation.id}/{msg.id}"

    PREFIX = f"""
    You are working with a pandas dataframe in Python. The name of the dataframe is `df`.
    You should use the tools below to answer the question posed of you:
    
    In your analysis, please ensure that Matplotlib is utilized in non-GUI mode.
    Generate visual graphs to illustrate key insights or trends, using Matplotlib without relying on a graphical user 
    interface (GUI), and save the graphs to "{path_to_image}" directory. eg:
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    
    Include the file paths of the generated graphs in your response. Format is a json response as follows:
    
    "answer": "Your answer",
    "graphs": ["/path/to/save/graph1.png", "/path/to/save/graph2.png"],
    "questions": ["Question 1", "Question 2", "Question 3"]
    
    
    Summary of the whole conversation:
    {{chat_history}}
    """
    print(PREFIX)

    pd_agent = create_pandas_dataframe_agent(
        llm_code,
        df,
        prefix=PREFIX,
        verbose=True,
        agent_executor_kwargs={"memory": memory},
        input_variables=['df_head', 'input', 'agent_scratchpad', 'chat_history'],
        handle_parsing_errors="Check your output and make sure it conforms! Do not output an action and a final answer at the same time."
    )
    return pd_agent


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
    prompt2 = (
        f"""
        For the following query, Analyze the provided dataset [describe the dataset briefly] and present a detailed summary. Additionally, 
        generate visual graphs to illustrate key insights or trends, and save the graphs to "images/{msg.conversation.id}/{msg.id}" directory. 
        Make sure to always use matplotlib in non-GUI mode.
        Include the file paths of the generated graphs in your response. Format the response as follows:
        {{
        "answer": "Your comprehensive summary",
        "graphs": ["/path/to/save/graph1.png", "/path/to/save/graph2.png"],
        "questions": ["Question 1", "Question 2", "Question 3"]
        }}
        Below is the query.
        Query:
        """ + query
    )

    # Run the prompt through the agent.
    response = agent.run(prompt2)

    # Convert the response to a string.
    return response.__str__()


def file_query(file_path, query, msg=None):
    # agent = create_agent(file_path)

    df = get_dataframe(file_path)
    agent_mem = pd_agent_with_memory(llm, df, msg)

    if not query:
        query = 'Analyze the provided dataset [describe the dataset briefly] and present a detailed summary'
    # response = agent_mem.run(input=query, path_to_image=f"images/{msg.conversation.id}/{msg.id}")
    response = agent_mem.run(query)

    return response


def get_sql_prompt(table_name, query, msg=None):
    prompt = (
            f"""
                For the following query, you are to determine the best way to present the answer using the following:
                There query will be about {table_name}.
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

    return prompt


def sql_query(query, table_name, msg):
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

    prompt = get_sql_prompt(table_name, query, msg)

    response = agent_executor.run(prompt)
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
