"""
Business Services for MERE AI Agent
Day 6 Task 6.1: Core Business Logic Implementation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import logging

from database import SessionLocal, User, Memo, Todo, Event
from nlu_service import Intent, NLUResult

logger = logging.getLogger(__name__)

class BusinessServiceError(Exception):
    """Base exception for business service errors"""
    pass

class UserService:
    """User management service"""
    
    def __init__(self):
        pass
    
    def get_or_create_user(self, user_id: str, username: str = None) -> User:
        """Get existing user or create new user"""
        db = SessionLocal()
        try:
            # Always search by username for non-UUID strings
            if isinstance(user_id, str) and len(user_id) < 36:
                # Use username as unique identifier for simple cases like "e2e-test-user"
                user = db.query(User).filter(User.username == user_id).first()
                
                if not user:
                    # Create new user with UUID but use user_id as username
                    user = User(
                        id=uuid.uuid4(),  # Always generate proper UUID for ID
                        username=user_id,  # Use the provided user_id as username
                        created_at=datetime.utcnow(),
                        is_active=True
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    logger.info(f"Created new user: {user.username} (ID: {user.id})")
            else:
                # Handle proper UUIDs
                try:
                    uuid.UUID(user_id)  # Validate UUID format
                    user = db.query(User).filter(User.id == user_id).first()
                    if not user:
                        user = User(
                            id=user_id,
                            username=username or f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            created_at=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        logger.info(f"Created new user: {user.username} (ID: {user.id})")
                except ValueError:
                    # Invalid UUID format, treat as username
                    user = db.query(User).filter(User.username == user_id).first()
                    if not user:
                        user = User(
                            id=uuid.uuid4(),
                            username=user_id,
                            created_at=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        logger.info(f"Created new user: {user.username} (ID: {user.id})")
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"User service error: {e}")
            raise BusinessServiceError(f"Failed to get or create user: {e}")
        finally:
            db.close()

class MemoService:
    """Memo management service"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def create_memo(self, user_id: str, content: str, tags: List[str] = None, 
                   priority: int = 1, metadata: Dict = None, extra_data: Dict = None) -> Memo:
        """Create a new memo"""
        db = SessionLocal()
        try:
            # Ensure user exists
            user = self.user_service.get_or_create_user(user_id)
            
            memo = Memo(
                user_id=user.id,
                content=content,
                tags=tags or [],
                priority=priority,
                created_at=datetime.utcnow(),
                extra_data=extra_data or metadata or {}
            )
            
            db.add(memo)
            db.commit()
            db.refresh(memo)
            
            logger.info(f"Created memo for user {user_id}: '{content[:50]}...'")
            return memo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create memo: {e}")
            raise BusinessServiceError(f"Failed to create memo: {e}")
        finally:
            db.close()
    
    def get_memos(self, user_id: str, limit: int = 10, tags: List[str] = None,
                 priority: int = None, search_query: str = None) -> List[Memo]:
        """Get memos for user with optional filtering"""
        db = SessionLocal()
        try:
            user = self.user_service.get_or_create_user(user_id)
            
            query = db.query(Memo).filter(Memo.user_id == user.id)
            
            # Apply filters
            if tags:
                query = query.filter(Memo.tags.op('&&')(tags))
            
            if priority is not None:
                query = query.filter(Memo.priority >= priority)
            
            if search_query:
                query = query.filter(Memo.content.ilike(f'%{search_query}%'))
            
            memos = query.order_by(Memo.created_at.desc()).limit(limit).all()
            
            logger.info(f"Retrieved {len(memos)} memos for user {user_id}")
            return memos
            
        except Exception as e:
            logger.error(f"Failed to get memos: {e}")
            raise BusinessServiceError(f"Failed to get memos: {e}")
        finally:
            db.close()
    
    def update_memo(self, memo_id: str, content: str = None, tags: List[str] = None,
                   priority: int = None) -> Memo:
        """Update existing memo"""
        db = SessionLocal()
        try:
            memo = db.query(Memo).filter(Memo.id == memo_id).first()
            if not memo:
                raise BusinessServiceError("Memo not found")
            
            if content is not None:
                memo.content = content
            if tags is not None:
                memo.tags = tags
            if priority is not None:
                memo.priority = priority
            
            memo.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(memo)
            
            logger.info(f"Updated memo {memo_id}")
            return memo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update memo: {e}")
            raise BusinessServiceError(f"Failed to update memo: {e}")
        finally:
            db.close()
    
    def delete_memo(self, memo_id: str) -> bool:
        """Delete memo"""
        db = SessionLocal()
        try:
            memo = db.query(Memo).filter(Memo.id == memo_id).first()
            if not memo:
                raise BusinessServiceError("Memo not found")
            
            db.delete(memo)
            db.commit()
            
            logger.info(f"Deleted memo {memo_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete memo: {e}")
            raise BusinessServiceError(f"Failed to delete memo: {e}")
        finally:
            db.close()

