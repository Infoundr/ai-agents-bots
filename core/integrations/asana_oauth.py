import streamlit as st
import os
from urllib.parse import urlencode
from .user_credentials import UserCredentialStore
import asana
from asana.rest import ApiException

class AsanaOAuth:
    def __init__(self):
        self.client_id = os.environ.get("ASANA_CLIENT_ID")
        self.client_secret = os.environ.get("ASANA_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("ASANA_REDIRECT_URI")
        
    def get_authorization_url(self):
        """Generate the URL for Asana authorization."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "default"
        }
        return f"https://app.asana.com/-/oauth_authorize?{urlencode(params)}"
        
    def exchange_code_for_token(self, code):
        """Exchange the authorization code for an access token."""
        import requests
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        response = requests.post("https://app.asana.com/-/oauth_token", data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        raise Exception(f"Error exchanging code: {response.text}")

def render_asana_connection_ui():
    """UI for connecting Asana account."""
    st.title("Connect Your Asana Account")
    
    # Only show if user is logged in
    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.error("Please log in first.")
        return
        
    user_id = st.session_state.user_id
    credential_store = UserCredentialStore()
    
    # Check if already connected
    asana_creds = credential_store.get_asana_credentials(user_id)
    if asana_creds:
        st.success("✅ Your Asana account is already connected!")
        
        # Show option to disconnect or go back
        if st.button("Use Connected Account"):
            # Force has_integrations to True and return to main
            st.session_state["has_integrations"] = True
            st.session_state["page"] = "main"
            st.experimental_rerun()
            
        if st.button("Disconnect Account"):
            # Clear credentials
            credential_store = UserCredentialStore()
            credential_store.clear_asana_credentials(user_id)
            st.experimental_rerun()
            
        return
    
    # Check if we have OAuth settings
    client_id = os.environ.get("ASANA_CLIENT_ID")
    client_secret = os.environ.get("ASANA_CLIENT_SECRET")
    redirect_uri = os.environ.get("ASANA_REDIRECT_URI")
    
    if not client_id or not client_secret or not redirect_uri:
        # If OAuth is not set up, allow direct API token entry
        st.write("Enter your Asana API Token to connect your account.")
        st.write("You can create a personal access token at: https://app.asana.com/0/developer-console")
        
        with st.form("asana_token_form"):
            st.markdown("#### Enter your Asana API Token")
            st.write("1. Go to [Asana Developer Console](https://app.asana.com/0/developer-console)")
            st.write("2. Create a 'Personal Access Token'")
            st.write("3. Copy and paste the token below")
            
            api_token = st.text_input("Asana Personal Access Token", type="password")
            workspace_gid = st.text_input("Asana Workspace GID (optional)")
            project_gid = st.text_input("Asana Project GID (optional)")
            
            # Add token validation help
            if api_token:
                if len(api_token) < 30:
                    st.warning("Token seems too short. Asana tokens are typically longer.")
                elif api_token.startswith(" ") or api_token.endswith(" "):
                    st.warning("Token has leading or trailing spaces. Please remove them.")
            
            submit = st.form_submit_button("Connect Asana")
            
            if submit and api_token:
                try:
                    # Use the new SDK approach
                    configuration = asana.Configuration()
                    configuration.access_token = api_token
                    api_client = asana.ApiClient(configuration)
                    
                    # Create specific API instances
                    workspaces_api = asana.WorkspacesApi(api_client)
                    projects_api = asana.ProjectsApi(api_client)
                    
                    # Get workspaces - IMPORTANT: Convert generator to list
                    workspaces = list(workspaces_api.get_workspaces({}))
                    
                    # If workspace not specified, use the first one
                    if not workspace_gid and workspaces:
                        workspace_gid = workspaces[0]["gid"]
                        st.success(f"Using workspace: {workspaces[0]['name']}")
                    
                    # Store the credentials
                    project_gids = {}
                    if project_gid:
                        # Try to get the project name
                        try:
                            project = projects_api.get_project(project_gid, {})
                            project_gids[project["name"]] = project_gid
                        except:
                            project_gids["Default Project"] = project_gid
                    
                    # Store credentials
                    credential_store.store_asana_credentials(
                        user_id,
                        api_token,
                        workspace_gid,
                        project_gids
                    )
                    
                    # Set flags to ensure we detect the integration
                    st.session_state["has_integrations"] = True
                    
                    st.success("Successfully connected to Asana!")
                    st.session_state["page"] = "main"
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Error connecting to Asana: {str(e)}")
    else:
        # Use OAuth flow
        asana_oauth = AsanaOAuth()
        
        if "asana_oauth_state" not in st.session_state:
            st.session_state.asana_oauth_state = "initial"
            
        if st.session_state.asana_oauth_state == "initial":
            st.write("Click below to authorize the app to access your Asana account.")
            if st.button("Authorize with Asana"):
                auth_url = asana_oauth.get_authorization_url()
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
                    
                    # Use the new SDK approach
                    configuration = asana.Configuration()
                    configuration.access_token = access_token
                    api_client = asana.ApiClient(configuration)
                    
                    # Create API instances
                    workspaces_api = asana.WorkspacesApi(api_client)
                    
                    # Get workspaces - IMPORTANT: Convert generator to list
                    workspaces = list(workspaces_api.get_workspaces({}))
                    
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
