# Data sources

## What is in the repository

The processed base (`dados/df_final.csv`, `dados/df_mc.csv`, `dados/df_ata.csv`,
`dados/df_def.csv`, `dados/df_gk.csv`, the `.tex` tables, and the checkpoint in
`dados/clubes/outcome/`) **is version-controlled**. This is what lets you run
`codes/pipeline/11` through `15` and reproduce the published model without
having to re-collect anything.

## What is not in the repository

The raw dumps scraped directly from Transfermarkt and FBref **are not
version-controlled** (`.gitignore`): `dados/clubes/*_2024*.csv`, `dados/selecao/`,
`dados/minutes_played/`, `dados/transfers_brazilian_league/`. They remain on
the local disk of anyone cloning from this environment, but do not get
pushed to GitHub.

**Reason:** Transfermarkt and FBref do not license free redistribution of
data scraped from their pages (see discussion in `CLAUDE.md`).

**Origin and collection dates:**

| Source | Content | Collected on |
|---|---|---|
| Transfermarkt | Market value, age, height, transfer fee, squad by club | 2025-08-25 to 2025-08-28 |
| Transfermarkt | Transfers and club revenue/expense for the 2025 Série A | 2025-08-27 |
| Transfermarkt | National team call-ups | 2025-08-29 |
| FBref (Opta partnership) | Minutes played, xG, performance metrics | original collection ~2025-08-28, cleaned version 2025-09-18 |

Sample: squads of the clubs in the 2025 Brazilian Série A men's championship
through matchday 20 (see `Monografia_Igor_Huttl.pdf`, section 3.2).

**How to re-obtain it:** the scripts in `codes/scraping/` performed the
original collection, but they depend on the Transfermarkt/FBref page
structure at the time — since those pages change frequently, the scripts
likely no longer run without adjustment. Re-obtaining the data requires a
new manual scrape or adapting these scripts to the pages' current structure.

## Excluded third-party document

`dados/clubes/RNC - Ranking Nacional dos Clubes 2025.pdf` (a national club
ranking report) is not redistributed — no confirmed authorization to
publish it. `.gitignore` also covers this file. Merging this data into the
pipeline (`codes/pipeline/10_merge_rnc_into_final.py`) is already documented
as blocked for another reason in `docs/pipeline.md` (the intermediate CSV
extracted from the PDF was saved outside the project folder and never
version-controlled) — the absence of the PDF here is a second, independent
reason that step is not reproducible from this repository.
