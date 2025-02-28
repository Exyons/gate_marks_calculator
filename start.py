
"""
This modules calcultes GATE marks
"""
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
# from annotated_text import annotated_text

# Load the answer key which is converted to csv format
answer_key = pd.read_csv("answer_key.csv")

# Fetch the html content of response page
HTML_CONTENT = ""
response_url = st.text_input(
    "Resoponse URL", value="https://cdn.digialm.com//per/g01/pub/585/touchstone/AssessmentQPHTMLMode1//GATE2454/GATE2454S5D2005/17402089937868153/DA25S55042104_GATE2454S5D2005E1.html")
if response_url:
    response = requests.get(response_url, timeout=30)
    if response.status_code == 200:
        HTML_CONTENT = response.text
    else:
        st.write(
            f"Failed to retrieve content. Status code: {response.status_code}")

    # Load the html into beautiful soup
    soup = BeautifulSoup(HTML_CONTENT, features="lxml")
    # Get all image elements
    # These images are of questions and their options
    # NAT type does not have any options
    all_images = soup.find_all(name="img")
    # These elements contain the candidate's response for MCQ and MSQ questions
    response_elements = soup.find_all(
        name="table", attrs={"class": "menu-tbl"})
    # These elements are used to find the candidat's answer for NAT type questions
    question_row_tables = soup.find_all(
        name="table", attrs={"class": "questionRowTbl"})

    # This code stores NAT answers
    nat_responses = []
    for tbl_row in question_row_tables:
        nat_response_data = tbl_row.find_all(name="td")  # type: ignore
        if nat_response_data[-2].get_text() == "Given Answer :":
            nat_answer = nat_response_data[-1].get_text()
            if nat_answer.strip() != "--":
                nat_responses.append(nat_answer)

    # Intro-
    # As options and questions are in random order, we need to find out actual question number and options as per answer key

    # This code stores the names "name" attribute of img elements
    # "name" attribute has a pattern
    # Using this pattern we can identify the actual question number and compare it with the answer key
    # Pattern Explanantion-
    # Every img element "name" attribute contains this sequence "585_142276_0_27112816_"
    # Followed by "question section" either "ga" (For General Aptitude) or "da" (For Data Science)
    # then either a number or nothing
    # followed by character "q"
    # which is followed by actual question number as per the answer key
    # And
    # Every img element of options contain its actual option value after the question number.
    # This will help to replace them with actual options of the answer key.
    # Storing question and option image elements
    question_images = []
    option_images = []
    for img in all_images:
        if re.match(pattern=r'585_142276_0_27112816_(ga|da)\d*q\d+.jpg', string=img.get("name")):  # type: ignore
            question_images.append(img)
        else:
            option_images.append(img)

    # Storing actual question number with candidate's response options
    actual_question_num_with_options = {}
    for q_img in question_images:
        pattern = f"{q_img.get("name").split(".")[0]}"
        actual_q_number = q_img.get("name").split(
            "q")[-1].split(".")[0]
        for img in option_images:
            name = img.get("name")
            if re.match(pattern, name):
                name = name.split(pattern)
                # st.write(pattern, name)
                option = name[-1][0].capitalize()
                if option in ['A', 'B', 'C', 'D']:
                    if actual_q_number in actual_question_num_with_options:
                        actual_question_num_with_options[actual_q_number].append(
                            option)
                    else:
                        actual_question_num_with_options[actual_q_number] = [
                            option]

    # Storing all responses as dictionary
    # Counting answered and unaswered questions
    responses = {}
    COUNT_ANSWERED = 0
    COUNT_UNANSWERED = 0
    NAT_ANSWERED = 0
    MSQ_ANSWERED = 0
    MCQ_ANSWERED = 0
    for q_img, res_elem in zip(question_images, response_elements):
        res_data = res_elem.find_all(                # type: ignore
            name="td", attrs={"class": "bold"})
        actual_q_number = q_img.get("name").split(
            "q")[-1].split(".")[0]
        q_type = res_data[0].get_text()
        if q_type == "NAT":
            is_answered = res_data[-1].get_text(
            ) == "Answered" or res_data[-1].get_text() == "Marked For Review"
            if is_answered:
                responses[actual_q_number] = nat_responses[NAT_ANSWERED]
                COUNT_ANSWERED += 1
                NAT_ANSWERED += 1
            else:
                COUNT_UNANSWERED += 1
        else:
            is_answered = res_data[-2].get_text(
            ) == "Answered" or res_data[-2].get_text() == "Marked For Review"
            if is_answered:
                responses[actual_q_number] = res_data[-1].get_text()
                COUNT_ANSWERED += 1
                if q_type == "MCQ":
                    MCQ_ANSWERED += 1
                else:
                    MSQ_ANSWERED += 1
            else:
                COUNT_UNANSWERED += 1

    # Replacing candidate's response options with the actual options as per answer key
    actual_responses = {}
    for q_num, res in responses.items():
        if q_num in actual_question_num_with_options:
            actual_responses[q_num] = []
            actual_optns = actual_question_num_with_options[q_num]
            for optn in res.split(","):
                match optn:
                    case "A":
                        actual_responses[q_num].append(actual_optns[0])
                    case "B":
                        actual_responses[q_num].append(actual_optns[1])
                    case "C":
                        actual_responses[q_num].append(actual_optns[2])
                    case "D":
                        actual_responses[q_num].append(actual_optns[3])
            actual_responses[q_num] = list(sorted(actual_responses[q_num]))
        else:  # It is NAT question
            actual_responses[q_num] = res
    actual_responses = dict(
        map(lambda item: (int(item[0]), "".join(item[1])), actual_responses.items()))

    # Storing negative marks of MCQ questions. NAT and MSQ have zero negative marks
    answer_key["neg_marks"] = answer_key.apply(lambda row: -row["marks"]/3 if row["q_type"]
                                               == "MCQ" else 0, axis=1)
    total_mcq, total_msq, total_nat = answer_key["q_type"].value_counts().array

    # Calculating final marks and summarizing
    MSQ_CORRECT = 0
    MSQ_POSITIVE_MARKS = 0

    MCQ_CORRECT = 0
    MCQ_POSITIVE_MARKS = 0
    MCQ_NEGATIVE_MARKS = 0

    TOTAL_ONE_MARK_WRONG = 0
    TOTAL_NEGATIVE_MARKS_DUE_TO_ONE_MARK = 0
    TOTAL_TWO_MARK_WRONG = 0
    TOTAL_NEGATIVE_MARKS_DUE_TO_TWO_MARK = 0

    NAT_CORRECT = 0
    NAT_POS_MARKS = 0

    TOTAL_POSITIVE_MARKS = 0
    TOTAL_NEGATIVE_MARKS = 0

    for r_q_num, r_answer in actual_responses.items():
        for q_num, q_type, answer, marks, neg_marks in answer_key.iloc:
            if r_q_num == q_num:
                if r_answer == answer:
                    TOTAL_POSITIVE_MARKS += marks
                    match q_type:
                        case "MCQ":
                            MCQ_CORRECT += 1
                            MCQ_POSITIVE_MARKS += marks
                        case "MSQ":
                            MSQ_CORRECT += 1
                            MSQ_POSITIVE_MARKS += marks
                        case "NAT":
                            NAT_CORRECT += 1
                            NAT_POS_MARKS += marks
                else:
                    TOTAL_NEGATIVE_MARKS += neg_marks
                    if q_type == "MCQ":
                        MCQ_NEGATIVE_MARKS += marks
                        if marks == 1:
                            TOTAL_ONE_MARK_WRONG += 1
                            TOTAL_NEGATIVE_MARKS_DUE_TO_ONE_MARK += neg_marks
                        if marks == 2:
                            TOTAL_TWO_MARK_WRONG += 1
                            TOTAL_NEGATIVE_MARKS_DUE_TO_TWO_MARK += neg_marks

    FINAL_MARKS = TOTAL_POSITIVE_MARKS + TOTAL_NEGATIVE_MARKS
    TOTAL_CORRECT_QUESTIONS = MSQ_CORRECT + MCQ_CORRECT + NAT_CORRECT
    TOTAL_INCORRECT_QUESTIONS = COUNT_ANSWERED - TOTAL_CORRECT_QUESTIONS
    INCORRECT_MCQ = MCQ_ANSWERED - MCQ_CORRECT
    INCORRECT_MSQ = MSQ_ANSWERED - MSQ_CORRECT
    INCORRECT_NAT = NAT_ANSWERED - NAT_CORRECT

    st.write(f"{'Summary':^20}")
    # st.write("\n")
    st.write(f"Total Questions  {65}")
    st.write(f"Total MCQ Questions  {total_mcq}")
    st.write(f"Total MSQ Questions  {total_msq}")
    st.write(f"Total NAT Questions  {total_nat}")

    # st.write("\n")
    st.write(f"Questions Answered  {COUNT_ANSWERED}")
    st.write(f"Questions Unanswerd  {COUNT_UNANSWERED}")

    # st.write("\n")
    st.write(f"Total MCQ answered  {MCQ_ANSWERED}")
    st.write(f"Total MSQ answered  {MSQ_ANSWERED}")
    st.write(f"Total NAT answered  {NAT_ANSWERED}")

    # st.write("\n")
    st.write(f"Total Correct Questions  {TOTAL_CORRECT_QUESTIONS}")
    st.write(f"Total Correct MCQ  {MCQ_CORRECT}")
    st.write(f"Total Correct MSQ  {MSQ_CORRECT}")
    st.write(f"Total Correct NAT  {NAT_CORRECT}")

    # st.write("\n")
    st.write(
        f"Actual number of questions attempted (Ignoring incorrect NATs and MSQs)  {COUNT_ANSWERED - INCORRECT_MSQ - INCORRECT_NAT}")

    # st.write("\n")
    st.write(
        f"Total Incorrect Questions  {TOTAL_INCORRECT_QUESTIONS}")
    st.write(f"Total Incorrect MCQ  {INCORRECT_MCQ}")
    st.write(f"Total Incorrect MSQ  {INCORRECT_MSQ}")
    st.write(f"Total Incorrect NAT  {INCORRECT_NAT}")

    # st.write("\n")
    st.write(f"Total one mark MCQ wrong  {TOTAL_ONE_MARK_WRONG}")
    st.write(f"Total two mark MCQ wrong  {TOTAL_TWO_MARK_WRONG}")

    # st.write("\n")
    st.write(
        f"Total negative marks due to wrong one mark MCQ  {TOTAL_NEGATIVE_MARKS_DUE_TO_ONE_MARK:0.2f}")
    st.write(
        f"Total negative marks due to wrong two mark MCQ  {TOTAL_NEGATIVE_MARKS_DUE_TO_TWO_MARK:0.2f}")

    # st.write("\n")
    st.write(f"Total Positive Marks  {TOTAL_POSITIVE_MARKS}")
    st.write(f"Total Negative Marks (Due to MCQ)  {TOTAL_NEGATIVE_MARKS}")

    # st.write("\n")
    st.write(f"Final Marks  {FINAL_MARKS}")
