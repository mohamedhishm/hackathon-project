# MASTER PROMPT — Complete "Buy or Wait?" (HackerRank Orchestrate, Sept 2026)

You are taking over an in-progress repository from a senior engineer. Phases 1–4 are
implemented. Your job is to (a) do a **quick, targeted audit** of Phases 1–4 and fix only
what materially affects correctness/score, then (b) **fully implement Phases 5–9** and
leave the project submission-ready. Do not rewrite working code for style. Do not skip
ahead — work phase by phase, run tests after each phase, and report what you changed and why.

The dataset is **not present yet**. Work from the code/docs below to understand its shape;
once `dataset/` is dropped in at the repo root, re-run everything against the real data
before finalizing `output.csv`.

---

## 0. Ground truth: what this system must produce

Read `problem_statement.md` / `README.md` / `Buy_or_Wait_HackerRank.md` in full — they are
the authoritative spec (they are consistent with each other; where they differ, the more
detailed `problem_statement.md` wins). In one sentence: for every row of
`dataset/requests.csv`, deterministically decide `amount_safe_to_pay`,
`affordability_status`, `recommended_payment_method`, `payment_plan`,
`earliest_date_for_full_payment`, `spending_changes_needed`, `decision_explanation`, using
a 90-day cash-flow simulation, and write one row per request to `output.csv` (root) and
`dataset/output.csv`, in that exact column order.

Core architectural law already established and must be preserved:

> **The LLM describes. Deterministic Python decides.** Extraction (`extraction_schema.py`,
> whatever LLM client you add) only answers "what does the evidence say?". `forecaster.py`,
> `logic.py`, and `validator.py` own every number, date, and decision.

---

## 1. Current repository map (already built)

| File | Phase | Responsibility |
|---|---|---|
| `code/data_loader.py` | 1 | CSV → typed dataclasses (`Profile`, `FinancialEvent`, `PaymentOption`, `Message`, `ImageRecord`, `Request`, `SampleRequest`) + indexes in `LoadedData`. Preserves `missing != 0`. Validates FK references. |
| `code/schemas.py` | 2 | Pydantic v2 mirrors of the loader dataclasses (`from_attributes=True, extra="forbid"`) for validation/serialization at boundaries. |
| `code/extraction_schema.py` | 3 | Strict `RequestExtraction` Pydantic contract an LLM must fill (`item`, `amount`, `currency`, `partial_payment_intent`, `mentioned_dates`, `future_income_mentions`, `spending_change_mentions`), each with `Evidence` provenance. **No decision fields allowed (`extra="forbid"`).** |
| `code/evidence.py` | "3.5" | **Regex-only**, non-LLM extractor (`extract_message_evidence`) that pulls salary overrides, rent increases, arrears, contract-end, invoice confirmations out of `message_text` via hand-written patterns (English + Indonesian). Returns `ExtractedMessageEvidence`. |
| `code/forecaster.py` | 4 | `convert_currency` (fixed-date FX), `detect_recurring_streams` (cadence detection), `simulate_timeline` (91-day balance projection), `compute_amount_safe_to_pay`, `find_earliest_full_date`. |
| `code/logic.py` | 5 (started) | `CandidatePlan` dataclass + `evaluate_request`: generates Candidates A (full payment now), B (installments from `request_payment_options.csv`), C (partial payment), D (full payment + spending changes), E (wait), filters by deadline, ranks, returns best. |
| `code/validator.py` | 6 (started) | `validate_plan`: bounds check, method-allowed check, status/method coherence, spending-change legality, installment-option match, 90-day re-simulation of the chosen plan. |
| `code/main.py` | orchestration | Loads data, runs evidence → forecast → logic → validator per request, writes `output.csv` / `dataset/output.csv`, writes a **hardcoded, zero-token** `evaluation/usage_report.md`. |
| `code/test_schema.py`, `code/test_extraction_schema.py` | tests | Smoke tests for Phases 2 and 3 contracts only. |
| `shap_data_loader.py` | reference | **Not runnable code** — a hand-worked example trace (user_02, user_14) showing the intended reasoning for two sample requests. Treat this as a worked answer key / spec clarification, not a module to import. |

