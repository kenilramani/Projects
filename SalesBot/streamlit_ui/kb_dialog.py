import streamlit as st
import requests
import os
from config import API_BASE_URL


@st.dialog("📚 Knowledge Base", width="large")
def kb_dialog():
    """
    Render the Knowledge Base management dialog.
    Allows users to upload .txt files to be ingested into their personal collection.
    """
    st.markdown(
        "Upload documents to your personal Knowledge Base. The bot will use these documents to answer questions."
    )

    # User Context
    user_id = st.session_state.get("auth_user_id")
    if not user_id:
        st.error("You must be logged in to manage your Knowledge Base.")
        return

    st.info(f"Managing Knowledge Base for User ID: `{user_id}`")

    # File Uploader
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt"],
        help="Currently supports .txt files. Content will be split by '##' headers.",
    )

    if uploaded_file:
        if st.button("📤 Upload & Ingest", type="primary", use_container_width=True):
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                try:
                    # Prepare the request
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "text/plain",
                        )
                    }
                    data = {"user_id": user_id}

                    # Send to backend
                    response = requests.post(
                        f"{API_BASE_URL}/ingest_documents",
                        files=files,
                        data=data,
                        timeout=120,  # Longer timeout for embedding generation
                    )

                    if response.status_code == 200:
                        st.success(f"✅ Successfully ingested `{uploaded_file.name}`!")
                    else:
                        st.error(
                            f"Failed to ingest: {response.status_code} - {response.text}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()
    st.caption(
        "Note: Duplicate uploads will create duplicate entries. Manage carefully."
    )
