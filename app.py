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
st.title("🎯 Daily 5 Quiz Battle (Osama vs Kaifi)")
st.write(
    "Aapas me padhai karo, roz 5 sawaal pucho, aur prep mazboot karo! (5th"
    " Option: Question not attempted)"
)

# Sidebar for User Selection
st.sidebar.header("👤 User Profile")
current_user = st.sidebar.selectbox(
    "Kaun login kar raha hai?", ["Select Name", "Osama", "Kaifi"]
)

if current_user == "Select Name":
  st.warning("👈 Pehle sidebar se apna naam select karo bhai!")
  st.stop()

# Determine the opponent
opponent = "Kaifi" if current_user == "Osama" else "Osama"

# Load database
db = load_data()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(
    ["📝 Add Questions", "🎯 Take Quiz", "📊 View & Manage Questions"]
)

# --- TAB 1: ADD QUESTIONS ---
with tab1:
  st.header(f"Add Questions (For {opponent})")
  st.write(
      f"Yahan aap jo sawaal daaloge, wo **{opponent}** ke liye quiz me dikhenge."
  )

  with st.form("add_question_form", clear_on_submit=True):
    q_text = st.text_area("Sawaal (Question) yahan likho:")
    opt_a = st.text_input("Option (a)")
    opt_b = st.text_input("Option (b)")
    opt_c = st.text_input("Option (c)")
    opt_d = st.text_input("Option (d)")

    correct_opt = st.selectbox(
        "Sahi Jawab (Correct Option)",
        ["Option (a)", "Option (b)", "Option (c)", "Option (d)"],
    )

    explanation_text = st.text_area(
        "Explanation (Optional - Sahi jawab ka reason yahan likh sakte hain):"
    )

    submitted = st.form_submit_button("Sawaal Save Karein")

    if submitted:
      if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
        st.error(
            "Bhai a, b, c, d saare options aur sawaal bharna zaroori hai!"
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
        st.success("🎉 Sawaal safaltapoorvak save ho gaya!")

# --- TAB 2: TAKE QUIZ ---
with tab2:
  st.header(f"Quiz Section ({current_user}'s Turn)")

  # Filter questions meant for the current user
  pending_questions = [
      q for q in db["questions"] if q.get("target") == current_user
  ]

  if not pending_questions:
    st.info(f"Abhi {opponent} ne tumhare liye koi naya sawaal nahi dala hai!")
  else:
    st.write(f"Total available questions: {len(pending_questions)}")
    st.write(
        "Note: Har question ke neeche submit karne par turant result aur"
        " explanation dikhega."
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
            f"Select options for Q{idx + 1}",
            opts_list,
            index=None,
            key=f"ans_radio_{idx}",
        )

        ans_submitted = st.form_submit_button("Check Answer")

        if ans_submitted:
          if selected_choice is None:
            st.warning(
                "Pehle koi option select karo ya 'Question not attempted' chuno!"
            )
          else:
            selected_key = f"Option ({selected_choice[1])"
            correct_key = q["answer"]

            if selected_key == "Option (e)":
              st.info(
                  "ℹ️ Yeh question aapne **Attempt Nahi Kiya** chuna hai. Sahi"
                  f" Jawab tha: **{q['options'][correct_key]}**"
              )
            elif selected_key == correct_key:
              st.success("✅ Sahi Jawab! Shandar!")
            else:
              st.error(
                  "❌ Galat Jawab! Sahi Jawab yeh tha:"
                  f" **{q['options'][correct_key]}**"
              )

            if q.get("explanation"):
              st.info(f"💡 **Explanation:** {q['explanation']}")
            else:
              st.caption(
                  "*(Creator ne is question ke liye koi explanation nahi"
                  " dala)*"
              )
      st.divider()

# --- TAB 3: VIEW & MANAGE QUESTIONS ---
with tab3:
  st.header("📊 Database History & Management")
  st.write(
      "Yahan saare add kiye gaye sawaal dikhenge. Agar koi galat ho toh use"
      " delete kar sakte hain:"
  )

  if not db["questions"]:
    st.write("Database abhi khali hai.")
  else:
    for i, q in enumerate(db["questions"]):
      col1, col2 = st.columns([4, 1])

      with col1:
        st.markdown(
            f"**{i + 1}. [By: {q['creator']} -> For: {q['target']}]**"
            f" {q['question']}"
        )
        st.write(
            f" - Correct Answer: {q['answer']} ({q['options'][q['answer']]})"
        )
        if q.get("explanation"):
          st.write(f" - Explanation: {q['explanation']}")

      with col2:
        if st.button("🗑️ Delete", key=f"del_btn_{i}"):
          db["questions"].pop(i)
          save_data(db)
          st.success("Sawaal delete ho gaya!")
          st.rerun()

      st.markdown("---")
