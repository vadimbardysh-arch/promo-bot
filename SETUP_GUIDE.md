# Promo Bot — Інструкція з налаштування

Покрокова інструкція для налаштування скрипта на твоєму Mac.

---

## Крок 1: Встановити Python

Перевір чи Python вже встановлений. Відкрий **Terminal** (Finder → Програми → Утиліти → Terminal) і введи:

```
python3 --version
```

Якщо бачиш щось на кшталт `Python 3.12.0` — переходь до Кроку 2.

Якщо бачиш помилку — встанови Python:

1. Перейди на https://www.python.org/downloads/
2. Натисни жовту кнопку **Download Python**
3. Відкрий завантажений `.pkg` файл
4. Натискай **Continue → Continue → Agree → Install**
5. Після встановлення закрий і знову відкрий Terminal
6. Перевір ще раз: `python3 --version`

---

## Крок 2: Встановити Git

Перевір чи Git вже встановлений:

```
git --version
```

Якщо бачиш `git version 2.x.x` — переходь до Кроку 3.

Якщо Mac запитає "Would you like to install developer tools?" — натисни **Install** і дочекайся завершення.

---

## Крок 3: Завантажити Promo Bot

В Terminal виконай ці команди (копіюй кожну і натискай Enter):

```
cd ~/Desktop
```

```
git clone https://github.com/vadimbardysh-arch/promo-bot.git
```

```
cd promo-bot
```

Після цього на Робочому столі з'явиться папка **promo-bot**.

---

## Крок 4: Запустити інсталяцію

Все ще в Terminal, виконай:

```
./install.sh
```

Якщо бачиш помилку "permission denied":

```
chmod +x install.sh && ./install.sh
```

Дочекайся повідомлення **"✓ Встановлення завершено!"**

Це потрібно зробити лише один раз.

---

## Крок 5: Готово! Як запускати

### Відкрити Terminal і перейти в папку

Кожного разу коли хочеш запустити скрипт, спочатку перейди в папку:

```
cd ~/Desktop/promo-bot
```

### Перевірити які Smart Promo доступні

```
python3 promo_bot.py check-promo --login EMAIL --password PASS
```

Замість `EMAIL` та `PASS` підстав реальні дані для Food Partner Portal.

### Перевірити які Sponsored Listing доступні

```
python3 promo_bot.py check-listing --login EMAIL --password PASS
```

### Підключити Smart Promo

```
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start 01/05/2026 --end 15/05/2026 --cohorts all
```

Параметри:
- `--start` — дата початку (формат: DD/MM/YYYY)
- `--end` — дата закінчення (формат: DD/MM/YYYY)
- `--cohorts` — які когорти увімкнути:
  - `all` — всі доступні
  - `"Найкращі"` — лише когорта з такою назвою (в лапках!)
  - `"Top Customers"` — по англійській назві
  - `1,3` — 1-ша і 3-тя когорта за порядком

### Вимкнути Smart Promo

```
python3 promo_bot.py end-promo --login EMAIL --password PASS
```

### Додати заклади через Admin Panel

```
python3 promo_bot.py add-vendors --csv venues.csv
```

Скрипт відкриє Admin Panel → залогінся вручну → скрипт додасть вендорів з CSV.

#### Як правильно вказати шлях до CSV файлу

**Варіант 1 (найпростіший):** покласти CSV файл в папку `promo-bot` на Desktop і вказати тільки назву:

```
python3 promo_bot.py add-vendors --csv venues.csv
```

**Варіант 2:** файл лежить в Downloads:

```
python3 promo_bot.py add-vendors --csv ~/Downloads/venues.csv
```

**Варіант 3 (drag & drop):** написати команду до `--csv` і після пробілу **перетягнути файл з Finder прямо в Terminal** — шлях вставиться автоматично:

```
python3 promo_bot.py add-vendors --csv [перетягни CSV файл сюди]
```

> ⚠️ **Важливо:** `/path/to/file.csv` — це приклад, не справжній шлях! Завжди вказуй реальну назву або шлях до свого CSV файлу.

### Фільтр по конкретних venues

Додай `--venues` щоб обробити тільки певні точки:

```
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start 01/05/2026 --end 15/05/2026 --cohorts all --venues "Грушевського,Валова"
```

---

## Як оновити скрипт

Коли Вадим скаже що є оновлення:

```
cd ~/Desktop/promo-bot
```

```
git pull
```

---

## Часті проблеми

### "command not found: python3"
Python не встановлений. Повернись до Кроку 1.

### "permission denied"
Виконай `chmod +x install.sh` і спробуй знову.

### "xcrun: error: invalid active developer path"
Потрібно встановити Xcode Command Line Tools:
```
xcode-select --install
```

### Скрипт відкриває браузер але нічого не відбувається
Дочекайся — скрипт працює автоматично. Не клікай нічого в браузері поки скрипт працює.

### "Timeout exceeded"
Інтернет повільний або сторінка довго вантажиться. Запусти ще раз.

### Браузер закрився з помилкою
Запусти команду ще раз — скрипт пропустить venues де промо вже підключено.

### Як знайти Terminal?
- Натисни `Cmd + Пробіл` (Spotlight)
- Напиши `Terminal`
- Натисни Enter

---

## Повний список команд

| Команда | Що робить |
|---------|-----------|
| `check-promo` | Перевіряє які Smart Promo доступні |
| `check-listing` | Перевіряє які Sponsored Listing доступні |
| `smart-promo` | Підключає Smart Promotions |
| `end-promo` | Вимикає активні Smart Promotions |
| `listing` | Запускає Sponsored Listing |
| `add-vendors` | Додає вендорів через Admin Panel |
| `add-venues` | Додає провайдерів через Admin Panel |

Щоб побачити всі параметри будь-якої команди:

```
python3 promo_bot.py smart-promo --help
```
