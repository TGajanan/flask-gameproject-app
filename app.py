#import necessary modules
from flask import Flask, request, render_template, redirect,url_for, session,jsonify
# from jinja2 import escape
from pymongo import MongoClient
import random,secrets,os,random
import requests
import json
import string 
from bson import ObjectId 
from bson.objectid import ObjectId #for getting the user id
from urllib.parse import parse_qs #for reading the url link
#from gridfs import GridFS #to store the images in mogodb #pip install gridfs 
from flask import flash
from datetime import datetime
from gridfs import GridFS
import datetime
import string
import uuid
from bson.objectid import ObjectId
import pytz #python -m pip install pytz
from config import winners_needed


# rapid api url for msg to email
url = "https://rapidprod-sendgrid-v1.p.rapidapi.com/mail/send"

# define the mongodb client
client = MongoClient('mongodb://localhost:27017')
# client = MongoClient('mongodb+srv://gaja:gaja123@cluster0.jdoybcv.mongodb.net/gameproject')
# client = MongoClient('mongodb+srv://kinmartapplication:admin12345@cluster1.d6fwfh6.mongodb.net/gameproject')
db = client.gameproject
fs = GridFS(db)

application = Flask(__name__)
application.secret_key = 'admin'
# app.config['UPLOAD_FOLDER'] = 'static/img'
# app.static_folder = 'static'
application.config['UPLOAD_FOLDER'] = os.path.join(application.root_path, 'static', 'img')

def generate_user_id():
    return ObjectId()

local_tz = pytz.timezone('Asia/Kolkata')
# local_tz = pytz.timezone('Asia/Kolkata') 
# def get_current_time():
#     return datetime.datetime.now(local_tz)

@application.route('/', methods=["POST","GET"])
def home():
    user_id = session.get('user_id')
    print(user_id)
    collection1 = db['admindetails'] 
    products = collection1.find()  # Retrieve all products
    print(products)
    collection2 = db['winnersdetails'] 
    winners = collection2.find()
    print(winners)
    now = datetime.datetime.now(local_tz)
    print('hello time',now)
    user_in_gamedetails = False
    if user_id:
        user = db.userdetails.find_one({'_id': ObjectId(user_id)})   # Convert user_id to ObjectId
        print('user exist',user)
        if user:
            # Check if the user exists in the gamedetails collection
            if db.gamedetails.find_one({'user_id': user_id}):
                user_in_gamedetails = True
                print('exist in gamedetails',user)
            return render_template('home.html', user=user, logged_in=True, products=products,winners=winners,user_in_gamedetails=user_in_gamedetails,now=now,local_tz=local_tz,datetime=datetime)
    
    return render_template("home.html", products=products,winners=winners,logged_in=False,user_in_gamedetails=user_in_gamedetails,now=now,local_tz=local_tz,datetime=datetime)

'''@application.route('/', methods=["POST","GET"])
def home():
    collection1 = db['admindetails']
    products = collection1.find()
    collection2 = db['winnersdetails']
    winners = collection2.find()
    user_in_gamedetails = False

    user = db.userdetails.find_one({})  # Fetch the first user from the userdetails collection
    if user:
        user_id = str(user['_id'])  # Get the user_id from the user document
        # Check if the user exists in the gamedetails collection
        if db.gamedetails.find_one({'user_id': user_id}):
            user_in_gamedetails = True

    return render_template("home.html", user=user, logged_in=True, products=products, winners=winners, user_in_gamedetails=user_in_gamedetails)'''

@application.route('/login', methods=["POST", "GET"])
def login():
    # local_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(local_tz)
    # now=now,local_tz=local_tz,datetime=datetime
    print('hello time',now)
    collection = db['admindetails']
    products = collection.find()
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = db.userdetails.find_one({'email': email})
        # user_id = session.get('_id')
        print('Data fetched:', user)
        if user and user['password'] == password:
            msg = "User validated"
            session['email'] = email
            session['user_id'] = str(user['_id'])  # Store user_id in the session 
            # session['user_id'] = user_id
            print('Stored user_id in session')
            logged_in = True
            return render_template("home.html", msg=msg, success=0, logged_in=logged_in,user=True,products=products,now=now,local_tz=local_tz,datetime=datetime)
        else:
            msg = "Invalid credentials"
            return render_template("login.html", msg=msg, success=1,user=True,now=now,local_tz=local_tz)
    return render_template("login.html", user=True,now=now,datetime=datetime,local_tz=local_tz)

