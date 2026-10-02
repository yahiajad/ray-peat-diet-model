"""Figure 1: weekly mean intake as % of the NRV reference (EAR, else AI), by scenario and database.
Diverging blue<->red on log2(% of reference), neutral grey at 100%. Requirement-based references above the rule,
median-intake (convention) AIs below it. Bold outline = weekly mean above a food-applicable UL in that cell."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parent.parent
t = pd.read_csv(ROOT / "results/adequacy_table.csv")
t = t[t.ref_kind.isin(["EAR", "AI"])]

COLS = [("classic", "Classic, man"), ("classic_woman", "Classic, woman"), ("late", "Late, man"), ("late_woman", "Late, woman")]
REQ = [("protein_g", "Protein"), ("b1_mg", "Thiamin"), ("b2_mg", "Riboflavin"), ("niacin_ne_mg", "Niacin"),
       ("b6_mg", "Vitamin B6"), ("b12_ug", "Vitamin B12"), ("folate_dfe_ug", "Folate"), ("vita_rae_ug", "Vitamin A"),
       ("vitc_mg", "Vitamin C"), ("vitd_ug", "Vitamin D"), ("choline_mg", "Choline"), ("ca_mg", "Calcium"),
       ("p_mg", "Phosphorus"), ("mg_mg", "Magnesium"), ("fe_mg", "Iron"), ("zn_mg", "Zinc"), ("i_ug", "Iodine"),
       ("se_ug", "Selenium")]
MED = [("fibre_g", "Dietary fibre"), ("la_g", "Linoleic acid"), ("ala_g", "Alpha-linolenic acid"),
       ("lcn3_mg", "Long-chain omega-3"), ("vite_mg", "Vitamin E"), ("vitk_ug", "Vitamin K"), ("b5_mg", "Pantothenic acid"),
       ("cu_mg", "Copper"), ("mn_mg", "Manganese"), ("k_mg", "Potassium")]
ROWS = REQ + MED

pct = np.full((len(ROWS), len(COLS) * 2), np.nan)
over = np.zeros_like(pct, dtype=bool)
for j, (scen, _) in enumerate(COLS):
    for k, db in enumerate(["afcd", "usda"]):
        g = t[(t.scenario == scen) & (t.db == db)].set_index("nutrient")
        for i, (n, _) in enumerate(ROWS):
            pct[i, j * 2 + k] = g.loc[n, "pct_ref"]
            over[i, j * 2 + k] = bool(g.loc[n, "mean_over_ul"])

cmap = LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#2a78d6"])
norm = TwoSlopeNorm(vmin=-2, vcenter=0, vmax=3)  # 25% .. 100% .. 800%
z = np.log2(np.clip(pct, 25, 800) / 100)

fig, ax = plt.subplots(figsize=(7.2, 9.4))
ax.imshow(z, cmap=cmap, norm=norm, aspect="auto")
for i in range(pct.shape[0]):
    for j in range(pct.shape[1]):
        v = pct[i, j]
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5,
                color="#1a1a19" if abs(z[i, j]) < 1.6 else "white")
        if over[i, j]:
            ax.add_patch(plt.Rectangle((j - .48, i - .48), .96, .96, fill=False, lw=1.6, ec="#1a1a19"))
ax.set_yticks(range(len(ROWS)), [r[1] for r in ROWS], fontsize=8.5)
ax.set_xticks(range(len(COLS) * 2), ["AU", "US"] * len(COLS), fontsize=8)
for j, (_, lab) in enumerate(COLS):
    ax.text(j * 2 + .5, -1.3, lab, ha="center", va="bottom", fontsize=8.5, fontweight="bold")
for x in (1.5, 3.5, 5.5):
    ax.axvline(x, color="white", lw=3)
ax.axhline(len(REQ) - .5, color="#1a1a19", lw=1.2)
n = len(COLS) * 2
for y0, y1, lab in [(0, len(REQ) - 1, "Requirement-based reference"), (len(REQ), len(ROWS) - 1, "AI set at median intake")]:
    ax.plot([n - .3, n - .3], [y0 - .4, y1 + .4], color="#1a1a19", lw=1, clip_on=False)
    ax.text(n - .05, (y0 + y1) / 2, lab, rotation=270, ha="left", va="center", fontsize=8, clip_on=False)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_ylim(len(ROWS) - .5, -1.6)
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation="horizontal", fraction=.03, pad=.04,
                  ticks=np.log2([.25, .5, 1, 2, 4, 8]))
cb.ax.set_xticklabels(["25%", "50%", "100%", "200%", "400%", "800%"], fontsize=7.5)
cb.set_label("Weekly mean intake as % of reference (EAR, or AI where no EAR)", fontsize=8)
cb.outline.set_visible(False)
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(ROOT / f"figures/Fig1_adequacy.{ext}", dpi=300)
print("saved")
