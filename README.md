# Process Visualization Tool

The **Process Visualization Tool** is a Python-based desktop application designed to monitor system resources in real-time and simulate CPU scheduling algorithms. It features a user-friendly interface with a modern dark theme, making it both functional and visually appealing.

## Features

- **System Monitor Dashboard**:
  - Real-time monitoring of CPU, GPU, RAM, and Disk usage with speedometer-style gauges.
  - Displays the top 50 running processes by CPU usage in a sortable table.
  - Gauges are styled like Ookla Speedtest, with a left-to-right arc and color gradients (green to red) indicating usage levels.

- **Process Scheduling Simulator**:
  - Simulate CPU scheduling algorithms: First-Come-First-Serve (FCFS), Shortest Job First (SJF), and Round Robin.
  - Input the number of processes, arrival times, burst times, and (for Round Robin) the time quantum.
  - Visualize the scheduling process with a Gantt chart and view process details in a table.

- **Dark Theme UI**:
  - Sleek, modern interface with a dark theme for improved readability and aesthetics.

## Installation

To run the Process Visualization Tool, install the required Python libraries using the following command:

```bash
pip install -r requiremnt.txt