@application.route('/forgot_password', methods=["POST", "GET"])
def forgot_password():
    if request.method == "POST":
        email = request.form['email']
        # Generate a temporary password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        # to send the ranodm generated passowrd to Email
        payload = {
                        "personalizations": [
                            {
                                "to": [{"email": email}],
                                "subject": "Registration details"
                            }
                        ],
                        "from": {"email": "gajanantodetti1998@gmail.com"},
                        "content": [
                            {
                                "type": "text/plain",
                                "value": "Dear, \n Welcome to Kinmart e-commerce pvt.ltd,Your details to Login below \nYOUR Email:{} \n Your Password:{} \n Thank you for registering with us".format(email,temp_password)
                            }
                        ]
                    }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "ddf653f293msh0dfe49acf77f064p1bf374jsna9d592378c2f",
            "X-RapidAPI-Host": "rapidprod-sendgrid-v1.p.rapidapi.com"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        print(response.text)
        db.userdetails.update_one({'email': email}, {'$set': {'password': temp_password}})
        msg= "Password reset successful. Please check your email for the temporary password. "
        return render_template("login.html", success = 0, msg=msg)
    return render_template("forgot_password.html")

@application.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        password1 = request.form['password1']
        password2 = request.form['password2']
        user_referral_code = generate_referral_code(email)
        
        # Retrieve referral code from form input field or URL query parameter
        invite_referral_code = request.form.get('referral_code') or request.args.get('ref') or None
        
        # print(user_referral_code)
        # invite_referral_code = request.form['referral_code']  # Retrieve referral code from form input field
        # invite_referral_code1 = request.args.get('ref') 
        '''invite_referral_code = request.form['referral_code']
        print(invite_referral_code1)
        if not invite_referral_code1:
            invite_referral_code1 = request.args.get('ref')  # Retrieve referral code from URL query parameter
            if invite_referral_code1 is None:
                query_string = request.query_string.decode()
                parsed_query = parse_qs(query_string)
                invite_referral_code = parsed_query.get('ref', [None])[0]
        else:       
            invite_referral_code = request.form['referral_code']'''
        print("Final invite_referral_code:", invite_referral_code)
        collection = db['userdetails']
        if password1 != password2:
            msg = "Please check that the passwords do not match"
            print(msg)
            return render_template("newregister.html", msg=msg, success=1,user=True)

        if invite_referral_code:
            invite = collection.find_one({'user_referral_code': invite_referral_code})
            print('Data fetched:', invite)
            if invite is None or invite['user_referral_code'].lower() != invite_referral_code.lower():
                msg = "Invalid referral code!"
                print(msg)
                return render_template("newregister.html", msg=msg, success=1,user=True)
            
        # Continue with the registration process
        user = collection.find_one({'email': email, 'password': password1})
        print('Data fetched:', user)
        if user:
            msg = "This email already exists!"
            print(msg)
            return render_template("newregister.html", msg=msg, success=1,user=True)
        else:
            data = {
                'email': email,
                'password': password1,
                'mobile_number': mobile_number,
                'profileImage':" ",
                'user_referral_code': user_referral_code,
                'invite_referral_code': invite_referral_code
            }
            db.userdetails.insert_one(data)
            print(data)
            #sending otp to user
            # otp = generate_otp()
            # url = "https://www.fast2sms.com/dev/bulkV2"
            # querystring = {
            #     "authorization": "7MVEax6qnutB129z0QIGbhypZgmrPDNH3FdsJj48c5ReWvKSCipv5m1C0IxLWSqXKGtBesyrk7dFl3Vn",
            #     "variables_values": otp,
            #     "route": "otp",
            #     "numbers": mobile_number
            # }
            # headers = {
            #     'cache-control': "no-cache"
            # }
            # response = requests.request("GET", url, headers=headers, params=querystring)
            # response_text = response.text
            # data = json.loads(response_text)
            # message = data['message'][0]
            # session['otp'] = otp
            # print(message)
            # to send the welcome email
            ''' payload = {
                        "personalizations": [
                            {
                                "to": [{"email": email}],
                                "subject": "Registration details"
                            }
                        ],
                        "from": {"email": "gajanantodetti1998@gmail.com"},
                        "content": [
                            {
                                "type": "text/plain",
                                "value": "Dear, \n Welcome to Kinmart e-commerce pvt.ltd,Your details to Login below \nYOUR Email:{} \n Your Password:{} \n Thank you for registering with us".format(email,password1)
                            }
                        ]
                    }
            headers = {
                    "content-type": "application/json",
                    "X-RapidAPI-Key": "ddf653f293msh0dfe49acf77f064p1bf374jsna9d592378c2f",
                    "X-RapidAPI-Host": "rapidprod-sendgrid-v1.p.rapidapi.com"
                }
            response = requests.request("POST", url, json=payload, headers=headers)
            print(response.text)'''
            return render_template('login.html', success=0,user=True)
    return render_template("newregister.html", user=True)

