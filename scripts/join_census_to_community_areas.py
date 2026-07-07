import geopandas as gpd
import pandas as pd

def weighted_income(g):
    valid = g.dropna(subset=["median_income"])          # drop tracts with no real income data
    if valid.empty or valid["population"].sum() == 0:    # if NOTHING is left, don't divide by zero
        return pd.NA
    return (valid["median_income"] * valid["population"]).sum() / valid["population"].sum()


community_areas = gpd.read_file("../data/raw/geo/community_areas.geojson")
print(community_areas.columns.tolist())  # check the actual name/number field first — often "community" or "area_numbe"

tracts = gpd.read_file("../data/raw/geo/tracts/tl_2024_17_tract.shp")
tracts = tracts.to_crs(community_areas.crs)

# Use Illinois State Plane (feet) for accurate centroids and area calcs
tracts_proj = tracts.to_crs(epsg=3435)
tracts["centroid"] = tracts_proj.geometry.centroid.to_crs(community_areas.crs)
tract_points = tracts.set_geometry("centroid")

joined = gpd.sjoin(tract_points, community_areas, how="inner", predicate="within")

acs = pd.read_csv("../data/raw/census_tract_acs.csv", dtype={"GEOID": str})

acs["median_income"] = acs["median_income"].where(acs["median_income"] >= 0)

joined = joined.merge(acs, on="GEOID")

CA_COL = "community"  # <- replace with whatever printed above

agg = joined.groupby(CA_COL).apply(
    lambda g: pd.Series({
        "population": g["population"].sum(),
        "median_income": weighted_income(g),
    }), include_groups=False
).reset_index()

community_areas_proj = community_areas.to_crs(epsg=3435)
community_areas_proj["area_sqmi"] = community_areas_proj.geometry.area / 27_878_400

agg = agg.merge(community_areas_proj[[CA_COL, "area_sqmi"]], on=CA_COL)
agg["density"] = agg["population"] / agg["area_sqmi"]

agg.to_csv("../data/processed/community_area_census.csv", index=False)
print(agg.head())

print(len(agg))                              # should be 77 — one row per community area
print(agg["population"].sum())                # should land near Chicago's total pop, ~2.7M
print(agg["median_income"].isna().sum())       # how many areas had zero valid tracts for income
