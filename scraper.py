#!/usr/bin/env python3
"""
CrossFit Daily WOD Scraper
Runs automatically via GitHub Actions every morning.
Fetches today's WOD from public sources and saves to wod.json
"""

import json
import re
import sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_url(url):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None

def scrape_crossfit_com():
    """Try to scrape crossfit.com/workout/YYYY/MM/DD"""
    today = datetime.now(timezone.utc)
    url = f"https://www.crossfit.com/workout/{today.strftime('%Y/%m/%d')}"
    print(f"  Trying {url}")
    html = fetch_url(url)
    if not html:
        return None

    # Try to extract the workout title
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    title = title_match.group(1).strip() if title_match else "CrossFit WOD"

    # Try to extract workout content from common patterns
    # Look for workout description in article/main content
    patterns = [
        r'<div[^>]*class="[^"]*workout[^"]*"[^>]*>(.*?)</div>',
        r'<article[^>]*>(.*?)</article>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<p>((?:(?:For time|AMRAP|Every|Complete|As many)[^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)+)</p>',
    ]

    workout_text = ""
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for m in matches:
            # Strip HTML tags
            clean = re.sub(r'<[^>]+>', ' ', m)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if len(clean) > 50 and any(kw in clean.lower() for kw in ['round', 'rep', 'time', 'amrap', 'minute', 'meter', 'lb', 'kg']):
                workout_text = clean[:800]
                break
        if workout_text:
            break

    if workout_text:
        return {
            "source": "crossfit.com",
            "title": title,
            "description": workout_text,
            "url": url
        }
    return None

