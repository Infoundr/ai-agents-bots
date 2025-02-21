from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.tools.ddg_search import DuckDuckGoSearchRun
from langchain.utilities import SerpAPIWrapper
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
import streamlit as st
from typing import Dict, List
import os
from dotenv import load_dotenv
from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
from typing import Union

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Infoundr - AI Entrepreneurship Assistant",
    page_icon="🤖",
    layout="wide"
)

class KnowledgeBase:
    def __init__(self, domain: str):
        self.domain = domain
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = self.initialize_knowledge_base()
        
    def initialize_knowledge_base(self):
        loader = TextLoader(f'knowledge_bases/{self.domain}.txt')
        documents = loader.load()
        return FAISS.from_documents(documents, self.embeddings)
        
    def query(self, question: str) -> str:
        docs = self.vectorstore.similarity_search(question)
        return docs[0].page_content

class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        return AgentFinish(
            return_values={"output": llm_output},
            log=llm_output,
        )

class Bot:
    def __init__(self, name: str, role: str, expertise: str, personality: str):
        self.name = name
        self.filename = name.lower().replace(" ", "_")
        self.role = role
        self.expertise = expertise
        self.personality = personality
        self.memory = ConversationBufferMemory()
        self.knowledge_base = KnowledgeBase(name.lower())
        self.tools = self.get_specialized_tools()
        
        # Create specialized prompt template
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=f"""You are {name}, {role}. Your expertise is in {expertise}.
            Personality: {personality}
            
            Current conversation:
            {'{history}'}
            Human: {'{input}'}
            {name}:"""
        )
        
        # Initialize conversation chain
        self.chain = ConversationChain(
            llm=ChatOpenAI(temperature=0.7),
            memory=self.memory,
            prompt=self.prompt,
            input_key="input",
            output_key="output"
        )

        # Initialize agent
        output_parser = CustomOutputParser()
        
        self.agent = LLMSingleActionAgent(
            llm_chain=self.chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=[tool.name for tool in self.tools],
            input_key="input"
        )

        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def get_specialized_tools(self):
        search = DuckDuckGoSearchRun()
        knowledge_tool = Tool(
            name="Knowledge Base",
            func=self.knowledge_base.query,
            description=f"Access specialized knowledge about {self.expertise}"
        )
        return [search, knowledge_tool]

    def output_parser(self, llm_output: str):
        return llm_output


def display_bot_persona(bot_name: str):
    cols = st.columns([1, 3])
    
    with cols[0]:
        image_path = f"assets/bot_images/{bot_name.lower()}.png"
        st.image(image_path, caption=bot_name)
        
    with cols[1]:
        st.markdown(f"""
        ### {BOTS[bot_name].role}
        **Expertise**: {BOTS[bot_name].expertise}
        **Approach**: {BOTS[bot_name].personality}
        """)

def generate_proactive_suggestions(bot: Bot, chat_history: List[dict]) -> List[str]:
    suggestion_prompt = PromptTemplate(
        input_variables=["history", "expertise"],
        template="""Based on this conversation history and your expertise in {expertise},
        what are 3 proactive suggestions or insights you could offer?
        
        History: {history}
        
        Suggestions:"""
    )
    
    suggestions = bot.chain.predict(
        input=suggestion_prompt.format(
            history=str(chat_history),
            expertise=bot.expertise
        )
    )
    return suggestions.split('\n')

# Define bots with their characteristics
BOTS = {
    "Benny": Bot(
        name="Benny",
        role="Financial Decision Making Expert from Payd",
        expertise="fintech strategies, payment solutions, financial planning for startups",
        personality="Professional, data-driven, focused on financial innovation"
    ),
    "Innocent": Bot(
        name="Innocent",
        role="Business Strategy Expert from Startinev",
        expertise="startup scaling, business growth, leadership development",
        personality="Wise, mentoring, encouraging but practical"
    ),
    "Dean": Bot(
        name="Dean",
        role="Tech Product Development Expert from Quick API",
        expertise="API integrations, tech product development, scaling solutions",
        personality="Tech-savvy, innovative, efficiency-focused"
    ),
    "Ali": Bot(
        name="Ali",
        role="Chairman of the Fintech Association",
        expertise="regulatory compliance, fintech trends, business regulations",
        personality="Professional, authoritative, detail-oriented"
    ),
    "Sheila": Bot(
        name="Sheila",
        role="Founder of Chasing Maverick",
        expertise="startup launches, marketing strategies, blockchain network management",
        personality="Dynamic, innovative, blockchain-savvy"
    ),
    "Felix": Bot(
        name="Felix",
        role="Founder of KotaniPay",
        expertise="fundraising strategies, investment acquisition, license compliance",
        personality="Strategic, investment-focused, compliance-oriented"
    ),
    "Matt": Bot(
        name="Matt",
        role="Founder of Jobzy",
        expertise="hiring strategies, job marketplace development, team culture",
        personality="People-oriented, culture-focused, hiring expert"
    ),
    "Nelly": Bot(
        name="Nelly",
        role="Founder of Zidallie",
        expertise="customer outreach, marketing strategies, customer engagement",
        personality="Welcoming, customer-focused, engagement specialist"
    ),
    "Liech": Bot(
        name="Liech",
        role="Head of Liech Group",
        expertise="innovation, ideation, cross-industry problem solving",
        personality="Strategic, innovative, multi-industry expert"
    ),
    "Steve": Bot(
        name="Steve",
        role="Tech Product Development Expert",
        expertise="scalable product development, technical innovation, product roadmaps",
        personality="Technical, innovative, product-focused"
    ),
    "Muoka": Bot(
        name="Muoka",
        role="Legal and Blockchain Expert",
        expertise="business registration, licensing, legal compliance",
        personality="Professional, detail-oriented, compliance-focused"
    ),
    "Caleb": Bot(
        name="Caleb",
        role="Founder of Tech Safari",
        expertise="strategic partnerships, networking, collaboration opportunities",
        personality="Connector, partnership-focused, strategic networker"
    )
}

# Add caching for bot responses
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_bot_response(bot, prompt):
    return bot.agent_executor.run(prompt)

# Add caching for proactive suggestions
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_proactive_suggestions(bot, history):
    return generate_proactive_suggestions(bot, history)

def main():
    st.title("🤖 Infoundr - Your AI Entrepreneurship Assistant")
    
    selected_bot = st.sidebar.selectbox("Select an expert:", list(BOTS.keys()))
    display_bot_persona(selected_bot)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Show proactive suggestions
    if st.session_state.messages:
        with st.sidebar.expander("💡 Proactive Suggestions"):
            suggestions = generate_proactive_suggestions(
                BOTS[selected_bot], 
                st.session_state.messages
            )
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What's on your mind?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            response = BOTS[selected_bot].agent_executor.run(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
