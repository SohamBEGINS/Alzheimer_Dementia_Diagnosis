"""
Alzheimer's Detection Flask Application
Production-ready refactored version
"""
import os
import logging
import tempfile
import time
import threading
from io import BytesIO
from datetime import datetime, timezone
from functools import lru_cache

import numpy as np
import joblib
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, send_file, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import RequestEntityTooLarge
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.applications import DenseNet201
from keras.utils import load_img, img_to_array
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

from middleware import auth, guest

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with explicit template and static folder paths
# This ensures compatibility with case-sensitive file systems (Linux/Docker)
application = Flask(__name__, 
                    template_folder='Templates',
                    static_folder='static')
app = application

# Base directory paths using relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'mri_models')
MODEL_BASE_DIR = BASE_DIR

# Temporary file directory (configurable for containers)
TEMP_DIR = os.getenv("TEMP_DIR", tempfile.gettempdir())
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"Temporary files directory: {TEMP_DIR}")

# Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
app.secret_key = SECRET_KEY

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# Configure file upload limits (configurable)
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # Default 16MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Resource limits configuration
MAX_MEMORY_USAGE_MB = int(os.getenv("MAX_MEMORY_USAGE_MB", "2048"))  # Default 2GB
MODEL_LOAD_TIMEOUT = int(os.getenv("MODEL_LOAD_TIMEOUT", "300"))  # Default 5 minutes

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

# Google OAuth configuration
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        access_token_params=None,
        authorize_params=None,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
else:
    logger.warning("Google OAuth credentials not configured. Google login will not work.")
    google = None

# MongoDB configuration with retry logic
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required")

MONGODB_CONNECT_TIMEOUT = int(os.getenv("MONGODB_CONNECT_TIMEOUT", "5000"))
MONGODB_SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT", "5000"))
MONGODB_RETRY_ATTEMPTS = int(os.getenv("MONGODB_RETRY_ATTEMPTS", "3"))
MONGODB_RETRY_DELAY = int(os.getenv("MONGODB_RETRY_DELAY", "2"))  # seconds

def connect_mongodb():
    """Connect to MongoDB with retry logic"""
    for attempt in range(1, MONGODB_RETRY_ATTEMPTS + 1):
        try:
            client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=MONGODB_CONNECT_TIMEOUT,
                retryWrites=True,
                maxPoolSize=50,
                minPoolSize=10
            )
            # Test connection with timeout
            client.admin.command('ping', maxTimeMS=2000)
            db = client['user_db']
            users_collection = db['users']
            logger.info(f"Successfully connected to MongoDB on attempt {attempt}")
            return client, db, users_collection
        except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
            if attempt < MONGODB_RETRY_ATTEMPTS:
                logger.warning(f"MongoDB connection attempt {attempt} failed: {e}. Retrying in {MONGODB_RETRY_DELAY} seconds...")
                time.sleep(MONGODB_RETRY_DELAY)
            else:
                logger.error(f"Failed to connect to MongoDB after {MONGODB_RETRY_ATTEMPTS} attempts: {e}")
                raise

# Initialize MongoDB connection
client, db, users_collection = connect_mongodb()

# Model lazy loading with thread-safe caching
_model_cache = {}
_model_lock = threading.Lock()
_model_errors = []

def load_scaler():
    """Load scaler model (lazy loading)"""
    if 'scaler' not in _model_cache:
        with _model_lock:
            if 'scaler' not in _model_cache:
                try:
                    scaler_path = os.path.join(MODEL_BASE_DIR, 'scaler.pkl')
                    if not os.path.exists(scaler_path):
                        raise FileNotFoundError(f"scaler.pkl not found at {scaler_path}")
                    _model_cache['scaler'] = joblib.load(scaler_path)
                    logger.info("Scaler loaded successfully")
                except Exception as e:
                    error_msg = f"Error loading scaler: {str(e)}"
                    _model_errors.append(error_msg)
                    logger.error(error_msg)
                    _model_cache['scaler'] = None
    return _model_cache.get('scaler')

