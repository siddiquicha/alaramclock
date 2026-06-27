#!/usr/bin/env python3
"""
Alarm Clock - Python CLI Application
Features: set multiple alarms, list/delete alarms, snooze, sound alert
"""

import time
import datetime
import threading
import sys
import os
import argparse

# Try to use platform sound; fall back to terminal bell
def play_alarm_sound(duration=5):
    """Play alarm sound using available system tools."""
    start = time.time()
    while time.time() - start < duration:
        # Terminal bell character + visual flash
        sys.stdout.write('\a')
        sys.stdout.flush()
        print("🔔 ALARM RINGING! 🔔", flush=True)
        time.sleep(0.5)

# ── Data store (in-memory) ────────────────────────────────────────────────────

alarms: list[dict] = []          # {"id": int, "time": datetime.time, "label": str, "active": bool}
_alarm_id_counter = 0

def _next_id() -> int:
    global _alarm_id_counter
    _alarm_id_counter += 1
    return _alarm_id_counter

# ── Alarm logic ───────────────────────────────────────────────────────────────

def add_alarm(alarm_time: str, label: str = "Alarm") -> dict:
    """Parse HH:MM or HH:MM:SS and schedule an alarm."""
    try:
        if alarm_time.count(":") == 1:
            t = datetime.datetime.strptime(alarm_time, "%H:%M").time()
        else:
            t = datetime.datetime.strptime(alarm_time, "%H:%M:%S").time()
    except ValueError:
        raise ValueError(f"Invalid time format '{alarm_time}'. Use HH:MM or HH:MM:SS.")

    alarm = {"id": _next_id(), "time": t, "label": label, "active": True}
    alarms.append(alarm)
    return alarm


def delete_alarm(alarm_id: int) -> bool:
    for alarm in alarms:
        if alarm["id"] == alarm_id:
            alarm["active"] = False
            alarms.remove(alarm)
            return True
    return False


def list_alarms():
    active = [a for a in alarms if a["active"]]
    if not active:
        print("  (no alarms set)")
        return
    print(f"  {'ID':<4} {'Time':<10} {'Label'}")
    print("  " + "-" * 30)
    for a in active:
        print(f"  {a['id']:<4} {a['time'].strftime('%H:%M:%S'):<10} {a['label']}")


def seconds_until(t: datetime.time) -> float:
    """Seconds from now until the next occurrence of time t."""
    now = datetime.datetime.now()
    target = now.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def _alarm_thread(alarm: dict, snooze_minutes: int):
    """Background thread: sleeps until alarm time, then fires."""
    wait = seconds_until(alarm["time"])
    label = alarm["label"]
    alarm_id = alarm["id"]

    print(f"\n  ⏰  Alarm '{label}' set for {alarm['time'].strftime('%H:%M:%S')} "
          f"(in {int(wait//3600):02d}:{int((wait%3600)//60):02d}:{int(wait%60):02d})\n",
          flush=True)

    time.sleep(wait)

    # Check if still active (user may have deleted it)
    if not any(a["id"] == alarm_id and a["active"] for a in alarms):
        return

    print(f"\n{'='*40}", flush=True)
    print(f"  ⏰  ALARM: {label}  [{alarm['time'].strftime('%H:%M:%S')}]", flush=True)
    print(f"{'='*40}\n", flush=True)

    play_alarm_sound(duration=5)

    # Snooze prompt (only in interactive mode)
    if sys.stdin.isatty():
        try:
            ans = input(f"  Snooze for {snooze_minutes} min? [y/N]: ").strip().lower()
            if ans == "y":
                snooze_alarm(alarm, snooze_minutes)
        except (EOFError, KeyboardInterrupt):
            pass


def snooze_alarm(alarm: dict, minutes: int):
    """Re-schedule an alarm <minutes> from now."""
    now = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    new_time = now.time().replace(microsecond=0)
    snooze_entry = {
        "id": _next_id(),
        "time": new_time,
        "label": alarm["label"] + " (snooze)",
        "active": True,
    }
    alarms.append(snooze_entry)
    t = threading.Thread(target=_alarm_thread, args=(snooze_entry, minutes), daemon=True)
    t.start()
    print(f"  💤  Snoozed until {new_time.strftime('%H:%M:%S')}", flush=True)


# ── Interactive REPL ──────────────────────────────────────────────────────────

HELP_TEXT = """
Commands:
  set  HH:MM [label]   – Set a new alarm (24-hour clock)
  list                 – Show all active alarms
  delete <id>          – Cancel an alarm by ID
  time                 – Show current time
  help                 – Show this help
  quit / exit          – Exit the alarm clock
"""


def repl(snooze_minutes: int = 5):
    print("\n🕐  Python CLI Alarm Clock  🕐")
    print("Type 'help' for commands.\n")
    threads: list[threading.Thread] = []

    while True:
        try:
            raw = input("alarm> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            print("Goodbye!")
            break

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "time":
            print(f"  Current time: {datetime.datetime.now().strftime('%H:%M:%S')}")

        elif cmd == "list":
            list_alarms()

        elif cmd == "set":
            if len(parts) < 2:
                print("  Usage: set HH:MM [label]")
                continue
            alarm_time = parts[1]
            label = parts[2] if len(parts) == 3 else "Alarm"
            try:
                alarm = add_alarm(alarm_time, label)
                t = threading.Thread(
                    target=_alarm_thread, args=(alarm, snooze_minutes), daemon=True
                )
                t.start()
                threads.append(t)
            except ValueError as e:
                print(f"  ❌  {e}")

        elif cmd == "delete":
            if len(parts) < 2 or not parts[1].isdigit():
                print("  Usage: delete <id>")
                continue
            if delete_alarm(int(parts[1])):
                print(f"  ✅  Alarm {parts[1]} deleted.")
            else:
                print(f"  ❌  No alarm with id {parts[1]}.")

        else:
            print(f"  Unknown command '{cmd}'. Type 'help' for help.")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="⏰  Python CLI Alarm Clock",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python alarm_clock.py                        # interactive mode
  python alarm_clock.py --set 07:30            # set alarm at start
  python alarm_clock.py --set 07:30 "Wake up"  # set alarm with label
  python alarm_clock.py --snooze 10            # custom snooze (minutes)
        """,
    )
    parser.add_argument("--set", metavar="HH:MM", help="Pre-set an alarm on launch")
    parser.add_argument("label", nargs="?", default="Alarm", help="Label for --set alarm")
    parser.add_argument(
        "--snooze", type=int, default=5, metavar="MINUTES",
        help="Snooze duration in minutes (default: 5)"
    )
    args = parser.parse_args()

    if args.set:
        try:
            alarm = add_alarm(args.set, args.label)
            t = threading.Thread(
                target=_alarm_thread, args=(alarm, args.snooze), daemon=True
            )
            t.start()
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    repl(snooze_minutes=args.snooze)


if __name__ == "__main__":
    main()
