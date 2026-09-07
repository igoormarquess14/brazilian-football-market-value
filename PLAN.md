# PLAN.md

Execution plan for turning `claude_git` into a public portfolio repository.
Ordered by portfolio value (what a visitor sees first comes first), not by
the logical sequence of building the pipeline.

Status: diagnosis completed on 2026-08-31. Steps 1 through 7 below are done.
Git history was squashed into a single local commit. Nothing has been
pushed to GitHub yet — the previous target repository, `transfermkt_scraper`,
was deleted by the user; a new one will be created and its coordinates
passed before any push (see Step 8).

**2026-08-31 update:** the user requested the repository be published in
English. `CLAUDE.md`'s Language section, `README.md`, `docs/data_sources.md`,
`docs/pipeline.md`, `docs/divergences.md` (renamed from `docs/divergencias.md`),
`legacy/README.md`, and this file were translated. Data column names
(`Clube`, `Player`, `Value_Num`, `ln_Value_Num`, `age_centered`, `age_sq`,
`fb_xG(+/-)`, `fb_MnMP`, etc.), the thesis PDF, and the contents of `legacy/`
scripts were explicitly left untouched — the thesis stays in Portuguese and
column names must match what `session.inp` references for the reproduction
to hold.

---

## Step 1 — README and repository narrative — ✅ DONE on 2026-08-31
**Deliverable:** `README.md` at the root — main result, how to reproduce it, repository structure table, current limitations, and a note on data sources.

## Step 2 — Reproduce the single published model (Table 7 / Appendix A) — ✅ DONE on 2026-08-31

**Fix applied:** `dados/df_mc.csv`, row for player `Jádson` (Juventude), column `fb_xG+/-`: corrupted value `"x "` replaced with `-17.1`. Root cause: the file was overwritten on 2025-11-18, one month after the Gretl session (2025-10-16, per `session.inp`) that produced Table 7. The value `-17.1` was confirmed from three independent sources predating the corruption. No other field in the file was touched (a surgical single-cell edit).

