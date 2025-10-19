#!/usr/bin/env python3
"""
Setup script for Lead Generation Tool
Initializes database and creates necessary tables
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            db_name = os.getenv('DB_NAME', 'lead_generation')
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{db_name}' created successfully (or already exists)")
            
            cursor.close()
            connection.close()
            return True
    
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def initialize_tables():
    """Initialize all database tables"""
    try:
        from database import db
        db.initialize_schema()
        print("✅ Database tables initialized successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error initializing tables: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'lead_generation'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Connected to MySQL Server version {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"✅ Connected to database: {record[0]}")
            
            cursor.close()
            connection.close()
            return True
    
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

def create_sample_data():
    """Create sample lead data for testing"""
    try:
        from database import db
        
        sample_leads = [
            {
                'company_name': 'Stripe',
                'url': 'https://www.stripe.com',
                'email': 'info@stripe.com',
                'email_valid': True,
                'email_confidence': 85,
                'email_provider': 'Business Email',
                'contact_name': 'Patrick Collison',
                'contact_position': 'CEO',
                'contact_department': 'Executive',
                'phone': '+1-888-926-2289',
                'phone_valid': True,
                'description': 'Online payment processing for internet businesses',
                'industry': 'Finance',
                'employee_estimate': '100-500',
                'revenue_estimate': '$20M-100M',
                'domain_age_years': 15.5,
                'registrar': 'MarkMonitor Inc.',
                'tech_stack': ['React', 'Ruby', 'JavaScript'],
                'social_links': {
                    'twitter': 'https://twitter.com/stripe',
                    'linkedin': 'https://linkedin.com/company/stripe'
                },
                'lead_score': 95,
                'contact_quality': 4.5,
                'status': 'new'
            },
            {
                'company_name': 'HubSpot',
                'url': 'https://www.hubspot.com',
                'email': 'contact@hubspot.com',
                'email_valid': True,
                'email_confidence': 90,
                'email_provider': 'Business Email',
                'contact_name': 'Yamini Rangan',
                'contact_position': 'CEO',
                'contact_department': 'Executive',
                'phone': '+1-888-482-7768',
                'phone_valid': True,
                'description': 'Inbound marketing, sales, and service software',
                'industry': 'Marketing',
                'employee_estimate': '100-500',
                'revenue_estimate': '$20M-100M',
                'domain_age_years': 18.0,
                'registrar': 'MarkMonitor Inc.',
                'tech_stack': ['JavaScript', 'React', 'Node.js'],
                'social_links': {
                    'twitter': 'https://twitter.com/hubspot',
                    'linkedin': 'https://linkedin.com/company/hubspot'
                },
                'lead_score': 92,
                'contact_quality': 4.8,
                'status': 'new'
            }
        ]
        
        for lead in sample_leads:
            db.insert_lead(lead)
            print(f"✅ Created sample lead: {lead['company_name']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def main():
    """Main setup function"""
    print("\n" + "=" * 60)
    print("LEAD GENERATION TOOL - DATABASE SETUP")
    print("=" * 60 + "\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("📝 Creating .env from .env.example...")
        
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env file created. Please update it with your configuration.")
            print("\n⚠️  You must configure your database credentials in .env before continuing!\n")
            sys.exit(1)
        else:
            print("❌ .env.example not found. Please create .env manually.")
            sys.exit(1)
    
    # Step 1: Test MySQL connection
    print("Step 1: Testing MySQL connection...")
    if not test_connection():
        # Try creating database if connection fails
        print("\nAttempting to create database...")
        if not create_database():
            print("\n❌ Setup failed. Please check your MySQL credentials in .env")
            sys.exit(1)
    
    # Step 2: Create database
    print("\nStep 2: Creating database...")
    create_database()
    
    # Step 3: Initialize tables
    print("\nStep 3: Initializing database tables...")
    if not initialize_tables():
        print("\n❌ Failed to initialize tables")
        sys.exit(1)
    
    # Step 4: Create sample data (optional)
    print("\nStep 4: Create sample data? (y/n): ", end='')
    response = input().strip().lower()
    if response == 'y':
        create_sample_data()
    
    # Step 5: Create necessary directories
    print("\nStep 5: Creating necessary directories...")
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    print("✅ Directories created")
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYou can now run the application with:")
    print("  python app.py")
    print("\nOr with Gunicorn (production):")
    print("  gunicorn -w 4 -b 0.0.0.0:5000 app:app")
    print("\n")

if __name__ == '__main__':
    main()