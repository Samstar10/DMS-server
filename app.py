import base64
from flask import request, session, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from cloudinary.uploader import upload
from werkzeug.datastructures import FileStorage

from config import app, db, api

parser = reqparse.RequestParser()
parser.add_argument('files', type=FileStorage, location='files', action='append')


@app.route('/')
def index():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(port=5555, debug=True)