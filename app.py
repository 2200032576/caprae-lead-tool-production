from dotenv import load_dotenv
import os

# Load environment variables FIRST, before any other imports
load_dotenv()

from flask import Flask, render_template, request, jsonify, send_file
from scraper import CompanyScraper
from enricher import DataEnricher
from validator import EmailValidator
from database import db
import pandas as pd
from datetime import datetime
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize components
scraper = CompanyScraper()
enricher = DataEnricher()
validator = EmailValidator()

# Initialize database schema on startup
try:
    db.initialize_schema()
    print("✅ Application started successfully")
except Exception as e:
    print(f"❌ Failed to initialize database: {e}")
    raise

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
        source_type = data.get('type', 'url')
        
        if not query:
            return jsonify({'error': 'Please provide a URL or search query'}), 400
        
        # Create scraping job
        job_id = db.create_scraping_job(query, source_type)
        
        # Run scraping in background
        thread = Thread(target=background_scrape, args=(job_id, query, source_type))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Scraping started',
            'job_id': job_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def background_scrape(job_id, query, source_type):
    """Background task for scraping and enriching leads"""
    try:
        # Scrape basic company data
        raw_leads = scraper.scrape(query, source_type)
        
        leads_count = 0
        
        # Enrich each lead with additional data
        for lead in raw_leads:
            try:
                # Add tech stack and company info
                enriched = enricher.enrich_lead(lead)
                
                # Validate email if present
                if enriched.get('email'):
                    enriched['email_valid'] = validator.validate_email(enriched['email'])
                    enriched['email_confidence'] = validator.get_confidence_score(enriched['email'])
                    enriched['email_provider'] = validator.get_email_provider(enriched['email'])
                
                # Calculate lead score (0-100)
                enriched['lead_score'] = calculate_lead_score(enriched)
                
                # Save to database
                lead_id = db.insert_lead(enriched)
                
                # Log activity
                db.log_activity(
                    lead_id, 
                    'lead_created', 
                    f"Lead scraped from {source_type}: {query}",
                    {'source': source_type, 'query': query}
                )
                
                leads_count += 1
                
            except Exception as e:
                print(f"Error enriching lead: {e}")
                continue
        
        # Mark job as completed
        db.complete_scraping_job(job_id, leads_count)
        
    except Exception as e:
        # Mark job as failed
        db.complete_scraping_job(job_id, 0, str(e))

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all stored leads with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        offset = (page - 1) * per_page
        
        leads = db.get_all_leads(limit=per_page, offset=offset)
        
        return jsonify({
            'success': True,
            'leads': leads,
            'page': page,
            'per_page': per_page,
            'total': len(leads)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get a single lead by ID"""
    try:
        lead = db.get_lead_by_id(lead_id)
        
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404
        
        return jsonify({
            'success': True,
            'lead': lead
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    """Update a lead"""
    try:
        data = request.json
        status = data.get('status')
        
        if status:
            success = db.update_lead_status(lead_id, status)
            if success:
                db.log_activity(
                    lead_id,
                    'status_changed',
                    f"Status changed to {status}"
                )
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Lead not found'}), 404
        
        return jsonify({'error': 'No updates provided'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    """Delete a lead"""
    try:
        query = "DELETE FROM leads WHERE id = %s"
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (lead_id,))
            
            if cursor.rowcount > 0:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Lead not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/filter', methods=['POST'])
def filter_leads():
    """Filter leads by criteria"""
    try:
        filters = request.json
        leads = db.filter_leads(filters)
        
        return jsonify({
            'success': True,
            'leads': leads,
            'count': len(leads)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_leads():
    """Export leads to CSV"""
    try:
        # Create data folder if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/leads_export_{timestamp}.csv'
        
        # Export from database
        result = db.export_to_csv(filename)
        
        if not result:
            return jsonify({'error': 'No leads to export'}), 400
        
        return send_file(
            filename, 
            as_attachment=True, 
            download_name=f'leads_{timestamp}.csv',
            mimetype='text/csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = db.get_statistics()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_leads': stats.get('total_leads', 0),
                'avg_score': round(float(stats.get('avg_score', 0)), 1),
                'valid_emails': stats.get('valid_emails', 0),
                'qualified_leads': stats.get('qualified_leads', 0),
                'converted_leads': stats.get('converted_leads', 0),
                'top_industries': stats.get('top_industries', [])
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a scraping job"""
    try:
        query = "SELECT * FROM scraping_jobs WHERE id = %s"
        
        with db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Convert datetime to string
            if job.get('started_at'):
                job['started_at'] = job['started_at'].isoformat()
            if job.get('completed_at'):
                job['completed_at'] = job['completed_at'].isoformat()
            if job.get('created_at'):
                job['created_at'] = job['created_at'].isoformat()
            
            return jsonify({
                'success': True,
                'job': job
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activities/<int:lead_id>', methods=['GET'])
def get_lead_activities(lead_id):
    """Get activity log for a lead"""
    try:
        query = """
        SELECT * FROM activity_log 
        WHERE lead_id = %s 
        ORDER BY created_at DESC
        """
        
        with db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (lead_id,))
            activities = cursor.fetchall()
            
            # Convert datetime to string
            for activity in activities:
                if activity.get('created_at'):
                    activity['created_at'] = activity['created_at'].isoformat()
            
            return jsonify({
                'success': True,
                'activities': activities
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_lead_score(lead):
    """Calculate lead quality score (0-100)"""
    score = 50  # Base score
    
    # Has valid email? +20
    if lead.get('email_valid'):
        score += 20
    
    # Email confidence bonus
    confidence = lead.get('email_confidence', 0)
    if confidence >= 90:
        score += 10
    elif confidence >= 70:
        score += 5
    
    # Has phone? +10
    if lead.get('phone_valid'):
        score += 10
    
    # Has revenue estimate? +10
    if lead.get('revenue_estimate') and lead.get('revenue_estimate') != 'Unknown':
        score += 10
    
    # Tech stack identified? +5
    if lead.get('tech_stack') and len(lead.get('tech_stack', [])) > 0:
        score += 5
    
    # Employee count known? +5
    if lead.get('employee_estimate'):
        score += 5
    
    # Has contact name? +5
    if lead.get('contact_name') and lead.get('contact_name').strip():
        score += 5
    
    # Has social links? +5
    social_links = lead.get('social_links', {})
    if isinstance(social_links, dict) and len(social_links) > 0:
        score += 5
    
    # Cap at 100
    return min(score, 100)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n🚀 Starting Flask application on {host}:{port}")
    print(f"📊 Debug mode: {debug}")
    print(f"🔗 Health check: http://localhost:{port}/health\n")
    
    app.run(debug=debug, host=host, port=port)