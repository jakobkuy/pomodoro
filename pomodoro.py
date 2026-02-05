#!/usr/bin/env python3
"""
Classic Pomodoro Timer with macOS notifications and session tracking.

The Pomodoro Technique:
- One Pomodoro = 4 work sessions (25 min each) + 4 short breaks (5 min) + 1 long break (15-30 min)
- After completing all cycles, you can start a new Pomodoro

Usage:
    python3 pomodoro.py                # Start a new Pomodoro session
    python3 pomodoro.py --stats        # View statistics
    python3 pomodoro.py --break 20  # Customize long break duration (15-30 min)
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


class PomodoroTimer:
    """Classic Pomodoro timer with tracking and macOS notifications."""

    WORK_DURATION = 25  # minutes
    SHORT_BREAK_DURATION = 5  # minutes
    WORK_SESSIONS_PER_POMODORO = 4

    def __init__(self, storage_path=None, long_break_duration=20, test_mode=False):
        """Initialize timer with storage location."""
        if storage_path is None:
            storage_path = Path.home() / '.pomodoro_data.json'
        self.storage_path = Path(storage_path)
        self.data = self._load_data()
        self.test_mode = test_mode

        # Use shortened durations in test mode for quick testing
        if test_mode:
            self.WORK_DURATION = 5 / 60  # 5 seconds
            self.SHORT_BREAK_DURATION = 3 / 60  # 3 seconds
            self.long_break_duration = 5 / 60  # 5 seconds
            print("⚡ TEST MODE: Using shortened durations (seconds instead of minutes)")
        else:
            self.long_break_duration = long_break_duration

    def _load_data(self):
        """Load session history from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Validate data structure
                    if not isinstance(data, dict):
                        print("⚠️  Warning: Invalid data format, resetting storage...")
                        return {'pomodoros': []}
                    if 'pomodoros' not in data:
                        data['pomodoros'] = []
                    if not isinstance(data['pomodoros'], list):
                        print("⚠️  Warning: Invalid pomodoros format, resetting storage...")
                        return {'pomodoros': []}
                    return data
            except json.JSONDecodeError:
                print("⚠️  Warning: Corrupted data file, resetting storage...")
                return {'pomodoros': []}
        return {'pomodoros': []}

    def _save_data(self):
        """Save session history to JSON file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def notify(self, title, message, sound=True):
        """Send macOS notification using terminal-notifier."""
        try:
            cmd = [
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-group', 'pomodoro-timer'  # Groups notifications together
            ]

            if sound:
                cmd.extend(['-sound', 'default'])

            subprocess.run(cmd, check=False, capture_output=True)
        except FileNotFoundError:
            print(f"⚠️  Warning: terminal-notifier not found. Install with: brew install terminal-notifier")
        except Exception as e:
            print(f"⚠️  Warning: Could not send notification: {e}")

    def format_time(self, seconds):
        """Format seconds as MM:SS."""
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}:{secs:02d}"

    def countdown(self, duration_minutes, session_type, session_number=None):
        """Run countdown timer with live display."""
        total_seconds = duration_minutes * 60
        start_time = time.time()

        # Display session info
        if session_type == 'work':
            print(
                f"\n🍅 WORK SESSION {session_number}/4: {duration_minutes} minutes")
        elif session_type == 'short_break':
            print(f"\n☕ SHORT BREAK: {duration_minutes} minutes")
        else:  # long_break
            print(f"\n🎉 LONG BREAK: {duration_minutes} minutes")

        print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
        print("\nPress Ctrl+C to cancel\n")

        try:
            while True:
                elapsed = time.time() - start_time
                remaining = total_seconds - elapsed

                if remaining <= 0:
                    # Print final 100% progress bar before breaking
                    bar_width = 20
                    bar = '█' * bar_width
                    print(
                        f"\r⏱️  00:00 remaining [{bar}] 100%",
                        end='', flush=True)
                    break

                # Print countdown timer (overwrites same line)
                percent_complete = (elapsed / total_seconds) * 100
                bar_width = 20
                filled = int((elapsed / total_seconds) * bar_width)
                bar = '█' * filled + '░' * (bar_width - filled)
                print(
                    f"\r⏱️  {self.format_time(remaining)} remaining [{bar}] {percent_complete:.0f}%",
                    end='', flush=True)
                time.sleep(1)

            # Session completed - compact format for small terminals
            label = session_type.replace('_', ' ').upper()
            print(f"\r✅ {label} DONE! [{bar}]      ")

            if session_type == 'work':
                self.notify(
                    "Work Session Complete!",
                    f"Great work on session {session_number}/4! Time for a break.",
                    sound=True
                )
            elif session_type == 'short_break':
                self.notify(
                    "Break Over!",
                    "Time to get back to work!",
                    sound=True
                )
            else:  # long_break
                self.notify(
                    "Pomodoro Complete!",
                    "You finished a full Pomodoro cycle! Great job!",
                    sound=True
                )

            return True

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Session cancelled")
            return False

    def run_pomodoro(self):
        """Run a complete Pomodoro cycle (4 work sessions + breaks)."""
        # Set terminal title
        print("\033]0;🍅Pomodoro Timer\007", end="")
        print("\n" + "=" * 48)
        print("🍅 STARTING NEW POMODORO")
        print(f"4x25min work + 5min breaks + {self.long_break_duration}min long break")
        print("=" * 48)

        pomodoro_start_time = datetime.now()
        completed_work_sessions = 0

        # Run 4 work sessions with short breaks
        for i in range(1, self.WORK_SESSIONS_PER_POMODORO + 1):
            # Work session
            work_completed = self.countdown(self.WORK_DURATION, 'work', i)

            if not work_completed:
                print("\n❌ Pomodoro cancelled.")
                self._save_incomplete_pomodoro(
                    pomodoro_start_time, completed_work_sessions)
                return

            completed_work_sessions += 1

            # Short break (except after last session)
            if i < self.WORK_SESSIONS_PER_POMODORO:
                print("\nTake a short break? (y/n): ", end='', flush=True)
                try:
                    response = input().strip().lower()
                    if response == 'y' or response == '':
                        break_completed = self.countdown(
                            self.SHORT_BREAK_DURATION, 'short_break')
                        if not break_completed:
                            print("\n❌ Pomodoro cancelled.")
                            self._save_incomplete_pomodoro(
                                pomodoro_start_time, completed_work_sessions)
                            return
                    else:
                        print("⏭️  Skipping break...\n")
                except KeyboardInterrupt:
                    print("\n\n❌ Pomodoro cancelled.")
                    self._save_incomplete_pomodoro(
                        pomodoro_start_time, completed_work_sessions)
                    return

        # Save completed pomodoro immediately (all 4 work sessions done)
        self._save_completed_pomodoro(pomodoro_start_time)

        # Long break after completing all 4 sessions
        print("\n🎉 ALL WORK SESSIONS COMPLETE!")
        print("Take a long break? (y/n): ", end='', flush=True)

        try:
            response = input().strip().lower()
            if response == 'y' or response == '':
                self.countdown(self.long_break_duration, 'long_break')
            else:
                print("⏭️  Skipping long break...\n")
        except KeyboardInterrupt:
            print("\n\nSkipping long break.")

        print("\n" + "=" * 48)
        print("✅ POMODORO COMPLETE!")
        total_pomodoros = len(
            [p for p in self.data['pomodoros'] if p['completed']])
        print(f"Total completed: {total_pomodoros}")
        print("=" * 48)

    def _save_completed_pomodoro(self, start_time):
        """Save a completed Pomodoro cycle."""
        if self.test_mode:
            return  # Don't save test runs
        pomodoro = {
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'completed': True,
            'work_sessions': self.WORK_SESSIONS_PER_POMODORO,
            'total_work_minutes': self.WORK_DURATION * self.WORK_SESSIONS_PER_POMODORO
        }
        if 'pomodoros' not in self.data:
            self.data['pomodoros'] = []
        self.data['pomodoros'].append(pomodoro)
        self._save_data()

    def _save_incomplete_pomodoro(self, start_time, completed_sessions):
        """Save an incomplete Pomodoro cycle."""
        if self.test_mode:
            return  # Don't save test runs
        if completed_sessions == 0:
            return  # Don't save if no sessions completed

        pomodoro = {
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'completed': False,
            'work_sessions': completed_sessions,
            'total_work_minutes': self.WORK_DURATION * completed_sessions
        }
        if 'pomodoros' not in self.data:
            self.data['pomodoros'] = []
        self.data['pomodoros'].append(pomodoro)
        self._save_data()

    def print_statistics(self, days=None):
        """Print Pomodoro statistics."""
        if 'pomodoros' not in self.data or not self.data['pomodoros']:
            print("\n📊 No Pomodoros recorded yet. Start your first one!")
            return

        # Filter by date range if specified
        pomodoros = self.data['pomodoros']
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            pomodoros = [
                p for p in pomodoros
                if datetime.fromisoformat(p['start_time']) >= cutoff
            ]

        if not pomodoros:
            print(f"\n📊 No Pomodoros in the last {days} days.")
            return

        # Calculate statistics
        completed_pomodoros = [p for p in pomodoros if p['completed']]
        incomplete_pomodoros = [p for p in pomodoros if not p['completed']]

        total_work_sessions = sum(p['work_sessions'] for p in pomodoros)
        total_work_minutes = sum(p['total_work_minutes'] for p in pomodoros)
        total_work_hours = total_work_minutes / 60

        # Print statistics
        period = f"last {days} days" if days else "all time"
        print(f"\n📊 POMODORO STATISTICS ({period})")
        print("=" * 48)
        print(f"✅ Completed Pomodoros: {len(completed_pomodoros)}")
        if incomplete_pomodoros:
            print(f"⚠️  Incomplete Pomodoros: {len(incomplete_pomodoros)}")
        print(f"🍅 Total work sessions: {total_work_sessions}")
        print(
            f"⏱️  Total work time: {total_work_minutes:.0f} minutes ({total_work_hours:.1f} hours)")

        if completed_pomodoros:
            avg_sessions_per_day = self._calculate_avg_per_day(
                completed_pomodoros, days)
            if avg_sessions_per_day:
                print(
                    f"📈 Average: {avg_sessions_per_day:.1f} work sessions/day")

        # Recent Pomodoros
        print(f"\n📅 Recent:")
        print("-" * 48)
        recent = pomodoros[-10:] if len(pomodoros) > 10 else pomodoros
        for pomo in reversed(recent):
            start = datetime.fromisoformat(pomo['start_time'])
            status = "✅" if pomo['completed'] else "⚠️"
            sessions_info = f"{pomo['work_sessions']}/4 sessions"
            print(
                f"   {status} {start.strftime('%Y-%m-%d %H:%M')} - {sessions_info} ({pomo['total_work_minutes']} min)")

        print()

    def _calculate_avg_per_day(self, pomodoros, days_filter=None):
        """Calculate average sessions per day."""
        if not pomodoros:
            return None

        dates = set()
        for pomo in pomodoros:
            date = datetime.fromisoformat(pomo['start_time']).date()
            dates.add(date)

        num_days = len(dates)
        if num_days == 0:
            return None

        total_sessions = sum(p['work_sessions'] for p in pomodoros)
        return total_sessions / num_days


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Classic Pomodoro timer with macOS notifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The Classic Pomodoro Technique:
  One Pomodoro consists of:
  - 4 work sessions (25 minutes each)
  - 3 short breaks (5 minutes each) between work sessions
  - 1 long break (15-30 minutes) after completing all 4 sessions

Examples:
  python3 pomodoro.py                    # Start a Pomodoro
  python3 pomodoro.py --break 25         # Use 25-min long break
  python3 pomodoro.py --stats            # View all-time stats
  python3 pomodoro.py --stats --week     # View this week's stats
        """
    )

    parser.add_argument(
        '--break',
        type=int,
        default=20,
        metavar='MINUTES',
        dest='long_break',
        help='Long break duration in minutes (default: 20, range: 15-30)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics instead of starting timer'
    )
    parser.add_argument(
        '--week',
        action='store_true',
        help='Show statistics for current week only (use with --stats)'
    )
    parser.add_argument(
        '--month',
        action='store_true',
        help='Show statistics for current month only (use with --stats)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with shortened durations (5 seconds per work session, 3 seconds per break)'
    )

    args = parser.parse_args()

    # Validate long break duration (skip validation in test mode)
    if not args.test and (args.long_break < 15 or args.long_break > 30):
        print("❌ Long break duration must be between 15-30 minutes")
        sys.exit(1)

    timer = PomodoroTimer(long_break_duration=args.long_break, test_mode=args.test)

    # Statistics
    if args.stats:
        days = None
        if args.week:
            days = 7
        elif args.month:
            days = 30
        timer.print_statistics(days=days)
        return

    # Start Pomodoro
    timer.run_pomodoro()


if __name__ == '__main__':
    main()
