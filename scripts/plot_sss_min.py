"""Area of very fresh surface water: test4 (no river spreading) vs test5 (river spreading)."""
import sys
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

IN, OUT = sys.argv[1], sys.argv[2]
BEFORE, AFTER = "#E8833A", "#236298"   # validated pair, same as the other impacts figures
INK, MUTED, GRID = "#1f1f1f", "#5f6368", "#e3e3e3"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Nimbus Sans", "Arial", "DejaVu Sans"],
    "font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300, "savefig.bbox": "tight"})

fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"wspace": 0.42})
for ax, var, title in ((axs[0], "area_lt1", "Surface area fresher than 1 psu"),
                       (axs[1], "area_lt5", "Surface area fresher than 5 psu")):
    ends = {}
    for key, col, lab in (("test4", BEFORE, "before"), ("test5", AFTER, "after")):
        d = xr.open_dataset(f"{IN}/{key}_sss_min_ts.nc")
        yr = np.floor(d.t.values).astype(int)
        ann = d[var].groupby(xr.DataArray(yr, dims="t")).mean() / 1e3   # 10^3 km2, annual mean
        x = ann[ann.dims[0]].values
        ax.plot(x, ann, color=col, lw=2, solid_capstyle="round")
        ends[lab] = (x[-1], float(ann[-3:].mean()))
    hi = max(ends, key=lambda k: ends[k][1])
    for lab, (x, y) in ends.items():
        ax.annotate(lab, (x, y), xytext=(6, 7 if lab == hi else -7), textcoords="offset points",
                    va="center", color=INK, fontsize=11)
    ax.set_title(title, loc="left")
    ax.set_ylim(bottom=0)
    if ax is axs[0]:
        ax.set_ylabel(r"10$^3$ km$^2$ (annual mean)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
fig.savefig(OUT)
for key in ("test4", "test5"):
    d = xr.open_dataset(f"{IN}/{key}_sss_min_ts.nc")
    print(key, "area<1 %.1f, area<5 %.1f (10^3 km2, 1958-1973 mean)" % (d.area_lt1.mean() / 1e3, d.area_lt5.mean() / 1e3))
