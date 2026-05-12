"""
Promo Bot — automation of promo campaigns via Bolt Food Partner Portal.

Phase 1: Adding venues to the test account via Admin Panel
Phase 2: Setting up promos (Smart Promotions, Sponsored Listing) via Food Partner Portal

Usage:
    # Phase 1: Add venues from CSV
    python3 promo_bot.py add-venues --csv /path/to/file.csv

    # Phase 2: Smart Promo for all venues
    python3 promo_bot.py smart-promo --login EMAIL --password PASS

    # Phase 2: Sponsored Listing for all venues
    python3 promo_bot.py listing --login EMAIL --password PASS --start 2026-04-01 --end 2026-04-14
"""

import asyncio
import csv
import argparse
import sys
import io
from collections import defaultdict
from playwright.async_api import async_playwright

ADMIN_PANEL_BASE_URL = "https://admin-panel.bolt.eu/delivery-provider/providerPortalAccounts"
FOOD_PARTNER_LOGIN_URL = "https://foodpartner.bolt.eu/login"


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

COLUMN_ALIASES = {
    "city": ["2. Merchant Information City Name", "City Name", "city", "City"],
    "provider_id": ["2. Merchant Information Provider ID", "Provider ID", "provider_id"],
    "provider_name": ["2. Merchant Information Provider Name", "Provider Name", "provider_name"],
    "vendor_id": ["2. Merchant Information Vendor ID", "Vendor ID", "vendor_id"],
    "vendor_name": ["2. Merchant Information Vendor Name", "Vendor Name", "vendor_name"],
}


def find_column(row: dict, aliases: list[str]) -> str:
    for alias in aliases:
        val = row.get(alias, "").strip()
        if val:
            return val
    for key in row:
        clean_key = key.lstrip("\ufeff").strip().strip(",").strip()
        for alias in aliases:
            if clean_key == alias:
                return row[key].strip()
    return ""


def read_providers_csv(csv_path: str) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for row in reader:
        city = find_column(row, COLUMN_ALIASES["city"])
        provider_id = find_column(row, COLUMN_ALIASES["provider_id"])
        provider_name = find_column(row, COLUMN_ALIASES["provider_name"])
        vendor_id = find_column(row, COLUMN_ALIASES["vendor_id"])
        vendor_name = find_column(row, COLUMN_ALIASES["vendor_name"])
        if city and provider_name:
            rows.append({
                "city": city,
                "provider_id": provider_id,
                "provider_name": provider_name,
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
            })
    return rows


def group_by_city_vendor(providers: list[dict]) -> dict:
    groups = defaultdict(list)
    for p in providers:
        key = (p["city"], p["vendor_name"])
        groups[key].append(p)
    return dict(groups)


def unique_vendors_by_city(providers: list[dict]) -> dict:
    """Групує унікальних вендорів по місту: {city: [{vendor_name, vendor_id}, ...]}"""
    seen = set()
    result = defaultdict(list)
    for p in providers:
        key = (p["city"], p["vendor_id"])
        if key not in seen:
            seen.add(key)
            result[p["city"]].append({
                "vendor_name": p["vendor_name"],
                "vendor_id": p["vendor_id"],
            })
    return dict(result)


# ---------------------------------------------------------------------------
# Phase 1a: Admin Panel — add vendors (швидкий варіант)
# ---------------------------------------------------------------------------

