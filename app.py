from __future__ import annotations
import io
import re
import pandas as pd
import streamlit as st
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Resume Analyzer",
    layout="wide"
)

# --- GLOBAL SKILLS DATABASE ---
skills_db = {
    "Data Scientist": ["Python", "Machine Learning", "Sql", "Pandas", "Numpy", "Statistics", "Scikit-Learn", "Deep Learning", "Nlp", "Tableau"],
    "Software Engineer": ["Java", "Python", "Git", "Aws", "Docker", "Algorithms", "Data Structures", "Ci/Cd", "Api", "Rest"],
    "Frontend Developer": ["Html", "Css", "Javascript", "React", "Vue", "Typescript", "Tailwind", "Figma", "Sass", "Php", "Jquery", "Web Developer", "Ui", "Ux"],
    "Backend Engineer": ["Node.js", "Django", "Flask", "Postgresql", "Apis", "Mongodb", "Redis", "Graphql", "Docker", "Express", "Sequelize", "Mysql"],
    "Data Analyst": ["Excel", "Sql", "Tableau", "Power BI", "Python", "Statistics", "Cleaning", "Reporting"],
    "Machine Learning Engineer": ["Pytorch", "Tensorflow", "Mlops", "Neural Networks", "Opencv", "Scipy", "Keras"],
    "Business Analyst": ["Jira", "Agile", "Scrum", "Requirements", "Stakeholder", "Visio", "Documentation"],
    "Product Manager": ["Roadmap", "Strategy", "User Stories", "Kpis", "Agile", "Ux Design", "Market Research"]
}

# --- Advanced CSS (Merged from earlier UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@900&display=swap');
    
    .stApp { background-color: #0E1117; color: #F9FAFB; }
    
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 6.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #2DD4BF, #38BDF8, #4ADE80);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 20px;
    }

    .step-container {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 15px;
        padding: 25px;
        height: 280px;
        transition: transform 0.3s ease;
    }
    
    .step-container:hover {
        transform: translateY(-5px);
        border-color: #10B981;
    }

    .step-number {
        background: #10B981;
        color: white;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 15px;
    }

    .metric-card {
        background: #111827;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #1F2937;
        border-left: 5px solid #10B981;
        text-align: center;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #10B981, #06B6D4) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Extraction Logic ---
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def extract_text(uploaded_file):
    ext = uploaded_file.name.lower().split(".")[-1]
    file_bytes = uploaded_file.getvalue()
    text = ""
    try:
        if ext == "pdf" and PdfReader:
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text += (page.extract_text() or "") + " "
        elif ext == "docx" and DocxDocument:
            doc = DocxDocument(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            text = file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text

def analyze_locally(text, role):
    # Character-stream normalization (mushed version for 100% detection)
    text_mushed = "".join(text.lower().split())
    
    target_skills = skills_db.get(role, [])
    found_skills = []
    
    for skill in target_skills:
        skill_to_find = skill.lower().replace(".", "") # node.js -> nodejs
        if skill_to_find in text_mushed:
            found_skills.append(skill)
    
    # Scoring: 70% Skill Match, 30% Experience Markers
    skill_score = int((len(found_skills) / len(target_skills)) * 100) if target_skills else 0
    exp_markers = ["intern", "experience", "developed", "project", "express", "node", "php"]
    exp_count = sum(1 for m in exp_markers if m in text_mushed)
    exp_score = min(100, int((exp_count / 3) * 100))
    
    overall_score = int((skill_score * 0.7) + (exp_score * 0.3))
    missing = [s for s in target_skills if s not in found_skills]
    
    return {
        "score": overall_score,
        "skills": found_skills,
        "breakdown": {"Skills Match": skill_score, "Experience Markers": exp_score},
        "suggestions": [
            f"Key Missing Skills: {', '.join(missing[:3])}" if missing else "Perfect skill alignment!",
            "Utilizing character-stream scanning to ensure high detection accuracy.",
            "Analyze focused on technical keyword density and role compatibility."
        ]
    }

# --- UI Rendering ---
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

if st.session_state.analysis is None:
    st.markdown("<h1 class='hero-title'>Smart Resume Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""<div class='step-container'>
            <div class='step-number'>1</div>
            <h3>Target Role</h3>
            <p>Select the specific career path you want to evaluate your resume against.</p>
        </div>""", unsafe_allow_html=True)
        target_role = st.selectbox("Choose Role:", options=sorted(list(skills_db.keys())), label_visibility="collapsed")
        
    with col2:
        st.markdown("""<div class='step-container'>
            <div class='step-number'>2</div>
            <h3>Upload File</h3>
            <p>Upload your latest resume in PDF or DOCX format for processing.</p>
        </div>""", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload:", type=["pdf", "docx"], label_visibility="collapsed")
        
    with col3:
        st.markdown("""<div class='step-container'>
            <div class='step-number'>3</div>
            <h3>Get Result</h3>
            <p>Run the analysis to see your match percentage and detected skills.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Analyze Resume"):
            if uploaded_file:
                resume_text = extract_text(uploaded_file)
                st.session_state.analysis = analyze_locally(resume_text, target_role)
                st.rerun()
            else: st.warning("Upload a file first!")
else:
    res = st.session_state.analysis
    st.markdown("<h1><span style='color:#10B981'>Analysis</span> Dashboard</h1>", unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    with m1: 
        st.markdown(f"<div class='metric-card'><h4>Overall Fit Score</h4><h2 style='color:#10B981'>{res['score']}%</h2></div>", unsafe_allow_html=True)
    with m2: 
        st.markdown(f"<div class='metric-card'><h4>Matches Detected</h4><h2 style='color:#10B981'>{len(res['skills'])} Keywords</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📊 Stats", "🛠️ Identified Skills", "💡 Suggestions"])
    
    with t1:
        df = pd.DataFrame(list(res['breakdown'].items()), columns=['Category', 'Score'])
        st.plotly_chart(px.bar(df, x='Category', y='Score', template="plotly_dark"), use_container_width=True)
        
    with t2:
        if res['skills']:
            cols = st.columns(4)
            for i, s in enumerate(res['skills']): cols[i % 4].success(s)
        else: 
            st.error("No matches found for the selected role.")
            
    with t3:
        for suggestion in res['suggestions']:
            st.info(f"👉 {suggestion}")

    if st.button("Reset Analysis"):
        st.session_state.analysis = None
        st.rerun()