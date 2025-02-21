from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
import streamlit as st
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Infoundr - AI Entrepreneurship Assistant",
    page_icon="🤖",
    layout="wide"
)

class Bot:
    def __init__(self, name: str, role: str, expertise: str, personality: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.personality = personality
        self.chat_model = ChatOpenAI(temperature=0.7)
        self.message_history = ChatMessageHistory()
        
        # Create specialized prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are {name}, {role}. Your expertise is in {expertise}. Personality: {personality}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create chain
        self.chain = self.prompt | self.chat_model

    def get_response(self, input_text: str) -> str:
            # Add user message to history
            self.message_history.add_user_message(input_text)
            
            # Generate response
            response = self.chain.invoke({
                "history": self.message_history.messages,
                "input": input_text
            })
            
            # Add AI response to history
            self.message_history.add_ai_message(response.content)
            
            return response.content

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

def main():
    st.title("🤖 Infoundr - Your AI Entrepreneurship Assistant")
    
    # Sidebar for bot selection
    st.sidebar.title("Choose Your Advisor")
    selected_bot = st.sidebar.selectbox(
        "Select an expert to chat with:",
        list(BOTS.keys())
    )
    
    # Initialize chat histories for each bot
    if "bot_messages" not in st.session_state:
        st.session_state.bot_messages = {bot: [] for bot in BOTS.keys()}
    
    # Display bot info
    st.sidebar.write(f"**Role:** {BOTS[selected_bot].role}")
    st.sidebar.write(f"**Expertise:** {BOTS[selected_bot].expertise}")
    
    # Display current bot's chat history
    for message in st.session_state.bot_messages[selected_bot]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What's on your mind?"):
        # Add user message to current bot's chat history
        st.session_state.bot_messages[selected_bot].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate bot response
        with st.chat_message("assistant"):
            response = BOTS[selected_bot].get_response(prompt)
            st.markdown(response)
            st.session_state.bot_messages[selected_bot].append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()