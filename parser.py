import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------

def create_stealth_driver():
    options = Options()
    # options.add_argument('--headless')  # раскомментировать для фонового режима
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ru')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-images')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            delete navigator.__proto__.webdriver;
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
            });
            Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru']});
        '''
    })
    return driver

def extract_text_by_keyword(page_text, keyword):
    pattern = rf"{re.escape(keyword)}\s*[:\-\s]*([^\n\r\t]+)"
    match = re.search(pattern, page_text)
    return match.group(1).strip() if match else ""

def parse_company_detail(driver, url):
    driver.get(url)
    time.sleep(2)

    try:
        full_name = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        full_name = "Название не найдено"

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except:
        body_text = ""

    # ИНН / КПП
    inn_kpp_raw = extract_text_by_keyword(body_text, "ИНН/КПП")
    if inn_kpp_raw:
        parts = inn_kpp_raw.split()
        inn = parts[0] if len(parts) > 0 else ""
        kpp = parts[1] if len(parts) > 1 else ""
    else:
        inn = kpp = ""

    # ОГРН
    ogrn = extract_text_by_keyword(body_text, "ОГРН").split()[0] if "ОГРН" in body_text else ""

    # Дата регистрации
    reg_date = extract_text_by_keyword(body_text, "Дата регистрации")
    if reg_date:
        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", reg_date)
        reg_date = date_match.group() if date_match else reg_date

    # Адрес
    address_match = re.search(r"\d{6},\s+[А-Яа-яЁё\s\-.,]+", body_text)
    address = address_match.group().strip() if address_match else ""

    # Руководитель
    director_match = re.search(r"(Директор|Руководитель|Генеральный директор)[\s\-—:]+([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)", body_text)
    director = director_match.group(2).strip() if director_match else ""

    # Коды статистики
    stats = {}
    for code in ["ОКПО", "ОКАТО", "ОКТМО", "ОКФС", "ОКОГУ", "ОКОПФ"]:
        stats[code] = extract_text_by_keyword(body_text, code)

    return {
        "Название": full_name,
        "ИНН": inn,
        "КПП": kpp,
        "ОГРН": ogrn,
        "Дата регистрации": reg_date,
        "Адрес": address,
        "Руководитель": director,
        "ОКПО": stats["ОКПО"],
        "ОКАТО": stats["ОКАТО"],
        "ОКТМО": stats["ОКТМО"],
        "ОКФС": stats["ОКФС"],
        "ОКОГУ": stats["ОКОГУ"],
        "ОКОПФ": stats["ОКОПФ"],
        "Ссылка Rusprofile": url
    }

def check_accreditation_on_gosuslugi(inn_list):
    """Проверяет ИНН на аккредитацию через https://www.gosuslugi.ru/itorgs"""
    driver = create_stealth_driver()
    results = []

    try:
        for inn in inn_list:
            if not inn or not re.fullmatch(r"\d{10}|\d{12}", inn):
                results.append("⚠️ Недействительный ИНН")
                continue

            print(f"🔍 Проверка ИНН {inn}...")
            driver.get("https://www.gosuslugi.ru/itorgs")
            wait = WebDriverWait(driver, 15)

            try:
                # Ожидаем поле ввода ИНН (внутри .white-box)
                input_field = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'white-box')]//input"))
                )
                input_field.clear()
                input_field.send_keys('\b' * 20)  # очистка
                input_field.send_keys(inn)
                input_field.send_keys(Keys.ENTER)

                # Ждём загрузки результата (до 15 секунд)
                time.sleep(15)

                # === СЛУЧАЙ 1: УСПЕХ (аккредитована) ===
                # На успешной странице должен быть заголовок с классом "title-h5"
                success_titles = driver.find_elements(By.XPATH, "//div[contains(@class, 'title-h5')]")
                if success_titles:
                    title_text = success_titles[0].text.strip()
                    # Если в заголовке есть фраза "входит в реестр", то аккредитована
                    if "входит в реестр аккредитованных ИТ-компаний" in title_text.lower():
                        status = "✅ Аккредитована"
                        results.append(status)
                        print(f"   → {status}")
                        continue

                # === СЛУЧАЙ 2: НЕ АККРЕДИТОВАНА (по вашему HTML) ===
                # В вашем HTML это div с классом "title-h5" и текстом "Компания не входит в реестр..."
                error_titles = driver.find_elements(By.XPATH, "//div[contains(@class, 'title-h5') and contains(text(), 'не входит в реестр')]")
                if error_titles:
                    status = "❌ Не аккредитована"
                    results.append(status)
                    print(f"   → {status}")
                    continue

                # === СЛУЧАЙ 3: ДРУГИЕ СООБЩЕНИЯ (например, "не найдена") ===
                other_errors = driver.find_elements(By.XPATH, "//div[contains(@class, 'alert-danger')] | //p[contains(text(), 'не найдена')]")
                if other_errors:
                    status = "⚠️ Не найдена"
                    results.append(status)
                    print(f"   → {status}")
                    continue

                # === СЛУЧАЙ 4: НЕОПРЕДЕЛЕННО ===
                status = "❓ Неизвестно"
                results.append(status)
                print(f"   → {status}")

            except Exception as e:
                status = f"⚠️ Ошибка: {str(e)[:60]}"
                results.append(status)
                print(f"   → {status}")

            time.sleep(1.5)

    finally:
        driver.quit()

    return results

# ------------------------------------------------------------
# ОСНОВНАЯ ЛОГИКА
# ------------------------------------------------------------

def main():
    try:
        company_count = int(input("Введите количество компаний для парсинга: "))
    except ValueError:
        print("❌ Введите корректное число.")
        return

    driver = create_stealth_driver()
    all_companies = []

    try:
        print("Загрузка Rusprofile...")
        driver.get("https://www.rusprofile.ru/search-advanced")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#additional-results"))
        )

        # Сбор ссылок на компании
        links = []
        while len(links) < company_count:
            elems = driver.find_elements(By.CSS_SELECTOR, "div.list-element")
            current = len(links)
            for i in range(current, min(company_count, len(elems))):
                try:
                    href = elems[i].find_element(By.CSS_SELECTOR, "a.list-element__title").get_attribute("href")
                    links.append(href)
                except:
                    links.append(None)

            if len(links) >= company_count or len(elems) == 0:
                break

            if elems:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elems[-1])
                time.sleep(2)

        print(f"\n✅ Найдено {len([x for x in links if x])} компаний. Начинаем парсинг...\n")

        # Парсинг деталей
        for idx, url in enumerate(links[:company_count], 1):
            if not url:
                print(f"⚠️ Пропущена компания {idx}: ссылка недоступна")
                all_companies.append({
                    "Название": "Ошибка: ссылка недоступна",
                    "ИНН": "", "КПП": "", "ОГРН": "", "Дата регистрации": "",
                    "Адрес": "", "Руководитель": "", "ОКПО": "", "ОКАТО": "",
                    "ОКТМО": "", "ОКФС": "", "ОКОГУ": "", "ОКОПФ": "",
                    "Ссылка Rusprofile": "",
                    "Аккредитация (Госуслуги)": "⚠️ Не проверялась"
                })
                continue

            print(f"[{idx}/{min(company_count, len(links))}] Парсинг: {url}")
            try:
                data = parse_company_detail(driver, url)
                all_companies.append(data)
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                all_companies.append({
                    "Название": f"Ошибка при парсинге ({url})",
                    "ИНН": "", "КПП": "", "ОГРН": "", "Дата регистрации": "",
                    "Адрес": "", "Руководитель": "", "ОКПО": "", "ОКАТО": "",
                    "ОКТМО": "", "ОКФС": "", "ОКОГУ": "", "ОКОПФ": "",
                    "Ссылка Rusprofile": url,
                    "Аккредитация (Госуслуги)": "⚠️ Не проверялась"
                })

        # Сбор всех ИНН
        inns = [comp["ИНН"] for comp in all_companies if comp["ИНН"]]

        # Проверка аккредитации
        print(f"\n🚀 Проверка {len(inns)} ИНН на https://www.gosuslugi.ru/itorgs...")
        accreditation_statuses = check_accreditation_on_gosuslugi(inns)

        # Добавление статусов
        inn_to_status = dict(zip(inns, accreditation_statuses))
        for comp in all_companies:
            comp["Аккредитация (Госуслуги)"] = inn_to_status.get(comp["ИНН"], "⚠️ Не проверялась")

        # Экспорт в Excel
        df = pd.DataFrame(all_companies)
        output_file = "companies_with_accreditation.xlsx"
        df.to_excel(output_file, index=False, engine='openpyxl')

        print(f"\n✅ Готово! Отчёт сохранён в: {output_file}")
        print(f"📊 Обработано компаний: {len(all_companies)}")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()