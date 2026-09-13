# Safe Amount Interpretation Analysis

This is a diagnostic artifact, not a decision rule. It compares the sample labels
with the current model under several definitions:

- **A**: current balance minus minimum balance.
- **B**: minimum projected buffer before the next detected recurring income.
- **C**: minimum projected buffer across all 91 simulated days.
- **D**: maximum immediate payment that leaves the complete simulated path above minimum.

## Representative results

| Request    |      Expected |             A |             B/C/D current model | Observation                                                           |
| ---------- | ------------: | ------------: | ------------------------------: | --------------------------------------------------------------------- |
| request_02 | 17,229,139.20 | 31,225,489.20 |                   18,376,094.03 | Close to projected-buffer interpretation, but not exact               |
| request_03 |       873,000 |     3,141,600 |            0 after full horizon | Label is positive while current projected path later breaches minimum |
| request_05 |           737 |     33,375.10 |  0 after final-payroll handling | Requires a different obligation/recurrence interpretation             |
| request_08 |        284.57 |        736.57 |            0 after full horizon | Label is positive despite later projected breach                      |
| request_10 |        12,700 |       524,755 | 0 after pending-income handling | Pending gig income and variable spending materially change result     |
| request_13 |        433.40 |      1,489.52 |                          941.60 | No single current interpretation matches                              |
| request_18 |           462 |         1,086 |                          539.39 | Close to projected-buffer interpretation                              |
| request_25 |     1,425,000 |     8,683,950 |    0 after salary deduplication | Previous duplicate salary was a confirmed simulator bug               |

## Conclusions

1. The sample labels do not consistently match the current full-90-day projected
   minimum, the simple current margin, or a single next-income cutoff.
2. Some labels remain positive where the current recurrence model projects a later
   minimum-balance breach. This points to event reconstruction/recurrence policy,
   not a safe-amount arithmetic typo.
3. Confirmed implementation bugs found independently of labels include duplicate
   salary projection when a scheduled salary changes description, future income
   projection after final payroll, and use of a single `d0` FX date for projected
   foreign-currency occurrences. These were fixed and regression-tested where
   applicable.
4. The remaining disagreement requires reconstructing the intended treatment of
   variable spending and sparse/terminal income from the dataset, worked trace, and
   labels. No formula tuning or sample-specific rule was applied.
