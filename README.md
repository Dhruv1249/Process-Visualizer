
# Process Visualization Tool

The **Process Visualization Tool** is a Python-based desktop application designed to monitor system resources in real-time and simulate CPU scheduling algorithms. It features a user-friendly interface with a modern dark theme, making it both functional and visually appealing.

## Features

- **System Monitor Dashboard**:
  - Real-time monitoring of CPU, GPU, RAM, and Disk usage with speedometer-style gauges.
  - Displays the current running processes by CPU usage in a sortable table.
  - Displays the top 10 running processes by CPU and RAM usage in a bar graph.


- **Process Scheduling Simulator**:
  - Simulate CPU scheduling algorithms: FCFS, SJF, and Round Robin.
  - Input the number of processes, arrival times, burst times, and (for Round Robin) the time quantum.
  - Visualize the scheduling process with a Gantt chart and view process details in a table.

- **Dark Theme UI**:
  - Sleek, modern interface with a dark theme for improved readability and aesthetics.

## Installation

To run the Process Visualization Tool, install the required Python libraries using the following command:

1) If you don't have a NVIDIA GPU:

```bash
pip install PyQt5 psutil 
```
2) If have a NVIDIA GPU available

```bash
pip install PyQt5 psutil pynvml
```

### Conthrax Font Installation

The application uses the Conthrax font for optimal UI display. Please download and install the Conthrax font by visiting the following link:

(https://dl.dafont.com/dl/?f=conthrax)

After downloading the zip file, unzip the file and run the .otf file and click on intall and it will be automatically installed in your system.

