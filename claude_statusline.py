#!/usr/bin/env python3
"""Claude Code statusline: Anthropic usage limits.

Usage: python3 claude_statusline.py <config_dir>
  config_dir: REQUIRED — the Claude profile directory containing
              .credentials.json and settings.json (e.g., ~/.claude).
              This is NOT the directory the script lives in — unless you
              deliberately placed the script inside the config dir.

--- AGENT SETUP INSTRUCTIONS ---
To enable this statusline for a Claude Code profile:

1. Find the config directory by looking at the current session's auto-memory
   path. The memory path follows the pattern:
     <config-dir>/projects/<project-hash>/memory/MEMORY.md
   The config directory is the root of that path — everything before /projects/.
   For example, if the memory file is at:
     C:/Users/ahmad/.claude/projects/C--my-project/memory/MEMORY.md
   then the config directory is: C:/Users/ahmad/.claude

2. The config_dir argument is REQUIRED. The command MUST include it.
   Add this to settings.json inside that config directory (merge with existing keys):
   {
     "statusLine": {
       "type": "command",
       "command": "python3 <absolute-path-to-this-file> <config-dir>"
     }
   }

   Example (if config dir is ~/.claude/):
   "command": "python3 C:/Users/ahmad/claude_statusline.py C:/Users/ahmad/.claude"

3. The config dir MUST contain .credentials.json (Claude Code creates this
   automatically when the user authenticates).

4. A .usage_cache.json file will be created in the config dir at runtime.
   Do not create it manually.

5. Requires Python 3.7+ (stdlib only, no pip dependencies).
"""
import sys, json, os, time, urllib.request
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=-6))

CONFIG_DIR = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(CONFIG_DIR, ".usage_cache.json")
CRED_FILE = os.path.join(CONFIG_DIR, ".credentials.json")
CACHE_TTL = 120  # seconds between API refreshes


def fetch_usage():
    # Try cache first
    try:
        if os.path.exists(CACHE_FILE):
            age = time.time() - os.path.getmtime(CACHE_FILE)
            if age < CACHE_TTL:
                with open(CACHE_FILE) as f:
                    return json.load(f)
    except Exception:
        pass

    # Fetch fresh from API
    try:
        with open(CRED_FILE) as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]

        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
                "User-Agent": "claude-code/2.0.31",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)

        return data
    except Exception:
        # Fall back to stale cache
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}


def format_duration(delta):
    total_sec = max(0, int(delta.total_seconds()))
    total_min = total_sec // 60
    if total_min < 60:
        return f"{total_min}min"
    h, rem_sec = divmod(total_sec, 3600)
    m, s = divmod(rem_sec, 60)
    if h < 24:
        return f"{h}h {m}m" if m else f"{h}h"
    days = total_min / 1440
    return f"{days:.1f}d".replace(".0d", "d")


def format_reset(resets_at):
    if not resets_at:
        return ""
    try:
        dt = datetime.fromisoformat(resets_at.replace("Z", "+00:00")).astimezone(CST)
        now = datetime.now(CST)
        nopad = "#" if os.name == "nt" else "-"  # Windows vs Unix
        h = dt.strftime(f"%{nopad}I:%M%p").lower()
        if h.endswith(":00am") or h.endswith(":00pm"):
            h = h.replace(":00", "")
        delta = dt - now if dt > now else timedelta()
        dur = format_duration(delta) if dt > now else "now"
        show_time = delta.total_seconds() <= 86400
        if dt.date() == now.date():
            return f" ({dur} - {h})"
        elif dt.date() == (now + timedelta(days=1)).date():
            return f" ({dur} - tmrw {h})" if show_time else f" ({dur} - tmrw)"
        else:
            date_str = dt.strftime(f'%{nopad}m/%{nopad}d')
            return f" ({dur} - {date_str} {h})" if show_time else f" ({dur} - {date_str})"
    except Exception:
        return ""


def main():
    usage = fetch_usage()

    parts = []

    five = usage.get("five_hour")
    if five:
        util = five.get("utilization", 0)
        reset_str = format_reset(five.get("resets_at"))
        parts.append(f"5h: {util:.0f}%{reset_str}")

    seven = usage.get("seven_day")
    if seven:
        util = seven.get("utilization", 0)
        reset_str = format_reset(seven.get("resets_at"))
        parts.append(f"7d: {util:.0f}%{reset_str}")

    print("\n".join(parts))


if __name__ == "__main__":
    main()
