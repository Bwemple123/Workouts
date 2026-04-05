# CrossFit WOD Library

A self-hosted CrossFit workout library with **200+ workouts** and a **daily auto-updating WOD**.

## What's inside

- **Benchmark Girls** — 31 classic benchmark WODs (Fran, Helen, Murph, etc.)
- **Hero WODs** — 32 hero workouts (Murph, DT, The Seven, Kalsu, etc.)
- **CrossFit Open 2015–2025** — every Open workout for 11 years
- **Josh Bridges workouts** — Pay the Man style WODs
- **Noah Ohlsen — Road to the Games** — 10 advanced sessions
- **Daily WOD** — auto-fetched every morning at 6 AM UTC via GitHub Actions

## Features
- Search by movement, name, or weight
- Filter by source, year, type, duration, or completion status
- Mark workouts as done
- Add personal notes / PR log per workout
- Random WOD button
- Dark athletic theme

---

## Deploy in 10 minutes (free forever)

### Step 1 — Create a GitHub account
Go to [github.com](https://github.com) and sign up (free).

### Step 2 — Create a new repository
1. Click the **+** button (top right) → **New repository**
2. Name it: `wod-library` (or anything you like)
3. Set it to **Public**
4. Click **Create repository**

### Step 3 — Upload the files
Click **uploading an existing file** and drag in these 4 files:
- `index.html`
- `scraper.py`
- `wod.json`
- `.github/workflows/daily.yml`

> **Important:** The `.github/workflows/` folder structure must be preserved.
> GitHub will prompt you to create the folder — just type `.github/workflows/daily.yml` as the file path.

### Step 4 — Enable GitHub Pages
1. Go to your repo → **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click **Save**

Your site will be live at:
```
https://YOUR-USERNAME.github.io/wod-library
```

### Step 5 — Test the daily scraper
1. Go to your repo → **Actions** tab
2. Click **Daily WOD Scraper** → **Run workflow** → **Run workflow**
3. Watch it run (takes ~30 seconds)
4. Check that `wod.json` was updated in your repo

After this, it will auto-run every day at 6 AM UTC — no action needed from you.

---

## How the daily WOD works

The scraper (`scraper.py`) runs on GitHub's free servers every morning:

1. **Tries crossfit.com/workout/YYYY/MM/DD** — the public daily WOD page
2. **Falls back to wodwell.com** — if crossfit.com is unavailable
3. **Uses rotating classic WODs** — if both sources fail (so the site always shows something)

The result is saved to `wod.json`, which your site reads on page load.

---

## Customizing

### Change the scrape time
Edit `.github/workflows/daily.yml`:
```yaml
- cron: '0 6 * * *'   # 6 AM UTC = 2 AM EST / 11 PM PST
```
Use [crontab.guru](https://crontab.guru) to find your preferred time.

### Add more workouts
Edit the `WODS` array in `index.html`. Each workout follows this format:
```js
{
  id: 999,           // unique number
  src: "girls",      // girls | hero | open | jb | noah
  name: "My WOD",
  type: "For Time",  // For Time | AMRAP | EMOM | For Load | etc.
  time: "~15 min",
  rx: "95/65 lb",
  score: "Time",
  yr: "",            // Open year e.g. "2023", or "" for non-Open
  desc: "3 rounds for time:\n• 5 Pull-Ups\n• 10 Push-Ups\n• 15 Squats"
}
```

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | The full website — all workouts, filters, UI |
| `scraper.py` | Python script that fetches the daily WOD |
| `wod.json` | Today's WOD — auto-updated by scraper |
| `.github/workflows/daily.yml` | GitHub Actions schedule — runs scraper daily |

---

## Local development

To test locally, just open `index.html` in a browser.
The daily WOD banner will show a placeholder message until deployed.

To test the scraper locally:
```bash
python3 scraper.py
```
This creates/updates `wod.json` with today's WOD.
