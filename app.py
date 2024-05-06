import os
from flask import request, session, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cloudinary.uploader import upload
from werkzeug.datastructures import FileStorage

from config import app, db, api
from models import Document

parser = reqparse.RequestParser()
parser.add_argument('files', type=FileStorage, location='files', action='append')


@app.route('/')
def index():
    return 'Hello, World!'

class FileUpload(Resource):
    def post(self):
        files = request.files.getlist('document')

        if not files:
            return {
                'message': 'No files were uploaded.',
            }, 400
        
        responses = []
        for file in files:
            if file and file.name:
                file_name = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
                file.save(file_path)

                new_document = Document(
                    file_name=file_name,
                    file_type = file.content_type,
                    document_category= 'test',
                    patient_name= 'John Doe',
                    file_path=file_path
                )

                db.session.add(new_document)
                db.session.commit()

                response = {
                    'id': new_document.id,
                    'file_name': new_document.file_name,
                    'document_category': new_document.document_category,
                    'patient_name': new_document.patient_name,
                    'file_type': new_document.file_type,
                    'file_path': new_document.file_path,
                }

                responses.append(response)

            else:
                return {
                    'message': 'No files were uploaded.',
                }, 400

        return {
            'message': 'Files uploaded successfully.',
            'data': responses
        }, 200
    


api.add_resource(FileUpload, '/upload')


if __name__ == '__main__':
    app.run(port=5555, debug=True)