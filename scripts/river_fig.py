"""Monthly river runoff around a river mouth in the 8 km test2 run (river spreading on).

Cell corners come from ocean_hgrid.nc and the land mask from topog.nc, so land
blocks eliminated from the run's output (NaN coords there) still draw as land.

usage: river_fig.py <title> <lon0> <lon1> <lat0> <lat1> <outputNNN> <time index> <out.png>
"""
import glob
import sys

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import LogNorm

RUN = "/g/data/ol01/outputs/access-om3-8km/MC_8km_jra_ryf-test2-expt-c349f800"
GRIDS = "/g/data/vk83/prerelease/configurations/inputs/access-om3/share/grids/global.8km"
HGRID = f"{GRIDS}/2026.10.07/ocean_hgrid.nc"
TOPOG = f"{GRIDS}/2026.10.08/topog.nc"

name, lon0, lon1, lat0, lat1 = sys.argv[1], *map(float, sys.argv[2:6])
seg, tidx, out = sys.argv[6], int(sys.argv[7]), sys.argv[8]

fr = xr.open_dataset(glob.glob(f"{RUN}/{seg}/access-om3.mom6.2d.friver.1mon.mean.*.nc")[0],
                     decode_timedelta=False).friver.isel(time=tidx)
print("time", str(fr.time.values))
hg = xr.open_dataset(HGRID)
xc, yc = hg.x.values[::2, ::2], hg.y.values[::2, ::2]   # cell corners, (ny+1, nx+1)
depth = xr.open_dataset(TOPOG).depth.values
assert depth.shape == fr.shape, (depth.shape, fr.shape)

# subset to the box (plus a margin) using cell centres
xt, yt = hg.x.values[1::2, 1::2], hg.y.values[1::2, 1::2]
lont = ((xt + 180) % 360) - 180
jj, ii = np.where((lont > lon0 - 2) & (lont < lon1 + 2) & (yt > lat0 - 1) & (yt < lat1 + 1))
j0, j1, i0, i1 = jj.min(), jj.max() + 1, ii.min(), ii.max() + 1
XC, YC = xc[j0:j1 + 1, i0:i1 + 1], yc[j0:j1 + 1, i0:i1 + 1]
wet = depth[j0:j1, i0:i1] > 0
F = np.nan_to_num(fr.values[j0:j1, i0:i1])

plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Nimbus Sans", "Arial", "DejaVu Sans"],
                     "font.size": 11, "savefig.dpi": 300, "savefig.bbox": "tight"})
proj = ccrs.LambertConformal(central_longitude=(lon0 + lon1) / 2, central_latitude=(lat0 + lat1) / 2)
fig = plt.figure(figsize=(3.6, 4.4))
ax = fig.add_axes([0, 0.12, 1, 0.85], projection=proj)
ax.set_extent([lon0, lon1, lat0, lat1], ccrs.PlateCarree())
ax.pcolormesh(XC, YC, np.where(wet, np.nan, 1.0), cmap="Greys", vmin=0, vmax=4,
              transform=ccrs.PlateCarree(), rasterized=True)
pc = ax.pcolormesh(XC, YC, np.where(wet & (F > 1e-5), F, np.nan), cmap="Purples",
                   norm=LogNorm(1e-4, 1e-1), transform=ccrs.PlateCarree(), rasterized=True)
ax.set_title(name, loc="left", fontsize=12, fontweight="bold", color="#1f1f1f")
cax = fig.add_axes([0.08, 0.06, 0.84, 0.03])
cb = fig.colorbar(pc, cax=cax, orientation="horizontal", extend="both")
cb.set_label(r"river runoff (kg m$^{-2}$ s$^{-1}$)", color="#1f1f1f")
cb.outline.set_visible(False)
fig.savefig(out)
