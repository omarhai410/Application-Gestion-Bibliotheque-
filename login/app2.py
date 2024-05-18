import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session
from pymongo import MongoClient
from bson import ObjectId
import smtplib
import json
from email.message import EmailMessage
app = Flask(__name__)

# Configure MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['LIB']
collection = db['adherent']
livre = db['livre']
discussion = db['discussion']
app.config['UPLOAD_FOLDER'] = 'C:/nosql/login/static'
app.secret_key = os.urandom(24)


@app.route('/')
def index():
  return render_template('login.html')


@app.route('/signup2')
def inscription():
  return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
  if request.method == 'POST':
    # Retrieve form data
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    telephone = request.form['telephone']
    cne = request.form['cne']
    cin = request.form['cin']
    occupation = request.form['occupation']
    password = request.form['password']

    # Insert data into the "adherent" collection
    user_data = {
      'name': name,
      'surname': surname,
      'email': email,
      'telephone': telephone,
      'cne': cne,
      'cin': cin,
      'occupation': occupation,
      'password': password,
    }

    collection.insert_one(user_data)

    return "User registered successfully!"


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = collection.find_one({'email': email, 'password': password})

        if user:
            occupation = user.get('occupation')
            username = user.get('name')

            # Stocker les informations dans la session
            session['username'] = username
            session['cin'] = user.get('cin', '')
            session['telephone'] = user.get('telephone', '')
            session['email'] = user.get('email', '')  # Add this line to store the email

            if occupation == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))

        return render_template('login.html', cin=session.get('cin', ''), telephone=session.get('telephone', ''))
@app.route('/logout')
def logout():
    # Check if the user is logged in
    if 'username' in session:
        # Get the username from the session
        username = session['username']

        # Update the user's record with the current logout date
        logout_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.update_one({'name': username}, {'$set': {'logout_date': logout_date}})

        # Clear the session data
        session.clear()

    # Redirect to the login page
    return redirect(url_for('index'))

