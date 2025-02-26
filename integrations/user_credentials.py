import os
import json
from typing import Dict, Optional
import streamlit as st

class UserCredentialStore:
    """Simple class to store user credentials using Streamlit's session state.
    In a production app, this would use a database."""
    
    def __init__(self):
        # Initialize the credentials store if it doesn't exist
        if "user_credentials" not in st.session_state:
            st.session_state.user_credentials = {}
    
    def store_asana_credentials(self, user_id: str, access_token: str, 
                               workspace_gid: str, project_gids: Dict[str, str]):
        """Store a user's Asana credentials."""
        if user_id not in st.session_state.user_credentials:
            st.session_state.user_credentials[user_id] = {}
            
        st.session_state.user_credentials[user_id]["asana"] = {
            "access_token": access_token,
            "workspace_gid": workspace_gid,
            "project_gids": project_gids,
            "integration_connected": True
        }
        
    def get_asana_credentials(self, user_id: str) -> Optional[Dict]:
        """Retrieve a user's Asana credentials."""
        if user_id not in st.session_state.user_credentials:
            return None
            
        asana_data = st.session_state.user_credentials[user_id].get("asana")
        if not asana_data:
            return None
            
        return {
            "access_token": asana_data.get("access_token"),
            "workspace_gid": asana_data.get("workspace_gid"),
            "project_gids": asana_data.get("project_gids", {})
        }

def clear_asana_credentials(self, user_id: str):
    """Clear a user's Asana credentials."""
    if user_id in st.session_state.user_credentials and "asana" in st.session_state.user_credentials[user_id]:
        del st.session_state.user_credentials[user_id]["asana"]
        return True
    return False
