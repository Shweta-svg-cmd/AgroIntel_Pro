# database.py - Complete Database Operations
import sqlite3
import json
from datetime import datetime, timedelta
import random
import os
import hashlib

# ==================== DATABASE CONFIGURATION ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "agrointel.db")

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

# ==================== DATABASE INITIALIZATION ====================

def init_database():
    """Initialize all database tables with updated schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table with complete registration fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            full_name TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            postal_code TEXT,
            farm_name TEXT,
            farm_size REAL,
            farm_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create fields table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            field_id TEXT UNIQUE NOT NULL,
            field_name TEXT NOT NULL,
            crop_type TEXT,
            acres REAL,
            yield_tons REAL,
            soil_health INTEGER,
            planting_date DATE,
            harvest_date DATE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create machinery table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machinery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            machine_id TEXT UNIQUE NOT NULL,
            machine_name TEXT NOT NULL,
            machine_type TEXT,
            operating_hours INTEGER,
            fuel_level INTEGER,
            status TEXT,
            last_maintenance DATE,
            next_maintenance DATE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create weather table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            field_id TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            rainfall REAL,
            wind_speed REAL,
            weather_condition TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create soil_analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soil_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            field_id TEXT NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ph REAL,
            nitrogen REAL,
            phosphorus REAL,
            potassium REAL,
            organic_matter REAL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create compliance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            compliance_type TEXT,
            status TEXT,
            score INTEGER,
            deadline DATE,
            submitted_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create ai_recommendations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recommendation_type TEXT,
            title TEXT,
            field_id TEXT,
            recommendation_text TEXT,
            confidence INTEGER,
            roi TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            implemented BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at: {DB_PATH}")

# ==================== USER FUNCTIONS ====================

def create_user(username, password, email, phone, full_name, address, city, state, country, postal_code, farm_name, farm_size, farm_type):
    """Create a new user with all registration details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if username already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Username already exists"
    
    # Check if email already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Email already registered"
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Insert new user
    cursor.execute('''
        INSERT INTO users (
            username, password, email, phone, full_name, address, 
            city, state, country, postal_code, farm_name, farm_size, farm_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, hashed_password, email, phone, full_name, address, 
          city, state, country, postal_code, farm_name, farm_size, farm_type))
    
    conn.commit()
    conn.close()
    return True, "Account created successfully!"

def get_user(username, password):
    """Authenticate user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    cursor.execute('''
        SELECT id, username, email, phone, full_name, address, city, state, 
               country, postal_code, farm_name, farm_size, farm_type
        FROM users 
        WHERE username = ? AND password = ?
    ''', (username, hashed_password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3] or '',
            'full_name': user[4],
            'address': user[5] or '',
            'city': user[6] or '',
            'state': user[7] or '',
            'country': user[8] or '',
            'postal_code': user[9] or '',
            'farm_name': user[10] or '',
            'farm_size': user[11] or 0,
            'farm_type': user[12] or ''
        }
    return None

def get_user_by_id(user_id):
    """Get user details by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, email, phone, full_name, address, city, state, 
               country, postal_code, farm_name, farm_size, farm_type
        FROM users 
        WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3] or '',
            'full_name': user[4],
            'address': user[5] or '',
            'city': user[6] or '',
            'state': user[7] or '',
            'country': user[8] or '',
            'postal_code': user[9] or '',
            'farm_name': user[10] or '',
            'farm_size': user[11] or 0,
            'farm_type': user[12] or ''
        }
    return None

def update_user_profile(user_id, email, phone, full_name, address, city, state, country, postal_code, farm_name, farm_size, farm_type):
    """Update user profile"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET email = ?, phone = ?, full_name = ?, address = ?, city = ?,
            state = ?, country = ?, postal_code = ?, farm_name = ?,
            farm_size = ?, farm_type = ?
        WHERE id = ?
    ''', (email, phone, full_name, address, city, state, country, postal_code,
          farm_name, farm_size, farm_type, user_id))
    
    conn.commit()
    conn.close()
    return True

