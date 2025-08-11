import os
from typing import TypedDict, Annotated, Sequence, Union, List
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import json
from typing import TypedDict, List


# Load environment variables
load_dotenv()

# Get API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Define state schema
class AgentState(TypedDict):
    messages: List[str]
    topic: str
    recipient_type: str
    research_findings: str
    email_strategy: str
    final_email: str
    current_agent: str
    next_agent: str
    done: bool

def load_documents_from_files(files):
    """Load documents from user-uploaded files."""
    documents = []
    
    for file in files:
        if file.lower().endswith('.pdf'):
            loader = PyPDFLoader(file)
            documents.extend(loader.load())
        elif file.lower().endswith('.txt'):
            loader = TextLoader(file)
            documents.extend(loader.load())
        else:
            print(f"Skipping {file.filename} - not a PDF or TXT file")
    
    return documents

def create_vector_store(documents):
    """Create a vector store from the documents."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    texts = text_splitter.split_documents(documents)

    print(f"Created {len(texts)} text chunks for processing")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large",api_key=OPENAI_API_KEY)
    vectorstore = Chroma.from_documents(texts, embeddings)

    return vectorstore

# Initialize agents
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=OPENAI_API_KEY
    # api_key="...",  # if you prefer to pass api key in directly instaed of using env vars
    # base_url="...",
    # organization="...",
    # other params...
)

class ResearchAgent:
    def __init__(self, vectorstore):
        self.retriever = vectorstore.as_retriever()
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=self.retriever,
            chain_type="stuff",
            return_source_documents=True
        )


    def __call__(self, state: AgentState) -> dict:
        print("Research Agent: Analyzing documents...")

        query = f"""
        Analyze the provided documents and extract key information about:
        1. Our company's services/products
        2. Key selling points
        3. Relevant case studies or success stories
        4. Any specific information related to {state['topic']}

        Format the findings in a clear, structured way.
        """

        response = self.qa_chain.invoke({"query": query})
        state['research_findings'] = response['result']
        state['current_agent'] = 'research' 
        state['next_agent'] = 'strategy'
        return state

class StrategyAgent:
    def __init__(self):
        self.llm = llm

    def __call__(self, state: AgentState) -> dict:
        print("Strategy Agent: Planning email approach...")

        prompt = f"""
        Based on the research findings below, develop a strategy for the marketing email:

        Research Findings:
        {state['research_findings']}

        Target Recipient: {state['recipient_type']}
        Topic Focus: {state['topic']}

        Create a strategic plan that includes:
        1. Key messages to emphasize
        2. Recommended tone and approach
        3. Specific points from the research to include
        4. Suggested structure for maximum impact
        """

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        state['email_strategy'] = response.content
        state['current_agent'] = 'strategy'
        state['next_agent'] = 'writer'
        return state

class WriterAgent:
    def __init__(self):
        self.llm = llm

    def __call__(self, state: AgentState) -> dict:
        print("Writer Agent: Composing email...")

        prompt = f"""
        Create a compelling marketing email using the research and strategy below:

        Research Findings:
        {state['research_findings']}

        Email Strategy:
        {state['email_strategy']}

        Topic Focus: {state['topic']}
        Target Recipient: {state['recipient_type']}

        Generate a professional email that includes:
        1. Attention-grabbing subject line
        2. Personalized greeting
        3. Compelling body content
        4. Clear call to action
        5. Professional signature

        Make sure to incorporate specific details from the research and follow the recommended strategy.
        """

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        state['final_email'] = response.content
        state['current_agent'] = 'writer'
        state['done'] = True
        return state

def should_continue(state: AgentState) -> str:
    """Determine if the workflow should continue or end."""
    if state['done']:
        return "end"
    return state['next_agent']

def create_agent_graph(vectorstore):
    # Initialize agents
    research_agent = ResearchAgent(vectorstore)
    strategy_agent = StrategyAgent()
    writer_agent = WriterAgent()

    # Create workflow graph
    workflow = StateGraph(AgentState)
    # Add agent nodes
    workflow.add_node('research', research_agent)
    workflow.add_node('strategy', strategy_agent)
    workflow.add_node('writer', writer_agent)
    # Define edges
    workflow.add_edge('research', 'strategy')
    workflow.add_edge('strategy', 'writer')
    # Set entry point
    workflow.set_entry_point('research')
    # Add conditional edge for completion
    workflow.add_conditional_edges(
        'writer',
        should_continue
    )
    # Set end point
    workflow.add_node("end", lambda x: x)

    # Compile workflow
    return workflow.compile()

def marketing_main(files, topic, recipient_type):
    try:
        documents = load_documents_from_files(files)
        vectorstore = create_vector_store(documents)
        workflow = create_agent_graph(vectorstore)
        
        state = AgentState(
            messages=[],
            topic=topic,
            recipient_type=recipient_type,
            research_findings="",
            email_strategy="",
            final_email="",
            current_agent="",
            next_agent="research",
            done=False
        )
        
        final_state = workflow.invoke(state)
        return final_state['final_email']
    
    except Exception as e:
        return f"An error occurred: {str(e)}"