Also present: `README.md`, `problem_statement.md`, `Buy_or_Wait_HackerRank.md` (spec, mostly
redundant with each other), and this progress log (treat as authoritative on what's "done"
vs "next").

---

## 2. Phase 1–4 audit — confirmed issues to fix (do these first)

These are concrete, code-level findings from reading the current implementation. Fix them
before building Phase 5 on top, because Phase 5's plan ranking inherits every bug below.

### 2.1 Critical: the "LLM extraction layer" is never actually called, and images are never read at all
- `extraction_schema.py` defines the contract, and `test_extraction_schema.py` tests the
  contract — but there is **no LLM client code anywhere** (no prompt templates, no API
  call, no Groq/OpenAI/Anthropic wiring) that actually produces a `RequestExtraction`.
- `main.py` only calls `extract_message_evidence` (regex-based, `evidence.py`), never
  touches `extraction_schema.RequestExtraction`.
- **Images are never opened, OCR'd, or vision-parsed anywhere in the pipeline.** The spec
  is explicit: *"When a financial event has a blank `amount`, use its `event_id` to find
  the matching `related_event_id` in `images.csv`, then extract the amount from that
  image... Do not treat a blank amount as zero."* Currently, any `FinancialEvent` with
  `amount is None` is silently skipped in `simulate_timeline` (`if amt is None: continue`)
  — this is exactly the "treat blank as zero/ignore" behavior the spec forbids.
