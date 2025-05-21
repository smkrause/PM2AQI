import unittest

# Copied from main.py for self-contained testing
HEALTH_RISKS_DATA = [
    ("Good", 
     "None", 
     "Air quality is considered satisfactory, and air pollution poses little or no risk.", 
     "Enjoy your usual outdoor activities."),
    ("Moderate", 
     "Unusually sensitive people should consider reducing prolonged or heavy exertion.", 
     "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.", 
     "Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion."),
    ("Unhealthy for Sensitive Groups", 
     "People with heart or lung disease, older adults, and children should reduce prolonged or heavy exertion.", 
     "Members of sensitive groups may experience health effects. The general public is not likely to be affected.", 
     "Active children and adults, and people with respiratory disease, such as asthma, should reduce prolonged outdoor exertion."),
    ("Unhealthy", 
     "People with heart or lung disease, older adults, and children should avoid prolonged or heavy exertion. Everyone else should reduce prolonged or heavy exertion.", 
     "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.", 
     "Active children and adults, and people with respiratory disease, such as asthma, should avoid prolonged outdoor exertion; everyone else, especially children, should limit prolonged outdoor exertion."),
    ("Very Unhealthy", 
     "People with heart or lung disease, older adults, and children should avoid all outdoor physical activity. Everyone else should avoid prolonged or heavy exertion.", 
     "Health alert: everyone may experience more serious health effects.", 
     "Everyone should avoid all outdoor exertion."),
    ("Hazardous", 
     "Everyone should avoid all outdoor physical activity.", 
     "Health warnings of emergency conditions. The entire population is more likely to be affected.", 
     "Remain indoors and keep activity levels low. Follow official health advice."),
    ("Extremely Hazardous",
     "Everyone should remain indoors and avoid all physical activity. Follow guidance from public health officials.",
     "Health warnings of emergency conditions. The entire population is at very high risk.",
     "Remain indoors, keep windows closed, use air purifiers if available, and minimize all physical activity. Follow official health advice strictly.")
]

# Copied from main.py for self-contained testing
def get_aqi_and_health_info(pm_value: float):
    if pm_value is None: # Explicit check for None
        return {
            'aqi': "Invalid PM2.5 value", 
            'category': "-", 'sensitive_group': "-", 
            'health_effect': "-", 'cautionary': "-"
        }
    if not isinstance(pm_value, (int, float)):
        try:
            pm_value = float(pm_value)
        except ValueError:
            return {
                'aqi': "Invalid PM2.5 value", 
                'category': "-", 'sensitive_group': "-", 
                'health_effect': "-", 'cautionary': "-"
            }

    if 0.0 <= pm_value <= 12.0:
        aqi = int(round((50.0 / 12.0) * pm_value))
        index = 0
    elif 12.0 < pm_value <= 35.4:
        aqi = int(round(((100.0 - 51.0) / (35.4 - 12.1)) * (pm_value - 12.1) + 51.0))
        index = 1
    elif 35.4 < pm_value <= 55.4:
        aqi = int(round(((150.0 - 101.0) / (55.4 - 35.5)) * (pm_value - 35.5) + 101.0))
        index = 2
    elif 55.4 < pm_value <= 150.4:
        aqi = int(round(((200.0 - 151.0) / (150.4 - 55.5)) * (pm_value - 55.5) + 151.0))
        index = 3
    elif 150.4 < pm_value <= 250.4:
        aqi = int(round(((300.0 - 201.0) / (250.4 - 150.5)) * (pm_value - 150.5) + 201.0))
        index = 4
    elif 250.4 < pm_value <= 350.4:
        aqi = int(round(((400.0 - 301.0) / (350.4 - 250.5)) * (pm_value - 250.5) + 301.0))
        index = 5
    elif 350.4 < pm_value <= 500.4: # Max defined AQI is 500
        aqi = int(round(((500.0 - 401.0) / (500.4 - 350.5)) * (pm_value - 350.5) + 401.0))
        index = 6 # Corresponds to "Extremely Hazardous" if we add that category
        if index >= len(HEALTH_RISKS_DATA): # Ensure index is within bounds
            index = len(HEALTH_RISKS_DATA) - 1
    else: # pm_value is < 0 or > 500.4
        return {
            'aqi': "PM2.5 value out of range (0-500.4 µg/m³).",
            'category': "-", 
            'sensitive_group': "-", 
            'health_effect': "-", 
            'cautionary': "-"
        }

    category, sensitive_group, health_effect, cautionary = HEALTH_RISKS_DATA[index]
    
    return {
        'aqi': aqi,
        'category': category,
        'sensitive_group': sensitive_group,
        'health_effect': health_effect,
        'cautionary': cautionary
    }

