import requests
import pandas as pd
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from tkinter import filedialog
from dotenv import load_dotenv
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

load_dotenv()  # Load variables from .env
fig = None  # Global figure

OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")

def geocode_city(city_name):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={OPENCAGE_API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        if data['results']:
            coords = data['results'][0]['geometry']
            return coords['lat'], coords['lng']
    return None, None

def fetch_weather():
    city = city_var.get()
    start_date = start_var.get()
    end_date = end_var.get()

    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
        return

    lat, lon = geocode_city(city)
    if lat is None or lon is None:
        messagebox.showerror("Location Error", "Could not find the city.")
        return

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone=Asia%2FKolkata"
    )

    response = requests.get(url)
    if response.status_code != 200:
        messagebox.showerror("API Error", "Failed to fetch weather data.")
        return

    data = response.json()
    if "daily" not in data:
        messagebox.showerror("Data Error", "No weather data available.")
        return

    df = pd.DataFrame({
        "Date": data["daily"]["time"],
        "Max Temp (°C)": data["daily"]["temperature_2m_max"],
        "Min Temp (°C)": data["daily"]["temperature_2m_min"]
    })
    df["Avg Temp (°C)"] = df[["Max Temp (°C)", "Min Temp (°C)"]].mean(axis=1)

    df = df.sort_values("Date")

    df["Date"] = pd.to_datetime(df["Date"])

    avg_temp = df["Avg Temp (°C)"].mean()
    max_temp = df["Max Temp (°C)"].max()
    min_temp = df["Min Temp (°C)"].min()
    temp_std = df["Avg Temp (°C)"].std()

    # 🔥 Trend calculation
    trend_slope = df["Avg Temp (°C)"].diff().mean()
    if trend_slope > 0.15:
       trend = "⬆️ Increasing"
    elif trend_slope < -0.15:
       trend = "⬇️ Decreasing"
    else:
       trend = "➡️ Stable"



    result_box.delete("1.0", "end")
    result_box.insert("end", f"📍 Weather Summary for {city}\n")
    result_box.insert("end", f"📅 {start_date} to {end_date}\n\n")
    result_box.insert("end", f"Average Temp: {avg_temp:.2f}°C\n")
    result_box.insert("end", f"Max Temp: {max_temp:.2f}°C\n")
    result_box.insert("end", f"Min Temp: {min_temp:.2f}°C\n")
    result_box.insert("end", f"Std Dev: {temp_std:.2f}\n\n")
    result_box.insert("end", f"Trend: {trend}\n\n")
    result_box.insert("end", f"📅 Daily Data:\n{df.to_string(index=False)}")

    df.to_csv("weather_data_summary.csv", index=False)

    with open("weather_summary.txt", "w", encoding="utf-8") as f:
     f.write(f"📍 Weather Summary for {city}\n")
     f.write(f"📅 {start_date} to {end_date}\n\n")
     f.write(f"Average Temp: {avg_temp:.2f}°C\n")
     f.write(f"Max Temp: {max_temp:.2f}°C\n")
     f.write(f"Min Temp: {min_temp:.2f}°C\n")
     f.write(f"Std Dev: {temp_std:.2f}°C\n")
     f.write(f"Trend: {trend}\n\n")

     # Clear previous chart (if any)
    for widget in chart_frame.winfo_children():
        widget.destroy()

# Create the plot figure
    global fig  # Declare global to modify
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    df["Date"] = pd.to_datetime(df["Date"])
    ax.plot(df["Date"], df["Max Temp (°C)"], label="Max Temp", color="red", marker="o")
    ax.plot(df["Date"], df["Min Temp (°C)"], label="Min Temp", color="blue", marker="o")
    ax.plot(df["Date"], df["Avg Temp (°C)"], label="Avg Temp", color="green", linestyle="--", marker="o")

    ax.set_title(f"Temperature Trends: {city}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temp (°C)")
    ax.grid(True)
    ax.legend()
    fig.autofmt_xdate()

# Embed chart in the GUI
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def save_chart():
    global fig
    if fig:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="Save Chart As"
        )
        if file_path:
            fig.savefig(file_path)
            messagebox.showinfo("Saved", f"Chart saved to:\n{file_path}")
    else:
        messagebox.showwarning("No Chart", "Please fetch weather data first.")

# 🖼️ GUI Setup
root = ttk.Window(title="🌤️ City-Based Weather Data", themename="solar", size=(1000, 700))

city_var = ttk.StringVar()
start_var = ttk.StringVar()
end_var = ttk.StringVar()

ttk.Label(root, text="🏙️ Enter City Name:").pack(pady=5)
ttk.Entry(root, textvariable=city_var, width=30).pack()

ttk.Label(root, text="📅 Start Date (YYYY-MM-DD):").pack(pady=5)
ttk.Entry(root, textvariable=start_var, width=30).pack()

ttk.Label(root, text="📅 End Date (YYYY-MM-DD):").pack(pady=5)
ttk.Entry(root, textvariable=end_var, width=30).pack()

ttk.Button(root, text="🔍 Fetch Weather & Summary", command=fetch_weather, bootstyle=SUCCESS).pack(pady=10)
ttk.Button(root, text="💾 Save Chart as Image", command=save_chart, bootstyle=PRIMARY).pack(pady=5)

# ⬅️➡️ Layout: Result Box | Chart Side-by-Side
content_frame = ttk.Frame(root)
content_frame.pack(fill="both", expand=True, padx=10, pady=10)

result_box = ttk.ScrolledText(content_frame, width=60, height=25)
result_box.pack(side="left", fill="both", expand=True, padx=(0, 10))

chart_frame = ttk.Frame(content_frame)
chart_frame.pack(side="left", fill="both", expand=True)

root.mainloop()

