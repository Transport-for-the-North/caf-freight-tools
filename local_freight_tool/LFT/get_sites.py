"""
    Downloads WebTRIS data from Highways England.
    Downloads All_Sites.csv to obtain latest list of sites from the API.
"""

import pandas as pd


if __name__ == "__main__":
    sites = pd.read_json("http://webtris.highwaysengland.co.uk/api/v1.0/sites")
    sites = pd.read_json((sites["sites"]).to_json()).T
    sites.set_index(["Id"], inplace=True)

    sites.to_csv("All_Sites.csv")
