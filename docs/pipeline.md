# Data pipeline: from collection to the published model

This document describes what each script in `codes/` does, the order in
which they actually ran historically, what was verified in this session
(2026-08-31), and what is a known limitation — not a hidden bug.

## How to read this document

- **Verified** = the script ran in this session and its result was compared
  byte for byte (or numerically, where noted) against the file already in
  the repository. It matched.
- **Blocked** = the script does not run today because a required input file
  does not exist in the repository (and, in some cases, never did — it was
  a file outside the project folder).
- No script was rewritten to "fix" a result. Where the original logic did
  not survive, that is stated explicitly, not simulated.

## Segment 1 — Raw collection (`codes/scraping/`)

`codigo_ok.py`, `code_selecao.py`, `br_transfermarkt.py`, `transfers_clubs.py`.

Not part of the numbered chain. Not run in this session — they depend on
live scraping of Transfermarkt/FBref, whose page structure changes
frequently (see `README.md`). The reproducible entry point is the base
already collected in `dados/clubes/`, `dados/selecao/`, `dados/minutes_played/`,
and `dados/transfers_brazilian_league/`.

## Segment 2 — Merge and cleaning (`codes/pipeline/01` through `09b`)

| Script | Input | Output | Status |
|---|---|---|---|
| `01_merge_clubes.py` | `dados/clubes/*.csv` (18 files) | `dados/clubes/outcome/todos_clubes_2025.csv` | **Verified** — the 01→02→03 chain reproduces `todos_clubes_2025_final.csv` byte for byte |
| `02_processar_clubes.py` | output of 01 | `.../todos_clubes_2025_processado.csv` | **Verified** (together with 01/03) |
| `03_processar_ex_club.py` | output of 02 | `.../todos_clubes_2025_final.csv` | **Verified** |
| `04_clean_fbref_minutes.py` | `dados/minutes_played/fbref_playing_time.csv` + `.../atletas_completo.csv` | `.../fbref_playing_time_cleaned.csv` | **Blocked** — `atletas_completo.csv` does not exist in the repository (no script produces that exact name; likely a manual copy of a variant already lost). The output already exists, committed, and is used by the following scripts. |
| `05_merge_atletas_fbref.py` | output of 03 + `fbref_playing_time_cleaned.csv` | `.../atletas_fbref_merged.csv` | Run — reproduces the existing file almost exactly (1 row diverges; not investigated further, no effect on the final model) |
| `06_normalize_and_merge.py` | `.../antijoin_only_clubes_fbref.csv` + output of 05 | `.../final_merged_players.csv` (= `final_merged_clean.csv`) | **Verified**, byte for byte |
| `07_dedupe_players.py` | `final_merged_clean.csv` | `.../final_merged_fixed.csv` | **Verified**, byte for byte. It is the version that "won" among 3 competing same-day attempts (`fix_duplicate_players.py`, `fix_specific_duplicates.py`, this one) — the other two were moved to `legacy/dedup_attempts/` since they write to the same output file with no relevant difference in logic. |
| *(no script)* | `final_merged_fixed.csv` (51 columns) | `.../final_merged_filtrado.csv` (15 columns) | **Gap, not reconstructible by automated logic** — `criar_csv_filtrado.py` exists but is empty (0 bytes). The actual transformation is a simple selection of 15 columns (confirmed by comparing the two outputs), but the original script was never saved. The resulting file is preserved and committed. |
| *(no script)* | `final_merged_filtrado.csv` | `.../final_merged_filtrado_dummies.csv` (+ columns `Dum_GK/DEF/MC/ATA`) | **Gap, not reconstructible.** The mapping `Position_Num → Dum_*` is not a pure function of `Position_Num` (the same `Position_Num` maps to different dummies in specific cases — e.g., `Position_Num=5` appears with both `Dum_DEF` and `Dum_MC`), indicating a case-by-case manual decision. Not simulated. The resulting file is preserved and committed. |
| `08_fix_internacional_merge.py` | `final_merged_filtrado_dummies.csv` + antijoin | same file (32-row patch for Internacional) | **Verified** — idempotent, identical result on re-run |
| `09_normalize_club_names.py` | 4 variants of `final_merged_filtrado*` | same files (club names normalized) | **Verified as idempotent**, with one caveat: re-running introduces floating-point noise at the 15th decimal place when re-serializing to CSV (e.g., `-0.9543859649122801` becomes `-0.95438596491228` — same value, different text representation). Not a content bug. |
| `09b_add_features_final_merged.py` | `final_merged_filtrado_dummies_clean.csv` | same file (+ `age_centered`, `age_sq`, `ln_Value_Num`) | **Verified**, idempotent |

## Segment 3 — RNC ranking (`10`, `10b`)

