import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox
import requests
import os

# Function to fetch latest PM2.5 and weather data from Ambient Weather REST API

def fetch_pm25_and_weather_from_ambient(api_key, app_key):
    try:
        url = f"https://rt.ambientweather.net/v1/devices?apiKey={api_key}&applicationKey={app_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return None, f"API error: {response.status_code}"
        devices = response.json()
        if not devices:
            return None, "No devices found."
        device = devices[0]
        last_data = device.get('lastData', {})
        # Extract all relevant fields
        weather_data = {
            'date': last_data.get('date'),
            'tempf': last_data.get('tempf'),
            'humidity': last_data.get('humidity'),
            'baromrelin': last_data.get('baromrelin'),
            'baromabsin': last_data.get('baromabsin'),
            'windspeedmph': last_data.get('windspeedmph'),
            'windgustmph': last_data.get('windgustmph'),
            'winddir': last_data.get('winddir'),
            'maxdailygust': last_data.get('maxdailygust'),
            'hourlyrainin': last_data.get('hourlyrainin'),
            'dailyrainin': last_data.get('dailyrainin'),
            'weeklyrainin': last_data.get('weeklyrainin'),
            'monthlyrainin': last_data.get('monthlyrainin'),
            'yearlyrainin': last_data.get('yearlyrainin'),
            'solarradiation': last_data.get('solarradiation'),
            'uv': last_data.get('uv'),
            'tempinf': last_data.get('tempinf'),
            'humidityin': last_data.get('humidityin'),
            'pm25_in': last_data.get('pm25_in'),
            'pm25_in_24h': last_data.get('pm25_in_24h'),
            'feelsLike': last_data.get('feelsLike'),
            'dewPoint': last_data.get('dewPoint'),
            'feelsLikein': last_data.get('feelsLikein'),
            'dewPointin': last_data.get('dewPointin'),
        }
        # Try both 'pm25' and 'pm25_in' keys for AQI
        pm25 = last_data.get('pm25')
        if pm25 is None:
            pm25 = last_data.get('pm25_in')
        if pm25 is None:
            return None, "No PM2.5 data found."
        weather_data['pm25'] = pm25
        return weather_data, None
    except Exception as e:
        return None, f'Error fetching data: {e}'

# Health risk information
health_risks = [
    ("Good", "None", "No health implications.", "Everyone can continue their outdoor activities normally."),
    ("Moderate", "Extremely sensitive individuals", "May cause mild respiratory symptoms in extremely sensitive people.", "Good air quality is expected."),
    ("Unhealthy for Sensitive Groups", "People with respiratory or heart disease, the elderly and children", "Increasing likelihood of respiratory symptoms in sensitive individuals, aggravation of heart or lung disease and premature mortality in persons with cardiopulmonary disease and the elderly.", "People with respiratory or heart disease, the elderly and children should limit prolonged exertion."),
    ("Unhealthy", "Everyone may begin to experience health effects", "Increased respiratory symptom, reduced exercise tolerance in persons with heart or lung disease; increased likelihood of symptoms in sensitive individuals.", "People with heart or lung disease, children and older adults should limit prolonged outdoor exertion; everyone else should limit prolonged outdoor exertion."),
    ("Very Unhealthy", "People with respiratory or heart disease, the elderly and children", "Significant increase in respiratory symptoms and reduced exercise tolerance in persons with heart or lung disease; increased likelihood of symptoms in sensitive individuals.", "People with heart or lung disease, elderly, children and people of lower socioeconomic status should avoid all outdoor exertion; everyone else should limit outdoor exertion."),
    ("Hazardous", "The entire population", "Health alert: The risk of health effects is increased for everyone.", "Everyone should avoid all outdoor exertion."),
    ("Beyond AQI", "The entire population", "Health warnings of emergency conditions. The entire population is more likely to be affected.", "Everyone should avoid all physical activity outdoors.")
]

