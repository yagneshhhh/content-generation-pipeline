import streamlit as st
import requests
import re
from langchain_groq import ChatGroq

# ---------------- CONFIG ----------------
AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

# ---------------- FUNCTIONS ----------------

def fetch_pending_records():
    params = {
        "filterByFormula": "{Status}='Pending'"
    }
    res = requests.get(BASE_URL, headers=HEADERS, params=params)
    res.raise_for_status()
    return res.json().get("records", [])

def generate_blog_post(brief):
    prompt = f"""
    You are a professional content writer.
    Write a detailed blog post based on the following brief:

    "{brief}"

    The post should be engaging, informative, and suitable for a tech-savvy audience.
    """
    return llm.invoke(prompt).content

def correct_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    data = {"text": text, "language": "en-US"}
    res = requests.post(url, data=data)
    res.raise_for_status()

    matches = sorted(res.json().get("matches", []),
                     key=lambda m: m["offset"],
                     reverse=True)

    corrected = text
    for m in matches:
        if m["replacements"]:
            start = m["offset"]
            end = start + m["length"]
            corrected = corrected[:start] + m["replacements"][0]["value"] + corrected[end:]
    return corrected

def restructure_content(text):
    text = re.sub(r"(\n)(\d+)\. ([^\n]+)", r"\1### \2. \3\n", text)

    paragraphs = text.split("\n\n")
    final_paras = []

    for para in paragraphs:
        sentences = re.split(r'(?<=[.!?]) +', para)
        for i in range(0, len(sentences), 3):
            final_paras.append(" ".join(sentences[i:i+3]))

    return "\n\n".join(final_paras)

def update_record(record_id, fields):
    url = f"{BASE_URL}/{record_id}"
    res = requests.patch(url, headers=HEADERS, json={"fields": fields})
    res.raise_for_status()

# ---------------- UI ----------------

st.set_page_config(page_title="Automated Content Pipeline", layout="wide")

st.title("🧠 Automated Content Generation Pipeline")

st.markdown("""
This app fetches **pending topics from Airtable**, generates content using an LLM,
validates it, and updates the workflow state automatically.
""")

# Session state
if "records" not in st.session_state:
    st.session_state.records = []

# -------- Fetch Button --------
if st.button("📥 Fetch Pending Topics"):
    st.session_state.records = fetch_pending_records()
    st.success(f"Fetched {len(st.session_state.records)} pending topics")

# -------- Display Topics --------
if st.session_state.records:
    st.subheader("📌 Pending Topics")

    for rec in st.session_state.records:
        topic_name = rec["fields"].get("Topic", "Untitled Topic")

        with st.expander(f"Topic: {topic_name}"):
            st.write(rec["fields"].get("Brief", "No brief available"))

# -------- Generate Content --------
if st.session_state.records:
    if st.button("⚙️ Generate Content"):
        for rec in st.session_state.records:
            brief = rec["fields"].get("Brief")
            if not brief:
                continue

            with st.spinner("Generating content..."):
                raw = generate_blog_post(brief)
                corrected = correct_grammar(raw)
                final_content = restructure_content(corrected)

                update_record(
                    rec["id"],
                    {
                        "Status": "Ready To Publish",
                        "Generated Content": final_content
                    }
                )

                st.success(f"Generated & updated content for {rec['id']}")

# -------- Zapier Section --------
st.divider()
st.subheader("🔗 Publish via Zapier")

st.markdown("""
**Zapier Workflow Template **  

🔗 **https://zapier.com/editor/336352609/published/336352609/fields**

### How to  use this Zapier template:
1. Open the link
2. Click **“Try this Zap”**
3. Connect your own Airtable & social accounts
4. change the social platform of your liking for posting the data generated
5. Publish content automatically

⚠️ the automation runs  **inside your  own Zapier account**
""")
