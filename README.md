# PM2.5 Data Logger

This script fetches PM2.5 sensor data from a public API (https://pm25.lass-net.org/), stores data in a local CSV file and periodically checks for new data. It then analyzes the data and generates reports. 
The reports include statistical analysis of PM2.5 levels and highlight periods when the levels exceed a predefined threshold. 
It also logs information such as CSV updates, PDF report generation, and errors in a log file.

To see an example of what script outputs, refer to the `example_output.zip` file.

## Features

- Fetches PM2.5 data from a public API (https://pm25.lass-net.org/)
- Stores data in a local CSV file
- Periodically checks for new data
- Analyzes PM2.5 data and generates reports
- Logs significant events and errors

## Dependencies

The following Python libraries are required:

- `requests`
- `pandas`
- `matplotlib`
- `fpdf`

The script automatically checks for and installs any missing libraries, but you can manually install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```
## Useage

Ensure that the `config.json` configuration file and the script file are located in the same directory and run the main script `pm25_logger.py`. To stop, press Ctrl+C on terminal.

## Configuration

Adjustable parameters are stored in `config.json` file.

```json
{
    "API_URL": "https://pm25.lass-net.org/data/history.php?device_id={device_id}",
    "DEVICE_ID": "74DA38B0539E",
    "CSV_FILE": "pm25_data.csv",
    "THRESHOLD": 30,
    "CHECK_INTERVAL": 300,
    "FOLDER_NAME": "PM25_Reports",
    "LOG_FILE": "pm25_log.log"
}
```

## Configuration Parameters

Below are the descriptions for each configuration parameter:

- **`API_URL:`** URL for the API endpoint that is used to fetch PM2.5 data
- **`DEVICE_ID:`** ID for PM2.5 sensor device
- **`CSV_FILE:`** Name of the CSV file where sensor data will be saved. This file will be stored in the directory specified by the `FOLDER_NAME`
- **`THRESHOLD:`** Threshold for PM2.5 concentration (μg/m³)
- **`CHECK_INTERVAL:`** Time interval, in seconds, between successive checks for new data from the API
- **`FOLDER_NAME`** Directory where the CSV file, PDF reports, and log files will be stored
- **`LOG_FILE:`** Filename for the log file where the script logs information about data fetching and errors

