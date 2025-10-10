import requests
from urllib.parse import urlparse
from config import HUNTER_API_KEY

class EmailFinder:
    """Find and enrich email data using Hunter.io API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or HUNTER_API_KEY
        self.base_url = "https://api.hunter.io/v2"
    
    def find_emails(self, url, limit=5):
        """
        Find email addresses for a company domain
        
        Args:
            url: Company website URL
            limit: Max number of emails to return (default 5)
        
        Returns:
            List of email dictionaries with details
        """
        if not self.api_key:
            return {
                'success': False,
                'emails': [],
                'error': 'No API key configured'
            }
        
        # Extract domain from URL
        domain = urlparse(url).netloc.replace('www.', '')
        
        try:
            endpoint = f"{self.base_url}/domain-search"
            params = {
                'domain': domain,
                'api_key': self.api_key,
                'limit': limit
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('data'):
                emails_data = data['data'].get('emails', [])
                
                # Format email data
                formatted_emails = []
                for email_obj in emails_data:
                    formatted_emails.append({
                        'email': email_obj.get('value'),
                        'confidence': email_obj.get('confidence'),
                        'first_name': email_obj.get('first_name'),
                        'last_name': email_obj.get('last_name'),
                        'position': email_obj.get('position'),
                        'department': email_obj.get('department'),
                        'type': email_obj.get('type')
                    })
                
                return {
                    'success': True,
                    'emails': formatted_emails,
                    'total_found': len(formatted_emails)
                }
            else:
                error_msg = data.get('errors', [{}])[0].get('details', 'Unknown error')
                return {
                    'success': False,
                    'emails': [],
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'emails': [],
                'error': str(e)
            }
    
    def get_best_email(self, url):
        """
        Get the single best email for a domain (highest confidence)
        
        Returns:
            dict with best email or None
        """
        result = self.find_emails(url, limit=1)
        
        if result['success'] and result['emails']:
            return result['emails'][0]
        
        return None