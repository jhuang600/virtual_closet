from flask import Flask, request, jsonify, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
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

# Initialize the database
db = SQLAlchemy(app)

# Define the database model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200))

# create database
with app.app_context():
    db.create_all()

# route to render the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route to add a new item
@app.route('/upload', methods=['POST'])
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
    new_item = Item(name=name, category=category, color=color, image_url=url_for('static', filename=f'uploads/{filename}'))
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': 'Item added successfully!', 'image_url': file_path})   

# Route to retrieve all items
@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    result = [{'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color,  'image_url': item.image_url} for item in items]
    return jsonify(result)    

@app.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    item = Item.query.get_or_404(id)
    return jsonify({
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'color': item.color,
        'image_url': item.image_url
    })

# Route to delete an item by id
@app.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get_or_404(id) 
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': "Item deleted successfully"})    

# Route to update an item's details
@app.route('/items/<int:id>', methods=['PUT'])
def update_item(id):
    item = Item.query.get_or_404(id)

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

# def update_item(id):
#     item = Item.query.get_or_404(id)
#     data = request.json
#     item.name = data.get('name', item.name)
#     item.category = data.get('category', item.category)
#     item.color = data.get('color', item.color)
#     db.session.commit()
#     return jsonify({'message': 'Item updated successfully'})

# Route to search for items by name, category and color
@app.route('/items/search', methods=['GET'])
def search_items():
    name = request.args.get('name', '').lower()
    category = request.args.get('category', '').lower()
    color = request.args.get('color', '').lower()

    # start with all item
    query = Item.query

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



# Route to retrive all items
if __name__ == '__main__':
    app.run(debug=True)
