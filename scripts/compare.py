"""Adequacy table: weekly mean intake of each scenario x database vs NRVs (31-50, sex from scenario name) and vs Peat's own targets."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"

# model column -> (NRV nutrient name, reference used)
NRV = {
    "protein_g": "protein", "fibre_g": "dietary fibre", "la_g": "linoleic acid (n-6)", "ala_g": "alpha-linolenic acid (n-3)",
    "lcn3_mg": "LC n-3 (DHA+EPA+DPA)", "b1_mg": "thiamin", "b2_mg": "riboflavin", "niacin_ne_mg": "niacin",
    "b6_mg": "vitamin B6", "b12_ug": "vitamin B12", "folate_dfe_ug": "folate", "b5_mg": "pantothenic acid",
    "vita_rae_ug": "vitamin A", "vitc_mg": "vitamin C", "vitd_ug": "vitamin D", "vite_mg": "vitamin E",
    "vitk_ug": "vitamin K", "choline_mg": "choline", "ca_mg": "calcium", "p_mg": "phosphorus", "mg_mg": "magnesium",
    "fe_mg": "iron", "zn_mg": "zinc", "i_ug": "iodine", "se_ug": "selenium", "cu_mg": "copper", "mn_mg": "manganese",
    "k_mg": "potassium",
}
# ULs that bind on food intake (magnesium/folate/niacin ULs are supplement-only, so not applied to food)
UL_FOOD = {"retinol_ug": 3000, "ca_mg": 2500, "p_mg": 4000, "fe_mg": 45, "zn_mg": 40, "i_ug": 1100, "se_ug": 400,
           "cu_mg": 10, "vitd_ug": 80, "choline_mg": 3500}


def main():
    allnrv = pd.read_csv(ROOT / "data/nrv_adults.csv")
    out = []
    for f in sorted(RES.glob("*_summary.csv")):
        scen, db = f.stem.removesuffix("_summary").rsplit("_", 1)
        sex = "F" if "woman" in scen else "M"
        nrv = allnrv[allnrv.sex.str.startswith(sex) & (allnrv.age == "31-50")].set_index("nutrient")
        eer_kcal = float(nrv.loc["energy (EER)", "EAR"]) * 1000 / 4.184
        s = pd.read_csv(f, index_col=0)
        daily = pd.read_csv(RES / f"{scen}_{db}_daily.csv", index_col=0)
        for col, name in NRV.items():
            r = nrv.loc[name]
            ref, kind = (float(r.EAR), "EAR") if pd.notna(r.EAR) else (float(r.AI), "AI")
            mean = s.loc[col, "mean"]
            ul = UL_FOOD.get(col)
            out.append(dict(scenario=scen, db=db, sex=sex, nutrient=col, mean=mean, ref=ref, ref_kind=kind,
                            pct_ref=round(100 * mean / ref), below_ref=mean < ref,
                            ul=ul, mean_over_ul=bool(ul and mean > ul),
                            days_over_ul=int((daily[col] > ul).sum()) if ul else None))
        ret = daily["retinol_ug"]  # vitamin A UL is preformed retinol only
        out.append(dict(scenario=scen, db=db, nutrient="retinol_ug", mean=ret.mean(), ul=3000,
                        mean_over_ul=ret.mean() > 3000, days_over_ul=int((ret > 3000).sum())))
        for col, target, note in [("pufa_pctE", None, "Peat: as low as possible"),
                                  ("ca_p_ratio", 0.5, "Peat C03: P <= 2x Ca"),
                                  ("free_sugars_pctE", 10, "WHO < 10% E"),
                                  ("protein_pctE", 25, "AMDR 15-25% E"),
                                  ("kcal", eer_kcal, f"EER {sex} 31-50")]:
            out.append(dict(scenario=scen, db=db, nutrient=col, mean=s.loc[col, "mean"], ref=target, ref_kind=note))
    t = pd.DataFrame(out)
    t.to_csv(RES / "adequacy_table.csv", index=False)
    wide = t.pivot_table(index="nutrient", columns=["scenario", "db"], values="mean", sort=False).round(1)
    wide.to_csv(RES / "adequacy_wide.csv")
    return t


if __name__ == "__main__":
    main()