# function is to generate a random 4-digit OTP
def generate_otp():
    return str(random.randint(1000, 9999))

# Generate a random 4-byte string
def generate_referral_code(email):
    random_string = secrets.token_hex(4)  
    referral_code = f'{email}_{random_string}'
    print(referral_code)
    return referral_code

#To verify the user number with Opt Verifications
@application.route('/verify', methods=["POST","GET"])
def verify():
    if request.method == "POST":
        user_otp = request.form['otp']
        if user_otp == session.get('otp'):
            return render_template("login.html",msg='OTP Verified! Please Login',success=0,user=True)
        else:
            return render_template("verifyotp.html",msg='OTP Verification failed!',success=1)
    return render_template("verifyotp.html")

#rout for user profile checking 
@application.route('/myprofile', methods=["GET", "POST"])
def myprofile():
    user_id = session.get('user_id')
    print(user_id)
    if user_id:
        user = db.userdetails.find_one({'_id': ObjectId(user_id)})  # Convert user_id to ObjectId
        print(user)
        if user:
            invite_referral_code = user['user_referral_code']
            referred_users = db.userdetails.find({'invite_referral_code': invite_referral_code})
            return render_template('new_profile.html', user=user, referred_users=referred_users, loggedin=True)
    return render_template('new_profile.html',loggedin=True)

#route for user profile edit
@application.route('/editprofile/<string:user_id>', methods=["POST","GET"])
def edit_profile(user_id):
    msg=""
    user_id = session.get('user_id')
    user = db.userdetails.find_one({'_id': ObjectId(user_id)})
    # user = db.userdetails.find_one({'_id': user_id})
    if request.method=="POST":
        file = request.files['profileImage']
        fname=request.form['fname']
        lname=request.form['lname']
        email=session.get('email')
        mobile_number=request.form['mobile_number']
        pincode=request.form['pincode']
        address=request.form['address']
        country=request.form['country']
        state=request.form['state']
        filename = file.filename
        if file:
            file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        print('File uploaded successfully')
        db.userdetails.update_one({'email': email}, {'$set': {'profileImage': filename,'fname':fname,'lname':lname,"mobile_number":mobile_number,"pincode":pincode,"address":address,"country":country,"state":state}})
        user = db.userdetails.find_one({'email': email})
        msg="user profile updated"
        print(msg)
        return render_template("new_profile.html",msg=msg, user=user,email=email,fname=fname,lname=lname,mobile_number=mobile_number,pincode=pincode,address=address,country=country,state=state,success = True)
    return render_template("new_profile.html",msg=msg,logged_in=True, user=user)

