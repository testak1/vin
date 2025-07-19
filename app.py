from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    """Configure and return a Chrome WebDriver with stealth settings"""
    chrome_options = Options()
    
    # Path configuration for Render
    chrome_bin = os.getenv("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    # Essential Chrome options for Render
    chrome_options.binary_location = chrome_bin
    chrome_options.add_argument("--headless=new")  # New headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Mimic regular browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(
            executable_path=chromedriver_path,
            options=chrome_options
        )
        
        # Apply stealth configurations
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        
        logger.info("Chrome WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise Exception(f"Driver setup failed: {str(e)}")

@app.route('/decode', methods=['GET'])
def decode_vin():
    """Endpoint to decode VIN and return equipment data"""
    vin = request.args.get('vin')
    if not vin or len(vin) < 10:  # Basic validation
        return jsonify({"error": "Valid VIN parameter is required"}), 400
    
    driver = None
    try:
        logger.info(f"Processing VIN: {vin}")
        driver = setup_driver()
        url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
        
        logger.info(f"Fetching URL: {url}")
        driver.get(url)
        
        # Wait for Cloudflare and page load
        logger.info("Waiting for page load...")
        time.sleep(10)  # Increased wait for Cloudflare
        
        # Verify page loaded
        if "VIN Decoder" not in driver.title:
            logger.warning("Page title doesn't match expected VIN Decoder")
            return jsonify({"error": "Failed to load VIN decoder page"}), 502
        
        # Parse page content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-hover'})
        
        if not table:
            logger.warning("Equipment table not found in page source")
            return jsonify({"error": "Equipment table not found"}), 404
        
        # Extract equipment data
        equipment = []
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                equipment.append({
                    "code": cols[0].get_text(strip=True),
                    "description": cols[1].get_text(strip=True)
                })
        
        logger.info(f"Successfully decoded VIN, found {len(equipment)} items")
        return jsonify({
            "vin": vin,
            "equipment": equipment
        })
        
    except Exception as e:
        logger.error(f"Error processing VIN {vin}: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "VIN decoding failed"
        }), 500
        
    finally:
        if driver:
            logger.info("Quitting WebDriver...")
            driver.quit()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "message": "Service is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
