from flask import Flask, render_template, url_for, request, send_file, jsonify
from src.exception import CustomException
from src.logger import logging as lg
import sys
from joblib import load
import pandas as pd
from src.utils.extract_features import ExtractFeatures

from src.pipeline.train_pipeline import TrainingPipeline
from src.pipeline.predict_pipeline import PredictionPipeline

app = Flask(__name__)

try:    
    model = load('trained_model/model.pkl')
except Exception as e:
    model = None

@app.route("/")
def home():
    return render_template('home.html', name=model)

@app.route("/train")
def train_route():
    try:
        if not model:
            train_pipeline = TrainingPipeline()
            train_pipeline.run_pipeline()
        return render_template('training.html')
    except Exception as e:
        raise CustomException(e,sys)

@app.route("/url_classifier", methods=['POST', 'GET'])
def url_classifier():
    if request.method == 'POST':
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify(error="Please enter a URL"), 400
        object = ExtractFeatures()
        object.extract_features(url)
        feature_names = [
            'having_IP_Address', 'URL_Length', 'Shortining_Service', 'having_At_Symbol',
            'double_slash_redirecting', 'Prefix_Suffix', 'having_Sub_Domain', 'SSLfinal_State',
            'Domain_registeration_length', 'Favicon', 'port', 'HTTPS_token',
            'Request_URL', 'URL_of_Anchor', 'Links_in_tags', 'SFH', 'Submitting_to_email',
            'Abnormal_URL', 'Redirect', 'on_mouseover', 'RightClick', 'popUpWidnow',
            'Iframe', 'age_of_domain', 'DNSRecord', 'web_traffic', 'Page_Rank',
            'Google_Index', 'Links_pointing_to_page', 'Statistical_report'
        ]
        features_df = pd.DataFrame([object.features], columns=feature_names)
        # features = [1,0,-1,1,1,-1,1,1,-1,1,1,-1,1,0,1,-1,1,1,0,1,1,1,1,1,-1,1,1,1,0,1]
        prediction = model.predict(features_df)[0]
        result = 'Phishing' if prediction == 0 else 'Legitimate'
        return jsonify(result=result, url=url)
    
    # For GET requests or page load
    return render_template('url_classifier.html')

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    try:
        if request.method == 'POST':
            prediction_pipeline = PredictionPipeline(request)
            prediction_file_detail = prediction_pipeline.run_pipeline()
            lg.info("prediction completed. Downloading prediction file.")
            return send_file(prediction_file_detail.prediction_file_path, download_name= prediction_file_detail.prediction_file_name, as_attachment= True)
        else:
            return render_template('prediction.html')
    except Exception as e:
        raise CustomException(e,sys)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug= True)