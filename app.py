# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ENCRYPTED_FOLDER'] = 'encrypted/'

# Set the encryption key (ideally, this should be fetched securely from a key management service)
encryption_key = b'0123456789abcdef0123456789abcdef'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENCRYPTED_FOLDER'], exist_ok=True)

# Function to encrypt a file
def encrypt_file(file_path, encrypted_path):
    # Read the file contents
    with open(file_path, 'rb') as f:
        plaintext = f.read()

    # Create a cipher object for AES encryption
    backend = default_backend()
    cipher = Cipher(algorithms.AES(encryption_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()

    # Add padding to the plaintext
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    # Encrypt the padded file contents
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    # Write the encrypted file
    with open(encrypted_path, 'wb') as f:
        f.write(ciphertext)

# Function to check if user is logged in
def is_logged_in():
    return 'username' in session

# Route for the home page
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    encrypted_files = os.listdir(app.config['ENCRYPTED_FOLDER'])
    return render_template('index.html', encrypted_files=encrypted_files)

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username and password are correct (you can replace this with a database lookup)
        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html', error=None)

# Route for uploading a file
@app.route('/upload', methods=['POST'])
def upload_file():
    if not is_logged_in():
        return redirect(url_for('login'))

    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], filename + '.encrypted')
        encrypt_file(upload_path, encrypted_path)

        # Remove the original file after encryption
        os.remove(upload_path)

    return redirect(url_for('home'))

# Route for downloading a file
@app.route('/download/<filename>')
def download_file(filename):
    if not is_logged_in():
        return redirect(url_for('login'))

    encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], filename)
    decrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], filename[:-10])  # Remove '.encrypted' from the filename

    decrypt_file(encrypted_path, decrypted_path)

    return send_file(decrypted_path, as_attachment=True)

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