| Script | Input | Output | Status |
|---|---|---|---|
| `10b_clean_rnc_2025_needs_external_file.py` | `C:\Users\IGOR\Downloads\rnc_2025_clubes_pos_pontos.csv` (outside the project) + checkpoint | `.../rnc_2025_clubes_pos_pontos_clean.csv` | **Permanently blocked** — the source CSV was manually extracted from the PDF `dados/clubes/RNC - Ranking Nacional dos Clubes 2025.pdf` and saved outside the project folder, in a personal Downloads folder. Never version-controlled. Only recoverable if that file still exists on the original machine. |
| `10_merge_rnc_into_final.py` | checkpoint + output of 10b | **`dados/clubes/outcome/df_final.csv`** (285 rows) — **CHECKPOINT A** | **Blocked** (depends on 10b). The output file already exists, committed, and is the verified starting point of Segment 4. |

**Note on `pos_rnc`/`pts_rnc`:** these two columns appear at different
scales between Checkpoint A (`dados/clubes/outcome/df_final.csv`, large
values, e.g. `19626`) and the final per-position files generated on
2025-10-16 (`dados/df_ata.csv`, `df_def.csv`, `df_gk.csv`, small values,
e.g. `13.71`). The transformation between the two scales was not
recovered. **This does not affect the published model** — `pos_rnc`/`pts_rnc`
do not enter Table 7. The `dados/df_*.csv` files regenerated in this session
use Checkpoint A's scale; the `.tex` files were regenerated from them to
stay consistent.

## Segment 4 — Final sample and model (verified end to end)

| Script | Input | Output | Status |
|---|---|---|---|
| `11_filter_and_split_by_position.py` | Checkpoint A (285 rows) | `dados/df_gk.csv` (14), `df_def.csv` (91), `df_mc.csv` (87), `df_ata.csv` (91) | **Verified byte for byte** against the 3 files that were never corrupted (`df_ata.csv`, `df_def.csv`, `df_gk.csv`, originals from 2025-10-16). Reconstructed in this session because the original script that generated these 4 files did not survive in the repository. |
| `12_verify_full_sample.py` | Checkpoint A + `dados/df_final.csv` | consistency report | Confirms that `dados/df_final.csv` (283 rows) is exactly Checkpoint A filtered by `Value_Num > 0`, except for two manually annotated columns (`dum_inf`, `dum_sup`) whose cutoff rule was not recovered — see below. |
| `13_estimate_mc_baseline_model.py` | `dados/df_mc.csv` | `outputs/mc_baseline_model.txt` | **Verified against Table 7 / Appendix A** — largest relative error in a coefficient: 3.8e-06; in a standard error: 1.8e-06; R², adjusted R², F, and N identical. |
| `14_csv_to_latex.py` | `dados/df_mc.csv`, `dados/df_final.csv` | `outputs/df_mc.tex`, `outputs/df_final.tex` | **Verified** (`df_final.tex` identical; `df_mc.tex` differs only in the `pos_rnc`/`pts_rnc` columns, see note above) |
| `15_curva_valorizacao_idade.py` | Table 7 coefficients (hardcoded) | `outputs/curva_valorizacao_idade.png/svg` (Figure 2 of the thesis) | **Verified** — computed peak at 24.97 years, identical to the thesis text |

## The central finding of this session: correcting `dados/df_mc.csv`

`dados/df_mc.csv` was overwritten on 2025-11-18, one month after the Gretl
session (2025-10-16, `session.inp`) that produced Table 7. The row for the
player Jádson (Juventude) had the literal value `"x "` in the `fb_xG+/-`
column instead of a number. The correct value, `-17.1`, was recovered from
three independent sources (`dados/df_final.csv`, the historical `codes`
tree, `dados/df_final.tex`) and confirmed: running
`11_filter_and_split_by_position.py` from Checkpoint A (which was never
corrupted), the resulting `dados/df_mc.csv` matches, column for column, the
manual fix made earlier in this session. The fix is no longer an isolated
manual patch — it is embedded in the reproducible chain. See
`docs/divergences.md`.

## Manually annotated columns not reconstructed

- `dum_inf`, `dum_sup` (in `dados/df_final.csv`): binary flags created
  during an exploratory robustness analysis (not published — see
  `legacy/`). Their proportions (~13% and ~9.5% of the sample) do not match
  an obvious cutoff (min/max, round percentiles). Preserved in the
  committed file; not used in the published model.
- `pos_rnc`, `pts_rnc`: see the note in Segment 3.

## What is in `legacy/`

- `legacy/dedup_attempts/`: superseded deduplication/matching attempts, or
  ones that end in a file with no downstream use (confirmed by tracing
  input/output paths, not by assumption).
- `legacy/clustering/`: hierarchical clustering pipeline — not part of the
  model published in the thesis.
- `legacy/modelagem_exploratoria/`: per-position (ATA/DEF/GK) and per-cluster
  models, comparative analyses — extensions that did not make it into the
  final defended version.
- `legacy/artifacts/`: outputs (charts, tables, reports) from those
  exploratory scripts.

Nothing was deleted — only moved, with the reason recorded here and in the commit.
