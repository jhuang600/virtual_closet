from flask import Flask, request, jsonify, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configure the upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///closet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key_here'

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
    return render_template('index.html')

# Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        profile_picture = request.files.get('profile_picture')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Check if the email is already in use
        if User.query.filter_by(email=email).first():
            return 'Email is already in use', 400

        # Save profile picture
        if profile_picture and profile_picture.filename:
            filename = secure_filename(profile_picture.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(file_path)
            profile_picture_url = url_for('static', filename=f'uploads/{filename}')
        else:
            profile_picture_url = None    

        # Create new user
        user = User(name=name, email=email, password=hashed_password, profile_picture=profile_picture_url)
        db.session.add(user)
        db.session.commit()
        
        return redirect('/login')

    return render_template('register.html')

# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')

        return 'Invalid credentials'

    return render_template('login.html')

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
    result = [{'id': user.id, 'email': user.email} for user in users]
    return jsonify(result)

# Route to retrive all items
if __name__ == '__main__':
    app.run(debug=True)