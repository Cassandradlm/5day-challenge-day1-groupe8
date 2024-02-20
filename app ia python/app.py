# app.py
from flask import Flask, request, render_template, url_for, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import requests
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Aucun fichier envoyé", 400
    file = request.files['file']
    if file.filename == '':
        return "Aucun fichier sélectionné", 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    api_url = "https://5daychallengeiacustomvisiongroupe8-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/7653d23e-6abf-49c3-bfb5-82c6574ddb68/detect/iterations/Iteration5/image"
    prediction_key = "ec8007fd08174303a22d9e2b0e3ebfd2"
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream"
    }

    with open(filepath, 'rb') as img:
        response = requests.post(api_url, headers=headers, data=img)

    if response.status_code == 200:
        predictions = response.json().get('predictions', [])
        
        image = Image.open(filepath)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()  # Utilisation de la police par défaut pour éviter les problèmes de chargement

        for prediction in predictions:
            prob = prediction.get('probability', 0) * 100
            if prob > 50:  # Filtrer pour n'afficher que les prédictions avec probabilité > 50%
                box = prediction['boundingBox']
                left = box['left'] * image.width
                top = box['top'] * image.height
                width = box['width'] * image.width
                height = box['height'] * image.height

                draw.rectangle([left, top, left + width, top + height], outline="red", width=3)
                text = f"{prob:.2f}%"
                # Positionnement du texte ajusté pour éviter le chevauchement avec le rectangle
                draw.text((left, top - 15), text, fill="red", font=font)

        modified_filename = f"modified_{file.filename}"
        modified_filepath = os.path.join(app.config['UPLOAD_FOLDER'], modified_filename)
        image.save(modified_filepath)

        # Passer les prédictions au template result.html
        return render_template('result.html', image_path=url_for('uploaded_file', filename=modified_filename), predictions=predictions)
    else:
        return "Erreur lors de l'appel à l'API", 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)