# Pomodoro Timer

A simple command-line Pomodoro timer for macOS with notifications and session tracking.

## The Pomodoro Technique

One Pomodoro consists of:
- 4 work sessions (25 minutes each)
- 3 short breaks (5 minutes) between sessions
- 1 long break (15-30 minutes) after completing all 4 sessions

## Requirements

- Python 3.6+
- macOS (for notifications)
- `terminal-notifier` for desktop notifications:
  ```bash
  brew install terminal-notifier
  ```

## Usage

```bash
# Start a Pomodoro session
python3 pomodoro.py

# Customize long break duration (15-30 minutes)
python3 pomodoro.py --break 25

# View statistics
python3 pomodoro.py --stats

# View this week's stats
python3 pomodoro.py --stats --week

# View this month's stats
python3 pomodoro.py --stats --month
```

## Features

- Live countdown display with progress bar
- macOS desktop notifications at session transitions
- Session tracking saved to `~/.pomodoro_data.json`
- Statistics for all-time, weekly, or monthly progress
- Option to skip breaks if you're in the zone
