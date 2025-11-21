# --------------------------------------------------
# Шаг 1: Парсинг данных
# --------------------------------------------------
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import webbrowser

def create_stealth_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=MediaRouter,WebRTC')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("window.chrome = {runtime: {}}")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru']})")
    return driver

def parse_federal_reestr(max_records=20):
    """Парсит данные из федерального реестра ПО"""
    print("🔍 Шаг 1: Запуск парсинга данных из реестра...")
    driver = create_stealth_driver()
    try:
        driver.get("https://reestr.digital.gov.ru/reestr/")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.collection-registry"))
        )
        time.sleep(random.uniform(2, 4))

        rows = driver.find_elements(By.CSS_SELECTOR, "div.collection-item.a-link")
        results = []
        for row in rows[:max_records]:
            try:
                number = row.find_element(By.CSS_SELECTOR, 'div[data-name="№ реестровой записи"] span').text.strip()
                software = row.find_element(By.CSS_SELECTOR, 'div[data-name="Наименование ПО"]').text.strip()
                owner = row.find_element(By.CSS_SELECTOR, 'div[data-name="Правообладатель"] .owner-name').text.strip()
                if number and software and owner:
                    results.append({"number": number, "software": software, "owner": owner})
            except Exception:
                continue
        print(f"✅ Успешно получено {len(results)} записей.")
        return results
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        return []
    finally:
        driver.quit()

# --------------------------------------------------
# Шаг 2: Генерация HTML-страницы с данными
# --------------------------------------------------
def render_html_page(data, output_path="it_reestr_kaliningrad.html"):
    """Создаёт HTML-страницу и 'загружает' в неё данные"""
    print("🎨 Шаг 2: Генерация HTML-страницы...")
    
    # Подготавливаем строки карточек
    cards_html = ""
    for item in data:
        cards_html += f"""
        <div class="company-card">
            <div class="registry-number">№ {item['number']}</div>
            <div class="software-name">{item['software']}</div>
            <div class="owner-label">Правообладатель:</div>
            <div class="owner-name">{item['owner']}</div>
        </div>
        """

    full_html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>ИТ-компании | Калининград</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f8fafc;
            color: #1e293b;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 40px 0 30px;
        }}
        h1 {{
            font-size: 2.2rem;
            color: #1d4ed8;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 1.1rem;
        }}
        .counter {{
            background: #dbeafe;
            color: #1d4ed8;
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            margin-top: 12px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 24px;
        }}
        .company-card {{
            background: white;
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            transition: transform 0.2s;
        }}
        .company-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        }}
        .registry-number {{
            background: #eff6ff;
            color: #1d4ed8;
            font-size: 0.85rem;
            padding: 4px 12px;
            border-radius: 50px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 14px;
        }}
        .software-name {{
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 12px;
            line-height: 1.3;
        }}
        .owner-label {{
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 4px;
        }}
        .owner-name {{
            font-size: 1.05rem;
            color: #334155;
        }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Реестр ИТ-компаний</h1>
            <div class="subtitle">Калининградская область • Данные из федерального реестра ПО</div>
            <div class="counter">Загружено компаний: {len(data)}</div>
        </header>
        <div class="grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"✅ HTML-страница создана: {os.path.abspath(output_path)}")
    return output_path

# --------------------------------------------------
# Главный запуск
# --------------------------------------------------
if __name__ == "__main__":
    # 1. Парсим данные
    parsed_data = parse_federal_reestr(max_records=20)

    if not parsed_data:
        print("⚠️ Нет данных для отображения.")
        exit()

    # 2. Генерируем и "загружаем" их на HTML-страницу
    html_file = render_html_page(parsed_data, "reestr_kaliningrad_it.html")

    # 3. Открываем в браузере
    print("🌐 Шаг 3: Открываю страницу в браузере...")
    webbrowser.open("file://" + os.path.abspath(html_file))