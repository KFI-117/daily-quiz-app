import streamlit as st
from supabase import create_client, Client

# Page configuration
st.set_page_config(
    page_title="Daily Quiz Battle: Osama vs Kaifi",
    page_icon="🎯",
    layout="centered",
)

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = "https://dqcyhbbhtyweafwubcgs.supabase.co"  #[cite: 3, 4]
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxY3loYmJodHl3ZWFmd3ViY2dzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA0OTYyMzgsImV4cCI6MjEwNjA3MjIzOH0.hq2Tw-0J4CB2Xe9fAmF5I-_i-jZefu9yVf1J-QH8nSA"  #[cite: 4]


@st.cache_resource
def init_supabase():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase: Client = init_supabase()


# Helper functions for Supabase Database
def load_questions():
  try:
    response = (
        supabase.table("quiz_questions")
        .select("*")
        .order("id", desc=False)
        .execute()
    )
    return response.data if response.data else []
  except Exception as e:
    st.error(f"Error loading questions: {e}")
    return []


def save_question_to_db(question_data):
  try:
    supabase.table("quiz_questions").insert(question_data).execute()
    return True
  except Exception as e:
    st.error(f"Error saving question: {e}")
    return False


def delete_question_from_db(q_id):
  try:
    supabase.table("quiz_questions").delete().eq("id", q_id).execute()
    return True
  except Exception as e:
    st.error(f"Error deleting question: {e}")
    return False


# Main UI Title
st.title("🎯 Daily Quiz Battle (Osama & Kaifi)")
st.write(
    "Structured peer quizzing platform powered by Supabase Cloud. (5th Option:"
    " Question not attempted)"
)

# Sidebar for User Selection
st.sidebar.header("👤 User Profile")
current_user = st.sidebar.selectbox(
    "Select User Profile", ["Select Name", "Osama", "Kaifi"]
)

if current_user == "Select Name":
  st.warning("⚠️ Please select your profile from the sidebar to proceed.")
  st.stop()

# Determine the opponent
opponent = "Kaifi" if current_user == "Osama" else "Osama"

# Fetch questions from Supabase
questions_list = load_questions()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(
    ["📝 Add Questions", "🎯 Attempt Quiz", "📊 Manage Questions"]
)

# --- TAB 1: ADD QUESTIONS ---
with tab1:
  st.header(f"Add New Question (Target: {opponent})")
  st.write(
      f"Questions added here will appear in the quiz session for **{opponent}**."
  )

  with st.form("add_question_form", clear_on_submit=True):
    q_text = st.text_area("Question Statement:")
    opt_a = st.text_input("Option (a)")
    opt_b = st.text_input("Option (b)")
    opt_c = st.text_input("Option (c)")
    opt_d = st.text_input("Option (d)")

    correct_opt = st.selectbox(
        "Correct Answer Option",
        ["Option (a)", "Option (b)", "Option (c)", "Option (d)"],
    )

    explanation_text = st.text_area(
        "Explanation (Optional - Provide reasoning for the correct answer):"
    )

    submitted = st.form_submit_button("Save Question")

    if submitted:
      if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
        st.error("Please fill in all options (a, b, c, d) and the question text.")
      else:
        new_q = {
            "creator": current_user,
            "target": opponent,
            "question": q_text,
            "opt_a": opt_a,
            "opt_b": opt_b,
            "opt_c": opt_c,
            "opt_d": opt_d,
            "answer": correct_opt,
            "explanation": explanation_text.strip(),
        }

        if save_question_to_db(new_q):
          st.success("🎉 Question successfully saved to Supabase Cloud!")
          st.rerun()

