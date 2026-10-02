"""Ray Peat diet nutrient-adequacy model.

Input:  menus/<scenario>.csv  columns: day,meal,food_key,fdc_id,grams,is_juice,rule_id,note
Food:   AFCD Release 3 per-100 g profiles + USDA SR Legacy, from $PEAT_DATA (see prepare_data.py)
Usage:  analyse.py <scenario> [afcd|usda]\nOutput: results/<scenario>_<db>_daily.csv, results/<scenario>_<db>_summary.csv
"""
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PEAT_DATA", ROOT / "data/raw"))  # built by prepare_data.py
AFCD = DATA / "afcd_per100g.csv"
USDA = DATA / "sr_wide.csv"  # SR Legacy: second database + amino acids, vitamin K, choline

# AFCD column -> short name. Fatty-acid (g) and amino-acid (mg) columns are absolute per 100 g.
COLS = {
    "Energy with dietary fibre, equated (kJ)": "energy_kj",
    "Protein (g)": "protein_g",
    "Fat, total (g)": "fat_g",
    "Available carbohydrate, without sugar alcohols (g)": "carb_g",
    "Total sugars (g)": "sugars_g",
    "Free sugars (g)": "free_sugars_afcd_g",
    "Starch (g)": "starch_g",
    "Total dietary fibre (g)": "fibre_g",
    "Total saturated fatty acids, equated (g)": "sfa_g",
    "Total monounsaturated fatty acids, equated (g)": "mufa_g",
    "Total polyunsaturated fatty acids, equated (g)": "pufa_g",
    "C18:2w6 (g)": "la_g",
    "C18:3w3 (g)": "ala_g",
    "Total long chain omega 3 fatty acids, equated (mg)": "lcn3_mg",
    "Calcium (Ca) (mg)": "ca_mg",
    "Phosphorus (P) (mg)": "p_mg",
    "Magnesium (Mg) (mg)": "mg_mg",
    "Iron (Fe) (mg)": "fe_mg",
    "Zinc (Zn) (mg)": "zn_mg",
    "Iodine (I) (ug)": "i_ug",
    "Selenium (Se) (ug)": "se_ug",
    "Copper (Cu) (mg)": "cu_mg",
    "Manganese (Mn) (mg)": "mn_mg",
    "Potassium (K) (mg)": "k_mg",
    "Sodium (Na) (mg)": "na_mg",
    "Retinol (preformed vitamin A) (ug)": "retinol_ug",
    "Vitamin A retinol equivalents (ug)": "vita_rae_ug",
    "Thiamin (B1) (mg)": "b1_mg",
    "Riboflavin (B2) (mg)": "b2_mg",
    "Niacin derived equivalents (mg)": "niacin_ne_mg",
    "Pyridoxine (B6) (mg)": "b6_mg",
    "Cobalamin (B12) (ug)": "b12_ug",
    "Dietary folate equivalents (ug)": "folate_dfe_ug",
    "Pantothenic acid (B5) (mg)": "b5_mg",
    "Vitamin C (mg)": "vitc_mg",
    "Vitamin D3 equivalents (ug)": "vitd_ug",
    "Vitamin E (mg)": "vite_mg",
    "Caffeine (mg)": "caffeine_mg",
    "Tryptophan (mg)": "trp_mg",
}

# from USDA, per g protein (amino acids, scaled to AFCD protein) or per 100 g
USDA_AA = {"Glycine": "gly_mg", "Methionine": "met_mg", "Cystine": "cys_mg"}
USDA_100G = {"Vitamin K (phylloquinone)": "vitk_ug", "Choline, total": "choline_mg"}


def load_foods():
    f = pd.read_csv(AFCD).set_index("Public Food Key")
    out = f[list(COLS)].rename(columns=COLS).apply(pd.to_numeric, errors="coerce")
    out["name"] = f["Food Name"]
    return out


