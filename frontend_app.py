import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", API_BASE_URL)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "davschool123")
CONTACT_NUMBER = os.getenv("CONTACT_NUMBER", "Contact number not configured")


@st.cache_data
def fetch_json(url: str):
    response = requests.get(url, timeout=20)
    if response.status_code >= 400:
        raise ValueError(f"API request failed: {response.text}")
    return response.json()


def refresh_after_change():
    fetch_json.clear()
    st.rerun()


def upload_file(url: str, files: Dict[str, Any], data: Dict[str, str]):
    try:
        return requests.post(url, files=files, data=data, timeout=60)
    except requests.exceptions.RequestException as error:
        st.error(f"Backend se connection nahi ho paaya: {error}")
        return None


def render_info_card(title: str, value: str, accent: str = "#1d5ec9"):
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {accent} 0%, #0b3d91 100%); border-radius: 16px; padding: 18px 20px; color: white; box-shadow: 0 10px 24px rgba(11,61,145,0.15); margin-bottom: 14px;">
            <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.8;">{title}</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-top: 8px;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_python_editor():
    st.subheader("Python Code Editor")
    st.caption("Write Python code and run it directly in the browser.")
    code = st.text_area(
        "Python code",
        "print('Hello from Teaching App!')\nname = 'Student'\nprint(f'Welcome {name}')",
        height=260,
        key="student_python_code",
    )
    if st.button("Run code", key="run_student_code", use_container_width=True):
        try:
            execution_environment = os.environ.copy()
            execution_environment["MPLBACKEND"] = "Agg"
            execution_environment["PYTHONWARNINGS"] = "ignore::UserWarning"
            with tempfile.TemporaryDirectory() as output_directory:
                capture_graphics = f'''
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

output_directory = pathlib.Path({output_directory!r})
original_show = plt.show

def capture_show(*args, **kwargs):
    for figure_number in plt.get_fignums():
        figure = plt.figure(figure_number)
        figure.savefig(output_directory / f"figure_{{figure_number}}.png", dpi=150, bbox_inches="tight")
    return original_show(*args, **kwargs)

plt.show = capture_show
exec(compile(__import__("sys").stdin.read(), "student_code.py", "exec"), {{}})

for figure_number in plt.get_fignums():
    figure_path = output_directory / f"figure_{{figure_number}}.png"
    if not figure_path.exists():
        plt.figure(figure_number).savefig(figure_path, dpi=150, bbox_inches="tight")
'''
                result = subprocess.run(
                    [sys.executable, "-c", capture_graphics],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                    env=execution_environment,
                )
                figure_paths = sorted(
                    pathlib.Path(output_directory).glob("figure_*.png"),
                    key=lambda path: path.name,
                )
                for figure_path in figure_paths:
                    st.image(str(figure_path), caption=figure_path.stem.replace("_", " ").title())

            if result.stdout:
                st.code(result.stdout, language="python")
            if result.stderr:
                st.code(result.stderr, language="python")
            if not result.stdout and not result.stderr and not figure_paths:
                st.info("No output returned.")
        except subprocess.TimeoutExpired:
            st.error("Code execution timed out. Keep it short and efficient.")


