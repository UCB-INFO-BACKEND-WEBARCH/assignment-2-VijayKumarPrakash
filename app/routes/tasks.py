from flask import request, jsonify
from app import db
from app.models import Task, Category
from app.jobs import send_due_reminder
from datetime import datetime, timedelta
import redis
from rq import Queue
import os

# Initialize Redis and Queue
redis_connection = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
queue_instance = Queue(connection=redis_connection)


def validate_task_input(data, partial=False):
    """Validate task input data. Returns (validated_data, errors) tuple."""
    errors = {}
    
    if not partial:
        # Title is required
        if 'title' not in data or not data['title']:
            errors['title'] = ['Title is required.']
        else:
            title = data['title']
            if not isinstance(title, str):
                errors['title'] = ['Title must be a string.']
            elif len(title) < 1 or len(title) > 100:
                errors['title'] = ['Length must be between 1 and 100.']
    
    # Description validation (optional)
    if 'description' in data and data['description'] is not None:
        description = data['description']
        if not isinstance(description, str):
            errors['description'] = ['Description must be a string.']
        elif len(description) > 500:
            errors['description'] = ['Length must not exceed 500.']
    
    # Category ID validation (optional)
    if 'category_id' in data and data['category_id'] is not None:
        if not isinstance(data['category_id'], int):
            errors['category_id'] = ['Category ID must be an integer.']
    
    if errors:
        return None, errors
    
    return data, None


def get_all_tasks():
    """GET /tasks - Returns a list of all tasks with optional filtering."""
    completed_filter = request.args.get('completed')
    
    query = Task.query
    
    if completed_filter is not None:
        if completed_filter.lower() == 'true':
            query = query.filter_by(is_finished=True)
        elif completed_filter.lower() == 'false':
            query = query.filter_by(is_finished=False)
    
    all_tasks = query.all()
    
    task_list = []
    for task in all_tasks:
        task_data = {
            'id': task.task_id,
            'title': task.task_name,
            'description': task.task_note,
            'completed': task.is_finished,
            'due_date': task.gotta_do_by.isoformat() if task.gotta_do_by else None,
            'category_id': task.category_id,
            'created_at': task.created_at.isoformat() + 'Z',
            'updated_at': task.last_changed.isoformat() + 'Z',
        }
        
        if task.category_info:
            task_data['category'] = {
                'id': task.category_info.category_id,
                'name': task.category_info.category_name,
                'color': task.category_info.color
            }
        
        task_list.append(task_data)
    
    return jsonify({'tasks': task_list}), 200


def get_single_task(task_id):
    """GET /tasks/:id - Returns a single task."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task_data = {
        'id': task.task_id,
        'title': task.task_name,
        'description': task.task_note,
        'completed': task.is_finished,
        'due_date': task.gotta_do_by.isoformat() if task.gotta_do_by else None,
        'category_id': task.category_id,
        'created_at': task.created_at.isoformat() + 'Z',
        'updated_at': task.last_changed.isoformat() + 'Z',
    }
    
    if task.category_info:
        task_data['category'] = {
            'id': task.category_info.category_id,
            'name': task.category_info.category_name,
            'color': task.category_info.color
        }
    
    return jsonify(task_data), 200


def create_task():
    """POST /tasks - Creates a new task with validation."""
    data = request.get_json()
    
    validated_data, validation_errors = validate_task_input(data, partial=False)
    if validation_errors:
        return jsonify({'errors': validation_errors}), 400
    
    # Check if category_id exists (if provided)
    if validated_data.get('category_id'):
        category = Category.query.get(validated_data['category_id'])
        if not category:
            return jsonify({'errors': {'category_id': ['Category does not exist']}}), 400
    
    # Create task
    new_task = Task(
        task_name=validated_data['title'],
        task_note=validated_data.get('description'),
        is_finished=validated_data.get('completed', False),
        gotta_do_by=validated_data.get('due_date'),
        category_id=validated_data.get('category_id')
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    # Check if notification should be queued
    notification_queued = False
    if new_task.gotta_do_by:
        now = datetime.utcnow()
        time_until_due = new_task.gotta_do_by - now
        if timedelta(0) < time_until_due <= timedelta(hours=24):
            notification_queued = True
            queue_instance.enqueue(send_due_reminder, new_task.task_name)
    
    task_data = {
        'id': new_task.task_id,
        'title': new_task.task_name,
        'description': new_task.task_note,
        'completed': new_task.is_finished,
        'due_date': new_task.gotta_do_by.isoformat() if new_task.gotta_do_by else None,
        'category_id': new_task.category_id,
        'created_at': new_task.created_at.isoformat() + 'Z',
        'updated_at': new_task.last_changed.isoformat() + 'Z',
    }
    
    return jsonify({
        'task': task_data,
        'notification_queued': notification_queued
    }), 201


def update_task(task_id):
    """PUT /tasks/:id - Updates an existing task."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    validated_data, validation_errors = validate_task_input(data, partial=True)
    if validation_errors:
        return jsonify({'errors': validation_errors}), 400
    
    # Check if category_id exists (if provided)
    if validated_data.get('category_id'):
        category = Category.query.get(validated_data['category_id'])
        if not category:
            return jsonify({'errors': {'category_id': ['Category does not exist']}}), 400
    
    # Update fields
    if 'title' in validated_data:
        task.task_name = validated_data['title']
    if 'description' in validated_data:
        task.task_note = validated_data['description']
    if 'completed' in validated_data:
        task.is_finished = validated_data['completed']
    if 'due_date' in validated_data:
        task.gotta_do_by = validated_data['due_date']
    if 'category_id' in validated_data:
        task.category_id = validated_data['category_id']
    
    db.session.commit()
    
    task_data = {
        'id': task.task_id,
        'title': task.task_name,
        'description': task.task_note,
        'completed': task.is_finished,
        'due_date': task.gotta_do_by.isoformat() if task.gotta_do_by else None,
        'category_id': task.category_id,
        'created_at': task.created_at.isoformat() + 'Z',
        'updated_at': task.last_changed.isoformat() + 'Z',
    }
    
    if task.category_info:
        task_data['category'] = {
            'id': task.category_info.category_id,
            'name': task.category_info.category_name,
            'color': task.category_info.color
        }
    
    return jsonify(task_data), 200


def delete_task(task_id):
    """DELETE /tasks/:id - Deletes a task."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'Task deleted'}), 200


def register_routes(app):
    """Register all task routes to the Flask app."""
    app.add_url_rule('/tasks', 'get_all_tasks', get_all_tasks, methods=['GET'])
    app.add_url_rule('/tasks/<int:task_id>', 'get_single_task', get_single_task, methods=['GET'])
    app.add_url_rule('/tasks', 'create_task', create_task, methods=['POST'])
    app.add_url_rule('/tasks/<int:task_id>', 'update_task', update_task, methods=['PUT'])
    app.add_url_rule('/tasks/<int:task_id>', 'delete_task', delete_task, methods=['DELETE'])
