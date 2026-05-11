# Promo Bot

Автоматизація промо-кампаній через Bolt Food Partner Portal.

## Що вміє

| Команда | Опис |
|---------|------|
| `add-vendors` | Додати вендорів через Admin Panel (швидкий) |
| `add-venues` | Додати окремих провайдерів через Admin Panel |
| `check-promo` | Перевірити які Smart Promo доступні кожній venue |
| `check-listing` | Перевірити які Sponsored Listing доступні кожній venue |
| `smart-promo` | Підключити Smart Promotions |
| `end-promo` | Вимкнути активні Smart Promotions |
| `listing` | Запустити Sponsored Listing |

## Встановлення

### 1. Клонувати репозиторій

```bash
git clone https://github.com/YOUR_USERNAME/promo-bot.git
cd promo-bot
```

### 2. Запустити інсталяцію

```bash
./install.sh
```

Це встановить Python-залежності та Chromium для браузерної автоматизації.

### 3. Оновлення

Коли з'являться оновлення:

```bash
cd promo-bot
git pull
```

## Використання

### Типовий робочий цикл

**Фаза 1 — Додати заклади в портал:**

```bash
python3 promo_bot.py add-vendors --csv /path/to/file.csv
```

Скрипт відкриє Admin Panel → залогінся вручну → скрипт додасть вендорів з CSV.

**Фаза 2 — Перевірити доступні промо:**

```bash
python3 promo_bot.py check-promo --login EMAIL --password PASS
```

```bash
python3 promo_bot.py check-listing --login EMAIL --password PASS
```

**Фаза 3 — Підключити промо:**

```bash
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start 01/05/2026 --end 15/05/2026 --cohorts all
```

**Вимкнути промо:**

```bash
python3 promo_bot.py end-promo --login EMAIL --password PASS
```

### Параметри Smart Promo

| Параметр | Опис | Приклад |
|----------|------|---------|
| `--login` | Email для Food Partner Portal | `user@gmail.com` |
| `--password` | Пароль | `MyPass123` |
| `--start` | Дата початку | `01/05/2026` |
| `--end` | Дата закінчення | `15/05/2026` |
| `--cohorts` | Когорти користувачів | `all`, `"Найкращі"`, `1,3` |
| `--venues` | Фільтр venues (необов'язково) | `"Грушевського,Валова"` |

### Когорти

- `all` або `All` — увімкнути всі доступні когорти
- `"Найкращі"` — увімкнути лише когорту, назва якої містить "Найкращі"
- `"Top Customers"` — по англійській назві
- `1,3` — увімкнути 1-шу та 3-тю когорту (за порядком на сторінці)

### CSV формат

CSV файл для `add-vendors` / `add-venues` має містити колонки:

| Колонка | Опис |
|---------|------|
| `2. Merchant Information City Name` | Назва міста |
| `2. Merchant Information Provider ID` | ID провайдера |
| `2. Merchant Information Provider Name` | Назва провайдера |
| `2. Merchant Information Vendor ID` | ID вендора |
| `2. Merchant Information Vendor Name` | Назва вендора |

## Troubleshooting

- **Скрипт не знаходить venue** — може бути через апостроф (ʼ vs '). Спробуй `--venues` з частиною назви
- **Cookie banner блокує кліки** — скрипт автоматично прибирає оверлеї, але іноді потрібна пауза
- **"Oops, something went wrong"** — скрипт натисне "Try again" автоматично
- **Розлогінило** — скрипт автоматично залогіниться заново
- **Скріншоти** — зберігаються в папці `screenshots/` коли скрипт не знаходить когорти чи кнопки
