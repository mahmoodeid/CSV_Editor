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

def process_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip decimals from any column ending in _X, _Y or _Z."""
    for col in df.columns:
        if col.endswith(("_X", "_Y", "_Z")):
            df[col] = df[col].round().astype("Int64")
    return df

st.set_page_config(page_title="CSV Joiner Portal", layout="wide")
st.title("📑 CSV Joiner Portal")
st.write("Upload multiple CSVs, reorder them, strip decimals from joint X/Y/Z, and download the merged file.")

# Initialize session state for file order
if "file_order" not in st.session_state:
    st.session_state.file_order = []

# Upload multiple CSV files
uploaded_files = st.file_uploader(
    "Upload CSV files (hold Ctrl/Cmd to select multiple)",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    names = [f.name for f in uploaded_files]

    # Only init or re-init when the list is empty or the set of files changes
    if (not st.session_state.file_order) or (set(st.session_state.file_order) != set(names)):
        st.session_state.file_order = names

    st.subheader("🔀 Reorder Files")
    file_map = {f.name: f for f in uploaded_files}

    # Show each filename with Up/Down buttons
    for idx, fname in enumerate(st.session_state.file_order):
        cols = st.columns([6, 1, 1])
        cols[0].write(fname)

        up_disabled = idx == 0
        down_disabled = idx == len(st.session_state.file_order) - 1

        if cols[1].button("⬆️", key=f"up_{fname}", disabled=up_disabled):
            # swap up in session state
            st.session_state.file_order[idx - 1], st.session_state.file_order[idx] = (
                st.session_state.file_order[idx],
                st.session_state.file_order[idx - 1],
            )

        if cols[2].button("⬇️", key=f"down_{fname}", disabled=down_disabled):
            # swap down in session state
            st.session_state.file_order[idx + 1], st.session_state.file_order[idx] = (
                st.session_state.file_order[idx],
                st.session_state.file_order[idx + 1],
            )

    # Once ordering is set, process & concatenate on demand
    if st.button("▶️ Process & Download"):
        dfs = []
        for fname in st.session_state.file_order:
            file_obj = file_map[fname]
            df = pd.read_csv(file_obj)
            dfs.append(process_df(df))

        combined = pd.concat(dfs, ignore_index=True)
        buffer = io.StringIO()
        combined.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Combined CSV",
            data=buffer.getvalue(),
            file_name="combined.csv",
            mime="text/csv"
        )

# Sidebar instructions
st.sidebar.header("ℹ️ Instructions")
st.sidebar.markdown(
    "1. Upload your CSV files.\n"
    "2. Reorder them using the Up/Down buttons.\n"
    "3. Click **Process & Download** to get the merged CSV."
)
