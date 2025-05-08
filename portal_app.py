# portal_app.py
# A Streamlit-based web portal to upload, reorder, strip decimals from joint X/Y/Z columns,
# concatenate multiple CSV files, and download the combined result.
#
# Deployment Instructions:
#
# 1. Prepare requirements.txt
#    Create a file named requirements.txt in the same directory containing:
#      streamlit
#      pandas
#
# 2. Push to GitHub
#    - Initialize a git repo:    git init
#    - Stage files:              git add portal_app.py requirements.txt
#    - Commit:                   git commit -m "Initial commit of CSV Joiner Portal"
#    - Create GitHub repo and add remote:
#        git remote add origin https://github.com/<your-username>/<repo-name>.git
#    - Push:                     git push -u origin main
#
# 3. Deploy on Streamlit Community Cloud
#    a. Go to https://streamlit.io/cloud and log in with your GitHub account.
#    b. Click "New app" in the top right.
#    c. In the dialog:
#         - Repository: select <your-username>/<repo-name>
#         - Branch:      main (or the branch you pushed to)
#         - Main file path: /portal_app.py
#    d. Click "Deploy". Streamlit will install dependencies from requirements.txt and launch your app.
#    e. Once deployed, you can share the generated URL (e.g. https://<app-name>.streamlit.app) with users.
#    f. To update the app, commit and push changes to main; Streamlit Cloud auto-redeploys.
#
# 4. Local Run (for testing):
#    pip install -r requirements.txt
#    streamlit run portal_app.py

import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

def process_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip decimals from any column ending in _X, _Y or _Z."""
    for col in df.columns:
        if col.endswith(("_X", "_Y", "_Z")):
            df[col] = df[col].round().astype("Int64")
    return df

st.set_page_config(page_title="CSV Joiner Portal", layout="wide")
st.title("📑 CSV Joiner Portal")
st.write("Upload multiple CSVs, drag to reorder them, strip decimals from joint X/Y/Z, and download the merged file.")

# Keep track of the last set of filenames
if "file_set" not in st.session_state:
    st.session_state.file_set = []

uploaded_files = st.file_uploader(
    "Upload CSV files (hold Ctrl/Cmd to select multiple)",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    # Extract names and detect changes
    names = [f.name for f in uploaded_files]
    if set(names) != set(st.session_state.file_set):
        st.session_state.file_set = names.copy()

    st.subheader("🔀 Drag to Reorder Files")
    st.info("Click and drag a filename to change its position in the merge order.")

    # Render the drag-and-drop list
    ordered_names = sort_items(
        items=st.session_state.file_set,
        key="sortable_file_list"
    )

    # Process & Download
    if st.button("▶️ Process & Download"):
        # Build a map from name → UploadedFile
        file_map = {f.name: f for f in uploaded_files}

        # Read, process, and collect DataFrames in the user-defined order
        dfs = []
        for fname in ordered_names:
            df = pd.read_csv(file_map[fname])
            dfs.append(process_df(df))

        # Concatenate and offer download
        combined = pd.concat(dfs, ignore_index=True)
        buf = io.StringIO()
        combined.to_csv(buf, index=False)
        buf.seek(0)

        st.download_button(
            label="📥 Download Combined CSV",
            data=buf.getvalue(),
            file_name="combined.csv",
            mime="text/csv"
        )

# Sidebar instructions
st.sidebar.header("ℹ️ Instructions")
st.sidebar.markdown(
    """
    1. Upload your CSV files.  
    2. Drag and drop filenames to reorder them.  
    3. Click **Process & Download** to merge in that order.
    """
)
