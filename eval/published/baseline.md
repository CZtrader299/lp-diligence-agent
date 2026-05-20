# LP Diligence Agent — Eval Report

Generated: 2026-05-20 18:00:18
Model: `claude-sonnet-4-6` (judge: `claude-haiku-4-5-20251001`)

## Summary

- **Questions**: 20
- **Refusal correctness**: 0.80
- **Keyword match**: 0.80
- **Faithfulness (mean)**: 0.78
- **Context recall (mean)**: 0.62
- **Context precision (mean)**: 0.60
- **Avg latency**: 4215 ms
- **Total tokens**: 67378 in / 3884 out

## Per-question results

| ID | doc | conf | refusal ok | kw ok | faith | recall | precision |
|---|---|---|---|---|---|---|---|
| psers_2q17_nav_change | PSERS_HL_2Q17 | high | ✓ | ✓ | 0.30 | 0.40 | 0.20 |
| psers_2q17_unfunded | PSERS_HL_2Q17 | high | ✓ | ✓ | 1.00 | 1.00 | 0.95 |
| psers_2q17_irr | PSERS_HL_2Q17 | high | ✓ | ✓ | 0.95 | 1.00 | 0.85 |
| psers_3q17_nav_change | PSERS_HL_3Q17 | medium | ✓ | ✓ | 0.85 | 0.95 | 0.85 |
| psers_3q17_top_holdings | PSERS_HL_3Q17 | medium | ✓ | ✓ | 0.00 | 0.00 | 0.20 |
| psers_3q17_cash_flows | PSERS_HL_3Q17 | medium | ✓ | ✓ | 0.95 | 0.50 | 0.60 |
| psers_4q17_capital_called | PSERS_HL_4Q17 | high | ✓ | ✓ | 1.00 | 1.00 | 0.30 |
| psers_4q17_irr_yoy | PSERS_HL_4Q17 | high | ✓ | ✓ | 1.00 | 1.00 | 0.95 |
| psers_4q17_unfunded | PSERS_HL_4Q17 | high | ✓ | ✓ | 1.00 | 1.00 | 0.85 |
| psers_4q17_key_person_refusal | PSERS_HL_4Q17 | refused | ✓ | ✓ | 1.00 | 1.00 | 1.00 |
| blackstone_q1_nav | Blackstone_PES_Q1_2025 | high | ✓ | ✓ | 0.95 | 1.00 | 0.85 |
| blackstone_q1_capital | Blackstone_PES_Q1_2025 | high | ✓ | ✗ | 0.10 | 0.30 | 0.40 |
| blackstone_q1_distributions | Blackstone_PES_Q1_2025 | refused | ✗ | ✗ | 1.00 | 0.00 | 0.20 |
| blackstone_q1_valuation | Blackstone_PES_Q1_2025 | high | ✓ | ✓ | 0.30 | 0.60 | 0.70 |
| blackstone_q1_fees | Blackstone_PES_Q1_2025 | high | ✓ | ✓ | 0.85 | 0.90 | 0.75 |
| blackstone_q3_nav | Blackstone_PES_Q3_2025 | refused | ✗ | ✗ | 1.00 | 0.00 | 0.30 |
| blackstone_q3_capital | Blackstone_PES_Q3_2025 | refused | ✗ | ✗ | 1.00 | 0.00 | 0.30 |
| blackstone_q3_top_holdings | Blackstone_PES_Q3_2025 | medium | ✓ | ✓ | 0.90 | 0.20 | 0.40 |
| blackstone_q3_valuation | Blackstone_PES_Q3_2025 | high | ✓ | ✓ | 0.95 | 0.90 | 0.85 |
| blackstone_q3_key_person_refusal | Blackstone_PES_Q3_2025 | medium | ✗ | ✓ | 0.60 | 0.70 | 0.50 |
