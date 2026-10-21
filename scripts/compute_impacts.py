"""Reduce test3v2 (no balance/spreading) and test4 (balance + spreading) output
to small netCDF files for the poster's impacts figures.

Per run:
  - annual area-mean |salt_flux_added| (salinity restoring), global / S of 60S / N of 60N
  - annual total frazil ice volume growth, S of 50S / N of 50N
  - 1994-2023 mean maps of salt_flux_added and frazil_m
"""
import glob
import os
import sys

import numpy as np
import xarray as xr

ROOT = "/g/data/ol01/outputs/access-om3-25km"
RUNS = {
    "test3v2": "MC_25km_jra_iaf+wombatlite-test3v2-00532b88",
    "test4": "MC_25km_jra_iaf+wombatlite-test4-d28e0359",
}
MAP_YEARS = (1994, 2023)
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

for key, exp in RUNS.items():
    base = f"{ROOT}/{exp}"
    mstat = xr.open_dataset(f"{base}/output000/access-om3.mom6.static.nc", decode_timedelta=False)
    cstat = xr.open_dataset(f"{base}/output000/access-om3.cice.static.nc", decode_timedelta=False)
    area_o, lat_o = mstat.areacello.fillna(0), mstat.geolat
    area_c, lat_c = cstat.tarea.fillna(0), cstat.TLAT
    regions_o = {"global": lat_o > -91, "south": lat_o < -60, "north": lat_o > 60}
    regions_c = {"south": lat_c < -50, "north": lat_c > 50}

    # ---- salinity restoring
    rows, maps = [], []
    for f in sorted(glob.glob(f"{base}/output*/access-om3.mom6.2d.salt_flux_added.1mon.mean.*.nc")):
        sfa = xr.open_dataset(f, decode_timedelta=False).salt_flux_added.load()
        year = int(sfa.time.dt.year[0])
        absann = np.abs(sfa).mean("time")
        rec = {"year": year}
        for r, m in regions_o.items():
            w = area_o.where(m, 0)
            rec[f"abs_{r}"] = float((absann * w).sum() / w.sum())
        rows.append(rec)
        if MAP_YEARS[0] <= year <= MAP_YEARS[1]:
            maps.append(sfa.mean("time"))
        print(key, "sfa", year, flush=True)
    ts = xr.Dataset({k: ("year", [r[k] for r in rows]) for k in rows[0] if k != "year"},
                    coords={"year": [r["year"] for r in rows]})
    ts.attrs["units"] = "kg m-2 s-1 (area-mean of |annual-mean salt_flux_added|)"
    ts.to_netcdf(f"{OUT}/{key}_restoring_ts.nc")
    xr.concat(maps, "year").mean("year").rename("salt_flux_added").to_dataset().assign(
        geolat=lat_o, geolon=mstat.geolon).to_netcdf(f"{OUT}/{key}_restoring_map.nc")

    # ---- frazil (CICE, monthly files)
    files = sorted(glob.glob(f"{base}/output*/access-om3.cice.1mon.mean.*.nc"))
    annual, maps = {}, []
    for f in files:
        fr = xr.open_dataset(f, decode_timedelta=False).frazil_m.isel(time=0).load()  # cm/day
        year = int(os.path.basename(f).split(".")[-2].split("-")[0])
        vol = {r: float((fr.fillna(0) * area_c.where(m, 0)).sum()) * 0.01 / 86400  # m3/s
               for r, m in regions_c.items()}
        a = annual.setdefault(year, {r: [] for r in regions_c})
        for r in regions_c:
            a[r].append(vol[r])
        if MAP_YEARS[0] <= year <= MAP_YEARS[1]:
            maps.append(fr)
    years = sorted(annual)
    ts = xr.Dataset({f"frazil_{r}": ("year", [np.mean(annual[y][r]) for y in years]) for r in regions_c},
                    coords={"year": years})
    ts.attrs["units"] = "m3 s-1 of frazil ice growth (annual mean)"
    ts.to_netcdf(f"{OUT}/{key}_frazil_ts.nc")
    xr.concat(maps, "t").mean("t").rename("frazil_m").to_dataset().assign(
        TLAT=lat_c, TLON=cstat.TLON).to_netcdf(f"{OUT}/{key}_frazil_map.nc")
    print(key, "frazil done", flush=True)