def render_file_gallery(title: str, items: List[Dict[str, Any]], endpoint_prefix: str, resource_type: str):
    st.subheader(title)
    if not items:
        st.info(f"No {resource_type.lower()} available for this chapter yet.")
        return
    for item in items:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{item['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{item.get('description', '')}</div>
                <a class="resource-link" href="{PUBLIC_API_BASE_URL}{endpoint_prefix}{item['id']}/download" target="_blank" rel="noopener noreferrer">Open in browser</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.set_page_config(
    page_title="Teaching App",
    page_icon="📚",
    layout="wide",
    menu_items={
        "About": f"""
        ### Teaching App
        Teacher-DAV Public School, Sasaram

        **Contact:** {CONTACT_NUMBER}
        """,
    },
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #e9f7f2 0%, #dff1f5 48%, #d8e8f8 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b3d91 0%, #1d5ec9 100%);
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label, [data-testid="stSidebar"] .stButton button {
        color: white !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px;
    }
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="tag"] {
        background: rgba(255,255,255,0.1);
    }
    .teacher-box {
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 12px;
        padding: 14px 12px;
        margin-bottom: 12px;
        color: white;
        font-weight: 700;
    }
    .header-card {
        background: linear-gradient(135deg, #0b5ed7 0%, #0a3d91 100%);
        border-radius: 18px;
        padding: 22px 24px;
        box-shadow: 0 10px 25px rgba(11, 61, 145, 0.22);
        margin-bottom: 18px;
    }
    .header-card h1 {
        margin: 0;
        font-size: 2.2rem;
        color: white;
        font-weight: 700;
    }
    .header-card .subhead {
        margin-top: 6px;
        font-size: 1.1rem;
        color: #eaf4ff;
        letter-spacing: 0.04em;
    }
    .student-card {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(17, 76, 146, 0.12);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 22px rgba(23, 64, 124, 0.12);
        margin-bottom: 16px;
    }
    .stTabs [role="tablist"] {
        background: #e7f0ff;
        border-radius: 12px;
        padding: 6px;
        box-shadow: inset 0 1px 2px rgba(17, 76, 146, 0.08);
    }
    .stTabs [role="tab"] {
        color: #12325b !important;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }
    .stTabs [role="tab"] p {
        color: #12325b !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #12325b !important;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        color: #12325b !important;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: #1769d1;
        color: #ffffff !important;
    }
    .stTabs [role="tab"][aria-selected="true"] p {
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab"][aria-selected="true"] span,
    .stTabs [data-baseweb="tab"][aria-selected="true"] div {
        color: #ffffff !important;
    }
    .stTabs [role="tab"]:hover {
        background: #c8ddff;
        color: #0b3d91 !important;
    }
    .content-card {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(13, 70, 160, 0.12);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 22px rgba(23, 64, 124, 0.08);
        margin-bottom: 16px;
    }
    .resource-link {
        display: inline-block;
        background: linear-gradient(135deg, #0b5ed7, #0a3d91);
        color: white !important;
        text-decoration: none !important;
        border-radius: 10px;
        padding: 0.7rem 1.1rem;
        font-weight: 600;
        margin-top: 10px;
    }
    .question-box {
        border-left: 4px solid #1d5ec9;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        background: rgba(28, 94, 201, 0.04);
        margin-top: 0.8rem;
    }
    .answer-pill {
        display: inline-block;
        background: rgba(39, 174, 96, 0.12);
        color: #1d7b3d;
        border-radius: 999px;
        padding: 0.25rem 0.7rem;
        font-weight: 600;
        margin-top: 0.6rem;
    }
    @media (max-width: 640px) {
        [data-testid="stAppViewContainer"] > .main {
            padding: 0 0.65rem 1rem;
        }
        [data-testid="stSidebar"] {
            min-width: 82vw;
            max-width: 82vw;
        }
        .header-card {
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .header-card h1 {
            font-size: 1.55rem;
        }
        .header-card .subhead {
            font-size: 0.9rem;
        }
        .student-card, .content-card {
            border-radius: 12px;
            padding: 13px;
        }
        .stTabs [role="tablist"] {
            gap: 0.15rem;
            overflow-x: auto;
            flex-wrap: nowrap;
        }
        .stTabs [role="tab"] {
            flex: 0 0 auto;
            padding: 0.5rem 0.65rem;
            font-size: 0.82rem;
        }
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header-card">
        <h1>Teaching App</h1>
        <div class="subhead">Teacher-DAV Public School, Sasaram</div>
    </div>
    """,
    unsafe_allow_html=True,
)

teacher_mode = st.session_state.get("teacher_mode", False)

with st.sidebar:
    st.markdown("<div class='teacher-box'>Teacher / Admin Access</div>", unsafe_allow_html=True)
    st.caption("Enter password to unlock the admin panel.")
    if not teacher_mode:
        with st.form("teacher_login_form"):
            password = st.text_input("Admin password", type="password", key="teacher_password")
            submitted = st.form_submit_button("Login as teacher")
            if submitted:
                if password == ADMIN_PASSWORD:
                    st.session_state.teacher_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Use: davschool123")
    else:
        st.success("Teacher mode enabled")
        if st.button("Logout"):
            st.session_state.teacher_mode = False
            st.session_state.pop("teacher_password", None)
            st.rerun()

    st.header("Menu")
    try:
        classes = fetch_json(f"{API_BASE_URL}/api/classes")
    except Exception as exc:  # pragma: no cover
        st.error(f"Could not connect to API: {exc}")
        st.stop()

    if not classes:
        st.info("No class found yet. Add a class from teacher mode.")
        st.stop()

    class_names = {item["id"]: item["name"] for item in classes}
    selected_class = st.selectbox("Class", options=list(class_names.keys()), format_func=lambda v: class_names[v])

    subjects = fetch_json(f"{API_BASE_URL}/api/classes/{selected_class}/subjects")
    if not subjects:
        subject_names = {}
        selected_subject = None
        st.info("No subject found for this class. Use Admin > Subject to add one.")
    else:
        subject_names = {item["id"]: item["name"] for item in subjects}
        selected_subject = st.selectbox("Subject", options=list(subject_names.keys()), format_func=lambda v: subject_names[v])

    if selected_subject:
        chapters = fetch_json(f"{API_BASE_URL}/api/subjects/{selected_subject}/chapters")
    else:
        chapters = []
    if not chapters:
        chapter_names = {}
        selected_chapter = None
        st.info("No chapter found for this subject. Use Admin > Chapter to add one.")
    else:
        chapter_names = {item["id"]: item["title"] for item in chapters}
        selected_chapter = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v])

    st.caption("Student portal")

if not selected_class or (not selected_subject and not teacher_mode) or (not selected_chapter and not teacher_mode):
    st.warning("Please select a class, subject, and chapter.")
    st.stop()

notes = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/notes") if selected_chapter else []
worksheets = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/worksheets") if selected_chapter else []
homework_assignments = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/homework-assignments") if selected_chapter else []
practice_sets = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/practice-sets") if selected_chapter else []
question_papers = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/question-papers") if selected_chapter else []
books = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/books") if selected_chapter else []
videos = fetch_json(f"{API_BASE_URL}/api/chapters/{selected_chapter}/videos") if selected_chapter else []

if teacher_mode:
    admin_tab, notes_tab, practice_tab, qp_tab, books_tab, videos_tab, python_tab = st.tabs(["Admin", "Notes", "Practice", "Question Papers", "Books", "Videos", "Python Editor"])
else:
    notes_tab, practice_tab, qp_tab, books_tab, videos_tab, python_tab = st.tabs(["Notes", "Practice", "Question Papers", "Books", "Videos", "Python Editor"])

if teacher_mode:
    with admin_tab:
        st.subheader("Admin content manager")
        admin_action = st.selectbox(
            "Choose content",
            ["Class", "Subject", "Chapter", "Notes", "Video", "Worksheet", "Homework Assignment", "Question Paper", "Book"],
            key="admin_action",
        )
        admin_operation = st.selectbox(
            "Choose action",
            ["Create / Upload", "Delete"] if admin_action == "Book" else ["Create / Upload", "Delete", "Update existing"],
            key="admin_operation",
        )

        if admin_operation == "Create / Upload":
            if admin_action == "Class":
                with st.form("menu_create_class"):
                    name = st.text_input("Class name")
                    description = st.text_area("Description")
                    if st.form_submit_button("Create class") and name:
                        response = requests.post(f"{API_BASE_URL}/api/classes", json={"name": name, "description": description or None})
                        if response.ok:
                            st.success("Class created.")
                            refresh_after_change()
                        else:
                            st.error(response.text)
            elif admin_action == "Subject":
                with st.form("menu_create_subject"):
                    name = st.text_input("Subject name")
                    class_id = st.selectbox("Assign to class", list(class_names), format_func=lambda item_id: class_names[item_id])
                    if st.form_submit_button("Create subject") and name:
                        response = requests.post(f"{API_BASE_URL}/api/subjects", json={"name": name, "class_id": int(class_id)})
                        if response.ok:
                            st.success("Subject created and assigned to class.")
                            refresh_after_change()
                        else:
                            st.error(response.text)
            elif admin_action == "Chapter":
                with st.form("menu_create_chapter"):
                    title = st.text_input("Chapter title")
                    description = st.text_area("Description")
                    subject_id = st.selectbox("Assign to subject", list(subject_names), format_func=lambda item_id: subject_names[item_id])
                    if st.form_submit_button("Create chapter") and title:
                        response = requests.post(f"{API_BASE_URL}/api/chapters", json={"title": title, "description": description or None, "subject_id": int(subject_id)})
                        if response.ok:
                            st.success("Chapter created and assigned to subject.")
                            refresh_after_change()
                        else:
                            st.error(response.text)
            elif admin_action == "Notes":
                with st.form("menu_create_note"):
                    title = st.text_input("Note title")
                    link = st.text_input("Note link")
                    description = st.text_area("Description")
                    uploaded_note = st.file_uploader("Upload note page", type=["pdf", "doc", "docx", "ppt", "pptx", "txt", "jpg", "jpeg", "png"])
                    chapter_id = st.selectbox("Assign to chapter", list(chapter_names), format_func=lambda item_id: chapter_names[item_id])
                    if st.form_submit_button("Add note") and title and (link or uploaded_note):
                        if uploaded_note:
                            files = {"file": (uploaded_note.name, uploaded_note.getvalue(), uploaded_note.type or "application/octet-stream")}
                            data = {"title": title, "description": description or "", "chapter_id": str(int(chapter_id))}
                            response = requests.post(f"{API_BASE_URL}/api/notes/upload", files=files, data=data)
                        else:
                            response = requests.post(f"{API_BASE_URL}/api/notes", json={"title": title, "description": description or None, "link": link, "chapter_id": int(chapter_id)})
                        if response.ok:
                            st.success("Note assigned to chapter.")
                            refresh_after_change()
                        else:
                            st.error(response.text)
            elif admin_action == "Video":
                with st.form("menu_create_video"):
                    title = st.text_input("Video title")
                    link = st.text_input("Video link", placeholder="YouTube or direct MP4 URL")
                    description = st.text_area("Description")
                    chapter_id = st.selectbox("Assign to chapter", list(chapter_names), format_func=lambda item_id: chapter_names[item_id])
                    if st.form_submit_button("Add video") and title and link:
                        response = requests.post(f"{API_BASE_URL}/api/videos", json={"title": title, "description": description or None, "link": link, "chapter_id": int(chapter_id)})
                        if response.ok:
                            st.success("Video assigned to chapter.")
                            refresh_after_change()
                        else:
                            st.error(response.text)
            else:
                upload_config = {
                    "Worksheet": ("menu_upload_worksheet", "/api/worksheets", ["pdf", "doc", "docx", "ppt", "pptx", "txt", "jpg", "png"]),
                    "Homework Assignment": ("menu_upload_homework", "/api/homework-assignments", ["pdf", "doc", "docx", "txt", "jpg", "png"]),
                    "Question Paper": ("menu_upload_question_paper", "/api/question-papers", ["pdf", "doc", "docx", "txt", "jpg", "png"]),
                    "Book": ("menu_upload_book", "/api/books", ["pdf"]),
                }[admin_action]
                with st.form(upload_config[0], clear_on_submit=True):
                    title = st.text_input(f"{admin_action} title")
                    description = st.text_area("Description")
                    chapter_id = st.selectbox("Assign to chapter", list(chapter_names), format_func=lambda item_id: chapter_names[item_id])
                    uploaded_file = st.file_uploader(f"Upload {admin_action.lower()}", type=upload_config[2])
                    if st.form_submit_button(f"Upload {admin_action.lower()}") and title and uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                        data = {"title": title, "description": description or "", "chapter_id": str(int(chapter_id))}
                        response = upload_file(f"{API_BASE_URL}{upload_config[1]}", files, data)
                        if response is not None and response.ok:
                            st.success(f"{admin_action} uploaded and assigned to chapter.")
                            refresh_after_change()
                        elif response is not None:
                            st.error(response.text)
        elif admin_operation == "Delete":
            delete_config = {
                "Class": (classes, "classes", lambda item: item["name"]),
                "Subject": (subjects, "subjects", lambda item: item["name"]),
                "Chapter": (chapters, "chapters", lambda item: item["title"]),
                "Notes": (notes, "notes", lambda item: item["title"]),
                "Video": (videos, "videos", lambda item: item["title"]),
                "Worksheet": (worksheets, "worksheets", lambda item: item["title"]),
                "Homework Assignment": (homework_assignments, "homework-assignments", lambda item: item["title"]),
                "Question Paper": (question_papers, "question-papers", lambda item: item["title"]),
                "Book": (books, "books", lambda item: item["title"]),
            }[admin_action]
            items, endpoint, label = delete_config
            if items:
                item_id = st.selectbox("Select item to delete", [item["id"] for item in items], format_func=lambda value: label(next(item for item in items if item["id"] == value)), key=f"delete_menu_{admin_action}")
                if st.button(f"Delete {admin_action.lower()}", type="secondary", key=f"delete_menu_button_{admin_action}"):
                    response = requests.delete(f"{API_BASE_URL}/api/{endpoint}/{item_id}", timeout=20)
                    if response.ok:
                        st.success("Deleted successfully.")
                        refresh_after_change()
                    else:
                        st.error(response.text)
            else:
                st.info(f"No {admin_action.lower()} available for this selection.")

if teacher_mode and False:
    with admin_tab:
        st.subheader("Teacher Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("Classes", len(classes))
        col2.metric("Subjects", len(subjects))
        col3.metric("Chapters", len(chapters))

        st.markdown("### Manage Content")

        st.subheader("Add New Class")
        with st.form("new_class_form"):
            class_name = st.text_input("Class name")
            class_description = st.text_area("Class description")
            if st.form_submit_button("Create class"):
                if class_name:
                    response = requests.post(
                        f"{API_BASE_URL}/api/classes",
                        json={"name": class_name, "description": class_description or None},
                    )
                    if response.ok:
                        st.success("Class created successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Add New Subject")
        with st.form("new_subject_form"):
            subject_name = st.text_input("Subject name")
            subject_class_id = st.selectbox("Class", options=list(class_names.keys()), format_func=lambda v: class_names[v], index=0)
            if st.form_submit_button("Create subject"):
                if subject_name:
                    response = requests.post(
                        f"{API_BASE_URL}/api/subjects",
                        json={"name": subject_name, "class_id": int(subject_class_id)},
                    )
                    if response.ok:
                        st.success("Subject created successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Add New Chapter")
        with st.form("new_chapter_form"):
            chapter_title = st.text_input("Chapter title")
            chapter_description = st.text_area("Chapter description")
            chapter_subject_id = st.selectbox("Subject", options=list(subject_names.keys()), format_func=lambda v: subject_names[v], index=0)
            if st.form_submit_button("Create chapter"):
                if chapter_title:
                    response = requests.post(
                        f"{API_BASE_URL}/api/chapters",
                        json={"title": chapter_title, "description": chapter_description or None, "subject_id": int(chapter_subject_id)},
                    )
                    if response.ok:
                        st.success("Chapter created successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Add Note")
        with st.form("new_note_form"):
            note_title = st.text_input("Note title")
            note_link = st.text_input("Note link")
            note_description = st.text_area("Note description")
            note_chapter_id = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v], index=0)
            if st.form_submit_button("Create note"):
                if note_title and note_link:
                    response = requests.post(
                        f"{API_BASE_URL}/api/notes",
                        json={"title": note_title, "description": note_description or None, "link": note_link, "chapter_id": int(note_chapter_id)},
                    )
                    if response.ok:
                        st.success("Note added successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Add Practice Set")
        with st.form("new_practice_form"):
            practice_title = st.text_input("Practice title")
            practice_description = st.text_area("Practice description")
            practice_chapter_id = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v], index=0)
            practice_questions = st.text_area(
                "Practice JSON",
                '[{"question": "What is the SI unit of speed?", "options": ["m/s", "km/h", "m", "sec"], "answer": "m/s"}]',
                height=180,
            )
            if st.form_submit_button("Create practice set"):
                if practice_title and practice_questions:
                    try:
                        payload = json.loads(practice_questions)
                        response = requests.post(
                            f"{API_BASE_URL}/api/practice-sets",
                            json={
                                "title": practice_title,
                                "description": practice_description or None,
                                "chapter_id": int(practice_chapter_id),
                                "questions": payload,
                            },
                        )
                        if response.ok:
                            st.success("Practice set created successfully.")
                        else:
                            st.error(response.text)
                    except json.JSONDecodeError:
                        st.error("Practice JSON is invalid. Use valid JSON array format.")

        st.subheader("Upload Worksheet")
        with st.form("upload_worksheet_form", clear_on_submit=True):
            worksheet_title = st.text_input("Worksheet title")
            worksheet_description = st.text_area("Worksheet description")
            worksheet_chapter_id = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v], index=0)
            worksheet_file = st.file_uploader("Upload worksheet", type=["pdf", "doc", "docx", "ppt", "pptx", "txt", "jpg", "png"])
            if st.form_submit_button("Upload worksheet"):
                if worksheet_file and worksheet_title:
                    files = {"file": (worksheet_file.name, worksheet_file.getvalue(), worksheet_file.type or "application/octet-stream")}
                    data = {"title": worksheet_title, "description": worksheet_description or "", "chapter_id": str(int(worksheet_chapter_id))}
                    response = requests.post(f"{API_BASE_URL}/api/worksheets", files=files, data=data)
                    if response.ok:
                        st.success("Worksheet uploaded successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Upload Homework Assignment")
        with st.form("upload_homework_form", clear_on_submit=True):
            homework_title = st.text_input("Homework title")
            homework_description = st.text_area("Homework description")
            homework_chapter_id = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v], index=0, key="admin_homework_chapter")
            homework_file = st.file_uploader("Upload homework assignment", type=["pdf", "doc", "docx", "txt", "jpg", "png"])
            if st.form_submit_button("Upload homework assignment"):
                if homework_file and homework_title:
                    files = {"file": (homework_file.name, homework_file.getvalue(), homework_file.type or "application/octet-stream")}
                    data = {"title": homework_title, "description": homework_description or "", "chapter_id": str(int(homework_chapter_id))}
                    response = requests.post(f"{API_BASE_URL}/api/homework-assignments", files=files, data=data)
                    if response.ok:
                        st.success("Homework assignment uploaded successfully.")
                    else:
                        st.error(response.text)

        st.subheader("Upload Question Paper")
        with st.form("upload_qp_form", clear_on_submit=True):
            qp_title = st.text_input("Question paper title")
            qp_description = st.text_area("Question paper description")
            qp_chapter_id = st.selectbox("Chapter", options=list(chapter_names.keys()), format_func=lambda v: chapter_names[v], index=0, key="admin_qp_chapter")
            qp_file = st.file_uploader("Upload question paper", type=["pdf", "doc", "docx", "txt", "jpg", "png"])
            if st.form_submit_button("Upload question paper"):
                if qp_file and qp_title:
                    files = {"file": (qp_file.name, qp_file.getvalue(), qp_file.type or "application/octet-stream")}
                    data = {"title": qp_title, "description": qp_description or "", "chapter_id": str(int(qp_chapter_id))}
                    response = requests.post(f"{API_BASE_URL}/api/question-papers", files=files, data=data)
                    if response.ok:
                        st.success("Question paper uploaded successfully.")
                    else:
                        st.error(response.text)

if teacher_mode and admin_operation == "Update existing":
    st.markdown("---")
    st.subheader("Update or delete content")
    resource_type = st.selectbox(
        "Resource",
        ["Class", "Subject", "Chapter", "Note", "Video", "Practice Set"],
        key="admin_resource_type",
    )

    resource_items = {
        "Class": classes,
        "Subject": subjects,
        "Chapter": chapters,
        "Note": notes,
        "Video": videos,
        "Practice Set": practice_sets,
    }[resource_type]
    resource_labels = {
        "Class": lambda item: item["name"],
        "Subject": lambda item: item["name"],
        "Chapter": lambda item: item["title"],
        "Note": lambda item: item["title"],
        "Video": lambda item: item["title"],
        "Practice Set": lambda item: item["title"],
    }

    if not resource_items:
        st.info(f"No {resource_type.lower()} available to manage.")
    else:
        resource_ids = [item["id"] for item in resource_items]
        selected_resource_id = st.selectbox(
            f"Select {resource_type.lower()}",
            resource_ids,
            format_func=lambda item_id: resource_labels[resource_type](next(item for item in resource_items if item["id"] == item_id)),
            key=f"manage_{resource_type.lower().replace(' ', '_')}",
        )
        selected_resource = next(item for item in resource_items if item["id"] == selected_resource_id)
        endpoint = {
            "Class": "classes",
            "Subject": "subjects",
            "Chapter": "chapters",
            "Note": "notes",
            "Video": "videos",
            "Practice Set": "practice-sets",
        }[resource_type]

        with st.form(f"edit_{resource_type.lower().replace(' ', '_')}_form"):
            if resource_type == "Class":
                edit_name = st.text_input("Class name", value=selected_resource["name"])
                edit_description = st.text_area("Description", value=selected_resource.get("description") or "")
                payload = {"name": edit_name, "description": edit_description or None}
            elif resource_type == "Subject":
                edit_name = st.text_input("Subject name", value=selected_resource["name"])
                edit_class_id = st.selectbox("Class", list(class_names), index=list(class_names).index(selected_resource["class_id"]))
                payload = {"name": edit_name, "class_id": int(edit_class_id)}
            elif resource_type == "Chapter":
                edit_title = st.text_input("Chapter title", value=selected_resource["title"])
                edit_description = st.text_area("Description", value=selected_resource.get("description") or "")
                edit_subject_id = st.selectbox("Subject", list(subject_names), index=list(subject_names).index(selected_resource["subject_id"]), format_func=lambda item_id: subject_names[item_id])
                payload = {"title": edit_title, "description": edit_description or None, "subject_id": int(edit_subject_id)}
            elif resource_type == "Note":
                edit_title = st.text_input("Note title", value=selected_resource["title"])
                edit_description = st.text_area("Description", value=selected_resource.get("description") or "")
                edit_link = st.text_input("Note link", value=selected_resource["link"])
                payload = {"title": edit_title, "description": edit_description or None, "link": edit_link, "chapter_id": int(selected_resource["chapter_id"])}
            elif resource_type == "Video":
                edit_title = st.text_input("Video title", value=selected_resource["title"])
                edit_description = st.text_area("Description", value=selected_resource.get("description") or "")
                edit_link = st.text_input("Video link", value=selected_resource["link"])
                payload = {"title": edit_title, "description": edit_description or None, "link": edit_link, "chapter_id": int(selected_resource["chapter_id"])}
            else:
                edit_title = st.text_input("Practice title", value=selected_resource["title"])
                edit_description = st.text_area("Description", value=selected_resource.get("description") or "")
                edit_questions = st.text_area("Practice JSON", value=json.dumps(selected_resource["questions"]), height=180)
                payload = {"title": edit_title, "description": edit_description or None, "chapter_id": int(selected_resource["chapter_id"])}

            if st.form_submit_button("Update"):
                try:
                    if resource_type == "Practice Set":
                        payload["questions"] = json.loads(edit_questions)
                    response = requests.put(f"{API_BASE_URL}/api/{endpoint}/{selected_resource_id}", json=payload)
                    if response.ok:
                        st.success("Updated successfully.")
                        refresh_after_change()
                    else:
                        st.error(response.text)
                except (json.JSONDecodeError, requests.RequestException) as exc:
                    st.error(f"Could not update: {exc}")

        if st.button("Delete selected resource", type="secondary", key=f"delete_{resource_type.lower().replace(' ', '_')}"):
            response = requests.delete(f"{API_BASE_URL}/api/{endpoint}/{selected_resource_id}", timeout=20)
            if response.ok:
                st.success("Deleted successfully.")
                refresh_after_change()
            else:
                st.error(response.text)

with notes_tab:
    st.subheader("Chapter Notes")
    st.markdown('<div class="student-card">', unsafe_allow_html=True)

    if not notes:
        st.info("No notes found for this chapter yet.")
    for note in notes:
        note_link = note["link"] if note["link"].startswith("http") else f"{API_BASE_URL}{note['link']}"
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{note['title']}</h3>
                <div style="color:#2b3a55;">{note.get('description', '')}</div>
                <a class="resource-link" href="{note_link}" target="_blank" rel="noopener noreferrer">Open note</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Worksheets")
    if not worksheets:
        st.info("No worksheets available for this chapter yet.")
    for worksheet in worksheets:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{worksheet['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{worksheet.get('description', '')}</div>
                <a class="resource-link" href="{API_BASE_URL}/api/worksheets/{worksheet['id']}/download" target="_blank" rel="noopener noreferrer">Open in browser</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Homework Assignments")
    if not homework_assignments:
        st.info("No homework assignments available for this chapter yet.")
    for homework in homework_assignments:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{homework['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{homework.get('description', '')}</div>
                <a class="resource-link" href="{API_BASE_URL}/api/homework-assignments/{homework['id']}/download" target="_blank" rel="noopener noreferrer">Open in browser</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)

with practice_tab:
    st.subheader("Practice Sets")
    st.markdown('<div class="student-card">', unsafe_allow_html=True)
    if not practice_sets:
        st.info("No practice set found for this chapter yet.")
    for practice in practice_sets:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{practice['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{practice.get('description', '')}</div>
            """,
            unsafe_allow_html=True,
        )
        for index, question in enumerate(practice["questions"], start=1):
            st.markdown(
                f"""
                <div class="question-box">
                    <strong>{index}. {question['question']}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if question.get("options"):
                for option in question["options"]:
                    st.write(f"- {option}")
            if question.get("answer"):
                st.markdown(f'<div class="answer-pill">Answer: {question["answer"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with qp_tab:
    st.subheader("Question Papers")
    st.markdown('<div class="student-card">', unsafe_allow_html=True)
    if not question_papers:
        st.info("No question papers available for this chapter.")
    for qp in question_papers:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{qp['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{qp.get('description', '')}</div>
                <a class="resource-link" href="{API_BASE_URL}/api/question-papers/{qp['id']}/download" target="_blank" rel="noopener noreferrer">Open in browser</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

with books_tab:
    st.subheader("Books")
    st.markdown('<div class="student-card">', unsafe_allow_html=True)
    if not books:
        st.info("No books available for this chapter yet.")
    for book in books:
        st.markdown(
            f"""
            <div class="content-card">
                <h3 style="margin-top:0; color:#0b3d91;">{book['title']}</h3>
                <div style="color:#2b3a55; margin-bottom: 12px;">{book.get('description', '')}</div>
                <a class="resource-link" href="{API_BASE_URL}/api/books/{book['id']}/download" target="_blank" rel="noopener noreferrer">Open PDF</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

with videos_tab:
    st.subheader("Chapter Videos")
    st.markdown('<div class="student-card">', unsafe_allow_html=True)
    if not videos:
        st.info("No videos available for this chapter yet.")
    for video in videos:
        st.markdown(f"<h3 style='color:#0b3d91;'>{video['title']}</h3>", unsafe_allow_html=True)
        if video.get("description"):
            st.write(video["description"])
        st.video(video["link"])
    st.markdown('</div>', unsafe_allow_html=True)

with python_tab:
    st.markdown('<div class="student-card">', unsafe_allow_html=True)
    render_python_editor()
    st.markdown('</div>', unsafe_allow_html=True)