async def add_vendors(csv_path: str, account_id: str):
    providers = read_providers_csv(csv_path)
    if not providers:
        print("CSV is empty or failed to read data.")
        return

    by_city = unique_vendors_by_city(providers)
    total = sum(len(v) for v in by_city.values())

    print(f"\n{'='*60}")
    print(f"  Phase 1a: Adding {total} vendors to Vendor Permissions")
    print(f"{'='*60}")
    for city, vendors in by_city.items():
        print(f"  {city}:")
        for v in vendors:
            print(f"    - {v['vendor_name']} (id: {v['vendor_id']})")
    print(f"{'='*60}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        account_url = f"{ADMIN_PANEL_BASE_URL}/{account_id}"
        print(f">> Opening Admin Panel (account {account_id})...")
        print(">> Please log in to Admin Panel.")
        print(">> After logging in, press Enter in the terminal.\n")
        await page.goto(account_url)
        input("   [Press Enter when logged in and you see the account page] ")

        await page.goto(account_url)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Секція "Vendor Permissions" — два combobox: City та Vendor
        vendor_section = page.locator("text=Vendor Permissions").locator("xpath=../..")
        section_combos = vendor_section.locator("input[role='combobox']")

        for city, vendors in by_city.items():
            print(f"\n>> City: {city}")

            # City — перший combobox
            try:
                city_input = section_combos.nth(0)
                await city_input.click(timeout=5000)
                await asyncio.sleep(0.3)
                await city_input.fill("")
                await city_input.type(city, delay=50)
                await asyncio.sleep(1)
                option = page.get_by_role("option", name=city).first
                await option.click(timeout=5000)
                print(f"   ✓ City: {city}")
            except Exception as e:
                print(f"   ⚠ Failed to select city '{city}': {e}")
                input(f"   [Select city '{city}' manually and press Enter] ")
            await asyncio.sleep(1)

            # Vendor — другий combobox (мультиселект з тегами)
            for v in vendors:
                vname = v["vendor_name"]
                vid = v["vendor_id"]
                tag_text = f"(id: {vid})"

                existing = page.get_by_text(tag_text, exact=False)
                if await existing.count() > 0:
                    print(f"   ✓ {vname} (id: {vid}) — already added")
                    continue

                try:
                    vendor_input = section_combos.nth(1)
                    await vendor_input.click(timeout=5000)
                    await asyncio.sleep(0.3)
                    await vendor_input.fill("")
                    await vendor_input.type(vname, delay=50)
                    await asyncio.sleep(1)
                    exact_option = page.get_by_role("option").filter(has_text=f"(id: {vid})")
                    await exact_option.click(timeout=5000)
                    print(f"   ✓ {vname} (id: {vid}) — added")
                except Exception as e:
                    print(f"   ⚠ Not found '{vname}' (id: {vid}): {e}")
                    input(f"   [Add '{vname}' manually and press Enter] ")
                await asyncio.sleep(0.5)

        # Зберігаємо
        print("\n>> All vendors added. Saving...")
        save_btn = page.locator("button:has-text('Save'), input[value='Save']").first
        try:
            await save_btn.click(timeout=5000)
            await asyncio.sleep(2)
            print("   ✓ Saved!")
        except Exception:
            print("   ⚠ Save button not found. Press it manually.")
            input("   [Press Save manually then press Enter] ")

        print(f"\n{'='*60}")
        print(f"  Phase 1a complete! Added {total} vendors.")
        print(f"{'='*60}\n")

        await browser.close()


# ---------------------------------------------------------------------------
# Phase 1b: Admin Panel — add venues (детальний варіант)
# ---------------------------------------------------------------------------

async def add_venues(csv_path: str, account_id: str):
    providers = read_providers_csv(csv_path)
    if not providers:
        print("CSV is empty or failed to read data.")
        return

    groups = group_by_city_vendor(providers)
    total = len(providers)

    print(f"\n{'='*60}")
    print(f"  Phase 1: Adding {total} providers to Admin Panel")
    print(f"{'='*60}")
    for (city, vendor), items in groups.items():
        print(f"  {city} → {vendor}: {len(items)} providers")
        for p in items:
            print(f"    - {p['provider_name']} (id: {p['provider_id']})")
    print(f"{'='*60}\n")

    async with async_playwright() as pw:
        # Запускаємо Chromium з видимим вікном
        # persistent_context використовує профіль браузера з SSL сертифікатами
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Крок 1: Користувач логіниться вручну
        account_url = f"{ADMIN_PANEL_BASE_URL}/{account_id}"
        print(f">> Opening Admin Panel (account {account_id})...")
        print(">> Please log in to Admin Panel.")
        print(">> After logging in, press Enter in the terminal.\n")
        await page.goto(account_url)
        input("   [Press Enter when logged in and you see the account page] ")

        # Крок 2: Переходимо на сторінку акаунту (на випадок якщо редірект)
        await page.goto(account_url)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Крок 3: Для кожної групи City+Vendor додаємо провайдерів
        # Шукаємо секцію "Provider Permissions" і комбобокси саме в ній
        # (на сторінці є ще Vendor Permissions з такими ж комбобоксами — не чіпаємо)
        provider_section = page.locator("text=Provider Permissions").locator("xpath=../..")
        section_combos = provider_section.locator("input[role='combobox']")

        for (city, vendor), items in groups.items():
            vendor_id = items[0]["vendor_id"]
            print(f"\n>> Adding providers: {city} → {vendor} (id: {vendor_id})")

            # City — перший combobox в секції Provider Permissions
            try:
                city_input = section_combos.nth(0)
                await city_input.click(timeout=5000)
                await asyncio.sleep(0.3)
                await city_input.fill("")
                await city_input.type(city, delay=50)
                await asyncio.sleep(1)
                option = page.get_by_role("option", name=city).first
                await option.click(timeout=5000)
                print(f"   ✓ City: {city}")
            except Exception as e:
                print(f"   ⚠ Failed to select city '{city}' automatically: {e}")
                input(f"   [Select city '{city}' manually and press Enter] ")
            await asyncio.sleep(1)

            # Vendor — другий combobox; матчимо по vendor_id з CSV
            # Формат опцій в дропдауні: "НАЗВА (id: XXXXX)"
            try:
                vendor_input = section_combos.nth(1)
                await vendor_input.click(timeout=5000)
                await asyncio.sleep(0.3)
                await vendor_input.fill("")
                await vendor_input.type(vendor, delay=50)
                await asyncio.sleep(1)
                exact_option = page.get_by_role("option").filter(has_text=f"(id: {vendor_id})")
                await exact_option.click(timeout=5000)
                print(f"   ✓ Vendor: {vendor} (id: {vendor_id})")
            except Exception as e:
                print(f"   ⚠ Failed to select vendor '{vendor}' (id: {vendor_id}): {e}")
                input(f"   [Select vendor '{vendor}' manually and press Enter] ")
            await asyncio.sleep(1)

            # Provider Permissions — третій combobox (мультиселект з тегами)
            for p in items:
                provider_name = p["provider_name"]
                provider_id = p["provider_id"]
                tag_text = f"{provider_name} (id: {provider_id})"

                existing = page.get_by_text(tag_text, exact=False)
                if await existing.count() > 0:
                    print(f"   ✓ {provider_name} — already added")
                    continue

                try:
                    provider_input = section_combos.nth(2)
                    await provider_input.click(timeout=5000)
                    await asyncio.sleep(0.3)
                    await provider_input.fill("")
                    await provider_input.type(provider_name, delay=30)
                    await asyncio.sleep(1)
                    option = page.get_by_role("option", name=provider_name).first
                    await option.click(timeout=5000)
                    print(f"   ✓ {provider_name} — added")
                except Exception as e:
                    print(f"   ⚠ Not found '{provider_name}': {e}")
                    input(f"   [Add '{provider_name}' manually and press Enter] ")
                await asyncio.sleep(0.5)

        # Крок 4: Зберігаємо
        print("\n>> All providers added. Saving...")
        save_btn = page.locator("button:has-text('Save'), input[value='Save']").first
        try:
            await save_btn.click(timeout=5000)
            await asyncio.sleep(2)
            print("   ✓ Saved!")
        except Exception:
            print("   ⚠ Save button not found. Press it manually.")
            input("   [Press Save manually then press Enter] ")

        print(f"\n{'='*60}")
        print(f"  Phase 1 complete! Added {total} providers.")
        print(f"{'='*60}\n")

        await browser.close()


# ---------------------------------------------------------------------------
# Phase 2: Food Partner Portal — Smart Promotions
# ---------------------------------------------------------------------------

async def dismiss_overlays(page):
    """Прибирає cookie banner та будь-які MUI діалоги що блокують кліки."""
    try:
        await page.locator("button:has-text('Allow all')").click(timeout=1000)
        await asyncio.sleep(0.3)
    except Exception:
        pass

    # Закриваємо MUI діалоги (кнопки OK, Close, Got it, Зрозуміло тощо)
    for btn_text in ["OK", "Close", "Got it", "Зрозуміло", "Закрити", "Done"]:
        try:
            btn = page.locator(f"div[role='presentation'] button:has-text('{btn_text}')")
            if await btn.count() > 0:
                await btn.first.click(timeout=2000)
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass

    # Видаляємо cookie banner та MUI overlay через JS
    await page.evaluate("""
        document.getElementById('cookiebanner')?.remove();
        document.querySelectorAll('.cb-container, [name="cookiebanner"]')
            .forEach(el => el.remove());
        // Закриваємо MUI Modal backdrop кліком
        const backdrop = document.querySelector('.MuiModal-root .MuiBackdrop-root');
        if (backdrop) backdrop.click();
    """)


async def handle_error_page(page):
    """Натискає 'Try again' якщо сторінка показує помилку, і перевіряє логін."""
    # "Oops, something went wrong" → натиснути "Try again"
    try_again = page.locator("button:has-text('Try again'), button:has-text('Спробувати')")
    if await try_again.count() > 0:
        print("   ↻ Page error — clicking Try again...")
        await try_again.first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        await dismiss_overlays(page)
        return True
    return False


async def ensure_logged_in(page, login: str, password: str):
    """Перевіряє чи ми залогінені. Якщо ні — логіниться заново."""
    if "/login" in page.url:
        print("   ↻ Session expired — re-logging in...")
        await login_food_partner(page, login, password)
        return True
    return False


async def login_food_partner(page, login: str, password: str):
    """Логін в Food Partner Portal з обробкою cookies та welcome dialog."""
    print("\n>> Logging in to Food Partner Portal...")
    await page.goto(FOOD_PARTNER_LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    await dismiss_overlays(page)

    await page.fill("input[name='username'], input[type='text']", login)
    await page.fill("input[type='password']", password)
    await page.locator("button:has-text('Login'), button:has-text('Log in')").first.click()
    await asyncio.sleep(4)

    await dismiss_overlays(page)

    try:
        await page.locator("button:has-text('OK')").click(timeout=5000)
        await asyncio.sleep(1)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Phase 2: Food Partner Portal — Check available Smart Promo
# ---------------------------------------------------------------------------

async def check_promo(login: str, password: str, venue_filter: str = None):
    filters = [f.strip() for f in venue_filter.split(",")] if venue_filter else None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await login_food_partner(page, login, password)

        all_venues = await get_all_venues(page)
        if filters:
            venues = [v for v in all_venues if any(f in v for f in filters)]
            print(f"\n>> Found {len(all_venues)} venues, selected {len(venues)} by filter")
        else:
            venues = all_venues
            print(f"\n>> Found {len(venues)} venues")

        report = []

        for i, venue_name in enumerate(venues):
            print(f"\n>> [{i+1}/{len(venues)}] Checking: {venue_name}")

            await ensure_logged_in(page, login, password)
            await handle_error_page(page)

            try:
                await switch_venue(page, venue_name)
            except Exception:
                await dismiss_overlays(page)
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
                try:
                    await ensure_logged_in(page, login, password)
                    await page.goto("https://foodpartner.bolt.eu/dashboard/promotions")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    await dismiss_overlays(page)
                    await handle_error_page(page)
                    await switch_venue(page, venue_name)
                except Exception:
                    print(f"   ⚠ Failed to switch venue — skipping")
                    report.append({"venue": venue_name, "status": "ERROR", "cohorts": [], "reason": "Failed to switch venue"})
                    continue

            await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            await dismiss_overlays(page)
            await handle_error_page(page)

            # Перевіряємо чи вже є активне Smart Promo
            active_promo = page.get_by_text("Custom smart promotion", exact=False)
            active_badge = page.locator("text=Active")
            if await active_promo.count() > 0 and await active_badge.count() > 0:
                print(f"   ● Smart Promo already ACTIVE")
                report.append({"venue": venue_name, "status": "ACTIVE", "cohorts": [], "reason": "Smart Promo already connected"})
                continue

            # Пробуємо зайти в налаштування Smart Promo
            entered = False
            for attempt in range(3):
                create_plan = page.locator("button:has-text('Create plan'), button:has-text('Створити план')")
                if await create_plan.count() > 0:
                    await create_plan.first.click()
                    await asyncio.sleep(3)
                    entered = True
                    break

                get_started = page.locator("button:has-text('Get started'), button:has-text('Розпочати')")
                if await get_started.count() > 0:
                    await get_started.first.click()
                    await asyncio.sleep(3)
                    try:
                        customize = page.locator("button:has-text('Customize weekly plan'), button:has-text('Налаштувати')")
                        await customize.first.click(timeout=3000)
                        await asyncio.sleep(2)
                    except Exception:
                        pass
                    entered = True
                    break

                if attempt < 2:
                    await asyncio.sleep(3)

            if not entered:
                print(f"   ✕ Smart Promo UNAVAILABLE")
                report.append({"venue": venue_name, "status": "UNAVAILABLE", "cohorts": [], "reason": "No Create plan / Get started button"})
                continue

            # Зчитуємо когорти
            toggles = page.get_by_role("switch")
            for _ in range(5):
                if await toggles.count() > 0:
                    break
                await asyncio.sleep(3)
            if await toggles.count() == 0:
                toggles = page.locator("[role='switch'], [type='checkbox'][class*='witch'], [aria-checked]")
                await asyncio.sleep(2)
            toggle_count = await toggles.count()

            if toggle_count == 0:
                print(f"   ✕ Cohorts not found")
                report.append({"venue": venue_name, "status": "UNAVAILABLE", "cohorts": [], "reason": "Cohorts not found"})
                continue

            cohort_names = []
            for t in range(toggle_count):
                toggle = toggles.nth(t)
                name = f"#{t+1}"
                for level in range(1, 6):
                    xpath_up = "/".join([".."] * level)
                    container = toggle.locator(f"xpath={xpath_up}")
                    texts = await container.inner_text()
                    first_line = texts.strip().split("\n")[0].strip()
                    if first_line and len(first_line) > 3 and first_line not in ("Discounts",):
                        name = first_line
                        break
                cohort_names.append(name)

            print(f"   ✓ Available {toggle_count} cohorts: {', '.join(cohort_names)}")
            report.append({"venue": venue_name, "status": "AVAILABLE", "cohorts": cohort_names, "reason": ""})

            # Повертаємось назад (не зберігаємо нічого)
            await page.go_back()
            await asyncio.sleep(2)

        # Звіт
        available = [r for r in report if r["status"] == "AVAILABLE"]
        active = [r for r in report if r["status"] == "ACTIVE"]
        unavailable = [r for r in report if r["status"] == "UNAVAILABLE"]
        errors = [r for r in report if r["status"] == "ERROR"]

        print(f"\n{'='*60}")
        print(f"  REPORT — Smart Promo Check")
        print(f"{'='*60}")
        print(f"  Total venues:    {len(venues)}")
        print(f"  ✓ Available:     {len(available)}")
        print(f"  ● Already active:{len(active)}")
        print(f"  ✕ Unavailable:   {len(unavailable)}")
        print(f"  ⚠ Errors:        {len(errors)}")
        print(f"{'='*60}")

        if available:
            print(f"\n  ✓ AVAILABLE ({len(available)}):")
            for r in available:
                print(f"    • {r['venue']}")
                print(f"      Cohorts: {', '.join(r['cohorts'])}")

        if active:
            print(f"\n  ● ALREADY ACTIVE ({len(active)}):")
            for r in active:
                print(f"    • {r['venue']}")

        if unavailable:
            print(f"\n  ✕ UNAVAILABLE ({len(unavailable)}):")
            for r in unavailable:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        if errors:
            print(f"\n  ⚠ ERRORS ({len(errors)}):")
            for r in errors:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        print(f"\n{'='*60}\n")
        await browser.close()


# ---------------------------------------------------------------------------
# Phase 2b: Food Partner Portal — Check available Sponsored Listing
# ---------------------------------------------------------------------------

async def check_listing(login: str, password: str, venue_filter: str = None):
    filters = [f.strip() for f in venue_filter.split(",")] if venue_filter else None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await login_food_partner(page, login, password)

        all_venues = await get_all_venues(page)
        if filters:
            venues = [v for v in all_venues if any(f in v for f in filters)]
            print(f"\n>> Found {len(all_venues)} venues, selected {len(venues)} by filter")
        else:
            venues = all_venues
            print(f"\n>> Found {len(venues)} venues")

        report = []

        for i, venue_name in enumerate(venues):
            print(f"\n>> [{i+1}/{len(venues)}] Checking Listing: {venue_name}")

            await ensure_logged_in(page, login, password)
            await handle_error_page(page)

            try:
                await switch_venue(page, venue_name)
            except Exception:
                await dismiss_overlays(page)
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
                try:
                    await ensure_logged_in(page, login, password)
                    await page.goto("https://foodpartner.bolt.eu/dashboard/promotions")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    await dismiss_overlays(page)
                    await handle_error_page(page)
                    await switch_venue(page, venue_name)
                except Exception:
                    print(f"   ⚠ Failed to switch venue — skipping")
                    report.append({"venue": venue_name, "status": "ERROR", "listings": [], "reason": "Failed to switch venue"})
                    continue

            await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            await dismiss_overlays(page)
            await handle_error_page(page)

            # Скролимо до секції "Set up other promotions"
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            listings = []

            async def check_listing_card(page, title_text: str, label: str):
                """Знаходить картку Listing по заголовку, клікає Create, перевіряє результат."""
                # Структура: div.css-1q8rlr9 > div > span(title) + div > span(Create)
                title_el = page.locator(f"span.MuiTypography-body-m-accent:has-text('{title_text}')")
                if await title_el.count() == 0:
                    return f"{label}: not found"

                # Картка = найближчий батьківський div.css-1q8rlr9
                card = title_el.first.locator("xpath=ancestor::div[contains(@class, 'css-1q8rlr9')]")
                if await card.count() == 0:
                    # Fallback: піднімаємось на 3 рівні
                    card = title_el.first.locator("xpath=../../..")

                # Знаходимо Create span всередині картки
                create_span = card.locator("span:has-text('Create')")
                if await create_span.count() == 0:
                    return f"{label}: no button"

                url_before = page.url
                try:
                    await create_span.first.click(timeout=5000)
                    await asyncio.sleep(3)
                    await page.wait_for_load_state("networkidle")

                    url_after = page.url
                    has_form = (
                        url_after != url_before
                        or await page.locator("button:has-text('Launch'), button:has-text('Запустити')").count() > 0
                        or await page.locator("input[type='checkbox']").count() > 0
                    )

                    if has_form:
                        await page.go_back()
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(1)
                        return f"{label}: AVAILABLE"
                    else:
                        return f"{label}: UNAVAILABLE"
                except Exception:
                    return f"{label}: UNAVAILABLE"

            listings.append(await check_listing_card(page, "Sponsored Listing on Homepage", "Homepage"))
            listings.append(await check_listing_card(page, "Sponsored Listing in Search", "Search"))

            # Перевіряємо чи вже є активний Sponsored Listing
            active_listing = page.get_by_text("Sponsored Listing", exact=False)
            active_badge = page.locator("text=Active")
            has_active = False
            if await active_listing.count() > 0 and await active_badge.count() > 0:
                # Переконуємось що Active відноситься до Listing, а не Smart Promo
                all_text = await page.locator("main").inner_text()
                if "Sponsored Listing" in all_text:
                    has_active = True

            def colorize_listing(text):
                """Додає ANSI-кольори: AVAILABLE=зелений, UNAVAILABLE=червоний."""
                g = "\033[32m"  # green
                r = "\033[31m"  # red
                reset = "\033[0m"
                text = text.replace(": AVAILABLE", f": {g}AVAILABLE{reset}")
                text = text.replace(": UNAVAILABLE", f": {r}UNAVAILABLE{reset}")
                text = text.replace(": not found", f": {r}not found{reset}")
                return text

            has_any_available = any(": AVAILABLE" in l for l in listings)

            if has_active:
                print(f"   ● Sponsored Listing already ACTIVE")
                if listings:
                    print(f"     {colorize_listing(' | '.join(listings))}")
                report.append({"venue": venue_name, "status": "ACTIVE", "listings": listings, "reason": "Sponsored Listing already connected"})
            elif has_any_available:
                print(f"   ✓ {colorize_listing(' | '.join(listings))}")
                report.append({"venue": venue_name, "status": "AVAILABLE", "listings": listings, "reason": ""})
            elif listings:
                print(f"   ✕ {colorize_listing(' | '.join(listings))}")
                report.append({"venue": venue_name, "status": "UNAVAILABLE", "listings": listings, "reason": "All Listing types unavailable"})
            else:
                print(f"   \033[31m✕ Sponsored Listing section not found\033[0m")
                report.append({"venue": venue_name, "status": "UNAVAILABLE", "listings": [], "reason": "Sponsored Listing section not found"})

        # Звіт
        g = "\033[32m"
        r = "\033[31m"
        y = "\033[33m"
        b = "\033[1m"
        reset = "\033[0m"

        available = [rec for rec in report if rec["status"] == "AVAILABLE"]
        active = [rec for rec in report if rec["status"] == "ACTIVE"]
        unavailable = [rec for rec in report if rec["status"] == "UNAVAILABLE"]
        errors = [rec for rec in report if rec["status"] == "ERROR"]

        def color_listings(items):
            colored = []
            for item in items:
                if ": AVAILABLE" in item:
                    colored.append(item.replace(": AVAILABLE", f": {g}AVAILABLE{reset}"))
                elif ": UNAVAILABLE" in item:
                    colored.append(item.replace(": UNAVAILABLE", f": {r}UNAVAILABLE{reset}"))
                elif ": not found" in item:
                    colored.append(item.replace(": not found", f": {r}not found{reset}"))
                else:
                    colored.append(item)
            return " | ".join(colored)

        print(f"\n{'='*60}")
        print(f"  {b}REPORT — Sponsored Listing Check{reset}")
        print(f"{'='*60}")
        print(f"  Total venues:    {b}{len(venues)}{reset}")
        print(f"  {g}✓ Available:     {len(available)}{reset}")
        print(f"  {y}● Already active: {len(active)}{reset}")
        print(f"  {r}✕ Unavailable:   {len(unavailable)}{reset}")
        print(f"  {r}⚠ Errors:        {len(errors)}{reset}")
        print(f"{'='*60}")

        # Детальний звіт по кожній venue
        print(f"\n  {b}DETAILS PER VENUE:{reset}\n")
        for rec in report:
            if rec["status"] == "ERROR":
                print(f"    {r}⚠{reset} {rec['venue']}")
                print(f"      {r}Error: {rec['reason']}{reset}")
            elif rec["status"] == "ACTIVE":
                print(f"    {y}●{reset} {rec['venue']}")
                if rec['listings']:
                    print(f"      {color_listings(rec['listings'])}")
                print(f"      {y}Already active{reset}")
            elif rec["status"] == "AVAILABLE":
                print(f"    {g}✓{reset} {rec['venue']}")
                print(f"      {color_listings(rec['listings'])}")
            else:
                print(f"    {r}✕{reset} {rec['venue']}")
                if rec['listings']:
                    print(f"      {color_listings(rec['listings'])}")
                else:
                    print(f"      {r}{rec['reason']}{reset}")

        print(f"\n{'='*60}\n")
        await browser.close()


# ---------------------------------------------------------------------------
# Phase 3: Food Partner Portal — Smart Promotions
# ---------------------------------------------------------------------------

async def setup_smart_promo(
    login: str,
    password: str,
    start_date: str = None,
    end_date: str = None,
    cohorts: str = "all",
    venue_filter: str = None,
):
    # cohorts: "all", "1,3" (за позицією), або "Найкращі,Активні" (за назвою)
    cohort_mode = "all"
    cohort_indices = None
    cohort_keywords = None
    if cohorts.strip().lower() != "all":
        parts = [x.strip() for x in cohorts.split(",")]
        if all(p.isdigit() for p in parts):
            cohort_mode = "index"
            cohort_indices = [int(p) - 1 for p in parts]
        else:
            cohort_mode = "name"
            cohort_keywords = parts

    filters = [f.strip() for f in venue_filter.split(",")] if venue_filter else None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await login_food_partner(page, login, password)

        all_venues = await get_all_venues(page)
        if filters:
            venues = [v for v in all_venues if any(f in v for f in filters)]
            print(f"\n>> Found {len(all_venues)} venues, selected {len(venues)} by filter")
        else:
            venues = all_venues
            print(f"\n>> Found {len(venues)} venues")
        for v in venues:
            print(f"   - {v}")

        report = []
        retry_venues = []

        for i, venue_name in enumerate(venues):
            print(f"\n>> [{i+1}/{len(venues)}] Smart Promo for: {venue_name}")

            # Перевіряємо логін та помилки сторінки
            await ensure_logged_in(page, login, password)
            await handle_error_page(page)

            try:
                await switch_venue(page, venue_name)
            except Exception as e:
                print(f"   ⚠ Failed to switch venue — resetting page state")
                await dismiss_overlays(page)
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
                try:
                    await ensure_logged_in(page, login, password)
                    await page.goto("https://foodpartner.bolt.eu/dashboard/promotions")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    await dismiss_overlays(page)
                    await handle_error_page(page)
                    await switch_venue(page, venue_name)
                except Exception:
                    print(f"   ⚠ Retry also failed — skipping")
                    report.append({"venue": venue_name, "status": "ERROR", "reason": "Failed to switch venue"})
                    continue

            await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            await dismiss_overlays(page)

            # Якщо сторінка показує помилку — Try again і retry
            if await handle_error_page(page):
                await asyncio.sleep(2)

            # Скролимо вниз щоб побачити секцію Smart Promo
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # Два можливих шляхи:
            entered = False

            # Спочатку пробуємо знайти кнопки з retry (сторінка може довантажуватись)
            for attempt in range(3):
                create_plan = page.locator("button:has-text('Create plan'), button:has-text('Створити план')")
                if await create_plan.count() > 0:
                    await create_plan.first.click()
                    await asyncio.sleep(3)
                    entered = True
                    break

                get_started = page.locator("button:has-text('Get started'), button:has-text('Розпочати')")
                if await get_started.count() > 0:
                    await get_started.first.click()
                    await asyncio.sleep(3)
                    try:
                        customize = page.locator("button:has-text('Customize weekly plan'), button:has-text('Налаштувати')")
                        await customize.first.click(timeout=3000)
                        await asyncio.sleep(2)
                    except Exception:
                        pass
                    entered = True
                    break

                if attempt < 2:
                    await asyncio.sleep(3)

            if not entered:
                # Перевіряємо чи промо вже активне
                active_text = page.locator("text=Active")
                custom_promo = page.get_by_text("Custom smart promotion", exact=False)
                if await active_text.count() > 0 and await custom_promo.count() > 0:
                    print(f"   ○ Smart Promo already active — skipping")
                    report.append({"venue": venue_name, "status": "SKIPPED", "reason": "Smart Promo already active"})
                else:
                    import os
                    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
                    os.makedirs(screenshots_dir, exist_ok=True)
                    try:
                        await page.screenshot(path=os.path.join(screenshots_dir, f"no_button_{venue_name[:30].replace('/', '_')}.png"), timeout=10000)
                    except Exception:
                        pass
                    print(f"   ⚠ Smart Promo unavailable — skipping (screenshot saved)")
                    report.append({"venue": venue_name, "status": "SKIPPED", "reason": "Smart Promo unavailable (no button, screenshot saved)"})
                continue

            # Чекаємо поки toggles з'являться (retry до 15 сек)
            toggles = page.get_by_role("switch")
            for _ in range(5):
                if await toggles.count() > 0:
                    break
                await asyncio.sleep(3)
            # Fallback: якщо get_by_role не знайшов, шукаємо ширше
            if await toggles.count() == 0:
                toggles = page.locator("[role='switch'], [type='checkbox'][class*='witch'], [aria-checked]")
                await asyncio.sleep(2)
            toggle_count = await toggles.count()

            if toggle_count == 0:
                import os
                screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                try:
                    await page.screenshot(path=os.path.join(screenshots_dir, f"no_cohorts_{venue_name[:30].replace('/', '_')}.png"), timeout=10000)
                except Exception:
                    pass
                print(f"   ⚠ Cohorts not found — skipping (screenshot saved)")
                report.append({"venue": venue_name, "status": "SKIPPED", "reason": "Cohorts not found (screenshot saved)"})
                continue

            print(f"   Found {toggle_count} cohort(s)")

            enabled_cohorts = []

            # Зчитуємо назви когорт з UI (текст біля кожного toggle)
            cohort_names = {}
            for t in range(toggle_count):
                toggle = toggles.nth(t)
                name = f"#{t+1}"
                for level in range(1, 6):
                    xpath_up = "/".join([".."] * level)
                    container = toggle.locator(f"xpath={xpath_up}")
                    texts = await container.inner_text()
                    first_line = texts.strip().split("\n")[0].strip()
                    if first_line and len(first_line) > 3 and first_line not in ("Discounts",):
                        name = first_line
                        break
                cohort_names[t] = name

            if cohort_mode == "name":
                found_any = False
                for keyword in cohort_keywords:
                    matched = False
                    for level in range(1, 8):
                        xpath_up = "/".join([".."] * level)
                        container = page.get_by_text(keyword, exact=False).first.locator(f"xpath={xpath_up}")
                        toggle_in = container.locator("[role='switch']")
                        if await toggle_in.count() == 1:
                            is_on = await toggle_in.get_attribute("aria-checked")
                            if is_on != "true":
                                await toggle_in.click()
                                await asyncio.sleep(0.5)
                                print(f"   ✓ '{keyword}' enabled")
                                enabled_cohorts.append(keyword)
                            else:
                                print(f"   ✓ '{keyword}' already enabled")
                                enabled_cohorts.append(f"{keyword} (was already on)")
                            matched = True
                            found_any = True
                            break
                    if not matched:
                        print(f"   ⚠ Cohort '{keyword}' not found")

                if not found_any:
                    print(f"   ⚠ None of the cohorts found — skipping venue")
                    report.append({"venue": venue_name, "status": "SKIPPED", "reason": f"Cohort '{', '.join(cohort_keywords)}' not found"})
                    continue
            else:
                # Режим "all" або по індексу
                for t in range(toggle_count):
                    toggle = toggles.nth(t)
                    cname = cohort_names.get(t, f"#{t+1}")
                    is_on = await toggle.get_attribute("aria-checked")
                    should_enable = cohort_indices is None or t in cohort_indices

                    if should_enable and is_on != "true":
                        await toggle.click()
                        await asyncio.sleep(0.5)
                        print(f"   ✓ '{cname}' enabled")
                        enabled_cohorts.append(cname)
                    elif should_enable and is_on == "true":
                        print(f"   ✓ '{cname}' already enabled")
                        enabled_cohorts.append(f"{cname} (was already on)")
                    else:
                        if is_on == "true":
                            await toggle.click()
                            await asyncio.sleep(0.5)
                            print(f"   ○ '{cname}' disabled")

            # Редагуємо розклад (дати)
            # "Edit" може бути <button> або clickable <div>/<span>
            if start_date or end_date:
                try:
                    edit_clicked = False
                    # Спершу шукаємо enabled button
                    edit_btn = page.locator("button:has-text('Edit')").first
                    if await edit_btn.count() > 0:
                        is_disabled = await edit_btn.get_attribute("disabled")
                        if is_disabled is None:
                            await edit_btn.click(timeout=5000)
                            edit_clicked = True
                    # Якщо кнопки нема — шукаємо clickable text "Edit"
                    if not edit_clicked:
                        edit_text = page.get_by_text("Edit", exact=True).first
                        await edit_text.click(timeout=5000)
                    await asyncio.sleep(2)

                    if start_date:
                        start_input = page.get_by_role("textbox", name="Start date")
                        await start_input.click(click_count=3)
                        await asyncio.sleep(0.3)
                        await start_input.fill(start_date)

                    if end_date:
                        end_input = page.get_by_role("textbox", name="End date")
                        await end_input.click(click_count=3)
                        await asyncio.sleep(0.3)
                        await end_input.fill(end_date)

                    await asyncio.sleep(0.5)
                    await dismiss_overlays(page)
                    save_btn = page.locator("button:has-text('Save')").first
                    if await save_btn.count() > 0:
                        await save_btn.click(timeout=5000)
                        await asyncio.sleep(1)
                    print(f"   ✓ Dates: {start_date} — {end_date}")
                except Exception as e:
                    print(f"   ⚠ Failed to change dates: {e}")
                    input("   [Set dates manually and press Enter] ")

            # Приймаємо T&C
            await dismiss_overlays(page)
            tc = page.locator("input[type='checkbox']")
            if await tc.count() > 0:
                checkbox = tc.last
                try:
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.click()
                        await asyncio.sleep(0.5)
                except Exception:
                    await checkbox.click(force=True)
                    await asyncio.sleep(0.5)

            # Натискаємо "Schedule promotion" / "Запланувати промоакцію"
            await dismiss_overlays(page)
            schedule_btn = page.locator(
                "button:has-text('Schedule promotion'), button:has-text('Запланувати')"
            )
            try:
                await schedule_btn.first.click(timeout=5000)
                await asyncio.sleep(3)

                # Якщо з'явився діалог "End and replace your ongoing promotion?"
                end_ongoing = page.locator("button:has-text('End ongoing promotion'), button:has-text('Закінчити поточне')")
                if await end_ongoing.count() > 0:
                    print(f"   ↻ Replacing current promo — needs re-setup...")
                    await end_ongoing.first.click()
                    await asyncio.sleep(3)
                    await dismiss_overlays(page)
                    retry_venues.append(venue_name)
                    report.append({"venue": venue_name, "status": "RETRY", "reason": "Replaced current promo — will retry setup"})
                    continue

                # Закриваємо будь-які діалоги після Schedule
                await dismiss_overlays(page)
                await asyncio.sleep(2)

                # Верифікація: переходимо на Promotions і перевіряємо чи промо активне
                await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)

                is_active = (
                    await page.get_by_text("Custom smart promotion", exact=False).count() > 0
                    and await page.locator("text=Active").count() > 0
                )

                cohort_str = ", ".join(enabled_cohorts) if enabled_cohorts else "all"
                dates_str = f"{start_date} — {end_date}" if start_date and end_date else "default"

                if is_active:
                    print(f"   ✓ Smart Promo activated!")
                    report.append({"venue": venue_name, "status": "ACTIVATED", "reason": f"Cohorts: {cohort_str} | Dates: {dates_str}"})
                else:
                    print(f"   ⚠ Promo not confirmed — adding to retry pass")
                    retry_venues.append(venue_name)
                    report.append({"venue": venue_name, "status": "RETRY", "reason": "Schedule clicked but promo not active — will retry"})
            except Exception:
                print(f"   ⚠ 'Schedule promotion' unavailable — check manually")
                input("   [Check and press Enter] ")
                report.append({"venue": venue_name, "status": "MANUAL", "reason": "Schedule promotion unavailable — needs manual check"})

            # Закриваємо діалог підтвердження якщо з'явився
            await dismiss_overlays(page)
            await asyncio.sleep(1)

        # Повторний прохід для venues де було замінено поточне промо
        if retry_venues:
            print(f"\n{'='*60}")
            print(f"  Retry pass: {len(retry_venues)} venues (after promo replacement)")
            print(f"{'='*60}")

            for i, venue_name in enumerate(retry_venues):
                print(f"\n>> [RETRY {i+1}/{len(retry_venues)}] Smart Promo for: {venue_name}")

                await ensure_logged_in(page, login, password)
                await handle_error_page(page)

                try:
                    await switch_venue(page, venue_name)
                except Exception:
                    await dismiss_overlays(page)
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    try:
                        await ensure_logged_in(page, login, password)
                        await page.goto("https://foodpartner.bolt.eu/dashboard/promotions")
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)
                        await dismiss_overlays(page)
                        await handle_error_page(page)
                        await switch_venue(page, venue_name)
                    except Exception:
                        print(f"   ⚠ Failed to switch venue — skipping")
                        report.append({"venue": venue_name, "status": "ERROR", "reason": "Retry pass: failed to switch venue"})
                        continue

                await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                await dismiss_overlays(page)
                await handle_error_page(page)

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)

                entered = False
                for attempt in range(3):
                    create_plan = page.locator("button:has-text('Create plan'), button:has-text('Створити план')")
                    if await create_plan.count() > 0:
                        await create_plan.first.click()
                        await asyncio.sleep(3)
                        entered = True
                        break
                    get_started = page.locator("button:has-text('Get started'), button:has-text('Розпочати')")
                    if await get_started.count() > 0:
                        await get_started.first.click()
                        await asyncio.sleep(3)
                        try:
                            customize = page.locator("button:has-text('Customize weekly plan'), button:has-text('Налаштувати')")
                            await customize.first.click(timeout=3000)
                            await asyncio.sleep(2)
                        except Exception:
                            pass
                        entered = True
                        break
                    if attempt < 2:
                        await asyncio.sleep(3)

                if not entered:
                    print(f"   ⚠ Button not found during retry pass — skipping")
                    report.append({"venue": venue_name, "status": "ERROR", "reason": "Retry pass: button not found"})
                    continue

                toggles = page.get_by_role("switch")
                for _ in range(5):
                    if await toggles.count() > 0:
                        break
                    await asyncio.sleep(3)
                if await toggles.count() == 0:
                    toggles = page.locator("[role='switch'], [type='checkbox'][class*='witch'], [aria-checked]")
                    await asyncio.sleep(2)
                toggle_count = await toggles.count()

                if toggle_count == 0:
                    print(f"   ⚠ Cohorts not found during retry pass")
                    report.append({"venue": venue_name, "status": "ERROR", "reason": "Retry pass: cohorts not found"})
                    continue

                enabled_cohorts = []
                cohort_names = {}
                for t in range(toggle_count):
                    toggle = toggles.nth(t)
                    name = f"#{t+1}"
                    for level in range(1, 6):
                        xpath_up = "/".join([".."] * level)
                        container = toggle.locator(f"xpath={xpath_up}")
                        texts = await container.inner_text()
                        first_line = texts.strip().split("\n")[0].strip()
                        if first_line and len(first_line) > 3 and first_line not in ("Discounts",):
                            name = first_line
                            break
                    cohort_names[t] = name

                if cohort_mode == "name":
                    for keyword in cohort_keywords:
                        for level in range(1, 8):
                            xpath_up = "/".join([".."] * level)
                            container = page.get_by_text(keyword, exact=False).first.locator(f"xpath={xpath_up}")
                            toggle_in = container.locator("[role='switch']")
                            if await toggle_in.count() == 1:
                                is_on = await toggle_in.get_attribute("aria-checked")
                                if is_on != "true":
                                    await toggle_in.click()
                                    await asyncio.sleep(0.5)
                                    enabled_cohorts.append(keyword)
                                else:
                                    enabled_cohorts.append(f"{keyword} (was already on)")
                                break
                else:
                    for t in range(toggle_count):
                        toggle = toggles.nth(t)
                        cname = cohort_names.get(t, f"#{t+1}")
                        is_on = await toggle.get_attribute("aria-checked")
                        should_enable = cohort_indices is None or t in cohort_indices
                        if should_enable and is_on != "true":
                            await toggle.click()
                            await asyncio.sleep(0.5)
                            enabled_cohorts.append(cname)
                        elif should_enable:
                            enabled_cohorts.append(f"{cname} (was already on)")

                if start_date or end_date:
                    try:
                        edit_btn = page.locator("button:has-text('Edit')").first
                        if await edit_btn.count() > 0:
                            is_disabled = await edit_btn.get_attribute("disabled")
                            if is_disabled is None:
                                await edit_btn.click(timeout=5000)
                        else:
                            await page.get_by_text("Edit", exact=True).first.click(timeout=5000)
                        await asyncio.sleep(2)
                        if start_date:
                            si = page.get_by_role("textbox", name="Start date")
                            await si.click(click_count=3)
                            await asyncio.sleep(0.3)
                            await si.fill(start_date)
                        if end_date:
                            ei = page.get_by_role("textbox", name="End date")
                            await ei.click(click_count=3)
                            await asyncio.sleep(0.3)
                            await ei.fill(end_date)
                        await asyncio.sleep(0.5)
                        await dismiss_overlays(page)
                        save_btn = page.locator("button:has-text('Save')").first
                        if await save_btn.count() > 0:
                            await save_btn.click(timeout=5000)
                            await asyncio.sleep(1)
                    except Exception:
                        pass

                await dismiss_overlays(page)
                tc = page.locator("input[type='checkbox']")
                if await tc.count() > 0:
                    checkbox = tc.last
                    try:
                        if not await checkbox.is_checked():
                            await checkbox.click()
                            await asyncio.sleep(0.5)
                    except Exception:
                        await checkbox.click(force=True)
                        await asyncio.sleep(0.5)

                await dismiss_overlays(page)
                schedule_btn = page.locator("button:has-text('Schedule promotion'), button:has-text('Запланувати')")
                try:
                    await schedule_btn.first.click(timeout=5000)
                    await asyncio.sleep(3)
                    print(f"   ✓ Smart Promo activated (retry pass)!")
                    cohort_str = ", ".join(enabled_cohorts) if enabled_cohorts else "all"
                    dates_str = f"{start_date} — {end_date}" if start_date and end_date else "default"
                    # Видаляємо попередній запис RETRY
                    report[:] = [r for r in report if not (r["venue"] == venue_name and r["status"] == "RETRY")]
                    report.append({"venue": venue_name, "status": "ACTIVATED", "reason": f"Cohorts: {cohort_str} | Dates: {dates_str} (after replacement)"})
                except Exception:
                    print(f"   ⚠ Failed to activate — check manually")
                    input("   [Check and press Enter] ")

                await dismiss_overlays(page)
                await asyncio.sleep(1)

        # Звіт
        activated = [r for r in report if r["status"] == "ACTIVATED"]
        skipped = [r for r in report if r["status"] == "SKIPPED"]
        errors = [r for r in report if r["status"] == "ERROR"]
        manual = [r for r in report if r["status"] == "MANUAL"]

        print(f"\n{'='*60}")
        print(f"  REPORT — Smart Promo")
        print(f"{'='*60}")
        print(f"  Total venues:  {len(venues)}")
        print(f"  ✓ Activated:   {len(activated)}")
        print(f"  ○ Skipped:     {len(skipped)}")
        print(f"  ✋ Manual:      {len(manual)}")
        print(f"  ✕ Errors:      {len(errors)}")
        print(f"{'='*60}")

        if activated:
            print(f"\n  ✓ ACTIVATED ({len(activated)}):")
            for r in activated:
                print(f"    • {r['venue']}")
                print(f"      {r['reason']}")

        if skipped:
            print(f"\n  ○ SKIPPED ({len(skipped)}):")
            for r in skipped:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        if manual:
            print(f"\n  ✋ MANUAL ({len(manual)}):")
            for r in manual:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        if errors:
            print(f"\n  ✕ ERRORS ({len(errors)}):")
            for r in errors:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        not_in_report = set(venues) - {r["venue"] for r in report}
        if not_in_report:
            print(f"\n  ? NOT PROCESSED ({len(not_in_report)}):")
            for v in not_in_report:
                print(f"    • {v}")
                print(f"      Reason: already active or skipped without marking")

        print(f"\n{'='*60}\n")
        await browser.close()


