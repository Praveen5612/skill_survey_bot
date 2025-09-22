# app.py
import logging
import sys
import streamlit as st

class IgnoreScriptRunContextFilter(logging.Filter):
    def filter(self, record):
        return "missing ScriptRunContext" not in record.getMessage()

f = IgnoreScriptRunContextFilter()

# Attach filter to root logger, common streamlit loggers, and any existing handlers
logging.getLogger().addFilter(f)
for name in ("streamlit", "streamlit.runtime", "streamlit.runtime.scriptrunner"):
    logging.getLogger(name).addFilter(f)
for h in logging.getLogger().handlers:
    h.addFilter(f)

# ensure a handler exists early so handler-level filters apply
if not logging.getLogger().handlers:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

import streamlit as st
import pandas as pd
import os
import json
import uuid
from typing import List, Dict



# -------------------------
# Config / file paths
# -------------------------
PROCESS_FILE = "processes.xlsx"
USER_FILE = "users.csv"
RESUME_FOLDER = "resumes"
DATA_FILE = "data.json"



# -------------------------
# Helper functions
# -------------------------
def safe_read_processes():
    if not os.path.exists(PROCESS_FILE):
        return pd.DataFrame(columns=["ProcessID", "ProcessName", "Description", "Industry"])
    return pd.read_excel(PROCESS_FILE)

def safe_read_users():
    if not os.path.exists(USER_FILE):
        return pd.DataFrame(columns=["UserID", "Name", "Email", "Role"])
    return pd.read_csv(USER_FILE)

def load_resumes_texts():
    resumes = {}
    if not os.path.exists(RESUME_FOLDER):
        return resumes
    for f in os.listdir(RESUME_FOLDER):
        if f.lower().endswith(".txt"):
            try:
                with open(os.path.join(RESUME_FOLDER, f), "r", encoding="utf-8") as fh:
                    resumes[f] = fh.read()
            except Exception:
                resumes[f] = ""
    return resumes

