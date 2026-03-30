# Mentor Scoring System
### WnCC Seasons of Code — Convenor Assignment 2026-27

---

## Project Structure

```
mentor_scoring/
├── score.py          ← Main script: computes and ranks mentor scores
├── requirements.txt  ← Python dependencies
├── IDEATION.md       ← Design choices, justifications, assumptions
├── mentor_scores.csv ← Generated output (ranked mentor list)
├── mentors.csv       ← Input: mentor information
├── students.csv      ← Input: student milestone data
├── interactions.csv  ← Input: mentor-student interaction data
└── feedbacks.csv     ← Input: student ratings for mentors
```

---

## Setup Instructions

**1. Clone / download the repository**

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Ensure all four CSV files are in the same directory as `score.py`**
- `mentors.csv`
- `students.csv`
- `interactions.csv`
- `feedbacks.csv`

**4. Run the script**
```bash
python score.py
```

---

## Output

The script produces two outputs:

1. **Console table** — ranked list of all mentors with individual component scores (P, R, E, F) and final Mentor Score
2. **`mentor_scores.csv`** — CSV file with columns: `MentorID`, `Name`, `MentorScore`, `Rank`

Mentors are sorted in **descending order** of their final Mentor Score.

---

## Scoring Formula

```
M(m) = 0.35×P  +  0.25×R  +  0.25×E  +  0.15×F
```

| Component | Description |
|-----------|-------------|
| P | Student Progress Score — weighted milestone completion ratio |
| R | Responsiveness Score — exponential decay on avg response time |
| E | Engagement Score — per-mentee meetings, code reviews, messages |
| F | Feedback Score — Bayesian-smoothed, trimmed student ratings |

For full design justification, see `IDEATION.md`.

---

## How to Reproduce Results

Simply run `python score.py` with all four CSV files present. The script is deterministic — the same input always produces the same output.
