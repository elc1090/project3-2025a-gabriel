from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1) # SQLAlchemy prefere postgresql://

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///./desenho_local.db' # Fallback para SQLite local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa warnings desnecessários

db = SQLAlchemy(app)

class UserTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<UserTest {self.username}>'

# --- Rotas da API ---
@app.route('/')
def home():
    return "Olá do Backend Flask com SQLAlchemy configurado!"

@app.route('/api/status')
def status_api():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = "conectado"
    except Exception as e:
        db_status = f"desconectado ({e})"
    return jsonify(message="API Flask está rodando!", database_status=db_status)

@app.route('/dev/create_tables')
def create_tables_dev():
    if app.debug:
        try:
            with app.app_context():
                db.create_all()
            return "Tabelas criadas (se não existiam)!"
        except Exception as e:
            return f"Erro ao criar tabelas: {e}"
    return "Comando não permitido fora do modo debug.", 403


if __name__ == '__main__':
    #  with app.app_context():
    #      db.create_all()
    app.run(debug=True)