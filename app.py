from flask import Flask, request, jsonify
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
    return "Backend server is running!"

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

# Route to retrive all items
if __name__ == '__main__':
    app.run(debug=True)
