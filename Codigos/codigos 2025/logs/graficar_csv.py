import os
import matplotlib.pyplot as plt
import pandas as pd

def main():
    # Get the current script's directory path
    script_path = os.path.dirname(os.path.abspath(__file__))
    
    # Specify the CSV file to be read
    data = "battery_data_sustrend_bank_2023-11-12_00-05-36.csv"
    absolute_csv_path = os.path.join(script_path, data)
    
    # Check if the specified file exists in the directory
    if not os.path.exists(absolute_csv_path):
        print(f"The file {data} does not exist in the directory.")
        return

    # Read the CSV file
    data_frame = pd.read_csv(absolute_csv_path)
    
    # Define the specific timestamps for the start and end of the plot
    #start = "2023-09-04 23:20:19"
    #end = "2023-09-05 06:00:00"

    # Initialize the figure for plotting
    plt.figure(figsize=(10, 6))

    # Calculate time intervals in seconds
    time_intervals = range(len(data_frame))

    # Convert time intervals to hours by dividing by 3600
    hours = [t / 3600 for t in time_intervals]

    # Iterate over the columns starting with "Cell 1"
    for column in data_frame.columns:
        if "Voltage" in column or "Current" in column or "Temp" in column:
            # Extract cell number from the column name
            cell_number = column.split(" ")[1]
            
            # Create the left y-axis for current and voltage
            ax1 = plt.gca()
            ax1.plot(hours, data_frame[f"Cell {cell_number} Current"], label=f"Cell {cell_number} Current (A)")
            ax1.plot(hours, data_frame[f"Cell {cell_number} Voltage"], label=f"Cell {cell_number} Voltage (V)")
            ax1.set_ylabel('Current (A) / Voltage (V)')
            ax1.tick_params(axis='y')
            ax1.set_xlabel('Time (hours)')
            plt.xticks(rotation=45)

            # Create the right y-axis for temperature
            ax2 = ax1.twinx()
            ax2.plot(hours, data_frame[f"Cell {cell_number} Temp"], label=f"Cell {cell_number} Temperature (°C)")
            ax2.set_ylabel('Temperature (°C)')

    # Set the x-axis limits using the start and end variables
    ax1.set_xlim(0, len(data_frame) / 3600)
    ax2.set_xlim(0, len(data_frame) / 3600)

    # Set the title of the plot
    plt.title('Current, Voltage, and Temperature Plot of ' + data)
    plt.tight_layout()
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.savefig(absolute_csv_path + ".png")
    plt.show()

if __name__ == "__main__":
    main()
