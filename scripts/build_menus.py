"""Build 7-day menus from the codebook. Every row cites a rule ID; ASSUME = modeller's choice where Peat gave no number.

classic = his 2008-2016 advice (reference man).  late = his 2022 advice.
Weights in grams; volumes converted at milk 1.03 g/mL, juice 1.04 g/mL. 1 US qt = 946 mL.
"""
import os
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "menus"

# name: (AFCD key, USDA fdc_id for amino acids/vit K/choline, is_juice)
F = {
    "milk1": ("F005614", 172205, 0),  # USDA: no unfortified 1% entry; 2% unfortified used
    "oj": ("F004739", 169098, 1),
    "egg_fried": ("F003718", 173423, 0),
    "butter": ("F001973", 173410, 0),
    "cheddar": ("F002414", 170899, 0),
    "gelatin": ("F004196", 169599, 0),
    "carrot_raw": ("F002276", 170393, 0),
    "coconut_oil": ("F006163", 171412, 0),
    "vinegar": ("F009498", 173469, 0),
    "mushroom": ("F005946", 169252, 0),  # raw AFCD values; no cooked entry in AFCD
    "potato_boiled": ("F007320", 170440, 0),
    "coffee": ("F003065", 171890, 0),
    "sugar": ("F008976", 169655, 0),
    "salt": ("F007879", 173468, 0),  # non-iodised; iodised = sensitivity
    "salt_iod": ("F007878", 173468, 0),
    "lamb_liver": ("F005021", 172532, 0),  # AFCD has no beef liver
    "oyster": ("F006285", 171978, 0),
    "beef_rump": ("F000738", 168634, 0),
    "prawn": ("F007432", 171971, 0),
    "chicken_liver": ("F002708", 174491, 0),
    "kale": ("F004781", 169238, 0),  # AFCD raw only; USDA boiled
    "mango": ("F005299", 169910, 0),
    "pineapple": ("F006702", 169124, 0),
    "watermelon": ("F005520", 167765, 0),
    "papaya": ("F006528", 169926, 0),
    "cherry": ("F002522", 171719, 0),
    "grape": ("F004260", 174683, 0),
}
FRUIT = ["mango", "pineapple", "watermelon", "papaya", "cherry", "grape", "mango"]
QT_MILK, QT_JUICE = 946 * 1.03, 946 * 1.04


def row(day, meal, food, g, rule, note=""):
    key, fdc, juice = F[food]
    return dict(day=day, meal=meal, food=food, food_key=key, fdc_id=fdc, grams=round(g, 1),
                is_juice=juice, rule_id=rule, note=note)


def supp(day, nutrient, amount, rule, note):
    """Supplement row: food_key SUPP, `food` names the model column, `grams` holds the amount in that column's unit."""
    return dict(day=day, meal="supp", food=nutrient, food_key="SUPP", fdc_id=None, grams=amount,
                is_juice=0, rule_id=rule, note=note)


def scaled(df, factor):
    """Proportional scaling of every food (not supplements), e.g. to the reference woman's EER."""
    df = df.copy()
    df.loc[df.food_key != "SUPP", "grams"] = (df.grams * factor).round(1)
    return df


def with_supps(df):
    return pd.concat([df, pd.DataFrame([supp(d, "vite_mg", 100, "I03;U01", "vitamin E 100 mg/day")
                                        for d in range(1, 8)])])


