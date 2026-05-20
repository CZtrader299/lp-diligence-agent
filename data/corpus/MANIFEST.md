# Corpus Manifest

Documents in this directory are publicly available regulatory or FOIA-released filings. They are included verbatim with provenance metadata so that retrieval results can be traced back to a primary source.

| File | Type | Source | Public-records basis |
|---|---|---|---|
| `PSERS_HL_2Q17.pdf` | Quarterly report (LP-format) | Pennsylvania Joint State Government Commission, Act 5 archive | FOIA / PA Act 5 data request response |
| `PSERS_HL_3Q17.pdf` | Quarterly report (LP-format) | Pennsylvania Joint State Government Commission, Act 5 archive | FOIA / PA Act 5 data request response |
| `PSERS_HL_4Q17.pdf` | Quarterly report (LP-format) | Pennsylvania Joint State Government Commission, Act 5 archive | FOIA / PA Act 5 data request response |
| `Blackstone_PES_10Q_Q1_2025.htm` | SEC Form 10-Q | SEC EDGAR (CIK 1930054) | Registered public filing |
| `Blackstone_PES_10Q_Q3_2025.htm` | SEC Form 10-Q | SEC EDGAR (CIK 1930054) | Registered public filing |

## Source URLs

- PSERS 2Q17: https://jsg.legis.state.pa.us/resources/documents/ftp/act5/pdf/Appendix%202/PSERS%20Data%20Request%20Responses/PSERS%20-%20Aug%20Sep%20Oct%20Additional%20Response/Request1/Redacted%202Q17%20Hamilton%20Lane%20Quarterly%20Report%20for%20Private%20Markets%20-%20FINAL%204.18.18.pdf
- PSERS 3Q17: https://jsg.legis.state.pa.us/resources/documents/ftp/act5/pdf/Appendix%202/PSERS%20Data%20Request%20Responses/PSERS%20-%20Aug%20Sep%20Oct%20Additional%20Response/Request1/Redacted%20Hamilton%20Lane%20Quarterly%20Report%20-%20PSERS%20PM%20-%203Q17%20-%20FINAL.pdf
- PSERS 4Q17: https://jsg.legis.state.pa.us/resources/documents/ftp/act5/pdf/Appendix%202/PSERS%20Data%20Request%20Responses/PSERS%20-%20Aug%20Sep%20Oct%20Additional%20Response/Request1/Hamilton%20Lane%20Quarterly%20Report%20-%20PSERS%20PM%20-%204Q17-Final-Redacted.pdf
- Blackstone Q1 2025 10-Q: https://www.sec.gov/Archives/edgar/data/0001930054/000119312525119825/d945051d10q.htm
- Blackstone Q3 2025 10-Q: https://www.sec.gov/Archives/edgar/data/0001930054/000119312525277478/d12786d10q.htm

## Why this corpus

The PSERS reports are the closest publicly available analog to true GP-to-LP quarterly communications. They span three consecutive quarters of the same client's portfolio, which lets the agent demonstrate change-over-time analysis. The Blackstone 10-Qs cover what the PSERS reports redact: fund-level fee detail and Level 1/2/3 valuation methodology. The two report types together cover all nine checklist items.

## Redactions

The PSERS reports contain manual redactions (black bars) applied by the source archive prior to public release. The agent's refusal-correctness metric depends on these — questions targeting redacted content should be answered "data not available in this filing" rather than hallucinated.
