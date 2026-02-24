import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

WAKATIME_API_KEY = os.environ.get("WAKATIME_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER = "Hamdan772"


def fetch_wakatime_stats():
    """Fetch stats from WakaTime API."""
    url = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {WAKATIME_API_KEY}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())["data"]
    except Exception as e:
        print(f"WakaTime API error: {e}")
        return None


def fetch_github_profile_views():
    """Fetch profile view count from GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_USER}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("watchers_count", 0)
    except Exception:
        return 0


def fetch_total_lines():
    """Estimate total lines of code across repos."""
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&type=owner"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    total = 0
    try:
        with urllib.request.urlopen(req) as resp:
            repos = json.loads(resp.read().decode())
            for repo in repos:
                total += repo.get("size", 0)
        # Rough estimate: 1 KB ≈ 25 lines of code
        return total * 25
    except Exception:
        return 0


def format_number(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_time(seconds):
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} hrs {mins} mins"
    return f"{mins} mins"


def make_bar_blocks(pct):
    """Create a 25-char block bar like ███░░░░░░░░░░░░░░░░░░░░░░"""
    filled = round(pct / 4)
    return "█" * filled + "░" * (25 - filled)


# ── Default / fallback data ──

defaults = {
    "code_time": "7 hrs 31 mins",
    "profile_views": "1,247",
    "lines_of_code": "142.8K",
    "timezone": "Asia/Dubai",
    "days": [
        {"name": "Monday", "commits": 1038, "pct": 11.95},
        {"name": "Tuesday", "commits": 1231, "pct": 14.17},
        {"name": "Wednesday", "commits": 1235, "pct": 14.22},
        {"name": "Thursday", "commits": 1038, "pct": 11.95},
        {"name": "Friday", "commits": 917, "pct": 10.56},
        {"name": "Saturday", "commits": 1422, "pct": 16.37},
        {"name": "Sunday", "commits": 1806, "pct": 20.79},
    ],
    "languages": [
        {"name": "TypeScript", "time": "6 hrs 29 mins", "pct": 86.16, "color": "#3178c6"},
        {"name": "Markdown", "time": "41 mins", "pct": 9.08, "color": "#083fa1"},
        {"name": "JSON", "time": "9 mins", "pct": 2.19, "color": "#a7a7a7"},
        {"name": "textmate", "time": "5 mins", "pct": 1.23, "color": "#e38c00"},
        {"name": "JavaScript", "time": "2 mins", "pct": 0.63, "color": "#f1e05a"},
    ],
    "editors": [
        {"name": "WebStorm", "time": "7 hrs 31 mins", "pct": 100.0, "color": "#07c3f2"},
    ],
    "os": [
        {"name": "Mac", "time": "7 hrs 31 mins", "pct": 100.0},
    ],
}

LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Markdown": "#083fa1",
    "JSON": "#a7a7a7",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Bash": "#89e051",
    "Shell Script": "#89e051",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Vue.js": "#41b883",
    "YAML": "#cb171e",
    "TOML": "#9c4221",
    "XML": "#0060ac",
    "SQL": "#e38c00",
    "GraphQL": "#e10098",
    "textmate": "#e38c00",
    "Other": "#8b949e",
}

EDITOR_COLORS = {
    "WebStorm": "#07c3f2",
    "VS Code": "#007ACC",
    "IntelliJ IDEA": "#FE315D",
    "PyCharm": "#21D789",
    "Neovim": "#57A143",
    "Vim": "#019733",
    "Sublime Text": "#FF9800",
    "Atom": "#66595C",
    "Other": "#8b949e",
}


def get_data():
    """Try to fetch live data from WakaTime, fall back to defaults."""
    data = dict(defaults)

    waka = fetch_wakatime_stats()
    if waka:
        # Code time
        total_secs = waka.get("total_seconds", 0)
        if total_secs > 0:
            data["code_time"] = format_time(int(total_secs))

        # Languages
        langs = waka.get("languages", [])
        if langs:
            data["languages"] = []
            for lang in langs[:5]:
                color = LANG_COLORS.get(lang["name"], "#8b949e")
                data["languages"].append({
                    "name": lang["name"],
                    "time": lang.get("text", "0 mins"),
                    "pct": lang.get("percent", 0),
                    "color": color,
                })

        # Editors
        editors = waka.get("editors", [])
        if editors:
            data["editors"] = []
            for editor in editors[:3]:
                color = EDITOR_COLORS.get(editor["name"], "#8b949e")
                data["editors"].append({
                    "name": editor["name"],
                    "time": editor.get("text", "0 mins"),
                    "pct": editor.get("percent", 0),
                    "color": color,
                })

        # OS
        oses = waka.get("operating_systems", [])
        if oses:
            data["os"] = []
            for o in oses[:3]:
                data["os"].append({
                    "name": o["name"],
                    "time": o.get("text", "0 mins"),
                    "pct": o.get("percent", 0),
                })

    # Profile views
    views = fetch_github_profile_views()
    if views:
        data["profile_views"] = f"{views:,}"

    # Lines of code
    lines = fetch_total_lines()
    if lines:
        data["lines_of_code"] = format_number(lines)

    return data


def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── SVG Generation ──

def generate_stats_svg(data, theme="dark"):
    is_dark = theme == "dark"
    bg = "#0d1117" if is_dark else "#ffffff"
    border = "#21262d" if is_dark else "#d0d7de"
    text_primary = "#e6edf3" if is_dark else "#1f2328"
    text_secondary = "#8b949e" if is_dark else "#656d76"
    c1 = "#38bdf8" if is_dark else "#0969da"
    c2 = "#818cf8" if is_dark else "#8250df"
    c3 = "#c084fc" if is_dark else "#8250df"
    g_start = c1
    g_end = c3

    return f'''<svg width="800" height="180" viewBox="0 0 800 180" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{g_start}"/>
    <stop offset="100%" stop-color="{g_end}"/>
  </linearGradient>
</defs>
<rect width="800" height="180" rx="12" fill="{bg}" stroke="{border}" stroke-width="1"/>
<g transform="translate(133, 90)">
  <text y="-40" text-anchor="middle" fill="{c1}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28">⏱️</text>
  <text y="-5" text-anchor="middle" fill="{text_primary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="24" font-weight="bold">{xml_escape(data["code_time"])}</text>
  <text y="25" text-anchor="middle" fill="{text_secondary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="13" letter-spacing="1.5">Code Time</text>
</g>
<g transform="translate(400, 90)">
  <text y="-40" text-anchor="middle" fill="{c2}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28">👁️</text>
  <text y="-5" text-anchor="middle" fill="{text_primary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="24" font-weight="bold">{xml_escape(data["profile_views"])}</text>
  <text y="25" text-anchor="middle" fill="{text_secondary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="13" letter-spacing="1.5">Profile Views</text>
</g>
<g transform="translate(667, 90)">
  <text y="-40" text-anchor="middle" fill="{c3}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28">💻</text>
  <text y="-5" text-anchor="middle" fill="{text_primary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="24" font-weight="bold">{xml_escape(data["lines_of_code"])}</text>
  <text y="25" text-anchor="middle" fill="{text_secondary}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="13" letter-spacing="1.5">Lines of Code</text>
</g>
<rect x="50" y="160" width="700" height="2" rx="1" fill="url(#accent)" opacity="0.4"/>
</svg>'''


def generate_activity_svg(data, theme="dark"):
    is_dark = theme == "dark"
    bg = "#0d1117" if is_dark else "#ffffff"
    border = "#21262d" if is_dark else "#d0d7de"
    divider = "#21262d" if is_dark else "#d0d7de"
    text_primary = "#e6edf3" if is_dark else "#1f2328"
    text_secondary = "#8b949e" if is_dark else "#656d76"
    text_mono = "#c9d1d9" if is_dark else "#1f2328"
    bar_bg = "#161b22" if is_dark else "#eaeef2"
    bar_blue = "#58a6ff" if is_dark else "#0969da"
    bar_opacity = "0.85" if is_dark else "0.75"
    os_color = "#c084fc" if is_dark else "#8250df"
    os_opacity = "0.7" if is_dark else "0.5"

    g_start = "#38bdf8" if is_dark else "#0969da"
    g_mid = "#818cf8" if is_dark else "#8250df"
    g_end = "#c084fc" if is_dark else "#8250df"

    now = datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")

    lines = []
    lines.append(f'<svg width="880" height="720" viewBox="0 0 880 720" xmlns="http://www.w3.org/2000/svg">')
    lines.append('<defs>')
    lines.append(f'  <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">')
    lines.append(f'    <stop offset="0%" stop-color="{g_start}"/>')
    lines.append(f'    <stop offset="50%" stop-color="{g_mid}"/>')
    lines.append(f'    <stop offset="100%" stop-color="{g_end}"/>')
    lines.append(f'  </linearGradient>')
    lines.append(f'  <linearGradient id="bar1" x1="0%" y1="0%" x2="100%" y2="0%">')
    lines.append(f'    <stop offset="0%" stop-color="{g_start}"/>')
    lines.append(f'    <stop offset="100%" stop-color="{g_mid}"/>')
    lines.append(f'  </linearGradient>')
    lines.append('</defs>')
    lines.append(f'<rect width="880" height="720" rx="12" fill="{bg}" stroke="{border}" stroke-width="1"/>')

    # Title
    lines.append(f'<text x="440" y="40" text-anchor="middle" fill="url(#accent)" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="18" font-weight="bold" letter-spacing="2">📊 WEEKLY DEV ACTIVITY</text>')
    lines.append(f'<rect x="90" y="52" width="700" height="1" rx="0.5" fill="url(#accent)" opacity="0.3"/>')

    # Timezone
    lines.append(f'<text x="440" y="76" text-anchor="middle" fill="{text_secondary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="13">🕑︎ Time Zone: {data["timezone"]}</text>')

    # Commits by Day
    lines.append(f'<text x="60" y="112" fill="{text_primary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="14" font-weight="bold">📅 Commits by Day of Week</text>')

    max_commits = max(d["commits"] for d in data["days"])
    for i, day in enumerate(data["days"]):
        y_text = 142 + i * 26
        y_bar = y_text - 12
        bar_w = max(3, int(161 * day["commits"] / max_commits))
        blocks = make_bar_blocks(day["pct"])
        lines.append(f'<text x="60" y="{y_text}" fill="{text_mono}" font-family="\'Courier New\', monospace" font-size="12.5">{day["name"]}</text>')
        lines.append(f'<rect x="180" y="{y_bar}" width="161" height="16" rx="3" fill="{bar_bg}"/>')
        lines.append(f'<rect x="180" y="{y_bar}" width="{bar_w}" height="16" rx="3" fill="url(#bar1)" opacity="{bar_opacity}"/>')
        lines.append(f'<text x="354" y="{y_text}" fill="{text_secondary}" font-family="\'Courier New\', monospace" font-size="11">{day["commits"]:,} commits</text>')
        lines.append(f'<text x="510" y="{y_text}" fill="{bar_blue}" font-family="\'Courier New\', monospace" font-size="11">{blocks}</text>')
        lines.append(f'<text x="780" y="{y_text}" fill="{text_secondary}" font-family="\'Courier New\', monospace" font-size="11" text-anchor="end">{day["pct"]:.2f}%</text>')

    # Divider
    lines.append(f'<rect x="90" y="320" width="700" height="1" rx="0.5" fill="{divider}"/>')

    # Languages
    lines.append(f'<text x="60" y="352" fill="{text_primary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="14" font-weight="bold">💬 Programming Languages</text>')

    for i, lang in enumerate(data["languages"]):
        y_text = 382 + i * 26
        y_bar = y_text - 12
        bar_w = max(3, int(400 * lang["pct"] / 100))
        color = lang.get("color", "#8b949e")
        lines.append(f'<text x="60" y="{y_text}" fill="{text_mono}" font-family="\'Courier New\', monospace" font-size="12.5">{xml_escape(lang["name"])}</text>')
        lines.append(f'<rect x="200" y="{y_bar}" width="400" height="16" rx="3" fill="{bar_bg}"/>')
        lines.append(f'<rect x="200" y="{y_bar}" width="{bar_w}" height="16" rx="3" fill="{color}" opacity="{bar_opacity}"/>')
        lines.append(f'<text x="620" y="{y_text}" fill="{text_secondary}" font-family="\'Courier New\', monospace" font-size="11">{xml_escape(lang["time"])}</text>')
        lines.append(f'<text x="780" y="{y_text}" fill="{color}" font-family="\'Courier New\', monospace" font-size="11" text-anchor="end">{lang["pct"]:.2f}%</text>')

    # Divider
    lines.append(f'<rect x="90" y="508" width="700" height="1" rx="0.5" fill="{divider}"/>')

    # Editors
    lines.append(f'<text x="60" y="540" fill="{text_primary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="14" font-weight="bold">🔥 Editors</text>')

    for i, editor in enumerate(data["editors"]):
        y_text = 570 + i * 26
        y_bar = y_text - 12
        bar_w = max(3, int(400 * editor["pct"] / 100))
        color = editor.get("color", "#8b949e")
        lines.append(f'<text x="60" y="{y_text}" fill="{text_mono}" font-family="\'Courier New\', monospace" font-size="12.5">{xml_escape(editor["name"])}</text>')
        lines.append(f'<rect x="200" y="{y_bar}" width="400" height="16" rx="3" fill="{bar_bg}"/>')
        lines.append(f'<rect x="200" y="{y_bar}" width="{bar_w}" height="16" rx="3" fill="{color}" opacity="0.7"/>')
        lines.append(f'<text x="620" y="{y_text}" fill="{text_secondary}" font-family="\'Courier New\', monospace" font-size="11">{xml_escape(editor["time"])}</text>')
        lines.append(f'<text x="780" y="{y_text}" fill="{color}" font-family="\'Courier New\', monospace" font-size="11" text-anchor="end">{editor["pct"]:.2f}%</text>')

    # Divider
    lines.append(f'<rect x="90" y="592" width="700" height="1" rx="0.5" fill="{divider}"/>')

    # OS
    lines.append(f'<text x="60" y="624" fill="{text_primary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="14" font-weight="bold">💻 Operating System</text>')

    for i, o in enumerate(data["os"]):
        y_text = 654 + i * 26
        y_bar = y_text - 12
        bar_w = max(3, int(400 * o["pct"] / 100))
        lines.append(f'<text x="60" y="{y_text}" fill="{text_mono}" font-family="\'Courier New\', monospace" font-size="12.5">{xml_escape(o["name"])}</text>')
        lines.append(f'<rect x="200" y="{y_bar}" width="400" height="16" rx="3" fill="{bar_bg}"/>')
        lines.append(f'<rect x="200" y="{y_bar}" width="{bar_w}" height="16" rx="3" fill="{os_color}" opacity="{os_opacity}"/>')
        lines.append(f'<text x="620" y="{y_text}" fill="{text_secondary}" font-family="\'Courier New\', monospace" font-size="11">{xml_escape(o["time"])}</text>')
        lines.append(f'<text x="780" y="{y_text}" fill="{os_color}" font-family="\'Courier New\', monospace" font-size="11" text-anchor="end">{o["pct"]:.2f}%</text>')

    # Bottom
    lines.append(f'<rect x="90" y="690" width="700" height="2" rx="1" fill="url(#accent)" opacity="0.4"/>')
    lines.append(f'<text x="440" y="712" text-anchor="middle" fill="{text_secondary}" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="10">Last Updated: {now} • Hamdan772/Hamdan772</text>')
    lines.append('</svg>')

    return "\n".join(lines)


def main():
    data = get_data()

    # Stats SVGs
    with open("stats_dark.svg", "w") as f:
        f.write(generate_stats_svg(data, "dark"))
    with open("stats_light.svg", "w") as f:
        f.write(generate_stats_svg(data, "light"))

    # Activity SVGs
    with open("dev_activity_dark.svg", "w") as f:
        f.write(generate_activity_svg(data, "dark"))
    with open("dev_activity_light.svg", "w") as f:
        f.write(generate_activity_svg(data, "light"))

    print("✅ All SVGs generated successfully!")


if __name__ == "__main__":
    main()
