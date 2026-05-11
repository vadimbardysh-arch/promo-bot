#!/bin/bash
set -e

echo "========================================"
echo "  Promo Bot — встановлення залежностей"
echo "========================================"
echo ""

# Перевіряємо Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не знайдено."
    echo "   Встанови його: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✓ $PYTHON_VERSION"

# Встановлюємо залежності
echo ""
echo ">> Встановлюю Python-залежності..."
pip3 install -r requirements.txt --quiet

# Встановлюємо Chromium для Playwright
echo ""
echo ">> Встановлюю Chromium для Playwright..."
python3 -m playwright install chromium

echo ""
echo "========================================"
echo "  ✓ Встановлення завершено!"
echo "========================================"
echo ""
echo "Тепер можеш запускати:"
echo ""
echo "  # Перевірити які промо доступні"
echo "  python3 promo_bot.py check-promo --login EMAIL --password PASS"
echo ""
echo "  # Підключити Smart Promo"
echo "  python3 promo_bot.py smart-promo --login EMAIL --password PASS --start DD/MM/YYYY --end DD/MM/YYYY --cohorts all"
echo ""
echo "  # Вимкнути Smart Promo"
echo "  python3 promo_bot.py end-promo --login EMAIL --password PASS"
echo ""
echo "  Повний список команд: python3 promo_bot.py --help"
echo ""