def load_datafile() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_datafile(payload: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def ensure_data_structure():
    d = load_datafile()
    changed = False
    if "surveys" not in d:
        d["surveys"] = {}
        changed = True
    if "responses" not in d:
        d["responses"] = {}
        changed = True
    if "assignments" not in d:
        d["assignments"] = {}  # survey_id -> list of emails
        changed = True
    if changed:
        save_datafile(d)
    return d

def generate_survey_id():
    return str(uuid.uuid4())[:8]

def suggest_skills_for_process(process_name: str) -> List[str]:
    # Simple static suggestions for demo. Extend as needed.
    # Keep short list to let admin edit.
    mapping = {
        "Order to Cash": ["Order Processing", "Invoicing", "Accounts Receivable", "SAP"],
        "Procure to Pay": ["Procurement", "Supplier Management", "PO Processing", "SAP"],
        "Hire to Retire": ["Recruitment", "Payroll", "Onboarding", "Employee Relations"],
        "Record to Report": ["Financial Reporting", "Reconcilations", "Excel", "Accounting"],
        "Incident Management": ["Incident Triage", "Troubleshooting", "Ticketing Systems"],
        "Inventory Management": ["Stock Control", "Cycle Count", "ERP", "Logistics"],
        "Data Migration": ["ETL", "Data Mapping", "SQL", "Python"],
        "Network Security": ["Firewalls", "IDS/IPS", "Vulnerability Management"],
        "Event Management": ["Venue Management", "Vendor Coordination", "Logistics"],
    }
    # return specific if found, else a generic list
    for k, v in mapping.items():
        if k.lower() in process_name.lower():
            return v
    return ["Communication", "Process Knowledge", "Documentation", "Tools"]




def extract_skills_from_text(text: str) -> List[str]:
    # naive extractor: looks for comma-separated "Skills:" line or picks capitalized words heuristically
    lines = text.splitlines()
    for ln in lines:
        if "skills:" in ln.lower():
            # split on ":" then on commas
            parts = ln.split(":", 1)[1]
            skills = [s.strip() for s in parts.split(",") if s.strip()]
            return skills
    # fallback: return some tokens (very naive)
    tokens = set()
    words = text.split()
    for w in words:
        # heuristics: words with length 3-20 and titlecase (start uppercase)
        if w.istitle() and len(w) > 2 and len(w) < 20:
            tokens.add(w.strip().strip(",.()"))
    return list(tokens)[:8]

def match_resumes_for_skill(skill: str, resumes: Dict[str, str]) -> List[str]:
    matches = []
    skill_lower = skill.lower()
    for fname, text in resumes.items():
        if skill_lower in text.lower():
            matches.append(fname)
    return matches






# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Skill Survey Bot (Prototype)", layout="wide")
st.title("🧭 Skill Survey Bot — Offline Prototype")

# load data sources
processes_df = safe_read_processes()
users_df = safe_read_users()
resumes = load_resumes_texts()
data = ensure_data_structure()

# Sidebar role switch
role = st.sidebar.selectbox("Choose Mode", ["Admin", "User", "Dashboard"])





# -------------------------
# Admin View
# -------------------------
if role == "Admin":
    st.header("Admin — Create & Manage Surveys")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Create a new survey")
        proc_choice = st.selectbox("Select process", options=processes_df["ProcessName"].tolist() if not processes_df.empty else [])
        proc_row = processes_df[processes_df["ProcessName"] == proc_choice]
        st.markdown("**Process description:**")
        if not proc_row.empty:
            st.info(proc_row.iloc[0]["Description"])
        # suggested skills
        suggested = suggest_skills_for_process(proc_choice) if proc_choice else []
        st.write("Suggested skills (edit/add as needed):")
        skills_input = st.text_area("Skills (comma separated)", value=", ".join(suggested))
        skills = [s.strip() for s in skills_input.split(",") if s.strip()]

        st.write("Define questions for the survey (one per line):")
        default_qs = "How confident are you performing this process step?\nAny blockers or comments?"
        questions_input = st.text_area("Questions (one per line)", value=default_qs, height=120)
        questions = [q.strip() for q in questions_input.splitlines() if q.strip()]

        st.write("Select users to assign the survey:")
        user_emails = users_df["Email"].tolist() if not users_df.empty else []
        selected_emails = st.multiselect("Users (emails)", options=user_emails)

        if st.button("Create & Save Survey"):
            if not proc_choice:
                st.error("Please select a process.")
            elif not skills:
                st.error("Please provide at least one skill.")
            else:
                sid = generate_survey_id()
                survey = {
                    "survey_id": sid,
                    "process": proc_choice,
                    "process_id": int(proc_row.iloc[0]["ProcessID"]) if not proc_row.empty and "ProcessID" in proc_row.columns else None,
                    "skills": skills,
                    "questions": questions,
                    "creator": "admin",
                }
                data = load_datafile()
                data.setdefault("surveys", {})[sid] = survey
                data.setdefault("assignments", {})[sid] = selected_emails
                save_datafile(data)
                st.success(f"Survey created: {sid}")
                st.write("Assigned to:", selected_emails if selected_emails else "No users assigned yet.")

    with col2:
        st.subheader("Existing Surveys")
        surveys = load_datafile().get("surveys", {})
        if not surveys:
            st.info("No surveys created yet.")
        else:
            for sid, s in surveys.items():
                with st.expander(f"{s.get('process')} — {sid}"):
                    st.write("Skills:", s.get("skills", []))
                    st.write("Questions:", s.get("questions", []))
                    st.write("Assigned to:", load_datafile().get("assignments", {}).get(sid, []))
                    if st.button(f"Delete {sid}", key=f"del_{sid}"):
                        d = load_datafile()
                        d["surveys"].pop(sid, None)
                        d.get("assignments", {}).pop(sid, None)
                        # remove responses for that survey
                        d.get("responses", {}).pop(sid, None)
                        save_datafile(d)
                        st.experimental_rerun()






# -------------------------
# User View
# -------------------------
elif role == "User":
    st.header("User — Take Survey")
    st.info("Login using your email from users.csv. Select from the dropdown to simulate real login.")

    email = st.selectbox("Select your email", options=users_df["Email"].tolist() if not users_df.empty else [])
    user_row = users_df[users_df["Email"] == email]
    user_name = user_row.iloc[0]["Name"] if not user_row.empty else "Guest"

    st.write(f"Logged in as: **{user_name}** ({email})")

    # fetch assigned surveys
    all_data = load_datafile()
    assigned = []
    for sid, emails in all_data.get("assignments", {}).items():
        if email in emails:
            assigned.append((sid, all_data["surveys"][sid]))

    if not assigned:
        st.info("No surveys assigned to you.")
    else:
        for sid, survey in assigned:
            with st.form(key=f"form_{sid}"):
                st.subheader(f"Survey: {survey.get('process')}  —  ID: {sid}")
                st.write("Skills (select the ones you have):")
                skill_options = survey.get("skills", [])
                chosen_skills = st.multiselect("Select your skills", options=skill_options, key=f"skills_{sid}")

                st.write("Rate your level for each selected skill:")
                skill_ratings = {}
                for skl in chosen_skills:
                    skill_ratings[skl] = st.radio(f"{skl} level", options=["High", "Medium", "Low"], key=f"rate_{sid}_{skl}")

                responses = {}
                for i, q in enumerate(survey.get("questions", []), start=1):
                    responses[f"q{i}"] = st.text_area(q, key=f"q_{sid}_{i}")

                comments = st.text_area("General comments (optional)", key=f"comments_{sid}")

                submitted = st.form_submit_button("Submit Survey")
                if submitted:
                    d = load_datafile()
                    d.setdefault("responses", {})
                    d["responses"].setdefault(sid, [])
                    entry = {
                        "respondent_email": email,
                        "respondent_name": user_name,
                        "skills_selected": chosen_skills,
                        "skill_ratings": skill_ratings,
                        "answers": responses,
                        "comments": comments,
                        "timestamp": pd.Timestamp.now().isoformat(),
                    }
                    d["responses"][sid].append(entry)
                    save_datafile(d)
                    st.session_state[f"submitted_{sid}"] = True
                    st.experimental_rerun()

                # Show success message if just submitted
                if st.session_state.get(f"submitted_{sid}", False):
                    st.success("Response saved. Thank you!")
                    # Optionally clear the flag so it doesn't show on next rerun
                    st.session_state[f"submitted_{sid}"] = False



# -------------------------
# Dashboard View
# -------------------------
elif role == "Dashboard":
    st.header("Dashboard — Responses, Analysis & Resume Matching")
    d = load_datafile()
    surveys = d.get("surveys", {})
    responses = d.get("responses", {})
    assignments = d.get("assignments", {})

    if not surveys:
        st.info("No surveys available. Create one in Admin.")
    else:
        sel_sid = st.selectbox("Select survey", options=list(surveys.keys()), format_func=lambda x: f"{surveys[x]['process']} — {x}" if x else "")
        if sel_sid:
            survey = surveys[sel_sid]
            st.subheader(f"Survey: {survey['process']} — {sel_sid}")
            st.write("Skills required:", survey.get("skills", []))
            st.write("Assigned users:", assignments.get(sel_sid, []))

            resp_list = responses.get(sel_sid, [])
            st.write(f"Total responses: {len(resp_list)}")
            if resp_list:
                for i, r in enumerate(resp_list, start=1):
                    with st.expander(f"{i}. {r.get('respondent_name')} ({r.get('respondent_email')}) - {r.get('timestamp')[:19]}"):
                        st.write("Skills selected:", r.get("skills_selected"))
                        st.write("Skill ratings:", r.get("skill_ratings"))
                        st.write("Answers:", r.get("answers"))
                        st.write("Comments:", r.get("comments"))

            # Simple skill aggregation
            st.markdown("### Skill aggregation")
            skill_map = {}
            for r in resp_list:
                for skl in r.get("skills_selected", []):
                    rating = r.get("skill_ratings", {}).get(skl, "Low")
                    skill_map.setdefault(skl, []).append(rating)

            if skill_map:
                rows = []
                for skl, ratings in skill_map.items():
                    high = ratings.count("High")
                    med = ratings.count("Medium")
                    low = ratings.count("Low")
                    rows.append({"Skill": skl, "High": high, "Medium": med, "Low": low, "Total": len(ratings)})
                st.table(pd.DataFrame(rows))

            # Gap analysis
            st.markdown("### Gap Analysis (required vs available)")
            required = set([s.lower() for s in survey.get("skills", [])])
            available = set([s.lower() for s in skill_map.keys()])
            missing = required - available
            st.write("Missing skills (not selected by anyone):", list(missing) if missing else "None")

            # Resume matching for missing skills
            if missing:
                st.markdown("### Resume matching suggestions for missing skills")
                resume_texts = load_resumes_texts()
                for ms in missing:
                    matches = match_resumes_for_skill(ms, resume_texts)
                    st.write(f"Skill: **{ms}** — Matches: {len(matches)}")
                    if matches:
                        for m in matches:
                            with st.expander(m):
                                st.text(resume_texts[m][:500] + ("..." if len(resume_texts[m]) > 500 else ""))
                    else:
                        # fallback: try fuzzy extracting by tokenizing resumes
                        suggestions = []
                        for fname, txt in resume_texts.items():
                            extracted = [x.lower() for x in extract_skills_from_text(txt)]
                            if ms in extracted:
                                suggestions.append(fname)
                        if suggestions:
                            st.write("Fallback matches (skill tokens):", suggestions)
                        else:
                            st.write("No matches found in resumes folder.")

            # Option: export survey responses to CSV
            if st.button("Export responses to CSV"):
                if resp_list:
                    export_rows = []
                    for r in resp_list:
                        base = {
                            "respondent_email": r.get("respondent_email"),
                            "respondent_name": r.get("respondent_name"),
                            "timestamp": r.get("timestamp"),
                            "comments": r.get("comments")
                        }
                        # flatten skills & ratings
                        for skl in survey.get("skills", []):
                            base[f"has_{skl}"] = skl in r.get("skills_selected", [])
                            base[f"rating_{skl}"] = r.get("skill_ratings", {}).get(skl)
                        # add answers
                        for k, v in r.get("answers", {}).items():
                            base[k] = v
                        export_rows.append(base)
                    export_df = pd.DataFrame(export_rows)
                    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download CSV", data=csv_bytes, file_name=f"responses_{sel_sid}.csv", mime="text/csv")
                else:
                    st.warning("No responses yet to export.")