@app.route('/user_details')
def user_details():
    # Get the logout date for the user "MIMOUNE" from the database
    user_info2 = collection.find_one({'name': 'MIMOUNE'}, {'_id': 0, 'logout_date': 1})

    # Convert the logout_date to a readable format (if it exists)
    if 'logout_date' in user_info2:
        user_info2['logout_date'] = datetime.strptime(user_info2['logout_date'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

    # Render the template with the user information
    return render_template('user.html', user_infos=user_info2)

@app.route('/admin_dashboard')
def admin_dashboard():
    cin = session.get('cin', '') if 'cin' in session else ''
    telephone = session.get('telephone', '')
    return render_template('admin.html', cin=cin, telephone=telephone)



@app.route('/modify_books', methods=['POST'])
def modify_books():
  if request.method == 'POST':
    # Récupérer les données du formulaire pour la modification de livre
    titre = request.form['titreModif']
    auteur = request.form['auteurModif']

    # Rechercher des livres dans la base de données en fonction du titre et de l'auteur
    results = livre.find({'titre': titre, 'auteur': auteur})

    return render_template('admin.html', results=results)

  return render_template('admin.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
  if request.method == 'POST':
    titre = request.form['titre']
    auteur = request.form['auteur']
    sommaire = request.form['sommaire']
    nbr_pages = int(request.form['nbr_pages'])
    categorie = request.form['categorie']
    source = request.form['source']
    quantite = int(request.form['quantite'])

    book_data = {
      'titre': titre,
      'auteur': auteur,
      'sommaire': sommaire,
      'nbr_pages': nbr_pages,
      'categorie': categorie,
      'source': source,
      'quantite': quantite,
    }

    livre.insert_one(book_data)

  return render_template('admin.html')  # Adjust the template name as needed


@app.route('/delete_book/<book_id>', methods=['DELETE'])
def delete_book(book_id):
  try:
    # Delete the book from the database based on the provided ID
    livre.delete_one({'_id': ObjectId(book_id)})
    return jsonify({"success": True})
  except Exception as e:
    print(e)
    return jsonify({"success": False})


@app.route('/modify_book/<book_id>', methods=['GET', 'POST'])
def modify_book(book_id):
  if request.method == 'POST':
    # Récupérer les données du formulaire pour la modification de livre
    titre = request.form['titreModif']
    auteur = request.form['auteurModif']
    sommaire = request.form['sommaireModif']
    nbr_pages = int(request.form['nbr_pagesModif'])
    categorie = request.form['categorieModif']
    source = request.form['sourceModif']
    quantite = int(request.form['quantiteModif'])

    # Mettre à jour l'information du livre dans la base de données
    livre.update_one({'_id': ObjectId(book_id)}, {
      '$set': {
        'titre': titre,
        'auteur': auteur,
        'sommaire': sommaire,
        'nbr_pages': nbr_pages,
        'categorie': categorie,
        'source': source,
        'quantite': quantite,
      }
    })

    return redirect('/')  # Rediriger vers la page principale après la modification

  book = livre.find_one({'_id': ObjectId(book_id)})
  return render_template('admin.html', book=book)

  return render_template('admin.html', results=None)


@app.route('/search_books', methods=['GET'])
def search_books():
  # Récupérer les paramètres de recherche
  titre = request.args.get('titre')
  auteur = request.args.get('auteur')
  categorie = request.args.get('categorie')
  source = request.args.get('source')

  search_results = livre.find({
    'titre': {'$regex': f'.*{titre}.*', '$options': 'i'},
    'auteur': {'$regex': f'.*{auteur}.*', '$options': 'i'},
    'categorie': {'$regex': f'.*{categorie}.*', '$options': 'i'},
    'source': {'$regex': f'.*{source}.*', '$options': 'i'}
  })

  return render_template('admin.html', search_results=search_results)


from flask import jsonify

@app.route('/get_user_info/<username>', methods=['GET'])
def get_user_info(username):
    app.logger.info(f"Received request for username: {username}")
    try:
        user_info = collection.find_one({'name': username}, {'_id': 0, 'cin': 1, 'telephone': 1})

        if user_info:
            app.logger.info(f"User info found: {user_info}")
            return jsonify(user_info)
        else:
            app.logger.warning(f"User not found for username: {username}")
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        app.logger.error(f"Error fetching user info: {e}")
        return jsonify({"error": "Internal server error"}), 500


from flask import Flask, render_template, session, request
from datetime import datetime, timedelta

@app.route('/omar', methods=['GET', 'POST'])
def recherche():
    # Retrieve user information from the session
    user_info = {
        'username': session.get('username', ''),
        'cin': session.get('cin', ''),
        'telephone': session.get('telephone', ''),
        'email': session.get('email', ''),
    }

    if request.method == 'POST':
        titre = request.form.get('titre')
        auteur = request.form.get('auteur')
        categorie = request.form.get('categorie')
        source = request.form.get('source')

        # Build MongoDB query with regex
        query = {}
        if titre:
            query['titre'] = {'$regex': re.compile(titre, re.IGNORECASE)}
        if auteur:
            query['auteur'] = {'$regex': re.compile(auteur, re.IGNORECASE)}
        if categorie:
            query['categorie'] = {'$regex': re.compile(categorie, re.IGNORECASE)}
        if source:
            query['source'] = {'$regex': re.compile(source, re.IGNORECASE)}

        # Search in MongoDB collection
        resultats = livre.find(query)

        # Get the logout date for the user "MIMOUNE" from the database
        user_data = collection.find_one({'name': 'MIMOUNE'}, {'_id': 0, 'logout_date': 1})

        if user_data and 'logout_date' in user_data:
            user_info['logout_date'] = user_data['logout_date']

            # Convert the logout_date to a readable format (if it exists)
            if user_info['logout_date']:
                logout_datetime = datetime.strptime(user_info['logout_date'], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()

                if logout_datetime.date() == now.date():
                    # If the date is today, format as "aujourd'hui at l'heure et la minute"
                    formatted_date = f"aujourd'hui à {logout_datetime.strftime('%H:%M')}"
                elif logout_datetime.date() == (now - timedelta(days=1)).date():
                    # If the date is yesterday, format as "hier at l'heure et la minute"
                    formatted_date = f"hier à {logout_datetime.strftime('%H:%M')}"
                else:
                    # Otherwise, format the full date
                    formatted_date = logout_datetime.strftime("%Y-%m-%d %H:%M:%S")

                user_info['formatted_date'] = formatted_date
                print("Formatted Date:", formatted_date)  # Print the formatted date

        return render_template('user.html', resultats=resultats, user_info=user_info)

    return render_template('user.html', user_info=user_info)

from datetime import datetime, timedelta

@app.route('/user_dashboard')
def user_dashboard():
    # Retrieve user information from the session
    user_info = {
        'username': session.get('username', ''),
        'cin': session.get('cin', ''),
        'telephone': session.get('telephone', ''),
        'email': session.get('email', ''),
    }

    # Get the logout date for the user "MIMOUNE" from the database
    user_info['logout_date'] = collection.find_one({'name': 'MIMOUNE'}, {'_id': 0, 'logout_date': 1})

    # Convert the logout_date to a readable format (if it exists)
    if 'logout_date' in user_info['logout_date']:
        logout_datetime = datetime.strptime(user_info['logout_date']['logout_date'], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        if logout_datetime.date() == now.date():
            # If the date is today, format as "aujourd'hui at l'heure et la minute"
            formatted_date = f"aujourd'hui à {logout_datetime.strftime('%H:%M')}"
        elif logout_datetime.date() == (now - timedelta(days=1)).date():
            # If the date is yesterday, format as "hier at l'heure et la minute"
            formatted_date = f"hier à {logout_datetime.strftime('%H:%M')}"
        else:
            # Otherwise, format the full date
            formatted_date = logout_datetime.strftime("%Y-%m-%d %H:%M:%S")

        user_info['logout_date']['formatted_date'] = formatted_date
        print("Formatted Date:", formatted_date)  # Print the formatted date

    # Print the user_info for debugging
    print("User Info:", user_info)

    # Render the template with user information and user_info
    return render_template('user.html', user_info=user_info)

# Load Gmail configuration from the json file
json_file = open("config.json")
gmail_cfg = json.load(json_file)

@app.route('/envoyer-email', methods=['POST'])
def envoyer_email_route():
    if request.method == 'POST':
        # Get JSON data from the request
        data = request.get_json()

        # Extract username from the session or JSON data
        username = session.get('username') or data.get('username')

        # Store the data in the 'paiement' collection
        db.paiement.insert_one({
            'creditCardNumber': data.get('creditCardNumber'),
            'expirationDate': data.get('expirationDate'),
            'securityCode': data.get('securityCode'),
            'cardHolderName': data.get('cardHolderName'),
            'countryRegion': data.get('countryRegion'),
            'numberOfBooks': data.get('numberOfBooks'),
            'totalPaymentAmount': data.get('totalPaymentAmount'),
            'username': username,  # Include username in the data
        })

    # Define the recipient's email address
        recipient_email = data.get('cardHolderEmail', '')

        # Create the message to send using MIMEMultipart
        msg = MIMEMultipart()
        msg["to"] = recipient_email
        msg["from"] = f"ENSAH BIB <{gmail_cfg['email']}>"
        msg["Subject"] = 'Détails de la carte de crédit'

        professional_message = f'''
                <div class="container" style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                    <h4 class="text-primary">Cher {data['cardHolderName']},</h4>
                    <p class="mb-4">Nous vous remercions pour votre récente transaction. Voici les détails de la carte de crédit que vous avez fournis:</p>
                </div>
                '''

        body_message = f'''
        <html>
        <head>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
            <script src="https://kit.fontawesome.com/a076d05399.js"></script>
        </head>
        <body>
            <div class="container" style="margin: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <p>{professional_message}</p>
                <table class="table table-bordered" style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Numéro de carte</th>
                        <td style="border: 1px solid #dee2e6;">{data['creditCardNumber']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Date d'expiration</th>
                        <td style="border: 1px solid #dee2e6;">{data['expirationDate']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Code de sécurité</th>
                        <td style="border: 1px solid #dee2e6;">{data['securityCode']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Nom du titulaire de la carte</th>
                        <td style="border: 1px solid #dee2e6;">{data['cardHolderName']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Pays/Région</th>
                        <td style="border: 1px solid #dee2e6;">{data['countryRegion']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Nombre de livres</th>
                        <td style="border: 1px solid #dee2e6;">{data['numberOfBooks']}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #dee2e6;">Montant total du paiement</th>
                        <td style="border: 1px solid #dee2e6;">{data['totalPaymentAmount']}</td>
                    </tr>
                </table>
                <div class="container" style="margin-top: 20px;">
                    <p class="mb-4">Cordialement,</p>
                </div>
                <div class="container" style="margin-top: 20px; padding: 20px; border-top: 1px solid #ddd;">
                    <table class="table table-bordered" style="border-collapse: collapse; width: 100%;">
                        <tr>
                            <td style="border: 1px solid #dee2e6;"><i class="fas fa-map-marker-alt"></i></td>
                            <td style="border: 1px solid #dee2e6;">30 rue tadla quartier moulouiya Berkane</td>
                            <td style="border: 1px solid #dee2e6;"><i class="fas fa-phone"></i> <a href="tel:+212 6 49 20 59 89">+212 6 49 20 59 89</a></td>
                            <td style="border: 1px solid #dee2e6;">
                                <a href="https://static.neopse.com/medias/p/541/site/be/48/08/be4808a334e57d375440f15d28dd6dd2ab75cac1.png?v=v1" target="_blank">
                                    <img src="https://static.neopse.com/medias/p/541/site/be/48/08/be4808a334e57d375440f15d28dd6dd2ab75cac1.png?v=v1" alt="Logo" style="max-width: 30px; max-height: 30px;">
                                </a>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        '''

        # Attach the HTML content to the email
        msg.attach(MIMEText(body_message, 'html'))

        # Connect to SMTP server and send the email
        try:
          with smtplib.SMTP_SSL(gmail_cfg["server"], gmail_cfg["port"]) as server:
            server.login(gmail_cfg["email"], gmail_cfg["pwd"])
            server.sendmail(gmail_cfg["email"], recipient_email, msg.as_string())
          return jsonify({'message': 'E-mail envoyé avec succès'})
        except Exception as e:
          print(f"Erreur lors de l'envoi de l'e-mail : {str(e)}")
          return jsonify({'error': str(e)}), 500

from datetime import datetime

from flask import jsonify

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        user_name = request.form['user_name']
        message_type = request.form['message_type']
        message_content = request.form['message_content']

        if message_type == 'audio' and (message_content == 'http://127.0.0.1:502/omar' or not message_content):
            return 'Audio message skipped from storage.', 200  # HTTP OK

        existing_message = discussion.find_one({'message_content': message_content})
        if existing_message:
            return 'Duplicate audio message. Skipped from storage.', 409  # HTTP Conflict

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        message_data = {
            'user_name': user_name,
            'message_type': message_type,
            'message_content': message_content,
            'timestamp': formatted_datetime
        }
        discussion.insert_one(message_data)

        # Retrieve messages from the database sorted by timestamp
        messages = discussion.find().sort('timestamp', pymongo.ASCENDING)

        # Convert messages to a list and send to the client
        messages_list = list(messages)
        return jsonify(messages_list), 201  # HTTP Created

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return 'Internal server error.', 500

from flask import Flask, render_template, session, request, jsonify  # Add 'jsonify' import
from datetime import datetime, timedelta
import pymongo

from reportlab.pdfgen import canvas
from io import BytesIO
from flask import Flask, render_template, request, session, jsonify, make_response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from bson import ObjectId

@app.route('/submit-emprunt', methods=['POST'])
def submit_emprunt():
    if request.method == 'POST':
        try:
            # Get username from the form
            username = request.form.get('nomUtilisateur')

            # Insert emprunt data into MongoDB collection
            emprunt_data = {
                "nomUtilisateur": request.form.get('nomUtilisateur'),
                "emailUtilisateur": request.form.get('emailUtilisateur'),
                "livreTitre": request.form.get('livreTitre'),
                "livreAuteur": request.form.get('livreAuteur'),
                "livreSommaire": request.form.get('livreSommaire'),
                "livreNbrPages": request.form.get('livreNbrPages'),
                "livreCategorie": request.form.get('livreCategorie'),
                "livreSource": request.form.get('livreSource'),
                "livreQuantite": request.form.get('livreQuantite'),
                "dateEmprunt": request.form.get('dateEmprunt'),
                "dateRetour": request.form.get('dateRetour'),
                "nombreLivres": request.form.get('nombreLivres'),
                "methodePaiement": request.form.get('methodePaiement'),
            }
            db.emprunts.insert_one(emprunt_data)

            # Update book collection quantity
            book_title = request.form.get('livreTitre')
            borrowed_quantity = int(request.form.get('nombreLivres'))

            # Find the book in the collection
            book_query = {"titre": book_title}
            book = db.livre.find_one(book_query)

            if book:
              # Subtract the borrowed quantity from the original quantity
              original_quantity = book.get('quantite')
              updated_quantity = max(0, original_quantity - borrowed_quantity)

              # Update the book collection with the new quantity
              db.livre.update_one(book_query, {"$set": {"quantite": updated_quantity}})
            else:
              print(f"Book '{book_title}' not found in the collection.")

            # Retrieve payment data from MongoDB collection based on username
            payment_data = db.paiement.find_one({'username': username})

            if payment_data:
                # Include payment data in the PDF table
                emprunt_data.update(payment_data)


            # Create a list to hold the table data
            table_data = [["Champ", "Valeur"]]

            # Add emprunt information to the table data
            for key, value in emprunt_data.items():
                table_data.append([key.replace('_', ' ').title(), str(value)])

            # Create the PDF buffer
            pdf_buffer = BytesIO()
            pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)

            # Create the table and set style
            table = Table(table_data)
            style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.skyblue),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)])

            table.setStyle(style)

            # Build the PDF
            elements = [table]
            pdf.build(elements)

            # Return the PDF as a download response
            return pdf_buffer.getvalue(), 200, {'Content-Type': 'application/pdf',
                                                'Content-Disposition': 'attachment; filename=emprunt.pdf'}

        except Exception as e:
            print(f"Error processing emprunt data: {str(e)}")
            return 'Internal server error.', 500

