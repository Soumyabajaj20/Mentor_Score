import math
import pandas as pd
import numpy as np

W1, W2, W3, W4 = 0.35, 0.25, 0.25, 0.15

def load_data():
    mentors      = pd.read_csv("mentors.csv")
    students     = pd.read_csv("students.csv")
    interactions = pd.read_csv("interactions.csv")
    feedbacks    = pd.read_csv("feedbacks.csv")
    return mentors, students, interactions, feedbacks

def compute_p(interactions, students):

    df = interactions[["MentorID", "StudentID"]].merge(
        students[["StudentID", "MilestonesCompleted", "TotalMilestones"]],
        on="StudentID", how="left"
    )

    df["TotalMilestones"] = df["TotalMilestones"].replace(0, np.nan)

    k = df["MilestonesCompleted"]
    n = df["TotalMilestones"]

    df["P_student"] = (k * (k + 1)) / (n * (n + 1))

    P = df.groupby("MentorID")["P_student"].mean()
    return P

LAMBDA = 0.05

def compute_r(interactions):

    avg_t = interactions.groupby("MentorID")["AvgResponseTime"].mean()

    R = np.exp(-LAMBDA * avg_t)
    return R

ALPHA_MEETINGS  = 0.30
ALPHA_REVIEWS   = 0.50
ALPHA_MESSAGES  = 0.20

def compute_e(interactions):

    agg = interactions.groupby("MentorID").agg(
        total_meetings=("Meetings",    "sum"),
        total_reviews =("CodeReviews", "sum"),
        total_messages=("Messages",    "sum"),
        num_students  =("StudentID",   "count")
    )

    agg["meetings_pm"]  = agg["total_meetings"]  / agg["num_students"]
    agg["reviews_pm"]   = agg["total_reviews"]   / agg["num_students"]
    agg["messages_pm"]  = agg["total_messages"]  / agg["num_students"]

    agg["E_raw"] = (
        ALPHA_MEETINGS * agg["meetings_pm"] +
        ALPHA_REVIEWS  * agg["reviews_pm"]  +
        ALPHA_MESSAGES * agg["messages_pm"]
    )

    e_min = agg["E_raw"].min()
    e_max = agg["E_raw"].max()

    if e_max == e_min:
        agg["E"] = 0.5
    else:
        agg["E"] = (agg["E_raw"] - e_min) / (e_max - e_min)

    return agg["E"]

BAYESIAN_K = 3 

def trimmed_weighted_mean(ratings):

    ratings = list(ratings)
    n = len(ratings)

    if n == 0:
        return np.nan

    weights = {i: 1.0 for i in range(n)}

    if n >= 3:
        min_idx = ratings.index(min(ratings))
        max_idx = ratings.index(max(ratings))
        weights[min_idx] = 0.0
        weights[max_idx] = 0.0

    if n >= 4:
        arr = np.array(ratings)
        q1, q3 = np.percentile(arr, 25), np.percentile(arr, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        for i, r in enumerate(ratings):
            if r < lower or r > upper:
                weights[i] = min(weights[i], 0.5)

    total_weight = sum(weights.values())
    if total_weight == 0:
        return np.mean(ratings) 

    weighted_sum = sum(ratings[i] * weights[i] for i in range(n))
    return weighted_sum / total_weight


def compute_f(feedbacks):

    global_mean = feedbacks["Rating"].mean()

    results = {}
    for mentor_id, group in feedbacks.groupby("MentorID"):
        ratings = group["Rating"].tolist()
        n = len(ratings)

        trimmed = trimmed_weighted_mean(ratings)

        smoothed = (n * trimmed + BAYESIAN_K * global_mean) / (n + BAYESIAN_K)

        f_normalized = (smoothed - 1) / 4

        results[mentor_id] = f_normalized

    return pd.Series(results, name="F")

def compute_mentor_scores(mentors, students, interactions, feedbacks):
    P = compute_p(interactions, students)
    R = compute_r(interactions)
    E = compute_e(interactions)
    F = compute_f(feedbacks)

    scores = mentors[["MentorID", "Name", "Domain", "Projects"]].copy()
    scores = scores.set_index("MentorID")

    scores["P"] = P
    scores["R"] = R
    scores["E"] = E
    scores["F"] = F

    scores[["P", "R", "E", "F"]] = scores[["P", "R", "E", "F"]].fillna(0)

    scores["MentorScore"] = (
        W1 * scores["P"] +
        W2 * scores["R"] +
        W3 * scores["E"] +
        W4 * scores["F"]
    )

    scores["Rank"] = scores["MentorScore"].rank(ascending=False, method="min").astype(int)

    scores = scores.sort_values("Rank")
    scores = scores.reset_index()

    return scores

ALPHA_SMOOTH = 0.4

def update_score_over_time(M_prev, M_current):
    return (1 - ALPHA_SMOOTH) * M_prev + ALPHA_SMOOTH * M_current

DECAY_RATE = 0.10

def apply_decay(M_old):
    return M_old * (1 - DECAY_RATE)

def print_table(scores):
    output = scores[["Rank", "MentorID", "Name", "Domain",
                      "P", "R", "E", "F", "MentorScore"]].copy()
    output = output.round(4)
    print("\n" + "="*85)
    print("  MENTOR SCORE RANKINGS — WnCC Seasons of Code")
    print("="*85)
    print(output.to_string(index=False))
    print("="*85)
    print(f"\nWeights used: P={W1}, R={W2}, E={W3}, F={W4}")
    print(f"Smoothing α={ALPHA_SMOOTH}, Decay d={DECAY_RATE}, λ={LAMBDA}\n")


def save_csv(scores):
    output = scores[["MentorID", "Name", "MentorScore", "Rank"]].copy()
    output = output.round(4)
    output.to_csv("mentor_scores.csv", index=False)
    print("Saved mentor_scores.csv")

if __name__ == "__main__":
    mentors, students, interactions, feedbacks = load_data()
    scores = compute_mentor_scores(mentors, students, interactions, feedbacks)
    print_table(scores)
    save_csv(scores)