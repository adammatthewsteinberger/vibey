---
name: gis-coordinate-systems-data-models-and-formats
description: "Use before writing any code that touches coordinates: the layered model of datums, ellipsoids and coordinate reference systems, the axis-order problem that silently swaps latitude and longitude, projections and what each one distorts, the vector and raster data models, and the file formats and their trade-offs. Includes the router for the whole geospatial-software reference."
---

# Geospatial Software: Coordinate Systems, Data Models, and File Formats

> **Part 1 of 5** of the *Geospatial Software* reference (plugin `geospatial-software`), covering §0–§3. Sibling skills: `gis-indexing-databases-tiling-and-rendering` (§4–§7), `gis-routing-geocoding-and-positioning` (§8–§10), `gis-spatial-analysis-remote-sensing-and-privacy` (§11–§14), `gis-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Geodesy and projection mathematics are settled. Two areas moved. See §16 → `gis-reference` for the open basemap landscape and the cloud-native format stack.

> **Scope.** ⚠️ **§1 is the most important section and the one most often skipped.**
> Almost every serious geospatial bug is a coordinate reference system problem wearing a
> different hat.
>
> **⚠️ GOTCHA** boxes mark the errors that silently produce wrong answers — and this
> domain specializes in bugs that look plausible.
>
> **The three ideas that prevent most disasters:**
> 1. **⚠️ A coordinate is meaningless without its CRS.** "40.7128, −74.0060" is not a
>    location until you say which datum and which axis order. **Data with an unknown CRS
>    is not data** (§1).
> 2. **⚠️ Every flat map lies.** Projection to a plane necessarily distorts area, angle,
>    distance, or shape — you choose which. **Web Mercator, the default of the entire web,
>    is unsuitable for area calculation and most analysis** (§1.3).
> 3. **⚠️ The Earth is not a sphere, and for many purposes not even an ellipsoid.**
>    Haversine on a sphere is off by up to ~0.5%; the geoid differs from the ellipsoid by
>    ±100 m vertically. **Whether that matters is a requirements question you must
>    actually ask** (§1.1, §10.3 → `gis-routing-geocoding-and-positioning`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Coordinate systems and projections** | **§1** |
| Data models | §2 |
| **File formats** | **§3** |
| **Spatial indexing** | **§4 → `gis-indexing-databases-tiling-and-rendering`** |
| Spatial databases | §5 → `gis-indexing-databases-tiling-and-rendering` |
| **Tiling** | **§6 → `gis-indexing-databases-tiling-and-rendering`** |
| Rendering libraries | §7 → `gis-indexing-databases-tiling-and-rendering` |
| **Routing** | **§8 → `gis-routing-geocoding-and-positioning`** |
| Geocoding | §9 → `gis-routing-geocoding-and-positioning` |
| **GNSS and positioning** | **§10 → `gis-routing-geocoding-and-positioning`** |
| Spatial analysis | §11 → `gis-spatial-analysis-remote-sensing-and-privacy` |
| Remote sensing | §12 → `gis-spatial-analysis-remote-sensing-and-privacy` |
| Data sources | §13 → `gis-spatial-analysis-remote-sensing-and-privacy` |
| **Privacy** | **§14 → `gis-spatial-analysis-remote-sensing-and-privacy`** |
| Misconceptions | §15 → `gis-reference` |
| **What moved** | **§16 → `gis-reference`** |
| Numbers | §17 → `gis-reference` |
| Books and tools | §18 → `gis-reference` |
| Quick reference | §19 → `gis-reference` |

---

## §1. Coordinate Systems — Read This First

### 1.1 The layered model
```
GEOID       ⚠️ the actual equipotential surface — lumpy, ±100 m from the ellipsoid
ELLIPSOID   a smooth mathematical approximation (e.g. GRS80, WGS84)
DATUM       ⚠️ an ellipsoid ANCHORED to the Earth — this is what makes coordinates mean
            something physical
CRS         datum + coordinate system (geographic lat/lon, or projected x/y)
```
**⚠️ Geographic CRS** — angular latitude/longitude on an ellipsoid. **Projected CRS** —
planar metres, produced by a projection.

**⚠️ Datums differ, and the differences are large enough to matter:**
- **WGS84** — the GPS datum, global.
- **NAD83** — North American; ⚠️ **differs from WGS84 by roughly 1–2 metres and growing.**
- **ETRS89** — European, ⚠️ **fixed to the Eurasian plate, so it diverges from WGS84 at
  plate-motion rates (~2.5 cm/year).**
- **GDA2020** — Australian; ⚠️ **Australia moves ~7 cm/year, which is why the datum was
  re-realized at all.**
> **⚠️ GOTCHA — datums drift because continents move.** ⚠️ **A coordinate captured in 1994
> and one captured today in a plate-fixed datum describe different physical points even
> with identical numbers.** **For centimetre work you need an *epoch*, not just a datum.**
> **This is why modern datums carry a year in the name.**

**EPSG codes** identify CRSs: **4326** (WGS84 lat/lon), **3857** (Web Mercator),
**UTM zones 32601–32660 N / 32701–32760 S**, **4269** (NAD83).

### 1.2 ⚠️ The axis order problem
> **⚠️ GOTCHA — this causes more geospatial bugs than any other single issue.**
> ⚠️ **EPSG:4326 is formally defined as (latitude, longitude). GeoJSON, most web APIs, and
> most JavaScript libraries use (longitude, latitude).** **PostGIS uses (x, y) = (lon,
> lat).** **Some WMS versions swapped between 1.1.1 and 1.3.0.**
>
> **⚠️ The symptom is diagnostic: your data appears off the coast of West Africa** —
> near (0,0) in the Gulf of Guinea — **or lands in the wrong hemisphere.** **Whenever
> anything looks like that, check axis order first.**
>
> **The defence**: name your variables `lon`/`lat`, never `x`/`y`; **assert plausible
> ranges (`|lat| ≤ 90`) at every boundary**; and ⚠️ **note that latitudes above 90 are
> impossible while longitudes above 90 are fine, which is what makes the assertion
> asymmetric and useful.**

### 1.3 Projections
**⚠️ Every projection distorts; you choose what to preserve.**
```
CONFORMAL      preserves ANGLES locally  ⚠️ distorts area
               Mercator, Web Mercator, Lambert Conformal Conic, UTM
