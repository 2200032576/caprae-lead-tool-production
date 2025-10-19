import os
from contextlib import contextmanager
import json
from datetime import datetime

# Try to import mysql.connector first, fallback to pymysql
try:
    import mysql.connector
    from mysql.connector import Error, pooling
    USING_PYMYSQL = False
except ImportError:
    import pymysql
    from pymysql import Error
    USING_PYMYSQL = True
    print("⚠️  Using PyMySQL (fallback connector)")

class Database:
    """MySQL Database Manager with connection pooling for PythonAnywhere"""
    
    def __init__(self):
        """Initialize database connection pool"""
        self.connection_pool = None
        self.init_pool()
    
    def init_pool(self):
        """Create MySQL connection pool"""
        try:
            if USING_PYMYSQL:
                # PyMySQL doesn't have pooling, connections created on demand
                self.connection_pool = None
                print("✅ PyMySQL ready (no pooling)")
            else:
                self.connection_pool = pooling.MySQLConnectionPool(
                    pool_name="lead_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    host=os.getenv('DB_HOST', '2200032576.mysql.pythonanywhere-services.com'),
                    database=os.getenv('DB_NAME', '2200032576$default'),
                    user=os.getenv('DB_USER', '2200032576'),
                    password=os.getenv('DB_PASSWORD', 'YOUR_DB_PASSWORD'),  # Replace with your actual password
                    port=int(os.getenv('DB_PORT', 3306)),
                    autocommit=False
                )
                print("✅ MySQL connection pool created successfully")
        except Error as e:
            print(f"❌ Error creating connection pool: {e}")
            raise
    
    def _create_connection(self):
        """Create a single database connection"""
        if USING_PYMYSQL:
            return pymysql.connect(
                host=os.getenv('DB_HOST', '2200032576.mysql.pythonanywhere-services.com'),
                database=os.getenv('DB_NAME', '2200032576$default'),
                user=os.getenv('DB_USER', '2200032576'),
                password=os.getenv('DB_PASSWORD', 'YOUR_DB_PASSWORD'),  # Replace
                port=int(os.getenv('DB_PORT', 3306)),
                autocommit=False,
                charset='utf8mb4'
            )
        else:
            return self.connection_pool.get_connection()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self._create_connection()
            yield connection
            connection.commit()
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            if connection:
                if USING_PYMYSQL:
                    if connection.open:
                        connection.close()
                else:
                    if connection.is_connected():
                        connection.close()
    
    def initialize_schema(self):
        """Create database tables if they don't exist"""
        schema = """
        CREATE TABLE IF NOT EXISTS leads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_name VARCHAR(255),
            url VARCHAR(512) UNIQUE,
            email VARCHAR(255),
            email_valid BOOLEAN DEFAULT FALSE,
            email_confidence INT DEFAULT 0,
            email_provider VARCHAR(100),
            contact_name VARCHAR(255),
            contact_position VARCHAR(255),
            contact_department VARCHAR(255),
            phone VARCHAR(50),
            phone_valid BOOLEAN DEFAULT FALSE,
            description TEXT,
            industry VARCHAR(100),
            employee_estimate VARCHAR(50),
            revenue_estimate VARCHAR(50),
            domain_age_years DECIMAL(5,2),
            registrar VARCHAR(255),
            tech_stack JSON,
            social_links JSON,
            lead_score INT DEFAULT 0,
            contact_quality DECIMAL(3,2) DEFAULT 0,
            status ENUM('new', 'contacted', 'qualified', 'unqualified', 'converted') DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_company_name (company_name),
            INDEX idx_email (email),
            INDEX idx_lead_score (lead_score),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        CREATE TABLE IF NOT EXISTS scraping_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            query VARCHAR(512),
            source_type ENUM('url', 'search') DEFAULT 'url',
            status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
            leads_found INT DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        CREATE TABLE IF NOT EXISTS email_validation_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT,
            email VARCHAR(255),
            validation_result BOOLEAN,
            confidence_score INT,
            validation_details JSON,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
            INDEX idx_lead_id (lead_id),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        CREATE TABLE IF NOT EXISTS activity_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT,
            activity_type VARCHAR(50),
            description TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
            INDEX idx_lead_id (lead_id),
            INDEX idx_activity_type (activity_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for statement in schema.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            print("✅ Database schema initialized")
    
    # -------------------- CRUD / Lead Methods --------------------
    def insert_lead(self, lead_data):
        """Insert or update a lead"""
        query = """
        INSERT INTO leads (
            company_name, url, email, email_valid, email_confidence, email_provider,
            contact_name, contact_position, contact_department, phone, phone_valid,
            description, industry, employee_estimate, revenue_estimate,
            domain_age_years, registrar, tech_stack, social_links,
            lead_score, contact_quality, status
        ) VALUES (
            %(company_name)s, %(url)s, %(email)s, %(email_valid)s, %(email_confidence)s, 
            %(email_provider)s, %(contact_name)s, %(contact_position)s, %(contact_department)s,
            %(phone)s, %(phone_valid)s, %(description)s, %(industry)s,
            %(employee_estimate)s, %(revenue_estimate)s, %(domain_age_years)s,
            %(registrar)s, %(tech_stack)s, %(social_links)s,
            %(lead_score)s, %(contact_quality)s, %(status)s
        )
        ON DUPLICATE KEY UPDATE
            company_name = VALUES(company_name),
            email = VALUES(email),
            email_valid = VALUES(email_valid),
            email_confidence = VALUES(email_confidence),
            email_provider = VALUES(email_provider),
            contact_name = VALUES(contact_name),
            contact_position = VALUES(contact_position),
            contact_department = VALUES(contact_department),
            phone = VALUES(phone),
            phone_valid = VALUES(phone_valid),
            description = VALUES(description),
            industry = VALUES(industry),
            employee_estimate = VALUES(employee_estimate),
            revenue_estimate = VALUES(revenue_estimate),
            domain_age_years = VALUES(domain_age_years),
            registrar = VALUES(registrar),
            tech_stack = VALUES(tech_stack),
            social_links = VALUES(social_links),
            lead_score = VALUES(lead_score),
            contact_quality = VALUES(contact_quality),
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = lead_data.copy()
        params['tech_stack'] = json.dumps(params.get('tech_stack', []))
        params['social_links'] = json.dumps(params.get('social_links', {}))
        params['status'] = params.get('status', 'new')
        
        for key in ['domain_age_years', 'email_confidence', 'lead_score', 'contact_quality']:
            if params.get(key) is None or params.get(key) == 'Unknown':
                params[key] = None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            lead_id = cursor.lastrowid or self.get_lead_by_url(params['url'])['id']
            return lead_id
    
    def get_lead_by_id(self, lead_id):
        query = "SELECT * FROM leads WHERE id = %s"
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor if USING_PYMYSQL else None, dictionary=not USING_PYMYSQL)
            cursor.execute(query, (lead_id,))
            lead = cursor.fetchone()
            if lead:
                lead['tech_stack'] = json.loads(lead['tech_stack']) if lead['tech_stack'] else []
                lead['social_links'] = json.loads(lead['social_links']) if lead['social_links'] else {}
                lead['created_at'] = lead['created_at'].isoformat() if lead['created_at'] else None
                lead['updated_at'] = lead['updated_at'].isoformat() if lead['updated_at'] else None
            return lead
    
    def get_lead_by_url(self, url):
        query = "SELECT * FROM leads WHERE url = %s"
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor if USING_PYMYSQL else None, dictionary=not USING_PYMYSQL)
            cursor.execute(query, (url,))
            lead = cursor.fetchone()
            if lead:
                lead['tech_stack'] = json.loads(lead['tech_stack']) if lead['tech_stack'] else []
                lead['social_links'] = json.loads(lead['social_links']) if lead['social_links'] else {}
            return lead
    
    def get_all_leads(self, limit=100, offset=0, order_by='lead_score DESC'):
        query = f"SELECT * FROM leads ORDER BY {order_by} LIMIT %s OFFSET %s"
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor if USING_PYMYSQL else None, dictionary=not USING_PYMYSQL)
            cursor.execute(query, (limit, offset))
            leads = cursor.fetchall()
            for lead in leads:
                lead['tech_stack'] = json.loads(lead['tech_stack']) if lead['tech_stack'] else []
                lead['social_links'] = json.loads(lead['social_links']) if lead['social_links'] else {}
                lead['created_at'] = lead['created_at'].isoformat() if lead['created_at'] else None
                lead['updated_at'] = lead['updated_at'].isoformat() if lead['updated_at'] else None
            return leads
    
    def filter_leads(self, filters):
        conditions, params = [], []
        if filters.get('min_score', 0) > 0:
            conditions.append("lead_score >= %s")
            params.append(filters['min_score'])
        if filters.get('industry'):
            conditions.append("industry LIKE %s")
            params.append(f"%{filters['industry']}%")
        if filters.get('has_email'):
            conditions.append("email IS NOT NULL AND email_valid = TRUE")
        if filters.get('status'):
            conditions.append("status = %s")
            params.append(filters['status'])
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM leads WHERE {where_clause} ORDER BY lead_score DESC"
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor if USING_PYMYSQL else None, dictionary=not USING_PYMYSQL)
            cursor.execute(query, tuple(params))
            leads = cursor.fetchall()
            for lead in leads:
                lead['tech_stack'] = json.loads(lead['tech_stack']) if lead['tech_stack'] else []
                lead['social_links'] = json.loads(lead['social_links']) if lead['social_links'] else {}
                lead['created_at'] = lead['created_at'].isoformat() if lead['created_at'] else None
                lead['updated_at'] = lead['updated_at'].isoformat() if lead['updated_at'] else None
            return leads
    
    def update_lead_status(self, lead_id, status):
        query = "UPDATE leads SET status = %s WHERE id = %s"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status, lead_id))
            return cursor.rowcount > 0

    # -------------------- Statistics --------------------
    def get_statistics(self):
        query = """
        SELECT 
            COUNT(*) as total_leads,
            AVG(lead_score) as avg_score,
            SUM(CASE WHEN email_valid = TRUE THEN 1 ELSE 0 END) as valid_emails,
            COUNT(CASE WHEN status = 'qualified' THEN 1 END) as qualified_leads,
            COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads
        FROM leads
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor if USING_PYMYSQL else None, dictionary=not USING_PYMYSQL)
            cursor.execute(query)
            stats = cursor.fetchone()
            cursor.execute("""
                SELECT industry, COUNT(*) as count 
                FROM leads 
                WHERE industry IS NOT NULL
                GROUP BY industry 
                ORDER BY count DESC 
                LIMIT 5
            """)
            top_industries = cursor.fetchall()
            stats['top_industries'] = [{'name': row['industry'], 'count': row['count']} for row in top_industries]
            return stats

    # -------------------- Activity Logging --------------------
    def log_activity(self, lead_id, activity_type, description, metadata=None):
        query = "INSERT INTO activity_log (lead_id, activity_type, description, metadata) VALUES (%s, %s, %s, %s)"
        metadata_json = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (lead_id, activity_type, description, metadata_json))

    # -------------------- Scraping Jobs --------------------
    def create_scraping_job(self, query, source_type):
        sql = "INSERT INTO scraping_jobs (query, source_type, status, started_at) VALUES (%s, %s, 'running', NOW())"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (query, source_type))
            return cursor.lastrowid
    
    def complete_scraping_job(self, job_id, leads_found, error_message=None):
        status = 'failed' if error_message else 'completed'
        sql = "UPDATE scraping_jobs SET status = %s, leads_found = %s, error_message = %s, completed_at = NOW() WHERE id = %s"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (status, leads_found, error_message, job_id))

    # -------------------- Export --------------------
    def export_to_csv(self, filename='leads_export.csv'):
        import csv
        leads = self.get_all_leads(limit=10000)
        if not leads:
            return None
        keys = leads[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(leads)
        return filename

# -------------------- Initialize --------------------
db = Database()
db.initialize_schema()  # Auto-create tables if not exist
