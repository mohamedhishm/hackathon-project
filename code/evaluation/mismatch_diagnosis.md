# Sample Mismatch Diagnosis

This report is based on the measured run after the accuracy-fix pass. No sample
labels or request-specific decision rules were changed.

## Confirmed Root Causes Fixed

### Future income evidence
- `request_10`: the message says the next gig payout is still pending. The previous implementation projected historical gig payouts as future salary. `ExtractedMessageEvidence.pending_income` now suppresses that unconfirmed income.
- `request_05`: `Final employer payroll credit` was treated as a recurring salary stream. Terminal payroll events now stop future projection after the final settlement.

### Earliest safe date
- `request_03`, `request_08`, `request_10`, `request_13`, `request_14`, `request_25`: the old implementation tested only the timeline after the proposed payment date. It could return a later date even when the balance had already breached the minimum before that date. `find_earliest_full_date` now requires the prefix before the payment date to remain safe.

### Validator coverage
- Added deadline checks, positive payment amounts, partial-payment structure, chronology, installment schedule matching, and spending-change legality checks.

## Remaining Root Causes

### Recurrence model mismatch
- `request_02`, `request_03`, `request_04`, `request_07`, `request_11`, `request_12`, `request_15`, `request_17`, `request_18`, `request_19`, `request_20`, `request_21`, `request_22`, `request_23`, `request_24`, `request_25` still have safe-amount or plan differences.
- The dataset contains variable spending with different descriptions inside the same category. Category-level cadence projection was added to avoid silently dropping these expenses, but the reference labels use a different conservative statistic/cadence policy for some streams. The implementation currently records the actual median interval and last observed amount; this is conservative in some users and over-conservative in others.
- This is the principal remaining forecasting issue, not a label or formatting issue.

### Missing image amounts
- There are 16 image-linked blank-amount events in the dataset; 11 remain unresolved in the current environment because no OCR executable or LLM provider is configured.
- These events are intentionally not converted to zero. The pipeline reports them and preserves missingness. This affects samples whose financial history depends on an image amount, including image-linked sample users.

### Spending-change candidate semantics
- `request_06`, `request_11`, `request_21`: expected changes are legal and candidate generation can find some related combinations, but ranking/safety differs because the projected recurring timeline differs. The implementation does not hardcode the expected event IDs.

### Payment options and status
- `request_05`, `request_06`, `request_08`, `request_12`, `request_14`, `request_22`: status/method mismatches are downstream effects of the recurrence forecast and unresolved evidence, not independent output formatting errors.

## Current Measured Accuracy

- `amount_safe_to_pay`: 3/25 within 0.01 after this pass
- `affordability_status`: 16/25 exact
- `recommended_payment_method`: 17/25 exact
- `payment_plan`: 14/25 exact
- `earliest_date_for_full_payment`: 16/25 exact
- `spending_changes_needed`: 22/25 exact

The project is not declared submission-ready while recurrence calibration and image
amount resolution remain incomplete.