#to update the passoword in user profile whic is in local 
@application.route('/update_password/<string:user_id>', methods=["POST", "GET"])
def update_password(user_id):
    msg=""
    user_id = session.get('user_id')
    user = db.userdetails.find_one({'_id': ObjectId(user_id)})
    if request.method == "POST":
        password = request.form['password']
        new_password1 = request.form['new_password1']
        new_password2 = request.form['new_password2']
        if new_password1 == new_password2:
            email = session.get('email')
            user = db.userdetails.find_one({'email': email})
            if user and user['password'] == password:
                db.userdetails.update_one({'email': email}, {'$set': {'password': new_password1}})
                msg = "Password updated successfully"
                return render_template("new_profile.html", msg=msg, success=0,password=password,new_password1=new_password1,new_password2=new_password2, user=user)
            else:
                msg = "Incorrect old password"
                return render_template("new_profile.html", msg=msg, success=1, user=user)
        else:
            msg = "New passwords do not match"
            return render_template("new_profile.html", msg=msg, success=1)
    return render_template("new_profile.html",msg=msg,logged_in=True, user=user)

#to update the passoword in user profile whic is in in mongodb atlas Grif Fs not not compltely
'''@application.route('/products', methods=["POST", "GET"])
def products():
    if request.method == "POST":
        file = request.files['productImage']
        pname = request.form['pname']
        priceofproduct = request.form['priceofproduct']
        eventdate = request.form['eventDate']
        eventtime = request.form['eventTime']
        eventtimeperiod = request.form['eventTimePeriod']
        session['email'] = session['email']  # Preserve admin email in session
        session['user_id'] = session['user_id']  # Preserve admin user_id in session
        
        if file:
             # Store the image in GridFS
            fs = MongoClient().db_name.fs
            file_id = fs.put(file, filename=filename)  # Use the file ID as the filename
        else:
            print('File uploaded, no images uploaded')
            msg = 'File uploaded, no images uploaded'
            return render_template("products.html", msg=msg, success=1)
        
        data = {
            'productImage': str(file_id),
            'pname': pname,
            'priceofproduct': priceofproduct,
            'eventdate': eventdate,
            'eventtime': f"{eventtime} {eventtimeperiod}"
        }
        
        db.admindetails.insert_one(data)
        print(data)
        print('File uploaded successfully')
        msg = 'File uploaded successfully'
        # return redirect(url_for("admin_home",msg=msg, success=1))
        return render_template("admin_home.html",admin=True, msg=msg, success=0)
    
    return render_template("products.html")
    
#grid FS image retrival
@application.route('/image/<file_id>')
def image(file_id):
    fs = gridfs.GridFS(db)
    grid_fs_file = fs.get(ObjectId(file_id))
    response = make_response(grid_fs_file.read())
    response.headers['Content-Type'] = 'image/jpeg'  # Modify the content type according to your image format
    return response'''

#adding products to display in Dashboard
@application.route('/products', methods=["POST", "GET"])
def products():
    now = datetime.datetime.now(local_tz)
    collection = db['admindetails']
    products = collection.find()
    if request.method == "POST":
        file = request.files['productImage']
        pname = request.form['pname']
        priceofproduct = request.form['priceofproduct']
        eventdate = request.form['eventDate']
        eventtime = request.form['eventTime']
        # eventtimeperiod = request.form['eventTimePeriod']
        winners_needed_value = int(request.form['winnersNeeded'])  
        winners_needed_value = max(1, winners_needed_value)  # Ensure winners_needed is at least 1
        # Update the winners_needed value in the config.py file
        with open('config.py', 'w') as f:
            f.write(f"winners_needed = {winners_needed_value}")
        filename = file.filename
        session['email'] = session['email']  # Preserve admin email in session
        session['user_id'] = session['user_id']  # Preserve admin user_id in session
        if file:
            file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        else:
            print('File uploaded, no images uploaded')
            msg = 'File uploaded, no images uploaded'
            return render_template("products.html", msg=msg, success=1)
          # Extracting 12-hour time format from eventtime
        eventtime_obj = datetime.datetime.strptime(eventtime, "%H:%M").time()
        eventtime_12hr = eventtime_obj.strftime("%I:%M %p")
        
        data = {
            'productImage': filename,
            'pname': pname,
            'priceofproduct': priceofproduct,
            'eventdate': eventdate,
            'eventtime': eventtime_12hr,
            'winners_needed': winners_needed_value
        }
        
        db.admindetails.insert_one(data)
        print(data)
        print('File uploaded successfully')
        msg = 'File uploaded successfully'
        # return redirect(url_for("admin_home",msg=msg, success=1))
        return render_template("admin_home.html", msg=msg, success=0,admin=True,products=products,now=now,local_tz=local_tz,datetime=datetime)
    return render_template("products.html", admin=True, add=True)