def load_stacking_model():
    """Load stacking model (lazy loading)"""
    if 'stacking_model' not in _model_cache:
        with _model_lock:
            if 'stacking_model' not in _model_cache:
                try:
                    stacking_path = os.path.join(MODEL_BASE_DIR, 'stacking_model.pkl')
                    if not os.path.exists(stacking_path):
                        raise FileNotFoundError(f"stacking_model.pkl not found at {stacking_path}")
                    _model_cache['stacking_model'] = joblib.load(stacking_path)
                    logger.info("Stacking model loaded successfully")
                except Exception as e:
                    error_msg = f"Error loading stacking model: {str(e)}"
                    _model_errors.append(error_msg)
                    logger.error(error_msg)
                    _model_cache['stacking_model'] = None
    return _model_cache.get('stacking_model')

def load_densenet_model():
    """Load DenseNet model (lazy loading)"""
    if 'densenet_model' not in _model_cache:
        with _model_lock:
            if 'densenet_model' not in _model_cache:
                try:
                    if not os.path.exists(MODEL_DIR):
                        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
                    
                    densenet_weights_path = os.path.join(MODEL_DIR, 'densenet_weights.h5')
                    if not os.path.exists(densenet_weights_path):
                        raise FileNotFoundError(f"DenseNet weights not found: {densenet_weights_path}")
                    
                    densenet_model = DenseNet201(weights=None, include_top=False, input_shape=(224, 224, 3))
                    densenet_model.load_weights(densenet_weights_path)
                    _model_cache['densenet_model'] = densenet_model
                    logger.info("DenseNet model loaded successfully")
                except Exception as e:
                    error_msg = f"Error loading DenseNet model: {str(e)}"
                    _model_errors.append(error_msg)
                    logger.error(error_msg)
                    _model_cache['densenet_model'] = None
    return _model_cache.get('densenet_model')

def load_ann_model():
    """Load ANN model (lazy loading)"""
    if 'ann_model' not in _model_cache:
        with _model_lock:
            if 'ann_model' not in _model_cache:
                try:
                    if not os.path.exists(MODEL_DIR):
                        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
                    
                    ann_weights_path = os.path.join(MODEL_DIR, 'ann_weights.h5')
                    if not os.path.exists(ann_weights_path):
                        raise FileNotFoundError(f"ANN weights not found: {ann_weights_path}")
                    
                    ann_model = Sequential([
                        Dense(512, input_dim=2000, activation='relu'),
                        Dropout(0.5),
                        Dense(256, activation='relu'),
                        Dropout(0.5),
                        Dense(128, activation='relu'),
                        Dense(4, activation='softmax')
                    ])
                    ann_model.load_weights(ann_weights_path)
                    _model_cache['ann_model'] = ann_model
                    logger.info("ANN model loaded successfully")
                except Exception as e:
                    error_msg = f"Error loading ANN model: {str(e)}"
                    _model_errors.append(error_msg)
                    logger.error(error_msg)
                    _model_cache['ann_model'] = None
    return _model_cache.get('ann_model')

def load_pca_model():
    """Load PCA model (lazy loading)"""
    if 'pca' not in _model_cache:
        with _model_lock:
            if 'pca' not in _model_cache:
                try:
                    if not os.path.exists(MODEL_DIR):
                        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
                    
                    pca_path = os.path.join(MODEL_DIR, 'pca_model.pkl')
                    if not os.path.exists(pca_path):
                        raise FileNotFoundError(f"PCA model not found: {pca_path}")
                    
                    _model_cache['pca'] = joblib.load(pca_path)
                    logger.info("PCA model loaded successfully")
                except Exception as e:
                    error_msg = f"Error loading PCA model: {str(e)}"
                    _model_errors.append(error_msg)
                    logger.error(error_msg)
                    _model_cache['pca'] = None
    return _model_cache.get('pca')

# Convenience functions for backward compatibility
def get_scaler():
    return load_scaler()

def get_stacking_model():
    return load_stacking_model()

def get_densenet_model():
    return load_densenet_model()

def get_ann_model():
    return load_ann_model()

def get_pca():
    return load_pca_model()

def get_model_errors():
    """Get list of model loading errors"""
    return _model_errors.copy()

# Pre-load models if EAGER_LOAD_MODELS is set (default: False for lazy loading)
if os.getenv("EAGER_LOAD_MODELS", "false").lower() == "true":
    logger.info("Eager loading models at startup...")
    load_scaler()
    load_stacking_model()
    load_densenet_model()
    load_ann_model()
    load_pca_model()
    logger.info("All models loaded at startup")
