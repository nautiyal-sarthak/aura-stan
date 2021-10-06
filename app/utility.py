from __future__ import division
from googleapiclient.discovery import build
import pandas as pd
import numpy as np



#Constants
total_kwh=53
max_range=423
kwh_per_km = total_kwh/max_range
super_charge_rate_per_kwh = 0.24
level2_rate_per_hour = 1
level1_rate_per_hour = 0.001125

fule_price_per_l = 1.20
ice_fule_per_100km = 7
cost_per_km_ice = ice_fule_per_100km * fule_price_per_l/100


def getDataFrame(credentials,SPREADSHEET_ID):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    df = pd.DataFrame(result["values"], columns=result["values"][0])
    df.drop(0, inplace=True)
    return df

def getChargeDF(credentials,SPREADSHEET_ID):
    ##Charge Details
    charge_df = getDataFrame(credentials,SPREADSHEET_ID)

    charge_df.set_index("session_id", inplace=True)
    charge_df.index = charge_df.index.astype(int, copy=False)
    charge_df = charge_df[charge_df["session_end_time"].notnull()]



    # # inforsing schema
    charge_df = charge_df.astype(dtype={
        "session_date": "int64",
        "session_start_time": "string",
        "session_start_odometer": "float",
        "session_start_longitude": "float",
        "session_start_latitude": "float",
        "session_start_ideal_battery_range": "float",
        "session_start_energy_added": "float",
        "session_start_battery_range": "float",
        "session_start_miles_added_ideal": "float",
        "session_start_miles_added_rated": "float",
        "session_start_est_battery_range": "float",
        "session_start_usable_battery_level": "int64",
        "session_start_battery_level": "int64",
        "session_end_odometer": "float",
        "session_end_longitude": "float",
        "session_end_latitude": "float",
        "session_end_ideal_battery_range": "float",
        "session_end_energy_added": "float",
        "session_end_battery_range": "float",
        "session_end_miles_added_ideal": "float",
        "session_end_miles_added_rated": "float",
        "session_end_est_battery_range": "float",
        "session_end_usable_battery_level": "int64",
        "session_end_battery_level": "int64",
        "session_end_time": "string",
        "charge_voltage": "string",
        "is_free": "string"
    })

    # adding important cols
    charge_df["session_start_time"] = pd.to_datetime(charge_df['session_start_time'], unit='ms').dt.tz_localize(
        "utc").dt.tz_convert('America/Montreal')

    charge_df["session_end_time"] = pd.to_datetime(charge_df['session_end_time'], unit='ms').dt.tz_localize(
        "utc").dt.tz_convert('America/Montreal')

    # # charge level
    def charge_lvl(row):
        charge_voltage = int(row['charge_voltage'])

        if charge_voltage <= 150:
            chr_typ = "Level 1"
        elif charge_voltage > 150 and charge_voltage < 450:
            chr_typ = "Level 2"
        elif charge_voltage >= 450:
            chr_typ = "Level 3"

        return chr_typ

    charge_df["charge_level"] = charge_df.apply(charge_lvl, axis=1)

    # 1. Charge durtion
    charge_df["charge_duration"] = (charge_df["session_end_time"] - charge_df["session_start_time"]).dt.total_seconds()

    charge_df["session_start_date"] = charge_df["session_start_time"].dt.date

    # 2. KWh added
    charge_df["kwh_added"] = charge_df["session_end_energy_added"] - charge_df["session_start_energy_added"]

    # 3. Km added
    charge_df["km_added"] = (charge_df["session_end_miles_added_ideal"] - charge_df[
        "session_start_miles_added_ideal"]) * 1.60934

    # 4. Cost
    def calCost(row):
        level = row['charge_level']
        is_free = row['is_free']
        duration = row['charge_duration'] / (60 * 60)
        kwh_added = row['kwh_added']
        cost = 0

        if is_free != "TRUE":
            if level == "Level 3":
                cost = kwh_added * super_charge_rate_per_kwh
            elif level == "Level 2":
                cost = duration * level2_rate_per_hour
            elif level == "Level 1":
                cost = duration * level1_rate_per_hour

        return cost

    charge_df['cost'] = charge_df.apply(calCost, axis=1)

    # 5. distance traveled
    charge_df["next_session_start"] = charge_df["session_start_odometer"].shift(-1)
    charge_df["Actual_Distance_km"] = (charge_df["next_session_start"] - charge_df["session_end_odometer"]) * 1.60934

    # 6. Cost per KM traveled
    charge_df["cost/km"] = charge_df['cost'] / charge_df["Actual_Distance_km"]

    charge_df_cal = charge_df[
        ["session_date", "session_start_date", "session_start_time", "session_end_time", "charge_duration",
         "session_start_battery_level", "session_end_battery_level", "kwh_added", "km_added", "cost",
         "Actual_Distance_km", "cost/km", "charge_level"]]

    return charge_df_cal