class TodoService:
    """Todo management service"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def create_todo(self, user_id: str, title: str, description: str = None,
                   priority: int = 1, due_date: datetime = None, 
                   category: str = None, metadata: Dict = None, extra_data: Dict = None) -> Todo:
        """Create a new todo"""
        db = SessionLocal()
        try:
            user = self.user_service.get_or_create_user(user_id)
            
            todo = Todo(
                user_id=user.id,
                title=title,
                description=description,
                status="pending",
                priority=priority,
                due_date=due_date,
                category=category,
                created_at=datetime.utcnow(),
                extra_data=extra_data or metadata or {}
            )
            
            db.add(todo)
            db.commit()
            db.refresh(todo)
            
            logger.info(f"Created todo for user {user_id}: '{title}'")
            return todo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create todo: {e}")
            raise BusinessServiceError(f"Failed to create todo: {e}")
        finally:
            db.close()
    
    def get_todos(self, user_id: str, status: str = None, limit: int = 10,
                 priority: int = None, category: str = None) -> List[Todo]:
        """Get todos for user with optional filtering"""
        db = SessionLocal()
        try:
            user = self.user_service.get_or_create_user(user_id)
            
            query = db.query(Todo).filter(Todo.user_id == user.id)
            
            # Apply filters
            if status:
                query = query.filter(Todo.status == status)
            
            if priority is not None:
                query = query.filter(Todo.priority >= priority)
            
            if category:
                query = query.filter(Todo.category == category)
            
            todos = query.order_by(Todo.priority.desc(), Todo.created_at.desc()).limit(limit).all()
            
            logger.info(f"Retrieved {len(todos)} todos for user {user_id}")
            return todos
            
        except Exception as e:
            logger.error(f"Failed to get todos: {e}")
            raise BusinessServiceError(f"Failed to get todos: {e}")
        finally:
            db.close()
    
    def update_todo_status(self, todo_id: str, status: str) -> Todo:
        """Update todo status"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise BusinessServiceError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        db = SessionLocal()
        try:
            todo = db.query(Todo).filter(Todo.id == todo_id).first()
            if not todo:
                raise BusinessServiceError("Todo not found")
            
            todo.status = status
            if status == "completed":
                todo.completed_at = datetime.utcnow()
            
            todo.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(todo)
            
            logger.info(f"Updated todo {todo_id} status to {status}")
            return todo
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update todo status: {e}")
            raise BusinessServiceError(f"Failed to update todo status: {e}")
        finally:
            db.close()
    
    def complete_todo(self, todo_id: str) -> Todo:
        """Mark todo as completed"""
        return self.update_todo_status(todo_id, "completed")
    
    def delete_todo(self, todo_id: str) -> bool:
        """Delete todo"""
        db = SessionLocal()
        try:
            todo = db.query(Todo).filter(Todo.id == todo_id).first()
            if not todo:
                raise BusinessServiceError("Todo not found")
            
            db.delete(todo)
            db.commit()
            
            logger.info(f"Deleted todo {todo_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete todo: {e}")
            raise BusinessServiceError(f"Failed to delete todo: {e}")
        finally:
            db.close()

