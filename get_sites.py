#!/usr/bin/env python2

import pandas as pd

sites = pd.read_json('http://webtris.highwaysengland.co.uk/api/v1.0/sites')
sites = pd.read_json((sites['sites']).to_json()).T
sites.set_index(['Id'], inplace=True)

sites.to_csv('All_Sites.csv')