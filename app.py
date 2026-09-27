import json
import os
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Daily Quiz Battle: Osama vs Kaifi",
    page_icon="🎯",
    layout="centered",
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
st.title("🎯 Daily Quiz Battle (Osama & Kaifi)")
st.write(
    "Structured peer quizzing platform to enhance daily preparation. (5th"
    " Option: Question not attempted)"
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

# Load database
db = load_data()

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
  st.header(f"Quiz Session ({current_user}'s Turn)")

  # Get pending questions along with their original absolute index in the database
  pending_with_indices = [
      (i, q)
      for i, q in enumerate(db["questions"])
      if q.get("target") == current_user
  ]

  if not pending_with_indices:
    st.info(f"No pending questions assigned by {opponent} at the moment.")
  else:
    st.write(f"Total Available Questions: {len(pending_with_indices)}")
    st.write(
        "Note: Most recent questions appear first, but original question"
        " numbers remain fixed."
    )

    # Reverse for display (Recent first)
    for original_idx, q in pending_with_indices[::-1]:
      q_num = original_idx + 1  # Fixed absolute numbering
      st.markdown(f"### Q{q_num}: {q['question']}")

      with st.form(key=f"q_form_{original_idx}"):
        opts_list = [
            f"(a) {q['options']['Option (a)']}",
            f"(b) {q['options']['Option (b)']}",
            f"(c) {q['options']['Option (c)']}",
            f"(d) {q['options']['Option (d)']}",
            "(e) Question not attempted",
        ]

        selected_choice = st.radio(
            f"Select your response for Q{q_num}",
            opts_list,
            index=None,
            key=f"ans_radio_{original_idx}",
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
                  "ℹ️ You marked this question as **Not Attempted**. Correct"
                  f" Answer: **{q['options'][correct_key]}**"
              )
            elif selected_key == correct_key:
              st.success("✅ Correct Answer! Excellent work.")
            else:
              st.error(
                  "❌ Incorrect Answer. Correct Answer was:"
                  f" **{q['options'][correct_key]}**"
              )

            if q.get("explanation"):
              st.info(f"💡 **Explanation:** {q['explanation']}")
            else:
              st.caption("*(No explanation provided by the creator)*")
      st.divider()

# --- TAB 3: VIEW & MANAGE QUESTIONS ---
with tab3:
  st.header("📊 Database History & Management")
  st.write(
      "Review all previously added questions with their permanent numbers"
      " (Most recent first):"
  )

  if not db["questions"]:
    st.write("Database is currently empty.")
  else:
    # Reverse order for management view, keeping original numbering
    reversed_management = list(enumerate(db["questions"]))[::-1]

    for original_idx, q in reversed_management:
      q_num = original_idx + 1
      col1, col2 = st.columns([4, 1])

      with col1:
        st.markdown(
            f"**Q{q_num}. [Created by: {q['creator']} -> Assigned to:"
            f" {q['target']}]** {q['question']}"
        )
        st.write(
            f" - Correct Answer: {q['answer']} ({q['options'][q['answer']]})"
        )
        if q.get("explanation"):
          st.write(f" - Explanation: {q['explanation']}")

      with col2:
        if st.button("🗑️ Delete", key=f"del_btn_{original_idx}"):
          db["questions"].pop(original_idx)
          save_data(db)
          st.success("Question deleted successfully!")
          st.rerun()

      st.markdown("---")
