---
name: gis-spatial-analysis-remote-sensing-and-privacy
description: "Use when analyzing spatial data or sourcing it responsibly: spatial analysis including overlay, buffering, interpolation and spatial statistics with the modifiable areal unit problem, remote sensing and the imagery types and their processing levels, the data sources and their licensing, and location privacy including re-identification risk and why trajectory data is unusually sensitive."
---

# Geospatial Software: Spatial Analysis, Remote Sensing, Data Sources, and Privacy

> **Part 4 of 5** of the *Geospatial Software* reference (plugin `geospatial-software`), covering §11–§14. Sibling skills: `gis-coordinate-systems-data-models-and-formats` (§0–§3), `gis-indexing-databases-tiling-and-rendering` (§4–§7), `gis-routing-geocoding-and-positioning` (§8–§10), `gis-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Geodesy and projection mathematics are settled. Two areas moved. See §16 → `gis-reference` for the open basemap landscape and the cloud-native format stack.

> **Scope.** ⚠️ **§1 → `gis-coordinate-systems-data-models-and-formats` is the most important section and the one most often skipped.**
> Almost every serious geospatial bug is a coordinate reference system problem wearing a
> different hat.
>
> **⚠️ GOTCHA** boxes mark the errors that silently produce wrong answers — and this
> domain specializes in bugs that look plausible.
>
> **The three ideas that prevent most disasters:**
> 1. **⚠️ A coordinate is meaningless without its CRS.** "40.7128, −74.0060" is not a
>    location until you say which datum and which axis order. **Data with an unknown CRS
>    is not data** (§1 → `gis-coordinate-systems-data-models-and-formats`).
> 2. **⚠️ Every flat map lies.** Projection to a plane necessarily distorts area, angle,
>    distance, or shape — you choose which. **Web Mercator, the default of the entire web,
>    is unsuitable for area calculation and most analysis** (§1.3 → `gis-coordinate-systems-data-models-and-formats`).
> 3. **⚠️ The Earth is not a sphere, and for many purposes not even an ellipsoid.**
>    Haversine on a sphere is off by up to ~0.5%; the geoid differs from the ellipsoid by
>    ±100 m vertically. **Whether that matters is a requirements question you must
>    actually ask** (§1.1 → `gis-coordinate-systems-data-models-and-formats`, §10.3 → `gis-routing-geocoding-and-positioning`).

---

## §11. Spatial Analysis

**Overlay** — intersection, union, difference, symmetric difference.
**Buffer** — ⚠️ **and buffering in degrees is a classic error; a 0.001° buffer is ~111 m at
the equator and ~40 m at 70° latitude. Project first.**
**Spatial joins**, **dissolve/aggregate**, **centroid** (⚠️ **which can fall outside a
concave polygon — use `ST_PointOnSurface` when you need a point that's actually inside**),
**convex and concave hulls**, **Voronoi and Delaunay**, **simplification**
(⚠️ **Douglas-Peucker is standard; Visvalingam-Whyatt often looks better**).

**⚠️ Spatial statistics has its own pitfalls, and they're substantive:**
- **Spatial autocorrelation** — ⚠️ **Tobler's first law: near things are more related.**
  **This violates the independence assumption of ordinary regression**, so **Moran's I,
  Geary's C, and spatially-explicit models exist for a reason.**
- **⚠️ MAUP (modifiable areal unit problem)** — **results change with the size and shape of
  your aggregation units.** ⚠️ **This is not a nuisance, it's a fundamental limitation of
  areal data, and gerrymandering is its most famous exploitation.**
- **⚠️ Ecological fallacy** — **area-level correlations do not transfer to individuals.**
- **Interpolation**: IDW, ⚠️ **kriging (which uniquely gives you an uncertainty estimate
  alongside the prediction)**, splines.

---

## §12. Remote Sensing

**Resolution has four dimensions** — ⚠️ **spatial, spectral, temporal, radiometric — and
they trade against each other.**
**Platforms**: **Landsat** (⚠️ **30 m, free, and continuous since 1972 — the longest
record**), **Sentinel-1 SAR** and **Sentinel-2** (⚠️ **10 m, 5-day revisit, free**),
**MODIS/VIIRS**, commercial sub-metre.
**⚠️ SAR is the underused one**: **active, so it works at night and sees through cloud** —
and **InSAR measures ground deformation to millimetres** (see a geoscience reference).
**Indices**: **NDVI** `(NIR−Red)/(NIR+Red)` for vegetation, NDWI, NDBI.
**⚠️ Processing levels matter**: **Level-1 is top-of-atmosphere; Level-2 is
surface reflectance after atmospheric correction.** ⚠️ **Comparing TOA across dates is
meaningless — use surface reflectance for any time series.**
**Platforms**: **Google Earth Engine**, **Microsoft Planetary Computer**, **STAC** catalogs.

---

## §13. Data Sources

**OpenStreetMap** — ⚠️ **the foundational open dataset; ODbL licensed, which is share-alike
and has real obligations for derived databases.** **Extracts via Geofabrik, Overpass API
for queries, planet.osm for the whole thing.**
**Overture Maps** — §16.1 → `gis-reference`.
**Government and open data**: **US Census TIGER**, **USGS 3DEP** (elevation), **Natural
Earth** (⚠️ **the right choice for small-scale cartography — clean, public domain,
generalized**), **Copernicus**, **national mapping agencies** (⚠️ **licensing varies
enormously — Ordnance Survey is largely commercial, many EU agencies are open**).
**Elevation**: SRTM (30 m global), Copernicus DEM, national lidar.
**Commercial**: Google, HERE, TomTom, Esri, Mapbox.

**⚠️ Licensing is the part that catches engineering teams, and it is not optional
reading**: **ODbL's share-alike applies to derived databases and is genuinely restrictive
for commercial products; Google Maps terms prohibit storing results, using them with
non-Google basemaps, and much else; Natural Earth and most US federal data are public
domain.** ⚠️ **Check before you build, because "we'll swap the data source later" is
rarely cheap.**

---

## §14. Privacy

> **⚠️ GOTCHA — location data is among the most sensitive categories that exists, and
> "anonymized" location data usually isn't.** ⚠️ **Four spatiotemporal points are
> typically enough to uniquely identify an individual in a mobility dataset** — the
> foundational result here — **because human movement patterns are extraordinarily
> distinctive.** **Home and work locations fall out of a trace almost immediately.**

**⚠️ What location data reveals directly**: home, workplace, religious attendance, medical
facility visits, protest attendance, relationships (co-location), and routine — ⚠️ **which
means it functions as a proxy for several protected categories at once.**

**Regulation**: **GDPR treats location as personal data** (⚠️ **and inferences from it can
be special-category data**), **CCPA/CPRA names precise geolocation as sensitive personal
information**, and platform rules (iOS/Android permission models, background location
restrictions) are tightening independently.

**⚠️ Engineering practices that actually help:**
- **Collect the coarsest granularity that works.** ⚠️ **City-level often suffices for what
  the product actually does.**
- **Truncate precision** — ⚠️ **a 5th decimal place is ~1 m; you almost never need it.**
- **Aggregate and apply k-anonymity thresholds before release**; consider **differential
  privacy** for published statistics.
- **⚠️ Redact around sensitive POIs** — clinics, places of worship, shelters.
- **Short retention.** **Fuzz or exclude home locations.** **On-device processing where
  possible.**
- **⚠️ Be honest in the permission prompt** — "while using the app" versus background is a
  meaningfully different ask and users understand the difference.
