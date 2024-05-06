import os
from flask import request, session, jsonify, send_from_directory
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
                    'created_at': new_document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': new_document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
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
    

class DocumentSearch(Resource):
    def get(self):
        query_params = request.args
        patient_name = query_params.get('patient_name')
        document_category = query_params.get('document_category')

        query = Document.query

        if patient_name:
            query = query.filter(Document.patient_name.ilike(f'%{patient_name}%'))

        if document_category:
            query = query.filter(Document.document_category.ilike(f'%{document_category}%'))

        documents = query.all()

        results = [{
            'id': document.id,
            'file_name': document.file_name,
            'document_category': document.document_category,
            'patient_name': document.patient_name,
            'file_type': document.file_type,
            'file_path': document.file_path,
            'created_at': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for document in documents]

        return {
            'message': 'Documents retrieved successfully.',
            'data': results
        }, 200
    
class DocumentDownload(Resource):
    def get(self, document_id):
        document = Document.query.filter_by(id=document_id).first()

        if document:
            directory = os.path.dirname(document.file_path)
            filename = os.path.basename(document.file_path)

            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        
        else:
            return {
                'message': 'Document not found.'
            }, 404
        
class DocumentDelete(Resource):
    def delete(self, document_id):
        document = Document.query.filter_by(id=document_id).first()

        if document:
            db.session.delete(document)
            db.session.commit()

            os.remove(document.file_path)

            return {
                'message': 'Document deleted successfully.'
            }, 200
        
        else:
            return {
                'message': 'Document not found.'
            }, 404


api.add_resource(FileUpload, '/upload')
api.add_resource(DocumentSearch, '/search')
api.add_resource(DocumentDownload, '/download/<int:document_id>')
api.add_resource(DocumentDelete, '/delete/<int:document_id>')


if __name__ == '__main__':
    app.run(port=5555, debug=True)