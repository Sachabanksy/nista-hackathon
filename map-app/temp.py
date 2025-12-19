## we need to read in the data from the google trends and then we need to make them into one

import pandas as pd
import os

path = 'data/google_data'
files= os.listdir(path)

file_name_to_program_lookup = {
    'HS2_uk_regional_daily.csv': 'HS2',
    'Sizewell_C_uk_cities_daily.csv': 'Sizewell C',
    'New_hospital_programme_uk_cities_daily.csv': 'New Hospital Programme'
}

all_data = pd.DataFrame()
for file in files:
    data = pd.read_csv(f'{path}/{file}')
    data['Program'] = file_name_to_program_lookup[file]
    all_data = pd.concat([all_data, data], ignore_index=True)

all_data.to_csv('data/combined_google_trends_data.csv', index=False)
print("done")