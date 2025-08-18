import pandas as pd
from typing import Dict, Optional

class CropInfo:
    def __init__(self, csv_path: str = "Crop Data.csv"):
        self.crop_info = self._load_crop_info(csv_path)
        self.mode_values = {
            'rationale': 'အခြေခံအကြောင်းအရာများ',
            'market_info': 'စိုက်ပျိုးရေးအကျိုးကျေးဇူးများ',
            'care_info': 'စိုက်ပျိုးရာတွင် လိုအပ်သော ပြုလုပ်နည်းများ'
        }
        
    def _load_crop_info(self, csv_path: str) -> Dict:
        """
        Load crop information from CSV and create a dictionary mapping
        crop names to their relevant information.
        Also calculate mode values for each field.
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Create a dictionary mapping crop names to their info
            crop_dict = {}
            rationale_values = []
            market_info_values = []
            care_info_values = []
            
            for _, row in df.iterrows():
                # Extract crop name from the instruction if it exists
                crop_name = row.get("Crop Name")
                if crop_name:
                    rationale = row.get('Planting Season', 'Not available')
                    market_info = f"Recommended Greenhouse Area: {row.get('Recommended Greenhouse Area (sq.m)', 'N/A')} sq.m"
                    care_info = f"Water Requirement: {row.get('Water Requirement (liters/day)', 'N/A')} liters/day, Fertilizer: {row.get('Fertilizer Type', 'N/A')}"
                    
                    # Store values for mode calculation
                    rationale_values.append(rationale)
                    market_info_values.append(market_info)
                    care_info_values.append(care_info)
                    
                    crop_dict[crop_name] = {
                        'rationale': rationale,
                        'market_info': market_info,
                        'care_info': care_info
                    }
            
            # Define generic placeholders to ignore
            GENERIC_PLACEHOLDERS = set([
                '',
                'အခြေခံအကြောင်းအရာများ',
                'စိုက်ပျိုးရေးအကျိုးကျေးဇူးများ',
                'စိုက်ပျိုးရာတွင် လိုအပ်သော ပြုလုပ်နည်းများ'
            ])
            def get_mode(values):
                filtered = [v for v in values if v and v not in GENERIC_PLACEHOLDERS]
                if filtered:
                    return max(set(filtered), key=filtered.count)
                return ''
            self.mode_values = {
                'rationale': get_mode(rationale_values),
                'market_info': get_mode(market_info_values),
                'care_info': get_mode(care_info_values)
            }
            
            return crop_dict
            
        except FileNotFoundError:
            print(f"Warning: Crop info file '{csv_path}' not found. CropInfo will use default/generic values.")
            # self.mode_values are already set in __init__, so just return empty crop_dict
            return {}
        except Exception as e:
            print(f"Error loading crop info from '{csv_path}': {str(e)}")
            # self.mode_values are already set in __init__
            return {}
            
    def _extract_crop_name(self, instruction: str) -> Optional[str]:
        """Extract crop name from instruction text"""
        # Simple pattern matching to extract crop names
        # This can be improved based on actual data patterns
        if "သစ်ပင်" in instruction or "အပင်" in instruction:
            # Extract words before "သစ်ပင်" or "အပင်"
            words = instruction.split()
            for i, word in enumerate(words):
                if word in ["သစ်ပင်", "အပင်"]:
                    if i > 0:
                        return words[i-1]
        return None
        
    def _get_market_info(self, instruction: str) -> str:
        """Extract market-related information from instruction"""
        # Add more specific patterns as needed
        if "စိုက်ပျိုးရေး" in instruction:
            return "အစိုက်ပျိုးရေးအကျိုးကျေးဇူးများ"
        return ""
        
    def _get_care_info(self, instruction: str) -> str:
        """Extract care-related information from instruction"""
        # Add more specific patterns as needed
        if "စိုက်ပျိုးရာတွင်" in instruction:
            return "စိုက်ပျိုးရာတွင် လိုအပ်သော ပြုလုပ်နည်းများ"
        return ""
        
    # Crop-specific details for dashboard UI
    CROP_DETAILS = {
        'rice': {
            'summary': "Rice is a staple food crop requiring abundant water and warm temperatures. Grows best in flooded fields.",
            'water_usage': "5000 liters/day per hectare",
            'fertilizer': "NPK 16-20-0 at transplanting, top-dress with urea mid-season"
        },
        'onion': {
            'summary': "Onions are cool-season crops that grow best in well-drained, fertile soil with consistent moisture.",
            'water_usage': "2500-3500 liters/day per hectare",
            'fertilizer': "NPK 10-20-10 at planting, side-dress with nitrogen 3-4 weeks after planting"
        },
        'watermelon': {
            'summary': "Watermelons require a long, warm growing season with plenty of sunlight and well-drained soil.",
            'water_usage': "3500-4500 liters/day per hectare",
            'fertilizer': "NPK 10-10-10 at planting, side-dress with nitrogen when vines begin to run"
        },
        'beans': {
            'summary': "Beans fix nitrogen in the soil and need moderate watering. They grow well in warm, sunny locations.",
            'water_usage': "2000 liters/day per hectare",
            'fertilizer': "Inoculated seed, minimal fertilizer needed"
        },
        'corn': {
            'summary': "Corn is a high-yield cereal crop, adaptable to many climates. It thrives in well-drained soils and full sunlight.",
            'water_usage': "5000 liters/day per hectare",
            'fertilizer': "NPK 10-10-10, apply at planting and mid-season"
        },
        'tea': {
            'summary': "Tea plants grow best in humid, highland areas with acidic soils. Regular pruning improves leaf quality.",
            'water_usage': "3000 liters/day per hectare",
            'fertilizer': "Organic manure or NPK 4-8-10, apply every 3 months"
        },
        'coffee': {
            'summary': "Coffee prefers shaded, highland regions with rich, well-drained soils. Requires regular watering.",
            'water_usage': "3000 liters/day per hectare",
            'fertilizer': "Compost or NPK 15-15-15, apply at start of rainy season"
        },
        'pineapple': {
            'summary': "Pineapple grows in warm climates and sandy soils. Needs moderate watering and good drainage.",
            'water_usage': "2500 liters/day per hectare",
            'fertilizer': "NPK 10-10-20, apply every 2 months"
        },
        'strawberry': {
            'summary': "Strawberries need cool temperatures, rich soil, and regular irrigation. Mulch to retain moisture.",
            'water_usage': "2000 liters/day per hectare",
            'fertilizer': "Compost or NPK 12-12-17, apply before flowering"
        },
        'coconut': {
            'summary': "Coconut palms thrive in sandy coastal soils with high rainfall. Deep watering is essential during dry spells.",
            'water_usage': "4000 liters/day per hectare",
            'fertilizer': "Organic manure or NPK 8-2-12, apply 3x/year"
        },
        'mango': {
            'summary': "Mango trees prefer tropical climates and deep, well-drained soils. Water regularly during flowering.",
            'water_usage': "3500 liters/day per hectare",
            'fertilizer': "Compost or NPK 6-6-6, apply at start of rainy season"
        },
        'banana': {
            'summary': "Bananas need rich, moist soils and frequent watering. Protect from wind and apply mulch.",
            'water_usage': "4000 liters/day per hectare",
            'fertilizer': "NPK 8-10-8, apply monthly"
        },
        'palm oil': {
            'summary': "Palm oil trees require tropical climates and high rainfall. Maintain regular irrigation and weed control.",
            'water_usage': "4000 liters/day per hectare",
            'fertilizer': "NPK 12-12-17, apply quarterly"
        },
        'sugarcane': {
            'summary': "Sugarcane grows best in sunny, warm regions with fertile soils. Needs abundant water.",
            'water_usage': "5000 liters/day per hectare",
            'fertilizer': "NPK 18-18-18, apply at planting and mid-growth"
        },
        'cotton': {
            'summary': "Cotton thrives in warm, dry regions. Needs well-drained soils and moderate irrigation.",
            'water_usage': "2000 liters/day per hectare",
            'fertilizer': "NPK 15-15-15, apply at planting and flowering"
        },
        'sesame': {
            'summary': "Sesame prefers sandy, well-drained soils and low rainfall. Drought-tolerant once established.",
            'water_usage': "1500 liters/day per hectare",
            'fertilizer': "Minimal fertilizer; compost at planting"
        },
        'groundnut': {
            'summary': "Groundnuts (peanuts) grow in sandy soils with moderate irrigation. Rotate crops for best yield.",
            'water_usage': "2000 liters/day per hectare",
            'fertilizer': "Gypsum or NPK 6-12-12, apply at planting"
        },
        'chickpea': {
            'summary': "Chickpeas are drought-tolerant legumes, ideal for dry zones. Require minimal watering.",
            'water_usage': "1500 liters/day per hectare",
            'fertilizer': "Inoculated seed, minimal fertilizer needed"
        },
        'wheat': {
            'summary': "Wheat is a cool-season cereal, best in well-drained loamy soils. Needs moderate irrigation.",
            'water_usage': "2000 liters/day per hectare",
            'fertilizer': "NPK 10-20-20, apply at planting and tillering"
        }
    }

    def get_crop_info(self, crop_name: str) -> Dict:
        """Get crop information for a specific crop, including summary, water, and fertilizer."""
        key = crop_name.lower().strip()
        crop_info = self.crop_info.get(key, {})
        details = self.CROP_DETAILS.get(key, {})
        crop_info['summary'] = details.get('summary', 'This is a commonly grown crop in this region.')
        crop_info['water_usage'] = details.get('water_usage', 'Water usage data not available.')
        crop_info['fertilizer'] = details.get('fertilizer', 'Fertilizer info not available.')
        return crop_info
