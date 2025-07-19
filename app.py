from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time
import os

app = Flask(__name__)

def setup_driver():
    chrome_options = Options()
    
    # Configuration for Render
    chrome_options.binary_location = os.getenv("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    # Initialize driver
    driver = webdriver.Chrome(
        executable_path=os.getenv("CHROMEDRIVER_PATH"),
        options=chrome_options
    )
    
    # Apply stealth settings
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

def get_vin_equipment(vin):
    driver = setup_driver()
    try:
        url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
        driver.get(url)
        
        # Wait for Cloudflare check and page load
        time.sleep(10)
        
        # Get page source and parse
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-hover'})
        
        if not table:
            return {"error": "Equipment table not found"}
        
        equipment = []
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                code = cols[0].get_text(strip=True)
                description = cols[1].get_text(strip=True)
                equipment.append({
                    "code": code,
                    "description": description
                })
        
        return equipment
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

@app.route('/decode', methods=['GET'])
def decode_vin():
    vin = request.args.get('vin')
    if not vin:
        return jsonify({"error": "VIN parameter is required"}), 400
    
    result = get_vin_equipment(vin)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
