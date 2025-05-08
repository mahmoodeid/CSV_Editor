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

# portal_app.py

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

# ─── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="CSV Joiner Portal", layout="wide")
st.title("📑 CSV Joiner Portal")
st.write(
    "Upload multiple CSV files, drag-and-drop to reorder them, "
    "optionally drop confidence columns, strip decimals from X/Y/Z, "
    "then download the combined CSV."
)

# ─── Session State for file order ─────────────────────────────────────────────
if "file_set" not in st.session_state:
    st.session_state.file_set = []

# ─── File Uploader ─────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload CSV files (hold Ctrl/Cmd to select multiple)",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    # 1) Get the list of filenames
    names = [f.name for f in uploaded_files]

    # 2) If the set of files changed, reset our stored order
    if set(st.session_state.file_set) != set(names):
        st.session_state.file_set = names.copy()

    # ─── Drag-and-Drop Reordering ───────────────────────────────────────────────
    st.subheader("🔀 Drag to Reorder Files")
    ordered_names = sort_items(
        items=st.session_state.file_set,
        key="csv_joiner_sortable"   # unique key for this component
    )
    # Persist the new order back into session state
    st.session_state.file_set = ordered_names

    # ─── Confidence–column toggle ───────────────────────────────────────────────
    remove_confidence = st.checkbox(
        "🗑️ Remove confidence columns",
        help="Tick to drop all columns ending in _Confidence before merging"
    )

    # ─── Process & Download ────────────────────────────────────────────────────
    if st.button("▶️ Process & Download"):
        file_map = {f.name: f for f in uploaded_files}
        dfs = []
        for fname in ordered_names:
            df = pd.read_csv(file_map[fname])

            # Optionally drop any *_Confidence columns
            if remove_confidence:
                conf_cols = [c for c in df.columns if c.endswith("_Confidence")]
                df = df.drop(columns=conf_cols, errors="ignore")

            # Strip decimals from X/Y/Z
            df = process_df(df)
            dfs.append(df)

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

# ─── Sidebar Instructions ─────────────────────────────────────────────────────
st.sidebar.header("ℹ️ Instructions")
st.sidebar.markdown(
    """
    1. Upload one or more CSV files.  
    2. Drag and drop the filenames to set your merge order.  
    3. (Optional) Tick **Remove confidence columns** to drop any *_Confidence fields.  
    4. Click **Process & Download** to get the concatenated CSV.
    """
)