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

def process_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip decimals from any column ending in _X, _Y or _Z."""
    for col in df.columns:
        if col.endswith(("_X", "_Y", "_Z")):
            df[col] = df[col].round().astype("Int64")
    return df

st.set_page_config(page_title="CSV Joiner Portal", layout="wide")
st.title("📑 CSV Joiner Portal")
st.write("Upload multiple CSVs, assign each a position, strip decimals from X/Y/Z, then merge in that order.")

# --- SESSION STATE SETUP ---
if "file_set" not in st.session_state:
    st.session_state.file_set = []
# We'll have keys "order_0", "order_1", ... seeded below.

# --- FILE UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload CSV files (Ctrl/Cmd to select multiple)",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    names = [f.name for f in uploaded_files]

    # If the set of files changed, reset our ordering state
    if set(st.session_state.file_set) != set(names):
        st.session_state.file_set = names.copy()
        # Remove any old order_* keys
        for key in list(st.session_state.keys()):
            if key.startswith("order_"):
                del st.session_state[key]
        # Seed new order_* keys = their original indices
        for idx in range(len(names)):
            st.session_state[f"order_{idx}"] = idx

    # --- ORDERING UI ---
    st.subheader("🔀 Assign Positions to Files")
    st.markdown("Lower numbers come first (0 = first).")
    cols = st.columns([4, 1])
    cols[0].markdown("**Filename**")
    cols[1].markdown("**Position**")

    for idx, fname in enumerate(st.session_state.file_set):
        c1, c2 = st.columns([4,1])
        c1.write(fname)
        order_key = f"order_{idx}"
        # number_input will read & write into st.session_state[order_key]
        c2.number_input(
            label="",
            min_value=0,
            max_value=len(names)-1,
            key=order_key
        )

    # Build final ordered list (ties broken by the original idx)
    ordering = [
        (st.session_state[f"order_{i}"], i, fname)
        for i, fname in enumerate(st.session_state.file_set)
    ]
    ordered_names = [t[2] for t in sorted(ordering, key=lambda x: (x[0], x[1]))]

    # --- PROCESS & DOWNLOAD ---
    if st.button("▶️ Process & Download"):
        file_map = {f.name: f for f in uploaded_files}
        dfs = []
        for fname in ordered_names:
            df = pd.read_csv(file_map[fname])
            dfs.append(process_df(df))
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

# --- SIDEBAR INSTRUCTIONS ---
st.sidebar.header("ℹ️ Instructions")
st.sidebar.markdown(
    """
    1. Upload one or more CSV files.  
    2. For each file, set its **Position** (0 = first, 1 = second, …).  
    3. Click **Process & Download** to get the concatenated CSV in that order.
    """
)
