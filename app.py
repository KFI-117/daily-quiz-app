import json
import os
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Daily 5 Quiz Battle", page_icon="🎯", layout="centered"
)

DATA_FILE = "quiz_data.json"


# Helper Functions to Load and Save JSON data securely
def load_data():
  if not os.path.exists(DATA_FILE):
    return {"questions": []}
  try:
    with open(DATA_FILE, "r") as f:
      return json.load(f)
  except json.JSONDecodeError:
    return {"questions": []}


def save_data(data):
  with open(DATA_FILE, "w") as f:
    json.dump(data, f, indent=4)


# Main UI Title
st.title("🎯 Daily 5 Quiz Battle")
st.write(
    "Collaborative daily quiz portal for focused preparation. (5th Option: Question"
    " not attempted)"
)

# Sidebar for User Selection
st.sidebar.header("👤 User Profile")
current_user = st.sidebar.selectbox(
    "Select your profile:", ["Select User", "Osama", "Kaifi"]
)

if current_user == "Select User":
  st.warning("👈 Please select your user profile from the sidebar to proceed.")
  st.stop()

# Determine the opponent
opponent = "Kaifi" if current_user == "Osama" else "Osama"

# Load database
db = load_data()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(
    ["📝 Add Questions", "🎯 Take Quiz", "📊 Database History"]
)

# --- TAB 1: ADD QUESTIONS ---
with tab1:
  st.header(f"Add Questions (Targeting: {opponent})")
  st.write(
      f"Questions submitted here will appear in the quiz session for"
      f" **{opponent}**."
  )

  with st.form("add_question_form", clear_on_submit=True):
    q_text = st.text_area("Question Statement:")
    opt_a = st.text_input("Option (a)")
    opt_b = st.text_input("Option (b)")
    opt_c = st.text_input("Option (c)")
    opt_d = st.text_input("Option (d)")

    correct_opt = st.selectbox(
        "Correct Answer",
        ["Option (a)", "Option (b)", "Option (c)", "Option (d)"],
    )

    explanation_text = st.text_area(
        "Explanation (Optional - Provide reasoning for the correct answer):"
    )

    submitted = st.form_submit_button("Save Question")

    if submitted:
      if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
        st.error(
            "Please fill in all options (a, b, c, d) and the question field."
        )
      else:
        new_q = {
            "creator": current_user,
            "target": opponent,
            "question": q_text,
            "options": {
                "Option (a)": opt_a,
                "Option (b)": opt_b,
                "Option (c)": opt_c,
                "Option (d)": opt_d,
                "Option (e)": "Question not attempted",
            },
            "answer": correct_opt,
            "explanation": explanation_text.strip(),
        }
        db["questions"].append(new_q)
        save_data(db)
        st.success("🎉 Question successfully saved to database!")

# --- TAB 2: TAKE QUIZ ---
with tab2:
  st.header(f"Quiz Section ({current_user}'s Turn)")

  # Filter questions meant for the current user
  pending_questions = [
      q for q in db["questions"] if q.get("target") == current_user
  ]

  if not pending_questions:
    st.info(f"No pending questions available from {opponent} yet.")
  else:
    st.write(f"Total available questions: {len(pending_questions)}")
    st.write(
        "Note: Submit individual answers to view instant evaluation and"
        " explanations."
    )

    for idx, q in enumerate(pending_questions):
      st.markdown(f"### Q{idx + 1}: {q['question']}")

      with st.form(key=f"q_form_{idx}"):
        opts_list = [
            f"(a) {q['options']['Option (a)']}",
            f"(b) {q['options']['Option (b)']}",
            f"(c) {q['options']['Option (c)']}",
            f"(d) {q['options']['Option (d)']}",
            "(e) Question not attempted",
        ]

        selected_choice = st.radio(
            f"Select option for Q{idx + 1}",
            opts_list,
            index=None,
            key=f"ans_radio_{idx}",
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

            if selected_key == "Option (e)":
              st.info(
                  "ℹ️ Status: **Question not attempted**. Correct Answer was:"
                  f" **{q['options'][correct_key]}**"
              )
            elif selected_key == correct_key:
              st.success("✅ Correct Answer! Excellent work.")
            else:
              st.error(
                  "❌ Incorrect Answer. Correct Answer was:"
                  f" **{q['options'][correct_key]}**"
              )

            # Show explanation if available
            if q.get("explanation"):
              st.info(f"💡 **Explanation:** {q['explanation']}")
            else:
              st.caption(
                  "*(No explanation provided by the question creator)*"
              )
      st.divider()

# --- TAB 3: VIEW ALL QUESTIONS ---
with tab3:
  st.header("📚 Database History")
  st.write("Complete repository of all submitted questions:")
  if not db["questions"]:
    st.write("Database is currently empty.")
  else:
    for i, q in enumerate(db["questions"]):
      st.markdown(
          f"**{i + 1}. [Created By: {q['creator']} -> Assigned To:"
          f" {q['target']}]** {q['question']}"
      )
      st.write(
          f" - Correct Answer: {q['answer']} ({q['options'][q['answer']]})"
      )
      if q.get("explanation"):
        st.write(f" - Explanation: {q['explanation']}")
      st.markdown("---")