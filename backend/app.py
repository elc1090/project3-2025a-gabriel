from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello do Backend Flask"

@app.route('/api/hello')
def hello_api():
    return jsonify(message="Hello API do Flask")

if __name__ == '__main__':
    app.run(debug=True)