# Function to calculate AQI based on the input PM2.5 value
def calculate_aqi(pm_value):
    try:
        pm_value = float(pm_value)
        # Determining the AQI based on PM2.5 concentration
        if 0 <= pm_value <= 12:
            aqi = int((50/12) * pm_value)
            index = 0
        elif 12 < pm_value <= 35.4:
            aqi = int(((100-51)/(35.4-12.1)) * (pm_value-12.1) + 51)
            index = 1
        elif 35.4 < pm_value <= 55.4:
            aqi = int(((150-101)/(55.4-35.5)) * (pm_value-35.5) + 101)
            index = 2
        elif 55.4 < pm_value <= 150.4:
            aqi = int(((200-151)/(150.4-55.5)) * (pm_value-55.5) + 151)
            index = 3
        elif 150.4 < pm_value <= 250.4:
            aqi = int(((300-201)/(250.4-150.5)) * (pm_value-150.5) + 201)
            index = 4
        elif 250.4 < pm_value <= 350.4:
            aqi = int(((400-301)/(350.4-250.5)) * (pm_value-250.5) + 301)
            index = 5
        elif 350.4 < pm_value <= 500.4:
            aqi = int(((500-401)/(500.4-350.5)) * (pm_value-350.5) + 401)
            index = 6
        else:
            return "PM2.5 value out of range (1-500)."
        # Getting health risk information
        category, sensitive_group, health_effect, cautionary = health_risks[index]
        # Creating the output string (single spaced)
        result = f"Category: {category}\n"
        result += f"Sensitive Groups: {sensitive_group}\n"
        result += f"Health Effects Statement: {health_effect}\n"
        result += f"Cautionary Statements: {cautionary}"
        return result
    except ValueError:
        return "Invalid input. Please enter a number."

def save_api_keys(api_key, app_key):
    if not api_key or not app_key:
        return "Please enter both API Key and App Key before saving."
    try:
        with open('.env', 'w') as f:
            f.write(f'AMBIENT_API_KEY={api_key}\n')
            f.write(f'AMBIENT_APP_KEY={app_key}\n')
        return "API Key and App Key saved to .env."
    except Exception as e:
        return f"Failed to save keys: {e}"

def load_api_keys_from_env():
    api_key = None
    app_key = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('AMBIENT_API_KEY='):
                    api_key = line.strip().split('=', 1)[1]
                elif line.startswith('AMBIENT_APP_KEY='):
                    app_key = line.strip().split('=', 1)[1]
    return api_key, app_key

class PM25AQIApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(PM25AQIApp, self).__init__()
        uic.loadUi('design.ui', self)

        # Connect buttons and actions
        self.pushButton_calculate.clicked.connect(self.calculate_aqi)
        self.pushButton_fetch.clicked.connect(self.fetch_and_set_pm25_and_weather)
        self.pushButton_save_api.clicked.connect(self.save_api_keys)

        # Initialize variables
        self.auto_refresh = False
        self.auto_refresh_timer = None

        # Load API keys from .env on startup
        self.load_api_keys()

    def calculate_aqi(self):
        pm_value = self.lineEdit_pm.text()
        aqi_result = calculate_aqi(pm_value)
        self.label_aqi_result.setText(aqi_result)

    def save_api_keys(self):
        api_key = self.lineEdit_api_key.text().strip()
        app_key = self.lineEdit_app_key.text().strip()
        message = save_api_keys(api_key, app_key)
        QMessageBox.information(self, "Save API Keys", message)

    def load_api_keys(self):
        api_key, app_key = load_api_keys_from_env()
        if api_key and app_key:
            self.lineEdit_api_key.setText(api_key)
            self.lineEdit_app_key.setText(app_key)
            # Optionally, hide API key fields if needed
            self.groupBox_api_keys.setVisible(False)

    def fetch_and_set_pm25_and_weather(self):
        api_key = self.lineEdit_api_key.text().strip()
        app_key = self.lineEdit_app_key.text().strip()
        if not api_key or not app_key:
            self.label_aqi_result.setText("Please enter both API Key and App Key.")
            return
        weather_data, error = fetch_pm25_and_weather_from_ambient(api_key, app_key)
        if error:
            self.label_aqi_result.setText(error)
        else:
            pm25_value = weather_data.get('pm25', '')
            self.lineEdit_pm.setText(str(pm25_value))
            aqi_result = calculate_aqi(pm25_value)
            self.label_aqi_result.setText(aqi_result)
            # Update weather labels
            self.label_weather_date.setText(f"Date: {weather_data.get('date', 'N/A')}")
            self.label_weather_temp.setText(f"Outdoor Temp: {weather_data.get('tempf', 'N/A')} °F")
            self.label_weather_humidity.setText(f"Outdoor Humidity: {weather_data.get('humidity', 'N/A')}%")
            # ... (set other weather labels similarly)

    def toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.schedule_auto_refresh()
        else:
            if self.auto_refresh_timer:
                self.auto_refresh_timer.stop()
                self.auto_refresh_timer = None

    def schedule_auto_refresh(self):
        self.fetch_and_set_pm25_and_weather()
        self.auto_refresh_timer = QtCore.QTimer.singleShot(60000, self.schedule_auto_refresh)  # 60 seconds

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PM25AQIApp()
    window.show()
    sys.exit(app.exec())