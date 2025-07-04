from flask import Flask, render_template, request, redirect, session, flash, url_for
import hashlib
import uuid
import boto3

app = Flask(__name__)
app.secret_key = 'super-secret-key'

# AWS Configuration

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table("MovieMagic_Users")
bookings_table = dynamodb.Table("MovieMagic_Bookings")
sns = boto3.client('sns', region_name='us-east-1')
sns_topic_arn = 'arn:aws:sns:us-east-1:605134439175:MovieMagicNotifications:259e3be3-5864-4985-ab9d-edfc09ca6300'

# Helpers
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_mock_email(email, booking_info):
    message = (f"Booking confirmed for {booking_info['movie']}\n"
               f"Seat: {', '.join(booking_info['seat'])}\n"
               f"Date: {booking_info['date']}, Time: {booking_info['time']}\n"
               f"Booking ID: {booking_info['id']}")
    print(f"[MOCK EMAIL] Sent to {email}:\n{message}")
    try:
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject="🎟 MovieMagic Booking Confirmation",
            Message=message
        )
    except Exception as e:
        print("SNS error:", e)

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if users_table.get_item(Key={'email': email}).get('Item'):
            flash("Account already exists.")
            return redirect(url_for('login'))
        users_table.put_item(Item={'email': email, 'password': hash_password(password)})
        flash("Account created! Please login.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_table.get_item(Key={'email': email}).get('Item')
        if user and user['password'] == hash_password(password):
            session['user'] = email
            flash("Login successful.")
            return redirect(url_for('home'))
        flash("Invalid email or password.")
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    now_showing = [
        {"title": "The Grand Premiere", "genre": "Drama", "poster": "posters/movie1.jpg"},
        {"title": "Laugh Riot", "genre": "Comedy", "poster": "posters/movie2.jpg"},
        {"title": "Edge of Tomorrow", "genre": "Action", "poster": "posters/movie3.jpg"},
        {"title": "Haunted Nights", "genre": "Horror", "poster": "posters/movie4.jpg"}
    ]
    return render_template('home.html', user=session['user'], movies=now_showing)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        session['pending_booking'] = {
            'movie': 'Example Movie',
            'seat': [],
            'date': request.form['date'],
            'time': request.form['time']
        }
        return redirect(url_for('seatmap'))
    return render_template('booking_form.html', movie='Example Movie')

@app.route('/seatmap', methods=['GET', 'POST'])
def seatmap():
    if 'user' not in session or 'pending_booking' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        seat_str = request.form.get('seat', '')
        seat_list = [s.strip() for s in seat_str.split(',') if s.strip()]
        session['pending_booking']['seat'] = seat_list
        return redirect(url_for('payment'))
    return render_template('seatmap.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session or 'pending_booking' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        booking_id = str(uuid.uuid4())[:8]
        seats = session['pending_booking']['seat']
        booking_info = {
            'user': session['user'],
            'movie': session['pending_booking']['movie'],
            'seat': seats,
            'date': session['pending_booking']['date'],
            'time': session['pending_booking']['time'],
            'id': booking_id
        }
        bookings_table.put_item(Item=booking_info)
        session['last_booking'] = booking_info
        send_mock_email(session['user'], booking_info)
        session.pop('pending_booking', None)
        return redirect(url_for('confirmation'))
    return render_template('payment.html')

@app.route('/confirmation')
def confirmation():
    if 'user' not in session or 'last_booking' not in session:
        return redirect(url_for('login'))
    return render_template('confirmation.html', booking=session['last_booking'])

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("MovieMagic running at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
