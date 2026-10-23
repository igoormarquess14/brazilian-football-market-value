# Data and methodology

## Sources

| Source | Content | Collected |
|---|---|---|
| Transfermarkt | Market value, age, height, transfer fee, squad by club | 2025-08-25 to 2025-08-28 |
| Transfermarkt | National team call-ups | 2025-08-29 |
| FBref (Opta data) | Minutes played, xG, performance metrics | 2025-08-28, cleaned version 2025-09-18 |

Coverage: 2025 Brazilian Série A, through matchday 20. Market value is the
Transfermarkt estimate on the collection date, not an observed transfer price.

## What is versioned, and why

Only the processed analytical base is in the repository (`data/`). The raw
scraped pages and the scraping scripts are not: the sites' terms do not grant
redistribution rights, and the scrapers depend on page structures that have
since changed. The processed files are kept because they are the minimum
needed to reproduce and audit the published result, and they are shared for
academic use only. They remain derived from Transfermarkt and FBref, and the
MIT license of the code does not cover them.

## Pipeline

All scripts read from `data/` and write to `data/` or `outputs/`. Paths are
relative to the repository root.

| Script | Input | Output |
|---|---|---|
| `01_split_by_position.py` | `players_checkpoint.csv` (285 rows) | `df_gk.csv` (14), `df_def.csv` (91), `df_mc.csv` (87), `df_ata.csv` (91) |
| `02_verify_full_sample.py` | `players_checkpoint.csv`, `df_final.csv` | `outputs/full_sample_check.txt` |
| `03_estimate_midfielder_model.py` | `df_mc.csv` | `outputs/midfielder_model.txt` |
| `04_tables_to_latex.py` | `df_mc.csv`, `df_final.csv` | `outputs/df_mc.tex`, `outputs/df_final.tex` |
| `05_age_value_curve.py` | Table 7 coefficients | `outputs/age_value_curve.png/svg` |

Re-running the chain reproduces every file in `data/` and `outputs/` byte for
byte (the PNG can differ in pixels across machines with different fonts). `01` was reconstructed from its outputs (the original script was lost)
and matches the three position files that were never edited after the Gretl
session (`df_ata.csv`, `df_def.csv`, `df_gk.csv`).

## How the checkpoint was built

`data/players_checkpoint.csv` is the result of merging the club squads from
Transfermarkt with FBref playing time, deduplicating players across the two
sources, normalizing club names, adding position dummies and the CBF club
ranking (RNC). That chain cannot run from a clone because it needs the raw
dumps. The scripts are preserved at the git tag
[`thesis-archive`](https://github.com/igoormarquess14/brazilian-football-market-value/tree/thesis-archive) (`codes/pipeline/01` to `10`,
`codes/scraping/`).

Three links in that chain did not survive and were not simulated:

- Column selection from 51 to 15 columns. The resulting file exists; the script was never saved.
- Position dummies. The mapping from `Position_Num` to `Dum_*` is not a pure
  function of `Position_Num` (some cases were classified by hand).
- RNC ranking. The CSV was extracted manually from the CBF PDF and kept outside
  the project.

None of these affect the published model, which uses only age, xG+/- and
minutes per match from the midfielder subset.

## The one data correction

`data/df_mc.csv` was overwritten on 2025-11-18, a month after the Gretl session
that produced Table 7 (2025-10-16, `thesis/gretl_session.inp`). In that version
the row for Jádson (Juventude) held the string `"x "` in `fb_xG+/-`. The value
`-17.1` was confirmed from three sources that predate the overwrite, and
`01_split_by_position.py` regenerates it from the checkpoint, so the
correction comes from the pipeline and not from a manual edit. With it, the
model reproduces Table 7 within tolerance.

## Known differences between files

`02_verify_full_sample.py` reports four columns that differ between
`df_final.csv` and the checkpoint. All are expected and outside the model:

- `age_centered`, `age_sq`: centered on the 283-row mean in `df_final.csv` and
  on the 285-row mean in the checkpoint. In `df_mc.csv` they are centered on the
  midfielder mean (28.41), which is the specification in the thesis.
- `pos_rnc`, `pts_rnc`: different scales; the transformation was not recovered.
- `dum_inf`, `dum_sup` exist only in `df_final.csv` (manual flags from an
  unpublished robustness check).

## Gretl session

`thesis/gretl_session.inp` is the original command log, unedited. It refers to
the file path on the author's machine at the time; open `data/df_mc.csv` in its
place to replay it in Gretl.
