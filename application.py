from keras.models import Sequential
from keras.layers import Dense, Dropout
import joblib
import numpy as np
from keras.applications import DenseNet201
import os
import tempfile
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from io import BytesIO
import time
from flask import Flask, render_template, request, redirect, url_for, flash  , send_file , session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from keras.utils import load_img , img_to_array
from middleware import auth , guest
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime , timezone
from authlib.integrations.flask_client import OAuth

application = Flask(__name__)
app = application

load_dotenv()  
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Secret key for session management
app.secret_key = os.getenv("SECRET_KEY")

#google oauth configuration 
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


# Load models and scaler
scaler = joblib.load('scaler.pkl')  # Load the scaler
stacking_model = joblib.load('stacking_model.pkl')  # Load the stacking model

model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ct_scan_models')


# Load DenseNet model weights
densenet_model = DenseNet201(weights=None, include_top=False, input_shape=(224, 224, 3))
densenet_model.load_weights(os.path.join(model_dir, 'densenet_weights.h5'))  # Load DenseNet model weights

# Rebuild the ANN model architecture and load weights
ann_model = Sequential([
    Dense(512, input_dim=2000, activation='relu'),
    Dropout(0.5),
    Dense(256, activation='relu'),
    Dropout(0.5),
    Dense(128, activation='relu'),
    Dense(4, activation='softmax')  # Output layer (softmax for binary classification)
])
ann_model.load_weights(os.path.join(model_dir, 'ann_weights.h5'))  # Load ANN model weights

# Load PCA model
pca = joblib.load(os.path.join(model_dir, 'pca_model.pkl'))  # Load PCA model

# Sample credentials for demonstration purposes
USER_CREDENTIALS = {"username": "admin", "password": "password123"}


# MongoDB configuration
client = MongoClient("mongodb+srv://alzheimer_detection:soham_animesh007@alzheimersdetection.mo7vr.mongodb.net/")  
db = client['user_db']  
users_collection = db['users']  # Use a collection (table) named 'users'

from flask import make_response

@app.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Route for the home page
@app.route('/')
def home():
    session.clear()
    return render_template('index.html')

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/get_help')
def get_help():
    return render_template('get_help.html')

@app.route('/authorize/google')
def authorize_google():
    
    token = google.authorize_access_token()

    userinfo_endpoint = google.server_metadata['userinfo_endpoint']
    
    # Call it, explicitly passing the token
    resp = google.get(userinfo_endpoint, token=token)
    user_info = resp.json()

    # Extract user data
    email = user_info.get('email')
    username = user_info.get('name')

    # Check if user exists in DB
    user = users_collection.find_one({'email': email})
    if not user:
        # If user not in DB, create a new user
        new_user = {
            "username": username,
            "email": email,
            "password": "",  # No password since it's Google Auth
            "created_at": datetime.now(timezone.utc)
        }
        users_collection.insert_one(new_user)
        user = new_user

    session['user_id'] = str(user.get('_id'))
    session['username'] = user.get('username')

    flash('Successfully logged in with Google', 'success')
    return redirect(url_for('dashboard'))


# Route for login
@app.route('/login', methods=['GET', 'POST'])
@guest
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find user by username
        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Store user ID in session
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password, please try again.' , 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Route for the registration page
@app.route('/sign_up', methods=['GET', 'POST'])
@guest
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Hash the password before saving
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if username already exists
        existing_user = users_collection.find_one({"username": username})

        if existing_user:
            flash('Username already exists. Please try another one.' ,'error')
            return redirect(url_for('register'))

        # Create a new user and insert into MongoDB
        new_user = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "created_at": datetime.now(timezone.utc)
        }

        users_collection.insert_one(new_user)
        flash('Registration successful! You can now log in.' , 'success')

        return redirect(url_for('login'))

    return render_template('sign_up.html')

# Route for the dashboard page
@app.route('/dashboard')
@auth
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    return render_template('dashboard.html')

