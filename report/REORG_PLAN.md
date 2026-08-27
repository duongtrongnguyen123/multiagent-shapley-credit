# Reorganisation plan — REPORT_GROUP13.tex

Shared context for every agent working on this reorganisation. Read this **and** `EN_SPEC.md`.

## The change in one sentence

The report currently has two theses and commits to neither. We are making the **same-capability
role-specialisation** result the spine, and demoting the cross-capability artifact experiment to
a supporting role: it explains why the obvious fix to the first problem also fails.

## Old thesis (being demoted)

"Showing a strong model a weak model's solution costs 27.2 points." True, well measured, but it
is a claim about context contamination, not about whether dividing labour among agents works.
It also drags in the $G/L/R$ identity, the capability-gap regression and the cross-domain
transfer test — the weakest material in the report (wide intervals, non-monotonic, 3 pairs).

## New thesis (the spine)

**The roles do not do what they are named.** When one model is split into planner, solver,
verifier and aggregator, the model ignores the role boundaries. What looks like a gain from
coordination is mostly the gain from sampling the model more than once.

Evidence, all at a single model size:

| Finding | Number |
|---|---|
| Shapley with the solver held fixed | P+V+A add 4.9 points on GSM8K, nothing measurable on MATH |
| Re-solving without reading the critique | 0.453 = 0.453 — the feedback content contributes nothing |
| LLM aggregation vs counting votes | `llm_agg@8` loses to `maj@8` by 19--26 points |
| Planner told not to solve, on maths | Still contains the correct answer 33.3% of the time |
| Same instruction removed | Leakage rises to 48.5%, solver gains +3.3 points |
| Planner told not to write code | Still writes code 53.7% of the time; told to, 100% |
| Planner on HumanEval | **Net harmful: 0.5375 with no planner, 0.4312 with one, 5/5 folds** |
| Solver given a plan | Produces no new numeric content 62.0% of the time |
| Aggregator | 3 new-and-correct answers in 2000 turns |
| Verifier at its own size | Intervention accuracy 56--59%, blind to injected digit errors |
| Seven training methods | All seven found a shortcut instead of learning the role |

## New evidence not yet in the report

Two experiment sets were run and never written up. Both live on the `archive` branch.

**`res_pa_g15` / `res_pa_m15`** — the planner-prompt study on maths. Three conditions: HIDE
("Do NOT compute the final answer"), FREE (no prohibition), ASK ("and compute the final answer").
GSM8K: plan already contains the answer in 33.3% / 48.5% / 46.3% of cases; solver downstream
0.6700 / 0.7025. MATH: leakage 21.3% / 27.8% / 25.0%; solver 0.4075 / 0.4450. 5 folds.

**`res_pc_he`** — the same study on HumanEval, 5 folds x 32 problems. No planner 0.5375;
HIDE 0.4312; FREE 0.3812; ASK 0.4437. Plan contains code: 53.7% / 73.8% / 100.0%.
`P_hide` is at or below `NoP` in 5/5 folds. `free_minus_hide` is negative in 4/5 folds.

The direction differs by domain and that is the point: a leaked arithmetic answer acts as a free
second attempt and helps a little; a leaked half-implementation anchors the solver and hurts.
Either way what is measured is not planning.

## New section order

| New | Title | Comes from |
|---|---|---|
| 5.1 | What the four-role pipeline appears to gain | unchanged |
| 5.2 | The gain is in extra generations, not in coordination | unchanged |
| 5.3 | Credit by role, with the solver held fixed | unchanged |
| **5.4** | **The planner does not plan** | NEW + part of old "assigned vs executed" |
| **5.5** | **The verifier does not verify at its own capability** | old "assigned vs executed" |
| **5.6** | **The aggregator does not aggregate** | old "assigned vs executed" |
| 5.7 | How much of the benchmark any mechanism can reach | old denominator section |
| 5.8 | Against a single strong model, on accuracy and on cost | old baseline section |
| **5.9** | **Making the checker stronger: what it buys and what it costs** | old artifact section, reframed |
| 5.10 | Objective versus learned verification signals | unchanged |
| 5.11 | Training the roles: seven objectives, seven shortcuts | unchanged |
| App. A | Capability gap and cross-domain transfer | old 5.7 + 5.8, compressed |

## Rules for this reorganisation

1. **Do not delete measurements.** Material that leaves the main text goes to the appendix. The
   limitations section stays complete.
2. **Do not restate a number differently from elsewhere in the report.** If you need a figure
   that another section owns, quote it exactly.
3. Section 5.9 keeps every number it has, including $-27.2$ and $+3.8$ and the 2x2 table. Only
   its framing changes: it is no longer the centrepiece, it is the answer to "so just use a
   stronger checker, then?".
4. Keep all `\label{}` keys as they are, even where a section moves or is renamed. Renaming
   labels breaks cross-references in sections you do not own.
5. Everything in `EN_SPEC.md` still applies: no changed numbers, no strengthened claims, no
   banned words, neutral register.