def usda_profile(u):
    """USDA SR Legacy rows -> same short names as AFCD. Iodine and free sugars are absent in SR: filled from AFCD."""
    out = pd.DataFrame(index=u.index)
    for c in COLS.values():
        if c in u:
            out[c] = u[c]
    out["niacin_ne_mg"] = u.niacin_mg + u.trp_g * 1000 / 60  # niacin equivalents
    out["lcn3_mg"] = (u.epa_g.fillna(0) + u.dha_g.fillna(0) + u.dpa_g.fillna(0)) * 1000
    out["trp_mg"] = u.trp_g * 1000
    return out


def run(scenario, db="afcd"):
    foods = load_foods()
    menu = pd.read_csv(ROOT / "menus" / f"{scenario}.csv")
    supps = menu[menu.food_key == "SUPP"]
    menu = menu[menu.food_key != "SUPP"].reset_index(drop=True)
    missing = set(menu.food_key) - set(foods.index)
    if missing:
        sys.exit(f"unknown AFCD keys: {missing}")

    nut = foods.loc[menu.food_key, list(COLS.values())].reset_index(drop=True)
    usda = pd.read_csv(USDA).set_index("fdc_id")
    if menu.fdc_id.isna().any():
        sys.exit(f"rows without USDA id: {set(menu.food[menu.fdc_id.isna()])}")
    u = usda.reindex(menu.fdc_id.astype(int)).reset_index(drop=True)
    if db == "usda":
        afcd = nut
        nut = usda_profile(u).reindex(columns=nut.columns)
        for c in ["i_ug", "free_sugars_afcd_g"]:  # not in SR Legacy
            nut[c] = afcd[c]
    for src, dst in USDA_AA.items():  # g AA per 100 g -> mg AA per g protein -> x protein of the db in use
        nut[dst] = u[src] * 1000 / u["Protein"] * nut.protein_g
        nut.loc[nut.protein_g == 0, dst] = 0
    for src, dst in USDA_100G.items():
        nut[dst] = u[src]
    gaps = nut.isna() & (menu.grams.values[:, None] > 0)
    rows = nut.fillna(0).mul(menu.grams.values / 100, axis=0)
    rows.insert(0, "day", menu.day.values)
    # WHO free sugars = added sugars + honey/syrups + ALL sugars in fruit juice; menu flags juice rows
    rows["free_sugars_g"] = rows.free_sugars_afcd_g.where(~menu.is_juice.astype(bool).values, rows.sugars_g)
    daily = rows.groupby("day").sum()
    for _, r in supps.iterrows():  # supplements add straight to the named column
        daily.loc[r.day, r.food] += r.grams

    kcal = daily.energy_kj / 4.184
    daily["kcal"] = kcal
    daily["protein_pctE"] = daily.protein_g * 17 / daily.energy_kj * 100
    daily["fat_pctE"] = daily.fat_g * 37 / daily.energy_kj * 100
    daily["carb_pctE"] = daily.carb_g * 17 / daily.energy_kj * 100
    daily["pufa_pctE"] = daily.pufa_g * 37 / daily.energy_kj * 100
    daily["free_sugars_pctE"] = daily.free_sugars_g * 17 / daily.energy_kj * 100
    # Peat's own targets
    daily["ca_p_ratio"] = daily.ca_mg / daily.p_mg
    daily["gly_met_ratio"] = daily.gly_mg / daily.met_mg

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    tag = f"{scenario}_{db}"
    daily.round(2).to_csv(out / f"{tag}_daily.csv")
    summ = daily.agg(["mean", "min", "max"]).T.round(2)
    summ.to_csv(out / f"{tag}_summary.csv")

    # nutrients with no AFCD value for a food actually eaten = undercount risk; report, never hide
    g = gaps.any()
    if g.any():
        print(f"{db} missing values (undercount):", "; ".join(
            f"{c} [{', '.join(sorted(set(menu.food[gaps[c]])))}]" for c in g[g].index))
    print(summ.to_string())


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "afcd")
