from flask import request, jsonify
from app import db
from app.models import Task, Category
import re


def validate_category_input(data):
    """Validate category input data. Returns (validated_data, errors) tuple."""
    errors = {}
    
    # Name is required
    if 'name' not in data or not data['name']:
        errors['name'] = ['Name is required.']
    else:
        name = data['name']
        if not isinstance(name, str):
            errors['name'] = ['Name must be a string.']
        elif len(name) < 1 or len(name) > 50:
            errors['name'] = ['Name length must be between 1 and 50.']
    
    # Color validation (this is optional, but gave me a good chance to work with some regex)
    if 'color' in data and data['color'] is not None:
        color = data['color']
        if not isinstance(color, str):
            errors['color'] = ['Color should be a string.']
        else:
            hex_pattern = r'^#[0-9A-Fa-f]{6}$'
            if not re.match(hex_pattern, color):
                errors['color'] = ['Must be a valid hex color code (#RRGGBB).']
    
    if errors:
        return None, errors
    
    return data, None


def get_all_categories():
    """GET /categories - Returns all categories with task counts."""
    all_categories = Category.query.all()
    
    category_list = []
    for category in all_categories:
        task_count = Task.query.filter_by(category_id=category.category_id).count()
        
        category_data = {
            'id': category.category_id,
            'name': category.category_name,
            'color': category.color,
            'task_count': task_count
        }
        category_list.append(category_data)
    
    return jsonify({'categories': category_list}), 200


def get_single_category(category_id):
    """GET /categories/:id - Returns a single category with its tasks."""
    category = Category.query.get(category_id)
    
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    tasks_list = []
    for task in category.all_tasks:
        task_data = {
            'id': task.task_id,
            'title': task.task_name,
            'completed': task.is_finished
        }
        tasks_list.append(task_data)
    
    category_data = {
        'id': category.category_id,
        'name': category.category_name,
        'color': category.color,
        'tasks': tasks_list
    }
    
    return jsonify(category_data), 200


def create_category():
    """POST /categories - Creates a new category."""
    data = request.get_json()
    
    validated_data, validation_errors = validate_category_input(data)
    if validation_errors:
        return jsonify({'errors': validation_errors}), 400
    
    # Check if name already exists (unique constraint)
    existing_category = Category.query.filter_by(category_name=validated_data['name']).first()
    if existing_category:
        return jsonify({'errors': {'name': ['Category with this name already exists.']}}), 400
    
    # Create category
    new_category = Category(
        category_name=validated_data['name'],
        color=validated_data.get('color')
    )
    
    db.session.add(new_category)
    db.session.commit()
    
    category_data = {
        'id': new_category.category_id,
        'name': new_category.category_name,
        'color': new_category.color
    }
    
    return jsonify({'category': category_data}), 201


def delete_category(category_id):
    """DELETE /categories/:id - Deletes a category if it has no tasks."""
    category = Category.query.get(category_id)
    
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    # Check if category has tasks
    task_count = Task.query.filter_by(category_id=category_id).count()
    if task_count > 0:
        return jsonify({
            'error': 'Cannot delete category with existing tasks. Move or delete tasks first.'
        }), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Category deleted'}), 200


def register_routes(app):
    """Register all category routes to the Flask app."""
    app.add_url_rule('/categories', 'get_all_categories', get_all_categories, methods=['GET'])
    app.add_url_rule('/categories/<int:category_id>', 'get_single_category', get_single_category, methods=['GET'])
    app.add_url_rule('/categories', 'create_category', create_category, methods=['POST'])
    app.add_url_rule('/categories/<int:category_id>', 'delete_category', delete_category, methods=['DELETE'])
