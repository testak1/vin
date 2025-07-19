from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import os
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def setup_driver():
    chrome_options = Options()
    
    # Essential options for Render
    chrome_options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Browser mimic settings
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    try:
        service = Service(executable_path="/opt/render/project/.render/chromedriver/linux64/114.0.5735.90/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        return driver
    except Exception as e:
        logging.error(f"Driver setup failed: {e}")
        raise

@app.route('/decode', methods=['GET'])
def decode_vin():
    vin = request.args.get('vin')
    if not vin:
        return jsonify({"error": "VIN parameter is required"}), 400
    
    driver = None
    try:
        driver = setup_driver()
        url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
        driver.get(url)
        time.sleep(5)  # Wait for Cloudflare
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-hover'})
        
        if not table:
            return jsonify({"error": "Equipment table not found"}), 404
        
        equipment = []
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                equipment.append({
                    "code": cols[0].get_text(strip=True),
                    "description": cols[1].get_text(strip=True)
                })
        
        return jsonify(equipment)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
