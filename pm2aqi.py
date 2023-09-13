import tkinter as tk
from tkinter import ttk

def calculate_aqi(event=None):
    try:
        pm_value = float(pm_var.get())
        
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

        aqi_reading.set(f"AQI: {aqi}")
        category, sensitive_group, health_effect, cautionary = health_risks[index]
        result = f"Category: {category}\n\n"
        result += f"Sensitive Groups: {sensitive_group}\n\n"
        result += f"Health Effects Statement: {health_effect}\n\n"
        result += f"Cautionary Statements: {cautionary}\n\n"
        aqi_output.set(result)
    except ValueError:
        aqi_output.set("Invalid input. Please enter a number.")

root = tk.Tk()

#root.geometry("400x600")
root.title("PM2.5 to AQI Calculator")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Assuming you want a 400x300 window, adjust as needed
window_width = 400
window_height = 600

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

# Widgets
header_label = ttk.Label(root, text="PM2.5 to AQI Calculator", font=header_font, background=color_header, foreground="white", padding=10)
header_label.pack(pady=10, fill="x")

description_label = ttk.Label(root, text="Enter a PM2.5 value (1-500) to get the AQI", font=label_font, background=color_bg)
description_label.pack(pady=5)

# Using a frame for better alignment of the entry and the button
input_frame = tk.Frame(root, background=color_bg)
input_frame.pack(pady=5)

pm_var = tk.StringVar()
pm_var.set("3")  # Default value upon launch

pm_entry = ttk.Entry(input_frame, textvariable=pm_var, justify="center", font=("Arial", 12), width=20)
pm_entry.bind("<Return>", calculate_aqi)
pm_entry.grid(row=0, column=0, padx=(0, 10))

calculate_button = ttk.Button(input_frame, text="Calculate AQI", command=calculate_aqi)
calculate_button.grid(row=0, column=1)

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

aqi_reading = tk.StringVar()
aqi_reading_label = ttk.Label(root, textvariable=aqi_reading, font=aqi_reading_font, background=color_output_bg, relief="solid", padding=10, justify="center")
aqi_reading_label.pack(pady=5, padx=20)

aqi_output = tk.StringVar()
aqi_info_label = ttk.Label(root, textvariable=aqi_output, justify=tk.LEFT, wraplength=350, font=output_font, background=color_output_bg, relief="solid", padding=10)
aqi_info_label.pack(pady=15, padx=20, fill="x")

calculate_aqi()
root.mainloop()
