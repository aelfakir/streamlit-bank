import streamlit as st
from github import Github
import json
from datetime import datetime

# --- 1. Configuration & Connection ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "aelfakir/streamlit-bank" 
FILE_PATH = "ledger.json"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def get_ledger():
    """Fetches current data and the version ID (SHA) from GitHub."""
    file_content = repo.get_contents(FILE_PATH)
    data = json.loads(file_content.decoded_content.decode())
    # Ensure all values are floats for math
    for user in data:
        data[user] = float(data[user])
    return data, file_content.sha

def update_ledger(new_data, sha, message):
    """Saves the entire updated dictionary back to GitHub."""
    content = json.dumps(new_data, indent=4)
    repo.update_file(FILE_PATH, message, content, sha)

# --- 2. Streamlit UI Setup ---
st.set_page_config(page_title="GitHub Bank", page_icon="💰", layout="wide")
st.title("💰 Mini-Pay: GitHub Edition")

# Load data at the start
try:
    ledger, sha = get_ledger()
except Exception as e:
    st.error(f"Error connecting to GitHub: {e}")
    st.stop()

# --- 3. Display Balances (Two Decimals) ---
st.subheader("Bank Ledger")
cols = st.columns(len(ledger) if len(ledger) > 0 else 1)
for i, (name, balance) in enumerate(ledger.items()):
    cols[i].metric(label=name, value=f"${balance:,.2f}")

st.divider()

# --- 4. Sidebar: Add New Participant ---
with st.sidebar:
    st.header("Admin Actions")
    st.subheader("Register New Participant")
    with st.form("new_user_form", clear_on_submit=True):
        new_name = st.text_input("Name")
        starting_bal = st.number_input("Initial Deposit", min_value=0.00, step=10.00, format="%.2f")
        add_submit = st.form_submit_button("Add to Bank")
    
    if add_submit:
        if new_name and new_name not in ledger:
            ledger[new_name] = round(starting_bal, 2)
            update_ledger(ledger, sha, f"Added {new_name}")
            st.success(f"Added {new_name}!")
            st.rerun()
        else:
            st.error("Invalid name or user exists.")

# --- 5. Main: Transaction Form ---
st.subheader("Send a Payment")
with st.form("transfer_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        sender = st.selectbox("From", list(ledger.keys()))
    with col2:
        recipient = st.selectbox("To", [n for n in ledger.keys() if n != sender])
    
    amount = st.number_input("Amount ($)", min_value=0.01, step=1.00, format="%.2f")
    submit = st.form_submit_button("Confirm Transfer")

if submit:
    if ledger[sender] >= amount:
        with st.spinner("Processing..."):
            # Logic: Rounding to 2 decimals to prevent floating point errors
            ledger[sender] = round(ledger[sender] - amount, 2)
            ledger[recipient] = round(ledger[recipient] + amount, 2)

            msg = f"Transfer: {sender} sent ${amount:.2f} to {recipient}"
            try:
                update_ledger(ledger, sha, msg)
                st.balloons()
                st.success(msg)
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
    else:
        st.error(f"Insufficient funds! {sender} only has ${ledger[sender]:.2f}")

# --- 6. Transaction History ---
st.divider()
with st.expander("📜 View Transaction History"):
    st.write("Recent Activity (GitHub Logs):")
    try:
        commits = repo.get_commits(path=FILE_PATH)
        for c in commits[:5]:
            st.text(f"• {c.commit.message}")
    except:
        st.write("History unavailable.")
