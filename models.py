from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.schema import CheckConstraint
from sqlalchemy import Enum

from config import db, bcrypt

class Document(db.Model, SerializerMixin):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    patient_name = db.Column(db.String, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

    def __repr__(self):
        return '<Document %r>' % self.file_name