"""Poster impacts figures from the reduced files written by compute_impacts.py.

Usage: python plot_impacts.py <reduced dir> <figure dir>
"""
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

IN, OUT = sys.argv[1], sys.argv[2]
CICE_STATIC = ("/g/data/ol01/outputs/access-om3-25km/MC_25km_jra_iaf+wombatlite-test4-d28e0359/"
               "output000/access-om3.cice.static.nc")

BEFORE, AFTER = "#E8833A", "#236298"   # validated pair (dataviz validator, light)
INK, MUTED, GRID = "#1f1f1f", "#5f6368", "#e3e3e3"
LABELS = {"test3v2": "before", "test4": "after"}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})


def circle_boundary(ax):
    theta = np.linspace(0, 2 * np.pi, 200)
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T * 0.5 + 0.5
    ax.set_boundary(mpath.Path(verts), transform=ax.transAxes)


def timeseries(ax, var, scale, ylabel, title):
    kind = "frazil" if var.startswith("frazil") else "restoring"
    ends = {}
    for key, col in (("test3v2", BEFORE), ("test4", AFTER)):
        ts = xr.open_dataset(f"{IN}/{key}_{kind}_ts.nc")
        y = ts[var] * scale
        ax.plot(ts.year, y, color=col, lw=2, solid_capstyle="round")
        ends[key] = (float(ts.year[-1]), float(y[-5:].mean()))  # label at the recent mean
    # direct labels, nudged apart so they never overlap when the lines end close together
    hi = max(ends, key=lambda k: ends[k][1])
    for key, (x, y) in ends.items():
        ax.annotate(LABELS[key], (x, y), xytext=(6, 7 if key == hi else -7),
                    textcoords="offset points", va="center", color=INK, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def south_map(ax, da, lon, lat, vmax, cbar_label, fig):
    ax.set_extent([-180, 180, -90, -55], ccrs.PlateCarree())
    circle_boundary(ax)
    pc = ax.pcolormesh(lon, lat, da, transform=ccrs.PlateCarree(), cmap="RdBu_r",
                       vmin=-vmax, vmax=vmax, rasterized=True, shading="auto")
    ax.add_feature(cfeature.LAND, facecolor="#d9d9d9", edgecolor="none", zorder=2)
    cb = fig.colorbar(pc, ax=ax, orientation="horizontal", shrink=0.8, pad=0.04, extend="both")
    cb.set_label(cbar_label, color=INK)
    cb.outline.set_visible(False)


# ------------------------------------------------------------ salinity restoring
fig = plt.figure(figsize=(7.0, 3.4))
ax1 = fig.add_axes([0.08, 0.15, 0.50, 0.72])
timeseries(ax1, "abs_south", 1e6, r"|restoring salt flux| (mg m$^{-2}$ s$^{-1}$)",
           "Restoring south of 60°S")
ax2 = fig.add_axes([0.62, 0.05, 0.38, 0.88], projection=ccrs.SouthPolarStereo())
b = xr.open_dataset(f"{IN}/test3v2_restoring_map.nc")
a = xr.open_dataset(f"{IN}/test4_restoring_map.nc")
# subtract raw arrays: the runs' yh coords differ by float rounding, so xarray alignment drops rows
diff = a.salt_flux_added.copy(data=(np.abs(a.salt_flux_added.values) - np.abs(b.salt_flux_added.values)) * 1e6)
XH, YH = a.xh.values, a.yh.values   # nominal 1D coords: exact south of the tripole
south_map(ax2, diff.values, XH, YH, float(np.nanpercentile(np.abs(diff.where(a.geolat < -55)), 98)),
          r"after − before, |flux| (mg m$^{-2}$ s$^{-1}$)", fig)
ax2.set_title("1994–2023 mean", loc="center")
fig.savefig(f"{OUT}/impact_restoring.png")

# ------------------------------------------------------------ latent heat -> frazil
fig = plt.figure(figsize=(7.0, 3.4))
ax1 = fig.add_axes([0.08, 0.15, 0.50, 0.72])
timeseries(ax1, "frazil_south", 1e-3, r"frazil growth (10$^3$ m$^3$ s$^{-1}$)",
           "Frazil ice formed south of 50°S")
# where the change happens: the first ring of ocean cells next to land vs offshore
from scipy.ndimage import binary_dilation
cst = xr.open_dataset(CICE_STATIC, decode_timedelta=False)
area, lat, ocean = cst.tarea.fillna(0).values, cst.TLAT.values, cst.tmask.values > 0
coast = binary_dilation(~ocean) & ocean
south = lat < -50
vals = {}
for key in ("test3v2", "test4"):
    fr = np.nan_to_num(xr.open_dataset(f"{IN}/{key}_frazil_map.nc").frazil_m.values)
    vol = fr * area * 0.01 / 86400 * 1e-3   # 10^3 m3/s
    vals[key] = [vol[coast & south].sum(), vol[~coast & ocean & south].sum()]
ax2 = fig.add_axes([0.70, 0.15, 0.28, 0.72])
x = np.arange(2)
w = 0.38
for i, (key, col) in enumerate((("test3v2", BEFORE), ("test4", AFTER))):
    bars = ax2.bar(x + (i - 0.5) * (w + 0.02), vals[key], w, color=col)
    for xb, v in zip(x + (i - 0.5) * (w + 0.02), vals[key]):
        ax2.text(xb, v + 1, f"{v:.0f}", ha="center", va="bottom", color=INK, fontsize=10)
ax2.set_xticks(x, ["coastal\ncells", "offshore"])
ax2.set_title("1994–2023 mean", loc="left")
ax2.set_ylim(0, max(max(v) for v in vals.values()) * 1.18)
ax2.grid(axis="y", color=GRID, lw=0.8)
ax2.set_axisbelow(True)
ax2.legend([plt.Rectangle((0, 0), 1, 1, color=BEFORE), plt.Rectangle((0, 0), 1, 1, color=AFTER)],
           ["before", "after"], frameon=False, loc="upper left", fontsize=10)
fig.savefig(f"{OUT}/impact_frazil.png")
print({k: [round(float(v), 1) for v in vv] for k, vv in vals.items()})
print("done")
