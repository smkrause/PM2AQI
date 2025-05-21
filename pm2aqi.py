import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
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
def calculate_aqi(event=None):
    try:
        pm_value = float(pm_var.get())
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
            aqi_output.set("PM2.5 value out of range (1-500).")
            return
        # Displaying the AQI
        aqi_reading.set(f"AQI: {aqi}")
        # Getting health risk information
        category, sensitive_group, health_effect, cautionary = health_risks[index]
        # Creating the output string (single spaced)
        result = f"Category: {category}\n"
        result += f"Sensitive Groups: {sensitive_group}\n"
        result += f"Health Effects Statement: {health_effect}\n"
        result += f"Cautionary Statements: {cautionary}"
        # Setting the output variable
        aqi_output.set(result)
    except ValueError:
        aqi_output.set("Invalid input. Please enter a number.")

def save_api_keys():
    api_key = api_key_var.get().strip()
    app_key = app_key_var.get().strip()
    if not api_key or not app_key:
        messagebox.showwarning("Missing Keys", "Please enter both API Key and App Key before saving.")
        return
    try:
        with open('.env', 'w') as f:
            f.write(f'AMBIENT_API_KEY={api_key}\n')
            f.write(f'AMBIENT_APP_KEY={app_key}\n')
        messagebox.showinfo("Saved", "API Key and App Key saved to .env.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save keys: {e}")

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

# Initializing the main window
root = tk.Tk()
root.title("PM2.5 to AQI Calculator")

# Output and state variables (must be defined after root)
aqi_reading = tk.StringVar()
aqi_output = tk.StringVar()
weather_output = tk.StringVar()
auto_refresh_var = tk.BooleanVar(value=False)
auto_refresh_job = [None]  # Use a mutable container to allow assignment in nested scope

# Update weather data output (single label)
def set_weather_output(weather_str):
    lines = weather_str.strip().split("\n")
    mid = (len(lines) + 1) // 2
    col1 = "\n".join(lines[:mid])
    col2 = "\n".join(lines[mid:])
    weather_col1.config(text=col1)
    weather_col2.config(text=col2)
    weather_inner.update_idletasks()
    weather_canvas.config(scrollregion=weather_canvas.bbox("all"))

def fetch_and_set_pm25_and_weather():
    api_key = api_key_var.get().strip()
    app_key = app_key_var.get().strip()
    if not api_key or not app_key:
        aqi_output.set("Please enter both API Key and App Key.")
        set_weather_output("")
        return
    weather_data, error = fetch_pm25_and_weather_from_ambient(api_key, app_key)
    if error:
        aqi_output.set(error)
        set_weather_output("")
    else:
        pm_var.set(str(weather_data.get('pm25', '')))
        calculate_aqi()
        weather_str = f"Date: {weather_data.get('date', 'N/A')}\n"
        weather_str += f"Outdoor Temp: {weather_data.get('tempf', 'N/A')} °F\n"
        weather_str += f"Outdoor Humidity: {weather_data.get('humidity', 'N/A')}%\n"
        weather_str += f"Barometer (rel): {weather_data.get('baromrelin', 'N/A')} inHg\n"
        weather_str += f"Barometer (abs): {weather_data.get('baromabsin', 'N/A')} inHg\n"
        weather_str += f"Wind Speed: {weather_data.get('windspeedmph', 'N/A')} mph\n"
        weather_str += f"Wind Gust: {weather_data.get('windgustmph', 'N/A')} mph\n"
        weather_str += f"Wind Dir: {weather_data.get('winddir', 'N/A')}°\n"
        weather_str += f"Max Daily Gust: {weather_data.get('maxdailygust', 'N/A')} mph\n"
        weather_str += f"Rain (hour): {weather_data.get('hourlyrainin', 'N/A')} in\n"
        weather_str += f"Rain (day): {weather_data.get('dailyrainin', 'N/A')} in\n"
        weather_str += f"Rain (week): {weather_data.get('weeklyrainin', 'N/A')} in\n"
        weather_str += f"Rain (month): {weather_data.get('monthlyrainin', 'N/A')} in\n"
        weather_str += f"Rain (year): {weather_data.get('yearlyrainin', 'N/A')} in\n"
        weather_str += f"Solar Radiation: {weather_data.get('solarradiation', 'N/A')} W/m²\n"
        weather_str += f"UV Index: {weather_data.get('uv', 'N/A')}\n"
        weather_str += f"Indoor Temp: {weather_data.get('tempinf', 'N/A')} °F\n"
        weather_str += f"Indoor Humidity: {weather_data.get('humidityin', 'N/A')}%\n"
        weather_str += f"Indoor PM2.5: {weather_data.get('pm25_in', 'N/A')} μg/m³\n"
        weather_str += f"Indoor PM2.5 (24h avg): {weather_data.get('pm25_in_24h', 'N/A')} μg/m³\n"
        weather_str += f"Outdoor Feels Like: {weather_data.get('feelsLike', 'N/A')} °F\n"
        weather_str += f"Outdoor Dew Point: {weather_data.get('dewPoint', 'N/A')} °F\n"
        weather_str += f"Indoor Feels Like: {weather_data.get('feelsLikein', 'N/A')} °F\n"
        weather_str += f"Indoor Dew Point: {weather_data.get('dewPointin', 'N/A')} °F\n"
        set_weather_output(weather_str)

def auto_refresh_toggle():
    if auto_refresh_var.get():
        schedule_auto_refresh()
    else:
        if auto_refresh_job[0] is not None:
            root.after_cancel(auto_refresh_job[0])
            auto_refresh_job[0] = None

