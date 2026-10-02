"""Download the two food composition databases and build the tables the model reads.
AFCD Release 3 (FSANZ) -> afcd_per100g.csv ; USDA SR Legacy (April 2018) -> sr_wide.csv.
Output dir: $PEAT_DATA, default ../data/raw (git-ignored)."""
import io, os, re, subprocess, zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("PEAT_DATA", ROOT / "data/raw")); OUT.mkdir(parents=True, exist_ok=True)
AFCD_URL = "https://www.foodstandards.gov.au/sites/default/files/2025-12/AFCD%20Release%203%20-%20Nutrient%20profiles.xlsx"
SR_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"


def get(url):  # curl: uses the system certificate store
    return subprocess.run(["curl", "-fsSL", "-A", "Mozilla/5.0", url], check=True, capture_output=True).stdout


afcd = pd.read_excel(io.BytesIO(get(AFCD_URL)), sheet_name=1, header=2)
afcd.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in afcd.columns]
afcd.to_csv(OUT / "afcd_per100g.csv", index=False)

z = zipfile.ZipFile(io.BytesIO(get(SR_URL)))
rd = lambda n, **k: pd.read_csv(z.open(next(f for f in z.namelist() if f.endswith("/" + n))), **k)
M = {1062: "energy_kj", 1003: "protein_g", 1004: "fat_g", 1005: "carb_g", 2000: "sugars_g", 1009: "starch_g",
     1079: "fibre_g", 1258: "sfa_g", 1292: "mufa_g", 1293: "pufa_g", 1269: "la_g", 1270: "ala_g", 1087: "ca_mg",
     1091: "p_mg", 1090: "mg_mg", 1089: "fe_mg", 1095: "zn_mg", 1100: "i_ug", 1103: "se_ug", 1098: "cu_mg",
     1101: "mn_mg", 1092: "k_mg", 1093: "na_mg", 1105: "retinol_ug", 1106: "vita_rae_ug", 1165: "b1_mg",
     1166: "b2_mg", 1167: "niacin_mg", 1175: "b6_mg", 1178: "b12_ug", 1190: "folate_dfe_ug", 1170: "b5_mg",
     1162: "vitc_mg", 1114: "vitd_ug", 1109: "vite_mg", 1057: "caffeine_mg", 1210: "trp_g", 1225: "gly_g",
     1215: "met_g", 1216: "cys_g", 1185: "vitk_ug", 1180: "choline_mg", 1278: "epa_g", 1272: "dha_g", 1280: "dpa_g"}
fn = rd("food_nutrient.csv", usecols=["fdc_id", "nutrient_id", "amount"])
w = fn[fn.nutrient_id.isin(M)].pivot_table(index="fdc_id", columns="nutrient_id", values="amount").rename(columns=M)
w = rd("food.csv", usecols=["fdc_id", "description"]).set_index("fdc_id").join(w, how="inner")
w["Protein"], w["Glycine"], w["Methionine"], w["Cystine"] = w.protein_g, w.gly_g, w.met_g, w.cys_g
w["Vitamin K (phylloquinone)"], w["Choline, total"] = w.vitk_ug, w.choline_mg
w.to_csv(OUT / "sr_wide.csv")
print(f"wrote {OUT}: AFCD {afcd.shape}, SR {w.shape}")