# ==================== FIELD FUNCTIONS ====================

def add_field(user_id, field_id, field_name, crop_type, acres, yield_tons, soil_health, planting_date=None, harvest_date=None):
    """Add a new field"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO fields (user_id, field_id, field_name, crop_type, acres, yield_tons, soil_health, planting_date, harvest_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, field_id, field_name, crop_type, acres, yield_tons, soil_health, planting_date, harvest_date))
        conn.commit()
        conn.close()
        return True, "Field added successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Field ID already exists. Please use a unique ID."

def get_fields(user_id):
    """Get all fields for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT field_id, field_name, crop_type, acres, yield_tons, soil_health
        FROM fields
        WHERE user_id = ?
        ORDER BY field_name
    ''', (user_id,))
    
    fields = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': f[0],
            'name': f[1],
            'crop': f[2],
            'acres': f[3],
            'yield': f[4],
            'soil_health': f[5]
        }
        for f in fields
    ]

def delete_field(user_id, field_id):
    """Delete a field"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fields WHERE user_id = ? AND field_id = ?", (user_id, field_id))
    conn.commit()
    conn.close()
    return True

# ==================== MACHINERY FUNCTIONS ====================

def add_machinery(user_id, machine_id, machine_name, machine_type, operating_hours, fuel_level, status, last_maintenance=None, next_maintenance=None):
    """Add new machinery"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO machinery (user_id, machine_id, machine_name, machine_type, operating_hours, fuel_level, status, last_maintenance, next_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, machine_id, machine_name, machine_type, operating_hours, fuel_level, status, last_maintenance, next_maintenance))
        conn.commit()
        conn.close()
        return True, "Machinery added successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Machine ID already exists. Please use a unique ID."

def get_machinery(user_id):
    """Get all machinery for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT machine_id, machine_name, machine_type, operating_hours, fuel_level, status
        FROM machinery
        WHERE user_id = ?
        ORDER BY machine_name
    ''', (user_id,))
    
    machinery = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': m[0],
            'name': m[1],
            'type': m[2],
            'hours': m[3],
            'fuel': m[4],
            'status': m[5]
        }
        for m in machinery
    ]

def delete_machinery(user_id, machine_id):
    """Delete machinery"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM machinery WHERE user_id = ? AND machine_id = ?", (user_id, machine_id))
    conn.commit()
    conn.close()
    return True

# ==================== SOIL ANALYSIS FUNCTIONS ====================

def add_soil_analysis(user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter):
    """Add soil analysis data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO soil_analysis (user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter))
    
    conn.commit()
    conn.close()
    return True

def get_soil_analysis(user_id):
    """Get soil analysis data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT field_id, ph, nitrogen, phosphorus, potassium, organic_matter
        FROM soil_analysis
        WHERE user_id = ?
    ''', (user_id,))
    
    soil = cursor.fetchall()
    conn.close()
    
    return [
        {
            'field': s[0],
            'pH': s[1],
            'nitrogen': s[2],
            'phosphorus': s[3],
            'potassium': s[4],
            'organic_matter': s[5]
        }
        for s in soil
    ]

# ==================== WEATHER FUNCTIONS ====================

def get_weather(user_id, days=7):
    """Get recent weather data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT recorded_at, temperature, humidity, rainfall, wind_speed
        FROM weather
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT ?
    ''', (user_id, days))
    
    weather = cursor.fetchall()
    conn.close()
    
    return [
        {
            'date': w[0],
            'temperature': w[1],
            'humidity': w[2],
            'rainfall': w[3],
            'wind_speed': w[4]
        }
        for w in weather
    ]

# ==================== COMPLIANCE FUNCTIONS ====================

def get_compliance(user_id):
    """Get compliance data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT compliance_type, status, score, deadline, notes
        FROM compliance
        WHERE user_id = ?
    ''', (user_id,))
    
    compliance = cursor.fetchall()
    conn.close()
    
    return [
        {
            'type': c[0],
            'status': c[1],
            'score': c[2],
            'deadline': c[3],
            'notes': c[4]
        }
        for c in compliance
    ]

