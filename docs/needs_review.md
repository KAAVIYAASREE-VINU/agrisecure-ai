# Keys needing Tamil / Hindi native-speaker review

The following i18n keys were added to `lang/ta.json` and `lang/hi.json` as
English text with a `(NEEDS REVIEW)` suffix.  A native-speaker reviewer must
translate them before the app goes live.

Do NOT invent translations — keep the English placeholder until reviewed.

## New keys (added in RUN B fixes)

| Key | English value |
|-----|---------------|
| `scheme_eligibility_label` | Who can apply |
| `scheme_documents_label` | Documents needed |
| `scheme_where_label` | Where to apply |
| `profit_range_label` | Profit range |
| `months_label` | months |
| `acres_label` | acres |
| `revenue_label` | Revenue |
| `profit_label` | Profit |
| `quick_questions_header` | Quick Questions |
| `breakeven_msp_safe` | ✅ Break-even {be} is below MSP {msp} — you should cover costs at MSP. |
| `breakeven_msp_risky` | ⚠️ Break-even {be} exceeds MSP {msp} — price risk if market falls. |
| `dscr_no_loan` | 🟢 No loan needed — costs are covered by your own capital. |
| `footer_data_note` | Planned data sources (PLACEHOLDER – verify): DES cost surveys, CACP MSP tables, Agmarknet price series. Not yet loaded. |
| `whatif_plus10` | Costs +20% |
| `whatif_minus10` | Income −20% |
| `whatif_less_land` | Less land (−0.5 ac) |
| `whatif_reset` | Reset |

## Note on existing Tamil/Hindi scheme text

Keys such as `scheme_kcc_benefit`, `scheme_pmkisan_eligibility_*`, etc. in
`ta.json` and `hi.json` also carry a `PLACEHOLDER – verify` prefix and need
native-speaker review before use.
