# Data Sources

**MSP** — Minimum Support Price tables from [PIB / CACP](https://cacp.dacnet.nic.in).
Announced annually; copy the relevant crop rows into `msp.csv`.

**Cost of Cultivation** — DES Cost of Cultivation for Tamil Nadu, published by the
Directorate of Economics and Statistics (DES), MoAFW.
Source: <https://eands.dacnet.nic.in/Cost_of_Cultivation.htm>

**Yield and Price** — DES crop production statistics and Agmarknet wholesale prices.

**Unit conversion**: all DES figures are per hectare — divide by 2.471 for per acre.

**Rule**: never fill a blank cell by hand. If the real figure is unknown, leave
`source_url` blank and set `note` to `PLACEHOLDER – verify`.