EQUAL-AREA     preserves AREA            ⚠️ distorts shape
               Albers, Mollweide, Equal Earth
EQUIDISTANT    preserves distance from a point or along lines
COMPROMISE     Robinson, Winkel Tripel — ⚠️ preserves nothing exactly, looks reasonable
```
**⚠️ Web Mercator (EPSG:3857) deserves specific warnings**, because it's the default of the
entire web:
- **Massive area distortion toward the poles** — ⚠️ **Greenland appears comparable to
  Africa and is about 14× smaller.**
- **⚠️ It uses a SPHERICAL model with ellipsoidal coordinates, which is mathematically
  inconsistent** and is why it has no proper EPSG standing for surveying.
- **Clipped around ±85.05°** to keep the map square.
- ⚠️ **NEVER compute areas or distances in Web Mercator.** **Reproject to an equal-area or
  local projection first.** **This is a common and silent source of wrong analysis.**

**Choosing**: ⚠️ **local/national grid for national work; UTM for regional metric work
(6° zones — and beware working across a zone boundary); equal-area for any statistic
involving area; Web Mercator for display only.**

**⚠️ PROJ is the library that does this** (via GDAL, PostGIS, and nearly everything else).
**Datum transformations need grid shift files for accuracy** — ⚠️ **and a missing grid
silently falls back to a lower-accuracy method rather than erroring, which is exactly the
kind of failure you don't notice.**

---

## §2. Data Models

**Vector** — points, lines, polygons with attributes. ⚠️ **Discrete features with sharp
boundaries.**
**Raster** — a grid of cells. ⚠️ **Continuous phenomena: elevation, imagery, temperature.**
**⚠️ The choice is about the phenomenon, not preference**: a road is a line; elevation is a
surface. **Forcing one into the other is where bad models start.**

**Geometry types (OGC Simple Features)**: Point, LineString, Polygon, and the Multi-
variants, GeometryCollection. **Polygons have an exterior ring and optional interior rings
(holes)**, ⚠️ **with ring winding order conventions that differ between specifications —
and GeoJSON's right-hand rule is widely violated in the wild.**

**⚠️ Validity is a real and under-checked property**: self-intersections, unclosed rings,
duplicate points, holes outside their shell. ⚠️ **Invalid geometry causes downstream
operations to fail or, worse, to silently return nonsense.** **`ST_IsValid` /
`ST_MakeValid` in PostGIS; check on ingest, not on error.**

**Topology** — ⚠️ **shared boundaries between adjacent polygons.** **Storing them
independently means they drift apart under editing, producing slivers and gaps.**
**Topological models store the shared edge once.**

---

## §3. File Formats

| Format | Type | ⚠️ Notes |
|---|---|---|
| **GeoJSON** | Vector, text | ⚠️ **Simple and universal; WGS84 only by spec; verbose; no index** |
| **Shapefile** | Vector | ⚠️ **Ancient, multi-file, 2 GB limit, 10-char field names, no UTF-8 guarantee. Still everywhere. Avoid for new work** |
| **GeoPackage** | Vector + raster | ⚠️ **SQLite-based; the right modern replacement for Shapefile** |
| **FlatGeobuf** | Vector, binary | ⚠️ **Streamable, spatially indexed, HTTP-range readable** |
| **GeoParquet** | Vector, columnar | ⚠️ **Cloud-native analytics; the §16 → `gis-reference` format** |
| **PMTiles** | Tiles, single file | ⚠️ **Serverless tile pyramid via range requests** |
| **GeoTIFF / COG** | Raster | ⚠️ **COG adds internal tiling + overviews for partial reads** |
| **Zarr** | N-d arrays | Multidimensional cubes; climate and time series |
| **COPC** | Point cloud | Cloud-optimized LAZ |
| **KML** | Vector | Google-origin; display-oriented |
| **WKT / WKB** | Geometry encoding | ⚠️ **WKT is text, WKB binary; the database interchange pair** |
| **MVT** | Vector tile | ⚠️ **Protobuf; the web vector tile standard** |

**⚠️ The rule for choosing**: **GeoPackage or FlatGeobuf for files, GeoParquet for
analytics at scale, PMTiles for serving map tiles, COG for imagery, GeoJSON only for small
data and interchange.** ⚠️ **Shapefile only when something old demands it — and its
limitations will bite you eventually.**
