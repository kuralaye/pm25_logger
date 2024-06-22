"""
pm25_logger.py

This script fetches PM2.5 sensor data from a public API, stores data in a local CSV file,
and periodically checks for new data. It then analyzes the data and generates reports.
The reports include statistical analysis of PM2.5 levels and highlight periods when the levels exceed a predefined threshold.
It also logs information such as CSV updates, PDF report generation, and errors in a log file.

Required Libraries:
- requests
- pandas
- matplotlib
- fpdf

To stop the script, use Ctrl+C in the terminal.

Author: Ertunc Kuralay
Date: 2024-06-22
"""

import subprocess
import sys

def install_libraries():
    """ Check if necessary libraries are available and install if not"""
    required_libraries = ["requests", "pandas", "matplotlib", "fpdf"]
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"{lib} not found, installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            
install_libraries()

import requests
import pandas as pd
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import logging
import json

def load_config():
    """ Loads config file to get settings such as API_URL, DEVICE_ID, and other relevant 
    parameters used throughout the script."""
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config

config = load_config()

API_URL = config['API_URL']
DEVICE_ID = config['DEVICE_ID'] # Enter Device ID, other devices tested ['B827EBD3DBA8','74DA38F7C1B4','08BEAC245F4A']
CSV_FILE = config['CSV_FILE']   #CSV file name to store data
THRESHOLD = config['THRESHOLD'] # Threshold for PM2.5 (unit: ug/m^3)
CHECK_INTERVAL = config['CHECK_INTERVAL'] # Time interval in seconds,default is 5 min
FOLDER_NAME = config['FOLDER_NAME'] # Folder to save reports and data
LOG_FILE = os.path.join(FOLDER_NAME, config['LOG_FILE'])

# Set up logging
if not os.path.exists(FOLDER_NAME):
    os.makedirs(FOLDER_NAME)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',force=True)


def fetch_data(device_id):
    """Fetch data from API"""
    try:
        response = requests.get(API_URL.format(device_id=device_id))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        print(f"Error fetching data: {e}")
        return None


def flatten_data(feeds, pm25_sensor='s_d0'):
    """Flatten JSON data"""
    flattened_data = []
    for feed in feeds:
        for source, entries in feed.items():
            for entry in entries:
                for timestamp, values in entry.items():
                    flattened_entry = {
                        'timestamp': values['timestamp'],
                        'PM2.5': values.get(pm25_sensor, None)
                    }
                    flattened_data.append(flattened_entry)
    return flattened_data

def save_data_to_csv(df, folder_name):
    """Store data in CSV file and update when new data is available"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    csv_path = os.path.join(folder_name, CSV_FILE)
    
    if not os.path.exists(csv_path):
        df.to_csv(csv_path, index=False)
        logging.info("CSV file created.")
        print("CSV file created.")
        return True
    else:
        existing_df = pd.read_csv(csv_path)
        
        # Check for new timestamps
        new_rows = df[~df['timestamp'].isin(existing_df['timestamp'])]
        
        if not new_rows.empty:
            combined_df = pd.concat([existing_df, new_rows]).reset_index(drop=True)
            combined_df.to_csv(csv_path, index=False)
            return True
        return False

def analyze_data(data):
    """Calculate daily statistics for PM2.5 and find points above threshold"""
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['date'] = data['timestamp'].dt.date
    daily_stats = data.groupby('date')['PM2.5'].agg(['max', 'min', 'mean']).reset_index()
    abovethreshold_periods = data[data['PM2.5'] > THRESHOLD]
    return daily_stats, abovethreshold_periods

def generate_plot(daily_stats, data, folder_name):
    """Generate plot from the data to be used in pdf report."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    plt.figure(figsize=(10, 8))

    # Plot daily statistics
    plt.subplot(2, 1, 1)
    plt.plot(daily_stats['date'], daily_stats['max'], label='Max (μg/m³)')
    plt.plot(daily_stats['date'], daily_stats['min'], label='Min (μg/m³)')
    plt.plot(daily_stats['date'], daily_stats['mean'], label='Mean (μg/m³)')
    plt.axhline(y=THRESHOLD, color='r', linestyle='--', label='Threshold (μg/m³)')
    plt.xlabel('Date')
    plt.ylabel('PM2.5 (μg/m³)')
    plt.title('Daily PM2.5 Statistics')
    plt.legend()
    plt.grid(True)

    # Plot all data points
    plt.subplot(2, 1, 2)
    below_threshold = data[data['PM2.5'] <= THRESHOLD]
    above_threshold = data[data['PM2.5'] > THRESHOLD]
    plt.scatter(below_threshold['timestamp'], below_threshold['PM2.5'], color='green', label=f'PM2.5 ≤ {THRESHOLD} μg/m³')
    plt.scatter(above_threshold['timestamp'], above_threshold['PM2.5'], color='red', label=f'PM2.5 > {THRESHOLD} μg/m³')
    plt.axhline(y=THRESHOLD, color='r', linestyle='--', label='Threshold')
    plt.xlabel('Date')
    plt.ylabel('PM2.5 (μg/m³)')
    plt.title('PM2.5 Concentrations')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    # Save the plot as a temporary file
    temp_plot_file = os.path.join(folder_name, 'temp_plot.png')
    plt.savefig(temp_plot_file)
    plt.close()
    return temp_plot_file