# ==================== AI RECOMMENDATIONS FUNCTIONS ====================

def get_ai_recommendations(user_id):
    """Get AI recommendations"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT recommendation_type, title, field_id, recommendation_text, confidence, roi
        FROM ai_recommendations
        WHERE user_id = ? AND implemented = FALSE
        ORDER BY confidence DESC
    ''', (user_id,))
    
    recommendations = cursor.fetchall()
    conn.close()
    
    return [
        {
            'type': r[0],
            'title': r[1],
            'field': r[2],
            'recommendation': r[3],
            'confidence': r[4],
            'roi': r[5]
        }
        for r in recommendations
    ]

# ==================== SUMMARY FUNCTIONS ====================

def get_total_acres(user_id):
    """Get total acres for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT SUM(acres) 
        FROM fields
        WHERE user_id = ?
    ''', (user_id,))
    
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_avg_yield(user_id):
    """Get average yield for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT AVG(yield_tons) 
        FROM fields
        WHERE user_id = ?
    ''', (user_id,))
    
    avg = cursor.fetchone()[0] or 0
    conn.close()
    return round(avg, 1)

def get_active_machinery_count(user_id):
    """Get count of active machinery"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM machinery
        WHERE user_id = ? AND status = 'Active'
    ''', (user_id,))
    
    count = cursor.fetchone()[0] or 0
    conn.close()
    return count

def get_total_machinery_count(user_id):
    """Get total machinery count"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM machinery
        WHERE user_id = ?
    ''', (user_id,))
    
    count = cursor.fetchone()[0] or 0
    conn.close()
    return count

def get_compliance_score(user_id):
    """Get overall compliance score"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT AVG(score) 
        FROM compliance
        WHERE user_id = ?
    ''', (user_id,))
    
    score = cursor.fetchone()[0] or 0
    conn.close()
    return round(score)

# ==================== INSERT SAMPLE DATA ====================

