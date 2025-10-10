from flask import Flask, render_template, request, jsonify, send_file
from scraper import CompanyScraper
from enricher import DataEnricher
from validator import EmailValidator
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Initialize components
scraper = CompanyScraper()
enricher = DataEnricher()
validator = EmailValidator()

# Store leads in memory
leads_database = []

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_leads():
    """Scrape leads from a given URL or search query"""
    try:
        data = request.json
        query = data.get('query', '')
        source_type = data.get('type', 'url')  # url or search
        
        if not query:
            return jsonify({'error': 'Please provide a URL or search query'}), 400
        
        # Scrape basic company data
        raw_leads = scraper.scrape(query, source_type)
        
        # Enrich each lead with additional data
        enriched_leads = []
        for lead in raw_leads:
            # Add tech stack and company info
            enriched = enricher.enrich_lead(lead)
            
            # Validate email if present
            if enriched.get('email'):
                enriched['email_valid'] = validator.validate_email(enriched['email'])
                enriched['email_confidence'] = validator.get_confidence_score(enriched['email'])
            
            # Calculate lead score (0-100)
            enriched['lead_score'] = calculate_lead_score(enriched)
            
            enriched_leads.append(enriched)
        
        # Add to database
        leads_database.extend(enriched_leads)
        
        return jsonify({
            'success': True,
            'leads': enriched_leads,
            'count': len(enriched_leads)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all stored leads"""
    # Sort by lead score (highest first)
    sorted_leads = sorted(leads_database, key=lambda x: x.get('lead_score', 0), reverse=True)
    return jsonify({'leads': sorted_leads, 'total': len(sorted_leads)})

@app.route('/api/leads/filter', methods=['POST'])
def filter_leads():
    """Filter leads by criteria"""
    try:
        filters = request.json
        min_score = filters.get('min_score', 0)
        industry = filters.get('industry', '')
        has_email = filters.get('has_email', False)
        
        filtered = leads_database
        
        # Apply filters
        if min_score > 0:
            filtered = [l for l in filtered if l.get('lead_score', 0) >= min_score]
        
        if industry:
            filtered = [l for l in filtered if industry.lower() in l.get('industry', '').lower()]
        
        if has_email:
            filtered = [l for l in filtered if l.get('email') and l.get('email_valid')]
        
        return jsonify({'leads': filtered, 'count': len(filtered)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_leads():
    """Export leads to CSV"""
    try:
        if not leads_database:
            return jsonify({'error': 'No leads to export'}), 400
        
        # Create DataFrame
        df = pd.DataFrame(leads_database)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/leads_export_{timestamp}.csv'
        
        # Create data folder if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        df.to_csv(filename, index=False)
        
        return send_file(filename, as_attachment=True, download_name=f'leads_{timestamp}.csv')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    if not leads_database:
        return jsonify({
            'total_leads': 0,
            'avg_score': 0,
            'valid_emails': 0,
            'top_industries': []
        })
    
    total = len(leads_database)
    avg_score = sum(l.get('lead_score', 0) for l in leads_database) / total
    valid_emails = sum(1 for l in leads_database if l.get('email_valid'))
    
    # Count industries
    industries = {}
    for lead in leads_database:
        ind = lead.get('industry', 'Unknown')
        industries[ind] = industries.get(ind, 0) + 1
    
    top_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total_leads': total,
        'avg_score': round(avg_score, 1),
        'valid_emails': valid_emails,
        'top_industries': [{'name': k, 'count': v} for k, v in top_industries]
    })

def calculate_lead_score(lead):
    """Calculate lead quality score (0-100)"""
    score = 50  # Base score
    
    # Has valid email? +20
    if lead.get('email_valid'):
        score += 20
    
    # Has phone? +10
    if lead.get('phone'):
        score += 10
    
    # Has revenue estimate? +10
    if lead.get('revenue_estimate'):
        score += 10
    
    # Tech stack identified? +5
    if lead.get('tech_stack') and len(lead.get('tech_stack', [])) > 0:
        score += 5
    
    # Employee count known? +5
    if lead.get('employee_count'):
        score += 5
    
    # Cap at 100
    return min(score, 100)

if __name__ == '__main__':
    app.run(debug=True, port=5000)