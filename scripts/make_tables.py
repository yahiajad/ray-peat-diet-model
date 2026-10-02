"""Tables 1-3 for the manuscript, straight from results/ (no hand-typed numbers)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
MAIN = ["classic", "late"]


def summ(scen, db):
    m = pd.read_csv(RES / f"{scen}_{db}_summary.csv", index_col=0)["mean"]
    m["energy_mj"] = m.energy_kj / 1000
    return m


def rng(scen, col, nd=0):
    a, u = summ(scen, "afcd")[col], summ(scen, "usda")[col]
    f = f"{{:,.{nd}f}}"
    return f.format(a) if f.format(a) == f.format(u) else f"{f.format(a)} / {f.format(u)}"


def md_table(df):
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    return "\n".join(lines + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def table1():
    rows = [("Energy (MJ)", "energy_mj", 1), ("Protein (g)", "protein_g", 0), ("Protein (% energy)", "protein_pctE", 1),
            ("Fat (g)", "fat_g", 0), ("Fat (% energy)", "fat_pctE", 1), ("Saturated fat (g)", "sfa_g", 0),
            ("Polyunsaturated fat (% energy)", "pufa_pctE", 1), ("Carbohydrate (g)", "carb_g", 0),
            ("Carbohydrate (% energy)", "carb_pctE", 1), ("Free sugars (% energy)", "free_sugars_pctE", 1),
            ("Dietary fibre (g)", "fibre_g", 0), ("Glycine:methionine", "gly_met_ratio", 1)]
    return pd.DataFrame([[lab] + [rng(s, c, nd) for s in MAIN] for lab, c, nd in rows],
                        columns=["Per day", "Classic (2008–2016)", "Late (2022)"])


LABEL = {"protein_g": ("Protein", "g"), "fibre_g": ("Dietary fibre", "g"), "la_g": ("Linoleic acid", "g"),
         "ala_g": ("Alpha-linolenic acid", "g"), "lcn3_mg": ("Long-chain omega-3", "mg"), "b1_mg": ("Thiamin", "mg"),
         "b2_mg": ("Riboflavin", "mg"), "niacin_ne_mg": ("Niacin", "mg NE"), "b6_mg": ("Vitamin B6", "mg"),
         "b12_ug": ("Vitamin B12", "µg"), "folate_dfe_ug": ("Folate", "µg DFE"), "b5_mg": ("Pantothenic acid", "mg"),
         "vita_rae_ug": ("Vitamin A", "µg RE"), "vitc_mg": ("Vitamin C", "mg"), "vitd_ug": ("Vitamin D", "µg"),
         "vite_mg": ("Vitamin E", "mg"), "vitk_ug": ("Vitamin K", "µg"), "choline_mg": ("Choline", "mg"),
         "ca_mg": ("Calcium", "mg"), "p_mg": ("Phosphorus", "mg"), "mg_mg": ("Magnesium", "mg"), "fe_mg": ("Iron", "mg"),
         "zn_mg": ("Zinc", "mg"), "i_ug": ("Iodine", "µg"), "se_ug": ("Selenium", "µg"), "cu_mg": ("Copper", "mg"),
         "mn_mg": ("Manganese", "mg"), "k_mg": ("Potassium", "mg")}


def table2():
    t = pd.read_csv(RES / "adequacy_table.csv")
    # NRV rationale (nrv_full.txt line): LA/ALA/LCn3 2702, fibre 3131, E 7974, K 8344, B5 6234, Mn 11026, Cu 9403,
    # K 11836 = median intake; vitamin D 7424 = 25(OH)D >= 27.5 nmol/L; choline 6659 = one study (weak)
    prov = {"la_g": "Median intake", "ala_g": "Median intake", "lcn3_mg": "Median intake", "fibre_g": "Median intake",
            "vite_mg": "Median intake", "vitk_ug": "Median intake", "b5_mg": "Median intake", "mn_mg": "Median intake",
            "cu_mg": "Median intake", "k_mg": "Median intake", "vitd_ug": "Biomarker (25(OH)D)", "choline_mg": "Requirement (weak)"}
    out = []
    for n, g in t[t.scenario.isin(MAIN) & t.ref_kind.isin(["EAR", "AI"])].groupby("nutrient", sort=False):
        r = g.iloc[0]
        cells = []
        for s in MAIN:
            x = g[g.scenario == s].set_index("db")
            below = x.below_ref.astype(bool)
            mark = "↓" if below.all() else ("" if not below.any() else "?")
            over = "↑" if x.mean_over_ul.astype(bool).all() else ""
            cells.append(f"{x.loc['afcd','mean']:,.1f} / {x.loc['usda','mean']:,.1f} {mark}{over}".strip())
        name, unit = LABEL[n]
        out.append([f"{name} ({unit})", f"{r.ref_kind} {r.ref:g}", prov.get(n, "Requirement"), *cells])
    return pd.DataFrame(out, columns=["Nutrient", "Reference (man 31–50)", "Basis of reference", "Classic AFCD / USDA",
                                      "Late AFCD / USDA"])


def table3():
    c, l = (lambda s: (summ(s, "afcd"), summ(s, "usda")))("classic"), (lambda s: (summ(s, "afcd"), summ(s, "usda")))("late")
    def met(pair, f):
        r = [f(x) for x in pair]
        return "Yes" if all(r) else ("No" if not any(r) else "Database-dependent")
    rows = [
        ("Protein at least 70–100 g/day, up to 150 g/day (classic) or ~50 g/day (late)", "P01–P07",
         met(c, lambda x: 70 <= x.protein_g <= 150), met(l, lambda x: 40 <= x.protein_g <= 60)),
        ("Calcium ≥ 1,500 mg/day", "C01", met(c, lambda x: x.ca_mg >= 1500), met(l, lambda x: x.ca_mg >= 1500)),
        ("Phosphorus ≤ 2 × calcium", "C03", met(c, lambda x: x.p_mg <= 2 * x.ca_mg), met(l, lambda x: x.p_mg <= 2 * x.ca_mg)),
        ("Polyunsaturated fat as low as practicable (no number given); % energy shown", "O05", rng("classic", "pufa_pctE", 1), rng("late", "pufa_pctE", 1)),
        ("Carbohydrate 400–600 g/day (late)", "S06", "n/a", met(l, lambda x: 400 <= x.carb_g <= 600)),
    ]
    return pd.DataFrame(rows, columns=["Peat's target", "Rule", "Classic", "Late"])


if __name__ == "__main__":
    md = []
    for name, fn in [("Table 1. Mean daily energy and macronutrients, reference man aged 31-50 years. Where the databases differ, values are Australian Food Composition Database / USDA Standard Reference Legacy", table1),
                     ("Table 2. Mean daily nutrient intake against the Nutrient Reference Values, reference man aged 31-50 years (Australian / USDA database). ↓ below the reference in both databases; ? below in one database only; ↑ above the Upper Level of Intake in both. EAR, Estimated Average Requirement; AI, Adequate Intake; NE, niacin equivalents; DFE, dietary folate equivalents; RE, retinol equivalents", table2),
                     ("Table 3. Whether each scenario met the targets Peat stated (reference man; both databases). Rule identifiers refer to Supplementary Table S1", table3)]:
        df = fn()
        df.to_csv(RES / f"{name.split('.')[0].replace(' ', '')}.csv", index=False)
        md += [f"### {name}", "", md_table(df), ""]
    (ROOT / "Tables v1.md").write_text("\n".join(md))
    print("\n".join(md))
