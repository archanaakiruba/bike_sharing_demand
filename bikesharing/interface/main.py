import pandas as pd

from bikesharing.ml_logic.data import get_raw_data, get_weather_data, get_polygons
from bikesharing.ml_logic.encoders import encode_district_label, encode_temporal_features
from bikesharing.ml_logic.preprocessor import group_rental_data_by_hour, preprocess_features
from bikesharing.ml_logic.feature_engineering import is_holiday, is_weekend ,feature_selection
from bikesharing.params import *

from pathlib import Path
from colorama import Fore, Style



def preprocess():
    """
    1. call get_raw_data
    2. drop cols
    3. clean (rm duplicates)
    3. encode y
    4. aggregate by hour
    5. join with weather data (get_weather_data)
    6. feature engineering & merge
    7. feature selection
    8. preproc-pipeline
    """

    cache_path_X_preproc=Path(f'{LOCAL_DATA_PATH}/processed/X_processed_from_{START_YEAR}_to_{END_YEAR}.csv')
    cache_path_y_preproc=Path(f'{LOCAL_DATA_PATH}/processed/y_processed_from_{START_YEAR}_to_{END_YEAR}.csv')

    if cache_path_X_preproc.is_file():
        print(Fore.BLUE + "\nLoad preprocessed data from local CSV..." + Style.RESET_ALL)
        X_processed = pd.read_csv(cache_path_X_preproc , header='infer')
        y = pd.read_csv(cache_path_y_preproc , header='infer')
        if X_processed.shape[0] == y.shape[0]:
            return X_processed , y
        print('\nShape mismatch between y and X')
        return None

    print(Fore.BLUE + "\nPreprocessing Data..." + Style.RESET_ALL)

    # 1. get_raw_data
    query =f'''
        SELECT *
        FROM `{GCP_PROJECT}.{BQ_DATASET}.raw_data_mvg`
    '''

    rental_data_df = get_raw_data(gcp_project=GCP_PROJECT , query=query , cache_path=Path(f'{LOCAL_DATA_PATH}/raw/mvg_rentals_from_{START_YEAR}_to_{END_YEAR}.csv'))

    # 2. drop cols
    rental_relavent_cols_df = rental_data_df[['STARTTIME' , 'STARTLAT' , 'STARTLON']]

    # 3. clean(rm duplicates)
    rental_relavent_cols_df = rental_relavent_cols_df.drop_duplicates()

    # 4. encode y
    encoded_rental_df = encode_district_label(rental_relavent_cols_df , get_polygons())

    # 5. aggregate by hour
    aggregated_rental_df = group_rental_data_by_hour(encoded_rental_df)

    # 6. join with weather data
    weather_data_df = get_weather_data(cache_path=Path(f'{LOCAL_DATA_PATH}/raw/histotical_weather_data_{START_YEAR}_to_{END_YEAR}.csv'))
    weather_data_df['time'] = pd.to_datetime(weather_data_df['time'])
    merged_df = aggregated_rental_df.merge(weather_data_df, right_on='time' , left_on='rent_date_hour' , how='outer')
    merged_df['rent_date_hour'] = merged_df['time']
    merged_df = merged_df.sort_values(by='rent_date_hour').drop(columns=['time'])

    # 7. feature enginering & merge
    holidays = is_holiday(merged_df[['rent_date_hour']])
    merged_df = merged_df.merge(holidays , on='rent_date_hour' , how='inner')

    weekends = is_weekend(merged_df[['rent_date_hour']])
    merged_df = merged_df.merge(weekends , on='rent_date_hour' , how='inner')

    encoded_date = encode_temporal_features(merged_df[['rent_date_hour']])
    merged_df = merged_df.merge(encoded_date , on='rent_date_hour' , how='inner')

    # 8. feature selection

    districts = ['Altstadt-Lehel', 'Au - Haidhausen',
       'Aubing-Lochhausen-Langwied', 'Berg am Laim', 'Bogenhausen',
       'Feldmoching', 'Hadern', 'Harlaching', 'Hasenbergl-Lerchenau Ost',
       'Laim', 'Lochhausen', 'Ludwigsvorstadt-Isarvorstadt', 'Maxvorstadt',
       'Milbertshofen-Am Hart', 'Moosach', 'Neuhausen-Nymphenburg',
       'Obergiesing', 'Obermenzing', 'Obersendling', 'Pasing',
       'Pasing-Obermenzing', 'Ramersdorf-Perlach', 'Schwabing-Freimann',
       'Schwabing-West', 'Schwanthalerhöhe', 'Sendling', 'Sendling-Westpark',
       'Südgiesing', 'Thalkirchen', 'Trudering', 'Trudering-Riem',
       'Untergiesing', 'Untergiesing-Harlaching', 'Untermenzing-Allach']

    X = merged_df.drop(columns=districts)
    y = merged_df[districts].fillna(0)

    features = ['temperature_2m', 'relativehumidity_2m', 'apparent_temperature',
       'windspeed_10m', 'precipitation', 'is_holiday', 'is_weekend',
       'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'day_sin', 'day_cos']

    selected_merged_df = feature_selection(X , features)

    # 9. preproc-pipeline (Keep date_time for RNN)
    X_processed = preprocess_features(selected_merged_df)

    X_processed.columns = features
    X_processed.to_csv(cache_path_X_preproc , header=True , index=False)
    y.to_csv(cache_path_y_preproc , header=True , index=False)

    if X_processed.shape[0] == y.shape[0]:
            return X_processed , y

    print('\nShape mismatch between y and X')
    return None

# function to be defined
def train():
    """
    - Download processed data from your BQ table (or from cache if it exists)
    - Train on the preprocessed dataset (which should be ordered by date)
    - Store training results and model weights

    Return val_mae as a float
    """

    # 1. Load processed data
        # 1.1 Load from cache if present

        # 1.2 Load from GBQ if not

    # 2. Test/Train/Val Split
        # Train=2 years
        # Test=1 year
        # Val=1 year
    pass

# function to be defined
def predict():
    pass

# function to be defined
def evaluate():
    pass
