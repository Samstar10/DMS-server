from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.schema import CheckConstraint

from config import db, bcrypt

class Document(db.Model, SerializerMixin):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String, nullable=False)
    document_category = db.Column(db.String, nullable=False)
    patient_name = db.Column(db.String, nullable=False)
    file_type = db.Column(db.String, nullable=False)
    file_path = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    versions = db.relationship('Version', backref='document', lazy=True, order_by='Version.version_number.desc()')

    def __repr__(self):
        return '<Document %r>' % self.file_name
    
    def get_latest_version(self):
        return self.versions.first() if self.versions else None
    
class Version(db.Model, SerializerMixin):
    __tablename__ = 'versions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def __repr__(self):
        return '<Version %r>' % self.version
    
class Notification(db.Model, SerializerMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)

    document = db.relationship('Document', backref='notifications', lazy=True)