@application.route('/delete_event/<string:_id>', methods=['POST'])
def delete_event(_id):
    
    collection = db['admindetails']
     # Convert the _id to ObjectId
    object_id = ObjectId(_id)
    # Delete the product document based on the _id field
    result = collection.delete_one({'_id': object_id})
    # Delete the product with the given product_id
    result = collection.delete_one({'_id': _id})
    if result.deleted_count == 1:
        print('Product deleted successfully')
    else:
        print('Product not found')
    return redirect(url_for('admin_home'))

@application.route('/update_event/<string:_id>', methods=['GET', 'POST'])
def update_event(_id):
    collection = db['admindetails']
    # Convert the _id to ObjectId
    object_id = ObjectId(_id)
    
    if request.method == "POST":
        # Retrieve the form data
        pname = request.form['pname']
        priceofproduct = request.form['priceofproduct']
        eventdate = request.form['eventDate']
        eventtime = request.form['eventTime']
        winners_needed_value = int(request.form['winnersNeeded'])
        winners_needed_value = max(1, winners_needed_value)  # Ensure winners_needed is at least 1
        # Update the winners_needed value in the config.py file
        with open('config.py', 'w') as f:
            f.write(f"winners_needed = {winners_needed_value}")
        # Check if the 'productImage' field exists in the form data
        if 'productImage' in request.files:
            file = request.files['productImage']
            filename = file.filename
            # Save the file if it exists
            if file:
                file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        else:
            filename = ""  # Set an empty string if 'productImage' is not present
        
        # Extracting 12-hour time format from eventtime
        eventtime_obj = datetime.datetime.strptime(eventtime, "%H:%M").time()
        eventtime_12hr = eventtime_obj.strftime("%I:%M %p")
        
        # Perform the update operation using the form data
        result = collection.update_one(
            {'_id': object_id},
            {'$set': {
                'productImage': filename,
                'pname': pname,
                'priceofproduct': priceofproduct,
                'winnersNeeded': winners_needed_value,
                'eventDate': eventdate,
                'eventTime': eventtime_12hr
            }}
        )
        
        if result.modified_count == 1:
            print('Product updated successfully')
            return redirect(url_for('admin_home', success=0, msg='Product updated successfully'))
        else:
            print('Product not found')
            return redirect(url_for('admin_home', success=1, msg='Product not found'))
    
    # else:
    #     # Retrieve the document from the MongoDB collection based on the _id
    document = collection.find_one({'_id': object_id})
        # Pass the document data to the update form template
    return render_template('products.html', document=document, admin=True, update=True)



#admin register
@application.route('/adminregister', methods=["POST", "GET"])
def adminregister():
    if request.method == "POST":
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        securitykey = request.form['securitykey']
        collection = db['userdetails']
        admin = collection.find_one({'email': email})
        if admin:
            msg='Email Already Exist!'
            return render_template('newregister.html',admin=True, msg=msg, success= 1)     
        data = {'email': email,
                'mobile_number': mobile_number,
                'securitykey': securitykey}
        db.userdetails.insert_one(data)
        print('Admin registered successfully ')
        msg='Admin registered successfully !'
        return render_template('login.html',admin=True, msg=msg,success= 0) 
    return render_template('newregister.html',admin=True)     

#admin login
@application.route('/adminlogin', methods=["POST", "GET"])
def adminlogin():
    now = datetime.datetime.now(local_tz)
    collection = db['admindetails']
    products = collection.find()

    if request.method == "POST":
        email = request.form['email']
        securitykey = request.form['securitykey']
        user = db.userdetails.find_one({'email': email})
        if user and user['securitykey'] == securitykey:
            msg = 'User validated'
            session['email'] = email
            session['user_id'] = str(user['_id'])
            return render_template("admin_home.html", admin=True, products=products, msg=msg, success=0,now=now,local_tz=local_tz,datetime=datetime)
        else:
            msg = 'Invalid credentials'
            return render_template("login.html", admin=True, msg=msg, success=1)

    return render_template("login.html", admin=True)

