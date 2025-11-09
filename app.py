import streamlit as st
import pandas as pd
import datetime
import time
import altair as alt
import io
import numpy as np

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Study Planner",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 1.5. Custom CSS with Motion Background & TEXT FIXES v2 ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Montserrat', sans-serif;
}

/* --- Keyframes for the background animation --- */
@keyframes gradient-animation {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* --- Main App Styling with Motion Background --- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #1A1A1A, #0A0A0A, #1A1A1A); /* Dark gradient */
    background-size: 400% 400%;
    animation: gradient-animation 15s ease infinite; /* Slow, continuous motion */
    color: #FAFAFA; /* Light text for dark background */
}

/* --- Sidebar Styling --- */
[data-testid="stSidebar"] {
    background-color: #212121; /* Slightly lighter dark for sidebar */
    border-right: 1px solid #333;
}
/* ⭐️ FIX: Force sidebar text to be visible */
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #E0E0E0 !important;
}

/* --- Main Title --- */
h1 {
    color: #FAFAFA;
    text-shadow: 0 0 10px rgba(76, 175, 80, 0.5); /* Green glow for title */
}

/* --- Headers (Subtitles) --- */
h2, h3 {
    color: #4CAF50; /* "Productive Green" for all subheaders */
}

/* --- ⭐️⭐️⭐️ FIXES FOR INVISIBLE TEXT ⭐️⭐️⭐️ --- 
*/

/* General text color for dark mode */
div[data-testid="stText"], 
div[data-testid="stMarkdown"], 
p, a, li {
    color: #E0E0E0 !important; /* Lighter grey for general text */
}

/* Fix for st.info box text */
div[data-testid="stInfo"] {
    color: #212121 !important; /* Dark text for light info box */
    background-color: #e0e0e0;
}

/* Fix for input box LABELS (Subject, Topic, etc.) */
label[data-testid="stWidgetLabel"] {
    color: #E0E0E0 !important; 
    font-weight: 600 !important;
}

/* Fix for text INSIDE input boxes */
input[type="text"], 
input[type="date"], 
textarea {
    color: #FAFAFA !important;
    background-color: #333 !important; /* Darker background for input */
}

/* Fix for placeholder text */
::placeholder {
  color: #888 !imporant;
  opacity: 1;
}
:-ms-input-placeholder {
  color: #888 !important;
}
::-ms-input-placeholder {
  color: #888 !important;
}
/* --- ⭐️⭐️⭐️ END OF FIXES ⭐️⭐️⭐️ --- 
*/


/* --- Button Styling --- */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #4CAF50, #388E3C);
    color: white;
    border-radius: 8px;
    border: none;
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    transition: all 0.3s ease;
    font-weight: 600;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #388E3C, #4CAF50);
    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.5);
    transform: translateY(-2px);
}
[data-testid="stButton"] button:active {
    transform: translateY(1px);
}

/* --- Special Red "STOP" Button --- */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #f44336, #d32f2f); /* Red for stop */
    box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #d32f2f, #f44336);
    box-shadow: 0 6px 20px rgba(244, 67, 54, 0.5);
}

/* --- Tab Styling --- */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #212121; /* Darker grey for tab bar */
    border-radius: 8px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: #aaa;
    font-weight: 600;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
}

/* --- Data Editor / Dataframe --- */
[data-testid="stDataEditor"] {
    border: 1px solid #333;
    border-radius: 8px;
}

/* --- Number Input, Text Input, Date Input, Slider Backgrounds --- */
div[data-testid="stNumberInput"],
div[data-testid="stTextInput"],
div[data-testid="stDateInput"],
div[data-testid="stSlider"] {
    background-color: #212121; /* Match sidebar background */
    border: 1px solid #333;
    border-radius: 8px;
    padding: 10px 10px 1px 10px; /* Adjust padding for better look */
    margin-bottom: 10px; /* Space out elements */
}

