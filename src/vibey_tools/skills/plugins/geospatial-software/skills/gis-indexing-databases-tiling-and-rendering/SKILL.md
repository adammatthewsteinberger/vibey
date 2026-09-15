---
name: gis-indexing-databases-tiling-and-rendering
description: "Use when storing, querying, or drawing spatial data at scale: spatial indexing with R-trees, quadtrees and geohashes and their query characteristics, spatial databases including PostGIS and the operations worth knowing, tiling schemes and vector versus raster tiles, and rendering including styling, generalization and label placement."
---

# Geospatial Software: Spatial Indexing, Spatial Databases, Tiling, and Rendering

> **Part 2 of 5** of the *Geospatial Software* reference (plugin `geospatial-software`), covering §4–§7. Sibling skills: `gis-coordinate-systems-data-models-and-formats` (§0–§3), `gis-routing-geocoding-and-positioning` (§8–§10), `gis-spatial-analysis-remote-sensing-and-privacy` (§11–§14), `gis-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Spatial Indexing

**⚠️ Spatial queries without an index are table scans, and the whole field exists to avoid
that.**
```
R-tree            ⚠️ hierarchical bounding boxes; THE standard for vector data
                  (PostGIS GiST, SQLite, GeoPackage)
Quadtree          recursive quadrant subdivision; rasters, tiles
k-d tree          point data, nearest-neighbour
Grid / geohash    ⚠️ base32 string; PREFIX = containment, which makes it work in
                  any plain key-value store
S2 (Google)       ⚠️ sphere → cube → Hilbert curve. No projection distortion; excellent
                  for global spherical work
H3 (Uber)         ⚠️ HEXAGONAL global grid. Uniform neighbour distance — better for
                  flow, aggregation and movement analysis
```
> **⚠️ GOTCHA — geohash has an edge problem people trip over.** ⚠️ **Two points a metre
> apart can have completely different prefixes if they straddle a cell boundary.**
> **Proximity search must check neighbouring cells, not just the shared prefix.** **S2 and
> H3 handle adjacency explicitly and are better for anything doing neighbourhood
> queries.**
>
> ⚠️ **And hexagons aren't a gimmick**: **a hexagon's six neighbours are all equidistant
> from its centre; a square's eight are not.** **That matters for anything modelling
> spread, flow or movement.** **The trade is that hexagons don't subdivide perfectly, so
> H3's hierarchy is approximate.**

**⚠️ The two-phase query pattern** underlies essentially all spatial querying: **filter by
bounding box using the index (cheap), then refine with exact geometry (expensive).**
**Getting this wrong — doing exact tests first — is a common performance bug.**

---

## §5. Spatial Databases

**PostGIS** is the reference implementation and the default choice.
```sql
-- ⚠️ Always index, always use && or ST_DWithin to hit it
CREATE INDEX idx ON t USING GIST (geom);

ST_Intersects, ST_Contains, ST_Within, ST_DWithin   -- ⚠️ these use the index
ST_Distance, ST_Area, ST_Length, ST_Buffer
ST_Transform(geom, 3857)     -- ⚠️ reproject
ST_MakeValid(geom)           -- §2
```
> **⚠️ GOTCHA — `geometry` vs `geography` is the type decision that matters.**
> ⚠️ **`geometry` is planar and fast; distances and areas are in the CRS's units, so
> using it with EPSG:4326 gives you answers in DEGREES, which are meaningless as
> distance.** **`geography` computes on the spheroid and returns metres, correctly, and is
> slower with fewer functions.**
> **⚠️ The pragmatic pattern: store `geometry` in a suitable projected CRS, or use
> `geography` for global data where correctness beats speed, and cast where needed.**
> **`ST_Distance` on 4326 geometry returning "0.0043" is the classic symptom.**

**⚠️ `ST_DWithin` beats `ST_Distance(...) < x`** — the former uses the index, the latter
computes distance for every row first.
**Others**: **SpatiaLite**, **DuckDB spatial** (⚠️ **increasingly the analytics choice, and
it reads GeoParquet directly**), **BigQuery GIS**, **Snowflake**, **Elasticsearch geo**,
**MongoDB 2dsphere**, **Apache Sedona** for distributed work.

---

## §6. Tiling

**⚠️ Serve maps as small pre-cut squares, not one giant image.**
**Slippy map scheme**: `z/x/y`, ⚠️ **doubling resolution per zoom level, in Web Mercator
(§1.3 → `gis-coordinate-systems-data-models-and-formats`).** **Zoom 0 is one 256×256 tile of the world; zoom `z` has `4^z` tiles.**
**⚠️ TMS flips the Y axis relative to XYZ/Google convention — a small, recurring source of
upside-down maps.**

**Raster vs vector tiles:**
- **Raster** — pre-rendered images. ⚠️ **Simple; styling is baked in, so restyling means
  re-rendering everything.**
- **Vector (MVT)** — ⚠️ **geometry plus attributes, styled on the client.** **Restyle
  instantly, rotate and tilt, high-DPI for free, smaller.** **The default for new work.**

**⚠️ Generation**: **tippecanoe** (⚠️ **the standard tool; it adaptively simplifies and
drops features per zoom to keep tiles small — that behaviour is a feature and it will
surprise you if you don't expect dropped features at low zoom**), **planetiler** for
planet-scale, **Martin** and **tegola** for dynamic serving from PostGIS.
**⚠️ Overzooming** lets you serve zoom 14 tiles up to zoom 20 by scaling client-side —
**which is why most vector basemaps stop generating at 14.**

---

## §7. Rendering

| Library | ⚠️ Character |
|---|---|
| **MapLibre GL JS** | ⚠️ **The open fork of Mapbox GL JS. WebGL vector rendering; the default for new open work** |
| **Leaflet** | ⚠️ **Simple, tiny, huge plugin ecosystem. Raster-first** |
| **OpenLayers** | ⚠️ **Most feature-complete; handles projections properly — the pick when CRS matters** |
| **deck.gl** | ⚠️ **Large-scale data visualization; GPU layers** |
| **Cesium** | 3D globe, terrain, time |
| **Mapbox GL JS** | Proprietary since v2 |
| **QGIS** | ⚠️ **Desktop GIS; free, excellent, and the tool for actually looking at your data** |

**⚠️ Style specification** (MapLibre/Mapbox style JSON) — declarative layers, sources,
paint and layout properties, **data-driven styling and expressions.** ⚠️ **This is the
piece that makes vector tiles worth it: the same tiles support unlimited cartography.**

**⚠️ Performance**: **simplify by zoom, cluster points, use the GPU rather than DOM,
avoid re-creating sources, and watch that "just add a GeoJSON layer" with 100k features
will destroy your frame rate.** **Put it in a tile pipeline instead.**
