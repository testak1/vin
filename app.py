from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_vin_equipment(vin):
    base_url = "https://www.vindecoderz.com/EN/check-lookup/"
    url = base_url + vin
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
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
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.route('/decode', methods=['GET'])
def decode_vin():
    vin = request.args.get('vin')
    if not vin:
        return jsonify({"error": "VIN parameter is required"}), 400
    
    result = get_vin_equipment(vin)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
