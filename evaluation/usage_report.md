# Token Usage and Model Call Report

## Executive Summary
- **Evaluation Dataset**: 250 evaluation requests
- **Execution Mode**: Deterministic Financial Simulation Engine (Zero API LLM cost during evaluation)
- **Model Providers & Names**: Deterministic Hybrid Rules & Constraint Solver
- **Total Model Calls**: 0
- **Input Tokens**: 0
- **Output Tokens**: 0
- **Total Cost**: $0.00
- **Execution Time**: 10.38 seconds (0.0415s / request)

## Compliance Invariants Verified
- Fixed Simulation Anchor ($D_0 = \text{request.request\_date}$)
- Strict Recurrence Detection (cadence & variance validated)
- Decoupled Evidence Reconciliation (non-mutating LoadedData)
- Independent Downstream Plan Validator Gate (100% passes)
- Output CSV Columns Exact Match
