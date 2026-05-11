# Promo Bot — Setup Guide

Step-by-step instructions to set up the script on your Mac.

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

### 1. Add vendors to account via Admin Panel

Place the CSV file into the `promo-bot` folder on Desktop, then:

```
python3 promo_bot.py add-vendors --csv venues.csv
```

The script will open Admin Panel → log in manually → the script will add vendors from CSV automatically.

### 2. Add providers to account via Admin Panel

```
python3 promo_bot.py add-venues --csv venues.csv
```

Same as above, but adds individual providers instead of vendors.

### 3. Check available Smart Promos

```
python3 promo_bot.py check-promo --login EMAIL --password PASS
```

Replace `EMAIL` and `PASS` with actual Food Partner Portal credentials.

### 3.1 Check available Sponsored Listings

```
python3 promo_bot.py check-listing --login EMAIL --password PASS
```

### 4. Activate Smart Promo (all venues)

```
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
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts "All" --venues "PASTA ITALIANO,Pani Mozzarella"
```

### 5. Deactivate Smart Promo (all venues)

```
python3 promo_bot.py end-promo --login EMAIL --password PASS
```

### 5.1 Deactivate Smart Promo for specific venues

```
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