def classic(milk_qt=2, oj_qt=1, salt_g=5, salt="salt", liver="lamb_liver", greens=0):
    rows = []
    for d in range(1, 8):
        rows += [
            row(d, "all", "milk1", QT_MILK * milk_qt, "M01;M05", "1% milk"),
            row(d, "all", "oj", QT_JUICE * oj_qt, "M01"),
            row(d, "breakfast", "egg_fried", 110, "E01;M04", "2 eggs"),
            row(d, "breakfast", "butter", 5, "M04", "ASSUME: butter to fry egg"),
            row(d, "snack", "cheddar", 40, "M09", "ASSUME: no qty given"),
            row(d, "dinner", "gelatin", 10, "M04;G02", "ASSUME: gelatinous soup almost daily"),
            row(d, "snack", "carrot_raw", 100, "K01;K03", "one good-sized carrot"),
            row(d, "snack", "coconut_oil", 5, "K02", "ASSUME: dressing"),
            row(d, "snack", "vinegar", 5, "K01;K02", "ASSUME: dressing"),
            row(d, "dinner", "mushroom", 100, "K05", "~1 cup cooked; raw values"),
            row(d, "dinner", "potato_boiled", 200, "T01;T02", "ASSUME: qty"),
            row(d, "dinner", "butter", 10, "T02", "ASSUME: 'a little butter'"),
            row(d, "all", "coffee", 800, "F01", "4 cups x 200 mL"),
            row(d, "all", "sugar", 40, "S04", "~3 tbsp"),
            row(d, "snack", "coconut_oil", 10, "O02;O03", "cooking/added"),
            row(d, "all", FRUIT[d - 1], 200, "S07", "ASSUME: qty; ripe tropical"),
            row(d, "all", salt, salt_g, "N01", "ASSUME: to taste"),
        ]
        if greens:
            rows.append(row(d, "dinner", "kale", greens, "K06", "1/2-1 cup cooked greens"))
        protein = {1: (liver, 170, "L01", "6 oz weekly"), 4: ("oyster", 100, "V07;M04", "weekly"),
                   3: ("prawn", 100, "I09;I06", "shellfish sub for meat")}.get(d, ("beef_rump", 100, "C07", "ASSUME: qty; milk preferred over meat"))
        rows.append(row(d, "dinner", protein[0], protein[1], protein[2], protein[3]))
    return pd.DataFrame(rows)


def late(oj_qt=2, salt_g=5, salt="salt", eer_kj=11000, milk_g=500):
    rows = []
    for d in range(1, 8):
        rows += [
            row(d, "all", "milk1", milk_g, "M07", "ASSUME: 'somewhat limit'"),
            row(d, "all", "oj", QT_JUICE * oj_qt, "S06", "OJ (+grape juice not in AFCD)"),
            row(d, "all", "sugar", 120, "S06;P06b", "ASSUME: to reach ~400 g carb"),
            row(d, "breakfast", "egg_fried", 55, "M07", "1 egg"),
            row(d, "breakfast", "butter", 5, "M04", "ASSUME"),
            row(d, "dinner", "gelatin", 5, "G01", "ASSUME"),
            row(d, "snack", "carrot_raw", 100, "K01"),
            row(d, "snack", "coconut_oil", 5, "K02", "ASSUME"),
            row(d, "snack", "vinegar", 5, "K02", "ASSUME"),
            row(d, "dinner", "mushroom", 100, "K05"),
            row(d, "dinner", "potato_boiled", 300, "S06", "very well-cooked veg"),
            row(d, "dinner", "butter", 5, "T02", "ASSUME"),
            row(d, "all", "coffee", 800, "F01"),
            row(d, "all", FRUIT[d - 1], 300, "S07", "ASSUME"),
            row(d, "all", salt, salt_g, "N01", "ASSUME"),
        ]
    df = pd.DataFrame(rows)  # liver ~1-2 oz per 2 months (L04) ~ <1 g/day: omitted
    if eer_kj:  # fill the gap to the reference man's EER with sucrose, within his 400-600 g carb (S06)
        afcd = pd.read_csv(Path(os.environ.get("PEAT_DATA", Path(__file__).resolve().parent.parent / "data/raw")) / "afcd_per100g.csv").set_index("Public Food Key")
        kj = afcd.loc[df.food_key, "Energy with dietary fibre, equated (kJ)"].values * df.grams.values / 100
        gap = eer_kj - pd.Series(kj).groupby(df.day.values).sum()
        sugar_kj = afcd.loc[F["sugar"][0], "Energy with dietary fibre, equated (kJ)"]
        df = pd.concat([df, pd.DataFrame([row(d, "all", "sugar", max(g, 0) / sugar_kj * 100, "S06;S01",
                                              "ASSUME: sucrose top-up to EER") for d, g in gap.items()])])
    return df


SCENARIOS = {
    "classic": classic(),
    "late": late(),
    "classic_oj2qt": classic(oj_qt=2),
    "classic_milk1gal": classic(milk_qt=4),
    "classic_iodised": classic(salt="salt_iod"),
    "classic_chickenliver": classic(liver="chicken_liver"),
    "classic_greens": classic(greens=100),
    "late_asdescribed": late(eer_kj=0),
    "classic_supps": with_supps(classic()),
    "classic_nogelatin": classic().query("food != 'gelatin'"),
    # reference woman 31-50: EER 8.9 MJ. Classic scaled from the man's 11.0 MJ basis; Late topped up to 8.9 MJ
    "classic_woman": scaled(classic(), 8.9 / 11.0),
    "late_woman": late(eer_kj=8900),
    "late_milk1l": late(milk_g=1030),
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, df in SCENARIOS.items():
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(name, len(df), "rows")