#admin dashboard
@application.route('/admin')
def admin_home():
    now = datetime.datetime.now(local_tz)
    user_id = session.get('user_id')
    collection = db['admindetails']
    products = collection.find()
    if user_id:
        user = db.userdetails.find_one({'_id': ObjectId(user_id)})
        if user:
            return render_template('admin_home.html', user=user, logged_in=True, products=products, admin=True,now=now,local_tz=local_tz,datetime=datetime)
    return render_template('admin_home.html', products=products, admin=True,now=now,local_tz=local_tz,datetime=datetime)

# ***************************************************Game code Starts*******************************************
@application.route('/leaderboard', methods=["POST","GET"])
def leaderboard():
    collection2 = db['winnersdetails'] 
    winners = collection2.find()
    return render_template('leaderboard.html',winners=winners)
# Set the winners_needed value
# winners_needed = 1

# Function to update live players list
live_players = []

def update_live_players(user_id):
    if user_id not in live_players:
        live_players.append(user_id)

@application.route('/gamepage', methods=['POST', 'GET'])
def gamepage():
    user_id = session.get('user_id')
    session['user_id'] = user_id

    # Retrieve the level from the session if it exists
    level = session.get('level')
    if not level:
        session['level'] = 1
        level = 1

    user_id = session['user_id']

    # Update the live_players list with the active user ID
    update_live_players(user_id)

    level_text = ""  # Initialize level_text with a default value

    if level == 1:
        level_text = "Level 1"
    elif level == 2:
        level_text = "Level 2"
    elif level == 3:
        level_text = "Level 3"

    reset_message = session.pop('reset_message', None)

    # Retrieve gamedetails for the specific user from MongoDB
    gamedetails = list(db.gamedetails.find({'user_id': user_id}))

    # Fetch the gamelevel from the latest gamedetails document
    gamelevel = gamedetails[-1]['gamelevel'] if gamedetails else 0

    # Check if the user has completed all three levels
    is_game_finished = gamelevel >= 3

    disable_button = False

    if gamedetails:
        latest_gamedetail = gamedetails[-1]
        winner_status = latest_gamedetail.get('winner', False)

        # Disable the button if the game level is 3 and the user has not completed the previous level
        if gamelevel > 1 and not winner_status:
            disable_button = True

        # Disable the button if the user is not a winner in level 2
        if gamelevel == 2 and not winner_status:
            disable_button = True

    # Check if the winners_needed requirement is fulfilled
    winners_count = db.gamedetails.count_documents({'user_id': user_id, 'winner': True})
    if gamelevel == 3 and winners_count >= winners_needed:
        disable_button = True

        # Store user details in the winnersdetails collection
        user_details = db.userdetails.find_one({'_id': ObjectId(user_id)})
        if user_details:
            # Check if winner's details already exist
            existing_winner = db.winnersdetails.find_one({'_id': user_details['_id']})
            if existing_winner:
                print("Winner's details already exist.")
            else:
                winner_data = {
                    '_id': uuid.uuid4().hex,  # Generate a unique _id using UUID
                    **user_details,
                    'winners_count': winners_count,
                    'timestamp': datetime.datetime.now()
                }
                db.winnersdetails.insert_one(winner_data)
        else:
            print("User details not found for user_id:", user_id)

    # Store the winner status in the session
    session['winner_status'] = winner_status if 'winner_status' in locals() else False

    print(live_players)
    print('usercount is here', len(live_players))

    return render_template("gamepage.html", session=session, level_text=level_text, reset_message=reset_message, gamedetails=gamedetails, is_game_finished=is_game_finished, disable_button=disable_button)


