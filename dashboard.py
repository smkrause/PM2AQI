import sys
import os
import asyncio
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
import requests
from dotenv import load_dotenv
from qasync import QEventLoop, asyncSlot

# Helper for running blocking code in a thread
async def run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ambient Weather Station Dashboard")
        self.setMinimumSize(800, 350)
        self.setStyleSheet("background: #181818; color: #fff;")
        self.api_key = ""
        self.app_key = ""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_and_update)
        self.init_ui()
        self.load_api_keys()
        self.refresh_timer.start(60000)  # Refresh every 60 seconds

    def load_api_keys(self):
        load_dotenv()
        self.api_key = os.getenv('AMBIENT_API_KEY', '')
        self.app_key = os.getenv('AMBIENT_APP_KEY', '')
        if self.api_key and self.app_key:
            self.fetch_and_update()

    def init_ui(self):
        font_large = QFont("Arial", 36, QFont.Weight.Bold)
        font_med = QFont("Arial", 24, QFont.Weight.Bold)
        font_small = QFont("Arial", 16)
        font_xsmall = QFont("Arial", 12)

        main_layout = QGridLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # PM2.5 and AQI widgets (top row)
        pm_aqi_frame = QFrame()
        pm_aqi_frame.setStyleSheet("background: #181818; border: none;")
        pm_aqi_layout = QHBoxLayout()
        pm_aqi_layout.setContentsMargins(0, 0, 0, 0)
        pm_aqi_layout.setSpacing(24)
        self.pm25_widget = QLabel("PM2.5: -- μg/m³")
        self.pm25_widget.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.pm25_widget.setStyleSheet("color: #4fc3f7; padding: 4px 16px 4px 4px;")
        self.aqi_widget = QLabel("AQI: --")
        self.aqi_widget.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.aqi_widget.setStyleSheet("color: #fff; padding: 4px 4px 4px 16px;")
        pm_aqi_layout.addWidget(self.pm25_widget)
        pm_aqi_layout.addWidget(self.aqi_widget)
        pm_aqi_layout.addStretch()
        pm_aqi_frame.setLayout(pm_aqi_layout)
        main_layout.addWidget(pm_aqi_frame, 0, 0, 1, 2)

        # WIND (Gust) -> WIND
        wind_frame = QFrame()
        wind_frame.setStyleSheet("background: #222; border-radius: 8px;")
        wind_layout = QVBoxLayout()
        wind_label = QLabel("WIND")
        wind_label.setFont(font_xsmall)
        wind_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        wind_label.setStyleSheet("color: #fff;")
        self.wind_speed = QLabel("7.8")
        self.wind_speed.setFont(font_large)
        self.wind_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wind_speed.setStyleSheet("color: #ffe082;")
        wind_unit = QLabel("mph")
        wind_unit.setFont(font_small)
        wind_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wind_unit.setStyleSheet("color: #ffe082;")
        wind_layout.addWidget(wind_label)
        wind_layout.addWidget(self.wind_speed)
        wind_layout.addWidget(wind_unit)
        wind_frame.setLayout(wind_layout)
        main_layout.addWidget(wind_frame, 1, 0, 1, 1)

        # OUTDOOR (Temp & Humidity)
        outdoor_frame = QFrame()
        outdoor_frame.setStyleSheet("background: #222; border-radius: 8px;")
        outdoor_layout = QVBoxLayout()
        outdoor_layout.setContentsMargins(0, 0, 0, 0)
        outdoor_layout.setSpacing(0)
        outdoor_label = QLabel("OUTDOOR")
        outdoor_label.setFont(font_xsmall)
        outdoor_label.setStyleSheet("color: #fff;")
        outdoor_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.out_temp = QLabel("78.5 °F")
        self.out_temp.setFont(font_large)
        self.out_temp.setStyleSheet("color: #fff;")
        self.out_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.out_hum = QLabel("58%")
        self.out_hum.setFont(font_large)
        self.out_hum.setStyleSheet("color: #fff;")
        self.out_hum.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outdoor_layout.addWidget(outdoor_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        outdoor_layout.addSpacing(2)
        outdoor_layout.addWidget(self.out_temp, alignment=Qt.AlignmentFlag.AlignCenter)
        outdoor_layout.addWidget(self.out_hum, alignment=Qt.AlignmentFlag.AlignCenter)
        outdoor_frame.setLayout(outdoor_layout)
        main_layout.addWidget(outdoor_frame, 1, 1, 1, 1)

        # RAIN (blue, below wind)
        rain_frame = QFrame()
        rain_frame.setStyleSheet("background: #181818;")
        rain_layout = QVBoxLayout()
        rain_label = QLabel("RAIN")
        rain_label.setFont(font_xsmall)
        rain_label.setStyleSheet("color: #4fc3f7;")
        rain_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        rain_value_unit = QLabel("0.56 in")
        rain_value_unit.setFont(font_large)
        rain_value_unit.setStyleSheet("color: #4fc3f7;")
        rain_value_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rain_value_unit = rain_value_unit
        rain_layout.addWidget(rain_label)
        rain_layout.addWidget(rain_value_unit)
        rain_frame.setLayout(rain_layout)
        main_layout.addWidget(rain_frame, 2, 0, 1, 1)

        # INDOOR (Temp & Humidity, orange)
        indoor_frame = QFrame()
        indoor_frame.setStyleSheet("background: #222; border-radius: 8px;")
        indoor_layout = QVBoxLayout()
        indoor_label = QLabel("INDOOR")
        indoor_label.setFont(font_xsmall)
        indoor_label.setStyleSheet("color: #ffb74d;")
        self.in_temp = QLabel("79.8 °F")
        self.in_temp.setFont(font_large)
        self.in_temp.setStyleSheet("color: #ffb74d;")
        self.in_hum = QLabel("52%")
        self.in_hum.setFont(font_large)
        self.in_hum.setStyleSheet("color: #ffb74d;")
        indoor_layout.addWidget(indoor_label)
        indoor_layout.addWidget(self.in_temp)
        indoor_layout.addWidget(self.in_hum, alignment=Qt.AlignmentFlag.AlignCenter)
        indoor_frame.setLayout(indoor_layout)
        main_layout.addWidget(indoor_frame, 2, 1, 1, 1)

        # TIME, DAY, DATE (yellow)
        time_frame = QFrame()
        time_frame.setStyleSheet("background: #181818;")
        time_layout = QVBoxLayout()
        self.time_date_label = QLabel("1:57 Thu 05.22")
        self.time_date_label.setFont(QFont("Arial", 35, QFont.Weight.Bold))
        self.time_date_label.setStyleSheet("color: #ffe082;")
        self.time_date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_layout.addWidget(self.time_date_label)
        time_frame.setLayout(time_layout)
        main_layout.addWidget(time_frame, 0, 2, 1, 2)

        # FORECAST ICON (centered, placeholder)
        forecast_frame = QFrame()
        forecast_frame.setStyleSheet("background: #222; border-radius: 8px;")
        forecast_layout = QVBoxLayout()
        forecast_label = QLabel("FORECAST")
        forecast_label.setFont(font_xsmall)
        forecast_label.setStyleSheet("color: #fff;")
        self.forecast_icon = QLabel()
        self.forecast_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Placeholder: use a cloud emoji for now
        self.forecast_icon.setText("☁️")
        self.forecast_icon.setFont(QFont("Arial", 40))
        forecast_layout.addWidget(forecast_label)
        forecast_layout.addWidget(self.forecast_icon)
        forecast_frame.setLayout(forecast_layout)
        main_layout.addWidget(forecast_frame, 1, 2, 1, 1)

        # PRESSURE (right of forecast)
        pressure_frame = QFrame()
        pressure_frame.setStyleSheet("background: #222; border-radius: 8px;")
        pressure_layout = QVBoxLayout()
        pressure_label = QLabel("PRESSURE")
        pressure_label.setFont(font_xsmall)
        pressure_label.setStyleSheet("color: #fff;")
        self.pressure_value = QLabel("29.91")
        self.pressure_value.setFont(font_large)
        self.pressure_value.setStyleSheet("color: #fff;")
        pressure_unit = QLabel("inHg")
        pressure_unit.setFont(font_small)
        pressure_unit.setStyleSheet("color: #fff;")
        pressure_layout.addWidget(pressure_label)
        pressure_layout.addWidget(self.pressure_value)
        pressure_layout.addWidget(pressure_unit)
        pressure_frame.setLayout(pressure_layout)
        main_layout.addWidget(pressure_frame, 1, 3, 1, 1)

        # UV INDEX (bottom left of forecast)
        uv_frame = QFrame()
        uv_frame.setStyleSheet("background: #181818;")
        uv_layout = QVBoxLayout()
        uv_label = QLabel("UVI")
        uv_label.setFont(font_xsmall)
        uv_label.setStyleSheet("color: #fff;")
        uv_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.uv_value = QLabel("1")
        self.uv_value.setFont(font_large)
        self.uv_value.setStyleSheet("color: #fff;")
        self.uv_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uv_level = QLabel("LOW")
        self.uv_level.setFont(font_small)
        self.uv_level.setStyleSheet("color: #fff;")
        self.uv_level.setAlignment(Qt.AlignmentFlag.AlignCenter)
        uv_layout.addWidget(uv_label)
        uv_layout.addWidget(self.uv_value)
        uv_layout.addWidget(self.uv_level)
        uv_frame.setLayout(uv_layout)
        main_layout.addWidget(uv_frame, 2, 2, 1, 1)

        # LIGHT (bottom right of pressure)
        light_frame = QFrame()
        light_frame.setStyleSheet("background: #181818;")
        light_layout = QVBoxLayout()
        light_label = QLabel("LIGHT")
        light_label.setFont(font_xsmall)
        light_label.setStyleSheet("color: #fff;")
        self.light_value = QLabel("286")
        self.light_value.setFont(font_large)
        self.light_value.setStyleSheet("color: #fff;")
        light_unit = QLabel("W/m²")
        light_unit.setFont(font_small)
        light_unit.setStyleSheet("color: #fff;")
        light_layout.addWidget(light_label)
        light_layout.addWidget(self.light_value)
        light_layout.addWidget(light_unit)
        light_frame.setLayout(light_layout)
        main_layout.addWidget(light_frame, 2, 3, 1, 1)

        self.setLayout(main_layout)

    def fetch_and_update(self):
        self.async_fetch()

    @asyncSlot()
    async def async_fetch(self):
        data, error = await run_in_executor(self.fetch_weather_from_ambient, self.api_key, self.app_key)
        if error:
            return
        # Update UI with data
        self.wind_speed.setText(str(data.get('windspeedmph', '--')))
        self.rain_value_unit.setText(f"{data.get('dailyrainin', '--')} in")
        self.out_temp.setText(f"{data.get('tempf', '--')} °F")
        self.out_hum.setText(f"{data.get('humidity', '--')}%")
        self.in_temp.setText(f"{data.get('tempinf', '--')} °F")
        self.in_hum.setText(f"{data.get('humidityin', '--')}%")
        self.pressure_value.setText(str(data.get('baromrelin', '--')))
        self.uv_value.setText(str(data.get('uv', '--')))
        # Set UVI level text
        try:
            uvi = float(data.get('uv', 0))
            if uvi < 3:
                level = "LOW"
            elif uvi < 6:
                level = "MODERATE"
            elif uvi < 8:
                level = "HIGH"
            elif uvi < 11:
                level = "VERY HIGH"
            else:
                level = "EXTREME"
            self.uv_level.setText(level)
        except Exception:
            self.uv_level.setText("--")
        self.light_value.setText(str(data.get('solarradiation', '--')))        # PM2.5 and AQI update
        pm25 = data.get('pm25', None)
        if pm25 is None or pm25 == '--':
            pm25 = data.get('pm25_in', '--')
        self.pm25_widget.setText(f"PM2.5: {pm25} μg/m³")
        try:
            pm25_val = float(pm25)
            aqi = self.aqi_from_pm25(pm25_val)
            self.aqi_widget.setText(f"AQI: {aqi}")
        except Exception:
            self.aqi_widget.setText("AQI: --")
        # Forecast icon (simple mapping)
        forecast = data.get('weather', 'cloudy')
        icon_map = {
            'cloudy': '☁️',
            'sunny': '☀️',
            'rain': '🌧️',
            'snow': '❄️',
            'partlycloudy': '⛅',
        }
        self.forecast_icon.setText(icon_map.get(forecast, '☁️'))
        # Time and date (single line, always current local time)
        from datetime import datetime
        import time as _time
        try:
            from zoneinfo import ZoneInfo
            tz_pacific = ZoneInfo("America/Los_Angeles")
        except ImportError:
            from pytz import timezone
            tz_pacific = timezone("US/Pacific")
        now = datetime.now(tz_pacific)
        # Use platform-independent hour formatting (no leading zero, no '-')
        hour = now.strftime('%I').lstrip('0') or '0'
        minute = now.strftime('%M')
        ampm = now.strftime('%p')
        ampm = '' if ampm == 'AM' else 'p'
        time_str = f"{hour}:{minute}{ampm} {now.strftime('%a %m.%d')}"
        self.time_date_label.setText(time_str)

    def fetch_weather_from_ambient(self, api_key, app_key):
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
            # Improved current conditions logic for icon:
            tempf = last_data.get('tempf', 40)
            rain_rate = last_data.get('hourlyrainin', 0)
            daily_rain = last_data.get('dailyrainin', 0)
            solarrad = last_data.get('solarradiation', 0)
            # Default
            weather = 'cloudy'
            # If it's raining (rain rate or daily rain just increased)
            if rain_rate > 0.01:
                # If cold enough, show snow
                if tempf <= 34:
                    weather = 'snow'
                else:
                    weather = 'rain'
            # If not raining, check for snow (below freezing, some rain)
            elif tempf <= 34 and (rain_rate > 0 or daily_rain > 0):
                weather = 'snow'
            # If not raining or snowing, check for sun/partly/cloudy
            elif solarrad > 600:
                weather = 'sunny'
            elif solarrad > 200:
                weather = 'partlycloudy'
            else:
                weather = 'cloudy'
            last_data['weather'] = weather
            return last_data, None
        except Exception as e:
            return None, f'Error fetching data: {e}'

    def aqi_from_pm25(self, pm_value):
        # Returns AQI as int (US EPA breakpoints)
        if 0 <= pm_value <= 12:
            return int((50/12) * pm_value)
        elif 12 < pm_value <= 35.4:
            return int(((100-51)/(35.4-12.1)) * (pm_value-12.1) + 51)
        elif 35.4 < pm_value <= 55.4:
            return int(((150-101)/(55.4-35.5)) * (pm_value-35.5) + 101)
        elif 55.4 < pm_value <= 150.4:
            return int(((200-151)/(150.4-55.5)) * (pm_value-55.5) + 151)
        elif 150.4 < pm_value <= 250.4:
            return int(((300-201)/(250.4-150.5)) * (pm_value-150.5) + 201)
        elif 250.4 < pm_value <= 350.4:
            return int(((400-301)/(350.4-250.5)) * (pm_value-250.5) + 301)
        elif 350.4 < pm_value <= 500.4:
            return int(((500-401)/(500.4-350.5)) * (pm_value-350.5) + 401)
        else:
            return 500

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = Dashboard()
    window.show()
    with loop:
        loop.run_forever()
