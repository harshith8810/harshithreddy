#!/usr/bin/env python3
"""
Personal Task Management System
A comprehensive CLI-based task manager with categories, priorities, and persistence
"""

import json
import os
import datetime
from typing import List, Dict, Optional
from enum import Enum
import argparse
import sys

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Task:
    """Represents a single task with all its attributes"""
    
    def _init_(self, title: str, description: str = "", category: str = "General", 
                 priority: Priority = Priority.MEDIUM, due_date: Optional[str] = None):
        self.id = None  # Will be set by TaskManager
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.status = Status.PENDING
        self.created_date = datetime.datetime.now().isoformat()
        self.due_date = due_date
        self.completed_date = None
        self.tags = []
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_date': self.created_date,
            'due_date': self.due_date,
            'completed_date': self.completed_date,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create task from dictionary"""
        task = cls(data['title'], data['description'], data['category'])
        task.id = data['id']
        task.priority = Priority(data['priority'])
        task.status = Status(data['status'])
        task.created_date = data['created_date']
        task.due_date = data['due_date']
        task.completed_date = data['completed_date']
        task.tags = data.get('tags', [])
        return task
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date or self.status == Status.COMPLETED:
            return False
        due = datetime.datetime.fromisoformat(self.due_date)
        return datetime.datetime.now() > due
    
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if not self.due_date:
            return None
        due = datetime.datetime.fromisoformat(self.due_date)
        delta = due - datetime.datetime.now()
        return delta.days

class TaskManager:
    """Main task management class"""
    
    def _init_(self, data_file: str = "tasks.json"):
        self.data_file = data_file
        self.tasks: List[Task] = []
        self.next_id = 1
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in data['tasks']]
                    self.next_id = data.get('next_id', 1)
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                print(f"Warning: Could not load tasks from {self.data_file}")
                self.tasks = []
                self.next_id = 1
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        data = {
            'tasks': [task.to_dict() for task in self.tasks],
            'next_id': self.next_id
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving tasks: {e}")
    
    def add_task(self, title: str, description: str = "", category: str = "General",
                 priority: Priority = Priority.MEDIUM, due_date: Optional[str] = None) -> int:
        """Add a new task"""
        task = Task(title, description, category, priority, due_date)
        task.id = self.next_id
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task.id
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update task attributes"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self.save_tasks()
        return True
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.save_tasks()
            return True
        return False
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed"""
        task = self.get_task(task_id)
        if task:
            task.status = Status.COMPLETED
            task.completed_date = datetime.datetime.now().isoformat()
            self.save_tasks()
            return True
        return False
    
    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Get all tasks in a specific category"""
        return [task for task in self.tasks if task.category.lower() == category.lower()]
    
    def get_tasks_by_status(self, status: Status) -> List[Task]:
        """Get all tasks with specific status"""
        return [task for task in self.tasks if task.status == status]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks"""
        return [task for task in self.tasks if task.is_overdue()]
    
    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Get all tasks with specific priority"""
        return [task for task in self.tasks if task.priority == priority]
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description"""
        query = query.lower()
        results = []
        for task in self.tasks:
            if (query in task.title.lower() or 
                query in task.description.lower() or
                query in [tag.lower() for tag in task.tags]):
                results.append(task)
        return results
    
    def get_statistics(self) -> Dict:
        """Get task statistics"""
        total_tasks = len(self.tasks)
        completed = len(self.get_tasks_by_status(Status.COMPLETED))
        pending = len(self.get_tasks_by_status(Status.PENDING))
        in_progress = len(self.get_tasks_by_status(Status.IN_PROGRESS))
        overdue = len(self.get_overdue_tasks())
        
        categories = {}
        for task in self.tasks:
            categories[task.category] = categories.get(task.category, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'overdue': overdue,
            'categories': categories
        }

class TaskCLI:
    """Command-line interface for the task manager"""
    
    def _init_(self):
        self.manager = TaskManager()
    
    def format_task(self, task: Task) -> str:
        """Format task for display"""
        status_icon = {
            Status.PENDING: "⏳",
            Status.IN_PROGRESS: "🔄",
            Status.COMPLETED: "✅",
            Status.CANCELLED: "❌"
        }
        
        priority_icon = {
            Priority.LOW: "🔵",
            Priority.MEDIUM: "🟡",
            Priority.HIGH: "🟠",
            Priority.URGENT: "🔴"
        }
        
        overdue_marker = " 🚨 OVERDUE" if task.is_overdue() else ""
        due_info = f" (Due: {task.due_date})" if task.due_date else ""
        
        return (f"{status_icon[task.status]} {priority_icon[task.priority]} "
                f"[{task.id}] {task.title}{due_info}{overdue_marker}\n"
                f"    Category: {task.category}\n"
                f"    Description: {task.description}\n")
    
    def list_tasks(self, status: Optional[str] = None, category: Optional[str] = None):
        """List tasks with optional filtering"""
        tasks = self.manager.tasks
        
        if status:
            try:
                status_enum = Status(status.lower())
                tasks = self.manager.get_tasks_by_status(status_enum)
            except ValueError:
                print(f"Invalid status: {status}")
                return
        
        if category:
            tasks = [t for t in tasks if t.category.lower() == category.lower()]
        
        if not tasks:
            print("No tasks found.")
            return
        
        # Sort by priority and due date
        tasks.sort(key=lambda t: (t.priority.value, t.due_date or "9999-12-31"))
        
        for task in tasks:
            print(self.format_task(task))
    
    def add_task_interactive(self):
        """Interactive task addition"""
        print("Creating a new task...")
        title = input("Title: ").strip()
        if not title:
            print("Title is required!")
            return
        
        description = input("Description (optional): ").strip()
        category = input("Category (default: General): ").strip() or "General"
        
        print("Priority options: 1=Low, 2=Medium, 3=High, 4=Urgent")
        try:
            priority_input = input("Priority (default: 2): ").strip()
            priority_value = int(priority_input) if priority_input else 2
            priority = Priority(priority_value)
        except ValueError:
            priority = Priority.MEDIUM
            print("Invalid priority, using Medium")
        
        due_date = input("Due date (YYYY-MM-DD, optional): ").strip()
        if due_date:
            try:
                datetime.datetime.fromisoformat(due_date)
            except ValueError:
                print("Invalid date format, ignoring due date")
                due_date = None
        
        task_id = self.manager.add_task(title, description, category, priority, due_date)
        print(f"Task created with ID: {task_id}")
         elif args.command == 'list':
            self.list_tasks(args.status, args.category)
        
        elif args.command == 'complete':
            if self.manager.complete_task(args.id):
                print(f"Task {args.id} marked as completed")
            else:
                print(f"Task {args.id} not found")
        
        elif args.command == 'delete':
            if self.manager.delete_task(args.id):
                print(f"Task {args.id} deleted")
            else:
                print(f"Task {args.id} not found")
                elif args.command == 'search':
            tasks = self.manager.search_tasks(args.query)
            if tasks:
                for task in tasks:
                    print(self.format_task(task))
            else:
                print("No tasks found matching your query")
        
        elif args.command == 'stats':
            self.show_statistics()
        
        elif args.command == 'interactive':
            self.add_task_interactive()
def main():
    """Main entry point"""
    try:
        cli = TaskCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if _name_ == "_main_":
    main()

