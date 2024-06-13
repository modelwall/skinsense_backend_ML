from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import pytz

class Database:
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string)
        self.db = self.client['skinsense']
        self.users_collection = self.db['user_info']
        self.result_collection = self.db['scan_result']
        self.product_collection = self.db['product']

    def add_user(self, username, password, firstname, lastname, congenital, skintype):
        hashed_password = generate_password_hash(password)
        new_user = {
            'username': username,
            'password': hashed_password,
            'firstname' : firstname,
            'lastname' : lastname,
            'skintype' : skintype,
            'congenital' : congenital,
        }
        result = self.users_collection.insert_one(new_user)
        return result.inserted_id
    
    def save_result(self, image, email, predicted):
        # Get the timezone for Thailand
        thailand_timezone = pytz.timezone('Asia/Bangkok')
        # Get the current time and localize it to Thailand timezone
        current_time = datetime.now().astimezone(thailand_timezone)
        predicted_result = {
            'input_image': image,
            'username': email,
            'predicted': predicted,
            'timestamp': current_time,
        }
        result = self.result_collection.insert_one(predicted_result)
        return result.inserted_id

    def find_user_by_username(self, username):
        return self.users_collection.find_one({'username': username})

    def get_results_by_email(self, email):
        results = self.result_collection.find({'username': email})
        results_list = list(results)
        return results_list
    
    def get_account_detail(self, email):
        results = self.users_collection.find_one({'username': email})
        return results
    
    def get_recommend_product(self, message):
        results = self.product_collection.find({'recommend_type': message})
        results_list = list(results)
        return results_list
    
    def update_account(self, old_email, new_email, firstname, lastname, congenital):
        results = self.users_collection.update_one(
            {'username': old_email},
            {'$set': {'username': new_email, 'firstname': firstname, 'lastname': lastname, 'congenital': congenital}}
        )
        self.result_collection.update_many(
            {'username': old_email},
            {'$set': {'username': new_email}}
        )
        return results
    
    def change_password(self,email, new_password):
        hashed_password = generate_password_hash(new_password)
        results = self.users_collection.update_one(
            {'username': email},
            {'$set': {'password': hashed_password}}
        )
        return results
    
    def get_skintype(self, email):
        user = self.users_collection.find_one(
            {'username': email},
            {'skintype': 1, '_id': 0}  
        )
        if user:
            return user.get('skintype')  
        else:
            return None  
