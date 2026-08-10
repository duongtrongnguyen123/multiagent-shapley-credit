# Self-assessed difficulty can't route: 142/150 collapse onto level 4–5

## Setup (MATH 1.5B, n=150)

`selflevel-math` kernel: Qwen2.5-1.5B reads each MATH question and self-ratings difficulty 1–5 (one cheap generation call). Joined to `results_rescue/math` traces by idx for `alone_correct` (Solver-by-itself).

## Core numbers

| self_level | n | S-alone acc |
|---|---|---|
| 1 | 1 | .000 |
| 2 | 1 | .000 |
| 3 | 6 | .500 |
| **4** | **101** | **.505** |
| **5** | **41** | **.195** |
| total | 150 | — |

**142/150 (95%) self-assign 4 or 5.** Only 8 questions rated 1–3. Pearson(self_level, alone_ok) = **−0.167** — weak *negative*, i.e. self-rated harder questions are *slightly less likely* to be solved, but the signal is nearly useless because the scale is not used.

`true_level` (Hendrycks) matched **0/150** — the join failed (MATH/train texts didn't match test-500 after normalize; the dataset's train files were loaded but no problem matched). So human-level baseline is **indistinguishable in this run**; but the self-assessed result is decisive on its own.

## Verdict

**Self-assessed level is NOT a viable routing signal.** The 1.5B model cannot discriminate difficulty: it pegs 95% of questions at 4–5. Even if it did, routing on perceived difficulty does not tell us which coalition actually solves a question – two questions both rated "4" have S-alone accuracies spanning .195–.505.

This is the same class of failure as H3 gate / fidelity / output-length: the model's *self-report* does not predict its *ability*.

## What DID correlate (recap from `DIFFICULTY_STRATA.md`)

The only signal shown to matter is **measured consensus among K independent solver samples**:
- 0/5 correct (too hard) and 5/5 (too easy) both have **high agreement** (all-wrong / all-right)
- middle strata (1–4/5) have low agreement → voting helps most there (+21.5pts)
- consensus is **observable without the gold answer** → usable at inference

So the viable router is not "classify difficulty from the question" but **"run K cheap samples, watch agreement, escalate/downgrade"** — exactly the consensus-router family `nguoi3-router` already prototyped (agree → stop at S+V, disagree → add A).