else:
    logger.info("Models will be loaded on-demand (lazy loading)")

# Helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_mg_dl(value, unit):
    """Convert cholesterol values to mg/dL"""
    if unit == "mmol/L":
        return round(value * 38.67, 2)
    return round(value, 2)

# Middleware
@app.after_request
def add_cache_control_headers(response):
    """Add cache control headers to prevent caching"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error_code=404, 
                          error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error_code=500, 
                          error_message="Internal server error. Please try again later."), 500

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """Handle file upload size limit errors"""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(request.url), 413

# Routes
@app.route('/')
def home():
    """Home page route"""
    session.clear()
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    # Try loading models to check their availability
    scaler = get_scaler()
    stacking_model = get_stacking_model()
    densenet_model = get_densenet_model()
    ann_model = get_ann_model()
    pca = get_pca()
    
    health_status = {
        'status': 'healthy',
        'models_loaded': {
            'scaler': scaler is not None,
            'stacking_model': stacking_model is not None,
            'densenet_model': densenet_model is not None,
            'ann_model': ann_model is not None,
            'pca': pca is not None
        },
        'database': 'connected',
        'model_errors': get_model_errors() if get_model_errors() else None,
        'lazy_loading': os.getenv("EAGER_LOAD_MODELS", "false").lower() != "true"
    }
    
    # Check database connection with timeout
    try:
        client.admin.command('ping', maxTimeMS=2000)
    except Exception as e:
        health_status['database'] = 'disconnected'
        health_status['database_error'] = str(e)
        health_status['status'] = 'degraded'
        logger.error(f"Database health check failed: {e}")
    
    # Check if critical models are missing
    if not all([scaler, stacking_model, densenet_model, ann_model, pca]):
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/login/google')
def login_google():
    """Google OAuth login route"""
    if not google:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/get_help')
def get_help():
    """Get help page route"""
    return render_template('get_help.html')

@app.route('/authorize/google')
def authorize_google():
    """Google OAuth callback route"""
    if not google:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('login'))
    
    try:
        token = google.authorize_access_token()
        userinfo_endpoint = google.server_metadata['userinfo_endpoint']
        resp = google.get(userinfo_endpoint, token=token)
        user_info = resp.json()

        email = user_info.get('email')
        username = user_info.get('name')

        if not email:
            flash('Failed to retrieve user information from Google.', 'error')
            return redirect(url_for('login'))

        # Check if user exists in DB
        user = users_collection.find_one({'email': email})
        if not user:
            # Create new user
            new_user = {
                "username": username,
                "email": email,
                "password": "",  # No password for Google Auth
                "created_at": datetime.now(timezone.utc)
            }
            users_collection.insert_one(new_user)
            user = new_user

        session['user_id'] = str(user.get('_id'))
        session['username'] = user.get('username')

        flash('Successfully logged in with Google', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        flash('An error occurred during Google login. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@guest
def login():
    """Login route"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Please provide both username and password.', 'error')
                return redirect(url_for('login'))

            user = users_collection.find_one({"username": username})

            if user and user.get('password') and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password, please try again.', 'error')
                logger.warning(f"Failed login attempt for username: {username}")
                return redirect(url_for('login'))
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/sign_up', methods=['GET', 'POST'])
@guest
def register():
    """Registration route"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            email = request.form.get('email', '').strip()

            # Validation
            if not username or not password or not email:
                flash('Please fill in all fields.', 'error')
                return redirect(url_for('register'))

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return redirect(url_for('register'))

            # Check if username already exists
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                flash('Username already exists. Please try another one.', 'error')
                return redirect(url_for('register'))

            # Check if email already exists
            existing_email = users_collection.find_one({"email": email})
            if existing_email:
                flash('Email already registered. Please use a different email.', 'error')
                return redirect(url_for('register'))

            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = {
                "username": username,
                "password": hashed_password,
                "email": email,
                "created_at": datetime.now(timezone.utc)
            }

            users_collection.insert_one(new_user)
            logger.info(f"New user registered: {username}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('sign_up.html')

@app.route('/dashboard')
@auth
def dashboard():
    """Dashboard route"""
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    """Logout route"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))

