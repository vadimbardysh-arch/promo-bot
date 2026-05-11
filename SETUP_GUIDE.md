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

### Перед кожним запуском

Відкрий Terminal і перейди в папку зі скриптом:

```
cd ~/Desktop/promo-bot
```

> 💡 **Як знайти Terminal:** натисни `Cmd + Пробіл`, напиши `Terminal`, натисни Enter.

---

### 1. Додати вендорів в акаунт через Admin Panel

Покласти CSV файл в папку `promo-bot` на Desktop, потім:

```
cd ~/Desktop/promo-bot
python3 promo_bot.py add-vendors --csv venues.csv
```

Скрипт відкриє Admin Panel → залогінся вручну → скрипт додасть вендорів з CSV автоматично.

### 2. Додати провайдерів в акаунт через Admin Panel

```
cd ~/Desktop/promo-bot
python3 promo_bot.py add-venues --csv venues.csv
```

Те саме, але додає окремих провайдерів замість вендорів.

### 3. Перевірити доступні Smart Promo

```
cd ~/Desktop/promo-bot
python3 promo_bot.py check-promo --login EMAIL --password PASS
```

Замість `EMAIL` і `PASS` підстав реальні креди для Food Partner Portal.

### 3.1 Перевірити доступні Sponsored Listing

```
cd ~/Desktop/promo-bot
python3 promo_bot.py check-listing --login EMAIL --password PASS
```

### 4. Підключити Smart Promo (всі точки)

```
cd ~/Desktop/promo-bot
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts "All"
```

Параметри:
- `--start` — дата початку (формат: DD/MM/YYYY, наприклад `22/04/2026`)
- `--end` — дата закінчення (формат: DD/MM/YYYY, наприклад `28/04/2026`)
- `--cohorts` — які когорти увімкнути:
  - `"All"` — всі доступні когорти
  - `"Top Customers"` — лише когорта з такою назвою (в лапках!)
  - `"Найкращі"` — по українській назві
  - `1,3` — 1-ша і 3-тя когорта за порядком

### 4.1 Підключити Smart Promo на окремі точки

Додай `--venues` з назвами через кому (в лапках):

```
cd ~/Desktop/promo-bot
python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts "All" --venues "PASTA ITALIANO,Pani Mozzarella"
```

### 5. Вимкнути Smart Promo (всі точки)

```
cd ~/Desktop/promo-bot
python3 promo_bot.py end-promo --login EMAIL --password PASS
```

### 5.1 Вимкнути Smart Promo на окремі точки

```
cd ~/Desktop/promo-bot
python3 promo_bot.py end-promo --login EMAIL --password PASS --venues "PASTA ITALIANO,Pani Mozzarella"
```

---

### Як правильно вказати шлях до CSV файлу

**Варіант 1 (найпростіший):** покласти CSV файл в папку `promo-bot` на Desktop і вказати тільки назву:

```
python3 promo_bot.py add-vendors --csv venues.csv
```

**Варіант 2:** файл лежить в Downloads:

```
python3 promo_bot.py add-vendors --csv ~/Downloads/venues.csv
```

**Варіант 3 (drag & drop):** написати команду до `--csv ` і після пробілу **перетягнути файл з Finder прямо в Terminal** — шлях вставиться автоматично:

```
python3 promo_bot.py add-vendors --csv [перетягни CSV файл сюди]
```

> ⚠️ **Важливо:** `/path/to/file.csv` — це приклад, не справжній шлях! Завжди вказуй реальну назву або шлях до свого CSV файлу. Якщо в шляху є пробіли — оберни його в лапки: `"my file.csv"`

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
