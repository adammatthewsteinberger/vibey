---
name: gis-routing-geocoding-and-positioning
description: "Use when computing paths or resolving positions: routing over road networks including graph construction, cost models, turn restrictions and contraction hierarchies; geocoding and reverse geocoding with their accuracy and ambiguity problems; and GNSS and positioning covering how it works, the real accuracy you get rather than the advertised figure, why altitude is a trap, and the other positioning methods."
---

# Geospatial Software: Routing, Geocoding, and GNSS and Positioning

> **Part 3 of 5** of the *Geospatial Software* reference (plugin `geospatial-software`), covering §8–§10. Sibling skills: `gis-coordinate-systems-data-models-and-formats` (§0–§3), `gis-indexing-databases-tiling-and-rendering` (§4–§7), `gis-spatial-analysis-remote-sensing-and-privacy` (§11–§14), `gis-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    actually ask** (§1.1 → `gis-coordinate-systems-data-models-and-formats`, §10.3).

---

## §8. Routing

**⚠️ Road networks are directed graphs with turn restrictions, and the turn restrictions
are what make naive graph libraries insufficient.**

**Algorithms:**
```
Dijkstra                exact, slow on large graphs
A*                      ⚠️ heuristic-guided; the heuristic must be admissible
                        (never overestimate) or you lose optimality
Contraction Hierarchies ⚠️ heavy preprocessing → millisecond continental queries.
                        The standard for static road networks (OSRM)
Multi-Level Dijkstra    ⚠️ better for dynamic costs — traffic, live updates (Valhalla)
Time-dependent          departure-time-varying edge weights
```
**⚠️ CH's limitation is the important one**: **preprocessing bakes in the cost function, so
changing weights means re-preprocessing.** **That's why traffic-aware systems favour MLD
or customizable CH.**

**Engines**: **OSRM** (⚠️ **fast, CH-based**), **Valhalla** (⚠️ **tiled, dynamic costing,
multimodal**), **GraphHopper**, **pgRouting**, and commercial APIs.

**⚠️ Map matching** — snapping noisy GPS traces to the road network — ⚠️ **is usually a
hidden Markov model over candidate road segments, not nearest-neighbour snapping.**
**Naive snapping fails badly on parallel roads, overpasses and tunnels.**
**Isochrones**, **the travelling salesman and vehicle routing problems** (⚠️ **NP-hard —
use OR-Tools or a heuristic, not an exact solver, beyond trivial sizes**).

---

## §9. Geocoding

**Forward** (address → coordinate) and **reverse** (coordinate → address).
**⚠️ The reason it's hard is that addresses are human artifacts, not a coordinate system**:
inconsistent formats, abbreviations, misspellings, multilingual and transliterated forms,
ambiguous names (⚠️ **there are dozens of Springfields**), buildings without numbers, and
countries where addressing is informal or absent.

**⚠️ Pipeline**: **parse** (⚠️ **libpostal is the standard for international address
parsing and it's genuinely hard to beat**) → **normalize** → **match** (fuzzy, hierarchical)
→ **rank by confidence**.
**Engines**: **Nominatim** (OSM), **Pelias**, **Photon**, commercial APIs.
**⚠️ Quality varies enormously by region**, and ⚠️ **always propagate a confidence score
and match type (rooftop / interpolated / street / city) rather than returning a bare
coordinate — an interpolated street-level match presented as exact is a real source of
downstream error.**

---

## §10. GNSS and Positioning

### 10.1 How it works
**⚠️ Trilateration from satellite signal travel times.** **Four satellites minimum — three
for position, the fourth to solve for receiver clock error**, ⚠️ **which is the part people
miss: the receiver's cheap clock is an unknown, not a given.**
**Constellations**: GPS, GLONASS, Galileo, BeiDou, plus QZSS and NavIC regionally.
⚠️ **Multi-constellation receivers are substantially better in urban environments simply
because more satellites are visible.**

### 10.2 ⚠️ Real accuracy
```
Consumer GNSS, open sky       ⚠️ 3–5 m
Urban canyon                  ⚠️ 10–50 m, sometimes far worse
Indoors                       ⚠️ unusable
SBAS (WAAS/EGNOS)             1–3 m
DGPS                          <1 m
RTK                           ⚠️ 1–2 cm — needs a base station or network
PPP                           cm, after convergence time
```
**⚠️ Error sources**: **ionospheric and tropospheric delay, multipath** (⚠️ **signals
bouncing off buildings — the dominant urban error and the reason accuracy degrades in
exactly the places with the most users**), **satellite geometry (DOP)**, ephemeris and
clock errors.

> **⚠️ GOTCHA — the accuracy number your phone reports is a radius of confidence, not a
> guarantee, and it is frequently optimistic.** ⚠️ **Phones fuse GNSS with WiFi
> positioning, cell towers, and inertial sensors, so the reported figure is a fused
> estimate whose provenance you cannot see.** **Never treat a reported accuracy as
> ground truth, and never assume a position is GNSS-derived just because it's precise.**

### 10.3 ⚠️ Altitude is a trap
**GNSS reports height above the ELLIPSOID; maps and people use height above the GEOID
(mean sea level).** ⚠️ **The difference — geoid undulation — ranges roughly ±100 m
globally.**
**⚠️ Converting requires a geoid model (EGM96, EGM2008).** **Reporting raw GNSS altitude as
"elevation" is simply wrong, and it's a common bug in fitness and aviation-adjacent
software.**

### 10.4 Other positioning
**WiFi** (⚠️ **RSSI fingerprinting against a database of access points — this is what
actually locates you indoors, and it's how phones get a fix so fast**), **cell tower**,
**Bluetooth beacons**, **UWB** (⚠️ **10–30 cm, and the basis of precise indoor
positioning**), **inertial dead reckoning** (⚠️ **drifts, so it's a bridge between fixes,
not a positioning system**), and **visual/SLAM** (see a computer-vision reference).
