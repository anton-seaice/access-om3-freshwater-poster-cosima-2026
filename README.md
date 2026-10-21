# Freshwater Forcings in ACCESS-OM3 — COSIMA 2026 poster

A0 poster on how ACCESS-OM3 handles freshwater from its prescribed JRA55-do
forcing: global freshwater balance, river runoff spreading, iceberg melt
spreading, a seasonal cycle in Antarctic iceberg melt, and their impacts on
latent heat (frazil ice) and salinity.

Built in LaTeX from the ACCESS-NRI poster template (V4); the template's
branding is redrawn in TikZ at the same positions.

## Build

```sh
xelatex poster.tex   # run twice so the background overlay lands on page 1
```

XeLaTeX or LuaLaTeX is needed (`fontspec`). The template's Arial / Arial Black
are used when installed; otherwise it falls back to Nimbus Sans (Gadi) or TeX
Gyre Heros (Overleaf). `\pscale` at the top of `poster.tex` sets the size:
`2.12851` gives A0, `1` gives the template's native 395 × 558 mm.

## Layout

| Path | Contents |
|---|---|
| `poster.tex` | poster source |
| `logos/` | ACCESS-NRI template images (ACCESS logo, colour bar, partner and NCRIS logos) |
| `figs/` | figures used on the poster |
| `scripts/` | scripts that make the impacts and river figures from model output on NCI Gadi |

## Figure sources

| Figure | Source |
|---|---|
| `fw_mass_constant.png` | 100 km RYF test of the freshwater balance (COSIMA talk, July 2026) |
| `river_yenisei_8km_test2.png` | `scripts/river_fig.py`, 8 km RYF test2 (`MC_8km_jra_ryf-test2-expt-c349f800`) |
| `rofi_jan_maps_scaled_spread.png`, `rofi_seasonal_timeseries_sh.png` | 100 km IAF test, [access-om3-configs#1492](https://github.com/ACCESS-NRI/access-om3-configs/issues/1492) |
| `impact_frazil.png` | `scripts/compute_impacts.py` + `plot_impacts.py`, 25 km IAF test3v2 vs test4 |
| `impact_fresh_area.png` | `scripts/sss_min.py` + `plot_sss_min.py`, 25 km IAF test4 vs test5 (1958–1973) |

Model output is read from `/g/data/ol01/outputs/access-om3-25km` and
`/g/data/ol01/outputs/access-om3-8km` (NCI projects `ol01`, `xp65`).

## Regenerating the impacts figures (on Gadi)

```sh
qsub scripts/run.pbs                                   # writes reduced/ (≈15 min)
module use /g/data/xp65/public/modules && module load conda/analysis3
python scripts/plot_impacts.py reduced figs            # impact_frazil.png
python scripts/sss_min.py reduced                      # test4/test5 minimum-SSS series
python scripts/plot_sss_min.py reduced figs/impact_fresh_area.png
python scripts/river_fig.py "Yenisei, June" 78 86 70.5 74 output002 1 figs/river_yenisei_8km_test2.png
```

`plot_impacts.py` also writes `impact_restoring.png`, which is not on the poster.