class IntentActionMapper:
    """Intent to Business Action mapping system"""
    
    def __init__(self):
        self.memo_service = MemoService()
        self.todo_service = TodoService()
    
    async def execute_intent(self, user_id: str, nlu_result: NLUResult) -> Dict[str, Any]:
        """Execute business logic based on NLU intent"""
        intent_name = nlu_result.intent.name
        entities = nlu_result.entities or {}
        
        try:
            if intent_name == "create_memo":
                return await self._handle_create_memo(user_id, entities)
            elif intent_name == "query_memo":
                return await self._handle_query_memo(user_id, entities)
            elif intent_name == "update_memo":
                return await self._handle_update_memo(user_id, entities)
            elif intent_name == "delete_memo":
                return await self._handle_delete_memo(user_id, entities)
            
            elif intent_name == "create_todo":
                return await self._handle_create_todo(user_id, entities)
            elif intent_name == "query_todo":
                return await self._handle_query_todo(user_id, entities)
            elif intent_name == "update_todo":
                return await self._handle_update_todo(user_id, entities)
            elif intent_name == "complete_todo":
                return await self._handle_complete_todo(user_id, entities)
            elif intent_name == "delete_todo":
                return await self._handle_delete_todo(user_id, entities)
            
            else:
                # Default response for unsupported intents
                return {
                    "success": True,
                    "action": "default_response",
                    "message": f"Intent '{intent_name}'를 인식했지만 아직 구현되지 않았습니다.",
                    "data": None
                }
                
        except BusinessServiceError as e:
            logger.error(f"Business service error for intent {intent_name}: {e}")
            return {
                "success": False,
                "action": intent_name,
                "message": f"처리 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error for intent {intent_name}: {e}")
            return {
                "success": False,
                "action": intent_name,
                "message": "처리 중 예상치 못한 오류가 발생했습니다.",
                "error": str(e)
            }
    
    async def _handle_create_memo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle memo creation"""
        content = entities.get("item_name") or "메모 내용"
        priority = 1
        tags = []
        
        # Extract priority
        if entities.get("priority"):
            priority_text = entities["priority"].lower()
            if "긴급" in priority_text or "높" in priority_text:
                priority = 3
            elif "중요" in priority_text or "보통" in priority_text:
                priority = 2
        
        # Extract tags/category
        if entities.get("category"):
            tags.append(entities["category"])
        
        memo = self.memo_service.create_memo(
            user_id=user_id,
            content=content,
            tags=tags,
            priority=priority,
            extra_data={"entities": entities}
        )
        
        return {
            "success": True,
            "action": "create_memo",
            "message": f"'{content}' 메모를 저장했습니다.",
            "data": {
                "memo_id": str(memo.id),
                "content": memo.content,
                "tags": memo.tags,
                "priority": memo.priority
            }
        }
    
    async def _handle_query_memo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle memo query"""
        search_query = entities.get("item_name")
        category = entities.get("category")
        priority = None
        
        if entities.get("priority"):
            priority_text = entities["priority"].lower()
            if "긴급" in priority_text or "높" in priority_text:
                priority = 3
        
        memos = self.memo_service.get_memos(
            user_id=user_id,
            search_query=search_query,
            tags=[category] if category else None,
            priority=priority,
            limit=5
        )
        
        if not memos:
            message = "조건에 맞는 메모를 찾을 수 없습니다."
        else:
            memo_list = [f"• {memo.content[:50]}..." if len(memo.content) > 50 else f"• {memo.content}" for memo in memos[:3]]
            message = f"{len(memos)}개의 메모를 찾았습니다:\n" + "\n".join(memo_list)
        
        return {
            "success": True,
            "action": "query_memo",
            "message": message,
            "data": {
                "memo_count": len(memos),
                "memos": [{
                    "id": str(memo.id),
                    "content": memo.content,
                    "tags": memo.tags,
                    "created_at": memo.created_at.isoformat()
                } for memo in memos]
            }
        }
    
    async def _handle_create_todo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle todo creation"""
        title = entities.get("item_name") or "할일"
        description = None
        priority = 1
        category = entities.get("category")
        due_date = None
        
        # Extract priority
        if entities.get("priority"):
            priority_text = entities["priority"].lower()
            if "긴급" in priority_text or "높" in priority_text:
                priority = 3
            elif "중요" in priority_text or "보통" in priority_text:
                priority = 2
        
        # Extract due date (basic parsing)
        if entities.get("date_time"):
            # This would need more sophisticated date parsing
            date_text = entities["date_time"]
            if "내일" in date_text:
                due_date = datetime.now() + timedelta(days=1)
            elif "다음주" in date_text:
                due_date = datetime.now() + timedelta(days=7)
        
        todo = self.todo_service.create_todo(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            category=category,
            extra_data={"entities": entities}
        )
        
        return {
            "success": True,
            "action": "create_todo",
            "message": f"'{title}' 할일을 추가했습니다.",
            "data": {
                "todo_id": str(todo.id),
                "title": todo.title,
                "priority": todo.priority,
                "status": todo.status,
                "due_date": todo.due_date.isoformat() if todo.due_date else None
            }
        }
    
    async def _handle_query_todo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle todo query"""
        status = None
        priority = None
        category = entities.get("category")
        
        # Extract status
        if entities.get("status"):
            status_text = entities["status"].lower()
            if "완료" in status_text:
                status = "completed"
            elif "진행" in status_text:
                status = "in_progress"
            else:
                status = "pending"
        
        if entities.get("priority"):
            priority_text = entities["priority"].lower()
            if "긴급" in priority_text or "높" in priority_text:
                priority = 3
        
        todos = self.todo_service.get_todos(
            user_id=user_id,
            status=status,
            priority=priority,
            category=category,
            limit=5
        )
        
        if not todos:
            message = "조건에 맞는 할일을 찾을 수 없습니다."
        else:
            todo_list = [f"• [{todo.status}] {todo.title}" for todo in todos[:3]]
            message = f"{len(todos)}개의 할일을 찾았습니다:\n" + "\n".join(todo_list)
        
        return {
            "success": True,
            "action": "query_todo",
            "message": message,
            "data": {
                "todo_count": len(todos),
                "todos": [{
                    "id": str(todo.id),
                    "title": todo.title,
                    "status": todo.status,
                    "priority": todo.priority,
                    "due_date": todo.due_date.isoformat() if todo.due_date else None
                } for todo in todos]
            }
        }
    
    # Placeholder methods for other intents
    async def _handle_update_memo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        return {"success": True, "action": "update_memo", "message": "메모 수정 기능은 아직 구현 중입니다."}
    
    async def _handle_delete_memo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        return {"success": True, "action": "delete_memo", "message": "메모 삭제 기능은 아직 구현 중입니다."}
    
    async def _handle_update_todo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        return {"success": True, "action": "update_todo", "message": "할일 수정 기능은 아직 구현 중입니다."}
    
    async def _handle_complete_todo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        return {"success": True, "action": "complete_todo", "message": "할일 완료 기능은 아직 구현 중입니다."}
    
    async def _handle_delete_todo(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        return {"success": True, "action": "delete_todo", "message": "할일 삭제 기능은 아직 구현 중입니다."}

# Global service instances
memo_service = MemoService()
todo_service = TodoService()
intent_mapper = IntentActionMapper()

def get_memo_service() -> MemoService:
    """Get memo service singleton"""
    return memo_service

def get_todo_service() -> TodoService:
    """Get todo service singleton"""
    return todo_service

def get_intent_mapper() -> IntentActionMapper:
    """Get intent action mapper singleton"""
    return intent_mapper