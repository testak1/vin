import os
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import time
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
]

app = Flask(__name__)

# EU-Based VIN Decoders
DECODERS = {
    'Audi': {
        'url': 'https://vag-codes.info/vin-decoder/audi',
        'method': 'post',
        'params': {'vin': ''},
        'parse': lambda soup: {
            'Model': soup.find('th', text='Model').find_next('td').text.strip(),
            'Year': soup.find('th', text='Year').find_next('td').text.strip(),
            'Engine': soup.find('th', text='Engine').find_next('td').text.strip()
        }
    },
    'BMW': {
        'url': 'https://bimmer.work/',
        'method': 'get',
        'params': {'vin': ''},
        'parse': lambda soup: {
            'Model': soup.select_one('.vehicle-model').text.strip(),
            'Production Date': soup.select_one('.production-date').text.strip(),
            'Options': [opt.text.strip() for opt in soup.select('.option-code')]
        }
    },
    'Mercedes': {
        'url': 'https://www.mercedes-benz.de/passengercars/mercedes-benz-cars/vin-decoder.html',
        'method': 'post',
        'params': {'identifier': ''},
        'parse': lambda soup: {
            'Model': soup.find('div', class_='model-name').text.strip(),
            'VIN Data': {dt.text.strip(): dd.text.strip() 
                        for dt, dd in zip(
                            soup.select('dl.data-table dt'),
                            soup.select('dl.data-table dd')
                        )}
        }
    },
    'Volkswagen': {
        'url': 'https://vag-codes.info/vin-decoder/vw',
        'method': 'post',
        'params': {'vin': ''},
        'parse': lambda soup: {
            'Model': soup.find('th', text='Model').find_next('td').text.strip(),
            'Engine Code': soup.find('th', text='Engine Code').find_next('td').text.strip()
        }
    },
    'Volvo': {
        'url': 'https://www.volvocars.com/eu/own/owner-info/vin-decoder',
        'method': 'post',
        'params': {'vin': ''},
        'parse': lambda soup: {
            'Vehicle Details': soup.select_one('.vehicle-details').text.strip(),
            'Specifications': [li.text.strip() for li in soup.select('.specs-list li')]
        }
    }
}

def scrape_vin(manufacturer, vin):
    decoder = DECODERS[manufacturer]
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        if decoder['method'] == 'post':
            response = requests.post(
                decoder['url'],
                data={**decoder['params'], 'vin': vin},
                headers=headers,
                timeout=20
            )
        else:
            response = requests.get(
                decoder['url'],
                params={**decoder['params'], 'vin': vin},
                headers=headers,
                timeout=20
            )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return {
                'success': True,
                'data': decoder['parse'](soup),
                'source': decoder['url']
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'source': decoder['url']
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'source': decoder['url']
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == 'POST':
        vin = request.form['vin'].strip()
        if len(vin) == 17:
            for manufacturer in DECODERS:
                results[manufacturer] = scrape_vin(manufacturer, vin)
                time.sleep(random.uniform(1, 3))  # Be polite
    
    return render_template('index.html', results=results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
