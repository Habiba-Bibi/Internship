from flask import Flask, request, jsonify, send_from_directory
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__, static_folder='static')

# Load the trained model and imputer
MODEL_PATH = 'xgboost_model.pkl'
IMPUTER_PATH = 'imputer.pkl'

if os.path.exists(MODEL_PATH) and os.path.exists(IMPUTER_PATH):
    model = joblib.load(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
else:
    print("Warning: Model or imputer not found. Please run model.py first.")
    model = None
    imputer = None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/predict', methods=['POST'])
def predict():
    if not model or not imputer:
        return jsonify({'error': 'Model not loaded on server.'}), 500
        
    try:
        data = request.json
        completion_time = float(data.get('completion_time'))
        feedback_rating = float(data.get('feedback_rating'))
        attendance = float(data.get('attendance'))
        
        # Create a dataframe for the input exactly as the imputer expects
        input_data = pd.DataFrame([[completion_time, feedback_rating, attendance]], 
                                  columns=['Completion_Time', 'Feedback_Rating', 'Attendance'])
        
        # Impute
        input_imputed = imputer.transform(input_data)
        
        # Predict
        predicted_score = float(model.predict(input_imputed)[0])
        
        # Determine category
        if predicted_score < 60:
            category = 'Struggle'
        elif predicted_score <= 80:
            category = 'Average'
        else:
            category = 'Excel'
            
        return jsonify({
            'score': round(predicted_score, 2),
            'category': category
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)
