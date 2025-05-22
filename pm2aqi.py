import sys
import asyncio
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QTextEdit, QGroupBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from dotenv import load_dotenv
from qasync import QEventLoop, asyncSlot

# Async helper for running blocking code in a thread
async def run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

class PM2AQIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PM2.5 to AQI Calculator (PyQt6)")
        self.setMinimumSize(500, 500)
        self.api_key = ""
        self.app_key = ""
        self.auto_refresh = False
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_and_update)
        self.api_fields_visible = True
        self.init_ui()
        self.load_api_keys()
        # Set window icon
        self.setWindowIcon(QIcon(os.path.join('assets', 'icon.ico')))

    def load_api_keys(self):
        load_dotenv()
        api_key = os.getenv('AMBIENT_API_KEY', '')
        app_key = os.getenv('AMBIENT_APP_KEY', '')
        if api_key and app_key:
            self.api_key_input.setText(api_key)
            self.app_key_input.setText(app_key)
            self.toggle_api_fields(False)
            self.api_group.setVisible(False)
            self.change_api_btn.setVisible(True)
            # Fetch data on startup if keys are present
            self.fetch_and_update()
        else:
            self.toggle_api_fields(True)
            self.api_group.setVisible(True)
            self.change_api_btn.setVisible(False)

    def toggle_api_fields(self, show):
        self.api_fields_visible = show
        self.api_key_input.setVisible(show)
        self.app_key_input.setVisible(show)
        self.api_key_label.setVisible(show)
        self.app_key_label.setVisible(show)
        self.save_api_btn.setVisible(show)
        self.change_api_btn.setVisible(not show)

    def save_api_keys(self):
        api_key = self.api_key_input.text().strip()
        app_key = self.app_key_input.text().strip()
        if not api_key or not app_key:
            self.weather_text.setText("Please enter both API Key and App Key.")
            return
        with open('.env', 'w') as f:
            f.write(f'AMBIENT_API_KEY={api_key}\n')
            f.write(f'AMBIENT_APP_KEY={app_key}\n')
        self.toggle_api_fields(False)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # API Key input (grouped)
        self.api_group = QGroupBox("API Keys")
        api_layout = QHBoxLayout()
        self.api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key")
        self.app_key_label = QLabel("App Key:")
        self.app_key_input = QLineEdit()
        self.app_key_input.setPlaceholderText("App Key")
        self.save_api_btn = QPushButton("Save API Keys")
        self.save_api_btn.clicked.connect(self.save_api_keys)
        self.change_api_btn = QPushButton("Change API Keys")
        self.change_api_btn.clicked.connect(lambda: self.show_api_fields())
        api_layout.addWidget(self.api_key_label)
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self.app_key_label)
        api_layout.addWidget(self.app_key_input)
        api_layout.addWidget(self.save_api_btn)
        self.api_group.setLayout(api_layout)
        layout.addWidget(self.api_group)
        layout.addWidget(self.change_api_btn)

        # PM2.5 input and buttons
        pm_group = QGroupBox("PM2.5 & AQI")
        pm_layout = QHBoxLayout()
        self.pm_input = QLineEdit()
        self.pm_input.setPlaceholderText("PM2.5 value (1-500)")
        pm_layout.addWidget(self.pm_input)
        self.calc_btn = QPushButton("Calculate AQI")
        self.calc_btn.clicked.connect(self.calculate_aqi)
        pm_layout.addWidget(self.calc_btn)
        self.fetch_btn = QPushButton("Fetch PM2.5 & Weather")
        self.fetch_btn.clicked.connect(self.fetch_and_update)
        pm_layout.addWidget(self.fetch_btn)
        pm_group.setLayout(pm_layout)
        layout.addWidget(pm_group)

        # Auto-refresh
        self.auto_refresh_check = QCheckBox("Auto-Refresh (every 60s)")
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_check)

        # AQI output (large badge)
        self.aqi_badge = QLabel("AQI: --")
        self.aqi_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aqi_badge.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        self.aqi_badge.setStyleSheet("border-radius: 16px; padding: 16px; background: #e0e0e0; color: #222;")
        layout.addWidget(self.aqi_badge)

        # Show AQI Details button
        self.show_aqi_details_btn = QPushButton("Show AQI Details")
        self.show_aqi_details_btn.setCheckable(True)
        self.show_aqi_details_btn.toggled.connect(self.toggle_aqi_details)
        layout.addWidget(self.show_aqi_details_btn)

        # AQI details (hidden by default)
        self.aqi_details_text = QTextEdit()
        self.aqi_details_text.setReadOnly(True)
        self.aqi_details_text.setVisible(False)
        self.aqi_details_text.setMaximumHeight(220)
        self.aqi_details_text.setStyleSheet("background: #f8f8f8; font-size: 12px;")
        layout.addWidget(self.aqi_details_text)

        # Weather summary (key stats) as 2x2 grid of blue bubbles
        summary_group = QGroupBox("Current Weather Summary")
        summary_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        bubble_style = (
            "border-radius: 16px; padding: 16px; background: #1976d2; color: #fff; "
            "font-size: 16px; min-width: 120px; min-height: 48px; text-align: center;"
        )
        self.o_temp_label = QLabel("Outdoor Temp: -- °F")
        self.o_temp_label.setFont(QFont("Arial", 16))
        self.o_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.o_temp_label.setStyleSheet(bubble_style)
        self.i_temp_label = QLabel("Indoor Temp: -- °F")
        self.i_temp_label.setFont(QFont("Arial", 16))
        self.i_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.i_temp_label.setStyleSheet(bubble_style)
        self.wind_label = QLabel("Wind: -- mph")
        self.wind_label.setFont(QFont("Arial", 16))
        self.wind_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wind_label.setStyleSheet(bubble_style)
        self.rain_label = QLabel("Rain: -- in")
        self.rain_label.setFont(QFont("Arial", 16))
        self.rain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rain_label.setStyleSheet(bubble_style)
        row1.addWidget(self.o_temp_label)
        row1.addWidget(self.i_temp_label)
        row2.addWidget(self.wind_label)
        row2.addWidget(self.rain_label)
        summary_layout.addLayout(row1)
        summary_layout.addLayout(row2)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Show More button for full weather details (centered)
        self.show_more_btn = QPushButton("Show More")
        self.show_more_btn.setCheckable(True)
        self.show_more_btn.toggled.connect(self.toggle_weather_details)
        show_more_layout = QHBoxLayout()
        show_more_layout.addStretch(1)
        show_more_layout.addWidget(self.show_more_btn)
        show_more_layout.addStretch(1)
        layout.addLayout(show_more_layout)

        # Weather details (hidden by default)
        self.weather_text = QTextEdit()
        self.weather_text.setReadOnly(True)
        self.weather_text.setVisible(False)
        self.weather_text.setMaximumHeight(200)
        self.weather_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.weather_text)

        self.setLayout(layout)

    def toggle_weather_details(self, checked):
        self.weather_text.setVisible(checked)
        self.show_more_btn.setText("Hide Details" if checked else "Show More")

    def toggle_aqi_details(self, checked):
        self.aqi_details_text.setVisible(checked)
        self.show_aqi_details_btn.setText("Hide AQI Details" if checked else "Show AQI Details")
        if checked:
            self.aqi_details_text.setText(self.get_aqi_details_text())

    def calculate_aqi(self):
        try:
            pm_value = float(self.pm_input.text())
            aqi, category, color = self.aqi_from_pm25(pm_value)
            self.aqi_badge.setText(f"AQI: {aqi}")
            self.aqi_badge.setStyleSheet(f"border-radius: 16px; padding: 16px; background: {color}; color: #fff;")
            # If AQI details are visible, update them immediately
            if self.aqi_details_text.isVisible():
                self.aqi_details_text.setText(self.get_aqi_details_text())
        except ValueError:
            self.aqi_badge.setText("Invalid input")
            self.aqi_badge.setStyleSheet("border-radius: 16px; padding: 16px; background: #e57373; color: #fff;")
            if self.aqi_details_text.isVisible():
                self.aqi_details_text.setText("No valid PM2.5 value.")

    def aqi_from_pm25(self, pm_value):
        # Returns (aqi, category, color)
        if 0 <= pm_value <= 12:
            aqi = int((50/12) * pm_value)
            return aqi, "Good", "#43a047"
        elif 12 < pm_value <= 35.4:
            aqi = int(((100-51)/(35.4-12.1)) * (pm_value-12.1) + 51)
            return aqi, "Moderate", "#fbc02d"
        elif 35.4 < pm_value <= 55.4:
            aqi = int(((150-101)/(55.4-35.5)) * (pm_value-35.5) + 101)
            return aqi, "Unhealthy for Sensitive Groups", "#fb8c00"
        elif 55.4 < pm_value <= 150.4:
            aqi = int(((200-151)/(150.4-55.5)) * (pm_value-55.5) + 151)
            return aqi, "Unhealthy", "#e53935"
        elif 150.4 < pm_value <= 250.4:
            aqi = int(((300-201)/(250.4-150.5)) * (pm_value-150.5) + 201)
            return aqi, "Very Unhealthy", "#8e24aa"
        elif 250.4 < pm_value <= 350.4:
            aqi = int(((400-301)/(350.4-250.5)) * (pm_value-250.5) + 301)
            return aqi, "Hazardous", "#6d4c41"
        elif 350.4 < pm_value <= 500.4:
            aqi = int(((500-401)/(500.4-350.5)) * (pm_value-350.5) + 401)
            return aqi, "Beyond AQI", "#212121"
        else:
            return "--", "Out of Range", "#e57373"

    def fetch_and_update(self):
        self.api_key = self.api_key_input.text().strip()
        self.app_key = self.app_key_input.text().strip()
        if not self.api_key or not self.app_key:
            self.weather_text.setText("Please enter both API Key and App Key.")
            return
        self.async_fetch()

    @asyncSlot()
    async def async_fetch(self):
        data, error = await run_in_executor(self.fetch_pm25_and_weather_from_ambient, self.api_key, self.app_key)
        if error:
            self.weather_text.setText(error)
        else:
            self.pm_input.setText(str(data.get('pm25', '')))
            self.update_summary(data)
            self.calculate_aqi()
            self.weather_text.setText(self.format_weather(data))
            # Removed PM2.5 plot

    def update_summary(self, data):
        self.o_temp_label.setText(f"Outdoor Temp: {data.get('tempf', '--')} °F")
        self.i_temp_label.setText(f"Indoor Temp: {data.get('tempinf', '--')} °F")
        self.wind_label.setText(f"Wind: {data.get('windspeedmph', '--')} mph")
        self.rain_label.setText(f"Rain: {data.get('dailyrainin', '--')} in")

    def fetch_pm25_and_weather_from_ambient(self, api_key, app_key):
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
            pm25 = last_data.get('pm25')
            if pm25 is None:
                pm25 = last_data.get('pm25_in')
            if pm25 is None:
                return None, "No PM2.5 data found."
            weather_data['pm25'] = pm25
            return weather_data, None
        except Exception as e:
            return None, f'Error fetching data: {e}'

    def format_weather(self, data):
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo  # Python 3.9+
            tz_pacific = ZoneInfo("America/Los_Angeles")
        except ImportError:
            from pytz import timezone, utc
            tz_pacific = timezone("US/Pacific")
        date_str = data.get('date', 'N/A')
        formatted_date = 'N/A'
        if date_str and date_str != 'N/A':
            try:
                # Parse as UTC
                dt_utc = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Convert to Pacific Time
                try:
                    # zoneinfo (Python 3.9+)
                    dt_pacific = dt_utc.astimezone(tz_pacific)
                except Exception:
                    # fallback for pytz
                    import pytz
                    dt_utc = dt_utc.replace(tzinfo=pytz.utc)
                    dt_pacific = dt_utc.astimezone(tz_pacific)
                formatted_date = dt_pacific.strftime('%Y-%m-%d %I:%M %p')
            except Exception:
                formatted_date = date_str
        items = [
            ("Date", formatted_date),
            ("Outdoor Temp", f"{data.get('tempf', 'N/A')} °F"),
            ("Outdoor Humidity", f"{data.get('humidity', 'N/A')}%"),
            ("Barometer (rel)", f"{data.get('baromrelin', 'N/A')} inHg"),
            ("Barometer (abs)", f"{data.get('baromabsin', 'N/A')} inHg"),
            ("Wind Speed", f"{data.get('windspeedmph', 'N/A')} mph"),
            ("Wind Gust", f"{data.get('windgustmph', 'N/A')} mph"),
            ("Wind Dir", f"{data.get('winddir', 'N/A')}°"),
            ("Max Daily Gust", f"{data.get('maxdailygust', 'N/A')} mph"),
            ("Rain (hour)", f"{data.get('hourlyrainin', 'N/A')} in"),
            ("Rain (day)", f"{data.get('dailyrainin', 'N/A')} in"),
            ("Rain (week)", f"{data.get('weeklyrainin', 'N/A')} in"),
            ("Rain (month)", f"{data.get('monthlyrainin', 'N/A')} in"),
            ("Rain (year)", f"{data.get('yearlyrainin', 'N/A')} in"),
            ("Solar Radiation", f"{data.get('solarradiation', 'N/A')} W/m²"),
            ("UV Index", f"{data.get('uv', 'N/A')}") ,
            ("Indoor Temp", f"{data.get('tempinf', 'N/A')} °F"),
            ("Indoor Humidity", f"{data.get('humidityin', 'N/A')}%"),
            ("Indoor PM2.5", f"{data.get('pm25_in', 'N/A')} μg/m³"),
            ("Indoor PM2.5 (24h avg)", f"{data.get('pm25_in_24h', 'N/A')} μg/m³"),
            ("Outdoor Feels Like", f"{data.get('feelsLike', 'N/A')} °F"),
            ("Outdoor Dew Point", f"{data.get('dewPoint', 'N/A')} °F"),
            ("Indoor Feels Like", f"{data.get('feelsLikein', 'N/A')} °F"),
            ("Indoor Dew Point", f"{data.get('dewPointin', 'N/A')} °F"),
        ]
        mid = (len(items) + 1) // 2
        col1 = items[:mid]
        col2 = items[mid:]
        lines = []
        for i in range(max(len(col1), len(col2))):
            left = f"{col1[i][0]}: {col1[i][1]}" if i < len(col1) else ""
            right = f"{col2[i][0]}: {col2[i][1]}" if i < len(col2) else ""
            lines.append(f"{left:<40}    {right:<40}")
        block = "\n".join(lines)
        # Center the block horizontally by adding spaces to each line
        max_line_length = max(len(line) for line in lines) if lines else 0
        pad = max(0, 20)
        centered_block = "\n".join([f"{'':<{pad}}{line}" for line in lines])
        return f"\n{centered_block}\n"

    def toggle_auto_refresh(self, state):
        if state == Qt.CheckState.Checked.value:
            self.auto_refresh = True
            self.refresh_timer.start(60000)
            self.fetch_and_update()
        else:
            self.auto_refresh = False
            self.refresh_timer.stop()

    def get_aqi_details_text(self):
        health_risks = [
            ("Good", "None", "No health implications.", "Everyone can continue their outdoor activities normally."),
            ("Moderate", "Extremely sensitive individuals", "May cause mild respiratory symptoms in extremely sensitive people.", "Good air quality is expected."),
            ("Unhealthy for Sensitive Groups", "People with respiratory or heart disease, the elderly and children", "Increasing likelihood of respiratory symptoms in sensitive individuals, aggravation of heart or lung disease and premature mortality in persons with cardiopulmonary disease and the elderly.", "People with respiratory or heart disease, the elderly and children should limit prolonged exertion."),
            ("Unhealthy", "Everyone may begin to experience health effects", "Increased respiratory symptom, reduced exercise tolerance in persons with heart or lung disease; increased likelihood of symptoms in sensitive individuals.", "People with heart or lung disease, children and older adults should limit prolonged outdoor exertion; everyone else should limit prolonged outdoor exertion."),
            ("Very Unhealthy", "People with respiratory or heart disease, the elderly and children", "Significant increase in respiratory symptoms and reduced exercise tolerance in persons with heart or lung disease; increased likelihood of symptoms in sensitive individuals.", "People with heart or lung disease, elderly, children and people of lower socioeconomic status should avoid all outdoor exertion; everyone else should limit outdoor exertion."),
            ("Hazardous", "The entire population", "Health alert: The risk of health effects is increased for everyone.", "Everyone should avoid all outdoor exertion."),
            ("Beyond AQI", "The entire population", "Health warnings of emergency conditions. The entire population is more likely to be affected.", "Everyone should avoid all physical activity outdoors.")
        ]
        # Determine current AQI and select the correct category
        try:
            pm_value = float(self.pm_input.text())
        except ValueError:
            return "No valid PM2.5 value."
        # Find the index as in aqi_from_pm25
        if 0 <= pm_value <= 12:
            idx = 0
        elif 12 < pm_value <= 35.4:
            idx = 1
        elif 35.4 < pm_value <= 55.4:
            idx = 2
        elif 55.4 < pm_value <= 150.4:
            idx = 3
        elif 150.4 < pm_value <= 250.4:
            idx = 4
        elif 250.4 < pm_value <= 350.4:
            idx = 5
        elif 350.4 < pm_value <= 500.4:
            idx = 6
        else:
            return "AQI out of range."
        cat, group, effect, caution = health_risks[idx]
        return f"Category: {cat}\nSensitive Groups: {group}\nHealth Effects Statement: {effect}\nCautionary Statements: {caution}\n"

    def show_api_fields(self):
        self.toggle_api_fields(True)
        self.api_group.setVisible(True)
        self.change_api_btn.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = PM2AQIApp()
    window.show()
    with loop:
        loop.run_forever()