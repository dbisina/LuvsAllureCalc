'''
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

app = Flask(__name__)
CORS(app)

# Global variable to store the latest exchange rate
current_rate = None
last_update_time = None




def get_chrome_options():
    """Configure Chrome options for cloud deployment"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return chrome_options


def get_usd_to_naira_rate():
    """Scrape USD to Naira rate with error handling and retries"""
    global current_rate, last_update_time
    
    url = 'https://abokiforex.app/dollar-to-naira-black-market'
    max_retries = 15
    
    for attempt in range(max_retries):
        try:
            chrome_options = get_chrome_options()
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
            
            # Add these lines to properly load the page
            driver.get(url)  # Add this line
            driver.implicitly_wait(20)  # Add this line
            
            usd_sell_element = driver.find_element(By.XPATH, '//*[@id="usdSell"]')
            usd_sell_text = usd_sell_element.text
            
            if not usd_sell_text:
                raise ValueError("USD Sell rate is empty")
            
            rate = float(usd_sell_text.replace(',', ''))
            current_rate = rate
            last_update_time = time.time()
            
            # Save to file as backup
            with open('last_rate.json', 'w') as f:
                json.dump({
                    'rate': rate,
                    'timestamp': last_update_time
                }, f)
            
            return rate
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                # If all retries failed, try to load from backup file
                try:
                    with open('last_rate.json', 'r') as f:
                        data = json.load(f)
                        if time.time() - data['timestamp'] < 86400:  # Use backup if less than 24h old
                            return data['rate']
                except:
                    raise Exception("Failed to get exchange rate")
            time.sleep(2 ** attempt)  # Exponential backoff
        finally:
            try:
                driver.quit()
            except:
                pass

def calculate_selling_cost(acquisition_cost):
    """Calculate selling cost based on acquisition cost"""
    x = acquisition_cost
    y = 2 * x + (0.35 * x + x)
    return y / 2

# Setup scheduler to update exchange rate every hour
scheduler = BackgroundScheduler()
scheduler.add_job(func=get_usd_to_naira_rate, trigger="interval", hours=1)
scheduler.start()


@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/calculate', methods=['POST'])
def calculate_price():
    try:
        data = request.get_json()
        cost_price = float(data['costPrice'])
        shipping_cost = float(data['shippingCost'])
        
        # Validate inputs
        if cost_price < 0 or shipping_cost < 0:
            return jsonify({'error': 'Costs cannot be negative'}), 400
        
        # Get current exchange rate
        try:
            if current_rate is None:
                rate = get_usd_to_naira_rate()
            else:
                # Use cached rate if less than 1 hour old
                if time.time() - last_update_time < 3600:
                    rate = current_rate
                else:
                    rate = get_usd_to_naira_rate()
        except Exception as e:
            return jsonify({'error': f'Failed to get exchange rate: {str(e)}'}), 500
        
        # Calculate prices
        acquisition_cost = cost_price + shipping_cost
        selling_cost_usd = calculate_selling_cost(acquisition_cost)
        selling_cost_naira = (selling_cost_usd * rate) + 5000
        
        return jsonify({
            'usdPrice': round(selling_cost_usd, 2),
            'nairaPrice': round(selling_cost_naira, 2),
            'exchangeRate': rate
        })
        
    except KeyError:
        return jsonify({'error': 'Missing required fields'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid number format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


if __name__ == '__main__':
    # Initialize exchange rate on startup
    try:
        get_usd_to_naira_rate()
    except:
        print("Failed to get initial exchange rate")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 
'''

# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_usd_to_naira_rate():
    url = 'https://abokiforex.app/dollar-to-naira-black-market'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        usd_sell_element = soup.find(id='usdSell')
        
        if not usd_sell_element:
            raise ValueError("Could not find USD Sell rate element")
            
        usd_sell_text = usd_sell_element.text.strip()
        
        if not usd_sell_text:
            raise ValueError("USD Sell rate is empty")
            
        return float(usd_sell_text.replace(',', ''))
        
    except requests.RequestException as e:
        raise Exception(f"Error making request: {str(e)}")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def selling_cost_calculator(acquisition_cost):
    x = acquisition_cost
    y = 2 * x + (0.35 * x + x)
    selling_cost = y / 2
    return selling_cost

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@app.route('/api/get-rate', methods=['GET'])
def get_rate():
    try:
        rate = get_usd_to_naira_rate()
        return jsonify({
            'success': True,
            'rate': rate
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        if not data or 'cost_price' not in data or 'shipping_cost' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: cost_price and shipping_cost'
            }), 400
            
        cost_price = float(data['cost_price'])
        shipping_cost = float(data['shipping_cost'])
        
        acquisition_cost = cost_price + shipping_cost
        selling_cost_usd = selling_cost_calculator(acquisition_cost)
        
        try:
            usd_to_naira_rate = get_usd_to_naira_rate()
            selling_cost_naira = (selling_cost_usd * usd_to_naira_rate) + 5000
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error getting exchange rate: {str(e)}'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'selling_price_usd': round(selling_cost_usd, 2),
                'selling_price_naira': round(selling_cost_naira, 2),
                'exchange_rate': usd_to_naira_rate
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)