@app.route('/medical_info', methods=['GET', 'POST'])
@auth
def get_medical_info():
    """Medical information prediction route"""
    if request.method == 'POST':
        scaler = get_scaler()
        stacking_model = get_stacking_model()
        
        if not scaler or not stacking_model:
            flash('Prediction models are not available. Please contact support.', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            input_features = []

            # Extract and validate form data
            input_features.append(int(request.form.get('Age', 0)))
            input_features.append(int(request.form.get('Gender', 0)))
            input_features.append(int(request.form.get('Ethnicity', 0)))
            input_features.append(int(request.form.get('EducationLevel', 0)))
            
            bmi_value = request.form.get('BMI', '')
            if bmi_value == "Not Available":
                return redirect("https://www.calculator.net/bmi-calculator.html")
            else:
                input_features.append(round(float(bmi_value), 2))
            
            input_features.append(int(request.form.get('Smoking', 0)))
            input_features.append(int(request.form.get('FamilyHistoryAlzheimers', 0)))
            input_features.append(int(request.form.get('CardiovascularDisease', 0)))
            input_features.append(int(request.form.get('Diabetes', 0)))
            input_features.append(int(request.form.get('Depression', 0)))
            input_features.append(int(request.form.get('HeadInjury', 0)))
            input_features.append(int(request.form.get('Hypertension', 0)))
            input_features.append(int(round(float(request.form.get('SystolicBP', 0)))))
            input_features.append(int(round(float(request.form.get('DiastolicBP', 0)))))
            
            input_features.append(convert_to_mg_dl(
                float(request.form.get('CholesterolTotal', 0)),
                request.form.get('CholesterolTotalUnit', 'mg/dL')
            ))
            input_features.append(convert_to_mg_dl(
                float(request.form.get('CholesterolLDL', 0)),
                request.form.get('CholesterolLDLUnit', 'mg/dL')
            ))
            input_features.append(convert_to_mg_dl(
                float(request.form.get('CholesterolHDL', 0)),
                request.form.get('CholesterolHDLUnit', 'mg/dL')
            ))
            input_features.append(convert_to_mg_dl(
                float(request.form.get('CholesterolTriglycerides', 0)),
                request.form.get('CholesterolTriglyceridesUnit', 'mg/dL')
            ))
            
            mmse_value = request.form.get('MMSE', '')
            if mmse_value == "Not Available":
                return redirect("https://compendiumapp.com/post_4xQIen-Ly")
            else:
                input_features.append(float(mmse_value))

            functional_assessment = request.form.get('FunctionalAssessment', '')
            if functional_assessment == "Not Available":
                return redirect("https://www.compassus.com/healthcare-professionals/determining-eligibility/functional-assessment-staging-tool-fast-scale-for-dementia/")
            else:
                input_features.append(round(float(functional_assessment), 2))

            adl_value = request.form.get('ADL', '')
            if adl_value == "Not Available":
                return redirect("https://www.mdcalc.com/calc/3912/barthel-index-activities-daily-living-adl#evidence")
            else:
                input_features.append(round(float(adl_value), 2))

            input_features.extend([
                int(request.form.get('MemoryComplaints', 0)),
                int(request.form.get('BehavioralProblems', 0)),
                int(request.form.get('Confusion', 0)),
                int(request.form.get('Disorientation', 0)),
                int(request.form.get('PersonalityChanges', 0)),
                int(request.form.get('DifficultyCompletingTasks', 0)),
                int(request.form.get('Forgetfulness', 0))
            ])

            # Scale features and predict
            scaled_features = scaler.transform([input_features])
            prediction = stacking_model.predict(scaled_features)
            diagnosis = "Positive for Alzheimer's" if prediction[0] == 1 else "Negative for Alzheimer's"

            # Save prediction in session
            session['input_features'] = input_features
            session['diagnosis'] = diagnosis

            return redirect('/generate_pdf')

        except ValueError as e:
            logger.error(f"Validation error in medical_info: {e}")
            flash('Invalid input data. Please check all fields and try again.', 'error')
            return redirect(url_for('get_medical_info'))
        except Exception as e:
            logger.error(f"Error in medical_info prediction: {e}")
            flash('An error occurred during prediction. Please try again.', 'error')
            return redirect(url_for('get_medical_info'))

    return render_template('predict_medical.html')

@app.route('/generate_pdf', methods=['GET'])
@auth
def trigger_pdf():
    """Generate PDF report route"""
    try:
        input_features = session.get('input_features')
        diagnosis = session.get('diagnosis')

        if not input_features or not diagnosis:
            flash('Missing data for PDF generation. Please submit medical information again.', 'error')
            return redirect(url_for('get_medical_info'))

        # Generate PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        data = [
            ["Feature", "Value"],
            ["Age", input_features[0]],
            ["Gender", input_features[1]],
            ["Ethnicity", input_features[2]],
            ["Education Level", input_features[3]],
            ["BMI", input_features[4]],
            ["Smoking", input_features[5]],
            ["Family History of Alzheimer's", input_features[6]],
            ["Cardiovascular Disease", input_features[7]],
            ["Diabetes", input_features[8]],
            ["Depression", input_features[9]],
            ["Head Injury", input_features[10]],
            ["Hypertension", input_features[11]],
            ["Systolic BP", input_features[12]],
            ["Diastolic BP", input_features[13]],
            ["Cholesterol Total", input_features[14]],
            ["Cholesterol LDL", input_features[15]],
            ["Cholesterol HDL", input_features[16]],
            ["Cholesterol Triglycerides", input_features[17]],
            ["MMSE", input_features[18]],
            ["Functional Assessment", input_features[19]],
            ["ADL Value", input_features[20]],
            ["Memory Complaints", input_features[21]],
            ["Behavioral Problems", input_features[22]],
            ["Confusion", input_features[23]],
            ["Disorientation", input_features[24]],
            ["Personality Changes", input_features[25]],
            ["Difficulty Completing Tasks", input_features[26]],
            ["Forgetfulness", input_features[27]],
            ["Diagnosis", diagnosis]
        ]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements = [table]
        doc.build(elements)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        flash('An error occurred while generating the PDF. Please try again.', 'error')
        return redirect(url_for('get_medical_info'))

