import requests
from urllib.parse import urlparse
import time
import os

class EmailFinder:
    """Find email addresses using Hunter.io API"""
    
    def __init__(self, api_key=None):
        """
        Initialize EmailFinder with Hunter.io API key
        Get your API key at: https://hunter.io/api
        """
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://api.hunter.io/v2"
        
        if not self.api_key:
            print("⚠️  Warning: No Hunter.io API key provided. Email finding will be limited.")
    
    def _load_api_key(self):
        """Load API key from environment or config.py"""
        # First try environment variable (from .env)
        api_key = os.getenv('HUNTER_API_KEY')
        if api_key:
            return api_key
        
        # Fallback to config.py if it exists
        try:
            from config import HUNTER_API_KEY
            return HUNTER_API_KEY
        except ImportError:
            return None
    
    def get_domain_from_url(self, url):
        """Extract clean domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = domain.replace('www.', '')
        return domain
    
    def domain_search(self, domain, limit=10):
        """
        Search for email addresses associated with a domain
        
        Args:
            domain: Company domain (e.g., 'stripe.com')
            limit: Maximum number of emails to return
        
        Returns:
            dict with 'emails' list and metadata
        """
        if not self.api_key:
            return {'success': False, 'error': 'No API key configured'}
        
        endpoint = f"{self.base_url}/domain-search"
        params = {
            'domain': domain,
            'api_key': self.api_key,
            'limit': limit
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                emails = []
                for email_data in data.get('data', {}).get('emails', []):
                    emails.append({
                        'email': email_data.get('value'),
                        'first_name': email_data.get('first_name'),
                        'last_name': email_data.get('last_name'),
                        'position': email_data.get('position'),
                        'department': email_data.get('department'),
                        'type': email_data.get('type'),
                        'confidence': email_data.get('confidence'),
                        'source': 'hunter.io'
                    })
                
                return {
                    'success': True,
                    'emails': emails,
                    'domain': domain,
                    'organization': data.get('data', {}).get('organization'),
                    'total': len(emails)
                }
            
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            
            elif response.status_code == 429:
                return {'success': False, 'error': 'API rate limit exceeded'}
            
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def email_verifier(self, email):
        """
        Verify if an email address is valid and deliverable
        
        Args:
            email: Email address to verify
        
        Returns:
            dict with verification results
        """
        if not self.api_key:
            return {'success': False, 'error': 'No API key configured'}
        
        endpoint = f"{self.base_url}/email-verifier"
        params = {
            'email': email,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                return {
                    'success': True,
                    'email': email,
                    'valid': result.get('status') in ['valid', 'accept_all'],
                    'status': result.get('status'),
                    'score': result.get('score'),
                    'regexp': result.get('regexp'),
                    'gibberish': result.get('gibberish'),
                    'disposable': result.get('disposable'),
                    'webmail': result.get('webmail'),
                    'mx_records': result.get('mx_records'),
                    'smtp_server': result.get('smtp_server'),
                    'smtp_check': result.get('smtp_check'),
                    'accept_all': result.get('accept_all'),
                    'block': result.get('block'),
                    'source': 'hunter.io'
                }
            
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def email_finder(self, domain, first_name=None, last_name=None):
        """
        Find email address for a specific person at a domain
        
        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
        
        Returns:
            dict with found email and confidence score
        """
        if not self.api_key:
            return {'success': False, 'error': 'No API key configured'}
        
        endpoint = f"{self.base_url}/email-finder"
        params = {
            'domain': domain,
            'api_key': self.api_key
        }
        
        if first_name:
            params['first_name'] = first_name
        if last_name:
            params['last_name'] = last_name
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                return {
                    'success': True,
                    'email': result.get('email'),
                    'score': result.get('score'),
                    'first_name': result.get('first_name'),
                    'last_name': result.get('last_name'),
                    'position': result.get('position'),
                    'department': result.get('department'),
                    'confidence': result.get('confidence'),
                    'source': 'hunter.io'
                }
            
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_account_info(self):
        """
        Get API account information and usage limits
        
        Returns:
            dict with account details
        """
        if not self.api_key:
            return {'success': False, 'error': 'No API key configured'}
        
        endpoint = f"{self.base_url}/account"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                account = data.get('data', {})
                
                return {
                    'success': True,
                    'email': account.get('email'),
                    'first_name': account.get('first_name'),
                    'last_name': account.get('last_name'),
                    'plan_name': account.get('plan_name'),
                    'requests_available': account.get('requests', {}).get('available'),
                    'requests_used': account.get('requests', {}).get('used'),
                    'reset_date': account.get('reset_date')
                }
            
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_emails_for_lead(self, lead_data):
        """
        Convenience method to find emails for a lead
        
        Args:
            lead_data: dict with 'url' or 'domain' field
        
        Returns:
            list of email addresses with metadata
        """
        # Get domain
        domain = lead_data.get('domain')
        if not domain and lead_data.get('url'):
            domain = self.get_domain_from_url(lead_data['url'])
        
        if not domain:
            return []
        
        # Search for emails at this domain
        result = self.domain_search(domain, limit=5)
        
        if result.get('success'):
            return result.get('emails', [])
        
        return []


# Example usage
if __name__ == "__main__":
    finder = EmailFinder()
    
    # Test API connection
    print("Testing Hunter.io API connection...\n")
    
    # Check account info
    account = finder.get_account_info()
    if account.get('success'):
        print(f"✅ API Key Valid!")
        print(f"Plan: {account.get('plan_name')}")
        print(f"Requests Available: {account.get('requests_available')}")
        print(f"Requests Used: {account.get('requests_used')}")
    else:
        print(f"❌ API Error: {account.get('error')}")
    
    print("\n" + "="*50 + "\n")
    
    # Test domain search
    test_domain = "stripe.com"
    print(f"Searching for emails at {test_domain}...\n")
    
    result = finder.domain_search(test_domain, limit=3)
    
    if result.get('success'):
        print(f"Found {result.get('total')} emails:")
        for email_data in result.get('emails', []):
            print(f"  📧 {email_data['email']}")
            if email_data.get('first_name'):
                print(f"     Name: {email_data['first_name']} {email_data['last_name']}")
            if email_data.get('position'):
                print(f"     Position: {email_data['position']}")
            print(f"     Confidence: {email_data['confidence']}%")
            print()
    else:
        print(f"❌ Error: {result.get('error')}")