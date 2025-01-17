from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

# Global variable to store the latest exchange rate
current_rate = None
last_update_time = None

def get_chrome_options():
    """Configure Chrome options for cloud deployment"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-setuid-sandbox')
    return chrome_options

def get_usd_to_naira_rate():
    """Scrape USD to Naira rate with error handling and retries"""
    global current_rate, last_update_time
    
    url = 'https://abokiforex.app/dollar-to-naira-black-market'
    max_retries = 3
    
    for attempt in range(max_retries):
        driver = None
        try:
            chrome_options = get_chrome_options()
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("Chrome instance created successfully")
            driver.get(url)
            print(f"Page loaded: {url}")
            
            driver.implicitly_wait(20)
            usd_sell_element = driver.find_element(By.XPATH, '//*[@id="usdSell"]')
            usd_sell_text = usd_sell_element.text
            
            print(f"Found USD sell rate: {usd_sell_text}")
            
            if not usd_sell_text:
                raise ValueError("USD Sell rate is empty")
            
            rate = float(usd_sell_text.replace(',', ''))
            current_rate = rate
            last_update_time = time.time()
            
            return rate
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                max_retries = max_retries - 1  # Return a fallback rate if all attempts fail
            time.sleep(2 ** attempt)
        finally:
            if driver:
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