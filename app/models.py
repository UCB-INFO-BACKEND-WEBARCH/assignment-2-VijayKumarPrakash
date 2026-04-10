from app import db
from datetime import datetime


class Task(db.Model):
    """
    Task model for To-Do items.
    """
    __tablename__ = 'task'
    
    # Constraint: primary key
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Constraint: required fields
    task_name = db.Column(db.String(100), nullable=False)
    
    # Constraint: optional fields
    task_note = db.Column(db.Text, nullable=True)
    is_finished = db.Column(db.Boolean, default=False)
    gotta_do_by = db.Column(db.DateTime, nullable=True)
    
    # Relationship: foreign key to Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_changed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to Category
    category_info = db.relationship('Category', backref=db.backref('all_tasks', lazy=True))
    
    def __repr__(self):
        return f'<Task {self.task_id}: {self.task_name}>'


class Category(db.Model):
    """
    Category model for organizing tasks.
    """
    __tablename__ = 'category'
    
    # Constraint: primary key
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Constraint: required fields with unique constraint
    category_name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Constraint: optional fields
    color = db.Column(db.String(7), nullable=True)
    
    def __repr__(self):
        return f'<Category {self.category_id}: {self.category_name}>'
