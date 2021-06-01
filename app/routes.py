from flask import render_template, request, abort, url_for
from flask.json import jsonify
from app import app, db
from app.models import User, Device, Reading, CellTower

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Derek'}
    return render_template('index.html', title='Home', user=user)




### REST API ROUTES ###

"""
API > USER > CREATE
"""
@app.route('/api/users', methods = ['POST'])
def new_user():
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email = request.json.get('email')
    password = request.json.get('password')
    if first_name is None or last_name is None or email is None or password is None:
        abort(400)  # missing args
    if User.query.filter_by(email = email).one_or_none() is not None:
        abort(400)  # existing user
    user = User(first_name = first_name, 
                last_name = last_name,
                email = email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'user_id': user.user_id }), 201, {'Location': url_for('get_user', id = user.user_id, _external = True)}


"""
API > USER > GET(ID)
"""
@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify(user.serialize())
        

"""
API > USERS > GET(ALL)
"""
@app.route('/api/users')
def get_users():
    users = User.query.all()
    return jsonify(users=[u.serialize() for u in users])