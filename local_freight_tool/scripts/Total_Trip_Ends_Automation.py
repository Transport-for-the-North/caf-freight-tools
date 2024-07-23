import pandas as pd
import os

output_path = r"U:\Lot3_LFT\2.LGV Model\Outputs\2028\LGV Model Outputs - 2023-10-04 10.05.51\trip ends"


def total_trip_ends(output_path):
    commute_drivers = pd.read_csv(os.path.join(output_path, r"commute_Drivers_trip_ends.csv"))
    commute_skilled_trades = pd.read_csv(os.path.join(output_path, r"commute_Skilled trades_trip_ends.csv"))
    delivery_grocery = pd.read_csv(os.path.join(output_path, r"delivery_grocery_trip_ends.csv"))
    delivery_parcel_bush = pd.read_csv(os.path.join(output_path, r"delivery_parcel_bush_trip_ends.csv"))
    delivery_parcel_stem = pd.read_csv(os.path.join(output_path, r"delivery_parcel_stem_trip_ends.csv"))
    service = pd.read_csv(os.path.join(output_path, r"service_trip_ends.csv"))


    function_dict = {
        'commute_drivers_productions_trip_end_totals': commute_drivers['Productions'].sum(),
        'commute_skilled_trades_productions_trip_end_totals': commute_skilled_trades['Productions'].sum(),
        'delivery_grocery_origins_trip_end_totals': delivery_grocery['Origins'].sum(),
        'delivery_parcel_bush_origins_trip_end_totals': delivery_parcel_bush['Origins'].sum(),
        'delivery_parcel_stem_productions_trip_end_totals': delivery_parcel_stem['Productions'].sum(),
        'service_productions_trip_end_totals': service['Productions'].sum(),
        'commute_drivers_attractions_trip_end_totals': commute_drivers['Attractions'].sum(),
        'commute_skilled_trades_attractions_trip_end_totals': commute_skilled_trades['Attractions'].sum(),
        'delivery_grocery_destinations_trip_end_totals': delivery_grocery['Destinations'].sum(),
        'delivery_parcel_bush_destinations_trip_end_totals': delivery_parcel_bush['Destinations'].sum(),
        'delivery_parcel_stem_attractions_trip_end_totals': delivery_parcel_stem['Attractions'].sum(),
        'service_attractions_trip_end_totals': service['Attractions'].sum(),
    }

    dataframe_list = []
    for trip_type, val in function_dict.items():
        dataframe_list.append({'Trip Type': trip_type, 'Trip Totals': val})
    output = pd.DataFrame(dataframe_list)
    return output

total_trip_ends(output_path).to_csv(os.path.join(output_path, 'trip_end_totals.csv'))