**Script created:** `codes/pipeline/13_estimate_mc_baseline_model.py` — reads `dados/df_mc.csv` via `pathlib`/`PROJECT_ROOT` (no absolute path), explicit sample cut, estimates non-robust OLS with `statsmodels` (`cov_type="nonrobust"`, matching Gretl's `ols` without `--robust`), compares each coefficient/SE/R²/F against Table 7's reference values, and writes a report to `outputs/mc_baseline_model.txt`.

**Verification result:** reproduction **within `CLAUDE.md`'s tolerance on every criterion** — N=87 identical; largest relative error in a coefficient = 3.77e-06 (limit 1e-4); largest relative error in an SE = 1.77e-06 (limit 1e-3); R²=0.226538 and adjusted R²=0.188808 identical to the thesis; F=6.004195 and p(F)=0.000274 identical. The script is idempotent.

## Step 3 — `docs/divergences.md` — ✅ DONE on 2026-08-31
**Deliverable:** `docs/divergences.md` with 4 items: (1) the `dados/df_mc.csv` corruption and its resolution — resolved; (2) absence of a `.gdt`/full Gretl session, only `session.inp` — open, no impact on the result; (3) broader specifications in `legacy/` (per-position models, clustering, RNC) not published in the thesis — open, decision made in Step 7; (4) two links in the cleaning chain with no surviving script — open, no impact on the result.

## Step 4 — Consolidate the data pipeline into numbered scripts — ✅ DONE on 2026-08-31

**Deliverable:** `codes/pipeline/` with a numbered chain `01` through `15`, each script using `PROJECT_ROOT`/`pathlib` (no absolute path). Full link-by-link documentation in `docs/pipeline.md`. Scripts outside the final chain moved to `legacy/` (`dedup_attempts/`, `clustering/`, `modelagem_exploratoria/`, `artifacts/`), with the reason recorded in the commit — none deleted. Scraping isolated in `codes/scraping/` (frozen, documented as likely broken).

**Real verification (run, not just statically analyzed):**
- Scripts `01→02→03` (club merge): the chain reproduces `todos_clubes_2025_final.csv` byte for byte.
- `06`, `07`, `08`, `09`, `09b`: each reproduces its existing output file byte for byte (or idempotently, for `08`/`09b`).
- `11` (new, reconstructed in this session): reproduces `dados/df_ata.csv`, `df_def.csv`, `df_gk.csv` byte for byte against the never-corrupted 2025-10-16 originals, and reproduces `dados/df_mc.csv` identical to Step 2's manual fix — the data fix is now embedded in the chain, no longer an isolated patch.
- `13` (model): reproduced against Table 7/Appendix A, same result as Step 2.
- `14`/`15`: reproduce `df_final.tex` and Figure 2 (peak at 24.97 years, identical to the thesis text).
- `04`, `10`, `10b`: **blocked** — depend on files that do not exist in the repository (one of them, the RNC ranking CSV, was manually extracted from the PDF and saved outside the project folder, in a personal Downloads folder — never version-controlled). The output files these scripts would produce already exist, committed, and serve as checkpoints for the rest of the chain.

**Genuine, documented, non-simulated gaps** (see `docs/pipeline.md` for detail): column selection from `final_merged_fixed.csv` to `final_merged_filtrado.csv` (`criar_csv_filtrado.py` exists but is empty) and creation of the position dummies — no surviving script for either; the `Position_Num → Dum_*` mapping is not a pure function (specific cases were decided manually). The resulting files are preserved; the logic that generated them is not. Neither gap affects the published model or the Table 7 reproduction.

## Step 5 — Decision and documentation on data and publication — ✅ DONE on 2026-08-31

**User decisions:** (1) the RNC PDF is not redistributed; (2) processed data is published, raw scraped dumps are not.

**Deliverable:** `docs/data_sources.md` (origin, collection date per source, what is version-controlled and why, how to re-obtain the raw data). `.gitignore` updated to exclude `dados/clubes/*_2024*.csv`, `dados/selecao/`, `dados/minutes_played/`, `dados/transfers_brazilian_league/`, and the RNC PDF — verified file by file with `git check-ignore` before applying. These files were removed from git's index (`git rm --cached`) but remain on local disk.

## Step 6 — Deduplicate artifact and data directories — ✅ DONE on 2026-08-31 (via Step 4)
The 9 `artifacts*` folders were consolidated into `legacy/artifacts/` and the `codes/dados/cluster/` duplicate into `legacy/clustering/dados_cluster_duplicado/` during the pipeline reorganization (Step 4).

## Step 7 — Decide the fate of unpublished exploratory work — ✅ DONE on 2026-08-31

**User decision:** keep `legacy/` public, clearly labeled as unpublished exploratory work.

**Deliverable:** `legacy/README.md` explaining what is in each subfolder (`dedup_attempts/`, `clustering/`, `modelagem_exploratoria/`, `artifacts/`) and why it is not part of the official result.

## Pre-push review — ✅ DONE on 2026-08-31

The user reviewed the single squashed commit and requested three corrections, all applied:
- `dados/clubes/outcome/` had 18 files; 17 were debug trail from successive merges (not required by any script in the reproducible pipeline) and were removed. Only `df_final.csv` stayed — it is the real input to `codes/pipeline/11` and `12`.
- Fresh grep for credentials/tokens/secrets across the whole repository: nothing found. Local absolute paths (`C:\Users\IGOR\...`) remain in 36 files under `legacy/` (not fixed on purpose, it's frozen code) — not a credential, but it reveals the local folder structure. **User decision:** keep as is, explicitly labeled — done in `legacy/README.md`.
- `dados/df_mc.tex`/`df_final.tex` are legitimate output from `codes/pipeline/14_csv_to_latex.py` (not debug trail), but were misplaced under `dados/` instead of `outputs/`. Moved, script fixed, re-tested with identical output.
- `LICENSE` (MIT) added, covering the code. Data follows `docs/data_sources.md`, outside the license's scope.

Git history was squashed into a single commit (twice, after the review round) using an orphan branch plus `git reflog expire` + `git gc --prune=now`, so the old commits containing raw data and the RNC PDF are not reachable, even as loose objects. Verified with `git rev-list --objects --all`.

## Step 8 — GitHub push — ✅ DONE
`git init` was done on 2026-08-31 as a safety net before Step 4's reorganization, with identity configured by the user. The original target repository, `transfermkt_scraper`, was deleted by the user (a "scraper" name undersold what the project became). New repository created at `github.com/igoormarquess14/brazilian-football-market-value`; the single squashed commit is pushed and `master` is up to date with `origin/master`.
