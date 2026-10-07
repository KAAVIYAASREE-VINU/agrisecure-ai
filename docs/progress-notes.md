# Handoff notes (Oct 2026)

## Done
- data/raw/msp_raw.csv: MSP 2018-2025 for paddy, maize, groundnut (PIB and farmer.gov.in), Rs per quintal.
- data/raw/cost_raw.csv: Tamil Nadu 2020-21 cost of cultivation (DES figures via TNAU pages), converted to Rs per acre (divided by 2.47105). Buckets: seed; fertilizer = fertilizer + manure; labour = human labour; irrigation; other = machine, bullock, plant protection, insurance, interest, misc. Season is NOT in the source, so rows are tagged PLACEHOLDER - verify season.
- Prices (not saved as files): CEDA Agri-Market monthly modal prices, Tamil Nadu. Harvest-time price = average of Sep and Oct modal prices (assumption for Kuruvai season).
  Year: paddy / maize (Rs per quintal)
  2018: 1708.91 / 1450.11
  2019: 1828.59 / 2176.41
  2020: 1790.94 / 1440.76
  2021: 1586.82 / 1870.35
  2022: 1807.09 / 2208.16
  2023: 2135.04 / 2214.56
  2024: 2172.84 / 2792.84
  2025: 2019.40 / 2835.61

## Still missing
- Tamil Nadu yield per acre by year for paddy (grain, NOT rice), maize, groundnut. The Statistical Handbook gives paddy in terms of rice, which cannot be used directly.
- Groundnut pods (raw) prices: CEDA file had many months missing and wild jumps, so not used.
- Native speaker review of Tamil/Hindi keys, docs/assumptions.md, docs/viva_qa.md, deployment.

## Warning
Do NOT run python3 data/clean_data.py until all three raw files exist. If any is missing it overwrites cost.csv, yield_price.csv and msp.csv with placeholders.
