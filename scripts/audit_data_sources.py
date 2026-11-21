"""Recount archived inputs for the MandiGuard source audit. Run with the repository path."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def main(root):
    raw = root / "data/raw"
    processed = root / "data/processed"
    prices = ["Min_Price", "Max_Price", "Modal_Price"]
    keys = ["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date"]
    archive = pd.read_parquet(raw / "agmarknet_6state_top_apple_2024_2026_all.parquet")
    panel = pd.read_parquet(raw / "agmarknet_6state_top_apple_2024_2026.parquet")
    decade = pd.read_parquet(raw / "agmarknet_6state_decade_2017_2026.parquet")
    result = {}
    for name, frame in [("core_panel", panel), ("all_clean", archive), ("decade", decade)]:
        market_cols = ["State", "Market"]
        result[name] = {
            "rows": len(frame), "days": frame.Arrival_Date.nunique(), "first": str(frame.Arrival_Date.min())[:10],
            "last": str(frame.Arrival_Date.max())[:10], "states": frame.State.nunique(),
            "state_market_keys": len(frame[market_cols].drop_duplicates()),
            "market_keys_multiple_districts": int((frame.groupby(market_cols).District.nunique() > 1).sum()),
            "nonunique_key_excess_rows": int(frame.duplicated(keys).sum()),
            "exact_price_key_duplicate_excess_rows": int(frame.duplicated(keys + prices).sum()),
            "modal_outside_bounds": int((~frame.Modal_Price.between(frame.Min_Price, frame.Max_Price)).sum()),
            "varieties": frame.Variety.nunique(), "grades": frame.Grade.nunique(),
            "crops": frame.Commodity.value_counts().to_dict(),
        }

    # Recompute rankings against a training-only 80-day eligibility requirement.
    training = archive.loc[archive.Arrival_Date < "2025-01-01"]
    days = training.groupby(["State", "Market"]).Arrival_Date.nunique().rename("days").reset_index()
    train_only = days[days.days >= 80].sort_values(["State","days","Market"], ascending=[True,False,True]).groupby("State").head(30)
    actual_markets = set(panel.set_index(market_cols).index)
    result["retained_only_due_to_full_period_eligibility"] = sorted(actual_markets-set(train_only.set_index(market_cols).index))

    def compare(left, right, key):
        # Compare key sets and price-triplet sets to avoid multiplying duplicate keys.
        a = left[key + prices].drop_duplicates()
        b = right[key + prices].drop_duplicates()
        match = a.merge(b, on=key, suffixes=("_a", "_b"))
        return {
            "left_rows": len(left), "right_rows_in_scope": len(right),
            "left_unique_keys": len(a.drop_duplicates(key)), "right_unique_keys": len(b.drop_duplicates(key)),
            "shared_keys": len(a[key].drop_duplicates().merge(b[key].drop_duplicates(), on=key)),
            "matched_row_pairs": len(match),
            "equal_key_price_triplets": len(a.merge(b, on=key + prices)),
            "min_max_modal_equal_row_pairs": [int((match[c+"_a"] == match[c+"_b"]).sum()) for c in prices],
            "left_dates": left.Arrival_Date.nunique(), "matched_dates": match.Arrival_Date.nunique(),
        }
    xml_rows = [{n.tag.replace("_x0020_","_"): n.text for n in row}
                for row in ET.parse(raw / "official_datagov_datewise_prices.xml").findall(".//Table")]
    xml = pd.DataFrame(xml_rows)
    xml["Arrival_Date"] = pd.to_datetime(xml.Arrival_Date, format="%d/%m/%Y")
    xml[prices] = xml[prices].apply(pd.to_numeric)
    national_day = xml.copy()
    national_day["Market"] = national_day.Market.str.replace(r"\s+APMC$", "", regex=True).str.strip()
    in_panel = national_day.merge(panel[market_cols].drop_duplicates(), on=market_cols)
    target_reporters = in_panel[in_panel.Commodity.isin(panel.Commodity.unique())]
    result["xml_core_markets_with_only_nonstudy_crops"] = sorted(set(in_panel.set_index(market_cols).index) -
                                                                 set(target_reporters.set_index(market_cols).index))
    xml = xml[xml.State.isin(panel.State.unique()) & xml.Commodity.isin(panel.Commodity.unique())].copy()
    xml["Market"] = xml.Market.str.replace(r"\s+APMC$", "", regex=True).str.strip()
    # Match district normalization in the archived panel via its own raw-to-canonical crosswalk.
    aliases = decade[["State", "District", "District_Raw"]].drop_duplicates()
    crosswalk = {(a.State,a.District_Raw):a.District for a in aliases.itertuples()}
    xml["District"] = [crosswalk.get((s,d),d) for s,d in zip(xml.State, xml.District)]
    source_states_markets = decade[market_cols].drop_duplicates()
    xml_core = xml.merge(source_states_markets, on=market_cols)
    core_day = decade[decade.Arrival_Date.isin(xml_core.Arrival_Date)]
    result["xml"] = {"source_rows": len(xml_rows), "target_rows_before_panel": len(xml), **compare(xml_core,core_day,keys)}

    hp = pd.read_csv(raw / "hp_apple_daily_2025_2026.csv").rename(columns={c.lower():c for c in keys+prices})
    hp["Arrival_Date"] = pd.to_datetime(hp.Arrival_Date)
    mir = archive[(archive.State == "Himachal Pradesh") & (archive.Commodity == "Apple")].copy()
    overlap = hp[hp.Arrival_Date <= mir.Arrival_Date.max()].copy()
    mir = mir[(mir.Arrival_Date >= overlap.Arrival_Date.min()) & (mir.Arrival_Date <= overlap.Arrival_Date.max())].copy()
    for d in [overlap,mir]:
        for c in ["Market","Variety","Grade","District"]:
            d[c] = d[c].str.strip().str.lower()
    result["hp_apple"] = {"source_rows":len(hp), "source_market_names":hp.Market.nunique(), "source_days":hp.Arrival_Date.nunique(),
        "source_first":str(hp.Arrival_Date.min())[:10], "source_last":str(hp.Arrival_Date.max())[:10],
        "retrieval_vintages":hp.retrieval_timestamp.unique().tolist(),
        "recorded_arrival_tonnes_median":float(hp.arrival_tonnes.median()), "rows_below_3_tonnes":int((hp.arrival_tonnes<3).sum()),
        "all_price_triplets_with_district":compare(overlap,mir,keys),
        "published_join_without_district":compare(overlap,mir,[k for k in keys if k != "District"])}

    coords = pd.read_parquet(processed / "mandi_coordinates.parquet")
    roads = pd.read_parquet(processed / "osrm_corridor_matrix.parquet")
    endpoints = coords[["State", "Market","geocode_precision"]].drop_duplicates(["State","Market"])
    routed = roads.rename(columns={"state":"State"})
    for side in ["origin","dest"]:
        routed = routed.merge(endpoints.rename(columns={"Market":side+"_market","geocode_precision":side+"_precision"}),on=["State",side+"_market"],validate="m:1")
    result["route_matrix"] = {"rows":len(roads), "endpoints":coords.geocode_precision.value_counts().to_dict(),
        "routes_with_centroid_endpoint":int(((routed.origin_precision=="district_centroid")|(routed.dest_precision=="district_centroid")).sum())}
    weather = pd.read_parquet(processed / "mandi_weather_2024_2026.parquet")
    weather_cells = []
    for name,d in weather.groupby("fc_source"):
        weather_cells.append({"source":name, "rows":len(d), "cells":len(d[["grid_lat","grid_lon"]].drop_duplicates()),
                "rows_with_forecast_equal_to_realized_rain":int((d.fc_rain_mm==d.era5_rain_mm).sum()),
                "rows_with_equal_positive_rain":int(((d.fc_rain_mm==d.era5_rain_mm)&(d.era5_rain_mm>0)).sum()),
                "rows_with_forecast_equal_to_realized_humidity":int((d.fc_rh_mean==d.era5_rh_mean).sum())})
    result["weather"] = weather_cells
    with (root / "data/manifests/govt_survey_manifest.json").open() as f:
        manifest = json.load(f)
    result["survey_snapshot_sha256_matches"] = {name:hashlib.sha256((root/entry["local_archive_path"]).read_bytes()).hexdigest()==entry["sha256"]
        for name,entry in manifest["sources_archived"].items()}
    snapshot = json.loads((raw / "live_nov2026_agmarknet_snapshot.json").read_text())
    weekly = snapshot["records"]
    def has_numeric_quote(record):
        return any(pd.notna(pd.to_numeric(value, errors="coerce"))
                   for row in record["data"] for k,value in row.items()
                   if k not in {"variety","unitOfPrice"})
    result["november_snapshot"] = {
        "queries":len(weekly), "http_200":sum(r["http_status"]==200 for r in weekly),
        "with_numeric_price":sum(has_numeric_quote(r) for r in weekly),
        "distinct_markets":len({(r["state_id"],r["market_id"]) for r in weekly}),
        "distinct_market_commodity_keys":len({(r["state_id"],r["market_id"],r["commodity_id"]) for r in weekly}),
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository",type=Path)
    print(json.dumps(main(parser.parse_args().repository),indent=2,default=int))
