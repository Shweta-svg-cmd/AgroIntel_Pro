# app.py - Complete AgroIntel Application
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import database as db

# ==================== INITIALIZE SESSION STATE ====================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AgroIntel - Universal Agricultural Intelligence Platform",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
def apply_custom_css():
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #1B5E20, #2E7D32, #43A047);
            padding: 1.5rem 2rem;
            border-radius: 15px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
        .main-header p { margin: 0; opacity: 0.9; font-size: 1rem; }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border-left: 5px solid #2E7D32;
            transition: transform 0.2s;
            height: 100%;
        }
        .metric-card:hover { transform: translateY(-2px); }
        .metric-value { font-size: 2.2rem; font-weight: bold; color: #1B5E20; margin: 0.3rem 0; }
        .metric-label { font-size: 0.85rem; color: #666; font-weight: 500; }
        .metric-sub { font-size: 0.8rem; color: #888; }
        
        .section-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #1B5E20;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #E8F5E9;
        }
        
        .ai-card {
            background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #81C784;
            height: 100%;
            transition: transform 0.2s;
        }
        .ai-card:hover { transform: translateY(-2px); }
        .ai-card h4 { color: #1B5E20; margin-top: 0; }
        .ai-card .confidence {
            background: #2E7D32;
            color: white;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-badge {
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .status-badge.success { background: #E8F5E9; color: #2E7D32; }
        .status-badge.warning { background: #FFF3E0; color: #E65100; }
        .status-badge.info { background: #E3F2FD; color: #1565C0; }
        .status-badge.danger { background: #FFEBEE; color: #C62828; }
        
        .sidebar-brand { text-align: center; padding: 1rem 0; }
        .sidebar-brand h2 { color: #1B5E20; margin: 0; }
        .sidebar-brand p { color: #666; font-size: 0.8rem; }
        
        .field-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border: 1px solid #E8E8E8;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .field-card .field-name { font-weight: 600; color: #1B5E20; }
        .crop-tag {
            background: #E8F5E9;
            padding: 0.2rem 0.8rem;
            border-radius: 12px;
            font-size: 0.75rem;
            color: #2E7D32;
        }
        
        .welcome-container { text-align: center; padding: 4rem 2rem; }
        .welcome-container .emoji { font-size: 4rem; }
        .welcome-container h1 { color: #1B5E20; margin: 1rem 0; }
        .welcome-container p { font-size: 1.2rem; color: #666; }
        .welcome-container .sub-text { color: #888; font-size: 0.9rem; }
        
        .data-entry-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }
        .data-entry-card h3 {
            color: #1B5E20;
            margin-top: 0;
        }
        .stButton button {
            background: #2E7D32;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton button:hover {
            background: #1B5E20;
            transform: scale(1.02);
        }
        .stButton button:active {
            transform: scale(0.98);
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# ==================== REGISTRATION PAGE ====================

def show_registration():
    """Show registration form"""
    st.markdown("""
        <div class="main-header">
            <h1>📝 Create Your Account</h1>
            <p>Join AgroIntel and start managing your farm intelligently</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("registration_form"):
        st.markdown("### 👤 Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username *", placeholder="Choose a unique username")
            full_name = st.text_input("Full Name *", placeholder="John Doe")
            email = st.text_input("Email *", placeholder="john@example.com")
            phone = st.text_input("Phone Number", placeholder="+1 234 567 8900")
            
        with col2:
            password = st.text_input("Password *", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password *", type="password")
        
        st.markdown("---")
        st.markdown("### 📍 Address Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            address = st.text_area("Address", placeholder="Street address", height=80)
        with col2:
            city = st.text_input("City", placeholder="Your city")
            state = st.text_input("State/Province", placeholder="Your state")
        with col3:
            postal_code = st.text_input("Postal Code", placeholder="12345")
            country = st.text_input("Country", placeholder="Your country")
        
        st.markdown("---")
        st.markdown("### 🚜 Farm Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            farm_name = st.text_input("Farm Name", placeholder="Sunset Farm")
        with col2:
            farm_size = st.number_input("Farm Size (acres)", min_value=0.0, step=1.0, help="Total farm area in acres")
        with col3:
            farm_type = st.selectbox("Farm Type", ["Select...", "Crop", "Livestock", "Mixed", "Organic", "Dairy", "Poultry", "Other"])
        
        st.markdown("---")
        st.markdown("*Required fields")
        
        submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
        
        if submitted:
            errors = []
            
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters")
            if not full_name:
                errors.append("Full name is required")
            if not email or '@' not in email:
                errors.append("Invalid email address")
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters")
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                success, message = db.create_user(
                    username=username,
                    password=password,
                    email=email,
                    phone=phone,
                    full_name=full_name,
                    address=address,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code,
                    farm_name=farm_name,
                    farm_size=farm_size,
                    farm_type=farm_type
                )
                
                if success:
                    st.success("✅ Account created successfully! Please login.")
                    st.balloons()
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

# ==================== PROFILE PAGE ====================

def show_profile():
    """Show user profile"""
    user = db.get_user_by_id(st.session_state.user_id)
    
    if not user:
        st.error("User not found")
        return
    
    st.markdown(f"""
        <div class="main-header">
            <h1>👤 My Profile</h1>
            <p>Welcome back, {user['full_name']}!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display profile info in cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="data-entry-card">
                <h3>👤 Personal Information</h3>
        """, unsafe_allow_html=True)
        st.write(f"**Full Name:** {user['full_name']}")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Phone:** {user['phone'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="data-entry-card">
                <h3>📍 Address Information</h3>
        """, unsafe_allow_html=True)
        st.write(f"**Address:** {user['address'] or 'Not set'}")
        st.write(f"**City:** {user['city'] or 'Not set'}")
        st.write(f"**State:** {user['state'] or 'Not set'}")
        st.write(f"**Country:** {user['country'] or 'Not set'}")
        st.write(f"**Postal Code:** {user['postal_code'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="data-entry-card">
                <h3>🚜 Farm Information</h3>
        """, unsafe_allow_html=True)
        st.write(f"**Farm Name:** {user['farm_name'] or 'Not set'}")
        st.write(f"**Farm Size:** {user['farm_size'] or 0} acres")
        st.write(f"**Farm Type:** {user['farm_type'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== DASHBOARD PAGE ====================

def show_dashboard(data):
    st.markdown(f"""
        <div class="main-header">
            <h1>🌾 AgroIntel Dashboard</h1>
            <p>Welcome back! Here's your farm overview for {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🌱 Total Acres</div>
                <div class="metric-value">{data['total_acres']:,.0f}</div>
                <div class="metric-sub">acres under cultivation</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📊 Average Yield</div>
                <div class="metric-value">{data['avg_yield']} t/ha</div>
                <div class="metric-sub">across all fields</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🚜 Active Machinery</div>
                <div class="metric-value">{data['active_machinery']}/{data['total_machinery']}</div>
                <div class="metric-sub">units operational</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📋 Compliance Score</div>
                <div class="metric-value">{data['compliance_score']}%</div>
                <div class="metric-sub">overall compliance rating</div>
            </div>
        """, unsafe_allow_html=True)
    
    if data['fields']:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-title">📊 Yield by Field</div>', unsafe_allow_html=True)
            df_fields = pd.DataFrame(data['fields'])
            fig = px.bar(df_fields, x='name', y='yield', color='crop',
                         title='', text='yield',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(texttemplate='%{text:.1f} t/ha', textposition='outside')
            fig.update_layout(height=350, showlegend=True, xaxis_title='', yaxis_title='Yield (t/ha)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="section-title">🌾 Crop Distribution</div>', unsafe_allow_html=True)
            df_fields = pd.DataFrame(data['fields'])
            fig = px.pie(df_fields, values='acres', names='crop', title='')
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No field data available. Add your first field in Farm Management!")
    
    # AI Insights
    if data['ai_recommendations']:
        st.markdown('<div class="section-title">🤖 AI-Powered Insights</div>', unsafe_allow_html=True)
        
        cols = st.columns(min(3, len(data['ai_recommendations'])))
        for idx, recommendation in enumerate(data['ai_recommendations'][:3]):
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class="ai-card">
                        <h4>{recommendation['title']}</h4>
                        <p><strong>{recommendation['field']}</strong></p>
                        <p>{recommendation['recommendation']}</p>
                        <span class="confidence">ROI: {recommendation['roi']}</span>
                        <span class="confidence" style="margin-left:0.5rem;">Confidence: {recommendation['confidence']}%</span>
                    </div>
                """, unsafe_allow_html=True)

# ==================== FARM MANAGEMENT PAGE ====================

def show_farm_management(data):
    st.markdown('<div class="main-header"><h1>🚜 Farm Management</h1></div>', unsafe_allow_html=True)
    
    # Data Entry Section
    with st.expander("➕ Add New Field", expanded=False):
        with st.form("add_field_form"):
            st.markdown("### 🌱 Add New Field")
            
            col1, col2 = st.columns(2)
            
            with col1:
                field_id = st.text_input("Field ID *", placeholder="e.g., F6", help="Unique identifier")
                field_name = st.text_input("Field Name *", placeholder="e.g., South Field")
                crop_type = st.selectbox("Crop Type", ["Winter Wheat", "Corn", "Soybeans", "Barley", "Potatoes", "Oats", "Sunflowers", "Other"])
                acres = st.number_input("Acres *", min_value=0.0, step=0.5)
            
            with col2:
                yield_tons = st.number_input("Yield (tons/ha)", min_value=0.0, step=0.1)
                soil_health = st.slider("Soil Health Score", 0, 100, 75)
                planting_date = st.date_input("Planting Date")
                harvest_date = st.date_input("Harvest Date")
            
            submitted = st.form_submit_button("🌱 Add Field", use_container_width=True)
            
            if submitted:
                if field_id and field_name and acres > 0:
                    success, message = db.add_field(
                        st.session_state.user_id,
                        field_id,
                        field_name,
                        crop_type,
                        acres,
                        yield_tons,
                        soil_health,
                        planting_date.strftime('%Y-%m-%d') if planting_date else None,
                        harvest_date.strftime('%Y-%m-%d') if harvest_date else None
                    )
                    if success:
                        st.success(f"✅ Field '{field_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Display existing fields
    st.markdown('<div class="section-title">📋 Your Fields</div>', unsafe_allow_html=True)
    
    if data['fields']:
        df_fields = pd.DataFrame(data['fields'])
        st.dataframe(df_fields, use_container_width=True)
        
        # Delete option
        st.markdown("### 🗑️ Delete Field")
        field_to_delete = st.selectbox("Select field to delete", 
                                       options=[f"{f['name']} ({f['id']})" for f in data['fields']],
                                       key="delete_field_select")
        
        if st.button("🗑️ Delete Selected Field", type="secondary"):
            field_id = field_to_delete.split('(')[-1].replace(')', '')
            if db.delete_field(st.session_state.user_id, field_id):
                st.success("✅ Field deleted successfully!")
                st.rerun()
    else:
        st.info("No fields added yet. Use the 'Add New Field' section above!")

# ==================== MACHINERY PAGE ====================

def show_machinery(data):
    st.markdown('<div class="main-header"><h1>⚙️ Machinery Management</h1></div>', unsafe_allow_html=True)
    
    # Data Entry Section
    with st.expander("➕ Add New Machinery", expanded=False):
        with st.form("add_machinery_form"):
            st.markdown("### 🚜 Add New Machinery")
            
            col1, col2 = st.columns(2)
            
            with col1:
                machine_id = st.text_input("Machine ID *", placeholder="e.g., M5")
                machine_name = st.text_input("Machine Name *", placeholder="e.g., John Deere 6120")
                machine_type = st.selectbox("Machine Type", ["Tractor", "Combine", "Sprayer", "Plow", "Drill", "Harvester", "Other"])
                operating_hours = st.number_input("Operating Hours", min_value=0, step=1)
            
            with col2:
                fuel_level = st.slider("Fuel Level (%)", 0, 100, 50)
                status = st.selectbox("Status", ["Active", "Maintenance", "Idle", "Broken"])
                last_maintenance = st.date_input("Last Maintenance Date")
                next_maintenance = st.date_input("Next Maintenance Date")
            
            submitted = st.form_submit_button("🚜 Add Machinery", use_container_width=True)
            
            if submitted:
                if machine_id and machine_name:
                    success, message = db.add_machinery(
                        st.session_state.user_id,
                        machine_id,
                        machine_name,
                        machine_type,
                        operating_hours,
                        fuel_level,
                        status,
                        last_maintenance.strftime('%Y-%m-%d') if last_maintenance else None,
                        next_maintenance.strftime('%Y-%m-%d') if next_maintenance else None
                    )
                    if success:
                        st.success(f"✅ Machinery '{machine_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Display existing machinery
    st.markdown('<div class="section-title">📋 Your Machinery</div>', unsafe_allow_html=True)
    
    if data['machinery']:
        df_machinery = pd.DataFrame(data['machinery'])
        st.dataframe(df_machinery, use_container_width=True)
        
        # Delete option
        st.markdown("### 🗑️ Delete Machinery")
        machine_to_delete = st.selectbox("Select machinery to delete", 
                                        options=[f"{m['name']} ({m['id']})" for m in data['machinery']],
                                        key="delete_machine_select")
        
        if st.button("🗑️ Delete Selected Machinery", type="secondary"):
            machine_id = machine_to_delete.split('(')[-1].replace(')', '')
            if db.delete_machinery(st.session_state.user_id, machine_id):
                st.success("✅ Machinery deleted successfully!")
                st.rerun()
    else:
        st.info("No machinery added yet. Use the 'Add New Machinery' section above!")

# ==================== SOIL ANALYSIS PAGE ====================

def show_soil_analysis(data):
    st.markdown('<div class="main-header"><h1>🧪 Soil Analysis</h1></div>', unsafe_allow_html=True)
    
    # Data Entry Section
    with st.expander("➕ Add Soil Analysis", expanded=False):
        with st.form("add_soil_form"):
            st.markdown("### 🧪 Add New Soil Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                field_options = [f['id'] for f in data['fields']] if data['fields'] else []
                if field_options:
                    field_id = st.selectbox("Field ID", options=field_options)
                    ph = st.slider("pH Level", 0.0, 14.0, 6.5, 0.1)
                    nitrogen = st.number_input("Nitrogen (mg/kg)", min_value=0.0, step=0.1)
                else:
                    st.warning("Please add fields first before adding soil analysis!")
                    field_id = None
                    ph = 6.5
                    nitrogen = 0.0
            
            with col2:
                phosphorus = st.number_input("Phosphorus (mg/kg)", min_value=0.0, step=0.1)
                potassium = st.number_input("Potassium (mg/kg)", min_value=0.0, step=0.1)
                organic_matter = st.slider("Organic Matter (%)", 0.0, 10.0, 3.0, 0.1)
            
            submitted = st.form_submit_button("🧪 Add Soil Analysis", use_container_width=True)
            
            if submitted and field_options:
                success = db.add_soil_analysis(
                    st.session_state.user_id,
                    field_id,
                    ph,
                    nitrogen,
                    phosphorus,
                    potassium,
                    organic_matter
                )
                if success:
                    st.success("✅ Soil analysis added successfully!")
                    st.rerun()
            elif submitted and not field_options:
                st.error("❌ Please add a field first!")
    
    # Display existing soil data
    st.markdown('<div class="section-title">📋 Soil Analysis Data</div>', unsafe_allow_html=True)
    
    if data['soil']:
        df_soil = pd.DataFrame(data['soil'])
        st.dataframe(df_soil, use_container_width=True)
    else:
        st.info("No soil analysis data available. Add some using the section above!")

# ==================== WEATHER PAGE ====================

def show_weather(data):
    st.markdown('<div class="main-header"><h1>🌤️ Weather Intelligence</h1></div>', unsafe_allow_html=True)
    
    if data['weather'] and len(data['weather']) > 0:
        latest = data['weather'][-1]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ Temperature", f"{latest['temperature']}°C")
        with col2:
            st.metric("💧 Humidity", f"{latest['humidity']}%")
        with col3:
            st.metric("🌧️ Rainfall", f"{latest['rainfall']} mm")
        with col4:
            st.metric("💨 Wind", f"{latest['wind_speed']} km/h")
        
        df_weather = pd.DataFrame(data['weather'])
        fig = px.line(df_weather, x='date', y=['temperature', 'humidity', 'rainfall', 'wind_speed'],
                      title='Weather Trends (30 Days)')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No weather data available")

# ==================== COMPLIANCE PAGE ====================

def show_compliance(data):
    st.markdown('<div class="main-header"><h1>📋 Compliance & Reporting</h1></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-label">Overall Compliance Score</div>
        </div>
    """, unsafe_allow_html=True)
    
    if data['compliance']:
        df_compliance = pd.DataFrame(data['compliance'])
        st.dataframe(df_compliance, use_container_width=True)
    else:
        st.info("No compliance data available")

# ==================== AI COPILOT PAGE ====================

def show_ai_copilot(data):
    st.markdown('<div class="main-header"><h1>🤖 AI Copilot</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="ai-card">
            <h4>💬 Ask AgroIntel AI</h4>
            <p>Get predictive, explainable, and actionable guidance for your farm</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_question = st.text_input("Ask a question about your farm:")
    
    if user_question:
        st.markdown("""
            <div class="ai-card">
                <h4>🤖 AI Response</h4>
                <p>Based on your farm data and integrated systems:</p>
            </div>
        """, unsafe_allow_html=True)
        
        if 'field' in user_question.lower() or 'crop' in user_question.lower():
            if data['fields']:
                st.write("Here's your current field data:")
                st.dataframe(pd.DataFrame(data['fields']))
            else:
                st.info("No field data available yet.")
        elif 'machine' in user_question.lower() or 'tractor' in user_question.lower():
            if data['machinery']:
                st.write("Here's your machinery status:")
                st.dataframe(pd.DataFrame(data['machinery']))
            else:
                st.info("No machinery data available yet.")
        elif 'weather' in user_question.lower():
            if data['weather']:
                st.write("Recent weather trends:")
                st.dataframe(pd.DataFrame(data['weather']))
            else:
                st.info("No weather data available yet.")
        else:
            st.info("I'll analyze your query and get back to you with insights!")

# ==================== DATA LOADING ====================

def load_user_data(user_id):
    """Load all user data from database"""
    return {
        'fields': db.get_fields(user_id),
        'machinery': db.get_machinery(user_id),
        'weather': db.get_weather(user_id, 30),
        'soil': db.get_soil_analysis(user_id),
        'compliance': db.get_compliance(user_id),
        'ai_recommendations': db.get_ai_recommendations(user_id),
        'total_acres': db.get_total_acres(user_id),
        'avg_yield': db.get_avg_yield(user_id),
        'active_machinery': db.get_active_machinery_count(user_id),
        'total_machinery': db.get_total_machinery_count(user_id),
        'compliance_score': db.get_compliance_score(user_id)
    }

# ==================== MAIN ====================

def main():
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-brand">
                <div style="font-size:3rem;">🌾</div>
                <h2>AgroIntel</h2>
                <p>Universal Agricultural Intelligence</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.session_state.authenticated:
            user = db.get_user_by_id(st.session_state.user_id)
            if user:
                st.markdown(f"👋 **Welcome, {user['full_name']}**")
            
            st.markdown("---")
            
            selected = option_menu(
                "Navigation",
                ["Dashboard", "Farm Management", "Machinery", "Weather", 
                 "Soil Analysis", "Compliance", "AI Copilot", "👤 My Profile"],
                icons=["house", "tractor", "gear", "cloud-sun", 
                       "droplet", "clipboard-check", "robot", "person"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "nav-link": {"font-size": "14px", "text-align": "left"},
                    "nav-link-selected": {"background-color": "#2E7D32"},
                }
            )
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.user_id = None
                st.rerun()
        
        else:
            tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Login", use_container_width=True)
                    
                    if submitted:
                        user = db.get_user(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = user['username']
                            st.session_state.user_id = user['id']
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            
            with tab2:
                st.markdown("### 📝 New User?")
                if st.button("Create Account", use_container_width=True):
                    st.session_state.page = 'register'
                    st.rerun()
    
    # Main content based on state
    if st.session_state.authenticated:
        data = load_user_data(st.session_state.user_id)
        
        if selected == "👤 My Profile":
            show_profile()
        elif selected == "Dashboard":
            show_dashboard(data)
        elif selected == "Farm Management":
            show_farm_management(data)
        elif selected == "Machinery":
            show_machinery(data)
        elif selected == "Weather":
            show_weather(data)
        elif selected == "Soil Analysis":
            show_soil_analysis(data)
        elif selected == "Compliance":
            show_compliance(data)
        elif selected == "AI Copilot":
            show_ai_copilot(data)
    else:
        if st.session_state.page == 'register':
            show_registration()
        else:
            st.markdown("""
                <div class="welcome-container">
                    <div class="emoji">🌾</div>
                    <h1>Welcome to AgroIntel</h1>
                    <p>Universal Agricultural Intelligence Platform</p>
                    <p class="sub-text">Please login or create an account to access your dashboard.</p>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()