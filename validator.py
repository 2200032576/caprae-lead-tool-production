import re
import dns.resolver
import socket

class EmailValidator:
    """Validates email addresses and checks deliverability"""
    
    def __init__(self):
        self.disposable_domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'throwaway.email', 'mailinator.com'
        ]
        
        self.common_typos = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'outlok.com': 'outlook.com'
        }
    
    def validate_email(self, email):
        """
        Comprehensive email validation
        Returns: True if valid, False otherwise
        """
        if not email:
            return False
        
        # Step 1: Format validation
        if not self.check_format(email):
            return False
        
        # Step 2: Check for disposable emails
        if self.is_disposable(email):
            return False
        
        # Step 3: DNS/MX record check
        if not self.check_mx_record(email):
            return False
        
        return True
    
    def check_format(self, email):
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_disposable(self, email):
        """Check if email is from a disposable email provider"""
        domain = email.split('@')[1] if '@' in email else ''
        return domain in self.disposable_domains
    
    def check_mx_record(self, email):
        """Check if domain has valid MX records"""
        try:
            domain = email.split('@')[1]
            
            # Check for common typos
            if domain in self.common_typos:
                return False
            
            # Try to get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            # If DNS check fails, assume valid (network issues, etc.)
            return True
    
    def get_confidence_score(self, email):
        """
        Calculate confidence score for email validity (0-100)
        """
        if not email:
            return 0
        
        score = 0
        
        # Format check (30 points)
        if self.check_format(email):
            score += 30
        
        # Not disposable (20 points)
        if not self.is_disposable(email):
            score += 20
        
        # Has MX record (30 points)
        if self.check_mx_record(email):
            score += 30
        
        # Domain quality (20 points)
        domain = email.split('@')[1] if '@' in email else ''
        
        # Common business domains
        business_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']
        if domain not in business_domains:
            score += 10  # Likely a business email
        
        # Has professional structure (10 points)
        if self.is_professional_format(email):
            score += 10
        
        return min(100, score)
    
    def is_professional_format(self, email):
        """Check if email follows professional naming patterns"""
        local_part = email.split('@')[0] if '@' in email else ''
        
        # Professional patterns: firstname.lastname, first.last, flast, etc.
        professional_patterns = [
            r'^[a-z]+\.[a-z]+$',  # john.doe
            r'^[a-z]+[a-z]$',     # jdoe
            r'^[a-z]+_[a-z]+$',   # john_doe
        ]
        
        local_lower = local_part.lower()
        
        for pattern in professional_patterns:
            if re.match(pattern, local_lower):
                return True
        
        return False
    
    def suggest_correction(self, email):
        """Suggest correction for common email typos"""
        if not email or '@' not in email:
            return None
        
        domain = email.split('@')[1]
        local = email.split('@')[0]
        
        if domain in self.common_typos:
            corrected_domain = self.common_typos[domain]
            return f"{local}@{corrected_domain}"
        
        return None
    
    def get_email_provider(self, email):
        """Identify email provider"""
        if not email or '@' not in email:
            return 'Unknown'
        
        domain = email.split('@')[1].lower()
        
        providers = {
            'gmail.com': 'Gmail',
            'outlook.com': 'Outlook',
            'hotmail.com': 'Hotmail',
            'yahoo.com': 'Yahoo',
            'icloud.com': 'iCloud',
            'protonmail.com': 'ProtonMail'
        }
        
        return providers.get(domain, 'Business Email')

# Test the validator
if __name__ == '__main__':
    validator = EmailValidator()
    
    test_emails = [
        'john.doe@company.com',
        'invalid@invalid',
        'test@tempmail.com',
        'contact@stripe.com'
    ]
    
    for email in test_emails:
        is_valid = validator.validate_email(email)
        confidence = validator.get_confidence_score(email)
        print(f"{email}: Valid={is_valid}, Confidence={confidence}%")