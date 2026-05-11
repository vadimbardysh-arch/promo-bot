# Promo Bot — Setup Guide

## What is this?

**Promo Bot** is a script that automates promo campaign setup for venues in the Bolt Food Partner Portal.

Instead of manually opening each venue, enabling cohorts, setting dates and clicking buttons — the script does it automatically across all venues at once.

### What it can do:

- **Add venues** to a manager's account via Admin Panel (from a CSV file)
- **Check** which Smart Promos and Sponsored Listings are available per venue
- **Activate Smart Promo** on all or specific venues (with cohort and date selection)
- **Deactivate Smart Promo** on all or specific venues
- **Generate reports** — what was activated, what was skipped and why

### How it works:

The script opens a browser (Chromium), logs into the Food Partner Portal and automatically clicks through all the necessary buttons — just like a manager would do manually, but in minutes instead of hours.

> ⚠️ **While the script is running — do not click anything in the browser!** It works automatically.

### Workflow (step by step):

```
1. Download CSV from Looker (list of venues)
         ↓
2. Add venues to portal via Admin Panel (add-vendors)
         ↓
3. Check which promos are available (check-promo / check-listing)
         ↓
4. Activate promos (smart-promo)
         ↓
5. When needed — deactivate promos (end-promo)
```

> First **preparation** (steps 1-2), then **verification** (step 3), and only then **launch promos** (step 4).

---

## Step 1: Install Python

Check if Python is already installed. Open **Terminal** (Finder → Applications → Utilities → Terminal) and type:

```
python3 --version
```

If you see something like `Python 3.12.0` — go to Step 2.

If you see an error — install Python:

1. Go to https://www.python.org/downloads/
2. Click the yellow **Download Python** button
3. Open the downloaded `.pkg` file
4. Click **Continue → Continue → Agree → Install**
5. After installation, close and reopen Terminal
6. Check again: `python3 --version`

---

## Step 2: Install Git

Check if Git is already installed:

```
git --version
```

If you see `git version 2.x.x` — go to Step 3.

If Mac asks "Would you like to install developer tools?" — click **Install** and wait for it to finish.

---

## Step 3: Download Promo Bot

In Terminal, run these commands (copy each one and press Enter):

```
cd ~/Desktop
```

```
git clone https://github.com/vadimbardysh-arch/promo-bot.git
```

```
cd promo-bot
```

A folder **promo-bot** will appear on your Desktop.

---

## Step 4: Run Installation

Still in Terminal, run:

```
./install.sh
```

If you see "permission denied":

```
chmod +x install.sh && ./install.sh
```

Wait for the message **"✓ Встановлення завершено!"** (Installation complete).

This only needs to be done once.

---

## Step 5: Done! How to Run

### Before each run

Open Terminal and navigate to the script folder:

```
cd ~/Desktop/promo-bot
```

> 💡 **How to find Terminal:** press `Cmd + Space`, type `Terminal`, press Enter.

---

### 0. Download CSV with venue data

Go to Looker and download the CSV with the venues you need:

👉 **https://bolt.cloud.looker.com/looks/51749**

Filter by your country/city → click **Download → CSV** → save the file and place it into the `promo-bot` folder on Desktop.

---

### 1. Add vendors to account via Admin Panel

Place the CSV file into the `promo-bot` folder on Desktop, then:

```
cd ~/Desktop/promo-bot
python3 promo_bot.py add-vendors --csv venues.csv
```

The script will open Admin Panel → log in manually → the script will add vendors from CSV automatically.

### 2. Add providers to account via Admin Panel

```
cd ~/Desktop/promo-bot
python3 promo_bot.py add-venues --csv venues.csv
```

Same as above, but adds individual providers instead of vendors.

### 3. Check available Smart Promos

```
cd ~/Desktop/promo-bot
python3 promo_bot.py check-promo --login EMAIL --password PASS
```

Replace `EMAIL` and `PASS` with actual Food Partner Portal credentials.

### 3.1 Check available Sponsored Listings

```
cd ~/Desktop/promo-bot
python3 promo_bot.py check-listing --login EMAIL --password PASS
```

### 4. Activate Smart Promo (all venues)

```
cd ~/Desktop/promo-bot
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts "All"
```

Parameters:
- `--start` — start date (format: DD/MM/YYYY, e.g. `22/04/2026`)
- `--end` — end date (format: DD/MM/YYYY, e.g. `28/04/2026`)
- `--cohorts` — which cohorts to enable:
  - `"All"` — all available cohorts
  - `"Top Customers"` — only the cohort matching this name (in quotes!)
  - `1,3` — 1st and 3rd cohort by position

### 4.1 Activate Smart Promo for specific venues

Add `--venues` with names separated by commas (in quotes):

```
cd ~/Desktop/promo-bot
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts "All" --venues "PASTA ITALIANO,Pani Mozzarella"
```

### 5. Deactivate Smart Promo (all venues)

```
cd ~/Desktop/promo-bot
python3 promo_bot.py end-promo --login EMAIL --password PASS
```

### 5.1 Deactivate Smart Promo for specific venues

```
cd ~/Desktop/promo-bot
python3 promo_bot.py end-promo --login EMAIL --password PASS --venues "PASTA ITALIANO,Pani Mozzarella"
```

---

### How to specify the CSV file path

**Option 1 (easiest):** put the CSV file into the `promo-bot` folder on your Desktop and use just the filename:

```
python3 promo_bot.py add-vendors --csv venues.csv
```

**Option 2:** the file is in Downloads:

```
python3 promo_bot.py add-vendors --csv ~/Downloads/venues.csv
```

**Option 3 (drag & drop):** type the command up to `--csv ` and then **drag the file from Finder directly into Terminal** — the path will be inserted automatically:

```
python3 promo_bot.py add-vendors --csv [drag your CSV file here]
```

> ⚠️ **Important:** `/path/to/file.csv` is just an example, not a real path! Always use the actual filename or path to your CSV file. If the path contains spaces, wrap it in quotes: `"my file.csv"`

---

## How to Update

When Vadym says there's an update:

```
cd ~/Desktop/promo-bot
```

```
git pull
```

---

## Troubleshooting

### "command not found: python3"
Python is not installed. Go back to Step 1.

### "permission denied"
Run `chmod +x install.sh` and try again.

### "xcrun: error: invalid active developer path"
You need to install Xcode Command Line Tools:
```
xcode-select --install
```

### The script opens a browser but nothing happens
Wait — the script works automatically. Do not click anything in the browser while the script is running.

### "Timeout exceeded"
Slow internet or the page is loading slowly. Run the command again.

### The browser closed with an error
Run the command again — the script will skip venues where promo is already active.

### How to find Terminal?
- Press `Cmd + Space` (Spotlight)
- Type `Terminal`
- Press Enter

---

## Full Command List

| Command | Description |
|---------|-------------|
| `check-promo` | Check which Smart Promos are available |
| `check-listing` | Check which Sponsored Listings are available |
| `smart-promo` | Activate Smart Promotions |
| `end-promo` | Deactivate active Smart Promotions |
| `listing` | Launch Sponsored Listing |
| `add-vendors` | Add vendors via Admin Panel |
| `add-venues` | Add providers via Admin Panel |

To see all parameters for any command:

```
python3 promo_bot.py smart-promo --help
```
