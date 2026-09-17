# HKUST Navigate API

Unofficial, community-contributed documentation for the publicly accessible HKUST Navigate API.

This documentation is not affiliated with, endorsed by, or officially supported by the Hong Kong University of Science and Technology (HKUST). Use responsibly and respect the university's systems.

## Overview

The [HKUST Navigate](https://navigate.ust.hk) system provides indoor wayfinding for the HKUST campus. Its underlying REST API exposes structured data about buildings, floors, room layouts as GeoJSON, and navigation nodes such as rooms, staircases, lifts, and points of interest.

## Base URL

```text
https://navigate.ust.hk/path/api/app
```

No authentication is required for the documented read-only endpoints.

## Endpoints

### Buildings

```text
GET /buildings?page={page}&limit={limit}
```

Returns campus buildings. Pagination should stop when an empty `buildings` array is returned because the API's `total` field may be inaccurate.

### Building Floors

```text
GET /locations/building-floors?building_id={building_id}&limit={limit}
```

Returns the floors for a building. The building ID comes from the Buildings endpoint.

### Floor GeoJSON

```text
GET /building-floors/geojson?building_floor_id={floor_id}
```

Returns a GeoJSON `FeatureCollection` nested at `data.building_floor.geojson`.

### Navigation Nodes

```text
GET /building-floors/nav-nodes?building_floor_id={floor_id}&limit={limit}&page={page}
```

Returns labelled navigation points such as rooms, toilets, staircases, lifts, canteens, and other points of interest.

## Response Notes

- Responses use a `meta` and `data` envelope.
- GeoJSON coordinates use WGS84 longitude, latitude, and elevation.
- Navigation-node `longitude` and `latitude` values are returned as strings and should be converted to numbers before calculations.
- Navigation-node icons may contain large base64-encoded PNG data. Strip the `icon.file_content` field when only metadata is needed.
- Add a small delay between requests, such as `0.3` seconds, and avoid unnecessary crawling.

## Responsible Use

- Use only the publicly accessible, read-only endpoints documented here.
- Respect the service and keep request rates low.
- Do not attempt to bypass authentication, access controls, or restrictions.
- Do not publish private data, credentials, cookies, or other secrets.
- Re-check the live service and official policies before relying on these endpoints.

## License

This documentation is released under the [MIT License](LICENSE). The underlying API and map data belong to HKUST.
