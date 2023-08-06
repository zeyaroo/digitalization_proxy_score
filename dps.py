import argparse
import requests
import json
from bs4 import BeautifulSoup
from collections import Counter
from selenium import webdriver
import time
import csv
from selenium.webdriver.chrome.options import Options
import os
import re
from retry import retry

@retry(tries=20, delay=2, backoff=2)
def make_request(uri, headers, params):
    response = requests.get(uri, headers=headers, params=params)
    response_json = response.json()
    return response_json

def main(company, start_year, end_year, url):
    subscription_key = "BING-KEY"
    uri = 'https://api.bing.microsoft.com/v7.0/search'
    headers = {
        'Ocp-Apim-Subscription-Key' : subscription_key,
    }
    # Keywords to search for in the page content
    keywords = [
        "digital transformation",
        "digital innovation",
        "digital strategy",
        "big data",
        "industry 4.0",
        "artificial intelligence",
        "cloud",
        "Internet of Things",
        "quantum computing",
        "digital twins",
        "digitalization",
        "digital technology",
        "information technology",
        "incubator",
        "accelerator",
        "crowdsourcer",
        "venture capitalist",
        "data lakes",
        "cloud computing",
        "virtual reality",
        "augmented reality",
        "wearable",
        "digital twins",
        "blockchain",
        "quantum computing",
        "machine learning",
        "neural networks",
        "deep learning",
        "algorithms",
        "digital channels",
        "data analytics",
        "digital marketing",
        "simulation",
        "AI-driven drug discovery",
        "digital patient monitoring",
        "data ecosystem",
        "real-time tracking",
        "connected patient platforms",
        "business intelligence",
        "smart factory",
        "lab of the future",
        "machine intelligence",
        "automation",
        "robotics",
        "natural language processing",
        "analyze data",
        "decentralized trials",
        "real-world data",
        "virtual assistance",
        "remote monitoring",
    ]
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.javascript": 2})


    driver = webdriver.Chrome('chromedriver', options=chrome_options)

    processed_urls = set()
    yearly_keyword_counts = []
    api_requests = 0

    company_folder = company.replace(' ', '_')
    if not os.path.exists(company_folder):
        os.makedirs(company_folder)

    for year in range(start_year, end_year + 1):
        keyword_counter = Counter(dict.fromkeys(keywords, 0))

        for keyword in keywords:
            search_query = f'"{keyword}"'
            if url:
                search_query = f"{search_query} site:{url}"

            params = {
                'q': search_query,
                'count': 50,
                'offset': 0,
                'mkt': 'en-US',
                'freshness': f'{year}-01-01..{year}-12-31',
            }
            while True:
                try:
                    response_json = make_request(uri, headers, params)
                    print(params)
                    print(response_json)
                    api_requests += 1
                    if 'webPages' in response_json and 'value' in response_json['webPages']:
                        for web_page in response_json['webPages']['value']:
                            if web_page['url'] not in processed_urls:
                                processed_urls.add(web_page['url'])

                                driver.get(web_page['url'])
                                time.sleep(3) 
                                soup = BeautifulSoup(driver.page_source, 'html.parser')
                                content = soup.get_text(separator=' ').lower()

                                for keyword in keywords:
                                    count = content.count(keyword.lower())
                                    keyword_counter[keyword] += len(re.findall(keyword, content))
                                
                                with open(os.path.join(company_folder, f'webpage_content_{year}.txt'), 'a') as file:
                                    file.write(content + '\n')
                    else:
                        break
                    params['offset'] += 50
                
                except Exception as e:
                    print(f"Request failed with exception {e}. Retrying...")
                    continue

        yearly_keyword_counts.append((year, keyword_counter))

    driver.quit()

    print(f'Total API requests made: {api_requests}')

    with open(os.path.join(company_folder, f"{company.replace(' ', '_')}_counts.csv"), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Year", "Keyword", "Count"])
        for year, keyword_counter in yearly_keyword_counts:
            for keyword, count in sorted(keyword_counter.items()):
                writer.writerow([year, keyword, count])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bing Search API query.')
    parser.add_argument('company', type=str, help='Company name')
    parser.add_argument('start_year', type=int, help='Start year')
    parser.add_argument('end_year', type=int, help='End year')
    parser.add_argument('--url', type=str, default=None, help='URL to target in the search')

    args = parser.parse_args()

    main(args.company, args.start_year, args.end_year, args.url)
