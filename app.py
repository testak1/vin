import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import time
import random

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
    app.run()
