from flask import Flask
import os
from flask_bcrypt import Bcrypt

# Initialize Flask app
app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
# Handle Render's DATABASE_URL
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Apply sslmode only for PostgreSQL
if db_uri.startswith('postgresql://'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'sslmode': 'require'}
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}

# Ensure static directories exist
base_dir = os.path.abspath(os.path.dirname(__file__))
static_dir = os.path.join(base_dir, '../static')  # Adjusted for root static/
os.makedirs(os.path.join(static_dir, 'images'), exist_ok=True)
os.makedirs(os.path.join(static_dir, 'videos'), exist_ok=True)
os.makedirs(os.path.join(static_dir, 'apks'), exist_ok=True)

# Initialize extensions
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Delay importing models and routes
def init_app():
    with app.app_context():
        from models import User
        db.create_all()
        # Create or reset master admin
        master_admin = User.query.filter_by(email='elvismalcom9@gmail.com').first()
        if master_admin:
            master_admin.password = bcrypt.generate_password_hash('Reddevil@256').decode('utf-8')
            master_admin.is_active = True
            db.session.commit()
        else:
            hashed_password = bcrypt.generate_password_hash('Reddevil@256').decode('utf-8')
            master_admin = User(
                username='elvis',
                email='elvismalcom9@gmail.com',
                password=hashed_password,
                is_admin=True,
                is_master=True,
                is_active=True
            )
            db.session.add(master_admin)
            db.session.commit()

from routes import *

if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))