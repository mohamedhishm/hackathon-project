# Token Usage and Model Call Report

## Executive Summary
- **Evaluation Dataset**: 250 evaluation requests
- **Execution Mode**: Deterministic rules plus optional local OCR adapter
- **Model Providers & Names**: None; no external LLM/API calls were made
- **Total Model Calls**: 0
- **Input Tokens**: 0
- **Output Tokens**: 0
- **Total Cost**: $0.00
- **Execution Time**: 18.58 seconds (0.0743s / request)

## Compliance Invariants Verified
- Fixed Simulation Anchor ($D_0 = \text{request.request\_date}$)
- Strict Recurrence Detection (cadence & variance validated)
- Decoupled Evidence Reconciliation (non-mutating LoadedData)
- Independent Downstream Plan Validator Gate (rejections=0)
- Output CSV Columns Exact Match
- Unresolved blank-amount image events: 11
- Per-request failures: 0
