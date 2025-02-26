import streamlit as st
from dotenv import load_dotenv
from integrations.manager import IntegrationManager
import os
from integrations.user_credentials import UserCredentialStore
from integrations.asana_integration import setup_authentication
from integrations.asana_oauth import render_asana_connection_ui

load_dotenv()

def main():
    # Set page config first before any other st calls
    st.set_page_config(
        page_title="Infoundr Task AI Agent", 
        page_icon="🤖",
        layout="wide"
    )
    
    # Check if we should be on a different page
    if "page" in st.session_state and st.session_state["page"] != "main":
        if st.session_state["page"] == "connect_asana":
            render_asana_connection_ui()  
            
            # Add a back button
            if st.button("Back to Main"):
                st.session_state["page"] = "main"
                st.experimental_rerun()
            return  # Exit the main function early
    
    # If we're here, we're on the main page
    if "page" not in st.session_state:
        st.session_state["page"] = "main"

    # Handle user authentication first
    setup_authentication()
    
    # Only proceed if authenticated
    if not st.session_state.get("authenticated", False):
        return
        
    user_id = st.session_state.user_id
    
    # Branding and header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://placekitten.com/100/100", use_column_width=True)  # Replace with Infoundr logo
    with col2:
        st.title("🤖 Infoundr Task AI Agent")
        st.subheader("Your intelligent task management assistant")
    
    st.markdown("---")

    # Check for existing credentials first
    credential_store = UserCredentialStore()
    asana_creds = credential_store.get_asana_credentials(user_id)
    
    # Force setup of integration if credentials exist
    integration_manager = IntegrationManager(user_id=user_id)
    
    # Special handling to ensure credentials are loaded
    if asana_creds:
        # Manually add the Asana integration using stored credentials
        from integrations.asana_integration import AsanaIntegration
        integration_manager.integrations["asana"] = AsanaIntegration(
            access_token=asana_creds["access_token"],
            workspace_gid=asana_creds["workspace_gid"]
        )
        st.session_state["has_integrations"] = True
    else:
        # Regular setup
        integration_manager.setup_user_integrations()
        st.session_state["has_integrations"] = bool(integration_manager.integrations)
    
    print(f"User ID: {user_id}")
    print(f"Integration Manager Integrations: {integration_manager.integrations}")
    print(f"Has Asana credentials: {asana_creds is not None}")

    # Check if user has any integrations set up
    if not integration_manager.integrations:
        print("No integrations found.")
        st.info("You need to connect a project management tool first.")
        
        # Offer integration options
        connect_asana = st.button("Connect Asana")
        if connect_asana:
            print("Connect Asana button clicked!")  # Add debug output
            st.session_state["page"] = "connect_asana"
            st.experimental_rerun()
            
        return
        
    # If we get here, we have integrations set up
    # Select integration to use
    available_integrations = list(integration_manager.integrations.keys())
    print(f"Available Integrations: {available_integrations}")
    selected_integration = st.selectbox(
        "Select project management tool:",
        available_integrations
    )
    print(f"Selected Integration: {selected_integration}")

    pm_tool = integration_manager.get_integration(selected_integration)
    
    # Get user's active project for this tool
    active_project_key = f"active_project_{user_id}"
    if active_project_key in st.session_state and st.session_state[active_project_key]:
        # Load credentials to get project GID
        creds = credential_store.get_asana_credentials(user_id)
        
        if creds and "project_gids" in creds:
            project_name = st.session_state[active_project_key]
            if project_name in creds["project_gids"]:
                pm_tool.project_gid = creds["project_gids"][project_name]
                st.info(f"Creating tasks in project: {project_name}")

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