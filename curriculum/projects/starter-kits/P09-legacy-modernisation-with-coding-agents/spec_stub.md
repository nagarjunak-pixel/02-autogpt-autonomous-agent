# PRMCALC premium basis: product-filing summary (fictional, Bhuvika Mutual Life)

This is what the filed product documents say. It is **not** a recovered spec. The legacy code differs from it in at least eight places. Recovering those rules and getting the Appointed Actuary to confirm them is the project.

- **Products:** TL01 and TL02 (term life) and EN05 (endowment). Premium rates are in `data/rate_table.csv`, per mille of sum assured per year, banded by entry age, term and smoker status.
- **Age:** the policyholder's age at the valuation date.
- **Mortality rate:** rate per mille ÷ 1000 × (1 + 0.0125 × (age − the band's lower age)), held to 7 decimal places.
- **Annual premium:** sum assured × mortality rate, less 2% when the sum assured is ₹10,00,000 or more.
- **Modal premium:** annual premium × modal factor: A 1, H 0.51, Q 0.26, M 0.0875. Monthly premiums are quoted in whole rupees; other modes to the paisa.
- **Rider premium (accidental death):** sum assured × 0.00045 × modal factor, truncated to whole rupees.
- **GST:** 18% of (modal + rider) for group policies. Individual life policies are exempt.
- **Output fields:** `policy_id`, `status`, `age`, `mortality_rate`, `modal_premium`, `rider_premium`, `tax_amount`, `total_due`. Money is formatted as a string with 2 decimals.
- **Protocol:** one JSON policy per line on stdin; one JSON result per line on stdout, in any order, exactly one per policy.
