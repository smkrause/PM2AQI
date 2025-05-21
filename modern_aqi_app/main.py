import flet as ft
from ambient_api.ambientapi import AmbientAPI
import time
import os
import collections
import configparser
from requests.exceptions import ConnectionError as RequestsConnectionError # For specific error handling

api_client = None
CONFIG_FILE = 'config.ini'

# Health Risk Data (Copied from pm2aqi.py)
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

def get_aqi_and_health_info(pm_value: float):
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

def main(page: ft.Page):
    page.title = "Modern PM2.5 to AQI Calculator"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Center content horizontally

    # --- Chart Data Storage ---
    chart_data = collections.deque(maxlen=20) 
    current_x_value = 0
    auto_refresh_timer = None # For page.run_every

    # --- Configuration Handling ---
    def save_api_keys_to_config(api_key, app_key):
        config = configparser.ConfigParser()
        config['AmbientWeather'] = {
            'api_key': api_key,
            'app_key': app_key
        }
        try:
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
        except IOError as e:
            status_bar.value = f"Error saving keys to config: {e}"
            page.update()
            # Re-raise or handle as appropriate for your app's error strategy
            # For now, just showing in status bar.

    def load_api_keys_from_config():
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            try:
                config.read(CONFIG_FILE)
                api_key = config.get('AmbientWeather', 'api_key', fallback=None)
                app_key = config.get('AmbientWeather', 'app_key', fallback=None)
                return api_key, app_key
            except (configparser.Error, IOError) as e:
                # Handle error reading file or bad format
                status_bar.value = f"Error reading config: {e}"
                page.update()
                return None, None
        return None, None

    # --- UI Elements ---
    api_key_field = ft.TextField(label="Ambient Weather API Key", password=True, can_reveal_password=True)
    app_key_field = ft.TextField(label="Ambient Weather Application Key", password=True, can_reveal_password=True)
    save_keys_checkbox = ft.Checkbox(label="Save Keys for Next Session")
    status_bar = ft.Text("")

    def attempt_auto_load_keys():
        # Called after UI elements are defined
        loaded_api, loaded_app = load_api_keys_from_config()
        if loaded_api and loaded_app:
            api_key_field.value = loaded_api
            app_key_field.value = loaded_app
            save_keys_checkbox.value = True # Assume if loaded, user wants to keep them saved
            status_bar.value = "API keys loaded from config. Click 'Load/Set Keys' to connect."
            page.update()
            # Optionally, directly call load_set_keys if you want to auto-connect
            # load_set_keys(None) # Be mindful of user experience if this auto-connects
            
    def load_set_keys(e):
        global api_client
        api_key = api_key_field.value
        app_key = app_key_field.value

        if not api_key or not app_key:
            status_bar.value = "API Key and Application Key are required."
            page.update()
            return

        try:
            status_bar.value = "Connecting to Ambient Weather..."
            page.update()
            
            # Set environment variables for AmbientAPI library as it seems to prefer them
            os.environ['AMBIENT_API_KEY'] = api_key
            os.environ['AMBIENT_APPLICATION_KEY'] = app_key
            
            temp_api_client = AmbientAPI() # Initialize temporarily
            devices = temp_api_client.get_devices() # Test call
            
            if not devices:
                status_bar.value = "Successfully connected, but no devices found on your account."
                api_client = None 
            else:
                api_client = temp_api_client # Assign to global if successful
                status_bar.value = f"API keys loaded. Found {len(devices)} device(s)."
                if save_keys_checkbox.value:
                    try:
                        save_api_keys_to_config(api_key, app_key)
                        status_bar.value += " Keys saved."
                    except Exception as ex_save:
                        status_bar.value += f" Error saving keys: {ex_save}"
        except RequestsConnectionError:
            status_bar.value = "Network error. Please check your internet connection."
            api_client = None
        except Exception as ex: # Catch other exceptions from AmbientAPI or get_devices
            status_bar.value = f"Error: Could not connect. Verify keys or API service status. ({type(ex).__name__})"
            api_client = None
        finally:
            # Clean up environment variables
            if 'AMBIENT_API_KEY' in os.environ: del os.environ['AMBIENT_API_KEY']
            if 'AMBIENT_APPLICATION_KEY' in os.environ: del os.environ['AMBIENT_APPLICATION_KEY']
        page.update()

    load_set_button = ft.ElevatedButton(text="Load/Set Keys", on_click=load_set_keys, icon=ft.icons.CLOUD_UPLOAD_OUTLINED)
    
    # --- Auto-Refresh Controls ---
    auto_refresh_switch = ft.Switch(label="Auto-refresh:", value=False)
    refresh_interval_field = ft.TextField(label="Interval (min)", width=100, value="10", disabled=True)

    def auto_refresh_change(e):
        nonlocal auto_refresh_timer
        refresh_interval_field.disabled = not auto_refresh_switch.value
        if auto_refresh_switch.value:
            try:
                interval_minutes = int(refresh_interval_field.value)
                if interval_minutes <= 0:
                    raise ValueError("Interval must be positive.")
                # Flet's page.run_every expects seconds
                page.run_every(lambda: refresh_data(None), interval_minutes * 60)
                status_bar.value = f"Auto-refresh enabled every {interval_minutes} minutes."
            except ValueError:
                status_bar.value = "Invalid refresh interval. Please enter a positive number."
                auto_refresh_switch.value = False # Turn off if interval is bad
                refresh_interval_field.disabled = True
        else:
            if page.task_exists(lambda: refresh_data(None)): # Check if task exists before trying to remove
                 page.stop_tasks(lambda: refresh_data(None))
            status_bar.value = "Auto-refresh disabled."
        page.update()

    auto_refresh_switch.on_change = auto_refresh_change


    api_key_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("API Configuration", style=ft.TextThemeStyle.HEADLINE_SMALL),
                api_key_field,
                app_key_field,
                save_keys_checkbox,
                load_set_button,
                ft.Row([auto_refresh_switch, refresh_interval_field], alignment=ft.MainAxisAlignment.START),
                status_bar,
            ], spacing=10),
            padding=10, width=450
        )
    )

    # --- Data Display ---
    pm25_display = ft.Text("PM2.5: -- µg/m³", size=18)
    aqi_display = ft.Text("AQI: --", size=18, weight=ft.FontWeight.BOLD)
    
    data_display_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Current Readings", style=ft.TextThemeStyle.HEADLINE_SMALL),
                pm25_display,
                aqi_display,
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, width=450
        )
    )

    # --- Health Info ---
    health_info_display = ft.Text("Health information will appear here.", size=14, text_align=ft.TextAlign.CENTER)
    health_info_container = ft.Container(
        content=health_info_display,
        padding=15,
        border=ft.border.all(1, ft.colors.with_opacity(0.5, ft.colors.OUTLINE)), # Softer border
        border_radius=8,
        width=430 # Slightly less than card width for padding effect
    )

    health_display_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                 ft.Text("Health Advisory", style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER),
                 health_info_container
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, width=450
        )
    )
    
    # --- Chart UI Element ---
    pm25_chart = ft.LineChart(
        tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY_700), # Darker tooltip
        expand=True,
        left_axis=ft.ChartAxis(title=ft.Text("PM2.5 (µg/m³)"), show_labels=True, title_size=12, labels_size=10),
        bottom_axis=ft.ChartAxis(title=ft.Text("Reading Sequence"), show_labels=True, title_size=12, labels_size=10),
        data_series=[], 
        border=ft.border.all(1, ft.colors.with_opacity(0.5, ft.colors.OUTLINE)), # Chart border
        horizontal_grid_lines=ft.ChartGridLines(interval=10, color=ft.colors.with_opacity(0.2, ft.colors.ON_SURFACE)), # Grid lines
        vertical_grid_lines=ft.ChartGridLines(interval=1, color=ft.colors.with_opacity(0.2, ft.colors.ON_SURFACE)), # Grid lines
    )
    
    chart_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("PM2.5 Trend (Last 20 Readings)", style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER),
                pm25_chart,
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, width=450, height=300 # Set fixed height for chart card
        )
    )

    # --- Chart Update Function ---
    def update_chart_display():
        nonlocal pm25_chart 
        nonlocal chart_data
        
        data_points = []
        for x_val, y_val in chart_data:
            data_points.append(ft.LineChartDataPoint(x_val, y_val))
        
        pm25_chart.data_series = [
            ft.LineChartDataSeries(
                data_points=data_points,
                color=ft.colors.BLUE,
                stroke_width=2,
                curved=True,
            )
        ]
        
        if chart_data:
            min_y = min(p[1] for p in chart_data)
            max_y = max(p[1] for p in chart_data)
            # Add some padding; ensure min_y isn't negative if data is always positive
            y_padding = 5
            pm25_chart.left_axis.min = max(0, min_y - y_padding) 
            pm25_chart.left_axis.max = max_y + y_padding
            
            if data_points: # Ensure there are data points before trying to access them.
                x_labels = []
                num_points = len(chart_data)

                if num_points == 1:
                     x_labels.append(ft.ChartAxisLabel(value=chart_data[0][0], label=ft.Text(str(chart_data[0][0]), size=10)))
                     pm25_chart.bottom_axis.min = chart_data[0][0] - 1
                     pm25_chart.bottom_axis.max = chart_data[0][0] + 1
                else:
                    # Always show first and last
                    x_labels.append(ft.ChartAxisLabel(value=chart_data[0][0], label=ft.Text(str(chart_data[0][0]), size=10)))
                    x_labels.append(ft.ChartAxisLabel(value=chart_data[-1][0], label=ft.Text(str(chart_data[-1][0]), size=10)))
                    pm25_chart.bottom_axis.min = chart_data[0][0]
                    pm25_chart.bottom_axis.max = chart_data[-1][0]

                    # Add intermediate labels (max 3 additional for total of 5 labels)
                    if num_points > 5: # Show up to 3 intermediate for total 5 labels
                        step = num_points // 4 # Creates 3 intermediate points
                        for i in range(1, 4):
                            idx = step * i
                            if 0 < idx < num_points -1 : # ensure it's not first or last
                                x_labels.append(ft.ChartAxisLabel(value=chart_data[idx][0], label=ft.Text(str(chart_data[idx][0]), size=10)))
                    elif num_points > 2 : # for 3, 4, 5 points, add the middle one if not already covered
                        mid_idx = num_points // 2
                        if chart_data[mid_idx][0] != chart_data[0][0] and chart_data[mid_idx][0] != chart_data[-1][0]:
                             x_labels.append(ft.ChartAxisLabel(value=chart_data[mid_idx][0], label=ft.Text(str(chart_data[mid_idx][0]), size=10)))
                
                pm25_chart.bottom_axis.labels = x_labels
            else: 
                pm25_chart.bottom_axis.labels = []
                pm25_chart.bottom_axis.min = None 
                pm25_chart.bottom_axis.max = None
        else: 
            pm25_chart.left_axis.min = 0
            pm25_chart.left_axis.max = 50 # Default max if no data
            pm25_chart.bottom_axis.labels = []
            pm25_chart.bottom_axis.min = None 
            pm25_chart.bottom_axis.max = None

        pm25_chart.update()

    # --- Controls ---
    refresh_button = ft.ElevatedButton(text="Refresh Data", on_click=lambda e: refresh_data(e), icon=ft.icons.REFRESH)

    def refresh_data(e): # Parameter e is passed by button click, can be None for auto-refresh
        global api_client
        nonlocal current_x_value 
        
        if not api_client:
            status_bar.value = "API keys not loaded. Please load keys first via API Configuration."
            page.update()
            return

        try:
            status_bar.value = "Fetching data..."
            page.update()

            # Ensure API client is still valid (e.g. after an error)
            # This re-uses the existing global api_client
            if not api_client:
                 status_bar.value = "API client not initialized. Load keys."
                 page.update()
                 return

            devices = api_client.get_devices() # This might raise if keys became invalid
            if not devices:
                status_bar.value = "No devices found on your account."
                # Reset displays
                pm25_display.value = "PM2.5: -- µg/m³"
                aqi_display.value = "AQI: --"
                health_info_display.value = "Health information will appear here."
                page.update()
                return

            device = devices[0]
            device_data = device.get_data(limit=1) 
            
            if not device_data:
                status_bar.value = "No data received from the station."
                pm25_display.value = "PM2.5: -- µg/m³"
                aqi_display.value = "AQI: --"
                health_info_display.value = "Health information will appear here."
                page.update()
                return

            latest_data = device_data[0]
            pm25_value = None
            common_pm25_keys = [
                'pm25', 'PM25', 'pm2_5', 'pm25_in', 'PM25_in', 'pm25_indoor', 
                'pm25outdoor', 'PM25outdoor', 'pm25_24h_avg', 'pm25avg',
                'pm25conc', 'pm25concentration' 
            ]
            found_key = None
            for key_attempt in common_pm25_keys:
                if key_attempt in latest_data:
                    value = latest_data[key_attempt]
                    if isinstance(value, (int, float)) and value >= 0: 
                        pm25_value = float(value)
                        found_key = key_attempt
                        break
            
            if pm25_value is not None:
                pm25_display.value = f"PM2.5: {pm25_value:.1f} µg/m³" # Format to 1 decimal place
                page.session.set("current_pm25", pm25_value)

                aqi_result = get_aqi_and_health_info(float(pm25_value))
                if isinstance(aqi_result['aqi'], int):
                    aqi_display.value = f"AQI: {aqi_result['aqi']}"
                else: 
                    aqi_display.value = f"AQI: {aqi_result['aqi']}"
                
                health_info_text = (
                    f"Category: {aqi_result['category']}\n"
                    f"Sensitive Groups: {aqi_result['sensitive_group']}\n"
                    f"Health Effects: {aqi_result['health_effect']}\n"
                    f"Cautionary: {aqi_result['cautionary']}"
                )
                health_info_display.value = health_info_text
                status_bar.value = f"Refreshed: PM2.5 ({found_key}) {pm25_value:.1f} µg/m³ at {latest_data.get('date', 'N/A')}. AQI: {aqi_result['aqi']}."

                chart_data.append((current_x_value, float(pm25_value)))
                current_x_value += 1
                update_chart_display()
            else:
                pm25_display.value = "PM2.5: Not Available"
                status_bar.value = f"PM2.5 data not found in latest report from {latest_data.get('date', 'N/A')}. Keys: {list(latest_data.keys())}"
                aqi_display.value = "AQI: --"
                health_info_display.value = "Health information will appear here."
        
        except RequestsConnectionError:
            status_bar.value = "Fetch failed: Network error. Check connection."
            # Optionally reset data displays to '--'
        except Exception as ex:
            status_bar.value = f"Fetch failed: API error ({type(ex).__name__}). Try reloading keys."
            # Optionally reset data displays
            pm25_display.value = "PM2.5: Error"
            aqi_display.value = "AQI: Error"
            health_info_display.value = "Error processing data."
            # api_client = None # Could reset client here, forcing re-auth
        
        page.update()
    
    # Attempt to load keys from config when app starts
    attempt_auto_load_keys()


    # --- Main Layout ---
    page.add(
        ft.Column(
            [
                api_key_card,
                ft.Row([refresh_button], alignment=ft.MainAxisAlignment.CENTER), # Centered refresh button
                data_display_card,
                health_display_card,
                chart_card,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15 # Spacing between cards
        )
    )
    
    update_chart_display() # Initial chart render
    page.update() 

if __name__ == "__main__":
    ft.app(target=main)
