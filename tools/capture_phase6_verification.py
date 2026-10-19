import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

artifact_dir = r"C:\Users\ASUS\.gemini\antigravity-ide\brain\19458d1c-39b9-48c3-8dc0-b59f77a4adbd"

options = Options()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)

try:
    # 1. Desktop full verification
    driver.set_window_size(1440, 1000)
    driver.get('http://localhost:5173/')
    time.sleep(2)

    # Scroll to Section 5: Weather & Fertilizer
    sec5 = driver.find_element(By.ID, "weather-fertilizer")
    driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", sec5)
    time.sleep(1.5)
    
    sec5_path = os.path.join(artifact_dir, "verified_section_5_weather_fertilizer.png")
    driver.save_screenshot(sec5_path)
    print(f"Saved Section 5 screenshot: {sec5_path}")

    # Scroll slightly down to capture the vegetable garden & fertilizer module
    driver.execute_script("window.scrollBy(0, 420);")
    time.sleep(1)
    split_path = os.path.join(artifact_dir, "verified_weather_cultivation_split.png")
    driver.save_screenshot(split_path)
    print(f"Saved Weather-Cultivation Split screenshot: {split_path}")

    # 2. Open Fertilizer Planner Tool Page
    fertilizer_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Open Fertilizer Planner')]")
    fertilizer_btn.click()
    time.sleep(2)

    fert_page_path = os.path.join(artifact_dir, "verified_fertilizer_page.png")
    driver.save_screenshot(fert_page_path)
    print(f"Saved Fertilizer Page screenshot: {fert_page_path}")

    # Scroll to bottom of Fertilizer Page to see the Practical Cultivation Guidance card
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    fert_guidance_path = os.path.join(artifact_dir, "verified_fertilizer_cultivation_guidance.png")
    driver.save_screenshot(fert_guidance_path)
    print(f"Saved Fertilizer Cultivation Guidance screenshot: {fert_guidance_path}")

    # 3. Mobile Viewport (390x844)
    driver.set_window_size(390, 844)
    # Go back to home
    driver.get('http://localhost:5173/')
    time.sleep(2)

    mobile_hero_path = os.path.join(artifact_dir, "verified_mobile_hero.png")
    driver.save_screenshot(mobile_hero_path)
    print(f"Saved Mobile Hero screenshot: {mobile_hero_path}")

    # Scroll to Section 2 on Mobile
    driver.execute_script("window.scrollBy(0, 750);")
    time.sleep(1)
    mobile_tools_path = os.path.join(artifact_dir, "verified_mobile_tools.png")
    driver.save_screenshot(mobile_tools_path)
    print(f"Saved Mobile Tools screenshot: {mobile_tools_path}")

    # Scroll to Section 4 on Mobile
    driver.execute_script("window.scrollBy(0, 950);")
    time.sleep(1)
    mobile_insights_path = os.path.join(artifact_dir, "verified_mobile_crop_insights.png")
    driver.save_screenshot(mobile_insights_path)
    print(f"Saved Mobile Insights screenshot: {mobile_insights_path}")

finally:
    driver.quit()
print("Verification capture complete!")