- **Fix required**: Build a real (even if minimal) LLM extraction step for Phase 5/9:
  - Add an LLM client module (`code/llm_client.py` or similar) using structured output
    (JSON mode / tool-calling) that fills `RequestExtraction` for `request_text` +
    relevant messages, and a parallel **image extraction** call (vision-capable model) that
    returns `{event_id, amount, currency, statement_date}`-shaped facts matching
    `ExtractedImageEvidence` in `evidence.py` (already defined, but nothing populates it —
    check: is `ExtractedImageEvidence` used anywhere? If not, wire it up).
  - Track every call for `evaluation/usage_report.md` (see §7) — the current report is
    hardcoded to "0 model calls / $0.00", which will misrepresent the true system once you
    add LLM calls, and will also be **factually wrong if you keep it while actually using
    an LLM for extraction**. Decide deliberately: either (a) truly keep this deterministic
    with zero LLM calls and instead do deterministic OCR/parsing for images (e.g.
    regex/heuristic on OCR text, still "LLM-free"), and update `problem_statement.md`
    compliance reasoning accordingly, or (b) add real LLM calls and report real usage. Pick
    (b) unless you have a strong deterministic alternative for image reading — vision
    extraction genuinely needs a model.
  - Whichever you choose, resolve blank `amount` events from images before they enter
    `simulate_timeline`/`detect_recurring_streams`. Do this as a pre-processing step
    (e.g. `resolve_event_amounts(events, images_by_event, extracted_image_evidence) ->
    Sequence[FinancialEvent]`) that returns event objects with amounts filled in from
    image evidence — never mutate `LoadedData` in place (matches the existing
    "non-mutating" design principle stated in `evidence.py`'s docstring).

### 2.2 `main.py` computes `validate_plan` but never acts on the result
- `val_result = validate_plan(...)` is computed and then **discarded**. If the validator
  finds the chosen plan unsafe/invalid, the pipeline currently ships it anyway.
- **Fix**: `main.py` must branch on `val_result.is_valid`. On failure, either (a) fall back
  deterministically to the next-best candidate plan (requires `evaluate_request` to expose
  its full ranked candidate list, not just the winner — see §3.1), or (b) fall back to the
  safe default (`not_affordable` / `not_recommended` / `payment_plan=none`) and log the
  validator errors for `evaluation/` diagnostics. Prefer (a): re-validate down the ranked
  list until one passes, only falling back to `not_recommended` if none do. Log every
  validator failure (which request, which candidate, which errors) for the Phase 7 report.

### 2.3 `compute_amount_safe_to_pay` hardcodes payday to "the 15th of the month"
In `forecaster.py`:
```python
for i in range(1, 35):
    day = d0 + timedelta(days=i)
    if day.day == 15:
        next_salary_d = day
        break
```
This assumes every user's income lands on calendar day 15, which is only true for the
worked example (`user_02`, `user_14` salaries settle on the 15th). Any user with a
different payday, a weekly/biweekly income stream, multiple income streams, or no
detected recurring income at all will get a wrong "buffer window," because
`compute_amount_safe_to_pay` picks an arbitrary day-15 cutoff instead of the user's actual
next confirmed inflow.
- **Fix**: Derive `next_salary_d` from the actual detected income streams / dataset future
  income events for that user (reuse `detect_recurring_streams` filtered to
  `event_type == 'income'`, plus any dataset-confirmed future credit within the window),
  falling back sensibly (e.g. 30 days, or end of horizon) only when no income is detected
  at all. This function's output feeds directly into `amount_safe_to_pay`, one of the most
  heavily-weighted scored fields — get this right.
- Also reconsider whether `amount_safe_to_pay` should really only look at the buffer
  *before the next payday* rather than the full 90-day minimum-buffer (the safety
  definition in the spec is about the balance never dropping below minimum over the whole
  horizon, not just until next payday — verify your interpretation is consistent between
  `compute_amount_safe_to_pay` and `validate_plan`'s 90-day check, and with the worked
  example in `shap_data_loader.py`).

### 2.4 `detect_recurring_streams` requires ≥2 historical occurrences (except salary) and exact `(event_type, category, description, direction)` match
- A flexible/protected expense that has occurred only once in history (e.g. a new
  subscription, a first-time rent record before a second month posts) will never be
  detected as recurring and will silently disappear from the 90-day forecast — this can
  make an unsafe plan look safe.
- Exact-string match on `description` is brittle (`"Municipal utilities"` vs any
  whitespace/casing variant would break grouping) — confirm against the real dataset
  whether descriptions are always identical per stream (`shap_data_loader.py`'s
  transcript suggests they are, but verify against the actual `financial_events.csv`
  once available; don't assume).
- **Fix**: At minimum, add explicit handling/flagging for single-occurrence recurring-shaped
  categories (e.g., known fixed categories like `rent`, `housing`, `insurance`, `education`
  even with 1 data point, treated as monthly going forward) rather than silently dropping
  them — but do this conservatively (a missed expense is more dangerous than a
  double-counted one, per the "financially safer interpretation" conflict rule). Document
  the decision in `decision_explanation`/logs when you do this.

### 2.5 `logic.py`, Candidate D: hardcoded magic fallback date
```python
earliest_date_for_full_payment=earliest_full_date or (d0 + timedelta(days=12)),
```
`+12 days` is an arbitrary magic number with no grounding. If `earliest_full_date` is
`None` (full payment is never safe even 90 days out without spending changes), this
Candidate should compute its **own** earliest-safe-date under the *same spending-change
combo* (there's already `find_earliest_full_date(..., spending_changes=combo)` support in
`forecaster.py` — it's just not called here), not invent a date.
- **Fix**: call `find_earliest_full_date(profile, user_events, msg_evidence,
  exchange_rates, d0, req_amt, desired_completion_date=comp_date,
  spending_changes=combo)` for Candidate D and use that result (or `d0` if it's already
  safe today with the combo applied, or leave empty if never safe).

### 2.6 `logic.py`, installment eligibility check is logically wrong
```python
duration_months = (num_pmts * freq_days) // 30
if num_pmts > profile.max_installment_months and duration_months > profile.max_installment_months:
    continue
```
This only excludes an option when **both** the payment count *and* the computed duration
exceed the max — an 18-payment/31-day-frequency plan (duration ≈ 18 months) with
`max_installment_months=7` should clearly be excluded (and the worked example in
`shap_data_loader.py` for `user_02`/`payment_option_07` confirms it must be excluded), but
verify this current `and` doesn't accidentally admit borderline cases where payment count
is small but total duration is long, or vice versa.
- **Fix**: `max_installment_months` should gate on the **plan's total duration** (last
  payment date minus first payment date, in months) — that's the natural reading of "max
  installment *months*." Change the condition to exclude whenever `duration_months >
  profile.max_installment_months` alone (drop the compound `and`/`num_pmts` comparison,
  which mixes a payment count against a month limit).

### 2.7 FX fallback silently uses the *earliest available* rate when no rate exists on/before the needed date
In `convert_currency`:
```python
best_d = max([d for d in all_dates if d <= rate_date], default=all_dates[0])
```
If no rate exists on or before `rate_date`, this falls back to `all_dates[0]` (the
earliest rate in the whole dataset, which could be *later* than `rate_date`), contradicting
the "nearest earlier date" rule implied by the comment above it, and contradicting
`problem_statement.md`'s "Fixed, dated conversion rates" framing (no rate should be
invented from the future relative to the event).
- **Fix**: decide and document the correct fallback: nearest date in either direction, or
  raise/flag if no valid earlier rate exists (this should be rare if the dataset supplies
  what's needed — verify against real `exchange_rates.csv` once available; add a hard
  assertion + logged warning rather than silent wrong-direction fallback).

### 2.8 No output rounding/formatting standard
`main.py` writes `str(safe_amount)` and `logic.py` builds `payment_plan` strings via plain
`f"{amt}"` on raw `Decimal` values that may have come from FX division
(`amount / exchange_rates[...]`) — these can produce long non-terminating decimal
representations inconsistent with the 2-decimal-place style shown in
`sample_requests.csv` / `shap_data_loader.py` (e.g. `IDR 17,229,139.20`,
`15952906.67`).
- **Fix**: standardize rounding to 2 decimal places (or the currency's natural precision —
  confirm IDR is displayed with 2 decimals per the sample data, even though real IDR has no
  minor unit) using `Decimal.quantize()` at the point where output strings are generated
  (`payment_plan`, `amount_safe_to_pay`), not earlier in the simulation (keep full precision
  internally, round only at formatting boundaries).

### 2.9 `data_loader.py` — minor, verify not ignore
- Loader is solid (typed parsing, `missing != 0`/`missing != False` preserved, FK
  validation, sorted indexes). No functional rewrite needed.
- Double-check `_parse_optional_int` for `max_installment_months`: it does
  `int(Decimal(text))`, which **truncates** rather than validates it's a whole number
  (e.g. `"7.9"` → `7` silently). Confirm the real CSV never has fractional months; if it's
  possible, decide whether truncation or rejection is correct and make it explicit either
  way.
- `_index_image_files` requires `media_dir` to exist; if `dataset/media/images/` might be
  fully absent in some environments the harness runs in, confirm graceful behavior
  (currently returns `{}` if the dir doesn't exist — fine — but every `image.exists` will
  then be `False`, meaning any blank-amount event with only that image as evidence
  silently has no resolvable amount; make sure this shows up as a loud warning, not a
  silent zero).

### 2.10 `schemas.py` — no functional issues found
Correctly separates domain contracts from extraction and decision layers, correctly uses
`from_attributes=True, extra="forbid"`, and correctly keeps `financing_fee`/
`max_installment_months`/etc. as `Optional` without defaulting to 0. **Do not rewrite.**
Only revisit if Phase 5/6 code needs a new boundary contract (e.g. a `CandidatePlanSchema`
or `OutputRowSchema` for validating the final CSV rows before writing — recommended, see
§4.3).

---

## 3. Phase 5 — Plan Generation + Ranking (extend, don't replace, `logic.py`)

`logic.py` already has the right shape (5 candidate types + ranking). Your job is to hard
en it, not redesign it.

### 3.1 Expose the full ranked candidate list, not just the winner
Change `evaluate_request` to return `(best: CandidatePlan, ranked: list[CandidatePlan])` (or
add a second function `rank_candidates(...) -> list[CandidatePlan]`) so `main.py` can fall
through to the next-best candidate when `validate_plan` rejects the top one (§2.2).

### 3.2 Re-verify the ranking order matches the spec exactly
Problem statement / README ranking order:
1. Complete full request by `desired_completion_date`
2. Require no spending changes
3. Minimize total amount paid
4. Start payment earlier
5. Use fewer payments
6. Lowest `payment_option_id` (tie-breaker)

Current `sort_key` in `logic.py` filters by (1) via `meets_deadline` *before* sorting
(functionally equivalent to putting it first, since non-meeting candidates are dropped —
confirm this is truly equivalent and not silently dropping candidates that should instead
be ranked lower rather than removed, per the spec's literal wording "rank the plans in this
order," which could be read as a full ordering including infeasible plans as last resort
information for `decision_explanation`, not necessarily removal). Also confirm:
- `total_cost` for `installments` uses `total_payable_amount` (or `pmt_amt * num_pmts`
  fallback) which includes financing fees, while `full_payment`/`partial_payment`/`wait`
  use `requested_amount` with no fee — confirm this is the *intended* apples-to-apples
  comparison for "minimize total amount paid" (it should be, since fees are real cost to
  the user), and add a code comment stating this explicitly so a future reader (or the AI
  Judge) doesn't flag it as a bug.
- `option_id` tie-break: current code uses string comparison
  (`"payment_option_10" < "payment_option_2"` lexicographically!). If `payment_option_id`
  values are not zero-padded, lexicographic sort will misorder `option_10` before
  `option_2`. **Fix**: sort by the numeric suffix if the ID format is `payment_option_<N>`,
  or confirm zero-padding in the real dataset before finalizing.

### 3.3 Handle `investment` and other non-purchase `request_type`s explicitly
Spec: *"Investment requests concern affordability and existing contributions. The task
does not require predicting asset prices or recommending securities."* Confirm
`evaluate_request` treats `investment`/`family_transfer`/`debt_repayment`/
`emergency_expense`/`housing`/`other` uniformly as "a cash outflow of `requested_amount`"
(which the current code already does, since it never branches on `request_type`) — this is
likely correct, but explicitly test it with at least one sample per `request_type` in
Phase 7 to be sure no `request_type` needs special-cased treatment (e.g., should
`emergency_expense` bias toward `full_payment`/`affordable_now` even under tighter margins,
per any priority signals in `financial_priorities`? Re-read `sample_requests.csv` once the
dataset is available for evidence of this before adding special-casing — don't invent
behavior not evidenced by the samples).

### 3.4 Decision explanations must reflect the *actual* fields used
Audit every `decision_explanation` f-string in `logic.py` for accuracy after your fixes
above (e.g. once §2.5's magic `+12 days` is removed, its explanation text must still make
sense; once amounts are rounded per §2.8, explanation strings must use the rounded values,
not raw `Decimal`s).

---

## 4. Phase 6 — Validator (harden `validator.py`)

`validate_plan` already covers bounds, method-allowed, status/method coherence, spending
change legality, installment-option match, and a 90-day re-simulation. Extend it:

### 4.1 Make validation failures block bad output (see §2.2) — this is the single highest-impact Phase 6 change.

### 4.2 Add missing checks
- **Partial-payment structural check**: verify `plan.payment_plan` for
  `recommended_payment_method == 'partial_payment'` has exactly 2 entries, in chronological
  order, summing exactly to `requested_amount`, with the first dated `request_date` and
  the second dated `earliest_date_for_full_payment` — the spec is explicit about this exact
  shape and it's not currently checked independently of `logic.py`'s own construction (i.e.
  the validator should catch it even if `logic.py` has a bug, that's the point of an
  *independent* validator).
- **Stop/reduce mutual exclusion**: spec says "Stopping and reducing the same financial
  event are mutually exclusive... must reference different events" — validator currently
  only checks category-level legality, not that no single `event_id` appears in both a
  `stop:` and a `reduce_to:` entry within the same `spending_changes_needed` string
  (`logic.py`'s combination generator already avoids this by construction, but the
  validator should check it independently too).
- **Chronological order of `payment_plan` entries** — not currently verified.
- **`earliest_date_for_full_payment` empty-string vs `None` handling** — confirm
  `main.py`'s CSV-writing (`.isoformat() if ... else ""`) matches what the validator and
  downstream scoring expect for the "leave empty" case.
- **`affordable_with_plan` invariant**: spec says this status covers "partial-payment
  schedule, installments, or permitted spending changes" — validator should assert the
  `recommended_payment_method` for this status is one of
  `{partial_payment, installments, full_payment-with-spending-changes}` and reject
  contradictions (e.g. `affordable_with_plan` + `recommended_payment_method='wait'`).
- **`decision_explanation` non-empty and non-templated-garbage check** (basic sanity, not
  semantic) — flag empty or clearly-broken explanation strings so Phase 7 evaluation
  catches formatting bugs early.

### 4.3 Add a final CSV-row schema validation pass in `main.py` before writing
Add a small `OutputRowSchema` (Pydantic, `extra="forbid"`) in `schemas.py` or a new
`output_schema.py` validating: `0 <= amount_safe_to_pay <= requested_amount`, allowed enum
values for `affordability_status`/`recommended_payment_method`, `payment_plan` regex shape
or `"none"`, `spending_changes_needed` regex shape or `"none"` with ≤3 `|`-separated
entries, valid ISO date or empty string for `earliest_date_for_full_payment`. Run every
`output_rows` entry through it before `csv.DictWriter` writes — this is a cheap, high-value
last-mile safety net independent of `validate_plan`'s financial-semantics validation.

---

## 5. Phase 7 — Run & evaluate the 25 labeled samples (`dataset/sample_requests.csv`)

1. Build `code/evaluate_samples.py` (new file) that:
   - Loads `sample_requests_by_id` via the existing `DataLoader`.
   - Runs the full pipeline (evidence → forecaster → logic → validator) on each sample's
     underlying `Request` fields.
   - Compares predictions against the labeled columns already on `SampleRequest`
     (`amount_safe_to_pay`, `affordability_status`, `recommended_payment_method`,
     `payment_plan`, `earliest_date_for_full_payment`, `spending_changes_needed`) field by
     field, and reports per-field accuracy plus a diff for every mismatch (predicted vs.
     expected).
   - For `amount_safe_to_pay`, use a small tolerance (e.g. exact match preferred, but flag
     near-misses within 0.01 currency units separately from large misses — real bugs vs.
     rounding).
   - Does **not** hardcode any answer or special-case any `request_id`/`user_id` — if you
     find yourself writing `if request_id == "request_02": ...`, stop, that is exactly the
     "no hardcoded labels" rule violation the README calls out.
2. Manually inspect every mismatch. For each, root-cause it to one of: extraction gap,
   simulation gap, ranking gap, formatting gap, or a genuine ambiguity in the spec — and fix
   the systemic cause in `forecaster.py`/`logic.py`/`evidence.py`/`validator.py`, not the
   sample.
3. Cross-check at least the two worked examples already hand-traced in
   `shap_data_loader.py` (`user_02`/`request_02`, `user_14`/`request_14`) — these come with
   full reasoning trails and expected outputs, so they're your fastest correctness oracle
   for `forecaster.py` and `logic.py` before you even look at the other 23.
4. Produce a short `evaluation/sample_eval_report.md` summarizing per-field accuracy and
   the fixes made as a result.
5. Do not proceed to Phase 8 until sample accuracy is high and every remaining mismatch is
   understood and explainable (not silently ignored).

---

## 6. Phase 8 — Run the full 250 requests

1. Run `python3 code/main.py` end to end against `dataset/requests.csv`.
2. Confirm zero crashes and zero unhandled exceptions — wrap the per-request loop in
   `main.py` with a try/except that logs the failing `request_id` and falls back to a safe
   `not_affordable`/`not_recommended` default rather than aborting the whole run (a single
   malformed row must not sink the batch — but log it loudly, don't swallow silently).
3. Confirm:
   - `output.csv` has exactly 250 data rows + header, in the same `request_id` order as
     `dataset/requests.csv` (or at minimum, exactly one row per `request_id`, no dupes, no
     omissions — verify via a set-equality check against `dataset/requests.csv`'s
     `request_id` column).
   - Every row passes the `OutputRowSchema` validation from §4.3.
   - Every installment `payment_plan` matches a real `payment_option_id`'s schedule
     verbatim (dates and amounts), for every row where `recommended_payment_method ==
     'installments'`.
   - Every `spending_changes_needed` event id is a real, flexible, non-protected event for
     that user.
4. Keep execution deterministic — no reliance on wall-clock time, random seeds, or
   nondeterministic LLM sampling for anything that affects the financial decision (if you
   add LLM extraction per §2.1, use temperature 0 / low temperature and treat its output as
   *evidence* only, never as the final decision, consistent with the architecture).
5. Add basic logging/telemetry (counts per `affordability_status`, per
   `recommended_payment_method`, validator-rejection counts, LLM-call counts) printed at
   the end of the run — cheap and very useful for the AI Judge interview.

---

## 7. Phase 9 — Submission packaging

### 7.1 `evaluation/usage_report.md`
Must reflect the **actual final full-dataset run** that produced `output.csv`:
- If you added real LLM calls (recommended for image/message extraction, §2.1(b)): report
  real provider/model name(s), total calls, total input/output tokens, total & average
  tokens per request, and an honest cost estimate using the provider's published per-token
  pricing (do not invent pricing — look it up or clearly mark it as an estimate with the
  rate used). If multiple models/providers are used, break out per-model totals **and** a
  combined total, per the spec's explicit requirement.
- If you deliberately kept the pipeline 100% LLM-free (deterministic-only, §2.1(a)),
  keep the `$0.00` / `0 calls` report **but only if that's actually true after your fixes**
  — don't leave a stale "0 calls" report if you added any LLM step. This must be the same
  numbers for whichever path you choose; don't let it drift from `main.py`'s actual behavior.
- No credentials/API keys anywhere in the report or repo. Load keys from environment
  variables only (`os.environ[...]`), never hardcoded.

### 7.2 `code.zip`
- Include: all of `code/` (data_loader.py, schemas.py, extraction_schema.py, evidence.py,
  forecaster.py, logic.py, validator.py, main.py, any new LLM client / evaluate_samples.py
  / output_schema.py you add), `README.md`, `evaluation/` folder (with
  `usage_report.md` and `sample_eval_report.md`), and any requirements/dependency file
  (`requirements.txt` or `pyproject.toml` — check whether one already exists in the repo;
  if not, create one listing `pandas`, `pydantic`, `numpy`, and whatever LLM SDK you add).
- Exclude: `dataset/`, virtualenvs, `__pycache__`, `.pytest_cache`, `node_modules`, any
  build artifacts, `.env` files.

### 7.3 `output.csv`
- Root-level file, 250 rows + header, exact column order per §0.

### 7.4 Chat transcript / `log.txt`
- Per `README.md`'s `AGENTS.md` convention: if `AGENTS.md` exists at the repo root, follow
  its instructions to append a running summary of your work to `<repo root>/log.txt`
  (gitignored, submitted separately as the chat transcript). If you cannot find
  `AGENTS.md` at the expected location, say so explicitly and ask where it is rather than
  silently skipping transcript logging — this is a required submission artifact.

### 7.5 Final submission checklist (must all be true before you say "done")
- [ ] `output.csv` has one row per row in `dataset/requests.csv`, exact required columns,
      exact order.
- [ ] Every `0 <= amount_safe_to_pay <= requested_amount`.
- [ ] Every installment plan matches a supplied payment option verbatim.
- [ ] Every spending change targets a flexible, non-protected, correctly-owned event.
- [ ] `validate_plan` is actually enforced in `main.py` (§2.2), not just computed and
      discarded.
- [ ] Blank-amount events are resolved from images, not silently skipped (§2.1).
- [ ] `evaluation/usage_report.md` reflects the real final run.
- [ ] `evaluation/sample_eval_report.md` exists and shows measured accuracy on the 25
      samples with mismatches root-caused, not swept under the rug.
- [ ] `code.zip` excludes `dataset/` and contains a runnable, documented solution.
- [ ] No API keys/secrets anywhere in the submission.
- [ ] `log.txt` / chat transcript captured per `AGENTS.md`.

---

## 8. Working style (non-negotiable)

1. Inspect before you touch anything — you already have the full audit above; re-verify it
   against the real code (don't trust this document blindly either) once you can actually
   run it against real `dataset/` files.
2. Fix only what's broken. Leave `data_loader.py` and `schemas.py` essentially untouched
   (§2.9, §2.10) — they're correct and well-reasoned.
3. Implement Phases 5–9 incrementally, running `test_schema.py`,
   `test_extraction_schema.py`, and your new tests after each phase.
4. Never hardcode a dataset-specific answer to make a sample pass.
5. Prefer the "financially safer interpretation" whenever the spec is ambiguous and you
   can't resolve it from the samples or `shap_data_loader.py`'s worked reasoning.
6. Finish the job — implement, run, evaluate, fix, re-run, and package. Don't stop at a
   list of recommendations.
