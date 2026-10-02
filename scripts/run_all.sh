#!/bin/sh
# Full rebuild: menus -> nutrient model (both databases) -> adequacy table -> tables -> figure.
# Run scripts/prepare_data.py once first.
set -e
cd "$(dirname "$0")"
python3 build_menus.py
for m in ../menus/*.csv; do
  s=$(basename "$m" .csv)
  for db in afcd usda; do python3 analyse.py "$s" "$db" > /dev/null; done
done
python3 compare.py
python3 make_tables.py > /dev/null
python3 figure.py
