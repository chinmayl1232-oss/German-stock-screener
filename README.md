
# 🇩🇪 German Wave-2 Scanner — iOS Web App

Scans all DAX / MDAX / SDAX / TecDAX stocks for **second-wave setups** coiling near the 40-week EMA.  
Runs automatically every weekday at 6pm Frankfurt time via GitHub Actions.  
No computer, no server, no cost.

-----

## How it works

```
GitHub Actions (free)
  → runs scanner.py every weekday evening
  → fetches price data from Yahoo Finance (free, no API key)
  → calculates 40W EMA, RS, wave structure for ~160 stocks
  → saves data.json to this repo
  → GitHub Pages serves index.html + data.json
  → your iPhone reads it like a native app
```

-----

## One-time Setup (10 minutes)

### 1. Create the GitHub repository

1. Go to [github.com](https://github.com) and click **New repository**
1. Name it anything e.g. `wave2-scanner`
1. Set it to **Public** (required for free GitHub Pages)
1. Click **Create repository**

### 2. Upload the files

Upload these 3 files to the root of your repo:

- `index.html` — the iOS web app
- `scanner.py` — the data scanner
- `.github/workflows/scanner.yml` — the automation schedule

You can drag & drop them on the GitHub website, or use:

```bash
git clone https://github.com/YOUR_USERNAME/wave2-scanner
cd wave2-scanner
# copy the 3 files here, then:
git add .
git commit -m "Initial setup"
git push
```

### 3. Enable GitHub Pages

1. In your repo → **Settings** → **Pages**
1. Under **Source**, select `Deploy from a branch`
1. Branch: `main`, folder: `/ (root)`
1. Click **Save**
1. Wait ~1 minute, then your app is live at:
   `https://YOUR_USERNAME.github.io/wave2-scanner/`

### 4. Run the scanner for the first time

1. In your repo → **Actions** tab
1. Click **Run Wave-2 Scanner** → **Run workflow** → **Run workflow**
1. Wait ~3 minutes for it to complete
1. Refresh your GitHub Pages URL — you’ll see real data

### 5. Add to iPhone home screen

1. Open Safari on your iPhone
1. Go to `https://YOUR_USERNAME.github.io/wave2-scanner/`
1. Tap the **Share** button (box with arrow)
1. Scroll down → tap **Add to Home Screen**
1. Name it “W2 Scanner” → tap **Add**

It now lives on your home screen and works like a native app. ✅

-----

## Schedule

The scanner runs automatically **Monday to Friday at 6pm Frankfurt time**.

To run it manually at any time:

- Go to your repo → **Actions** → **Run Wave-2 Scanner** → **Run workflow**

-----

## Customisation

Open `scanner.py` and adjust these settings at the top:

|Setting           |Default|Description                                             |
|------------------|-------|--------------------------------------------------------|
|`MAX_DIST_PCT`    |`15.0` |Max % above 40W EMA (lower = tighter coils only)        |
|`MIN_DIST_PCT`    |`0.0`  |Min % above 40W EMA (set >0 to exclude stocks below EMA)|
|`MIN_WAVE1_GAIN`  |`30.0` |Minimum Wave 1 rally size in %                          |
|`MIN_PULLBACK_PCT`|`15.0` |Minimum pullback from Wave 1 high in %                  |
|`EMA_WEEKS`       |`40`   |Change to 30 or 50 if preferred                         |

-----

## Data source

- **Price data**: Yahoo Finance (free, no API key required)
- **Universe**: Auto-discovered from Wikipedia pages for DAX, MDAX, SDAX, TecDAX (~160 stocks)
- **Benchmark**: DAX (^GDAXI) for Relative Strength calculation

-----

## Troubleshooting

**App shows sample data, not real data**  
→ The scanner hasn’t run yet. Trigger it manually via Actions tab.

**Actions workflow fails**  
→ Check the Actions log for errors. Most common cause is Yahoo Finance being temporarily unavailable — just re-run.

**Stock is missing from results**  
→ It didn’t meet the filter criteria today. Lower `MAX_DIST_PCT` or `MIN_WAVE1_GAIN` in `scanner.py`.

**GitHub Pages not working**  
→ Make sure your repo is **Public** and Pages is enabled in Settings.
