import pandas as pd
from app.data.region_crops import region_crops

# Load the original crop data
crop_df = pd.read_csv('data/crop_data.csv')

# Build crop to region mapping
crop_to_region = {}
for region, info in region_crops.items():
    for crop in info['suitable_crops']:
        crop_to_region[crop.lower()] = region

# Assign region to each crop
crop_df['region'] = crop_df['crop_name'].str.lower().map(crop_to_region)

# Drop rows where region could not be assigned
crop_df = crop_df.dropna(subset=['region'])

# Save new file
crop_df.to_csv('data/crop_data_with_region.csv', index=False)
print('Generated data/crop_data_with_region.csv with region column.')