class TestAQICalculator(unittest.TestCase):

    def test_good_aqi_low(self):
        pm_value = 3.0 # Original default value
        result = get_aqi_and_health_info(pm_value)
        # Standard Python round(12.5) is 12 (rounds to nearest even number for .5 cases)
        self.assertEqual(result['aqi'], 12) 
        self.assertEqual(result['category'], "Good")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[0][1])
        self.assertEqual(result['health_effect'], HEALTH_RISKS_DATA[0][2])
        self.assertEqual(result['cautionary'], HEALTH_RISKS_DATA[0][3])

    def test_good_aqi_zero(self): # Test PM2.5 = 0
        pm_value = 0.0
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 0) 
        self.assertEqual(result['category'], "Good")

    def test_good_aqi_mid(self):
        pm_value = 10.0
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 42) # (50/12)*10 = 41.666..., round(41.666...) = 42
        self.assertEqual(result['category'], "Good")

    def test_good_aqi_boundary_high(self): # PM2.5 = 12.0, AQI should be 50
        pm_value = 12.0
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 50) # (50/12)*12 = 50
        self.assertEqual(result['category'], "Good")

    def test_moderate_aqi_boundary_low(self):
        pm_value = 12.1
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 51)
        self.assertEqual(result['category'], "Moderate")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[1][1])
        self.assertEqual(result['health_effect'], HEALTH_RISKS_DATA[1][2])
        self.assertEqual(result['cautionary'], HEALTH_RISKS_DATA[1][3])

    def test_moderate_aqi_mid(self):
        pm_value = 25.0
        # Ih = 100, Il = 51, BPh = 35.4, BPl = 12.1
        # AQI = ((100-51)/(35.4-12.1))*(25-12.1) + 51 
        # AQI = (49/23.3)*12.9 + 51 = 2.1029... * 12.9 + 51 = 27.128... + 51 = 78.128... -> round(78.128) = 78
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 78) 
        self.assertEqual(result['category'], "Moderate")

    def test_moderate_aqi_boundary_high(self): # PM2.5 = 35.4, AQI should be 100
        pm_value = 35.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 100)
        self.assertEqual(result['category'], "Moderate")

    def test_unhealthy_sensitive_boundary_low(self): # PM2.5 = 35.5, AQI should be 101
        pm_value = 35.5
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 101)
        self.assertEqual(result['category'], "Unhealthy for Sensitive Groups")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[2][1])

    def test_unhealthy_sensitive_mid(self):
        pm_value = 40.0
        # Ih = 150, Il = 101, BPh = 55.4, BPl = 35.5
        # AQI = ((150-101)/(55.4-35.5))*(40-35.5) + 101
        # AQI = (49/19.9)*4.5 + 101 = 2.4623... * 4.5 + 101 = 11.08... + 101 = 112.08... -> round(112.08) = 112
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 112) 
        self.assertEqual(result['category'], "Unhealthy for Sensitive Groups")

    def test_unhealthy_sensitive_boundary_high(self): # PM2.5 = 55.4, AQI should be 150
        pm_value = 55.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 150)
        self.assertEqual(result['category'], "Unhealthy for Sensitive Groups")

    def test_unhealthy_boundary_low(self): # PM2.5 = 55.5, AQI should be 151
        pm_value = 55.5
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 151)
        self.assertEqual(result['category'], "Unhealthy")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[3][1])

    def test_unhealthy_mid(self):
        pm_value = 100.0 
        # Ih = 200, Il = 151, BPh = 150.4, BPl = 55.5
        # AQI = ((200-151)/(150.4-55.5))*(100-55.5) + 151
        # AQI = (49/94.9)*44.5 + 151 = 0.51633...*44.5 + 151 = 22.975... + 151 = 173.975... -> round(173.975) = 174
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 174)
        self.assertEqual(result['category'], "Unhealthy")
        
    def test_unhealthy_boundary_high(self): # PM2.5 = 150.4, AQI should be 200
        pm_value = 150.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 200)
        self.assertEqual(result['category'], "Unhealthy")

    def test_very_unhealthy_boundary_low(self): # PM2.5 = 150.5, AQI should be 201
        pm_value = 150.5
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 201)
        self.assertEqual(result['category'], "Very Unhealthy")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[4][1])

    def test_very_unhealthy_mid(self):
        pm_value = 200.0 
        # Ih = 300, Il = 201, BPh = 250.4, BPl = 150.5
        # AQI = ((300-201)/(250.4-150.5))*(200-150.5) + 201
        # AQI = (99/99.9)*49.5 + 201 = 0.99099...*49.5 + 201 = 49.054... + 201 = 250.054... -> round(250.054) = 250
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 250)
        self.assertEqual(result['category'], "Very Unhealthy")

    def test_very_unhealthy_boundary_high(self): # PM2.5 = 250.4, AQI should be 300
        pm_value = 250.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 300)
        self.assertEqual(result['category'], "Very Unhealthy")

    def test_hazardous_boundary_low(self): # PM2.5 = 250.5, AQI should be 301
        pm_value = 250.5
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 301)
        self.assertEqual(result['category'], "Hazardous")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[5][1])

    def test_hazardous_mid(self):
        pm_value = 300.0 
        # Ih = 400, Il = 301, BPh = 350.4, BPl = 250.5
        # AQI = ((400-301)/(350.4-250.5))*(300-250.5) + 301
        # AQI = (99/99.9)*49.5 + 301 = 0.99099...*49.5 + 301 = 49.054... + 301 = 350.054... -> round(350.054) = 350
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 350)
        self.assertEqual(result['category'], "Hazardous")
        
    def test_hazardous_boundary_high(self): # PM2.5 = 350.4, AQI should be 400
        pm_value = 350.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 400)
        self.assertEqual(result['category'], "Hazardous")

    def test_extremely_hazardous_boundary_low(self): 
        pm_value = 350.5
        result = get_aqi_and_health_info(pm_value)
        # AQI = ((500-401)/(500.4-350.5))*(350.5-350.5) + 401 = 401
        self.assertEqual(result['aqi'], 401) 
        self.assertEqual(result['category'], "Extremely Hazardous")
        self.assertEqual(result['sensitive_group'], HEALTH_RISKS_DATA[6][1])

    def test_extremely_hazardous_mid(self): 
        pm_value = 420.0 
        # Ih = 500, Il = 401, BPh = 500.4, BPl = 350.5
        # AQI = ((500-401)/(500.4-350.5))*(420.0-350.5) + 401
        # AQI = (99/149.9)*69.5 + 401 = 0.66044029...*69.5 + 401 = 45.90059... + 401 = 446.90059... -> round(446.90059) = 447
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 447) 
        self.assertEqual(result['category'], "Extremely Hazardous")

    def test_extremely_hazardous_boundary_high(self): 
        pm_value = 500.4
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], 500)
        self.assertEqual(result['category'], "Extremely Hazardous")

    def test_out_of_range_high(self):
        pm_value = 500.5 
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], "PM2.5 value out of range (0-500.4 µg/m³).")
        self.assertEqual(result['category'], "-")
        self.assertEqual(result['sensitive_group'], "-")
        self.assertEqual(result['health_effect'], "-")
        self.assertEqual(result['cautionary'], "-")

    def test_out_of_range_low(self):
        pm_value = -1.0
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], "PM2.5 value out of range (0-500.4 µg/m³).")
        self.assertEqual(result['category'], "-")

    def test_invalid_input_type_string(self):
        pm_value = "not_a_number"
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], "Invalid PM2.5 value")
        self.assertEqual(result['category'], "-")
        
    def test_invalid_input_type_none(self):
        pm_value = None
        result = get_aqi_and_health_info(pm_value)
        self.assertEqual(result['aqi'], "Invalid PM2.5 value")
        self.assertEqual(result['category'], "-")

if __name__ == '__main__':
    unittest.main()
