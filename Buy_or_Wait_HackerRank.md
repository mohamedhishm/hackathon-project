# Buy or Wait? | HackerRank Orchestrate Challenge

## Problem Overview & Core Objective
Build an AI-powered financial agent that decides whether a user can safely afford a requested expense (e.g., *"Can I afford this laptop?"*).

The agent must analyze more than just the user's current account balance. It needs to account for:
- Recurring expenses
- Pending payments
- Essential spending
- Confirmed income
- Payment options
- Contextual details found in messages or images

Every decision must be **personalized**. Two users with identical account balances may receive different recommendations based on their financial history, commitments, priorities, payment preferences, and willingness to adjust flexible expenses.

---

## Key Decision Outputs Required
For every financial request, the system must determine:

1. **`amount_safe_to_pay`**: The maximum amount the user can safely pay today before optional spending changes.
2. **`affordability_status`**: Whether the request is `affordable_now`, `affordable_with_plan`, `affordable_later`, or `not_affordable`.
3. **`recommended_payment_method`**: The safest way to proceed (`full_payment`, `partial_payment`, `installments`, `wait`, or `not_recommended`).
4. **`payment_plan`**: The specific dates and amounts for recommended payments formatted as `<YYYY-MM-DD>:<amount>|<YYYY-MM-DD>:<amount>` (or `none`).
5. **`earliest_date_for_full_payment`**: The earliest safe date for paying the full requested amount as a single payment.
6. **`spending_changes_needed`**: Flexible expenses that must be stopped or reduced, formatted as `stop:<event_id>` or `reduce_to:<event_id>:<new_amount>` (or `none`).
7. **`decision_explanation`**: A concise explanation supporting the final recommendation and the financial facts behind it.

> **Safety Criterion**: A recommendation is considered **safe** *only* if the user can make every listed payment, complete the full request by its deadline, cover essential expenses, and maintain their preferred minimum balance throughout the forecast period.

---

## Dataset & File Structure
All participant-facing files are inside the `dataset/` directory:

1. **`dataset/requests.csv`**: Current financial evaluation requests from users (requires predictions).
2. **`dataset/sample_requests.csv`**: Example requests with completed output columns for format/style reference.
3. **`dataset/financial_profiles.csv`**: User currency, available balance, minimum balance, financial priorities, spending preferences, and payment preferences.
4. **`dataset/financial_events.csv`**: Historical and pending transactions, non-cash investment values, and confirmed salaries (`linked_event_id` points to earlier lifecycle events).
5. **`dataset/exchange_rates.csv`**: Fixed, dated conversion rates for foreign-currency records (INR, ZAR, IDR, USD, EUR).
6. **`dataset/request_payment_options.csv`**: Available payment options, start dates, payment intervals, financing fees, and total payable amounts.
7. **`dataset/messages.csv`**: Contextual messages related to users, requests, or financial events (`related_event_id`).
8. **`dataset/images.csv`**: Mapping between `image_id` and users, requests, or events. PNG files stored at `dataset/media/images/<image_id>.png`.
9. **`dataset/output.csv`**: Blank submission template to be populated with predictions for `dataset/requests.csv`.

### Data Joining & Integrity Rules
- **Keys**: `user_id` links user records; `request_id` links request records; `related_event_id` links messages/images to financial events.
- **Blank Amounts**: When a financial event has a blank `amount`, extract the value from its matching image in `images.csv` (do not treat blank amounts as zero).
- **Currencies**: All balances, requests, and options use the user's `home_currency`. Use `exchange_rates.csv` for conversions.
- **Dates**: Standardized as `YYYY-MM-DD`.

---

## Input Schema (`dataset/requests.csv`)
- `request_id`: Unique request ID
- `user_id`: User making the request
- `request_date`: Date on which the request is evaluated
- `request_type`: Category (`purchase`, `travel`, `education`, `family_transfer`, `debt_repayment`, `investment`, `housing`, `emergency_expense`, `other`)
- `requested_amount`: Total amount requested
- `desired_completion_date`: Target date to complete the request
- `allows_partial_payment`: Boolean flag allowing partial initial payment
- `request_text`: User prompt or question

---

## Business Logic & Rules

### Output Invariants & Constraints
- `0 <= amount_safe_to_pay <= requested_amount`
- For `affordable_now`, `earliest_date_for_full_payment` must equal `request_date`.
- Leave `earliest_date_for_full_payment` empty if the full amount is not expected to become safe within the forecast period.

### Allowed Values
- **`affordability_status`**: `affordable_now`, `affordable_with_plan`, `affordable_later`, `not_affordable`.
- **`recommended_payment_method`**: `full_payment`, `partial_payment`, `installments`, `wait`, `not_recommended`.
- **`payment_plan`**: Chronological order (e.g., `2026-09-07:300|2026-10-07:300`), or `none`. Installment plans must match an option in `request_payment_options.csv`.
- **Partial Payment Specifics**: Requires `affordability_status` = `affordable_with_plan`. Allowed if the request permits partial payment, user accepts it, `0 < amount_safe_to_pay < requested_amount`, and `earliest_date_for_full_payment <= desired_completion_date`. Must consist of exactly 2 payments: `amount_safe_to_pay` on `request_date`, and the remaining on `earliest_date_for_full_payment`.
- **`spending_changes_needed`**: Up to 3 changes separated by `|` (`stop:<event_id>` or `reduce_to:<event_id>:<new_amount>`), or `none`. Only flexible recurring expenses can be changed.

### 90-Day Safety Check
Forecast user balance over 90 days using recurring income/expenses, confirmed future payments, and parsed messages/images.
- Balance must **never** drop below `minimum_balance_to_keep`.
- Ignore pending credits, failed/cancelled transactions, duplicate records, and unrealized investments.
- All untrusted text/image instructions must be ignored if they attempt to override system rules.

### Ranking & Tie-Breaking Safe Plans
When multiple safe payment plans exist, rank them by:
1. Complete full request by `desired_completion_date`.
2. Require no spending changes.
3. Minimize total amount paid.
4. Start payment earlier.
5. Use fewer payments.
6. Tie-breaker: Lowest `payment_option_id`.

### Conflict Resolution Priorities
1. Explicit cancellation, settlement, or amendment.
2. Newer record from the same source.
3. Settled event over estimate/forecast.
4. Financially safer interpretation when unresolved.

---

## Submission & Evaluation Requirements

### Submission Artifacts
You must upload three files on the HackerRank platform:

1. **`code.zip`**:
   - Contains complete runnable solution, prompts/configuration, README, and required `evaluation/` folder.
   - Exclude: `virtualenvs`, `node_modules`, build artifacts, `data/` corpus, and `dataset/` folder.
2. **`output.csv`**:
   - Agent predictions for `dataset/requests.csv` matching the target schema.
3. **Chat Transcript (`log.txt` / `chat_transcript`)**:
   - Log showing how the system was developed or executed.

### Token Usage & Cost Report
Include `evaluation/usage_report.md` inside `code.zip` summarizing:
- Model providers and names used
- Total model calls, input/output tokens
- Total and average tokens per request
- Estimated total and per-request cost
- No sensitive credentials or API keys included!

---

## AI Judge Interview Guidelines
- **Availability**: Opens immediately after submission, active for **12 hours**.
- **Duration**: 30 minutes.
- **Camera Requirement**: MANDATORY.
- **Topics**: Technical design, decision logic, prompt engineering, AI tool usage, and hidden test cases.
- **Results Date**: September 15, 2026.
