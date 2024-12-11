from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

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

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# Route to add a new item
@app.route('/items', methods=['POST'])
def add_item():
    data = request.json
    new_item = Item(name=data['name'], category=data['category'], color=data['color'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item added successfully!'})    

# Route to retrieve all items
@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    result = [{'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color} for item in items]
    return jsonify(result)    

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
    data = request.json
    item.name = data.get('name', item.name)
    item.category = data.get('category', item.category)
    item.color = data.get('color', item.color)
    db.session.commit()
    return jsonify({'message': 'Item updated successfully'})

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
    result = [{'id': item.id, 'name': item.name, 'category': item.category, 'color': item.color} for item in items] 
    return jsonify(result)   



# Route to retrive all items
if __name__ == '__main__':
    app.run(debug=True)
