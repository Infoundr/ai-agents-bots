from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # OpenChat user ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    message_history = relationship("MessageHistory", back_populates="user")
    asana_connection = relationship("AsanaConnection", back_populates="user", uselist=False)
    github_connection = relationship("GitHubConnection", back_populates="user", uselist=False)

class MessageHistory(Base):
    __tablename__ = 'message_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    bot_name = Column(String)
    message = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="message_history")

class AsanaConnection(Base):
    __tablename__ = 'asana_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    token = Column(String)
    workspace_gid = Column(String)
    project_gids = Column(JSON)  # Store as JSON: {"project_name": "project_gid"}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="asana_connection")
    tasks = relationship("AsanaTask", back_populates="connection")

class GitHubConnection(Base):
    __tablename__ = 'github_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    token = Column(String)
    selected_repo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="github_connection")
    issues = relationship("GitHubIssue", back_populates="connection")

class AsanaTask(Base):
    __tablename__ = 'asana_tasks'
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey('asana_connections.id'))
    task_gid = Column(String)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    
    # Relationship
    connection = relationship("AsanaConnection", back_populates="tasks")

class GitHubIssue(Base):
    __tablename__ = 'github_issues'
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey('github_connections.id'))
    issue_number = Column(Integer)
    title = Column(String)
    body = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    state = Column(String)  # open/closed
    
    # Relationship
    connection = relationship("GitHubConnection", back_populates="issues")