def schedule_auto_refresh():
    fetch_and_set_pm25_and_weather()
    auto_refresh_job[0] = root.after(60000, schedule_auto_refresh)  # 60,000 ms = 60 seconds

# Centering the window on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 400
window_height = 650
x = (screen_width/2) - (window_width/2)
y = (screen_height/2) - (window_height/2)
root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")

# Styles
color_bg = "#f0f4f6"
color_header = "#34495e"
color_button = "#2c3e50"
color_output_bg = "#ecf0f1"
label_font = ("Arial", 14)
header_font = ("Arial", 16, "bold")
output_font = ("Arial", 12)
aqi_reading_font = ("Arial", 20, "bold")

root.configure(bg=color_bg)

# Header
header_label = ttk.Label(root, text="PM2.5 to AQI Calculator", font=header_font, background=color_header, foreground="white", padding=10)
header_label.pack(pady=10, fill="x")

description_label = ttk.Label(root, text="Enter a PM2.5 value (1-500) to get the AQI", font=label_font, background=color_bg)
description_label.pack(pady=5)

# API Key Entry Section
api_frame = tk.Frame(root, background=color_bg)
api_frame.pack(pady=5)

api_key_var = tk.StringVar()
app_key_var = tk.StringVar()

api_key_label = ttk.Label(api_frame, text="API Key:", font=("Arial", 12), background=color_bg)
api_key_label.grid(row=0, column=0, sticky="e", padx=(0, 5))
api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, width=45)
api_key_entry.grid(row=0, column=1, padx=(0, 10))

app_key_label = ttk.Label(api_frame, text="App Key:", font=("Arial", 12), background=color_bg)
app_key_label.grid(row=1, column=0, sticky="e", padx=(0, 5))
app_key_entry = ttk.Entry(api_frame, textvariable=app_key_var, width=45)
app_key_entry.grid(row=1, column=1, padx=(0, 10))

save_api_button = ttk.Button(api_frame, text="Save API", command=save_api_keys)
save_api_button.grid(row=2, column=1, sticky="e", pady=(5,0))

# On startup, check for .env and hide API fields if found
loaded_api_key, loaded_app_key = load_api_keys_from_env()
if loaded_api_key and loaded_app_key:
    api_key_var.set(loaded_api_key)
    app_key_var.set(loaded_app_key)
    api_key_label.grid_remove()
    api_key_entry.grid_remove()
    app_key_label.grid_remove()
    app_key_entry.grid_remove()
    save_api_button.grid_remove()

# Input frame for PM2.5 and buttons
input_frame = tk.Frame(root, background=color_bg)
input_frame.pack(pady=5)

pm_var = tk.StringVar()
pm_var.set("3")  # Default value upon launch

pm_entry = ttk.Entry(input_frame, textvariable=pm_var, justify="center", font=("Arial", 12), width=20)
pm_entry.bind("<Return>", calculate_aqi)
pm_entry.grid(row=0, column=0, padx=(0, 10))

calculate_button = ttk.Button(input_frame, text="Calculate AQI", command=calculate_aqi)
calculate_button.grid(row=0, column=1)

fetch_button = ttk.Button(input_frame, text="Fetch PM2.5 & Weather", command=fetch_and_set_pm25_and_weather)
fetch_button.grid(row=0, column=2, padx=(10, 0))

# Auto-refresh checkbox
auto_refresh_check = ttk.Checkbutton(root, text="Auto-Refresh (every 60s)", variable=auto_refresh_var, command=auto_refresh_toggle)
auto_refresh_check.pack(pady=(0, 5))

# AQI reading label
aqi_reading_label = ttk.Label(root, textvariable=aqi_reading, font=aqi_reading_font, background=color_output_bg, relief="solid", padding=10, justify="center")
aqi_reading_label.pack(pady=5, padx=20)

# Weather data output with two columns and scrollbar
weather_frame = tk.Frame(root, background=color_output_bg, relief="solid", bd=1)
weather_frame.pack(pady=5, padx=20, fill="x")

weather_canvas = tk.Canvas(weather_frame, background=color_output_bg, highlightthickness=0, height=240)
weather_scrollbar = ttk.Scrollbar(weather_frame, orient="vertical", command=weather_canvas.yview)
weather_inner = tk.Frame(weather_canvas, background=color_output_bg)

weather_inner_id = weather_canvas.create_window((0, 0), window=weather_inner, anchor="nw")
weather_canvas.configure(yscrollcommand=weather_scrollbar.set)

weather_canvas.pack(side="left", fill="both", expand=True)
weather_scrollbar.pack(side="right", fill="y")

weather_col1 = tk.Label(weather_inner, text="", justify=tk.LEFT, font=output_font, background=color_output_bg)
weather_col2 = tk.Label(weather_inner, text="", justify=tk.LEFT, font=output_font, background=color_output_bg)
weather_col1.grid(row=0, column=0, sticky="nw", padx=(0, 16), pady=0)
weather_col2.grid(row=0, column=1, sticky="nw", padx=(0, 0), pady=0)

# AQI info label (health info, now below weather data, smaller font, single spaced)
small_output_font = ("Arial", 10)
aqi_info_label = ttk.Label(root, textvariable=aqi_output, justify=tk.LEFT, wraplength=350, font=small_output_font, background=color_output_bg, relief="solid", padding=8)
aqi_info_label.pack(pady=10, padx=20, fill="x")

# Start the Tkinter event loop
root.mainloop()