def generate_pdf_report(daily_stats, abovethreshold_periods, plot_file, folder_name):
    """Generate a PDF report with the analyzed data and plot."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt="PM2.5 Analysis Report", ln=True, align='C')

    # Device ID
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Device ID: {DEVICE_ID}", ln=True, align='L')
    
    
    # Start and End Time
    start_time = daily_stats['date'].min()
    end_time = daily_stats['date'].max()
    pdf.cell(200, 10, txt=f"Report Period: {start_time} - {end_time}", ln=True, align='L')

    # Insert plot
    pdf.image(plot_file, x=10, y=40, w=180)

    # Daily statistics table
    pdf.add_page()
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt="Daily PM2.5 Statistics", ln=True, align='L')
    col_width = pdf.w / 4.5
    pdf.cell(col_width, 10, txt="Date", border=1, ln=False, align='C')
    pdf.cell(col_width, 10, txt="Max (ug/m^3)", border=1, ln=False, align='C')
    pdf.cell(col_width, 10, txt="Min (ug/m^3)", border=1, ln=False, align='C')
    pdf.cell(col_width, 10, txt="Mean (ug/m^3)", border=1, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for index, row in daily_stats.iterrows():
        pdf.cell(col_width, 10, txt=str(row['date']), border=1, ln=False, align='C')
        pdf.cell(col_width, 10, txt=str(row['max']), border=1, ln=False, align='C')
        pdf.cell(col_width, 10, txt=str(row['min']), border=1, ln=False, align='C')
        pdf.cell(col_width, 10, txt=f"{row['mean']:.2f}", border=1, ln=True, align='C')

    # Date-time table for PM2.5 points above threshold
    pdf.add_page()
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt=f"Periods of High PM2.5 Concentration (Threshold: {THRESHOLD} ug/m^3)", ln=True, align='L')
    pdf.cell(col_width * 2, 10, txt="Timestamp", border=1, ln=False, align='C')
    pdf.cell(col_width * 2, 10, txt="PM2.5 (ug/m^3)", border=1, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for index, row in abovethreshold_periods.iterrows():
        pdf.cell(col_width * 2, 10, txt=str(row['timestamp']), border=1, ln=False, align='C')
        pdf.cell(col_width * 2, 10, txt=str(row['PM2.5']), border=1, ln=True, align='C')

    # Save PDF report
    pdf_output = os.path.join(folder_name, f"PM25_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    pdf.output(pdf_output)
    logging.info(f"PDF report generated: {pdf_output}")
    print(f"PDF report generated: {pdf_output}")

    # Remove the temporary plot file
    os.remove(plot_file)

def main():
    """Main function to fetch data, store, analyze, and generate reports."""
    while True:
        # Fetch data from API
        data = fetch_data(DEVICE_ID)
        if data is None:
            time.sleep(CHECK_INTERVAL)
            continue

        # Flatten the data
        flattened_data = flatten_data(data['feeds'])
        df = pd.DataFrame(flattened_data)

        # Save data to CSV and check if new data was added
        if save_data_to_csv(df, FOLDER_NAME):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"CSV updated with new sensor data - {current_time}.")
            logging.info("CSV updated with new sensor data")
            
            # Analyze the data
            daily_stats, abovethreshold_periods = analyze_data(df)

            # Generate plot and save as a temporary file
            plot_file = generate_plot(daily_stats, df, FOLDER_NAME)

            # Generate PDF report
            generate_pdf_report(daily_stats, abovethreshold_periods, plot_file, FOLDER_NAME)

        # Wait before fetching data again
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Process interrupted by user.")
        logging.info("Process interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.error(f"An unexpected error occurred: {e}")
