# GATE marks calculator

I made this to stop counting GATE marks by hand. You paste the URL of your response sheet, and it prints your score along with a breakdown of what went right and wrong.

It is a small Streamlit app. It scrapes the response page from the exam portal, decodes which question is which, compares your answers against a CSV answer key, and applies the negative marking rules.

## Why scraping is not trivial

The response sheet does not show questions in the order the answer key uses. Every candidate gets the questions shuffled, and the options inside each question are shuffled too. So "you picked option B" means nothing until you know what B was on your paper.

The one thing that survives the shuffle is the `name` attribute on the question and option images. It looks like this:

```
585_142276_0_27112816_da2q47.jpg
```

Read from the right: `q47` is the real question number from the answer key, `da` is the section (`ga` for General Aptitude, `da` for Data Science and AI), and the digits after `da` are the display position. Option images carry the same prefix plus the real option letter at the end. That is enough to map your shuffled response back onto the official numbering.

NAT questions have no options, so those answers are pulled from the "Given Answer :" cells in the question row tables instead.

## Running it

```bash
pip install -r requirements.txt
streamlit run start.py
```

Open the app, paste your response sheet URL into the box, and wait for the summary. The URL is the long `cdn.digialm.com/.../...html` link the portal gives you.

## The answer key

`answer_key.csv` holds the key. Four columns:

```csv
q_num,q_type,answer,marks
1,MCQ,A,1
```

For MSQ rows with several correct options, write them sorted and joined, so `AC` rather than `A,C` or `CA`. The app sorts your response the same way before comparing.

The key currently in the repo is the GATE 2025 Data Science and AI paper: 65 questions, 100 marks, 35 MCQ, 18 MSQ, 12 NAT.

## Using it for a different paper

Two things need changing.

Replace `answer_key.csv` with the key for your paper. Then open `start.py` and fix the regex around line 62:

```python
r'585_142276_0_27112816_(ga|da)\d*q\d+.jpg'
```

That prefix is specific to the GATE 2025 DA paper, and `da` is the section code for it. Open your own response sheet, view source, find any question image, and copy its prefix and section code into the pattern. Everything downstream works off that match.

## Marking scheme applied

A wrong MCQ costs one third of its marks, so -0.33 on a 1 mark question and -0.67 on a 2 mark one. MSQ and NAT carry no penalty. Unanswered questions score zero either way.

## What it prints

Question counts by type, how many you answered and skipped, correct and incorrect counts per type, negative marks split by 1 mark and 2 mark MCQs, and the final total. There is also a line for questions attempted ignoring wrong NATs and MSQs, which is the number worth looking at if you want to know how aggressive you were on the questions that could actually hurt you.

## Notes

Answers are matched by exact string, including NAT values. If the key says `3.5` and you entered `3.50`, it counts as wrong. Adjust the key to match how you typed it.
