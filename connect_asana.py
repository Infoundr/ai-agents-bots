from integrations.asana_oauth import AsanaOAuth 
from integrations.user_credentials import UserCredentialStore
import streamlit as st
import asana

def render_asana_connection_ui():
    """UI for connecting Asana account."""
    st.title("Connect Your Asana Account")
    
    # Only show if user is logged in
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.error("Please log in first.")
        return
        
    user_id = st.session_state.user_id
    credential_store = UserCredentialStore()
    asana_oauth = AsanaOAuth()
    
    # Check if user already has Asana connected
    asana_creds = credential_store.get_asana_credentials(user_id)
    
    if asana_creds:
        st.success("✅ Your Asana account is connected")
        
        # Show workspace and project selection
        try:
            client = asana.Client.access_token(asana_creds["access_token"])
            workspaces = client.workspaces.get_workspaces()
            
            workspace_names = {ws["gid"]: ws["name"] for ws in workspaces}
            current_workspace = asana_creds["workspace_gid"]
            
            selected_workspace = st.selectbox(
                "Select Workspace",
                options=list(workspace_names.keys()),
                format_func=lambda x: workspace_names[x],
                index=list(workspace_names.keys()).index(current_workspace) if current_workspace in workspace_names else 0
            )
            
            if selected_workspace:
                # Fetch projects for selected workspace
                projects = client.projects.get_projects({"workspace": selected_workspace})
                project_names = {p["gid"]: p["name"] for p in projects}
                
                # Get user's current active project
                active_project_key = f"active_project_{user_id}"
                if active_project_key not in st.session_state:
                    st.session_state[active_project_key] = None
                
                # Let user select default project
                selected_project_name = st.selectbox(
                    "Select Default Project",
                    options=list(project_names.values())
                )
                
                selected_project_gid = None
                for gid, name in project_names.items():
                    if name == selected_project_name:
                        selected_project_gid = gid
                        break
                
                if st.button("Save Preferences"):
                    # Update the user's project preferences
                    project_gids = asana_creds.get("project_gids", {})
                    project_gids[selected_project_name] = selected_project_gid
                    
                    credential_store.store_asana_credentials(
                        user_id,
                        asana_creds["access_token"],
                        selected_workspace,
                        project_gids
                    )
                    
                    # Set active project
                    st.session_state[active_project_key] = selected_project_name
                    
                    st.success("Preferences saved!")
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"Error connecting to Asana: {str(e)}")
            st.button("Reconnect Asana Account")
    else:
        # Show connect button
        st.info("Connect your Asana account to create and manage tasks.")
        
        if "asana_oauth_state" not in st.session_state:
            st.session_state.asana_oauth_state = "initial"
            
        if st.session_state.asana_oauth_state == "initial":
            if st.button("Connect Asana"):
                auth_url = asana_oauth.get_authorization_url()
                print(f"Authorization URL: {auth_url}")
                st.session_state.asana_oauth_state = "awaiting_redirect"
                st.experimental_rerun()
                
        elif st.session_state.asana_oauth_state == "awaiting_redirect":
            st.info("You'll be redirected to Asana to authorize the app.")
            st.markdown(f"[Click here to authorize]({asana_oauth.get_authorization_url()})")
            
            # For handling the OAuth callback
            auth_code = st.text_input("Paste the authorization code here:")
            if auth_code:
                try:
                    access_token = asana_oauth.exchange_code_for_token(auth_code)
                    
                    # Get workspaces
                    client = asana.Client.access_token(access_token)
                    workspaces = client.workspaces.get_workspaces()
                    
                    if workspaces:
                        # Store basic credentials
                        credential_store.store_asana_credentials(
                            user_id,
                            access_token,
                            workspaces[0]["gid"],  # Default to first workspace
                            {}  # Empty project dict to start
                        )
                        
                        st.session_state.asana_oauth_state = "connected"
                        st.success("Successfully connected Asana account!")
                        st.experimental_rerun()
                    else:
                        st.error("No workspaces found in your Asana account.")
                except Exception as e:
                    st.error(f"Error connecting to Asana: {str(e)}")