# ---------------------------------------------------------------------------
# Phase 2: Food Partner Portal — Sponsored Listing
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Phase 3: Food Partner Portal — End Smart Promo
# ---------------------------------------------------------------------------

async def end_promo(login: str, password: str, filters: str = None):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await login_food_partner(page, login, password)

        all_venues = await get_all_venues(page)
        if filters:
            filter_parts = [f.strip() for f in filters.split(",")]
            venues = [v for v in all_venues if any(f in v for f in filter_parts)]
            print(f"\n>> Found {len(all_venues)} venues, selected {len(venues)} by filter")
        else:
            venues = all_venues
            print(f"\n>> Found {len(venues)} venues")

        report = []

        for i, venue_name in enumerate(venues):
            print(f"\n>> [{i+1}/{len(venues)}] End Promo for: {venue_name}")

            try:
                await ensure_logged_in(page, login, password)
                await handle_error_page(page)

                try:
                    await switch_venue(page, venue_name)
                except Exception:
                    await dismiss_overlays(page)
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    await ensure_logged_in(page, login, password)
                    await page.goto("https://foodpartner.bolt.eu/dashboard/promotions")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    await dismiss_overlays(page)
                    await handle_error_page(page)
                    await switch_venue(page, venue_name)

                await page.locator("a:has-text('Promotions'), a:has-text('Промоакції')").first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                await handle_error_page(page)

                # Шукаємо саме "Custom smart promotion" — інші промо не чіпаємо
                smart_promo = page.get_by_text("Custom smart promotion", exact=False)
                if await smart_promo.count() == 0:
                    print(f"   ○ No Smart Promo — skipping")
                    report.append({"venue": venue_name, "status": "SKIPPED", "reason": "Smart Promo not found (other promos may be active)"})
                    continue

                await smart_promo.first.click(timeout=5000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # Зчитуємо інфо про когорти та дати перед вимкненням
                cohorts_info = []
                discounts_section = page.locator("text=Discounts").first
                if await discounts_section.count() > 0:
                    container = discounts_section.locator("xpath=../..")
                    items = container.locator("h3, h4, strong, [class*='title']")
                    for idx in range(await items.count()):
                        txt = (await items.nth(idx).inner_text()).strip()
                        if txt and txt != "Discounts":
                            cohorts_info.append(txt)
                if not cohorts_info:
                    all_text = await page.locator("main").inner_text()
                    for keyword in ["Top Customers", "Найкращі", "New to Bolt", "Нові", "Lapsed", "Давно", "High spenders", "Великий чек"]:
                        if keyword in all_text:
                            cohorts_info.append(keyword)

                dates_info = ""
                start_el = page.get_by_text("Start date").first
                if await start_el.count() > 0:
                    row = start_el.locator("xpath=..")
                    dates_info = (await row.inner_text()).strip().replace("\n", " ")
                if not dates_info:
                    end_el = page.get_by_text("End date").first
                    if await end_el.count() > 0:
                        row = end_el.locator("xpath=..")
                        dates_info = (await row.inner_text()).strip().replace("\n", " ")

                cohorts_str = ", ".join(cohorts_info) if cohorts_info else "not determined"
                print(f"   Cohorts: {cohorts_str}")
                if dates_info:
                    print(f"   {dates_info}")

                # Натискаємо "End promotion" (червона кнопка)
                await dismiss_overlays(page)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

                end_btn = page.locator("button:has-text('End promotion'), button:has-text('Завершити промоакцію')")
                if await end_btn.count() == 0:
                    print(f"   ⚠ 'End promotion' button not found — skipping")
                    report.append({"venue": venue_name, "status": "ERROR", "reason": "End promotion button not found"})
                    continue

                await end_btn.first.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await dismiss_overlays(page)
                await end_btn.first.click(timeout=10000)
                await asyncio.sleep(2)

                # Підтверджуємо в діалозі — натискаємо "End promotion" ще раз
                await asyncio.sleep(1)
                confirm_btn = page.locator("button:has-text('End promotion'), button:has-text('Завершити промоакцію')")
                try:
                    await confirm_btn.last.click(timeout=10000)
                    await asyncio.sleep(3)
                    print(f"   ✓ Promo disabled!")
                    detail = f"Cohorts: {cohorts_str}"
                    if dates_info:
                        detail += f" | {dates_info}"
                    report.append({"venue": venue_name, "status": "DISABLED", "reason": detail})
                except Exception:
                    print(f"   ⚠ Failed to confirm — check manually")
                    input("   [Check and press Enter] ")
                    report.append({"venue": venue_name, "status": "MANUAL", "reason": f"Cohorts: {cohorts_str} — needs manual confirmation"})

                await dismiss_overlays(page)
                await asyncio.sleep(1)

            except Exception as e:
                print(f"   ⚠ Error: {str(e)[:80]} — skipping")
                report.append({"venue": venue_name, "status": "ERROR", "reason": str(e)[:120]})
                await dismiss_overlays(page)
                await asyncio.sleep(1)

        # Звіт
        ended = [r for r in report if r["status"] == "DISABLED"]
        skipped = [r for r in report if r["status"] == "SKIPPED"]
        errors = [r for r in report if r["status"] == "ERROR"]
        manual = [r for r in report if r["status"] == "MANUAL"]

        print(f"\n{'='*60}")
        print(f"  REPORT — End Promo")
        print(f"{'='*60}")
        print(f"  Total venues:  {len(venues)}")
        print(f"  ✓ Disabled:    {len(ended)}")
        print(f"  ○ Skipped:     {len(skipped)}")
        print(f"  ✋ Manual:      {len(manual)}")
        print(f"  ✕ Errors:      {len(errors)}")
        print(f"{'='*60}")

        if ended:
            print(f"\n  ✓ DISABLED ({len(ended)}):")
            for r in ended:
                print(f"    • {r['venue']}")

        if skipped:
            print(f"\n  ○ SKIPPED ({len(skipped)}):")
            for r in skipped:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        if manual:
            print(f"\n  ✋ MANUAL ({len(manual)}):")
            for r in manual:
                print(f"    • {r['venue']}")

        if errors:
            print(f"\n  ✕ ERRORS ({len(errors)}):")
            for r in errors:
                print(f"    • {r['venue']}")
                print(f"      Reason: {r['reason']}")

        print(f"\n{'='*60}\n")
        await browser.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_all_venues(page) -> list[str]:
    """Отримує список venues з venue selector у навбарі."""
    await dismiss_overlays(page)
    venue_btn = page.locator("nav button").first
    await venue_btn.click()
    await asyncio.sleep(2)

    menu_items = page.locator("[role='menuitem']")
    count = await menu_items.count()
    venues = []
    for i in range(count):
        item = menu_items.nth(i)
        text = await item.inner_text()
        name = text.split("\n")[0].strip()
        if name:
            venues.append(name)

    await page.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    return venues


async def switch_venue(page, venue_name: str):
    """Перемикається на venue через venue selector menu."""
    await dismiss_overlays(page)
    venue_btn = page.locator("nav button").first
    await venue_btn.click()
    await asyncio.sleep(1)

    # Використовуємо пошук якщо є
    search = page.locator("input[placeholder='Search venues'], input[type='search']")
    if await search.count() > 0:
        await search.fill(venue_name[:20])
        await asyncio.sleep(1)

    # Нормалізуємо апострофи для пошуку
    normalized = venue_name.replace("\u02BC", "'").replace("\u2019", "'")

    target = page.get_by_role("menuitem").filter(has_text=venue_name)
    if await target.count() == 0 and normalized != venue_name:
        target = page.get_by_role("menuitem").filter(has_text=normalized)
    if await target.count() == 0:
        # Fallback: шукаємо по тексту без role
        target = page.get_by_text(venue_name, exact=False)
        if await target.count() == 0 and normalized != venue_name:
            target = page.get_by_text(normalized, exact=False)

    if await target.count() > 0:
        await target.first.click()
        await asyncio.sleep(3)
    else:
        await page.keyboard.press("Escape")
        raise Exception(f"Venue '{venue_name}' not found in menu")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Promo Bot — Bolt Food promo automation")
    subparsers = parser.add_subparsers(dest="command")

    # add-vendors (швидкий — тільки вендори)
    p_vendors = subparsers.add_parser("add-vendors", help="Add vendors via Admin Panel (fast)")
    p_vendors.add_argument("--csv", required=True, help="Path to CSV file")
    p_vendors.add_argument("--account", required=True, help="Account ID from Admin Panel URL (e.g. 20239)")

    # add-venues (детальний — провайдери)
    p_venues = subparsers.add_parser("add-venues", help="Add venues via Admin Panel (detailed)")
    p_venues.add_argument("--csv", required=True, help="Path to CSV file with providers")
    p_venues.add_argument("--account", required=True, help="Account ID from Admin Panel URL (e.g. 20239)")

    # check-promo
    p_check = subparsers.add_parser("check-promo", help="Check which Smart Promos are available per venue")
    p_check.add_argument("--login", required=True, help="Email for Food Partner Portal")
    p_check.add_argument("--password", required=True, help="Password")
    p_check.add_argument("--venues", default=None, help="Filter venues (name parts comma-separated)")

    # check-listing
    p_check_l = subparsers.add_parser("check-listing", help="Check which Sponsored Listings are available per venue")
    p_check_l.add_argument("--login", required=True, help="Email for Food Partner Portal")
    p_check_l.add_argument("--password", required=True, help="Password")
    p_check_l.add_argument("--venues", default=None, help="Filter venues (name parts comma-separated)")

    # smart-promo
    p_smart = subparsers.add_parser("smart-promo", help="Set up Smart Promotions")
    p_smart.add_argument("--login", required=True, help="Email for Food Partner Portal")
    p_smart.add_argument("--password", required=True, help="Password")
    p_smart.add_argument("--start", default=None, help="Start date (DD/MM/YYYY)")
    p_smart.add_argument("--end", default=None, help="End date (DD/MM/YYYY)")
    p_smart.add_argument(
        "--cohorts", default="all",
        help="Cohorts: 'all' (all) or numbers comma-separated '1,3' (1=New, 2=Lapsed, 3=Active, 4=High spenders)",
    )
    p_smart.add_argument(
        "--venues", default=None,
        help="Filter venues: name parts comma-separated, e.g. 'Грушевського,Валова,Костомарова'",
    )

    # end-promo
    p_end = subparsers.add_parser("end-promo", help="Disable active Smart Promotions")
    p_end.add_argument("--login", required=True, help="Email for Food Partner Portal")
    p_end.add_argument("--password", required=True, help="Password")
    p_end.add_argument("--venues", default=None, help="Filter venues (name parts comma-separated)")

    args = parser.parse_args()

    if args.command == "add-vendors":
        asyncio.run(add_vendors(args.csv, args.account))
    elif args.command == "add-venues":
        asyncio.run(add_venues(args.csv, args.account))
    elif args.command == "check-promo":
        asyncio.run(check_promo(args.login, args.password, args.venues))
    elif args.command == "check-listing":
        asyncio.run(check_listing(args.login, args.password, args.venues))
    elif args.command == "smart-promo":
        asyncio.run(setup_smart_promo(args.login, args.password, args.start, args.end, args.cohorts, args.venues))
    elif args.command == "end-promo":
        asyncio.run(end_promo(args.login, args.password, args.venues))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
