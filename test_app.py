import pytest
import json
from app import create_app, db
from app.models import Task, Category


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(config_name='testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_category(app):
    """Create a sample category for testing."""
    with app.app_context():
        category = Category(category_name='Work', color='#FF5733')
        db.session.add(category)
        db.session.commit()
        category_id = category.category_id
    return category_id


class TestCategoryEndpoints:
    """Test category endpoints."""
    
    def test_get_empty_categories(self, client):
        """Test getting categories when none exist."""
        response = client.get('/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['categories'] == []
    
    def test_create_category(self, client):
        """Test creating a new category."""
        response = client.post('/categories', 
            json={'name': 'Personal', 'color': '#33FF57'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['category']['name'] == 'Personal'
        assert data['category']['color'] == '#33FF57'
    
    def test_create_category_duplicate_name(self, client):
        """Test creating category with duplicate name."""
        client.post('/categories', json={'name': 'Work'})
        response = client.post('/categories', json={'name': 'Work'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'name' in data['errors']
    
    def test_create_category_invalid_hex_color(self, client):
        """Test creating category with invalid hex color."""
        response = client.post('/categories', 
            json={'name': 'Test', 'color': 'invalid'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'color' in data['errors']
    
    def test_get_single_category(self, client, sample_category):
        """Test getting a single category."""
        response = client.get(f'/categories/{sample_category}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Work'
    
    def test_get_categories_with_task_count(self, client, app, sample_category):
        """Test that categories endpoint includes task count."""
        with app.app_context():
            task = Task(task_name='Test', category_id=sample_category.category_id)
            db.session.add(task)
            db.session.commit()
        
        response = client.get('/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['categories'][0]['task_count'] == 1
    
    def test_delete_category_without_tasks(self, client, sample_category):
        """Test deleting a category with no tasks."""
        response = client.delete(f'/categories/{sample_category.category_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Category deleted'


class TestTaskEndpoints:
    """Test task endpoints."""
    
    def test_get_empty_tasks(self, client):
        """Test getting tasks when none exist."""
        response = client.get('/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['tasks'] == []
    
    def test_create_task(self, client):
        """Test creating a new task."""
        response = client.post('/tasks',
            json={'title': 'Buy groceries', 'description': 'Milk and eggs'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['task']['title'] == 'Buy groceries'
        assert data['task']['completed'] == False
        assert data['notification_queued'] == False
    
    def test_create_task_missing_title(self, client):
        """Test creating task without title."""
        response = client.post('/tasks', json={'description': 'No title'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'title' in data['errors']
    
    def test_create_task_title_too_long(self, client):
        """Test creating task with title exceeding 100 characters."""
        long_title = 'a' * 101
        response = client.post('/tasks', json={'title': long_title})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'title' in data['errors']
    
    def test_create_task_description_too_long(self, client):
        """Test creating task with description exceeding 500 characters."""
        long_desc = 'a' * 501
        response = client.post('/tasks',
            json={'title': 'Test', 'description': long_desc})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'description' in data['errors']
    
    def test_get_single_task(self, client, app):
        """Test getting a single task."""
        with app.app_context():
            task = Task(task_name='Clean room')
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id
        
        response = client.get(f'/tasks/{task_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Clean room'
    
    def test_get_task_not_found(self, client):
        """Test getting non-existent task."""
        response = client.get('/tasks/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Task not found'
    
    def test_update_task(self, client, app):
        """Test updating a task."""
        with app.app_context():
            task = Task(task_name='Old title')
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id
        
        response = client.put(f'/tasks/{task_id}',
            json={'title': 'New title', 'completed': True})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'New title'
        assert data['completed'] == True
    
    def test_delete_task(self, client, app):
        """Test deleting a task."""
        with app.app_context():
            task = Task(task_name='To delete')
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id
        
        response = client.delete(f'/tasks/{task_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Task deleted'
    
    def test_get_tasks_filtered_by_completed(self, client, app):
        """Test filtering tasks by completion status."""
        with app.app_context():
            task1 = Task(task_name='Task 1', is_finished=False)
            task2 = Task(task_name='Task 2', is_finished=True)
            db.session.add_all([task1, task2])
            db.session.commit()
        
        # Get completed tasks
        response = client.get('/tasks?completed=true')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['completed'] == True
        
        # Get incomplete tasks
        response = client.get('/tasks?completed=false')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['completed'] == False
    
    def test_task_with_invalid_category_id(self, client):
        """Test creating task with non-existent category."""
        response = client.post('/tasks',
            json={'title': 'Task', 'category_id': 999})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'category_id' in data['errors']
