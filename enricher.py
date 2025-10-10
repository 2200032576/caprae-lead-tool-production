import requests
from urllib.parse import urlparse
import whois
from datetime import datetime
import re
from email_finder import EmailFinder
from validator import EmailValidator

class DataEnricher:
    """Enriches lead data with additional information"""
    
    def __init__(self, hunter_api_key=None):
        # Initialize Hunter.io email finder
        self.email_finder = EmailFinder(hunter_api_key)
        self.email_validator = EmailValidator()
        
        self.tech_stack_patterns = {
            'React': ['react.js', 'reactjs', '_next'],
            'Vue': ['vue.js', 'vuejs'],
            'Angular': ['angular', 'ng-'],
            'WordPress': ['wp-content', 'wordpress'],
            'Shopify': ['shopify', 'cdn.shopify'],
            'Salesforce': ['salesforce'],
            'HubSpot': ['hubspot', 'hs-analytics'],
            'Google Analytics': ['google-analytics', 'gtag'],
            'Stripe': ['js.stripe.com'],
            'Intercom': ['intercom'],
            'Zendesk': ['zendesk'],
        }
    
    def is_valid_email(self, email):
        """Check if email is actually valid"""
        if not email or email.upper() in ['N/A', 'NONE', 'NULL', '']:
            return False
        
        # Basic email regex validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_valid_phone(self, phone):
        """Check if phone number is actually valid"""
        if not phone or str(phone).upper() in ['N/A', 'NONE', 'NULL', '']:
            return False
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
        # Check if it has at least 10 digits
        return len(cleaned) >= 10 and cleaned.isdigit()
    
    def enrich_lead(self, lead):
        """Add enrichment data to a lead"""
        url = lead.get('url', '')
        
        if not url:
            return lead
        
        # ===== STEP 1: FIND EMAIL USING HUNTER.IO =====
        print(f"🔍 Searching for emails at {url}...")
        email_data = self.email_finder.get_best_email(url)
        
        if email_data and email_data.get('email'):
            print(f"✅ Found email: {email_data['email']}")
            lead['email'] = email_data['email']
            lead['email_confidence'] = email_data.get('confidence', 0)
            lead['contact_name'] = f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip()
            lead['contact_position'] = email_data.get('position', '')
            lead['contact_department'] = email_data.get('department', '')
            
            # VALIDATE the email using your validator
            lead['email_valid'] = self.email_validator.validate_email(email_data['email'])
            lead['email_score'] = self.email_validator.get_confidence_score(email_data['email'])
            lead['email_provider'] = self.email_validator.get_email_provider(email_data['email'])
        else:
            print(f"❌ No email found for {url}")
            lead['email'] = None
            lead['email_valid'] = False
            lead['email_confidence'] = 0
            lead['email_status'] = 'Not found'
        
        # ===== STEP 2: TECH STACK DETECTION =====
        lead['tech_stack'] = self.detect_tech_stack(url)
        
        # ===== STEP 3: DOMAIN INFO =====
        domain_info = self.get_domain_info(url)
        lead.update(domain_info)
        
        # ===== STEP 4: ESTIMATE COMPANY SIZE & REVENUE =====
        lead['employee_estimate'] = self.estimate_employees(lead)
        lead['revenue_estimate'] = self.estimate_revenue(lead)
        
        # ===== STEP 5: INDUSTRY CLASSIFICATION =====
        lead['industry'] = self.classify_industry(lead)
        
        # ===== STEP 6: VALIDATE PHONE =====
        if not self.is_valid_phone(lead.get('phone')):
            lead['phone_valid'] = False
            lead['phone'] = None
        else:
            lead['phone_valid'] = True
        
        # ===== STEP 7: CONTACT QUALITY SCORE =====
        lead['contact_quality'] = self.rate_contact_quality(lead)
        
        return lead
    
    def detect_tech_stack(self, url):
        """Detect technologies used by the website"""
        try:
            response = requests.get(url, timeout=5)
            html = response.text.lower()
            headers = str(response.headers).lower()
            
            detected = []
            
            for tech, patterns in self.tech_stack_patterns.items():
                for pattern in patterns:
                    if pattern in html or pattern in headers:
                        detected.append(tech)
                        break
            
            return detected if detected else ['Unknown']
        
        except:
            return ['Unknown']
    
    def get_domain_info(self, url):
        """Get WHOIS domain information"""
        try:
            domain = urlparse(url).netloc
            domain = domain.replace('www.', '')
            
            w = whois.whois(domain)
            
            info = {}
            
            # Domain age
            if w.creation_date:
                if isinstance(w.creation_date, list):
                    creation = w.creation_date[0]
                else:
                    creation = w.creation_date
                
                age_days = (datetime.now() - creation).days
                info['domain_age_years'] = round(age_days / 365, 1)
            
            # Registrar
            if w.registrar:
                info['registrar'] = w.registrar
            
            return info
        
        except:
            return {'domain_age_years': 'Unknown'}
    
    def estimate_employees(self, lead):
        """Estimate company size based on signals"""
        score = 0
        
        # Tech stack sophistication
        tech_count = len(lead.get('tech_stack', []))
        if tech_count > 5:
            score += 100
        elif tech_count > 3:
            score += 50
        else:
            score += 10
        
        # Domain age (older = likely larger)
        domain_age = lead.get('domain_age_years', 0)
        if isinstance(domain_age, (int, float)):
            if domain_age > 10:
                score += 100
            elif domain_age > 5:
                score += 50
            else:
                score += 20
        
        # Social media presence
        social_count = len(lead.get('social_links', {}))
        score += social_count * 10
        
        # Categorize
        if score > 150:
            return "100-500"
        elif score > 100:
            return "50-100"
        elif score > 50:
            return "10-50"
        else:
            return "1-10"
    
    def estimate_revenue(self, lead):
        """Estimate annual revenue"""
        employee_range = lead.get('employee_estimate', '1-10')
        
        # Average revenue per employee: $200k (rough industry avg)
        revenue_map = {
            "1-10": "$0-2M",
            "10-50": "$2M-10M",
            "50-100": "$10M-20M",
            "100-500": "$20M-100M"
        }
        
        return revenue_map.get(employee_range, "Unknown")
    
    def classify_industry(self, lead):
        """Classify company industry based on available data"""
        description = lead.get('description', '').lower()
        name = lead.get('company_name', '').lower()
        tech_stack = [t.lower() for t in lead.get('tech_stack', [])]
        
        # Industry keywords
        industries = {
            'SaaS': ['software', 'saas', 'cloud', 'platform', 'api'],
            'E-commerce': ['shop', 'store', 'ecommerce', 'retail', 'shopify'],
            'Finance': ['finance', 'bank', 'payment', 'stripe', 'fintech'],
            'Marketing': ['marketing', 'advertising', 'hubspot', 'seo'],
            'Healthcare': ['health', 'medical', 'care', 'hospital', 'clinic'],
            'Education': ['education', 'learning', 'school', 'university', 'course'],
            'Real Estate': ['real estate', 'property', 'housing', 'realty'],
            'Technology': ['tech', 'software', 'it', 'development', 'react', 'angular']
        }
        
        combined_text = f"{description} {name} {' '.join(tech_stack)}"
        
        for industry, keywords in industries.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return industry
        
        return 'General Business'
    
    def rate_contact_quality(self, lead):
        """Rate the quality of contact information (0-5 stars)"""
        score = 0
        
        # Valid email with confidence scoring
        if lead.get('email_valid'):
            confidence = lead.get('email_confidence', 0)
            if confidence >= 90:
                score += 2.5
            elif confidence >= 70:
                score += 2
            else:
                score += 1.5
        
        # Has contact name
        if lead.get('contact_name') and lead.get('contact_name').strip():
            score += 0.75
        
        # Has position/department
        if lead.get('contact_position') or lead.get('contact_department'):
            score += 0.75
        
        # Valid phone
        if lead.get('phone_valid'):
            score += 1
        
        # Has social links
        social_links = lead.get('social_links', {})
        if social_links and len(social_links) > 0:
            score += 0.5
        
        # Has meaningful description
        description = lead.get('description', '')
        if description and description not in ['No description available', 'N/A', '']:
            score += 0.5
        
        return min(5, round(score, 1))

# Test the enricher
if __name__ == '__main__':
    enricher = DataEnricher()
    
    # Test with a real company
    test_lead = {
        'url': 'https://www.stripe.com',
        'company_name': 'Stripe',
        'description': 'Online payment processing for internet businesses'
    }
    
    print("=" * 50)
    print("TESTING HUNTER.IO INTEGRATION")
    print("=" * 50)
    
    enriched = enricher.enrich_lead(test_lead)
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Company: {enriched.get('company_name')}")
    print(f"Email: {enriched.get('email')}")
    print(f"Email Valid: {enriched.get('email_valid')}")
    print(f"Email Confidence: {enriched.get('email_confidence')}%")
    print(f"Contact Name: {enriched.get('contact_name')}")
    print(f"Contact Position: {enriched.get('contact_position')}")
    print(f"Contact Quality: {enriched.get('contact_quality')}/5")
    print(f"Tech Stack: {enriched.get('tech_stack')}")
    print(f"Industry: {enriched.get('industry')}")
    print("=" * 50)