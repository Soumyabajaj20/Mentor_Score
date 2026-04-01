# Ideation Document — Mentor Scoring System
## WnCC Seasons of Code | Convenor Assignment 2026-27

---

## 1. Functional Form for Responsiveness R(t_avg)

**Chosen form:** Exponential decay

```
R(t_avg) = exp(-λ * t_avg),   λ = 0.05
```

**Why exponential?**

The key insight is that the *marginal penalty* for being slow should itself decrease as response time grows. Consider two scenarios:
- Mentor A replies in 1 hour vs. 3 hours — that 2-hour difference is huge for a stuck student.
- Mentor B replies in 48 hours vs. 50 hours — that 2-hour difference is essentially irrelevant.

A linear function R = 1 - c*t treats both equally. An exponential function captures the correct intuition: early delays are disproportionately costly, later delays matter less.

**Why λ = 0.05?**

| t_avg | R(t) |
|-------|------|
| 2h    | 0.90 |
| 10h   | 0.61 |
| 24h   | 0.30 |
| 48h   | 0.09 |

These thresholds feel reasonable: a mentor who responds within 2 hours gets a near-perfect score; one who takes a full day gets penalised significantly but not eliminated.

---

## 2. Weight Justification

**Final weights: w1=0.35, w2=0.25, w3=0.25, w4=0.15**

| Component | Weight | Justification |
|-----------|--------|---------------|
| P — Progress | 0.35 | Student progress is the **ultimate outcome** of mentorship. All other signals are proxies; this is the direct measure. It receives the highest weight. |
| R — Responsiveness | 0.25 | Response time has an *immediate, concrete* effect on student momentum. A stuck student who waits 24h loses an entire day. This is the most impactful process metric. |
| E — Engagement | 0.25 | Meetings and code reviews drive learning depth. Equal to R because without engagement, even fast responses are shallow. |
| F — Feedback | 0.15 | Student ratings are subjective and prone to bias. They are a genuine signal but the least reliable one, so they get the lowest weight. |

**Sum check:** 0.35 + 0.25 + 0.25 + 0.15 = 1.00 ✓

---

## 3. Feedback Bias Handling

### Trimmed Mean
For mentors with 3+ ratings, the single highest and single lowest rating are dropped before averaging. This eliminates the effect of a student who gives a 1 because of a disagreement, or an unearned 5 from a personal friend.

### IQR-based Outlier Down-weighting (Bonus Question)
For mentors with 4+ ratings, we compute the Range (IQR) of their ratings. Any rating that falls outside the range [Q1 − 1.5×IQR, Q3 + 1.5×IQR] is considered "suspicious" and its weight is halved rather than zeroed. We halve rather than remove it because even biased feedback can contain a real signal.

**Why IQR and not standard deviation?**
IQR is more robust to outliers than standard deviation — the very thing we are trying to detect. Using standard deviation to detect outliers is circular because extreme values inflate the SD, making them harder to flag.

### Bayesian Method
```
F_smoothed = (n × trimmed_mean + k × μ₀) / (n + k)
```
- n = number of ratings
- μ₀ = global mean rating across all mentors
- k = 3 (prior strength, equivalent to 3 "neutral" ratings at the global mean)

**Effect:** A mentor with 1 rating of 5 gets a score close to the global mean, not a perfect 1.0. A mentor with 20 ratings of 5 gets a score very close to 1.0. This rewards consistency over luck.
So that mentor with more reviews and equal rating is placed higher than the person with same rating and less number of reviews.

---

## 4. Score Evolution Over Time (Theoretical Design)

Since only aggregated data was provided, we describe the system that would be used with weekly snapshots.

**Rule :**
```
M_{t+1} = (1 - α) × M_t  +  α × M_current
```
- α = 0.4
- Gives 40% weight to the most recent week, 60% to accumulated history

**Why α = 0.4?**
- Too high (e.g. 0.9): score becomes volatile — one bad week tanks a good mentor
- Too low (e.g. 0.1): score barely responds to genuine improvement or decline
- 0.4 balances responsiveness with stability

---

## 5. Activity Decay (Theoretical Design)

**Rule:** If a mentor has had zero interactions with any mentee for 2 consecutive evaluation periods (2 weeks), apply:
```
M_new = M_old × (1 - d),   d = 0.10
```

**Why d = 0.10?**
- A 10% decay per inactive period is noticeable in rankings but not catastrophic.
- After 1 inactive period: score = 90% of previous
- After 3 inactive periods: score ≈ 73%
- After 7 inactive periods: score ≈ 48%
- This gives inactive mentors a clear signal without permanently punishing a mentor who took a brief break (e.g., family vacation trip).

**Recovery:** Once the mentor re-engages, their current period score M_current will naturally be non-zero, and the exponential smoothing update rule will begin rebuilding their score.

---

## 6. Normalisation Across Mentors

Two strategies ensure cohort size does not introduce bias:

1. **Per-mentee normalisation in E:** All engagement metrics (meetings, code reviews, messages) are divided by the number of students the mentor supervises before being used in the score. A mentor with 10 students and 50 total meetings gets the same per-mentee score as a mentor with 5 students and 25 meetings.

2. **Min-max normalisation in E:** After computing per-mentee scores,i have  normalised across all mentors to [0, 1]. This ensures the engagement score is comparable in scale to P, R, and F.

3. **Progress score P:** Uses a ratio (milestones completed / total milestones), which is inherently scale-independent.

4. **Feedback score F:** Uses a per-student mean, so having more students simply means more data points — it does not inflate the score.

---

## 7. Multiple Project Participation (Bonus)

Mentors who supervise students across multiple projects are handled correctly because:
- All metrics are aggregated across **all** of a mentor's students (regardless of project)
- Per-mentee normalisation means a mentor with students in 3 projects is not penalised vs. one with students in 1 project

The `Projects` column in `mentors.csv` is informational. The source of truth for which students a mentor supervises is `interactions.csv`, which captures every (mentor, student) pair directly.

---

## 8. Assumptions

1. Milestones are completed sequentially (1 → 2 → 3...) — so "3 milestones completed" means milestones 1, 2, and 3 are done.
2. `AvgResponseTime` in `interactions.csv` is already the mean over all queries within a mentor-student pair (not raw timestamps).
3. A mentor with no entries in `interactions.csv` or `feedbacks.csv` receives a score of 0 for those components.
4. Each evaluation period ≈ 1 week (as specified in the clarification).
