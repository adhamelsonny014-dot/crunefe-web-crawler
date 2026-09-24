import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from random import uniform
from retrying import retry

# Configuration section - easily update these if Reuters changes their HTML
SELECTORS = {
    # Listing page selectors
    'article_card': '[data-testid="MediaStoryCard"]',
    'article_title': '[data-testid="Heading"]',
    'article_link': 'a',
    'article_time': 'time',
    
    # Article page selectors
    'content_body': 'div.article-body__content__17Yit, div.article-body__content',
    'content_paragraph': 'p',
    
    # Multiple potential image selectors (tried in order)
    'image_selectors': [
        'meta[property="og:image"]',        # OpenGraph image (most reliable)
        'img.article-header__image__3M6cJ',  # New header image class
        'img.Image__image',                  # More generic image class
        'figure img',                         # Fallback to any figure image
        'img[src*="/content/"]'              # Any image with /content/ in URL
    ]
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def log_selector_warning(selector_name):
    print(f"Warning: Selector '{selector_name}' may need updating - Reuters HTML structure might have changed")

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_url(url):
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
    return response

def extract_image_url(soup):
    """Try multiple image selectors in order of priority"""
    for selector in SELECTORS['image_selectors']:
        try:
            img_element = soup.select_one(selector)
            if img_element:
                if selector.startswith('meta'):
                    return img_element['content']  # For OpenGraph meta tags
                elif 'src' in img_element.attrs:
                    return img_element['src']
        except Exception as e:
            continue
    
    log_selector_warning('image_selectors')
    return None

def scrape_article_details(article_url):
    try:
        response = fetch_url(article_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract paragraphs
        paragraphs = []
        content_body = soup.select_one(SELECTORS['content_body'])
        if content_body:
            for p in content_body.find_all(SELECTORS['content_paragraph']):
                paragraph = p.get_text(strip=True)
                if paragraph:
                    paragraphs.append(paragraph)
        
        # Extract image using multiple fallback options
        image_url = extract_image_url(soup)
        
        return {
            'paragraphs': ' '.join(paragraphs) if paragraphs else None,
            'image_url': image_url
        }
    
    except Exception as e:
        print(f"Error scraping article details: {e}")
        return {
            'paragraphs': None,
            'image_url': None
        }

def scrape_reuters_page(url):
    try:
        response = fetch_url(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        for article in soup.select(SELECTORS['article_card']):
            try:
                title_elem = article.select_one(SELECTORS['article_title'])
                if not title_elem:
                    log_selector_warning('article_title')
                    continue
                
                title = title_elem.text.strip()
                
                link_elem = article.find(SELECTORS['article_link'])
                if not link_elem or 'href' not in link_elem.attrs:
                    log_selector_warning('article_link')
                    continue
                
                article_url = "https://www.reuters.com" + link_elem['href']
                
                time_elem = article.select_one(SELECTORS['article_time'])
                time = time_elem['datetime'] if time_elem and 'datetime' in time_elem.attrs else None
                
                article_details = scrape_article_details(article_url)
                
                articles.append({
                    'title': title,
                    'url': article_url,
                    'time': time,
                    'image_url': article_details['image_url'],
                    'content': article_details['paragraphs']
                })
                
                sleep(uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
                
        return articles
    
    except Exception as e:
        print(f"Error scraping page: {e}")
        return []

def mainy(url):
    base_url = url
    all_articles = []
    topics = ["/breakingviews/", "/world/", "/markets/", "/sports/formula1/"]
    i = 0
    for page in range(1, 5):
        print(f"Scraping page {page}...")
        url = f"{base_url}{topics[i]}"
        i += 1
        print(url)
        articles = scrape_reuters_page(url)
        all_articles.extend(articles)
        sleep(uniform(2, 4))
    
    if all_articles:
        df = pd.DataFrame({
            'title': [a['title'] for a in all_articles],
            'url': [a['url'] for a in all_articles],
            'time': [a['time'] for a in all_articles],
            'image_url': [a['image_url'] for a in all_articles],
            'content': [a['content'] for a in all_articles]
        })
        
        df.to_csv('reuters_news_extended.csv', index=False)
        print(f"Successfully saved {len(df)} articles to reuters_news_extended.csv")
    else:
        print("No articles were scraped. Check if the selectors need updating.")

if __name__ == "__main__":
    link = "https://www.reuters.com"
    mainy(link)