"""Monthly minimum SSS: test4 (no river spreading) vs test5 (river spreading), 1958-1973."""
import glob, sys
import numpy as np, xarray as xr
ROOT = "/g/data/ol01/outputs/access-om3-25km"
RUNS = {"test4": "MC_25km_jra_iaf+wombatlite-test4-d28e0359",
        "test5": "MC_25km_jra_iaf+wombatlite-test5-38867fcd"}
st = xr.open_dataset(f"{ROOT}/{RUNS['test4']}/output000/access-om3.mom6.static.nc", decode_timedelta=False)
area = st.areacello.fillna(0).values
out = {}
for k, e in RUNS.items():
    t, mn, a1, a5, where = [], [], [], [], []
    for f in sorted(glob.glob(f"{ROOT}/{e}/output*/access-om3.mom6.2d.sos.1mon.min.*.nc")):
        yr = int(f.split(".")[-2])
        if yr > 1973: continue
        s = xr.open_dataset(f, decode_timedelta=False).sos_min.values  # (12, y, x)
        for m in range(s.shape[0]):
            v = s[m]
            t.append(yr + (m + 0.5) / 12)
            mn.append(np.nanmin(v))
            a1.append(area[v < 1].sum() / 1e6)   # km2 below 1 psu
            a5.append(area[v < 5].sum() / 1e6)
            j, i = np.unravel_index(np.nanargmin(v), v.shape)
            where.append((float(st.geolat.values[j, i]), float(st.geolon.values[j, i])))
    out[k] = xr.Dataset({"min_sss": ("t", mn), "area_lt1": ("t", a1), "area_lt5": ("t", a5),
                         "lat_min": ("t", [w[0] for w in where]), "lon_min": ("t", [w[1] for w in where])},
                        coords={"t": t})
    out[k].to_netcdf(f"{sys.argv[1]}/{k}_sss_min_ts.nc")
    o = out[k]
    print(k, "mean monthly min SSS %.3f, lowest %.3f, mean area<1psu %.0f km2, area<5psu %.0f km2"
          % (o.min_sss.mean(), o.min_sss.min(), o.area_lt1.mean(), o.area_lt5.mean()))
    lat, lon = np.round(o.lat_min.values), np.round(o.lon_min.values)
    u, c = np.unique(np.stack([lat, lon], 1), axis=0, return_counts=True)
    print("   most common location of minimum:", [(tuple(x), int(n)) for x, n in sorted(zip(map(tuple, u), c), key=lambda z: -z[1])[:4]])
