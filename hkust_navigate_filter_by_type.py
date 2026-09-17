"""
HKUST Navigate API - Filter Locations by Type ID
==================================================
Crawls all buildings & floors and extracts only locations
matching the specified type_ids.

Target type IDs:
  - 100000000000000000000041
  - 100000000000000000000040
  - 10000000000000000000003f
"""

import requests
import csv
import time
from collections import defaultdict

BASE_URL   = "https://navigate.ust.hk/path/api/app"
OUTPUT_CSV = "hkust_filtered_locations.csv"
SLEEP_SEC  = 0.3

TARGET_TYPE_IDS = {
    "100000000000000000000041",
    "100000000000000000000040",
    "10000000000000000000003f",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Referer":    "https://navigate.ust.hk/",
    "Origin":     "https://navigate.ust.hk",
}


def get(url, **params):
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"    [ERROR] {url} -> {e}")
        return None


def get_all_buildings():
    buildings = []
    page = 1
    while True:
        data = get(f"{BASE_URL}/buildings", page=page, limit=100)
        if not data or data.get("meta", {}).get("code") != 200:
            break
        batch = data["data"].get("buildings", [])
        if not batch:
            break
        buildings.extend(batch)
        page += 1
        time.sleep(SLEEP_SEC)
    return buildings


def get_floors(building_id):
    data = get(
        f"{BASE_URL}/locations/building-floors",
        building_id=building_id,
        limit=50
    )
    if not data or data.get("meta", {}).get("code") != 200:
        return []
    return data["data"].get("location_building_floors", [])


def get_geojson_features(floor_id):
    data = get(
        f"{BASE_URL}/building-floors/geojson",
        building_floor_id=floor_id
    )
    if not data or data.get("meta", {}).get("code") != 200:
        return []
    try:
        features = data["data"]["building_floor"]["geojson"]["features"]
        return features if isinstance(features, list) else []
    except (KeyError, TypeError):
        return []


def get_centroid(geometry):
    """Return (longitude, latitude) centroid, or ('', '')."""
    try:
        gtype  = geometry.get("type", "")
        coords = geometry.get("coordinates", [])

        if gtype == "Point":
            return coords[0], coords[1]

        if gtype == "Polygon":
            ring = coords[0]
            lngs = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            return sum(lngs) / len(lngs), sum(lats) / len(lats)

        if gtype == "MultiPolygon":
            ring = coords[0][0]
            lngs = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            return sum(lngs) / len(lngs), sum(lats) / len(lats)

    except (IndexError, TypeError, ZeroDivisionError):
        pass

    return "", ""


def main():
    matched_rows = []
    stats = defaultdict(int)

    print("=" * 60)
    print("  HKUST Navigate - Filter by Type ID")
    print("=" * 60)
    print("\n  Target type IDs:")
    for type_id in sorted(TARGET_TYPE_IDS):
        print(f"    - {type_id}")

    print("\n[1] Fetching buildings...")
    buildings = get_all_buildings()
    print(f"    Found: {len(buildings)} buildings")

    print("\n[2] Scanning all floors...\n")

    for building in buildings:
        bid   = building["_id"]
        bname = building.get("full_name", bid)

        print(f"▶ {bname}")
        floors = get_floors(bid)

        for floor in floors:
            fid        = floor["_id"]
            fname      = floor.get("name", fid)
            felevation = floor.get("elevation", "")

            time.sleep(SLEEP_SEC)
            features = get_geojson_features(fid)
            stats["total_features"] += len(features)

            matches = [
                feature for feature in features
                if feature.get("properties", {}).get("type_id") in TARGET_TYPE_IDS
            ]

            if matches:
                print(f"    Floor {fname:>5}  ->  {len(matches)} match(es) found  (of {len(features)} features)")

                for feature in matches:
                    props    = feature.get("properties") or {}
                    geometry = feature.get("geometry") or {}
                    lng, lat = get_centroid(geometry)

                    matched_rows.append({
                        "building":                  bname,
                        "floor":                     fname,
                        "elevation":                 felevation,
                        "location_id":               props.get("location_id", ""),
                        "location_name":             props.get("location_name", ""),
                        "type_id":                   props.get("type_id", ""),
                        "type_name":                 props.get("type_name", ""),
                        "type_color_hex":            props.get("type_color_hex", ""),
                        "hidden_from_map":            props.get("hidden_from_map", ""),
                        "point_of_interest_id":      props.get("point_of_interest_id", ""),
                        "point_of_interest_type_id": props.get("point_of_interest_type_id", ""),
                        "geometry_type":             geometry.get("type", ""),
                        "longitude":                 round(lng, 10) if lng != "" else "",
                        "latitude":                  round(lat, 10) if lat != "" else "",
                    })

                stats["matched_floors"] += 1
                stats["matched_features"] += len(matches)
            else:
                print(f"    Floor {fname:>5}  ->  no matches  ({len(features)} features scanned)")

    print("\n[3] Saving results...")

    fieldnames = [
        "building", "floor", "elevation",
        "location_id", "location_name",
        "type_id", "type_name", "type_color_hex",
        "hidden_from_map",
        "point_of_interest_id", "point_of_interest_type_id",
        "geometry_type", "longitude", "latitude",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_rows)

    print(f"    ✓ {OUTPUT_CSV}  ({len(matched_rows)} rows)")

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Total features scanned : {stats['total_features']}")
    print(f"  Floors with matches    : {stats['matched_floors']}")
    print(f"  Total matched features : {stats['matched_features']}")

    if matched_rows:
        print("\n  Breakdown by type_id:")
        by_type = defaultdict(list)
        for row in matched_rows:
            by_type[row["type_id"]].append(row)

        for type_id, rows in sorted(by_type.items()):
            type_name = rows[0]["type_name"] if rows[0]["type_name"] else "(no name)"
            print(f"    {type_id}  |  {type_name:<30}  |  {len(rows):>4} locations")

        print("\n  Breakdown by building:")
        by_building = defaultdict(int)
        for row in matched_rows:
            by_building[row["building"]] += 1
        for bname, count in sorted(by_building.items(), key=lambda item: -item[1]):
            print(f"    {bname:<60}  {count:>4}")

    print("\nDone!")


if __name__ == "__main__":
    main()
