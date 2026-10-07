import csv, os

HA_TO_ACRE = 2.47105
RICE_TO_PADDY = 0.67   # milling outturn assumption; write this in docs/assumptions.md

# Tamil Nadu yield in kg/ha, from Season and Crop Report 2024-25, Table IX-C.
# Paddy = the "in terms of rice" figure. 2018 means 2018-19, and so on.
rice_kg_ha = {2018: 3562, 2019: 3809, 2020: 3380, 2021: 3566,
              2022: 3500, 2023: 3354, 2024: 3288, 2025: None}
maize_kg_ha = {2018: 7257, 2019: 7839, 2020: 6409, 2021: 7066,
               2022: 7007, 2023: 6239, 2024: 5487, 2025: None}

# From your friend's notes (CEDA, avg of Sep and Oct modal price, Rs/quintal)
price = {
    "paddy": {2018: 1708.91, 2019: 1828.59, 2020: 1790.94, 2021: 1586.82,
              2022: 1807.09, 2023: 2135.04, 2024: 2172.84, 2025: 2019.40},
    "maize": {2018: 1450.11, 2019: 2176.41, 2020: 1440.76, 2021: 1870.35,
              2022: 2208.16, 2023: 2214.56, 2024: 2792.84, 2025: 2835.61},
}

def q_per_acre(kg_ha):
    return round(kg_ha / 100 / HA_TO_ACRE, 2)

rows = []
for year, rice in rice_kg_ha.items():
    if rice:
        paddy = rice / RICE_TO_PADDY
        rows.append(["Tamil Nadu", "Kuruvai", "paddy", year, q_per_acre(paddy),
                     price["paddy"][year],
                     "Yield: TN Season and Crop Report, rice converted to paddy at 0.67; price: CEDA Sep-Oct avg"])
for year, m in maize_kg_ha.items():
    if m:
        rows.append(["Tamil Nadu", "Kuruvai", "maize", year, q_per_acre(m),
                     price["maize"][year],
                     "Yield: TN Season and Crop Report; price: CEDA Sep-Oct avg"])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "yield_price_raw.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["state", "season", "crop", "year", "yield_quintal_per_acre",
                "price_per_quintal", "note"])
    w.writerows(rows)
print(f"Wrote {len(rows)} rows to {out}")