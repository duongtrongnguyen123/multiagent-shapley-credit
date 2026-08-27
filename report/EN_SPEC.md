# Shared spec — Vietnamese → English rewrite of BAO_CAO_NHOM13.tex

Every agent working on a slice of this report MUST follow this file exactly.

## What this document is

A university course report (INT3406, NLP, VNU University of Engineering and Technology) on
multi-agent LLM systems. Four roles — planner, solver, verifier, aggregator — chained into a
pipeline. The group measures whether splitting work across roles beats one model running alone.
**Most findings are negative**, and that is the point of the report, not a flaw. Preserve that.

## Your job

Rewrite your assigned slice from Vietnamese into English. This is a **rewrite, not a
translation**: produce prose an English-speaking researcher would write, not Vietnamese
sentence structure carried over. Then apply the content fixes listed in your own task prompt.

## HARD RULES — violating any of these breaks the document

1. **Never change a number.** Not one digit. But **convert the decimal separator**: Vietnamese
   `$0{,}252$` becomes `$0.252$`, and `0,252` in plain text becomes `0.252`. Ranges like
   `73--81\%` stay. Do this everywhere, including inside tables and captions.
2. **Never change `\label{...}`, `\ref{...}`, `\cite{...}` keys.** They are cross-references.
   Labels stay in their original form (`tab:shapley` stays `tab:shapley`), only surrounding
   prose changes.
3. **Never change table structure** — same number of `&` per row, same `\\`, same column spec.
   Translate only the words inside cells and the caption.
4. **Never change these macros**: `\dceil`, `\dhonest`, `\CEIL`, `\acc`, `\mucB`. Use them where
   the original does.
5. **Never strengthen or weaken a claim.** If the Vietnamese says a confidence interval contains
   zero, or that something is below threshold, or that a result is not established, the English
   must say exactly that. Do not turn "not distinguishable from zero" into "zero" or into
   "negative". Do not add "significantly" anywhere.
6. **Do not invent content.** If something is unclear, keep it as close to the original as you
   can and note it in your final report back to the orchestrator.
7. **Do not touch the preamble** (lines before `\begin{document}`) unless your slice is P0.
8. **Do not compile the document.** The orchestrator will splice and compile.

## Terminology

| Vietnamese | English |
|---|---|
| model | model |
| vai trò | role |
| pipeline | pipeline |
| lần sinh | generation (a single sampled solution) |
| lượt gọi model | model call |
| trace | trace |
| pool | pool |
| mức dao động nền | noise floor |
| ngưỡng hiệu dụng | effective threshold |
| tiềm năng cải thiện | headroom |
| khả năng khai thác | exploitability |
| chốt trước | pre-registered / fixed in advance |
| thí nghiệm tác động artifact | artifact-exposure experiment |
| artifact | artifact (the weak model's solution) |
| tầng / phân tầng | stratum / stratification |
| fold | fold |
| bộ tổng hợp | aggregation method |
| bỏ phiếu đa số | majority voting |
| khoảng tin cậy (KTC) | confidence interval (CI) |
| ước lượng điểm | point estimate |
| độ chính xác | accuracy |
| điểm (đơn vị hiệu số accuracy) | points |
| chênh lệch năng lực | capability gap |
| giao thức sửa | repair protocol |
| lối tắt | shortcut (reward hacking) |
| tổ hợp | coalition |
| giá trị Shapley | Shapley value |
| người chơi (lý thuyết trò chơi) | player |
| tiên đề hiệu quả / đối xứng | efficiency / symmetry axiom |
| ống dẫn | conduit |
| mốc so sánh | baseline |
| đối chứng | control |

Symbols keep their existing meaning: $W$ weak model, $I$ strong model run independently,
$E$ strong model exposed to the artifact, $P/S/V/A$ the four roles, $G$ gain, $L$ loss,
$R$ rescue, $\kappa$ exploitability, $\varphi_i$ Shapley value of role $i$.

## Style

- Neutral and descriptive. State what was measured. No sales language.
- **Banned words**: significantly, dramatically, remarkably, substantially, powerful, impressive,
  crucially, notably, clearly demonstrates, proves.
- Prefer "we measured / we ran / we found" over passive constructions where it reads better.
- Short sentences. Break long Vietnamese sentences into two or three English ones.
- Section and subsection titles are **assertions**, not labels. The Vietnamese titles already
  work this way — keep that. Example: "Phân rã đóng góp theo vai trò bằng giá trị Shapley"
  becomes "Decomposing role contributions with Shapley values", not "Shapley Analysis".
- Use `--` for en-dashes as the original does. Keep `\emph{}` emphasis where the original has it.

## Output

Write your rewritten slice back to the **same file path you were given**, replacing its
contents. Keep the LaTeX valid: balanced braces, balanced environments. Do not add a preamble
or `\begin{document}` unless your slice already had one.

Then report back to the orchestrator: how many lines you wrote, which content fixes you applied,
and anything you could not resolve.
