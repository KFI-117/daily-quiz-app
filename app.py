import streamlit as st
from supabase import create_client, Client

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://dqcyhbbhtyweafwubcgs.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxY3loYmJodHl3ZWFmd3ViY2dzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA0OTYyMzgsImV4cCI6MjEwNjA3MjIzOH0.hq2Tw-0J4CB2Xe9fAmF5I-_i-jZefu9yVf1J-QH8nSA")

@st.cache_resource
def init_connection() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- PAGE SETUP ---
st.set_page_config(page_title="Osama & Kaifi Daily Quiz Platform", page_icon="📊", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = "Osama"

# --- SIDEBAR: USER & PROFILE SELECTION ---
st.sidebar.title("🔐 User Authentication")
selected_user = st.sidebar.selectbox("Select Your Profile", ["Osama", "Kaifi"], index=0 if st.session_state.user == "Osama" else 1)
st.session_state.user = selected_user

st.sidebar.markdown("---")
st.sidebar.info(f"Logged in as: **{st.session_state.user}**")
target_user = "Kaifi" if st.session_state.user == "Osama" else "Osama"
st.sidebar.write(f"You are viewing questions created by: **{target_user}**")

st.title("📚 Interactive Daily Quiz Platform")
st.markdown(f"Welcome back, **{st.session_state.user}**! Test your knowledge or contribute new challenges.")

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Take Quiz", "➕ Add Questions", "📊 Performance Scoreboard", "⚙️ Manage Questions"])

# ==========================================
# TAB 1: TAKE QUIZ
# ==========================================
with tab1:
    st.header(f"Assessment Hub — Created by {target_user}")
    
    response = supabase.table("quiz_questions").select("*").eq("creator", target_user).eq("target", st.session_state.user).execute()
    questions = response.data
    
    if not questions:
        st.info(f"No active questions available from {target_user} at the moment. Check back later or request a new batch!")
    else:
        with st.form("quiz_submission_form"):
            user_answers = {}
            for idx, q in enumerate(questions):
                st.subheader(f"Question {idx + 1}")
                st.write(q["question"])
                # Fixed column names matching your database (opt_a, opt_b, opt_c, opt_d)
                options = [q["opt_a"], q["opt_b"], q["opt_c"], q["opt_d"]]
                user_answers[q["id"]] = st.radio(
                    f"Select your option for Q{idx + 1}:",
                    options,
                    key=f"q_{q['id']}"
                )
                st.markdown("---")
            
            submit_quiz = st.form_submit_button("Submit Assessment")
            
            if submit_quiz:
                correct_count = 0
                incorrect_count = 0
                attempted_count = len(questions)
                
                for q in questions:
                    selected_ans = user_answers[q["id"]]
                    is_correct = (selected_ans == q["answer"])
                    
                    if is_correct:
                        correct_count += 1
                    else:
                        incorrect_count += 1
                        
                    attempt_data = {
                        "user": st.session_state.user,
                        "question_id": q["id"],
                        "selected_answer": selected_ans,
                        "is_correct": is_correct
                    }
                    supabase.table("quiz_attempts").upsert(attempt_data, on_conflict="user,question_id").execute()
                
                raw_score = correct_count * 1.0
                negative_penalty = incorrect_count * 0.33
                net_score = round(raw_score - negative_penalty, 2)
                
                st.success("Assessment submitted successfully and recorded on the cloud database!")
                st.metric(label="Raw Score (Without Negative Marking)", value=f"{raw_score} / {attempted_count}")
                st.metric(label="Net Score (With 1/3 Negative Marking)", value=f"{net_score} / {attempted_count}")

# ==========================================
# TAB 2: ADD QUESTIONS
# ==========================================
with tab2:
    st.header(f"Contribute Questions for {target_user}")
    st.markdown("Draft and publish high-quality questions for your peer evaluation.")
    
    with st.form("add_question_form"):
        q_text = st.text_area("Question Statement")
        col1, col2 = st.columns(2)
        with col1:
            opt_a = st.text_input("Option A")
            opt_b = st.text_input("Option B")
        with col2:
            opt_c = st.text_input("Option C")
            opt_d = st.text_input("Option D")
            
        correct_ans = st.selectbox("Correct Answer", [opt_a, opt_b, opt_c, opt_d] if opt_a and opt_b else ["Option A", "Option B"])
        explanation = st.text_area("Detailed Explanation")
        
        submitted = st.form_submit_button("Publish Question")
        
        if submitted:
            if not q_text or not opt_a or not opt_b:
                st.error("Please fill in the essential question details and options.")
            else:
                new_q = {
                    "creator": st.session_state.user,
                    "target": target_user,
                    "question": q_text,
                    "opt_a": opt_a,
                    "opt_b": opt_b,
                    "opt_c": opt_c,
                    "opt_d": opt_d,
                    "answer": correct_ans,
                    "explanation": explanation
                }
                supabase.table("quiz_questions").insert(new_q).execute()
                st.success(f"Question successfully published for {target_user}!")

# ==========================================
# TAB 3: PERFORMANCE SCOREBOARD
# ==========================================
with tab3:
    st.header("📊 Performance Analytics & Scoreboard")
    st.markdown("Track comprehensive evaluation metrics, accuracy rates, and net scores with negative marking penalties.")
    
    attempts_resp = supabase.table("quiz_attempts").select("*").execute()
    all_attempts = attempts_resp.data
    
    questions_resp = supabase.table("quiz_questions").select("*").execute()
    all_questions = {q["id"]: q for q in questions_resp.data}
    
    if not all_attempts:
        st.info("No assessment records found yet. Complete a quiz to populate the analytics dashboard.")
    else:
        user_attempts = [
            att for att in all_attempts 
            if att["question_id"] in all_questions and all_questions[att["question_id"]]["target"] == st.session_state.user
        ]
        
        if not user_attempts:
            st.info(f"No evaluation records found for {st.session_state.user}.")
        else:
            total_attempted = len(user_attempts)
            correct_answers = sum(1 for att in user_attempts if att["is_correct"])
            incorrect_answers = total_attempted - correct_answers
            
            raw_score = correct_answers * 1.0
            negative_deduction = round(incorrect_answers * 0.33, 2)
            net_score = round(raw_score - negative_deduction, 2)
            accuracy_rate = round((correct_answers / total_attempted) * 100, 2) if total_attempted > 0 else 0.0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Attempted", total_attempted)
            col2.metric("Correct Answers", correct_answers)
            col3.metric("Incorrect Answers", incorrect_answers)
            col4.metric("Accuracy Rate", f"{accuracy_rate}%")
            
            st.markdown("---")
            
            col_score1, col_score2 = st.columns(2)
            col_score1.metric("Score Without Negative Marking", f"{raw_score} / {total_attempted}")
            col_score2.metric("Score With Negative Marking (-0.33)", f"{net_score} / {total_attempted}")
            
            st.markdown("### Detailed Attempt Logs")
            for att in user_attempts:
                q_info = all_questions.get(att["question_id"])
                if q_info:
                    status_icon = "✅" if att["is_correct"] else "❌"
                    with st.expander(f"{status_icon} {q_info['question'][:60]}..."):
                        st.write(f"**Question:** {q_info['question']}")
                        st.write(f"**Your Answer:** {att['selected_answer']}")
                        st.write(f"**Correct Answer:** {q_info['answer']}")
                        st.info(f"**Explanation:** {q_info['explanation']}")

# ==========================================
# TAB 4: MANAGE QUESTIONS
# ==========================================
with tab4:
    st.header("⚙️ Manage Questions Repository")
    st.markdown("Review or purge questions you have previously authored.")
    
    my_questions_resp = supabase.table("quiz_questions").select("*").eq("creator", st.session_state.user).execute()
    my_questions = my_questions_resp.data
    
    if not my_questions:
        st.info("You have not authored any questions yet.")
    else:
        for q in my_questions:
            with st.expander(f"Q: {q['question'][:50]}... (Target: {q['target']})"):
                st.write(f"**Full Question:** {q['question']}")
                st.write(f"**Correct Answer:** {q['answer']}")
                if st.button(f"Delete Question ID {q['id']}", key=f"del_{q['id']}"):
                    supabase.table("quiz_questions").delete().eq("id", q["id"]).execute()
                    st.success("Question deleted successfully! Refresh the page to view updates.")