/* --- Balloons! --- */
[data-testid="stBalloons"] {
    opacity: 0.8;
}

</style>
""", unsafe_allow_html=True)


# --- 2. Initialize Session State ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame(columns=[
        "Subject", "Topic", "Deadline", "Difficulty (1-5)", "Status", "Priority"
    ])
if 'pomodoro_running' not in st.session_state:
    st.session_state.pomodoro_running = False
if 'pomodoro_end_time' not in st.session_state:
    st.session_state.pomodoro_end_time = None

# --- 3. Helper Functions ---
def calculate_priority(row):
    days_remaining = (pd.to_datetime(row['Deadline']) - datetime.datetime.now()).days
    if days_remaining < 0:
        urgency_score = 100
    elif days_remaining == 0:
        urgency_score = 50
    else:
        urgency_score = 10 / (days_remaining + 1)
    priority_score = (row['Difficulty (1-5)'] * 5) + urgency_score
    return round(priority_score, 2)

def get_recommendations(df):
    if df.empty:
        return "No recommendations. Add some tasks!"
    top_task = df.iloc[0]
    days_left = (pd.to_datetime(top_task['Deadline']) - datetime.datetime.now()).days
    recs = []
    recs.append(f"**Start with this:** Your highest priority task is **'{top_task['Topic']}'** for **{top_task['Subject']}**.")
    if days_left <= 1:
        recs.append(f"**High Alert!** This task is due in {days_left} day(s). Use your next Pomodoro session on this.")
    elif days_left < 3:
        recs.append(f"**Focus Up:** You only have {days_left} days for your top task. Make it a priority.")
    high_priority_tasks = df[df['Priority'] > 20]
    if len(high_priority_tasks) > 5:
        recs.append(f"**Workload Warning:** You have {len(high_priority_tasks)} high-priority tasks. Make sure to schedule extra study time.")
    return "\n".join(f"* {rec}" for rec in recs)

# --- 4. Sidebar (Data Input Module) ---
st.sidebar.title("MODULE 1: Add Task")
with st.sidebar.form("task_form", clear_on_submit=True):
    st.write("Add a new task to your planner:")
    subject = st.text_input("Subject", placeholder="e.g., Python")
    topic = st.text_input("Topic", placeholder="e.g., Streamlit Basics")
    deadline = st.date_input("Deadline", min_value=datetime.date.today())
    difficulty = st.slider("Difficulty (1-5)", 1, 5, 3)
    
    submitted = st.form_submit_button("Add Task") 
    
    if submitted:
        if subject and topic:
            new_task = {
                "Subject": subject,
                "Topic": topic,
                "Deadline": deadline,
                "Difficulty (1-5)": difficulty,
                "Status": "Not Started"
            }
            new_task_df = pd.DataFrame([new_task])
            st.session_state.tasks = pd.concat(
                [st.session_state.tasks, new_task_df], 
                ignore_index=True
            )
            st.session_state.tasks['Priority'] = st.session_state.tasks.apply(calculate_priority, axis=1)
            st.sidebar.success(f"Added: '{topic}'")
        else:
            st.sidebar.error("Please fill in all fields.")

# --- 5. Main App Layout (Tabs) ---
st.title("🧠 Smart Study Planner")
st.write("Welcome to your intelligent planner. Add tasks in the sidebar and see your plan update in real-time.")

tab_plan, tab_pomo, tab_progress, tab_ml_insights = st.tabs(
    ["My Study Plan",
     "Pomodoro Timer", 
     "Progress Tracker", 
     "Productivity Insights"]
)

# --- TAB 1: Study Plan (Modules 2 & 6) ---
with tab_plan:
    st.header("🤖 Your Generated Study Plan")
    st.write("This list is automatically sorted by priority, calculated based on deadlines and difficulty.")
    if not st.session_state.tasks.empty:
        plan_df = st.session_state.tasks.query("Status != 'Completed'").copy()
        plan_df = plan_df.sort_values(by="Priority", ascending=False)
        
        if plan_df.empty:
            st.success("🎉 All tasks completed! Add more tasks in the sidebar.")
        else:
            st.dataframe(plan_df, use_container_width=True)
            st.divider()
            st.subheader("💡 Recommendations")
            recommendations = get_recommendations(plan_df)
            st.markdown(recommendations)
    else:
        st.info("Add some tasks in the sidebar to generate your plan!")

# --- TAB 2: Pomodoro Timer (Module 3) ---
with tab_pomo:
    st.header("🍅 Pomodoro Timer")
    st.write("Select a task and set your focus time!")

    # --- ⭐️⭐️⭐️ TIMER FIX HERE ⭐️⭐️⭐️ ---
    duration_in_minutes = st.number_input(
        "Set focus duration (in minutes):", 
        min_value=1,  # <-- Changed from 5 to 1
        max_value=120, 
        value=25,
        step=5
    )
    
    duration_in_seconds = duration_in_minutes * 60

    if st.session_state.pomodoro_running:
        end_time = st.session_state.pomodoro_end_time
        if time.time() < end_time:
            timer_placeholder = st.empty()
            
            if st.button("STOP TIMER ⏹️", type="primary"):
                 st.session_state.pomodoro_running = False
                 timer_placeholder.empty()
                 st.warning("Timer stopped. Don't give up!")
                 time.sleep(1)
                 st.rerun()

            while time.time() < end_time and st.session_state.pomodoro_running:
                remaining_time = int(end_time - time.time())
                mins, secs = divmod(remaining_time, 60)
                timer_display = f"{mins:02d}:{secs:02d}"
                timer_placeholder.metric("Time Remaining", timer_display)
                try:
                    time.sleep(1)
                except st.errors.ScriptRunner.StopException:
                    st.session_state.pomodoro_running = False
                    break
            
            if st.session_state.pomodoro_running:
                timer_placeholder.empty()
                st.success(f"🎉 Session finished! Time for a break.")
                st.balloons()
                st.session_state.pomodoro_running = False
        else:
            st.session_state.pomodoro_running = False
    else:
        start_button_text = f"Start {duration_in_minutes}-Minute Pomodoro 🚀"
        
        if st.button(start_button_text): 
            st.session_state.pomodoro_end_time = time.time() + duration_in_seconds
            st.session_state.pomodoro_running = True
            st.rerun()

# --- TAB 3: Progress Tracker (Module 5) ---
with tab_progress:
    st.header("📊 Your Progress Tracker")
    st.write("See visualizations of your study habits and task status.")
    if not st.session_state.tasks.empty:
        df = st.session_state.tasks.copy()
        
        st.subheader("Task Status Overview")
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        c_status = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Status", type="nominal", title="Task Status",
                            scale=alt.Scale(domain=['Completed', 'In Progress', 'Not Started'],
                                            range=['#4CAF50', '#FFC107', '#F44336'])), # Green, Yellow, Red
            tooltip=['Status', 'Count']
        ).properties(title="Task Completion Status")
        st.altair_chart(c_status, use_container_width=True)

        st.subheader("Workload by Subject")
        subject_counts = df['Subject'].value_counts().reset_index()
        subject_counts.columns = ['Subject', 'Task Count']
        
        c_subject = alt.Chart(subject_counts).mark_bar().encode(
            x=alt.X('Subject', title='Subject'),
            y=alt.Y('Task Count', title='Number of Tasks'),
            color=alt.Color('Subject', title="Subject"),
            tooltip=['Subject', 'Task Count']
        ).properties(title="Tasks per Subject")
        st.altair_chart(c_subject, use_container_width=True)

        st.subheader("Update Task Status")
        st.write("Click on the 'Status' cell to update your tasks.")
        
        edited_df = st.data_editor(
            df, 
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Not Started", "In Progress", "Completed"]
                )
            },
            disabled=["Subject", "Topic", "Deadline", "Difficulty (1-5)", "Priority"],
            use_container_width=True,
            hide_index=True
        )
        
        if not edited_df.equals(st.session_state.tasks):
            st.session_state.tasks = edited_df
            st.success("Task status updated!")
            time.sleep(1)
            st.rerun()
    else:
        st.info("No data to track. Add tasks in the sidebar.")

# --- TAB 4: ML Productivity Insights (Module 4) ---
# --- ⭐️⭐️⭐️ THIS ENTIRE TAB IS REBUILT ⭐️⭐️⭐️ ---
with tab_ml_insights:
    st.header("💡 Productivity Insights (K-Means Clustering)")
    st.write("This module analyzes your **completed** tasks to find your unique study patterns.")

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler, OneHotEncoder
        from sklearn.compose import ColumnTransformer
        
        # Check if there are any completed tasks to analyze
        if 'Completed' not in st.session_state.tasks['Status'].unique():
            st.info("Once you complete some tasks (in the 'Progress Tracker' tab), your personalized insights will appear here.")
        
        else:
            # 1. Get *only* the completed tasks
            df_completed = st.session_state.tasks[st.session_state.tasks['Status'] == 'Completed'].copy()
            
            # We need at least 3 completed tasks to form clusters
            if len(df_completed) < 3:
                st.info(f"You've completed {len(df_completed)} task(s). Complete at least 3 tasks to generate insights.")
            else:
                # 2. Define features for the model
                # We will cluster based on 'Subject' and 'Difficulty'
                features_num = ['Difficulty (1-5)']
                features_cat = ['Subject']

                # 3. Create a preprocessor
                # We must scale numerical data (Difficulty)
                # We must one-hot encode categorical data (Subject)
                preprocessor = ColumnTransformer(
                    transformers=[
                        ('num', StandardScaler(), features_num),
                        ('cat', OneHotEncoder(handle_unknown='ignore'), features_cat)
                    ])

                # 4. Process the features
                features_processed = preprocessor.fit_transform(df_completed)

                # 5. Run K-Means Clustering
                # We'll try to find 2 or 3 patterns, whichever is smaller than the number of tasks
                n_clusters = min(3, len(df_completed) - 1) 
                
                if n_clusters > 0:
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    df_completed['Cluster'] = kmeans.fit_predict(features_processed)
                    df_completed['Study_Pattern'] = 'Pattern ' + (df_completed['Cluster'] + 1).astype(str)

                    st.subheader("Your Personalized Study Patterns")
                    st.write("We've analyzed your completed tasks and grouped them into these patterns:")

                    # 6. Visualize the results
                    c_ml = alt.Chart(df_completed).mark_circle(size=100).encode(
                        x=alt.X('Subject:N', title='Subject'),
                        y=alt.Y('Difficulty (1-5):O', title='Task Difficulty', scale=alt.Scale(domain=[1, 5])),
                        color=alt.Color('Study_Pattern:N', title='Your Study Pattern'),
                        tooltip=['Subject', 'Topic', 'Difficulty (1-5)', 'Study_Pattern']
                    ).properties(
                        title="Your Completed Task Clusters"
                    ).interactive()
                    
                    st.altair_chart(c_ml, use_container_width=True)

                    st.subheader("What This Means (Insights)")
                    st.markdown("""
                    This chart shows the "workload patterns" of the tasks you've completed.
                    * **Look at the clusters:** Does "Pattern 1" represent all your hard Math tasks? Does "Pattern 2" represent all your easy Python tasks?
                    * **As you complete more tasks,** this chart will update and give you a clearer picture of your study habits.
                    """)
                else:
                    st.info("Complete just a few more tasks to see your patterns emerge!")

    except ImportError:
        st.error("Please install scikit-learn to run the ML module: `pip install scikit-learn`")
    except Exception as e:
        st.error(f"An error occurred during ML processing: {e}")
