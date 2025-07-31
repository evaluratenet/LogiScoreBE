#!/usr/bin/env python3
"""
LogiScore Database Setup Script
This script helps set up the Supabase database and populate it with initial data.
"""

import os
import csv
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseSetup:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ Database connection closed")
    
    def create_schema(self):
        """Create database schema from SQL file"""
        try:
            # Read the schema file
            with open('database/supabase_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute the schema
            self.cursor.execute(schema_sql)
            self.conn.commit()
            print("✅ Database schema created successfully")
        except Exception as e:
            print(f"❌ Failed to create schema: {e}")
            self.conn.rollback()
            raise
    
    def load_freight_forwarders(self):
        """Load freight forwarders from CSV file"""
        try:
            csv_file = 'assets/LogiScore_table_freight_forwarders_data.csv'
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Clean and prepare data
                    name = row['Name'].strip()
                    website = row.get('Website', '').strip()
                    logo_url = row.get('Logo_URL', '').strip()
                    
                    if not name:
                        continue
                    
                    # Insert freight forwarder
                    self.cursor.execute("""
                        INSERT INTO freight_forwarders (id, name, website, logo_url, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO NOTHING
                    """, (
                        str(uuid.uuid4()),
                        name,
                        website if website else None,
                        logo_url if logo_url else None,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
            
            self.conn.commit()
            print("✅ Freight forwarders loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load freight forwarders: {e}")
            self.conn.rollback()
            raise
    
    def create_sample_branches(self):
        """Create sample branches for major freight forwarders"""
        try:
            # Get some major freight forwarders
            self.cursor.execute("""
                SELECT id, name FROM freight_forwarders 
                WHERE name IN ('DHL Supply Chain', 'Kuehne + Nagel', 'DB Schenker', 'CEVA Logistics', 'Bolloré Logistics')
                LIMIT 5
            """)
            
            forwarders = self.cursor.fetchall()
            
            sample_branches = [
                {
                    'name': 'Singapore Branch',
                    'country': 'Singapore',
                    'city': 'Singapore',
                    'address': '123 Marina Bay, Singapore 018956',
                    'contact_email': 'singapore@example.com',
                    'contact_phone': '+65 6123 4567'
                },
                {
                    'name': 'Hong Kong Branch',
                    'country': 'Hong Kong',
                    'city': 'Hong Kong',
                    'address': '456 Central District, Hong Kong',
                    'contact_email': 'hongkong@example.com',
                    'contact_phone': '+852 2345 6789'
                },
                {
                    'name': 'London Branch',
                    'country': 'United Kingdom',
                    'city': 'London',
                    'address': '789 Canary Wharf, London E14 5AB',
                    'contact_email': 'london@example.com',
                    'contact_phone': '+44 20 7123 4567'
                }
            ]
            
            for forwarder in forwarders:
                for branch_data in sample_branches:
                    self.cursor.execute("""
                        INSERT INTO branches (id, freight_forwarder_id, name, country, city, address, contact_email, contact_phone, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        forwarder['id'],
                        f"{forwarder['name']} - {branch_data['name']}",
                        branch_data['country'],
                        branch_data['city'],
                        branch_data['address'],
                        branch_data['contact_email'],
                        branch_data['contact_phone'],
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
            
            self.conn.commit()
            print("✅ Sample branches created successfully")
        except Exception as e:
            print(f"❌ Failed to create sample branches: {e}")
            self.conn.rollback()
            raise
    
    def create_sample_users(self):
        """Create sample users for testing"""
        try:
            sample_users = [
                {
                    'github_id': '12345',
                    'email': 'test@logiscore.net',
                    'username': 'testuser',
                    'full_name': 'Test User',
                    'user_type': 'shipper',
                    'subscription_tier': 'free'
                },
                {
                    'github_id': '67890',
                    'email': 'admin@logiscore.net',
                    'username': 'admin',
                    'full_name': 'Admin User',
                    'user_type': 'admin',
                    'subscription_tier': 'free'
                }
            ]
            
            for user_data in sample_users:
                self.cursor.execute("""
                    INSERT INTO users (id, github_id, email, username, full_name, user_type, subscription_tier, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    user_data['github_id'],
                    user_data['email'],
                    user_data['username'],
                    user_data['full_name'],
                    user_data['user_type'],
                    user_data['subscription_tier'],
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
            
            self.conn.commit()
            print("✅ Sample users created successfully")
        except Exception as e:
            print(f"❌ Failed to create sample users: {e}")
            self.conn.rollback()
            raise
    
    def create_sample_reviews(self):
        """Create sample reviews for testing"""
        try:
            # Get a sample user and branch
            self.cursor.execute("SELECT id FROM users WHERE username = 'testuser' LIMIT 1")
            user = self.cursor.fetchone()
            
            self.cursor.execute("SELECT id, freight_forwarder_id FROM branches LIMIT 3")
            branches = self.cursor.fetchall()
            
            if not user or not branches:
                print("⚠️ No users or branches found for sample reviews")
                return
            
            sample_reviews = [
                {
                    'overall_rating': 5,
                    'responsiveness_rating': 5,
                    'documentation_rating': 4,
                    'communication_rating': 5,
                    'reliability_rating': 5,
                    'cost_effectiveness_rating': 4,
                    'review_text': 'Excellent service! Very responsive and professional team.',
                    'is_anonymous': False,
                    'is_verified': True
                },
                {
                    'overall_rating': 4,
                    'responsiveness_rating': 4,
                    'documentation_rating': 5,
                    'communication_rating': 4,
                    'reliability_rating': 4,
                    'cost_effectiveness_rating': 3,
                    'review_text': 'Good service overall, but could be more cost-effective.',
                    'is_anonymous': True,
                    'is_verified': False
                }
            ]
            
            for branch in branches:
                for review_data in sample_reviews:
                    self.cursor.execute("""
                        INSERT INTO reviews (id, user_id, branch_id, freight_forwarder_id, overall_rating, 
                        responsiveness_rating, documentation_rating, communication_rating, reliability_rating, 
                        cost_effectiveness_rating, review_text, is_anonymous, is_verified, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        user['id'],
                        branch['id'],
                        branch['freight_forwarder_id'],
                        review_data['overall_rating'],
                        review_data['responsiveness_rating'],
                        review_data['documentation_rating'],
                        review_data['communication_rating'],
                        review_data['reliability_rating'],
                        review_data['cost_effectiveness_rating'],
                        review_data['review_text'],
                        review_data['is_anonymous'],
                        review_data['is_verified'],
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
            
            self.conn.commit()
            print("✅ Sample reviews created successfully")
        except Exception as e:
            print(f"❌ Failed to create sample reviews: {e}")
            self.conn.rollback()
            raise
    
    def verify_setup(self):
        """Verify the database setup by counting records"""
        try:
            tables = ['users', 'freight_forwarders', 'branches', 'reviews']
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = self.cursor.fetchone()
                print(f"📊 {table.capitalize()}: {result['count']} records")
            
            print("✅ Database setup verification complete")
        except Exception as e:
            print(f"❌ Failed to verify setup: {e}")
            raise

def main():
    """Main setup function"""
    print("🚀 Starting LogiScore Database Setup...")
    
    try:
        # Initialize database setup
        db_setup = DatabaseSetup()
        
        # Connect to database
        db_setup.connect()
        
        # Create schema
        print("\n📋 Creating database schema...")
        db_setup.create_schema()
        
        # Load freight forwarders
        print("\n📦 Loading freight forwarders...")
        db_setup.load_freight_forwarders()
        
        # Create sample branches
        print("\n🏢 Creating sample branches...")
        db_setup.create_sample_branches()
        
        # Create sample users
        print("\n👥 Creating sample users...")
        db_setup.create_sample_users()
        
        # Create sample reviews
        print("\n⭐ Creating sample reviews...")
        db_setup.create_sample_reviews()
        
        # Verify setup
        print("\n🔍 Verifying database setup...")
        db_setup.verify_setup()
        
        print("\n🎉 Database setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        return False
    finally:
        if 'db_setup' in locals():
            db_setup.disconnect()
    
    return True

if __name__ == "__main__":
    main() 