import streamlit as st
from dotenv import load_dotenv
from integrations.manager import IntegrationManager
import os
import json
from datetime import datetime

load_dotenv()

def main():
    st.set_page_config(
        page_title="Infoundr Task AI Agent", 
        page_icon="🤖",
        layout="wide"
    )

    # Branding and header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://placekitten.com/100/100", use_column_width=True)  # Replace with Infoundr logo
    with col2:
        st.title("🤖 Infoundr Task AI Agent")
        st.subheader("Your intelligent task management assistant")
    
    st.markdown("---")

    # Set up integration manager
    integration_manager = IntegrationManager()
    integration_manager.setup_default_integrations()

    # Check which integrations are available
    available_integrations = []
    for tool_name in ["jira", "asana", "trello"]:
        tool = integration_manager.get_integration(tool_name)
        if tool:
            available_integrations.append(tool_name)

    if not available_integrations:
        st.error("No project management integrations configured. Please check your .env file.")
        st.stop()

    # Select integration to test
    selected_integration = st.selectbox(
        "Select project management tool:",
        available_integrations
    )

    pm_tool = integration_manager.get_integration(selected_integration)

    # Sidebar with information
    with st.sidebar:
        st.header("About Infoundr Task AI")
        st.write("""
        The Infoundr Task AI Agent helps entrepreneurs and teams manage their tasks using 
        natural language. Simply describe what you need to do, and let the AI handle the details.
        """)
        
        st.subheader("Example prompts:")
        st.info("Create a task to review our marketing materials by next Friday")
        st.info("I need to prepare a presentation for the investor meeting on May 15th")
        st.info("Add a high priority task to follow up with clients this week")
        
        st.markdown("---")
        st.caption("© 2023 Infoundr | Powered by AI")

    # Natural language AI assistant interface
    # Initialize conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hi! I'm the Infoundr Task AI Assistant. I can help you create and manage tasks in {selected_integration.capitalize()}. Just describe what you need, and I'll take care of the details. How can I help you today?"}
        ]

    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("Describe your task or ask a question..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with AI agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if selected_integration == "asana":
                    # Process using our LangChain Asana integration
                    try:
                        response = pm_tool.process_natural_language_request(prompt)
                        
                        # Display AI response
                        st.markdown(response['response'])
                        
                        # If a task was created, show the details
                        if response.get('task') and response['task'].get('id'):
                            st.success("✅ Task created successfully!")
                            st.markdown(f"**Task URL:** [{response['task'].get('title', 'New Task')}]({response['task']['url']})")
                        
                        # Add to message history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response['response']
                        })
                    except Exception as e:
                        error_message = f"Sorry, I encountered an error: {str(e)}"
                        st.error(error_message)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_message
                        })
                else:
                    # For other integrations, we'll need similar implementations
                    message = f"I'm sorry, natural language task creation for {selected_integration} is not implemented yet with the Infoundr Task AI Agent."
                    st.markdown(message)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": message
                    })

if __name__ == "__main__":
    main()