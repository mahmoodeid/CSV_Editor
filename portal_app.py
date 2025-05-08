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
st.write("Upload multiple CSVs, assign each a position, strip decimals from X/Y/Z, then merge in that order.")

# --- SESSION STATE SETUP ---
if "file_set" not in st.session_state:
    st.session_state.file_set = []
# We'll store per-file integers under keys "order_0", "order_1", etc.

# --- FILE UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload CSV files (Ctrl/Cmd to select multiple)",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    # 1) Get just the list of filenames
    names = [f.name for f in uploaded_files]

    # 2) If the set of files changed, re-init our ordering state
    if set(st.session_state.file_set) != set(names):
        st.session_state.file_set = names.copy()
        # Clear any old order_* keys
        for key in list(st.session_state.keys()):
            if key.startswith("order_"):
                del st.session_state[key]
        # Initialize each file's position = its index
        for idx in range(len(names)):
            st.session_state[f"order_{idx}"] = idx

    # --- ORDERING UI ---
    st.subheader("🔀 Assign Positions to Files")
    cols = st.columns([4,1])
    cols[0].markdown("**Filename**")
    cols[1].markdown("**Position**")

    for idx, fname in enumerate(st.session_state.file_set):
        c1, c2 = st.columns([4,1])
        c1.write(fname)
        # Unique key per widget
        st.session_state[f"order_{idx}"] = c2.number_input(
            label="",
            min_value=0,
            max_value=len(names)-1,
            value=st.session_state[f"order_{idx}"],
            key=f"order_{idx}"
        )

    # Build the final ordered list (ties broken by original idx)
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

        buffer = io.StringIO()
        combined.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Combined CSV",
            data=buffer.getvalue(),
            file_name="combined.csv",
            mime="text/csv"
        )

# --- SIDEBAR INSTRUCTIONS ---
st.sidebar.header("ℹ️ Instructions")
st.sidebar.markdown(
    """
    1. Upload one or more CSV files.  
    2. For each file, assign a **Position** (0 = first, 1 = second, …).  
    3. Click **Process & Download** to get the concatenated CSV in that order.
    """
)
