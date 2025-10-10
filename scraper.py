import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

class CompanyScraper:
    """Scrapes company information from websites"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape(self, query, source_type='url'):
        """
        Main scraping function
        query: URL to scrape or search term
        source_type: 'url' or 'search'
        """
        if source_type == 'url':
            return [self.scrape_single_url(query)]
        else:
            # For search, we'll use a simple Google search approach
            return self.search_and_scrape(query)
    
    def scrape_single_url(self, url):
        """Scrape a single company website"""
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company data
            lead = {
                'url': url,
                'company_name': self.extract_company_name(soup, url),
                'email': self.extract_email(soup),
                'phone': self.extract_phone(soup),
                'description': self.extract_description(soup),
                'social_links': self.extract_social_links(soup, url)
            }
            
            return lead
        
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'company_name': self.get_domain_name(url)
            }
    
    def search_and_scrape(self, search_term, limit=5):
        """Search for companies and scrape them"""
        # For demo: simulate finding companies
        # In production, you'd use Google Custom Search API or similar
        demo_urls = [
            'https://www.salesforce.com',
            'https://www.hubspot.com',
            'https://www.zendesk.com'
        ]
        
        results = []
        for url in demo_urls[:limit]:
            results.append(self.scrape_single_url(url))
        
        return results
    
    def extract_company_name(self, soup, url):
        """Extract company name from page"""
        # Try multiple methods
        
        # Method 1: Meta tags
        og_title = soup.find('meta', property='og:site_name')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        # Method 2: Title tag
        title = soup.find('title')
        if title:
            # Clean up title
            name = title.text.split('|')[0].split('-')[0].strip()
            return name
        
        # Method 3: Domain name
        return self.get_domain_name(url)
    
    def extract_email(self, soup):
        """Find email addresses on the page"""
        # Search in text
        text = soup.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Filter out common non-contact emails
            filtered = [e for e in emails if not any(
                x in e.lower() for x in ['example.com', 'domain.com', 'yoursite']
            )]
            return filtered[0] if filtered else None
        
        # Check mailto links
        mailto = soup.find('a', href=re.compile(r'^mailto:'))
        if mailto:
            return mailto['href'].replace('mailto:', '')
        
        return None
    
    def extract_phone(self, soup):
        """Find phone numbers on the page"""
        text = soup.get_text()
        
        # US phone patterns
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def extract_description(self, soup):
        """Extract company description"""
        # Try meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'][:200]
        
        # Try OG description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'][:200]
        
        # Try first paragraph
        paragraphs = soup.find_all('p')
        if paragraphs:
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 50:
                    return text[:200]
        
        return "No description available"
    
    def extract_social_links(self, soup, base_url):
        """Find social media links"""
        social_platforms = {
            'linkedin': 'linkedin.com',
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'instagram': 'instagram.com'
        }
        
        social_links = {}
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Make absolute URL
            full_url = urljoin(base_url, href)
            
            for platform, domain in social_platforms.items():
                if domain in full_url:
                    social_links[platform] = full_url
                    break
        
        return social_links
    
    def get_domain_name(self, url):
        """Extract clean domain name"""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. and .com
        domain = domain.replace('www.', '').split('.')[0]
        return domain.title()

# Test the scraper
if __name__ == '__main__':
    scraper = CompanyScraper()
    result = scraper.scrape_single_url('https://www.stripe.com')
    print(result)