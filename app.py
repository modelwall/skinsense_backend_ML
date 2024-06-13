from flask import Flask, Response, request, jsonify, session
from database import Database
from werkzeug.security import check_password_hash 
from io import BytesIO
import base64
from flask_cors import CORS, cross_origin
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
from bson import json_util



app = Flask(__name__)
app.secret_key = 'seniorskinsense'
db = Database('mongodb+srv://guynatthakan:153467Guy.@cluster0.ruyhjzt.mongodb.net/')
cors = CORS(app)

model = load_model('./Acne_model_V2.h5')
model2 = load_model('./Hyperpig_model.h5')  

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'prediction': "test1234"})

@app.route('/register', methods=['POST'])
def add_user():
    username = request.json.get('Email')
    password = request.json.get('Password')
    firstname = request.json.get('Firstname')
    lastname = request.json.get('Lastname')
    congenital = request.json.get('Congenital')
    skintype = request.json.get('Skintype')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = db.find_user_by_username(username)
    if user:
        return jsonify({'error': 'Username already exists'}), 400
    
    user_id = db.add_user(username, password, firstname, lastname, congenital, skintype)
    return jsonify({'message': 'User added successfully', 'user_id': str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('Email')
    password = request.json.get('Password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = db.find_user_by_username(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Store user's username in the session to indicate that the user is logged in
    session['username'] = username
    
    return jsonify({'message': 'Login successful'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    # Clear the user's session data to log them out
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/predict_acne', methods=['POST'])
def predict_acne():
    image_data = request.json.get('image')
    email = request.json.get('email')
    
    try:
        image_bytes = BytesIO(base64.b64decode(image_data))
        image_binary = base64.b64decode(image_data)
        
        img = Image.open(image_bytes)
        # Resize image to 224x224
        img = img.resize((224, 224))

        # Convert image to numpy array
        img_array = np.array(img)

        # Normalize pixel values to range [0, 1]
        img_array = img_array / 255.0

        # Expand dimensions to match model input shape
        img_array = np.expand_dims(img_array, axis=0)

        # Perform prediction
        prediction = model.predict(img_array)
        
        predicted_category = np.argmax(prediction)
        
        result_id = db.save_result(image_binary,email,int(predicted_category))
        
        # Return prediction result
        return jsonify({
            'result_id': str(result_id),
            'predicted_acne_level': int(predicted_category),
            'prediction_values': prediction.tolist()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/predict_hyper', methods=['POST'])
def predict_hyper():
    image_data = request.json.get('image')
    email = request.json.get('email')
    
    try:
        image_bytes = BytesIO(base64.b64decode(image_data))
        image_binary = base64.b64decode(image_data)
        
        img = Image.open(image_bytes)
        # Resize image to 224x224
        img = img.resize((224, 224))

        # Convert image to numpy array
        img_array = np.array(img)

        # Normalize pixel values to range [0, 1]
        img_array = img_array / 255.0

        # Expand dimensions to match model input shape
        img_array = np.expand_dims(img_array, axis=0)

        # Perform prediction
        prediction = model2.predict(img_array)
        
        predicted_category = np.argmax(prediction)
        
        # Adjust predicted_category values
        if predicted_category == 0:
            predicted_category = 7
        elif predicted_category == 1:
            predicted_category = 8
        elif predicted_category == 2:
            predicted_category = 9
        
        result_id = db.save_result(image_binary,email,int(predicted_category))
        
        # Return prediction result
        return jsonify({
            'result_id': str(result_id),
            'predicted_hyper_level': int(predicted_category),
            'prediction_values': prediction.tolist()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/get_results_by_email', methods=['POST'])
def get_results_by_email():
    try:
        # Get email from the request body
        email = request.json.get('email')

        # Query the predicted_result collection for documents with matching email
        results = db.get_results_by_email(email)
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            result['_id'] = str(result['_id'])

        # Return the list of matching documents as a JSON response
        return json_util.dumps({'results': results})

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 400
    
@app.route('/get_account_detail', methods=['POST'])
def get_account_detail():
    try:
        # Get email from the request body
        email = request.json.get('email')

        # Query the predicted_result collection for documents with matching email
        result = db.get_account_detail(email)
        
        if result:
            # Convert ObjectId to string for JSON serialization
            result['_id'] = str(result['_id'])
            return json_util.dumps({'result': result})
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 400
    
@app.route('/get_recommend_product', methods=['POST'])
def get_recommend_product():
    try:
        # Get email from the request body
        message = request.json.get('message')

        # Query the predicted_result collection for documents with matching email
        results = db.get_recommend_product(message)
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            result['_id'] = str(result['_id'])

        # Return the list of matching documents as a JSON response
        return json_util.dumps({'results': results})

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 400
    
@app.route('/update_account_detail', methods=['POST'])
def update_account_detail():
    try:
        # Get data from the request
        old_email = request.json.get('oldEmail')
        new_email = request.json.get('newEmail')
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')
        congenital = request.json.get('congenital')
        
        # Update user details in the database
        result = db.update_account(old_email,new_email,firstname,lastname,congenital)
        
        # Check if the update was successful
        if result.modified_count > 0:
            return jsonify({'message': 'Account detail updated successfully'}), 200
        else:
            return jsonify({'message': 'No account detail updated'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/change_password', methods=['POST'])
def change_password():
    try:
        # Get data from the request
        email = request.json.get('email')
        new_password = request.json.get('new_password')
        
        # Update Password
        result = db.change_password(email, new_password)
        
        # Check if the update was successful
        if result.modified_count > 0:
            return jsonify({'message': 'Password updated successfully'}), 200
        else:
            return jsonify({'message': 'No account found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/get_skintype', methods=['POST'])
def get_skintype():
    try:
        # Get data from the request
        email = request.json.get('email')
        
        # Get Skin Type
        skintype = db.get_skintype(email)
        
        # Check if the skin type was found
        if skintype:
            return jsonify({'skintype': skintype}), 200
        else:
            return jsonify({'message': 'No account found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)