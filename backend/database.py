"""
Database connection and models for MERE AI Agent
"""
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, Boolean, ARRAY, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import os
from datetime import datetime
import uuid

# Import pgvector for semantic search
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mere_user:mere_password@localhost:5432/mere_ai")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True)

class Memo(Base):
    __tablename__ = "memos"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[])
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column("metadata", JSON, default={})

class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(Integer, default=1)
    due_date = Column(DateTime)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    extra_data = Column("metadata", JSON, default={})

class Event(Base):
    __tablename__ = "events"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255))
    calendar_provider = Column(String(50))
    external_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    session_id = Column(String(255), nullable=False)
    message_type = Column(String(20), nullable=False)  # user_input, ai_response, system
    content = Column(Text, nullable=False)
    audio_file_path = Column(String(500))
    intent = Column(String(100))
    entities = Column(JSON, default={})
    confidence = Column(Integer)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)

# Database utility functions
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session for dependency injection"""
    return SessionLocal()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
def init_search_db():
    """Initialize search-specific database features"""
    from search_models import Base as SearchBase, PGVECTOR_INIT_SQL
    
    # Create search tables
    SearchBase.metadata.create_all(bind=engine)
    
    # Initialize pgvector extension and functions
    if PGVECTOR_AVAILABLE:
        with engine.connect() as conn:
            try:
                conn.execute(PGVECTOR_INIT_SQL)
                conn.commit()
                print("✅ pgvector extension and search functions initialized")
            except Exception as e:
                print(f"⚠️ pgvector initialization failed: {e}")
    else:
        print("⚠️ pgvector not available - semantic search features disabled")

def get_user_by_username(db: Session, username: str) -> User:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, email: str = None) -> User:
    """Create a new user"""
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user