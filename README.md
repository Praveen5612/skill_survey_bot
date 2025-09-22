# 🧭 Skill Survey Bot — Offline Prototype

## 📌 Overview

The **Skill Survey Bot** is a **Streamlit-based web application** designed to streamline the process of assessing employee skills, identifying skill gaps, and mapping resumes to organizational needs.

It allows **Admins** to create surveys for different business processes, assign them to users, and analyze responses through dashboards. Users can take surveys, rate their skills, and provide feedback. The dashboard aggregates all responses and even matches missing skills with resumes for better workforce planning.

This project is useful for:

- **Skill assessment in organizations**
- **Identifying skill gaps across processes**
- **Resume matching for missing or required skills**
- **HR / L\&D / Workforce planning teams**

---

## ⚙️ How It Works

The app is divided into three modes, selectable from the sidebar:

### 1. **Admin Mode**

- Admins can create new surveys by:

  - Selecting a **business process** (e.g., Order to Cash, Procure to Pay, etc.)
  - Viewing process description
  - Defining **required skills** (auto-suggested but editable)
  - Adding **survey questions**
  - Assigning surveys to users (from `users.csv`)

- Admins can also manage existing surveys:

  - View details
  - Delete surveys
  - Manage assignments and responses

### 2. **User Mode**

- Users log in by selecting their email (from `users.csv`)
- They see surveys assigned to them
- For each survey:

  - Select which skills they have
  - Rate themselves (High, Medium, Low) on each skill
  - Answer open-ended questions
  - Provide general comments

- Responses are saved to `data.json`

### 3. **Dashboard Mode**

- Admins can analyze all survey responses:

  - View responses per user
  - Aggregate skill ratings (High/Medium/Low counts)
  - Compare **required vs available skills**
  - Identify **missing skills**

- Resume matching:

  - For missing skills, scans resumes (`resumes/` folder with `.txt` files)
  - Suggests candidate resumes containing those skills

- Export responses to CSV for reporting or further analysis

---

## 📂 Project Structure

```
skill_survey_bot/
│
├── app.py                # Main Streamlit app
├── processes.xlsx        # Stores process definitions
├── users.csv             # Stores user info (ID, Name, Email, Role)
├── resumes/              # Folder for resumes (.txt files)
├── data.json             # Persistent storage for surveys, responses, assignments
├── requirements.txt      # Python dependencies
```

---

## 📊 Data Flow

1. **Processes** → Defined in `processes.xlsx`
2. **Users** → Defined in `users.csv`
3. **Admin** → Creates surveys linked to processes and skills
4. **Assignments** → Stored in `data.json` (maps survey_id → users)
5. **Responses** → Stored in `data.json` (per survey_id)
6. **Dashboard** → Reads responses + resumes for analysis

---

## 🛠️ Installation & Running

### 1. Clone the project

```bash
git clone <your-repo-url>
cd skill_survey_bot
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
.\venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at: [http://localhost:8501](http://localhost:8501)

---

## 📦 Requirements

Create a `requirements.txt` with:

```
streamlit
pandas
openpyxl
```

---

## 🚀 Use Cases

- **HR departments**: Assess workforce skills & identify training needs
- **Project managers**: Match employee skills to project requirements
- **Learning & Development**: Design targeted training programs
- **Recruitment teams**: Quickly match resumes to missing skills

---

## ✅ Future Enhancements

- Add **user authentication** (instead of dropdown emails)
- Use **NLP-based skill extraction** from resumes
- Enable **survey scheduling & notifications**
- Integrate with **databases (PostgreSQL/MySQL)** instead of local JSON
- Add **visual charts** for better insights