def getTripDF(credentials, SPREADSHEET_ID,charge_df_cal):
    trip_df = getDataFrame(credentials, SPREADSHEET_ID)
    trip_df.set_index("trip_id", inplace=True)
    trip_df = trip_df[trip_df["trip_end_time"].notnull()]

    # inforsing schema
    trip_df = trip_df.astype(dtype={"trip_date": "int64",
                                    "charge_session_id": "int64",
                                    "trip_start_time": "string",
                                    "trip_start_odometer": "float",
                                    "trip_start_longitude": "float",
                                    "trip_start_latitude": "float",
                                    "trip_start_ideal_battery_range": "float",
                                    "trip_start_energy_added": "float",
                                    "trip_start_battery_range": "float",
                                    "trip_start_miles_added_ideal": "float",
                                    "trip_start_miles_added_rated": "float",
                                    "trip_start_est_battery_range": "float",
                                    "trip_start_usable_battery_level": "int64",
                                    "trip_start_battery_level": "int64",
                                    "trip_start_temp": "float",
                                    "trip_end_odometer": "float",
                                    "trip_end_longitude": "float",
                                    "trip_end_latitude": "float",
                                    "trip_end_ideal_battery_range": "float",
                                    "trip_end_energy_added": "float",
                                    "trip_end_battery_range": "float",
                                    "trip_end_miles_added_ideal": "float",
                                    "trip_end_miles_added_rated": "float",
                                    "trip_end_est_battery_range": "float",
                                    "trip_end_usable_battery_level": "int64",
                                    "trip_end_battery_level": "int64",
                                    "trip_end_temp": "float",
                                    "trip_end_time": "string"})

    # TRIP
    # creating impotant cols
    # 1. Convert epoc time to local time
    trip_df["trip_start_time"] = pd.to_datetime(trip_df['trip_start_time'], unit='ms').dt.tz_localize(
        "utc").dt.tz_convert('America/Montreal')
    trip_df["trip_end_time"] = pd.to_datetime(trip_df['trip_end_time'], unit='ms').dt.tz_localize("utc").dt.tz_convert(
        'America/Montreal')
    trip_df["trip_start_date"] = trip_df["trip_start_time"].dt.date

    # 2. Diffrence of odometer reading - distance traveled
    trip_df["distance_traveled"] = (trip_df["trip_end_odometer"] - trip_df["trip_start_odometer"]) * 1.60934

    # 3. diffence of ideal_battery_range
    trip_df["ideal_battery_range_used"] = (trip_df["trip_start_ideal_battery_range"] - trip_df[
        "trip_end_ideal_battery_range"]) * 1.60934

    # 7. diffrence of battery_level
    trip_df["battery_%_used"] = trip_df["trip_start_battery_level"] - trip_df["trip_end_battery_level"]

    # 8. avg of temp
    trip_df["avg_temp"] = (trip_df["trip_end_temp"] + trip_df["trip_start_temp"]) / 2

    # 9. duration of the trip
    trip_df["duration"] = (trip_df["trip_end_time"] - trip_df["trip_start_time"]).dt.total_seconds()

    # 10. Trip Efficiency = distance traveled/diffence of ideal_battery_range
    trip_df["efficiency"] = trip_df["distance_traveled"] / trip_df["ideal_battery_range_used"] * 100

    # 11. max range = trip_end_ideal_battery_range/(trip_end_battery_level/100)
    trip_df["max_range"] = (trip_df["trip_end_ideal_battery_range"] / (
                trip_df["trip_end_battery_level"] / 100)) * 1.60934

    # 12. max kwh =  max range * kwh_per_km
    trip_df["max_kwh"] = trip_df["max_range"] * kwh_per_km

    # 11. Estimated kwh used =  (max kwh/max range)*distance traveled
    trip_df["Estimated_kwh_used"] = (trip_df["battery_%_used"] / 100) * trip_df["max_kwh"]

    # 13. wh/km =  max kwh/max range
    trip_df["wh/km"] = trip_df["Estimated_kwh_used"] / trip_df["distance_traveled"] * 1000

    # 14 trip cost
    trip_df = trip_df.merge(charge_df_cal, left_on='charge_session_id', right_index=True)
    trip_df["cost_ev"] = trip_df["distance_traveled"] * trip_df["cost/km"]

    # 15 approx cost for ice
    trip_df["cost_ice"] = trip_df["distance_traveled"] * cost_per_km_ice

    # 16 approx cost for ice
    trip_df["money_saved"] = trip_df["cost_ice"] - trip_df["cost_ev"]

    # 17 approv distance
    # 10. Trip Efficiency = distance traveled/diffence of ideal_battery_range
    trip_df["real_dis"] = (trip_df["efficiency"] / 100) * trip_df["max_range"]

    trip_df_cal = trip_df[
        ["charge_session_id", "trip_start_date", "trip_start_time", "trip_end_time", "duration", "avg_temp",
         "distance_traveled", "ideal_battery_range_used", "efficiency", "Estimated_kwh_used", "wh/km", "max_range",
         "max_kwh", "real_dis", "cost_ev", "cost_ice", "money_saved"]]


    return trip_df_cal[~trip_df_cal.isin([np.nan,np.inf]).any(1)]

