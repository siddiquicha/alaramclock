# Python CLI Alarm Clock

A simple and lightweight Command-Line Alarm Clock built with Python. This application allows users to set an alarm by entering a specific time in the terminal. When the scheduled time is reached, the program notifies the user with an alarm sound or message.

## Features

- Set alarms using the command line
- Supports time in HH:MM format
- Real-time clock monitoring
- Lightweight and beginner-friendly
- Easy to customize and extend

## Technologies Used

- Python 3
- datetime
- time
- playsound (if used)

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/python-cli-alarm-clock.git

# Full command set:

set <time> [label] [--repeat] — add an alarm; --repeat fires it every 24 h
list — show all active alarms with IDs
cancel <id> — cancel by ID
snooze <id> [minutes] — default 5 min snooze
time — show current time
quit / exit — clean shutdown
