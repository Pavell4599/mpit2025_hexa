# parser.py
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def parse_federal_reestr_with_inn_ogrn(max_records=5):
    """Парсит данные из реестра и возвращает список записей."""
    print("🔍 Шаг 1: Запуск парсинга данных из реестра...")
    driver = create_stealth_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get("https://reestr.digital.gov.ru/reestr/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.collection-registry")))
        time.sleep(random.uniform(2, 3))

        # === Сбор данных с главной страницы ===
        rows = driver.find_elements(By.CSS_SELECTOR, "div.collection-item.a-link")
        basic_data = []
        
        for row in rows[:max_records]:
            try:
                number_elem = row.find_element(By.CSS_SELECTOR, 'div[data-name="№ реестровой записи"] span')
                number = number_elem.text.strip()
                
                software_elem = row.find_element(By.CSS_SELECTOR, 'div[data-name="Наименование ПО"]')
                software = software_elem.text.strip()
                
                owner_elem = row.find_element(By.CSS_SELECTOR, 'div[data-name="Правообладатель"] .owner-name')
                owner = owner_elem.text.strip()
                
                data_href = row.get_attribute("data-href")
                url = f"https://reestr.digital.gov.ru{data_href}" if data_href else ""
                
                if number and software and owner and url:
                    basic_data.append({
                        "number": number,
                        "software": software,
                        "owner": owner,
                        "url": url
                    })
                    print(f"✅ {number} | {software} | {owner}")
            except Exception as e:
                print(f"⚠️ Пропущена запись: {e}")
                continue

        if not basic_data:
            print("❌ Не удалось собрать данные с главной страницы.")
            return []

        print(f"\n✅ Успешно собрано {len(basic_data)} записей. Собираем ИНН и ОГРН...\n")

        # === Переход на страницу → сбор ИНН и ОГРН ===
        final_results = []
        for i, item in enumerate(basic_data):
            print(f"[{i+1}/{len(basic_data)}] ➤ {item['number']}")
            driver.get(item["url"])
            time.sleep(random.uniform(1.5, 2.5))

            inn = ""
            ogrn = ""

            # --- ИНН ---
            try:
                inn_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Идентификационный номер (ИНН)')]")
                inn_value = inn_label.find_element(By.XPATH, "./following-sibling::div[@class='fs-5']")
                inn = inn_value.text.strip()
            except Exception as e:
                print(f"    ❌ ИНН не найден")
                inn = ""

            # --- ОГРН (улучшенный поиск) ---
            try:
                # Вариант 1: точный текст
                ogrn_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Основной государственный регистрационный номер (ОГРН)')]")
                ogrn_value = ogrn_label.find_element(By.XPATH, "./following-sibling::div[@class='fs-5']")
                ogrn = ogrn_value.text.strip()
            except:
                pass

            # Вариант 2: без "(ОГРН)"
            if not ogrn:
                try:
                    ogrn_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Основной государственный регистрационный номер')]")
                    ogrn_value = ogrn_label.find_element(By.XPATH, "./following-sibling::div[@class='fs-5']")
                    ogrn = ogrn_value.text.strip()
                except:
                    pass

            # Вариант 3: поиск по тексту "ОГРН" в label
            if not ogrn:
                try:
                    elements = driver.find_elements(By.XPATH, "//label[contains(text(), 'ОГРН')]//following-sibling::div[@class='fs-5']")
                    if elements:
                        ogrn = elements[0].text.strip()
                except:
                    pass

            if not ogrn:
                print(f"    ❌ ОГРН не найден")
            else:
                print(f"    ✅ ОГРН: {ogrn}")

            final_results.append({
                "Номер записи": item["number"],
                "Название ПО": item["software"],
                "Правообладатель": item["owner"],
                "ИНН": inn,
                "ОГРН": ogrn,
                "URL": item["url"]
            })

        return final_results

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return []
    finally:
        driver.quit()

# === Основной запуск + экспорт в Excel ===
if __name__ == "__main__":
    # Парсим 10 компаний
    data = parse_federal_reestr_with_inn_ogrn(max_records=10)

    if data:
        # Преобразуем в DataFrame
        df = pd.DataFrame(data)

        # Сохраняем в Excel
        output_file = "reestr_companies.xlsx"
        df.to_excel(output_file, index=False, engine='openpyxl')

        print(f"\n✅ Данные успешно сохранены в файл: {output_file}")
        print(f"📁 Количество записей: {len(df)}")
    else:
        print("\n❌ Нет данных для сохранения.")