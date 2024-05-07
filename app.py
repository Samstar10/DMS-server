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
from models import Document, Version, Notification

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
                    document_category= request.form.get('document_category'),
                    patient_name= request.form.get('patient_name'),
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
        
class VersionHistory(Resource):
    def get(self, document_id):
        document = Document.query.get(document_id)

        if not document:
            return {
                'message': 'Document not found.'
            }, 404
        
        versions = Version.query.filter_by(document_id=document_id).all()
        version_list = [{
            'id': version.id,
            'version_number': version.version_number,
            'file_path': version.file_path,
            'created_at': version.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': version.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for version in versions]

        return {
            'message': 'Version history retrieved successfully.',
            'data': version_list
        }, 200
    
class RevertDocument(Resource):
    def put(self, document_id, version_number):
        document = Document.query.get(document_id)
        version = Version.query.get(version_number)

        if not document or not version:
            return {
                'message': 'Document or version not found.'
            }, 404
        
        if version.document_id != document.id:
            return {
                'message': 'Version does not belong to the document.'
            }, 404
        
        document.file_path = version.file_path
        db.session.commit()

        notification = Notification(
            message= f'Document {document.file_name} reverted to version {version.version_number}.',
            document_id= document.id
        )

        db.session.add(notification)
        db.session.commit()

        return {
            'message': 'Document reverted successfully.',
            'document_id': document.id,
            'version_id': version.id,
            'new_file_path': document.file_path
        }, 200


class DocumentNotification(Resource):
    def get(self, document_id):
        notifications = Notification.query.filter_by(document_id=document_id).all()
        return [{
            'message': notification.message,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for notification in notifications]
    

class DocumentFetch(Resource):
    def get(self, document_id):
        document = Document.query.get(document_id)

        if not document:
            return {
                'message': 'Document not found.'
            }, 404
        
        return {
            'message': 'Document retrieved successfully.',
            'data': {
                'id': document.id,
                'file_name': document.file_name,
                'document_category': document.document_category,
                'patient_name': document.patient_name,
                'file_type': document.file_type,
                'file_path': document.file_path,
                'created_at': document.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': document.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, 200
    
class DocumentEdit(Resource):
    def put(self, document_id):
        files = request.files.getlist('document')

        document = Document.query.get(document_id)
        
        if not document:
            return {
                'message': 'Document not found.',
            }, 400
        
        
        if files:
            file = files[0]
            file_name = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            file.save(file_path)

            document = Document.query.get(document_id)

            if not document:
                return {
                    'message': 'Document not found.'
                }, 404
            
            latest_version_number = db.session.query(db.func.max(Version.version_number)).filter_by(document_id=document_id).scalar() or 0
            new_version = Version(
                document_id=document_id,
                version_number=latest_version_number + 1,
                file_path=file_path
            )
            db.session.add(new_version)
            db.session.flush()

            document.file_path = file_path

        else:
            document_category = request.form.get('document_category', document.document_category)
            patient_name = request.form.get('patient_name', document.patient_name)

            document.document_category = document_category
            document.patient_name = patient_name

        db.session.commit()

        return {
            'message': 'Document updated successfully.',
            'document_id': document.id,
            'new_file_path': document.file_path,
            'patient_name': document.patient_name
        }, 200

        
    

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


api.add_resource(FileUpload, '/upload')
api.add_resource(DocumentSearch, '/search')
api.add_resource(DocumentDownload, '/download/<int:document_id>')
api.add_resource(DocumentDelete, '/delete/<int:document_id>')
api.add_resource(VersionHistory, '/versions/<int:document_id>')
api.add_resource(RevertDocument, '/revert/<int:document_id>/<int:version_number>')
api.add_resource(DocumentNotification, '/notifications/<int:document_id>')
api.add_resource(DocumentFetch, '/fetch/<int:document_id>')
api.add_resource(DocumentEdit, '/edit/<int:document_id>')


if __name__ == '__main__':
    app.run(port=5555, debug=True)