# --- TAB 2: TAKE QUIZ ---
with tab2:
  st.header(f"Quiz Session ({current_user}'s Turn)")

  pending_questions = [
      q for q in questions_list if q.get("target") == current_user
  ]

  if not pending_questions:
    st.info(f"No pending questions assigned by {opponent} at the moment.")
  else:
    st.write(f"Total Available Questions: {len(pending_questions)}")

    if "quiz_attempts" not in st.session_state:
      st.session_state.quiz_attempts = {}

    # Reverse list for recent-first display while keeping original absolute numbering
    for idx, q in enumerate(pending_questions[::-1]):
      q_id = q["id"]
      q_num = (
          questions_list.index(q) + 1
      )  # Permanent absolute numbering from database ID index
      st.markdown(f"### Q{q_num}: {q['question']}")

      attempt_key = f"attempted_{q_id}"

      if attempt_key in st.session_state.quiz_attempts:
        res = st.session_state.quiz_attempts[attempt_key]
        st.write(f"**Your Choice:** {res['selected_text']}")

        if res["is_skipped"]:
          st.info(
              f"ℹ️ You marked this question as **Not Attempted**. Correct"
              f" Answer: **{res['correct_text']}**"
          )
        elif res["is_correct"]:
          st.success("✅ Correct Answer! Excellent work.")
        else:
          st.error(
              f"❌ Incorrect Answer. Correct Answer was:"
              f" **{res['correct_text']}**"
          )

        if q.get("explanation"):
          st.info(f"💡 **Explanation:** {q['explanation']}")
        else:
          st.caption("*(No explanation provided by the creator)*")

        if st.button("🔄 Retry Question", key=f"retry_{q_id}"):
          del st.session_state.quiz_attempts[attempt_key]
          st.rerun()

      else:
        with st.form(key=f"q_form_{q_id}"):
          opts_list = [
              f"(a) {q['opt_a']}",
              f"(b) {q['opt_b']}",
              f"(c) {q['opt_c']}",
              f"(d) {q['opt_d']}",
              "(e) Question not attempted",
          ]

          selected_choice = st.radio(
              f"Select your response for Q{q_num}",
              opts_list,
              index=None,
              key=f"ans_radio_{q_id}",
          )

          ans_submitted = st.form_submit_button("Check Answer")

          if ans_submitted:
            if selected_choice is None:
              st.warning(
                  "Please select an option or choose 'Question not attempted'."
              )
            else:
              selected_key = f"Option ({selected_choice[1]})"
              correct_key = q["answer"]

              # Map option key to text value
              opt_map = {
                  "Option (a)": q["opt_a"],
                  "Option (b)": q["opt_b"],
                  "Option (c)": q["opt_c"],
                  "Option (d)": q["opt_d"],
              }
              correct_text = opt_map.get(correct_key, "")

              is_skipped = selected_key == "Option (e)"
              is_correct = selected_key == correct_key

              st.session_state.quiz_attempts[attempt_key] = {
                  "selected_text": selected_choice,
                  "is_skipped": is_skipped,
                  "is_correct": is_correct,
                  "correct_text": correct_text,
              }
              st.rerun()

      st.divider()

# --- TAB 3: VIEW & MANAGE QUESTIONS ---
with tab3:
  st.header("📊 Database History & Management")
  st.write(
      "Review all previously added questions from Supabase Cloud (Most recent"
      " first):"
  )

  if not questions_list:
    st.write("Database is currently empty.")
  else:
    for idx, q in enumerate(questions_list[::-1]):
      q_id = q["id"]
      q_num = len(questions_list) - idx
      opt_map = {
          "Option (a)": q["opt_a"],
          "Option (b)": q["opt_b"],
          "Option (c)": q["opt_c"],
          "Option (d)": q["opt_d"],
      }
      correct_ans_text = opt_map.get(q["answer"], "")

      col1, col2 = st.columns([4, 1])

      with col1:
        st.markdown(
            f"**Q{q_num}. [Created by: {q['creator']} -> Assigned to:"
            f" {q['target']}]** {q['question']}"
        )
        st.write(f" - Correct Answer: {q['answer']} ({correct_ans_text})")
        if q.get("explanation"):
          st.write(f" - Explanation: {q['explanation']}")

      with col2:
        if st.button("🗑️ Delete", key=f"del_btn_{q_id}"):
          if delete_question_from_db(q_id):
            if f"attempted_{q_id}" in st.session_state.get(
                "quiz_attempts", {}
            ):
              del st.session_state.quiz_attempts[f"attempted_{q_id}"]
            st.success("Question deleted from Cloud!")
            st.rerun()

      st.markdown("---")