def getParkDF(credentials, SPREADSHEET_ID):
    phantom_df = getDataFrame(credentials, SPREADSHEET_ID)
    phantom_df.set_index("park_id", inplace=True)


    for col in phantom_df.columns :
        if col not in ["park_start_time","park_sentry_mode","park_end_time"]:
            phantom_df[col] = pd.to_numeric(phantom_df[col], errors="coerce")
        else:
            phantom_df[col] = phantom_df[col].astype(str)

    phantom_df = phantom_df.dropna()


    # adding important cols
    phantom_df["park_start_time"] = pd.to_datetime(phantom_df['park_start_time'], unit='ms').dt.tz_localize(
        "utc").dt.tz_convert('America/Montreal')
    phantom_df["park_end_time"] = pd.to_datetime(phantom_df['park_end_time'], unit='ms').dt.tz_localize(
        "utc").dt.tz_convert('America/Montreal')
    phantom_df["park_start_date"] = phantom_df["park_start_time"].dt.date

    # 1. park durtion
    phantom_df["duration"] = (phantom_df["park_end_time"] - phantom_df["park_start_time"]).dt.total_seconds()

    # 2. diffrence of battery_level
    phantom_df["battery_%_lost"] = phantom_df["park_start_battery_level"] - phantom_df["park_end_battery_level"]

    # 3. max range = trip_end_ideal_battery_range/(trip_end_battery_level/100)
    phantom_df["max_range"] = (phantom_df["park_end_ideal_battery_range"] / (
                phantom_df["park_end_battery_level"] / 100)) * 1.60934

    # 4. max kwh =  max range * kwh_per_km
    phantom_df["max_kwh"] = phantom_df["max_range"] * kwh_per_km

    # 5. Estimated kwh lost =  (max kwh/max range)*distance traveled
    phantom_df["Estimated_kwh_lost"] = (phantom_df["battery_%_lost"] / 100) * phantom_df["max_kwh"]

    # 6. avg of temp
    phantom_df["avg_temp"] = (phantom_df["park_end_temp"] + phantom_df["park_start_temp"]) / 2

    # 7. rate of energy(wh) loss per hour
    phantom_df["wh_loss_rate_per_hr"] = (phantom_df["Estimated_kwh_lost"] * 1000) / (phantom_df["duration"] / (60 * 60))

    phantom_df_cal = phantom_df[
        ["park_date", "park_start_date", "charge_session_id", "park_sentry_mode", "park_start_time", "park_end_time",
         "duration", "avg_temp", "battery_%_lost", "Estimated_kwh_lost", "wh_loss_rate_per_hr"]]

    return phantom_df_cal
