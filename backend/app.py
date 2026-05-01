from flask import Flask, request, jsonify, session, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadData
import json
import smtplib
from email.message import EmailMessage
from datetime import timedelta
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'sky'), static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=7)

# initialize DB from models to avoid circular imports
from models import db
db.init_app(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

from models import Admin, Opportunity


def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error':'unauthenticated'}), 401
        return func(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    return app.send_static_file('admin.html')


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    name = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    if not name or not email or not password:
        return jsonify({'error':'Missing fields'}), 400
    if len(password) < 8:
        return jsonify({'error':'Password too short'}), 400
    if Admin.query.filter_by(email=email).first():
        return jsonify({'error':'Account already exists'}), 400
    admin = Admin(fullname=name, email=email, password_hash=generate_password_hash(password))
    db.session.add(admin)
    db.session.commit()
    return jsonify({'success':True}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    remember = bool(data.get('remember', False))
    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password_hash, password):
        return jsonify({'error':'Invalid email or password'}), 400
    session.clear()
    session['user_id'] = admin.id
    session['user_email'] = admin.email
    session.permanent = remember
    return jsonify({'success':True, 'email':admin.email})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success':True})


@app.route('/api/forgot', methods=['POST'])
def forgot():
    data = request.get_json() or {}
    email = data.get('email','').strip().lower()
    # Always return success message
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        token = serializer.dumps({'email': email})
        link = request.host_url.rstrip('/') + '/api/reset/' + token
        # Log the reset link internally and append to a dev-only file for retrieval
        app.logger.info('Password reset link for %s: %s', email, link)
        # Attempt to send email if SMTP config present
        smtp_host = os.environ.get('SMTP_HOST')
        if smtp_host:
            try:
                smtp_port = int(os.environ.get('SMTP_PORT', 587))
                smtp_user = os.environ.get('SMTP_USER')
                smtp_pass = os.environ.get('SMTP_PASS')
                smtp_from = os.environ.get('SMTP_FROM') or smtp_user
                smtp_tls = os.environ.get('SMTP_TLS', 'true').lower() not in ('0','false')

                msg = EmailMessage()
                msg['Subject'] = 'Password reset for Sky Foundation Admin'
                msg['From'] = smtp_from
                msg['To'] = email
                msg.set_content(f'You requested a password reset. Use the following link to reset your password (expires in 1 hour):\n\n{link}\n\nIf you did not request this, ignore this message.')

                if smtp_tls:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                    server.starttls()
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)

                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
                app.logger.info('Sent reset email to %s via SMTP', email)
            except Exception:
                app.logger.exception('Failed to send reset email via SMTP; falling back to log/file')
        try:
            links_path = os.path.join(BASE_DIR, 'backend', 'reset_links.jsonl')
            entry = {'email': email, 'link': link, 'token': token}
            with open(links_path, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(entry) + '\n')
        except Exception:
            app.logger.exception('Failed to write reset link to file')
    return jsonify({'success':True})


@app.route('/api/debug/reset-links', methods=['GET'])
def debug_reset_links():
    # Dev-only endpoint: available only when Flask debug mode is on
    if not app.debug:
        return jsonify({'error':'Not available'}), 404
    email = request.args.get('email')
    links_path = os.path.join(BASE_DIR, 'backend', 'reset_links.jsonl')
    if not os.path.exists(links_path):
        return jsonify([])
    items = []
    try:
        with open(links_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    obj = json.loads(line.strip())
                    items.append(obj)
                except Exception:
                    continue
    except Exception:
        return jsonify({'error':'Failed to read links'}), 500
    if email:
        email = email.lower()
        items = [i for i in items if i.get('email') == email]
    return jsonify(items)


@app.route('/api/reset/<token>', methods=['GET'])
def reset_check(token):
    try:
        data = serializer.loads(token, max_age=3600)
    except Exception:
        return jsonify({'error':'Invalid or expired token'}), 400
    return jsonify({'success':True, 'email': data.get('email')})


@app.route('/api/reset/<token>', methods=['POST'])
def reset_password(token):
    try:
        data = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        return jsonify({'error':'Reset link has expired'}), 400
    except BadData:
        return jsonify({'error':'Invalid reset link'}), 400

    email = data.get('email')
    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        return jsonify({'error':'Account not found'}), 400

    payload = request.get_json() or {}
    new_password = payload.get('password','')
    if not new_password or len(new_password) < 8:
        return jsonify({'error':'Password must be at least 8 characters'}), 400

    admin.password_hash = generate_password_hash(new_password)
    db.session.commit()
    app.logger.info('Password reset for %s', email)
    return jsonify({'success':True})


@app.route('/api/opportunities', methods=['GET'])
@login_required
def list_opps():
    user_id = session['user_id']
    opps = Opportunity.query.filter_by(admin_id=user_id).order_by(Opportunity.created_at.desc()).all()
    result = [o.to_dict() for o in opps]
    return jsonify(result)


@app.route('/api/opportunities', methods=['POST'])
@login_required
def create_opp():
    data = request.get_json() or {}
    required = ['name','duration','start_date','description','skills','category','future_opportunities']
    for r in required:
        if not data.get(r):
            return jsonify({'error':'Missing field '+r}), 400
    user_id = session['user_id']
    opp = Opportunity(
        admin_id=user_id,
        name=data.get('name'),
        duration=data.get('duration'),
        start_date=data.get('start_date'),
        description=data.get('description'),
        skills=','.join(data.get('skills')) if isinstance(data.get('skills'), list) else data.get('skills'),
        category=data.get('category'),
        future_opportunities=data.get('future_opportunities'),
        max_applicants=int(data.get('max_applicants')) if data.get('max_applicants') else None
    )
    db.session.add(opp)
    db.session.commit()
    return jsonify(opp.to_dict()), 201


@app.route('/api/opportunities/<int:opp_id>', methods=['GET'])
@login_required
def get_opp(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.admin_id != session['user_id']:
        return jsonify({'error':'Forbidden'}), 403
    return jsonify(opp.to_dict())


@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
@login_required
def edit_opp(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.admin_id != session['user_id']:
        return jsonify({'error':'Forbidden'}), 403
    data = request.get_json() or {}
    for field in ['name','duration','start_date','description','skills','category','future_opportunities','max_applicants']:
        if field in data:
            if field == 'skills' and isinstance(data[field], list):
                setattr(opp, field, ','.join(data[field]))
            elif field == 'max_applicants':
                setattr(opp, field, int(data[field]) if data[field] else None)
            else:
                setattr(opp, field, data[field])
    db.session.commit()
    return jsonify(opp.to_dict())


@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
@login_required
def delete_opp(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.admin_id != session['user_id']:
        return jsonify({'error':'Forbidden'}), 403
    db.session.delete(opp)
    db.session.commit()
    return jsonify({'success':True})


if __name__ == '__main__':
    # create DB tables if missing
    with app.app_context():
        db.create_all()
    app.run(debug=True)