@app.route('/store-location', methods=['POST'])
def store_location():
    try:
        if request.method == 'POST':
            # Vérifier si l'utilisateur est authentifié
            if 'username' not in session:
                return jsonify({'error': 'Utilisateur non authentifié'}), 401

            data = request.json
            username = session.get('username')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Vérifier si l'utilisateur a déjà enregistré sa localisation
            existing_location = db.locations.find_one({'username': username})

            if existing_location:
                # L'utilisateur a déjà enregistré sa localisation, mettez à jour le dictionnaire
                db.locations.update_one(
                    {'username': username},
                    {'$push': {'locations': {'latitude': latitude, 'longitude': longitude, 'timestamp': datetime.now()}}}
                )
            else:
                # L'utilisateur n'a pas encore enregistré sa localisation, créez le document
                google_maps_link = f'https://www.google.com/maps?q={latitude},{longitude}'
                db.locations.insert_one({
                    'username': username,
                    'locations': [{'latitude': latitude, 'longitude': longitude, 'timestamp': datetime.now()}],
                    'google_maps_link': google_maps_link
                })

            return jsonify({'message': 'Localisation enregistrée avec succès', 'google_maps_link': google_maps_link})
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la localisation : {str(e)}")
        return jsonify({'error': 'Erreur lors de l\'enregistrement de la localisation'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=502)