# Route for logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/medical_info', methods=['GET', 'POST'])
@auth
def get_medical_info():
    if request.method == 'POST':
        try:
            input_features = []

            def convert_to_mg_dl(value, unit):
                if unit == "mmol/L":
                    return round(value * 38.67, 2)
                return round(value, 2)

            input_features.append(int(request.form['Age']))
            input_features.append(int(request.form['Gender']))
            input_features.append(int(request.form['Ethnicity']))
            input_features.append(int(request.form['EducationLevel']))
            bmi_value = request.form['BMI']
            if bmi_value == "Not Available":
                return redirect("https://www.calculator.net/bmi-calculator.html")
            else:
                input_features.append(round(float(bmi_value), 2))
            input_features.append(int(request.form['Smoking']))
            input_features.append(int(request.form['FamilyHistoryAlzheimers']))
            input_features.append(int(request.form['CardiovascularDisease']))
            input_features.append(int(request.form['Diabetes']))
            input_features.append(int(request.form['Depression']))
            input_features.append(int(request.form['HeadInjury']))
            input_features.append(int(request.form['Hypertension']))
            input_features.append(int(round(float(request.form['SystolicBP']))))
            input_features.append(int(round(float(request.form['DiastolicBP']))))
            input_features.append(convert_to_mg_dl(float(request.form['CholesterolTotal']), request.form['CholesterolTotalUnit']))
            input_features.append(convert_to_mg_dl(float(request.form['CholesterolLDL']), request.form['CholesterolLDLUnit']))
            input_features.append(convert_to_mg_dl(float(request.form['CholesterolHDL']), request.form['CholesterolHDLUnit']))
            input_features.append(convert_to_mg_dl(float(request.form['CholesterolTriglycerides']), request.form['CholesterolTriglyceridesUnit']))
            mmse_value = request.form['MMSE']
            if mmse_value == "Not Available":
                return redirect("https://compendiumapp.com/post_4xQIen-Ly")
            else:
                input_features.append(float(mmse_value))

            functional_assessment = request.form['FunctionalAssessment']
            if functional_assessment == "Not Available":
                return redirect("https://www.compassus.com/healthcare-professionals/determining-eligibility/functional-assessment-staging-tool-fast-scale-for-dementia/")
            else:
                input_features.append(round(float(functional_assessment), 2))

            adl_value = request.form['ADL']
            if adl_value == "Not Available":
                return redirect("https://www.mdcalc.com/calc/3912/barthel-index-activities-daily-living-adl#evidence")
            else:
                input_features.append(round(float(adl_value), 2))

            input_features.extend([
                int(request.form['MemoryComplaints']),
                int(request.form['BehavioralProblems']),
                int(request.form['Confusion']),
                int(request.form['Disorientation']),
                int(request.form['PersonalityChanges']),
                int(request.form['DifficultyCompletingTasks']),
                int(request.form['Forgetfulness'])
            ])

            # Scale features and predict
            scaled_features = scaler.transform([input_features])
            prediction = stacking_model.predict(scaled_features)
            diagnosis = "Positive for Alzheimer's" if prediction[0] == 1 else "Negative for Alzheimer's"

            # Save the prediction and input data in the session
            session['input_features'] = input_features
            session['diagnosis'] = diagnosis

            return redirect('/generate_pdf')

        except Exception as e:
            return f"Error: {str(e)}"

    else:
        return render_template('predict_medical.html')


@app.route('/generate_pdf', methods=['GET'])
@auth
def trigger_pdf():
    try:
        # Retrieve the data from the session
        input_features = session.get('input_features')
        diagnosis = session.get('diagnosis')

        if not input_features or not diagnosis:
            return "Error: Missing data for PDF generation"

        # Generate PDF with user inputs and prediction result
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

        pdf_buffer.seek(0)  # Reset the buffer's position

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"medical_report.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return f"Error: {str(e)}"





from flask import jsonify
import time


@app.route('/upload_ct_scan', methods=['POST'])
@auth
def upload_ct_scan():
    try:
        # Get image file from POST request
        file = request.files['ct_scan']

        # Create a temporary file and save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file.save(tmp.name)  # Save the file temporarily
            tmp.close()  # Close the file so it can be used by load_img

            # Preprocess the image (resize, rescale, etc.)
            img = load_img(tmp.name, target_size=(224, 224))  # Pass the temporary file path
            img_array = img_to_array(img)  # Convert image to array
            img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
            img_array = img_array / 255.0  # Rescale the image

            

            # Extract features using the DenseNet model
            img_features = densenet_model.predict(img_array)  # Use DenseNet for feature extraction
            img_features_flat = img_features.reshape(1, -1)
            img_features_pca = pca.transform(img_features_flat)  # Apply PCA transformation

            # Predict using the trained ANN model
            prediction = ann_model.predict(img_features_pca)
            predicted_class = np.argmax(prediction, axis=1)
            class_label = ['Mild Demented', 'Moderate Demented', 'Non Demented', 'Very Mild Demented']

            
            time.sleep(3)  

            # Return prediction result
            return render_template('ct_scan_result.html', diagnosis=class_label[predicted_class[0]])

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(host="0.0.0.0")