@app.route('/upload_ct_scan', methods=['POST'])
@auth
def upload_ct_scan():
    """CT scan/MRI upload and prediction route"""
    densenet_model = get_densenet_model()
    ann_model = get_ann_model()
    pca = get_pca()
    
    if not densenet_model or not ann_model or not pca:
        flash('MRI prediction models are not available. Please contact support.', 'error')
        return redirect(url_for('dashboard'))
    
    tmp_file_path = None
    try:
        # Validate file exists
        if 'ct_scan' not in request.files:
            flash('No file provided. Please select an image file.', 'error')
            return redirect(url_for('dashboard'))
        
        file = request.files['ct_scan']
        
        if file.filename == '':
            flash('No file selected. Please choose an image file.', 'error')
            return redirect(url_for('dashboard'))
        
        # Validate file extension
        if not allowed_file(file.filename):
            flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
            return redirect(url_for('dashboard'))

        # Create temporary file in configured temp directory
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.jpg',
            dir=TEMP_DIR
        )
        tmp_file_path = tmp_file.name
        file.save(tmp_file_path)
        tmp_file.close()

        # Preprocess the image
        img = load_img(tmp_file_path, target_size=(224, 224))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0

        # Extract features using DenseNet model
        img_features = densenet_model.predict(img_array, verbose=0)
        img_features_flat = img_features.reshape(1, -1)
        img_features_pca = pca.transform(img_features_flat)

        # Predict using ANN model
        prediction = ann_model.predict(img_features_pca, verbose=0)
        predicted_class = np.argmax(prediction, axis=1)
        class_label = ['Mild Demented', 'Moderate Demented', 'Non Demented', 'Very Mild Demented']

        diagnosis = class_label[predicted_class[0]]
        logger.info(f"MRI scan prediction completed: {diagnosis}")

        return render_template('ct_scan_result.html', diagnosis=diagnosis)

    except Exception as e:
        logger.error(f"Error processing CT scan: {e}")
        flash('An error occurred while processing the image. Please ensure the file is a valid image and try again.', 'error')
        return redirect(url_for('dashboard'))
    
    finally:
        # Clean up temporary file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmp_file_path}: {e}")

if __name__ == '__main__':
    # Development server only - use Gunicorn in production
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host="0.0.0.0", port=port, debug=debug)