def scrape_wodwell():
    """Fallback: scrape WODwell's featured WOD"""
    url = "https://wodwell.com/wod/"
    print(f"  Trying {url}")
    html = fetch_url(url)
    if not html:
        return None

    # Look for workout descriptions
    patterns = [
        r'<div[^>]*class="[^"]*wod-description[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*workout-text[^"]*"[^>]*>(.*?)</div>',
        r'"description"\s*:\s*"([^"]{30,400})"',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        if matches:
            clean = re.sub(r'<[^>]+>', ' ', matches[0])
            clean = re.sub(r'\s+', ' ', clean).strip()
            if len(clean) > 30:
                return {
                    "source": "wodwell.com",
                    "title": "WOD of the Day",
                    "description": clean[:600],
                    "url": url
                }
    return None

def generate_manual_wod():
    """
    Last resort: generate a WOD from a rotating pool of classics.
    This ensures the site always shows something even if scraping fails.
    """
    today = datetime.now(timezone.utc)
    day_of_year = today.timetuple().tm_yday

    wods = [
        {"title": "Fran", "description": "21-15-9 Reps for Time:\n• Thrusters @ 95/65 lb\n• Pull-Ups", "type": "For Time"},
        {"title": "Helen", "description": "3 Rounds for Time:\n• 400m Run\n• 21 KB Swings @ 53/35 lb\n• 12 Pull-Ups", "type": "For Time"},
        {"title": "Cindy", "description": "AMRAP in 20 min:\n• 5 Pull-Ups\n• 10 Push-Ups\n• 15 Air Squats", "type": "AMRAP"},
        {"title": "Diane", "description": "21-15-9 Reps for Time:\n• Deadlift @ 225/155 lb\n• Handstand Push-Ups", "type": "For Time"},
        {"title": "Grace", "description": "30 Clean & Jerks for Time @ 135/95 lb\nGoal: unbroken or minimal sets", "type": "For Time"},
        {"title": "Isabel", "description": "30 Snatches for Time @ 135/95 lb\nGoal: unbroken or minimal touch-and-go sets", "type": "For Time"},
        {"title": "Karen", "description": "150 Wall Ball Shots for Time\n• Men: 20 lb to 10 ft\n• Women: 14 lb to 9 ft", "type": "For Time"},
        {"title": "Mary", "description": "AMRAP in 20 min:\n• 5 Handstand Push-Ups\n• 10 Pistol Squats (alternating)\n• 15 Pull-Ups", "type": "AMRAP"},
        {"title": "Nancy", "description": "5 Rounds for Time:\n• 400m Run\n• 15 Overhead Squats @ 95/65 lb", "type": "For Time"},
        {"title": "Annie", "description": "50-40-30-20-10 Reps for Time:\n• Double Unders\n• Sit-Ups", "type": "For Time"},
        {"title": "Jackie", "description": "For Time:\n• 1,000m Row\n• 50 Thrusters @ 45/35 lb\n• 30 Pull-Ups", "type": "For Time"},
        {"title": "Kelly", "description": "5 Rounds for Time:\n• 400m Run\n• 30 Box Jumps @ 24/20\"\n• 30 Wall Ball Shots @ 20/14 lb", "type": "For Time"},
        {"title": "DT", "description": "5 Rounds for Time:\n• 12 Deadlifts @ 155/105 lb\n• 9 Hang Power Cleans @ 155/105 lb\n• 6 Push Jerks @ 155/105 lb\n(same barbell throughout)", "type": "For Time"},
        {"title": "Nate", "description": "AMRAP in 20 min:\n• 2 Muscle-Ups\n• 4 Handstand Push-Ups\n• 8 KB Swings @ 70/53 lb", "type": "AMRAP"},
        {"title": "The Chief", "description": "5 × 3-minute AMRAPs, rest 1 min between:\n• 3 Power Cleans @ 135/95 lb\n• 6 Push-Ups\n• 9 Air Squats", "type": "AMRAP"},
        {"title": "Fight Gone Bad", "description": "3 Rounds — 1 min/station, 1 min rest:\n• Wall Ball @ 20/14 lb\n• Sumo DL High Pull @ 75/55 lb\n• Box Jump @ 20\"\n• Push Press @ 75/55 lb\n• Row (calories)", "type": "For Score"},
        {"title": "Eva", "description": "5 Rounds for Time:\n• 800m Run\n• 30 KB Swings @ 70/53 lb\n• 30 Pull-Ups", "type": "For Time"},
        {"title": "Randy", "description": "75 Power Snatches for Time @ 75/55 lb\nHero WOD — In honor of Randy Simmons, LAPD SWAT, KIA 2008", "type": "For Time"},
        {"title": "Murph", "description": "For Time (w/ 20/14 lb vest):\n• 1 Mile Run\n• 100 Pull-Ups\n• 200 Push-Ups\n• 300 Air Squats\n• 1 Mile Run\nPartition as needed.", "type": "For Time"},
        {"title": "Tommy V", "description": "For Time:\n• 21 Thrusters @ 115/75 lb → 12 Rope Climbs (15 ft)\n• 15 Thrusters → 9 Rope Climbs\n• 9 Thrusters → 6 Rope Climbs", "type": "For Time"},
        {"title": "Elizabeth", "description": "21-15-9 Reps for Time:\n• Squat Clean @ 135/95 lb\n• Ring Dips", "type": "For Time"},
        {"title": "Holleyman", "description": "AMRAP in 20 min:\n• 5 Wall Ball @ 20/14 lb\n• 3 Handstand Push-Ups\n• 1 Power Clean @ 225/155 lb\nHero WOD", "type": "AMRAP"},
        {"title": "Danny", "description": "AMRAP in 20 min:\n• 30 Box Jumps @ 24/20\"\n• 20 Push Press @ 115/75 lb\n• 30 Pull-Ups\nHero WOD", "type": "AMRAP"},
        {"title": "Hansen", "description": "5 Rounds for Time:\n• 30 KB Swings @ 70/53 lb\n• 30 Burpees\n• 30 GHD Sit-Ups\nHero WOD", "type": "For Time"},
        {"title": "The Seven", "description": "7 Rounds for Time:\n• 7 HSPU  •  7 Thrusters @ 135/95 lb\n• 7 Knees-to-Elbows  •  7 Deadlifts @ 245/165 lb\n• 7 Burpees  •  7 KB Swings @ 70/53 lb  •  7 Pull-Ups\nHero WOD — In honor of 7 CIA officers, KIA 2009", "type": "For Time"},
        {"title": "Jack", "description": "AMRAP in 20 min:\n• 10 Push Press @ 115/75 lb\n• 10 KB Swings @ 53/35 lb\n• 10 Box Jumps @ 24/20\"\nHero WOD", "type": "AMRAP"},
        {"title": "Loredo", "description": "6 Rounds for Time:\n• 24 Air Squats\n• 24 Push-Ups\n• 24 Walking Lunges\n• 400m Run\nHero WOD", "type": "For Time"},
        {"title": "Nasty Girls", "description": "3 Rounds for Time:\n• 50 Air Squats\n• 7 Muscle-Ups\n• 10 Hang Power Cleans @ 135/95 lb", "type": "For Time"},
        {"title": "Tabata This!", "description": "Tabata intervals (8×20 sec on / 10 sec off) per movement:\n• Row → Squat → Pull-Up → Push-Up → Sit-Up\nRest 1 min between movements", "type": "Tabata"},
        {"title": "CrossFit Total", "description": "3 attempts each to find 1-rep max:\n• Back Squat\n• Strict Press\n• Deadlift\nScore = sum of heaviest successful lift", "type": "For Load"},
        {"title": "Wittman", "description": "7 Rounds for Time:\n• 15 KB Swings @ 53/35 lb\n• 15 Power Cleans @ 95/65 lb\n• 15 Box Jumps @ 24/20\"\nHero WOD", "type": "For Time"},
        {"title": "Badger", "description": "3 Rounds for Time:\n• 30 Squat Cleans @ 95/65 lb\n• 30 Pull-Ups\n• 800m Run\nHero WOD", "type": "For Time"},
        {"title": "Kalsu", "description": "For Time:\n• 100 Thrusters @ 135/95 lb\n• 5 Burpees at the start AND at the top of every minute\nHero WOD — arguably the hardest Hero WOD", "type": "For Time"},
        {"title": "Linda", "description": "10-9-8-7-6-5-4-3-2-1 Reps for Time:\n• Deadlift @ 1.5× BW\n• Bench Press @ 1× BW\n• Clean @ 0.75× BW\nNicknamed: 3 Bars of Death", "type": "For Time"},
        {"title": "Lynne", "description": "5 Rounds for Max Reps:\n• Bench Press @ bodyweight\n• Pull-Ups\nNo time cap. Rest as needed.", "type": "For Load"},
        {"title": "The Filthy Fifty", "description": "For Time:\n• 50 Box Jumps @ 24/20\"  •  50 Jumping Pull-Ups\n• 50 KB Swings @ 35/26 lb  •  50 Walking Lunges\n• 50 KTE  •  50 Push Press @ 45/35 lb\n• 50 Back Extensions  •  50 Wall Ball @ 20/14 lb\n• 50 Burpees  •  50 Double Unders", "type": "For Time"},
        {"title": "Gwen", "description": "15-12-9 Reps for Load:\n• Clean & Jerks (touch-and-go, unbroken sets)\nSame load for all 3 sets. Rest as needed.", "type": "For Load"},
    ]

    # Rotate through WODs based on day of year
    wod = wods[day_of_year % len(wods)]
    return {
        "source": "rotation",
        "title": wod["title"],
        "description": wod["description"],
        "type": wod.get("type", "For Time"),
        "url": "https://www.crossfit.com/workout",
        "note": "Rotating classic WOD (live scrape unavailable today)"
    }

def main():
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%Y-%m-%d")
    day_name = today.strftime("%A, %B %-d, %Y")

    print(f"Fetching WOD for {date_str}...")

    wod_data = None

    # Try sources in order
    print("Attempting crossfit.com...")
    wod_data = scrape_crossfit_com()

    if not wod_data:
        print("Attempting wodwell.com...")
        wod_data = scrape_wodwell()

    if not wod_data:
        print("Using rotating classic WOD fallback...")
        wod_data = generate_manual_wod()

    output = {
        "date": date_str,
        "day": day_name,
        "fetched_at": today.isoformat(),
        "wod": wod_data
    }

    with open("wod.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSuccess! WOD saved to wod.json")
    print(f"  Source: {wod_data.get('source', 'unknown')}")
    print(f"  Title:  {wod_data.get('title', 'N/A')}")
    print(f"  Desc:   {wod_data.get('description', '')[:80]}...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
