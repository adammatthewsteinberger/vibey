---
name: gis-reference
description: "Use when correcting a geospatial misconception, checking what moved in the open basemap landscape and the cloud-native format stack (verified August 2026), looking up a precision, scale or accuracy figure, finding the books and tools, or needing a picker and a debugging checklist for coordinates that land in the wrong place. Companion to the other geospatial-software skills."
---

# Geospatial Software: Misconceptions, What Moved, Numbers, and Tools

> **Part 5 of 5** of the *Geospatial Software* reference (plugin `geospatial-software`), covering §15–§20. Sibling skills: `gis-coordinate-systems-data-models-and-formats` (§0–§3), `gis-indexing-databases-tiling-and-rendering` (§4–§7), `gis-routing-geocoding-and-positioning` (§8–§10), `gis-spatial-analysis-remote-sensing-and-privacy` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Geodesy and projection mathematics are settled. Two areas moved. See §16 below for the open basemap landscape and the cloud-native format stack.

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

## §15. Misconceptions

| Misconception | Correction |
|---|---|
| A lat/lon pair is a location | ⚠️ **Not without a CRS and epoch** (§1 → `gis-coordinate-systems-data-models-and-formats`) |
| EPSG:4326 is (lon, lat) | ⚠️ **Formally (lat, lon). GeoJSON is (lon, lat). Check every boundary** (§1.2 → `gis-coordinate-systems-data-models-and-formats`) |
| Web Mercator is fine for analysis | ⚠️ **Never compute area or distance in it** (§1.3 → `gis-coordinate-systems-data-models-and-formats`) |
| WGS84 and NAD83 are the same | ⚠️ **1–2 m apart and diverging** (§1.1 → `gis-coordinate-systems-data-models-and-formats`) |
| Datums are static | ⚠️ **Continents move; modern datums carry an epoch** (§1.1 → `gis-coordinate-systems-data-models-and-formats`) |
| Haversine is accurate | ⚠️ **Spherical — up to ~0.5% off. Use Vincenty/Karney for precision** (§17) |
| GNSS altitude is elevation | ⚠️ **Ellipsoidal vs geoid — up to ±100 m** (§10.3 → `gis-routing-geocoding-and-positioning`) |
| Reported GPS accuracy is real accuracy | ⚠️ **A fused confidence estimate, often optimistic** (§10.2 → `gis-routing-geocoding-and-positioning`) |
| Buffer in degrees | ⚠️ **111 m at the equator, ~40 m at 70°. Project first** (§11 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| A centroid is inside its polygon | ⚠️ **Not for concave shapes. Use ST_PointOnSurface** (§11 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| `ST_Distance` on 4326 gives metres | ⚠️ **It gives degrees. Use geography or project** (§5 → `gis-indexing-databases-tiling-and-rendering`) |
| Geohash prefixes solve proximity | ⚠️ **Edge problem — check neighbouring cells** (§4 → `gis-indexing-databases-tiling-and-rendering`) |
| Spatial data can use ordinary regression | ⚠️ **Autocorrelation violates independence** (§11 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| Aggregation boundaries don't affect results | ⚠️ **MAUP. They do, fundamentally** (§11 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| Shapefile is a reasonable modern choice | ⚠️ **2 GB, 10-char fields, encoding issues** (§3 → `gis-coordinate-systems-data-models-and-formats`) |
| Nearest-road snapping is map matching | ⚠️ **Use an HMM; parallel roads and overpasses break naive snapping** (§8 → `gis-routing-geocoding-and-positioning`) |
| Comparing TOA imagery across dates is valid | ⚠️ **Use surface reflectance** (§12 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| Anonymized location data is anonymous | ⚠️ **~4 points identify an individual** (§14 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| OSM data is free to use however you like | ⚠️ **ODbL is share-alike with real obligations** (§13 → `gis-spatial-analysis-remote-sensing-and-privacy`) |
| Overture replaces OpenStreetMap | ⚠️ **It's largely built FROM OSM — ~40% of records** (§16.1) |

---

## §16. What Moved — verified August 2026

### 16.1 ⚠️ The open basemap landscape
**Overture Maps Foundation** — under the **Linux Foundation**, announced December 2022,
backed by **Amazon, Meta, Microsoft and TomTom**, with **Esri** participating.
**Data assembled from ~200 sources into six themes**, distributed primarily as
**GeoParquet** (and PMTiles), under **CDLA-Permissive v2 where licensing allows.**
**The GA release included 2.3 billion building footprints**, and Overture data
⚠️ **already powers Microsoft's Bing Maps and Esri's ArcGIS Living Atlas**, with Esri
using it to fill coverage gaps in its 3D Buildings layer.

**⚠️ GERS (Global Entity Reference System) is the actual point of Overture**, not the data
volume: **persistent unique IDs attached to real-world entities so datasets can be joined
without re-conflation.** ⚠️ **The stated problem it solves is the "conflation tax" — the
recurring cost of re-matching your data to a new map release.** **As one Overture figure
put it, reality doesn't change, so the IDs shouldn't either.**

> **⚠️ GOTCHA — there is a live and genuinely unresolved governance dispute here, and you
> should know about it before building on GERS.**
> **In early 2026 the OGC considered adopting GERS as a community standard, and the
> proposal drew a sharp reaction from parts of the OpenStreetMap community.** ⚠️ **The
> objections reported are corporate enclosure, opaque governance, a membership model
> cited at $300,000, and a technical criticism of roughly 20% ID churn** — **which, if
> accurate, undercuts the persistence claim that is GERS's entire value proposition.**
>
> ⚠️ **I could not independently verify the churn figure, and it comes from a source
> arguing one side.** **Treat it as a claim to check rather than an established number.**
> **But the dispute itself is real and worth tracking.**

**⚠️ The relationship to OSM is the thing most often got wrong**: ⚠️ **Overture is not a
fork or a competitor — roughly 40% of Overture records come from OpenStreetMap**, the
foundation encourages members to contribute back to OSM, and ⚠️ **Overture data derived
from OSM carries ODbL obligations regardless of Overture's own licence.** **Check the
attribution documentation rather than assuming CDLA covers everything.**

**Also note**: **Esri moved its OpenStreetMap Vector Basemap to mature support in December
2024** after Meta moved the Daylight Distribution to mature support — ⚠️ **a quiet but
real consolidation of the open basemap supply chain toward Overture.**

### 16.2 The cloud-native format stack
**⚠️ The unifying principle is simple and it changed the economics of serving geodata:
put a deterministic layout and a front-loaded index in a single file on object storage,
and let clients fetch only the bytes they need via HTTP range requests.** **No server
process.**
```
COG          raster    ⚠️ internal tiling + overviews — the pattern all the others copied
GeoParquet   vector    columnar analytics; ⚠️ partition by region for large datasets
FlatGeobuf   vector    streamable, bbox-filtered over HTTP
PMTiles      tiles     ⚠️ single-file pyramid; replaces MBTiles, which needed a server
                       because SQLite can't be range-read efficiently
Zarr         N-d       data cubes
COPC         lidar     cloud-optimized point clouds
STAC         metadata  ⚠️ the discovery layer that ties them together
```
**⚠️ Tooling has caught up, which is what makes this practical now**: **tippecanoe
(maintained by Felt since v2.0)** for tile generation, **MapLibre plugins reading COG,
Zarr, PMTiles, FlatGeobuf, GeoParquet and STAC directly in the browser**, **Martin serving
tiles from GeoParquet**, and **DuckDB, Sedona, BigQuery, Snowflake and Databricks all
reading GeoParquet from cloud storage.**

**⚠️ Reported cost effects are large** — one write-up describes moving from GeoServer to
serverless PMTiles on object storage with a **~90% cost reduction** — ⚠️ **though that is a
vendor-adjacent figure and your mileage depends heavily on traffic pattern and egress
pricing.** **The architectural claim (no server process) is solid; treat the percentage as
illustrative.**

**⚠️ When NOT to use these**: **small datasets (<1 MB) where GeoJSON is simpler; interchange
with legacy tools where Shapefile or GeoPackage still wins; and editing workflows needing
row-level mutation, where PostGIS or GeoPackage are the right answer.** **Cloud-native
formats are read-optimized and immutable by design.**

---

## §17. Numbers

```
EARTH
Equatorial radius 6,378,137 m · polar 6,356,752 m · ⚠️ flattening 1/298.257223563
Mean radius 6,371,008 m · 1° latitude ≈ 111.32 km
⚠️ 1° longitude = 111.32 km × cos(latitude) — 0 at the poles

COORDINATE PRECISION ⚠️
1 decimal place  ~11 km      4 places  ~11 m
2 places         ~1.1 km     5 places  ~1.1 m
3 places         ~110 m      6 places  ~0.11 m  ⚠️ beyond GNSS accuracy — and a privacy risk
7+ places        ⚠️ false precision. Truncate

EPSG
4326 WGS84 lat/lon · 3857 Web Mercator · 4269 NAD83
UTM north 326xx · UTM south 327xx (xx = zone 01–60)

TILES
Zoom 0 = 1 tile · zoom z = 4^z tiles · tile 256×256 (or 512)
⚠️ Web Mercator clipped at ±85.05113°
Resolution at z: ~156543 × cos(lat) / 2^z metres/pixel
⚠️ Vector basemaps typically stop at z14 and overzoom

GNSS ⚠️
Consumer 3–5 m open sky · 10–50 m urban · RTK 1–2 cm
⚠️ 4 satellites minimum (the 4th solves clock error)
Geoid–ellipsoid separation ±100 m

DISTANCE METHODS
Haversine ⚠️ spherical, ~0.5% error · Vincenty ellipsoidal, ~mm, can fail to converge
⚠️ Karney (GeographicLib) — accurate and always converges. Use it

REMOTE SENSING
Landsat 30 m, 16-day · Sentinel-2 10 m, 5-day · SRTM 30 m
```

---

## §18. Books and Tools

| Source | Why |
|---|---|
| **Iliffe & Lott, *Datums and Map Projections*** | ⚠️ **§1 → `gis-coordinate-systems-data-models-and-formats` properly. The book that prevents the expensive bugs** |
| **Snyder, *Map Projections: A Working Manual*** (USGS) | ⚠️ **Free, canonical, has the actual formulas** |
| **Longley et al., *Geographic Information Systems and Science*** | The broad textbook |
| **Obe & Hsu, *PostGIS in Action*** | ⚠️ **§5 → `gis-indexing-databases-tiling-and-rendering`, and genuinely practical** |
| **de Smith, Goodchild & Longley, *Geospatial Analysis*** | ⚠️ **Free online, encyclopaedic on §11 → `gis-spatial-analysis-remote-sensing-and-privacy`** |
| **Brovelli et al. / *Open Source Geospatial* materials** | The FOSS4G ecosystem |
| **Tyner, *Principles of Map Design*** | ⚠️ **Cartography — the part engineers skip and shouldn't** |
| **Tufte / Brewer (ColorBrewer)** | ⚠️ **ColorBrewer for map colour schemes — use it rather than inventing** |

**Tools**: **QGIS** (⚠️ **desktop, free, excellent**), **GDAL/OGR** (⚠️ **the universal
translator; `ogr2ogr` and `gdalwarp` will do most conversions you need**), **PROJ**,
**PostGIS**, **GeoPandas/Shapely/Rasterio/Xarray**, **DuckDB spatial**, **Turf.js**,
**tippecanoe**, **planetiler**, **MapLibre**, **Leaflet**, **OpenLayers**, **deck.gl**,
**OSRM/Valhalla**, **Nominatim/Pelias**, **libpostal**.
**Communities**: **FOSS4G**, **Cloud-Native Geospatial Forum**, **OSM community**,
**GIS StackExchange** (⚠️ **unusually high quality**).

---

## §19. Quick Reference

### 19.1 Picker
| Need | Use |
|---|---|
| Store vector data in a file | ⚠️ **GeoPackage or FlatGeobuf — not Shapefile** (§3 → `gis-coordinate-systems-data-models-and-formats`) |
| Analytics on huge vector data | ⚠️ **GeoParquet + DuckDB** (§3 → `gis-coordinate-systems-data-models-and-formats`, §16.2) |
| Serve a basemap with no server | ⚠️ **PMTiles on object storage** (§6 → `gis-indexing-databases-tiling-and-rendering`, §16.2) |
| Serve imagery | **COG** (§3 → `gis-coordinate-systems-data-models-and-formats`) |
| Spatial queries with attributes | **PostGIS** (§5 → `gis-indexing-databases-tiling-and-rendering`) |
| Global point index in a KV store | **Geohash — ⚠️ handle edges** (§4 → `gis-indexing-databases-tiling-and-rendering`) |
| Neighbourhood/flow analysis | ⚠️ **H3 — equidistant neighbours** (§4 → `gis-indexing-databases-tiling-and-rendering`) |
| Spherical indexing without projection distortion | **S2** (§4 → `gis-indexing-databases-tiling-and-rendering`) |
| Compute area | ⚠️ **Equal-area projection, or `geography`** (§1.3 → `gis-coordinate-systems-data-models-and-formats`, §5 → `gis-indexing-databases-tiling-and-rendering`) |
| Accurate distance between two points | ⚠️ **Karney/GeographicLib** (§17) |
| Web map, vector, open | **MapLibre GL JS** (§7 → `gis-indexing-databases-tiling-and-rendering`) |
| Web map where CRS matters | ⚠️ **OpenLayers** (§7 → `gis-indexing-databases-tiling-and-rendering`) |
| Millions of points on a map | **deck.gl, or tile it** (§7 → `gis-indexing-databases-tiling-and-rendering`) |
| Routing, static costs | **OSRM (CH)** (§8 → `gis-routing-geocoding-and-positioning`) |
| Routing with traffic | ⚠️ **Valhalla (MLD)** (§8 → `gis-routing-geocoding-and-positioning`) |
| Snap GPS traces to roads | ⚠️ **HMM map matching, not nearest-neighbour** (§8 → `gis-routing-geocoding-and-positioning`) |
| Parse international addresses | **libpostal** (§9 → `gis-routing-geocoding-and-positioning`) |
| Convert anything to anything | **`ogr2ogr`** (§18) |

### 19.2 Debugging checklist
- [ ] Do I know the CRS of every input, and do they match? (§1 → `gis-coordinate-systems-data-models-and-formats`)
- [ ] Axis order — is my data in the Gulf of Guinea? (§1.2 → `gis-coordinate-systems-data-models-and-formats`)
- [ ] Am I computing area or distance in Web Mercator? (§1.3 → `gis-coordinate-systems-data-models-and-formats`)
- [ ] Am I buffering in degrees? (§11 → `gis-spatial-analysis-remote-sensing-and-privacy`)
- [ ] Is `ST_Distance` returning suspiciously small numbers? ⚠️ **Degrees** (§5 → `gis-indexing-databases-tiling-and-rendering`)
- [ ] Are my geometries valid? (§2 → `gis-coordinate-systems-data-models-and-formats`)
- [ ] Is the spatial index actually being used — check the query plan (§5 → `gis-indexing-databases-tiling-and-rendering`)
- [ ] Ellipsoidal or geoid height? (§10.3 → `gis-routing-geocoding-and-positioning`)
- [ ] Is that reported accuracy fused or GNSS? (§10.2 → `gis-routing-geocoding-and-positioning`)
- [ ] Have I checked the licence of every data source? (§13 → `gis-spatial-analysis-remote-sensing-and-privacy`)
- [ ] Am I collecting more location precision than the product needs? (§14 → `gis-spatial-analysis-remote-sensing-and-privacy`)

---

## §20. Method

**§1–§12 → `gis-coordinate-systems-data-models-and-formats`, `gis-indexing-databases-tiling-and-rendering`, `gis-routing-geocoding-and-positioning`, `gis-spatial-analysis-remote-sensing-and-privacy`, §14 → `gis-spatial-analysis-remote-sensing-and-privacy`, §15 and §17 rest on settled material** — **geodesy, projection mathematics
(Snyder's USGS manual is still the reference), OGC Simple Features, and standard
algorithms** — plus the references in §18. ⚠️ **Projection math has not changed since
Snyder, and the CRS bugs in §1 → `gis-coordinate-systems-data-models-and-formats` and §15 are the same ones people have made for thirty
years.**

**Two searches were run in August 2026**, on the two things that genuinely moved: **the
open basemap data landscape** and **the cloud-native format stack.**

**Confidence.** **High** in §1–§12 → `gis-coordinate-systems-data-models-and-formats`, `gis-indexing-databases-tiling-and-rendering`, `gis-routing-geocoding-and-positioning`, `gis-spatial-analysis-remote-sensing-and-privacy` and §14 → `gis-spatial-analysis-remote-sensing-and-privacy`. ⚠️ **§1 → `gis-coordinate-systems-data-models-and-formats` and §15 are where I'd put the emphasis
regardless of anything else in this document — the axis-order bug and Web Mercator area
calculation are responsible for an enormous share of real-world geospatial errors, and
both are trivially preventable once named.**

**High** in §16.2, which is well-corroborated across the Cloud-Native Geospatial Forum,
tooling documentation, and multiple independent practitioners. ⚠️ **The one figure I've
flagged is the "90% cost reduction" claim, which is vendor-adjacent — the architectural
claim underneath it (no server process, range reads from object storage) is solid and
uncontroversial.**

⚠️ **§16.1 needs a specific caution and I've built it into the section.** **The factual
core is well attested from Overture's own materials, the Linux Foundation, Esri, and the
OSM wiki**: the membership, the themes, GeoParquet distribution, GERS's purpose, the
2.3 billion buildings, the Bing and ArcGIS integrations, and ⚠️ **the ~40% OSM
derivation, which is the single most important fact for correctly understanding the
relationship.**

⚠️ **The governance dispute I have reported as a dispute rather than resolving it.** **The
$300,000 membership figure and the 20% ID churn claim come from a source explicitly
arguing one side of an OGC standardization fight, and I could not corroborate the churn
number independently.** **I've included it because if it's accurate it directly undermines
GERS's core value proposition and you'd want to check before building on it** — ⚠️ **but
it is a claim to verify, not a fact I'm asserting.** **The existence and shape of the
disagreement is not in doubt.**

**§14 → `gis-spatial-analysis-remote-sensing-and-privacy` I have treated as an engineering obligation rather than a legal footnote.** ⚠️ **The
result that a handful of spatiotemporal points uniquely identifies individuals is
foundational and well-replicated**, and it means **"we anonymized it" is not a defensible
claim for trajectory data without genuine aggregation or formal privacy guarantees.**
