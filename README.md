# HKUST Navigate API — Unofficial Documentation

> **Disclaimer:** This is an unofficial, community-contributed documentation of the publicly accessible HKUST Navigate API. It is not affiliated with, endorsed by, or officially supported by the Hong Kong University of Science and Technology (HKUST). Use responsibly and respect the university's systems.

---

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Data Hierarchy](#data-hierarchy)
- [Endpoints](#endpoints)
  - [1. Buildings](#1-buildings)
  - [2. Building Floors](#2-building-floors)
  - [3. Floor GeoJSON](#3-floor-geojson)
  - [4. Nav Nodes](#4-nav-nodes)
- [Field Reference](#field-reference)
- [Known Buildings](#known-buildings)
- [Python Examples](#python-examples)
- [Sample Crawlers](#sample-crawlers)
- [Notes & Limitations](#notes--limitations)

---

## Overview

The [HKUST Navigate](https://navigate.ust.hk) system provides an indoor wayfinding service for the HKUST campus. Its underlying REST API exposes structured data about buildings, floors, room layouts (as GeoJSON), and navigation nodes (points of interest, rooms, staircases, lifts, etc.).

This repository documents the discovered API endpoints and provides Python scripts to extract and work with the data.

---

## Base URL

```
https://navigate.ust.hk/path/api/app
```

All endpoints below are relative to this base URL. No authentication is required for read access.

### Recommended Request Headers

```http
User-Agent: Mozilla/5.0 (compatible)
Accept: application/json
Referer: https://navigate.ust.hk/
Origin: https://navigate.ust.hk
```

### Response Envelope

All responses follow the same envelope format:

```json
{
  "meta": {
    "code": 200,
    "message": "Success"
  },
  "data": { ... }
}
```

| `meta.code` | Meaning |
|-------------|---------|
| `200` | Success |
| `404` | Route does not exist |
| `4034` | Schema validation error (missing required parameter) |

---

## Data Hierarchy

```
Buildings
    │
    └── Building Floors
              │
              ├── Floor GeoJSON      (room polygons & geometry)
              └── Nav Nodes          (named points: rooms, toilets, lifts, canteens, etc.)
```

Each level uses an `_id` field that is passed as a parameter to the next level.

---

## Endpoints

### 1. Buildings

Returns a list of all campus buildings.

```
GET /buildings?page={page}&limit={limit}
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (pagination) |
| `limit` | integer | `20` | Max results per page |

#### Example Request

```
GET https://navigate.ust.hk/path/api/app/buildings?page=1&limit=20
```

#### Example Response

```json
{
  "meta": { "code": 200, "message": "Success" },
  "data": {
    "total": 20,
    "count": 6,
    "buildings": [
      {
        "_id": "b00000000000000000000001",
        "image_asset_ids": [],
        "full_name": "Academic Building",
        "description": ""
      }
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `_id` | string | Unique building ID — used in subsequent requests |
| `full_name` | string | Display name of the building |
| `description` | string | Optional description |
| `image_asset_ids` | array | Associated image asset IDs (may be empty) |

> ⚠️ **Note:** The `total` field in the response may be inaccurate (e.g. returns `20` when only `6` buildings exist). Always stop paginating when an empty `buildings` array is returned.

---

### 2. Building Floors

Returns all floors for a given building.

```
GET /locations/building-floors?building_id={building_id}&limit={limit}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_id` | string | ✅ | The `_id` from the Buildings endpoint |
| `limit` | integer | | Max number of floors to return (default: `20`, recommend `50`) |

#### Example Request

```
GET https://navigate.ust.hk/path/api/app/locations/building-floors?building_id=b00000000000000000000001&limit=50
```

#### Example Response

```json
{
  "meta": { "code": 200, "message": "Success" },
  "data": {
    "total": 15,
    "count": 15,
    "location_building_floors": [
      {
        "_id": "bf0000000000000000000107",
        "name": "G",
        "elevation": "0",
        "is_default": true,
        "show_in_path_advisor": true
      },
      {
        "_id": "bf0000000000000000000108",
        "name": "1",
        "elevation": "1",
        "is_default": false,
        "show_in_path_advisor": true
      }
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `_id` | string | Unique floor ID — used in GeoJSON and Nav Node requests |
| `name` | string | Floor label (e.g. `G`, `1`, `LG1`, `UG`, `R`) |
| `elevation` | string | Numeric elevation relative to ground (`"0"` = ground, `"-1"` = LG1, etc.) |
| `is_default` | boolean | Whether this is the default floor shown when the building is opened |
| `show_in_path_advisor` | boolean | Whether this floor appears in the path advisor UI |

---

### 3. Floor GeoJSON

Returns the floor plan as a **GeoJSON FeatureCollection**, including the geometry (polygons) and properties of each space (room, corridor, staircase, etc.).

```
GET /building-floors/geojson?building_floor_id={floor_id}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_floor_id` | string | ✅ | The `_id` from the Building Floors endpoint |

#### Example Request

```
GET https://navigate.ust.hk/path/api/app/building-floors/geojson?building_floor_id=bf000000000000000000010d
```

#### Response Structure

```
response
  └── data
        └── building_floor
                  └── geojson              ← Standard GeoJSON FeatureCollection
                        └── features[]     ← One feature per room/space
```

> ⚠️ **Important:** The GeoJSON is **nested** inside `data.building_floor.geojson`, not at the root level.

#### Example Feature

```json
{
  "id": 2,
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [114.26354289, 22.33769094, 147.925],
        [114.26358512, 22.33770514, 147.925],
        ...
      ]
    ]
  },
  "properties": {
    "location_id": "685cef8707973ca98d52c986",
    "location_name": "6SC06",
    "hidden_from_map": false,
    "type_id": "10000000000000000000003a",
    "type_name": "Staircase",
    "type_color_hex": "93CEFF",
    "point_of_interest_id": null,
    "point_of_interest_type_id": null
  }
}
```

#### Feature Properties

| Field | Type | Description |
|-------|------|-------------|
| `location_id` | string | Links to the corresponding nav node's `location_id` |
| `location_name` | string | Room/space label (e.g. `6SC06`, `LT-A`) — may be empty |
| `hidden_from_map` | boolean | Whether this feature is hidden in the UI |
| `type_id` | string | Internal type identifier (see [Known Type IDs](#known-type-ids)) |
| `type_name` | string | Human-readable type (e.g. `Staircase`, `Classroom`) |
| `type_color_hex` | string | Hex colour used to render this space on the map |
| `point_of_interest_id` | string\|null | Set if this space is also a POI |
| `point_of_interest_type_id` | string\|null | Type of the POI |

#### Geometry

Coordinates are in **WGS84 (longitude, latitude, elevation)** format. Elevation is in metres above sea level.

The centroid of a polygon can be computed as:

```python
ring = polygon["coordinates"][0]
longitude = sum(p[0] for p in ring) / len(ring)
latitude  = sum(p[1] for p in ring) / len(ring)
```

---

### 4. Nav Nodes

Returns named navigation points for a floor — these are the **labelled, searchable locations** such as rooms, toilets, staircases, canteens, ATMs, and other points of interest.

```
GET /building-floors/nav-nodes?building_floor_id={floor_id}&limit={limit}&page={page}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_floor_id` | string | ✅ | The `_id` from the Building Floors endpoint |
| `limit` | integer | | Max nodes per page (recommend `500`) |
| `page` | integer | | Page number for pagination |

#### Example Request

```
GET https://navigate.ust.hk/path/api/app/building-floors/nav-nodes?building_floor_id=bf0000000000000000000107&limit=500
```

#### Example Response

```json
{
  "meta": { "code": 200, "message": "Success" },
  "data": {
    "total": 82,
    "nav_nodes": [
      {
        "_id": "68823bfbc1ff19b610e5f20b",
        "name": "G31T",
        "remote_id": "USTG31T",
        "building_floor_id": "bf0000000000000000000107",
        "longitude": "114.26389603458340",
        "latitude": "22.33818599400004",
        "location_id": "6858defff5e020372bc3d405",
        "point_of_interest_id": null,
        "type_name": "Toilet(Male)",
        "type_display_setting": "show_icon",
        "icon": { "file_content": "data:image/png;base64,..." }
      }
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `_id` | string | Unique nav node ID |
| `name` | string | Display name of the location |
| `remote_id` | string | Short code used in the path advisor (e.g. `USTG31T`, `USTGSC01`) |
| `building_floor_id` | string | The floor this node belongs to |
| `longitude` | string | Longitude as a string — convert to float before use |
| `latitude` | string | Latitude as a string — convert to float before use |
| `location_id` | string\|null | Links to GeoJSON feature's `location_id` |
| `point_of_interest_id` | string\|null | Set if this node is a POI (e.g. ATM, shop) |
| `type_name` | string | Human-readable location type |
| `type_display_setting` | string | How the label is shown on the map (see below) |
| `icon` | object\|null | Contains `file_content` as a base64-encoded PNG |

#### `type_display_setting` Values

| Value | Description |
|-------|-------------|
| `show_location_name` | Shows only the room name label |
| `show_icon` | Shows only the type icon |
| `show_location_name_and_icon` | Shows both name and icon |
| `hidden` | Not shown on the map |

> ⚠️ **Note:** `longitude` and `latitude` are returned as **strings**, not numbers. Cast them with `float()` before any calculation.

> ⚠️ **Note:** The `icon.file_content` field contains a full base64-encoded PNG and can be very large. Strip it out if you only need location metadata.

---

## Field Reference

### Known Type IDs

Discovered from the GeoJSON `type_id` field. This list is partial.

| `type_id` | `type_name` |
|-----------|------------|
| `10000000000000000000003a` | Staircase |
| `100000000000000000000041` | *(run the crawler to discover)* |
| `100000000000000000000040` | *(run the crawler to discover)* |
| `10000000000000000000003f` | *(run the crawler to discover)* |
| `100000000000000000000026` | *(hidden/unlabelled space)* |

To discover all type IDs and names, run the GeoJSON crawler and inspect the `type_id` + `type_name` columns in the output CSV.

---

## Known Buildings

| `_id` | Building Name |
|-------|--------------|
| `b00000000000000000000001` | Academic Building |
| `b00000000000000000000002` | Cheng Yu Tung Building |
| `b00000000000000000000003` | Shaw Auditorium |
| `b00000000000000000000004` | Lee Shau Kee Business Building |
| `b00000000000000000000005` | HKUST Jockey Club Institute for Advanced Study / Lo Ka Chung Building |
| `69201b741c838d03d9fbe71b` | Martin Ka Shing Lee Innovation Building |

> The API reports `total: 20` buildings, but only 6 are currently returned. The remaining entries may be restricted or not yet published.

---

## Python Examples

### Install dependency

```bash
pip install requests
```

### Get all buildings

```python
import requests

BASE_URL = "https://navigate.ust.hk/path/api/app"
HEADERS  = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://navigate.ust.hk/",
}

resp = requests.get(f"{BASE_URL}/buildings", params={"limit": 100}, headers=HEADERS)
buildings = resp.json()["data"]["buildings"]

for b in buildings:
    print(b["_id"], b["full_name"])
```

### Get floors for a building

```python
resp = requests.get(
    f"{BASE_URL}/locations/building-floors",
    params={"building_id": "b00000000000000000000001", "limit": 50},
    headers=HEADERS
)
floors = resp.json()["data"]["location_building_floors"]

for f in floors:
    print(f["_id"], f["name"], f["elevation"])
```

### Get GeoJSON for a floor

```python
resp = requests.get(
    f"{BASE_URL}/building-floors/geojson",
    params={"building_floor_id": "bf000000000000000000010d"},
    headers=HEADERS
)

# NOTE: nested path
features = resp.json()["data"]["building_floor"]["geojson"]["features"]

for feature in features:
    props = feature["properties"]
    print(props["location_name"], props["type_name"], props["hidden_from_map"])
```

### Get nav nodes for a floor

```python
resp = requests.get(
    f"{BASE_URL}/building-floors/nav-nodes",
    params={"building_floor_id": "bf0000000000000000000107", "limit": 500},
    headers=HEADERS
)
nodes = resp.json()["data"]["nav_nodes"]

for node in nodes:
    print(
        node["remote_id"],
        node["name"],
        node["type_name"],
        float(node["longitude"]),
        float(node["latitude"]),
    )
```

---

## Sample Crawlers

`hkust_navigate_filter_by_type.py` crawls the available buildings and floors, fetches floor GeoJSON, and writes matching locations for the configured type IDs to `hkust_filtered_locations.csv`.

Run it after installing the dependency:

```bash
pip install requests
python hkust_navigate_filter_by_type.py
```

The script includes a `0.3` second delay between requests. Use it responsibly and avoid unnecessary repeated crawls.

---

## Notes & Limitations

- **No official documentation** — This was reverse-engineered by inspecting network requests from the HKUST Navigate web application.
- **No authentication required** — All documented endpoints are publicly accessible without tokens or cookies.
- **Rate limiting** — No rate limits were observed during testing, but please be courteous: add a small delay (e.g. `0.3s`) between requests.
- **`longitude` / `latitude` are strings** in the Nav Nodes API — always cast with `float()`.
- **GeoJSON path is nested** — The features array is at `data.building_floor.geojson.features`, not at the root.
- **`total` field may be wrong** — The Buildings endpoint reports `total: 20` but only 6 buildings are returned. Stop paginating when an empty list is returned instead of relying on `total`.
- **Icons are large** — The `icon.file_content` in nav nodes is a base64-encoded PNG that can be several kilobytes. Strip it from your data if not needed.
- **Undiscovered endpoints** — The `/locations` endpoint requires a `search` query parameter and may support full-text search. Further exploration is welcome.

---

## Contributing

Found a new endpoint? Discovered what the remaining type IDs mean? Contributions and corrections are welcome — please open an issue or submit a pull request.

---

## License

This documentation and the accompanying scripts are released under the [MIT License](LICENSE). The underlying API and map data belong to HKUST.