def insert_sample_data():
    """Insert sample data for testing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'demo'")
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Sample data already exists")
        conn.close()
        return
    
    # Create demo user
    hashed_password = hash_password('demo123')
    cursor.execute('''
        INSERT INTO users (username, password, email, phone, full_name, address, city, state, country, postal_code, farm_name, farm_size, farm_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('demo', hashed_password, 'demo@agrointel.com', '+1 234 567 8900', 
          'Demo Farmer', '123 Farm Road', 'Farmville', 'CA', 'USA', '12345',
          'Demo Farm', 510, 'Mixed'))
    user_id = cursor.lastrowid
    print("✅ Created demo user")
    
    # Insert sample fields
    fields = [
        ('F1', 'North Field', 'Winter Wheat', 120, 5.2, 85),
        ('F2', 'East Field', 'Corn', 95, 7.8, 72),
        ('F3', 'South Field', 'Soybeans', 150, 3.4, 91),
        ('F4', 'West Field', 'Barley', 80, 4.1, 68),
        ('F5', 'Central Field', 'Potatoes', 65, 12.3, 79),
    ]
    for field in fields:
        cursor.execute('''
            INSERT INTO fields (user_id, field_id, field_name, crop_type, acres, yield_tons, soil_health)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, *field))
    print(f"✅ Added {len(fields)} fields")
    
    # Insert sample machinery
    machinery = [
        ('M1', 'John Deere 6215R', 'Tractor', 1245, 78, 'Active'),
        ('M2', 'John Deere S780', 'Combine', 876, 45, 'Active'),
        ('M3', 'Hagie STS 12', 'Sprayer', 543, 62, 'Maintenance'),
        ('M4', 'John Deere 2623', 'Plow', 234, 0, 'Active'),
    ]
    for machine in machinery:
        cursor.execute('''
            INSERT INTO machinery (user_id, machine_id, machine_name, machine_type, operating_hours, fuel_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, *machine))
    print(f"✅ Added {len(machinery)} machinery")
    
    # Insert sample soil analysis
    soil = [
        ('F1', 6.2, 45.5, 32.1, 210.5, 3.8),
        ('F2', 5.8, 28.3, 18.7, 145.2, 2.5),
        ('F3', 6.5, 52.1, 38.4, 280.3, 4.2),
        ('F4', 6.0, 22.4, 16.2, 120.8, 2.1),
        ('F5', 5.5, 35.6, 25.3, 180.5, 3.1),
    ]
    for s in soil:
        cursor.execute('''
            INSERT INTO soil_analysis (user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, *s))
    print(f"✅ Added {len(soil)} soil analysis records")
    
    # Insert sample weather data (last 7 days)
    for i in range(7, 0, -1):
        date = datetime.now() - timedelta(days=i)
        cursor.execute('''
            INSERT INTO weather (user_id, field_id, recorded_at, temperature, humidity, rainfall, wind_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 'F1', date.strftime('%Y-%m-%d %H:%M:%S'),
            round(22 + 3 * (i/7) + random.uniform(-2, 2), 1),
            round(65 + 10 * (i/7) + random.uniform(-5, 5), 1),
            round(max(0, 5 + random.uniform(-3, 8)), 1),
            round(10 + 5 * (i/7) + random.uniform(-3, 3), 1)
        ))
    print("✅ Added 7 weather records")
    
    # Insert sample compliance data
    compliance = [
        ('CAP Compliance', 'Complete', 92, '2026-12-31', 'All CAP requirements fulfilled'),
        ('Environmental Regulations', 'In Progress', 78, '2026-10-15', 'Awaiting inspection'),
        ('Subsidy Applications', 'Pending', 85, '2026-09-15', 'Application submitted'),
    ]
    for c in compliance:
        cursor.execute('''
            INSERT INTO compliance (user_id, compliance_type, status, score, deadline, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, *c))
    print(f"✅ Added {len(compliance)} compliance records")
    
    # Insert sample AI recommendations
    ai = [
        ('crop_rotation', 'Crop Rotation', 'F1', 'Switch to Winter Wheat for 11% ROI increase', 87, '+11%'),
        ('maintenance', 'Predictive Maintenance', 'M1', 'Hydraulic service needed in 12 operating hours', 93, 'Preventive'),
        ('irrigation', 'Irrigation Alert', 'F5', 'Optimal irrigation window: 08:15 - 11:00', 91, 'Savings'),
        ('fertilizer', 'Fertilizer Optimization', 'F3', 'Apply 48kg/ha Nitrogen for +7% ROI', 85, '+7%'),
    ]
    for a in ai:
        cursor.execute('''
            INSERT INTO ai_recommendations (user_id, recommendation_type, title, field_id, recommendation_text, confidence, roi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, *a))
    print(f"✅ Added {len(ai)} AI recommendations")
    
    conn.commit()
    conn.close()
    print("\n✅ All sample data inserted successfully!")
    print("🔑 Login with: demo / demo123")

# ==================== MAIN ====================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clear":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_recommendations")
            cursor.execute("DELETE FROM compliance")
            cursor.execute("DELETE FROM soil_analysis")
            cursor.execute("DELETE FROM weather")
            cursor.execute("DELETE FROM machinery")
            cursor.execute("DELETE FROM fields")
            cursor.execute("DELETE FROM users")
            conn.commit()
            conn.close()
            print("✅ All data cleared!")
            sys.exit(0)
        elif sys.argv[1] == "--removedemo":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = 'demo'")
            conn.commit()
            conn.close()
            print("✅ Demo data removed!")
            sys.exit(0)
        elif sys.argv[1] == "--sample":
            init_database()
            insert_sample_data()
            sys.exit(0)
    
    print("🌾 AgroIntel Database Setup")
    print("="*40)
    print("Commands:")
    print("  python database.py --sample    # Initialize with sample data")
    print("  python database.py --clear     # Clear all data")
    print("  python database.py --removedemo # Remove demo data only")
    print("="*40)
    
    # Initialize if no command
    init_database()