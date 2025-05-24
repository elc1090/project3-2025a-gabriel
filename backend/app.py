from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or f'sqlite:///{os.path.join(app.instance_path, "desenho_local.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class DrawingBoard(db.Model):
    __tablename__ = 'drawing_board'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    strokes = db.relationship('Stroke', backref='board', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<DrawingBoard id={self.id} name={self.name}>'

class Stroke(db.Model):
    __tablename__ = 'stroke' # Nome explícito da tabela

    id = db.Column(db.Integer, primary_key=True)
    drawing_board_id = db.Column(db.Integer, db.ForeignKey('drawing_board.id'), nullable=False)
    
    color = db.Column(db.String(7), nullable=False) # Ex: #RRGGBB
    line_width = db.Column(db.Float, nullable=False)
    
    points_json = db.Column(db.Text, nullable=False) # [{"x":10,"y":20},{"x":12,"y":22}, ...]

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow) # Quando o traço foi concluído/salvo

    def __repr__(self):
        return f'<Stroke id={self.id} board_id={self.drawing_board_id} color={self.color}>'

@app.route('/')
def home():
    return "Backend Flask com SQLAlchemy e modelos DrawingBoard/Stroke."

@app.route('/api/status')
def status_api():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = "conectado"
    except Exception as e:
        db_status = f"desconectado ({type(e).__name__}: {e})"
    return jsonify(message="API Flask está rodando!", database_status=db_status)


if __name__ == '__main__':
    app.run(debug=True)