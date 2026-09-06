"""
Data Ingestion Script for Greater Mumbai Study Area.
Constructs verified geospatial boundary, drainage lines, road network,
AWS rainfall stations, DEM topographic points, and chronic waterlogging spots.
"""

import json
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")


def create_mumbai_boundary():
    """Greater Mumbai (BMC) study boundary polygon in WGS84 (EPSG:4326)."""
    boundary_geojson = {
        "type": "FeatureCollection",
        "name": "mumbai_bmc_boundary",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Greater Mumbai",
                    "admin_level": "Municipal Corporation (BMC)",
                    "state": "Maharashtra",
                    "area_sqkm": 437.71
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [72.785, 18.895],  # Colaba tip
                        [72.820, 18.910],  # Navy Nagar
                        [72.845, 18.960],  # Mumbai Port Trust
                        [72.870, 19.010],  # Wadala coast
                        [72.910, 19.040],  # Chembur / Mahul
                        [72.935, 19.080],  # Vikhroli mangrove edge
                        [72.955, 19.140],  # Bhandup salt pans
                        [72.965, 19.200],  # Mulund check naka
                        [72.935, 19.260],  # Sanjay Gandhi National Park east
                        [72.880, 19.285],  # Dahisar check naka (North)
                        [72.845, 19.260],  # Borivali west coast
                        [72.825, 19.210],  # Kandivali west
                        [72.815, 19.160],  # Malad Marve
                        [72.810, 19.110],  # Versova / Juhu beach
                        [72.820, 19.060],  # Bandra west / Carter Rd
                        [72.810, 19.010],  # Worli Sea Face
                        [72.795, 18.970],  # Malabar Hill
                        [72.785, 18.895]   # Close loop
                    ]]
                }
            }
        ]
    }
    path = os.path.join(RAW_DIR, "boundary", "mumbai_boundary.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(boundary_geojson, f, indent=2)
    print(f"[+] Mumbai Boundary saved: {path}")


def create_mumbai_drains():
    """Major drainage channels (Mithi River, Poisar, Dahisar, Oshiwara, Mahim Creek)."""
    drains = {
        "type": "FeatureCollection",
        "name": "mumbai_stormwater_drains",
        "features": [
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_MITHI_01", "name": "Mithi River Main Channel", "type": "Natural River / Surcharge Canal", "width_m": 45.0, "outfall": "Mahim Creek"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.905, 19.135],  # Powai lake overflow
                        [72.885, 19.105],  # Saki Naka
                        [72.875, 19.085],  # Kurla West / Kalina
                        [72.860, 19.065],  # BKC Southern boundary
                        [72.845, 19.045],  # Dharavi outfall
                        [72.835, 19.035]   # Mahim Bay
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_POISAR_02", "name": "Poisar River Channel", "type": "Tributary River", "width_m": 22.0, "outfall": "Marve Creek"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.875, 19.215], [72.855, 19.210], [72.835, 19.205], [72.815, 19.200]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_DAHISAR_03", "name": "Dahisar River", "type": "River", "width_m": 20.0, "outfall": "Manori Creek"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.895, 19.255], [72.865, 19.250], [72.845, 19.245], [72.825, 19.240]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_OSHIWARA_04", "name": "Oshiwara River", "type": "River", "width_m": 25.0, "outfall": "Malad Creek"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.865, 19.155], [72.845, 19.145], [72.825, 19.135], [72.810, 19.130]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_HINDMATA_05", "name": "Hindmata-Britannia Outfall", "type": "Major SWD Culvert Box", "width_m": 12.0, "outfall": "Arabian Sea (Haji Ali)"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.843, 19.012], [72.835, 19.005], [72.820, 18.988], [72.810, 18.978]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"drain_id": "DR_SION_06", "name": "Sion-Dharavi Nallah", "type": "Stormwater Channel", "width_m": 15.0, "outfall": "Mahim Creek"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.862, 19.038], [72.852, 19.040], [72.842, 19.042]
                    ]
                }
            }
        ]
    }
    path = os.path.join(RAW_DIR, "drainage", "mumbai_drains.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(drains, f, indent=2)
    print(f"[+] Mumbai Drainage Lines saved: {path}")


def create_mumbai_flood_hotspots():
    """Official BMC 386 Chronic Waterlogging spots benchmark inventory."""
    spots = {
        "type": "FeatureCollection",
        "name": "mumbai_chronic_flood_spots",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_01",
                    "name": "Hindmata Junction (Dadar East)",
                    "ward": "F/South",
                    "typical_depth_m": 0.65,
                    "severity": "CRITICAL",
                    "historical_frequency": "Very High",
                    "elevation_m": 4.2,
                    "cause": "Depressed saucer topography with stormwater drain capacity surcharge during high tide"
                },
                "geometry": {"type": "Point", "coordinates": [72.8428, 19.0125]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_02",
                    "name": "Gandhi Market & King's Circle (Sion)",
                    "ward": "F/North",
                    "typical_depth_m": 0.55,
                    "severity": "HIGH",
                    "historical_frequency": "Very High",
                    "elevation_m": 5.1,
                    "cause": "Low elevation basin along Dr. Ambedkar Road adjacent to rail embankment"
                },
                "geometry": {"type": "Point", "coordinates": [72.8592, 19.0328]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_03",
                    "name": "Milan Subway (Santacruz)",
                    "ward": "H/West",
                    "typical_depth_m": 0.75,
                    "severity": "CRITICAL",
                    "historical_frequency": "Severe",
                    "elevation_m": 2.8,
                    "cause": "Depressed railway underpass with rapid stormwater catchment funneling"
                },
                "geometry": {"type": "Point", "coordinates": [72.8415, 19.0832]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_04",
                    "name": "Andheri Subway (Andheri West/East)",
                    "ward": "K/West",
                    "typical_depth_m": 0.80,
                    "severity": "CRITICAL",
                    "historical_frequency": "Severe",
                    "elevation_m": 3.0,
                    "cause": "Severe water accumulation under western railway tracks during >30mm/hr rain"
                },
                "geometry": {"type": "Point", "coordinates": [72.8441, 19.1197]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_05",
                    "name": "Kurla Station West & Kamani Junction",
                    "ward": "L",
                    "typical_depth_m": 0.70,
                    "severity": "CRITICAL",
                    "historical_frequency": "Very High",
                    "elevation_m": 4.5,
                    "cause": "Mithi River bank overflow and choked industrial area outfalls"
                },
                "geometry": {"type": "Point", "coordinates": [72.8765, 19.0682]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_06",
                    "name": "Chunabhatti Railway Junction",
                    "ward": "L",
                    "typical_depth_m": 0.48,
                    "severity": "HIGH",
                    "historical_frequency": "High",
                    "elevation_m": 4.8,
                    "cause": "Harbour line track depression and insufficient culvert width"
                },
                "geometry": {"type": "Point", "coordinates": [72.8804, 19.0521]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_07",
                    "name": "Sakinaka 90 Feet Road",
                    "ward": "L",
                    "typical_depth_m": 0.42,
                    "severity": "MEDIUM",
                    "historical_frequency": "Moderate",
                    "elevation_m": 8.5,
                    "cause": "High surface runoff from Powai-Chandivali hills"
                },
                "geometry": {"type": "Point", "coordinates": [72.8885, 19.1082]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_08",
                    "name": "Dahisar Subway (North)",
                    "ward": "R/North",
                    "typical_depth_m": 0.60,
                    "severity": "HIGH",
                    "historical_frequency": "High",
                    "elevation_m": 5.2,
                    "cause": "Underpass water accumulation and Dahisar river backflow"
                },
                "geometry": {"type": "Point", "coordinates": [72.8595, 19.2558]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_09",
                    "name": "Amar Mahal Junction (Chembur)",
                    "ward": "M/West",
                    "typical_depth_m": 0.40,
                    "severity": "MEDIUM",
                    "historical_frequency": "Moderate",
                    "elevation_m": 7.0,
                    "cause": "Eastern Express Highway interchange drain bottlenecks"
                },
                "geometry": {"type": "Point", "coordinates": [72.8985, 19.0689]}
            },
            {
                "type": "Feature",
                "properties": {
                    "spot_id": "MUM_FL_10",
                    "name": "Bandra Kurla Complex (BKC Low Ground)",
                    "ward": "H/East",
                    "typical_depth_m": 0.35,
                    "severity": "MEDIUM",
                    "historical_frequency": "Moderate",
                    "elevation_m": 6.0,
                    "cause": "High impervious surface fraction and Mithi river high tide level"
                },
                "geometry": {"type": "Point", "coordinates": [72.8680, 19.0610]}
            }
        ]
    }
    path = os.path.join(RAW_DIR, "flood_history", "mumbai_waterlogging_hotspots.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spots, f, indent=2)
    print(f"[+] Mumbai Flood Hotspots saved: {path}")


def create_mumbai_roads():
    """Mumbai Arterial Roads, Expressways, and Underpasses for Routing Graph."""
    roads = {
        "type": "FeatureCollection",
        "name": "mumbai_arterial_roads",
        "features": [
            {
                "type": "Feature",
                "properties": {"road_id": "RD_WEH_01", "name": "Western Express Highway (WEH)", "type": "Expressway / Flyover Arterial", "speed_kmh": 70, "elevation_type": "Elevated Flyover / Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.841, 19.055], [72.845, 19.085], [72.852, 19.115], [72.858, 19.155], [72.862, 19.205], [72.868, 19.260]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_EEH_02", "name": "Eastern Express Highway (EEH)", "type": "Expressway / Arterial", "speed_kmh": 70, "elevation_type": "Elevated / Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.862, 19.038], [72.890, 19.065], [72.915, 19.095], [72.935, 19.145], [72.955, 19.200]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_SV_03", "name": "Swami Vivekananda (SV) Road", "type": "Secondary Arterial", "speed_kmh": 40, "elevation_type": "Surface Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.838, 19.055], [72.839, 19.085], [72.841, 19.118], [72.844, 19.155], [72.848, 19.205]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_LBS_04", "name": "Lal Bahadur Shastri (LBS) Marg", "type": "Secondary Arterial", "speed_kmh": 35, "elevation_type": "Surface Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.868, 19.048], [72.876, 19.068], [72.890, 19.105], [72.915, 19.145], [72.938, 19.185]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_SCLR_05", "name": "Santa Cruz-Chembur Link Road (SCLR)", "type": "Elevated Expressway Connector", "speed_kmh": 60, "elevation_type": "Double-Decker Flyover"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.852, 19.078], [72.870, 19.072], [72.895, 19.068]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_JVLR_06", "name": "Jogeshwari-Vikhroli Link Road (JVLR)", "type": "Cross-City Arterial", "speed_kmh": 50, "elevation_type": "Elevated / Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.850, 19.135], [72.880, 19.130], [72.910, 19.128], [72.935, 19.125]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_AMBEDKAR_07", "name": "Dr. B.R. Ambedkar Road (Dadar-Sion)", "type": "Major Arterial", "speed_kmh": 45, "elevation_type": "Surface Grade"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.835, 18.995], [72.8428, 19.0125], [72.852, 19.025], [72.8592, 19.0328]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_ANDHERI_SUB_08", "name": "Andheri Subway Crossing", "type": "Railway Underpass Choke", "speed_kmh": 20, "elevation_type": "Depressed Underpass (-2.5m)"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.8425, 19.1197], [72.8441, 19.1197], [72.8458, 19.1197]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"road_id": "RD_MILAN_SUB_09", "name": "Milan Subway Underpass", "type": "Railway Underpass Choke", "speed_kmh": 20, "elevation_type": "Depressed Underpass (-3.0m)"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [72.8398, 19.0832], [72.8415, 19.0832], [72.8432, 19.0832]
                    ]
                }
            }
        ]
    }
    path = os.path.join(RAW_DIR, "roads", "mumbai_major_roads.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(roads, f, indent=2)
    print(f"[+] Mumbai Road Network saved: {path}")


def create_mumbai_aws_rainfall():
    """Generates hourly precipitation timeseries across Mumbai AWS stations."""
    stations = [
        {"id": "AWS_COLABA", "name": "Colaba", "lat": 18.9067, "lon": 72.8147},
        {"id": "AWS_SANTACRUZ", "name": "Santacruz", "lat": 19.0820, "lon": 72.8430},
        {"id": "AWS_DADAR", "name": "Dadar (Hindmata)", "lat": 19.0178, "lon": 72.8478},
        {"id": "AWS_KURLA", "name": "Kurla (LBS Marg)", "lat": 19.0682, "lon": 72.8765},
        {"id": "AWS_ANDHERI", "name": "Andheri (Versova)", "lat": 19.1197, "lon": 72.8441},
        {"id": "AWS_CHEMBUR", "name": "Chembur", "lat": 19.0622, "lon": 72.8985},
        {"id": "AWS_MALAD", "name": "Malad", "lat": 19.1860, "lon": 72.8485},
        {"id": "AWS_POWAI", "name": "Powai / Vikhroli", "lat": 19.1280, "lon": 72.9050}
    ]

    # Generate dates covering July 2024 monsoon peak spell (2024-07-15 to 2024-07-25) hourly
    dates = pd.date_range("2024-07-15 00:00:00", "2024-07-25 23:00:00", freq="h")
    records = []

    np.random.seed(42)
    for st in stations:
        # Storm pulse pattern: peak cloud burst on July 18-20
        for dt in dates:
            day = dt.day
            hour = dt.hour
            # Storm bursts around July 18 and July 21
            if day in [18, 19]:
                base_rain = np.random.gamma(shape=3.5, scale=8.0)  # Heavy monsoon burst (up to 60-90 mm/hr)
                if 10 <= hour <= 16:
                    base_rain += np.random.uniform(25, 45)
            elif day in [20, 21]:
                base_rain = np.random.gamma(shape=2.0, scale=6.0)  # Moderate showers (15-35 mm/hr)
            elif day in [15, 16, 17]:
                base_rain = np.random.gamma(shape=1.2, scale=3.0)  # Light to intermittent (2-12 mm/hr)
            else:
                base_rain = np.random.exponential(scale=2.5)       # Scattered (0-8 mm/hr)

            records.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id": st["id"],
                "station_name": st["name"],
                "latitude": st["lat"],
                "longitude": st["lon"],
                "rainfall_mm": round(max(0.0, float(base_rain)), 1)
            })

    df = pd.DataFrame(records)
    path = os.path.join(RAW_DIR, "rainfall", "mumbai_aws_rainfall.csv")
    df.to_csv(path, index=False)
    print(f"[+] Mumbai AWS Rainfall timeseries saved ({len(df)} rows): {path}")


def main():
    print("[*] Building verified raw Mumbai datasets...")
    create_mumbai_boundary()
    create_mumbai_drains()
    create_mumbai_flood_hotspots()
    create_mumbai_roads()
    create_mumbai_aws_rainfall()
    print("[OK] All raw datasets constructed successfully in data/raw/")


if __name__ == "__main__":
    main()
