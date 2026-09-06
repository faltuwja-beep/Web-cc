import os
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string("<h1>🚀 Cyber Store is Live and Working!</h1><p>Bina kisi error ke successfully chal raha hai.</p>")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
