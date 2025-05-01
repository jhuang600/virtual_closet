from flask import Flask, request, jsonify, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer
import os
import json

app = Flask(__name__)

# Configure the upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///closet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'jessica.huang200@gmail.com'  
app.config['MAIL_PASSWORD'] = 'atsrqbuzorddludr'     
app.config['MAIL_DEFAULT_SENDER'] = 'jessica.huang200@gmail.com'
# Secret key for session management
app.config['SECRET_KEY'] = '1fHGjHqTyA3n5FtZ_lC7PqE0qzP7H0UdK_OZs7kXISk'

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize the database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)
    confirmed = db.Column(db.Boolean, default=False)

# Define the database model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# create database
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))    

# route to render the homepage
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/closet')
    return redirect('/all-users')

@app.route('/closet', methods=['GET'])
@login_required
def closet():
    items = Item.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', user=current_user, items=items)

# Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form inputs
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        profile_picture = request.files.get('profile_picture')

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            error = 'Email is already in use. Please try another email.'
            return render_template('register.html', error=error)

        # Save the profile picture using save_file
        profile_picture_path, error = save_file(profile_picture, app.config['UPLOAD_FOLDER'])
        if error:  # If file saving failed, use the default avatar
            profile_picture_path = 'default-avatar.png'

        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'profile_picture': profile_picture_path
        }
        token = serializer.dumps(json.dumps(user_data), salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        body = f'Hi {name}, confirm your email: {confirm_url}'

        try:
            send_email(email, 'Confirm your email for MyCloset', body)
            return redirect('/login')
        except Exception as e:
            print("Email sending failed:", e)
            return render_template('register.html', error="Failed to send confirmation email.")

    return render_template('register.html', error=None)


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        user_data = json.loads(serializer.loads(token, salt='email-confirm', max_age=3600))
    except Exception:
        return 'Invalid or expired confirmation link.'

    if User.query.filter_by(email=user_data['email']).first():
        return 'This email is already confirmed.'

    new_user = User(
        name=user_data['name'],
        email=user_data['email'],
        password=user_data['password'],
        profile_picture=url_for('static', filename=user_data['profile_picture']),
        confirmed=True
    )

    db.session.add(new_user)
    db.session.commit()

    return 'Your account has been verified! You can now log in.'


def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to

    with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)


def save_file(file, upload_folder):
    if not file or file.filename == '':
        return None, 'No selected file'
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    try:
        file.save(file_path)
        return f'uploads/{filename}', None
    except Exception as e:
        print(f"Error saving file: {e}")
        return None, 'Failed to upload file'

# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error to avoid UnboundLocalError

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.confirmed:
                error = 'Please confirm your email before logging in.'
            elif check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                error = 'Incorrect password. Please try again.'
        else:
            error = 'Email not found. Please register first.'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# Route to add a new item
@app.route('/upload', methods=['POST'])
@login_required
def upload_item():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Securely save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Retrieve form data (name, category, and color)
    name = request.form.get('name')
    category = request.form.get('category')
    color = request.form.get('color')

    # Save item details and image URL to the database
    new_item = Item(name=name, category=category, color=color, image_url=url_for('static', filename=f'uploads/{filename}'), user_id=current_user.id)
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': 'Item added successfully!', 'image_url': file_path})   

# Route to retrieve all items
@app.route('/items', methods=['GET'])
@login_required
def get_items():
    items = Item.query.filter_by(user_id=current_user.id).all()
    result = [{'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color, 'image_url': item.image_url} for item in items]
    return jsonify(result)    

@app.route('/items/<int:id>', methods=['GET'])
@login_required
def get_item(id):
    item = Item.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return jsonify({'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color, 'image_url': item.image_url})

# Route to delete an item by id
@app.route('/items/<int:id>', methods=['DELETE'])
@login_required
def delete_item(id):
    item = Item.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'})   

# Route to update an item's details
@app.route('/items/<int:id>', methods=['PUT'])
@login_required
def update_item(id):
    item = Item.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Update text fields
    name = request.form.get('name', item.name)
    category = request.form.get('category', item.category)
    color = request.form.get('color', item.color)
    item.name = name
    item.category = category
    item.color = color

    # Handle file upload if a new image is provided
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            item.image_url = url_for('static', filename=f'uploads/{filename}')

    db.session.commit()
    return jsonify({'message': 'Item updated successfully'})

@app.route('/items/search', methods=['GET'])
def search_items():
    name = request.args.get('name', '').lower()
    category = request.args.get('category', '').lower()
    color = request.args.get('color', '').lower()

    # start with all item
    query = Item.query.filter_by(user_id=current_user.id)

    # filter
    if name:
        query = query.filter(Item.name.ilike(f"%{name}%"))

    if category:     
        query = query.filter(Item.category.ilike(f"%{category}%"))

    if color: 
        query = query.filter(Item.color.ilike(f"%{color}%"))

    items = query.all()
    result = [{'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color, 'image_url': item.image_url} for item in items] 
    return jsonify(result)   

@app.route('/all-users', methods=['GET'])
def all_users():
    users = User.query.all()
    return render_template('all_users.html', users=users)

@app.route('/user/<int:user_id>', methods=['GET'])
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    items = Item.query.filter_by(user_id=user_id).all()
    return render_template('user_profile.html', user=user, items=items)

# Route to retrive all items
if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')