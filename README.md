# The diet Ray Peat described: nutrient adequacy model

Code and data for a modelling study of the diet the biologist Raymond Peat (1936–2022) recommended. The study assesses two eras of his advice against his own stated targets and against the Australian and New Zealand Nutrient Reference Values (NRVs).

- **Codebook:** `codebook/` holds 94 dietary rules taken only from Peat's own articles and interview transcripts. Each rule has a verbatim quotation and its source URL.
- **Menus:** `menus/` holds 7-day menus for each scenario. Every row cites a rule ID, and modelling assumptions are labelled `ASSUME`.
- **Two databases:** the model is run through both the Australian Food Composition Database (Release 3, FSANZ) and USDA SR Legacy (April 2018). A finding is treated as robust only when both agree.
- **NRVs:** `data/nrv_adults.csv` holds the NRVs for men and women aged 31–50, each traceable to the NHMRC document.

## Reproduce

```sh
pip install -r requirements.txt
python3 scripts/prepare_data.py   # downloads AFCD R3 + USDA SR Legacy into data/raw/
sh scripts/run_all.sh             # menus -> model (both databases) -> adequacy table -> tables -> figure
```

A clean rebuild from fresh downloads reproduces `results/` byte for byte.

## Scenarios

| Scenario | What it represents |
|---|---|
| `classic` | Peat's advice from 2008 to 2016, reference man |
| `late` | His 2022 advice (about 50 g protein, high carbohydrate), with sucrose top-up to the energy requirement |
| `late_asdescribed` | The late scenario without the energy top-up |
| `classic_woman`, `late_woman` | Reference woman (8.9 MJ) |
| `classic_oj2qt`, `classic_milk1gal` | His higher orange juice and milk quantities |
| `classic_iodised` | Iodised salt instead of non-iodised |
| `classic_chickenliver` | Chicken liver instead of lamb liver |
| `classic_greens` | Plus his cooked-greens advice |
| `classic_supps` | Plus his vitamin E 100 mg/day |
| `classic_nogelatin` | Without gelatin (for the glycine:methionine comparison) |

## Licence

MIT for the code. The source databases keep their own terms: FSANZ AFCD and USDA FoodData Central. Quotations in the codebook are short excerpts from Peat's published work and are cited to source.
