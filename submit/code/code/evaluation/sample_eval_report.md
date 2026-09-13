# Sample Evaluation Report

Evaluated `25` labeled sample requests.

## Mismatches by Field

- `amount_safe_to_pay`: 22 mismatches; 3/25 within target
- `affordability_status`: 9 mismatches; 16/25 within target
- `recommended_payment_method`: 8 mismatches; 17/25 within target
- `payment_plan`: 11 mismatches; 14/25 within target
- `earliest_date_for_full_payment`: 9 mismatches; 16/25 within target
- `spending_changes_needed`: 3 mismatches; 22/25 within target

## Detailed Diffs

- `request_02` `amount_safe_to_pay`: expected `17229139.2`, predicted `18376094.03`
- `request_03` `amount_safe_to_pay`: expected `873000`, predicted `0`
- `request_03` `affordability_status`: expected `affordable_later`, predicted `not_affordable`
- `request_03` `recommended_payment_method`: expected `wait`, predicted `not_recommended`
- `request_03` `payment_plan`: expected `2019-11-15:5491000`, predicted `none`
- `request_03` `earliest_date_for_full_payment`: expected `2019-11-15`, predicted `None`
- `request_04` `amount_safe_to_pay`: expected `8401800`, predicted `10283912.78`
- `request_05` `amount_safe_to_pay`: expected `737`, predicted `0`
- `request_06` `amount_safe_to_pay`: expected `603.3`, predicted `518.45`
- `request_06` `affordability_status`: expected `affordable_with_plan`, predicted `not_affordable`
- `request_06` `recommended_payment_method`: expected `full_payment`, predicted `not_recommended`
- `request_06` `payment_plan`: expected `2026-01-03:620.40`, predicted `none`
- `request_06` `earliest_date_for_full_payment`: expected `2026-01-15`, predicted `None`
- `request_06` `spending_changes_needed`: expected `stop:event_476`, predicted `none`
- `request_07` `amount_safe_to_pay`: expected `87170.56`, predicted `87730.86`
- `request_08` `amount_safe_to_pay`: expected `284.57`, predicted `0`
- `request_08` `affordability_status`: expected `affordable_later`, predicted `not_affordable`
- `request_08` `recommended_payment_method`: expected `wait`, predicted `not_recommended`
- `request_08` `payment_plan`: expected `2025-04-15:996.60`, predicted `none`
- `request_08` `earliest_date_for_full_payment`: expected `2025-04-15`, predicted `None`
- `request_10` `amount_safe_to_pay`: expected `12700`, predicted `0`
- `request_11` `amount_safe_to_pay`: expected `12510645`, predicted `12470824.54`
- `request_11` `affordability_status`: expected `affordable_with_plan`, predicted `affordable_later`
- `request_11` `recommended_payment_method`: expected `full_payment`, predicted `wait`
- `request_11` `payment_plan`: expected `2025-05-03:13110000`, predicted `2025-05-15:13110000`
- `request_11` `earliest_date_for_full_payment`: expected `2025-07-15`, predicted `2025-05-15`
- `request_11` `spending_changes_needed`: expected `reduce_to:event_989:665950`, predicted `none`
- `request_12` `amount_safe_to_pay`: expected `65164`, predicted `57790.43`
- `request_12` `affordability_status`: expected `affordable_with_plan`, predicted `not_affordable`
- `request_12` `recommended_payment_method`: expected `installments`, predicted `not_recommended`
- `request_12` `payment_plan`: expected `2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19`, predicted `none`
- `request_12` `earliest_date_for_full_payment`: expected `2026-04-05`, predicted `None`
- `request_13` `amount_safe_to_pay`: expected `433.4`, predicted `941.6`
- `request_13` `affordability_status`: expected `affordable_later`, predicted `affordable_now`
- `request_13` `recommended_payment_method`: expected `wait`, predicted `full_payment`
- `request_13` `payment_plan`: expected `2024-05-15:941.60`, predicted `2024-03-07:941.6`
- `request_13` `earliest_date_for_full_payment`: expected `2024-05-15`, predicted `2024-03-07`
- `request_14` `amount_safe_to_pay`: expected `597.74`, predicted `586.38`
- `request_14` `affordability_status`: expected `not_affordable`, predicted `affordable_with_plan`
- `request_14` `recommended_payment_method`: expected `not_recommended`, predicted `partial_payment`
- `request_14` `payment_plan`: expected `none`, predicted `2025-08-04:586.38|2025-09-15:4827.82`
- `request_14` `earliest_date_for_full_payment`: expected `None`, predicted `2025-09-15`
- `request_15` `amount_safe_to_pay`: expected `83.05`, predicted `0`
- `request_17` `amount_safe_to_pay`: expected `243849.58`, predicted `245677.35`
- `request_18` `amount_safe_to_pay`: expected `462`, predicted `539.39`
- `request_18` `payment_plan`: expected `2026-09-15:3246.10`, predicted `2026-09-15:3246.1`
- `request_19` `amount_safe_to_pay`: expected `28820`, predicted `27292.04`
- `request_19` `payment_plan`: expected `2024-09-04:28820|2024-09-15:10840`, predicted `2024-09-04:27292.04|2024-09-15:12367.96`
- `request_20` `amount_safe_to_pay`: expected `5400`, predicted `7819.51`
- `request_21` `amount_safe_to_pay`: expected `1543.35`, predicted `1574.4`
- `request_21` `affordability_status`: expected `affordable_with_plan`, predicted `affordable_now`
- `request_21` `payment_plan`: expected `2026-04-03:1574.40`, predicted `2026-04-03:1574.4`
- `request_21` `earliest_date_for_full_payment`: expected `2026-04-15`, predicted `2026-04-03`
- `request_21` `spending_changes_needed`: expected `stop:event_1815|reduce_to:event_1816:23.50`, predicted `none`
- `request_22` `amount_safe_to_pay`: expected `475.46`, predicted `458.85`
- `request_22` `affordability_status`: expected `affordable_with_plan`, predicted `not_affordable`
- `request_22` `recommended_payment_method`: expected `installments`, predicted `not_recommended`
- `request_22` `payment_plan`: expected `2024-12-08:253.59|2025-01-05:253.59|2025-02-02:253.59`, predicted `none`
- `request_22` `earliest_date_for_full_payment`: expected `2025-01-15`, predicted `None`
- `request_23` `amount_safe_to_pay`: expected `9152`, predicted `9402.31`
- `request_24` `amount_safe_to_pay`: expected `13420`, predicted `12773.10`
- `request_25` `amount_safe_to_pay`: expected `1425000`, predicted `0`