@application.route('/next-level')
def next_level():
    user_id = session['user_id']
    gamedetails = list(db.gamedetails.find({'user_id': user_id, 'gamelevel': {'$lte': session['level']}}))
    session['level'] += 1

    # Check if the user has completed the previous level
    if session['level'] > 2:
        previous_level_winner = any(g['winner'] for g in gamedetails if g['gamelevel'] == session['level'] - 1)
        if not previous_level_winner:
            return redirect(url_for('gamepage'))

    # Check if the current level is 3 and the winners count is less than the winners needed
    if session['level'] == 3 and len(live_players) > winners_needed:
        winners_count = sum(1 for g in gamedetails if g['winner'])
        if winners_count < winners_needed:
            return redirect(url_for('gamepage'))

    return render_template('gamepage.html', gamedetails=gamedetails)


@application.route('/shuffle/<int:gamelevel>/<int:index>', methods=['POST'])
def shuffle(gamelevel, index):
    if 'level' not in session:
        session['level'] = 1

    array = determine_initial_array(session['level'])
    shuffled_values = shuffle_array(array)
    flipped_values = shuffled_values[:]  # Make a copy of shuffled_values
    user_id = session['user_id']

    winners_count = db.gamedetails.count_documents({'user_id': user_id, 'winner': True})  # Count the number of winners for the current user

    # Check if the game level is 3 and the required number of winners is already reached
    if gamelevel == 3 and winners_count >= determine_winner_count(gamelevel):
        winner = False
    else:
        # Determine winner using determine_winners() function
        winner = determine_winners(flipped_values, index)

        # Increment the winners count if the user is a winner
        if winner:
            winners_count += 1

    # Inserting the user clickable event and userdetails details
    click_data = {
        'user_id': user_id,
        'gamelevel': gamelevel,
        'index': index,
        'flipped_values': flipped_values,
        'timestamp': datetime.datetime.now(),
        'winner': winner
    }
    db.gamedetails.insert_one(click_data)

    # Check if the user has cleared the current level
    if determine_winner_count(gamelevel) == winners_count:
        if gamelevel < 3:
            session['level'] += 1
            reset_message = get_congratulations_message(gamelevel)
            session['reset_message'] = reset_message
            return jsonify({'redirect': '/next-level'})  # Redirect to next level
        else:
            user_details = db.userdetails.find_one({'_id': ObjectId(user_id)})
            if user_details:
                winner_data = {**user_details, **click_data}
                winner_data['_id'] = ObjectId()
                db.winnersdetails.insert_one(winner_data)
            else:
                print("User details not found for user_id:", user_id)
                db.winners.insert_one(click_data)
            reset_message = get_congratulations_message(gamelevel)
            session['reset_message'] = reset_message

    response = {
        'shuffled_array': shuffled_values,
        'flipped_values': flipped_values,
        'winner': winner,
        'current_step': session['level']
    }

    return jsonify(response)


def determine_initial_array(level):
    if level == 1:
        return ['in', 'in', 'in', 'in', 'in', 'out']
    elif level == 2:
        return ['in', 'in', 'in', 'in', 'out', 'out']
    elif level == 3:
        return ['in', 'in', 'in', 'out', 'out', 'out']
    else:
        # Return a default array if an invalid level is provided
        return ['in', 'in', 'in', 'out', 'out', 'out']

def shuffle_array(array):
    random.shuffle(array)
    return array

def determine_winner_count(level):
    if level == 1:
        return 10
    elif level == 2:
        return 10
    elif level == 3:
        return 10

def determine_winners(array, index):
    if array[index] == 'in':
        return True
    return False

def generate_user_id():
    return str(uuid.uuid4())

def get_congratulations_message(level):
    if level == 1:
        return "Congratulations! You have cleared level 1. Proceed to level 2."
    elif level == 2:
        return "Congratulations! You have cleared level 2. Proceed to level 3."
    elif level == 3:
        return "Congratulations! You have cleared all levels. You are the ultimate winner!"

#logout function
@application.route('/logout')
def logout():
    now = datetime.datetime.now(local_tz)
    collection = db['admindetails']
    products = collection.find()
    session.pop('email', None)
    session.pop('user_id', None)
    session.pop('level', None)
    session.pop('reset_message', None)
    session.pop('winner_status', None)
    return render_template('home.html',products=products,now=now,local_tz=local_tz,datetime=datetime)

# start the flask server
if __name__ == '__main__':
    application.run(debug=True, host="0.0.0.0")