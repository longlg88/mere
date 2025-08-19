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
from calendar_service import get_calendar_processor

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
                   priority: int = 1, metadata: Dict = None, extra_data: Dict = None, target_date = None) -> Memo:
        """Create a new memo"""
        db = SessionLocal()
        try:
            # Ensure user exists
            user = self.user_service.get_or_create_user(user_id)
            
            # 목적 날짜가 있으면 그 날짜로, 없으면 현재 시간 사용
            created_at = target_date if target_date else datetime.utcnow()
            
            memo = Memo(
                user_id=user.id,
                content=content,
                tags=tags or [],
                priority=priority,
                created_at=created_at,
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
    
    def get_memos_by_date(self, user_id: str, target_date) -> List[Memo]:
        """Get memos for a specific date"""
        db = SessionLocal()
        try:
            from datetime import datetime, time
            
            # Get the user object first
            user = self.user_service.get_or_create_user(user_id)
            
            # Convert date to datetime range for the full day
            start_datetime = datetime.combine(target_date, time.min)
            end_datetime = datetime.combine(target_date, time.max)
            
            memos = db.query(Memo).filter(
                Memo.user_id == user.id,  # Use the actual UUID from user object
                Memo.created_at >= start_datetime,
                Memo.created_at <= end_datetime
            ).order_by(Memo.created_at.desc()).all()
            
            logger.info(f"Retrieved {len(memos)} memos for user {user_id} on date {target_date}")
            return memos
            
        except Exception as e:
            logger.error(f"Failed to get memos by date: {e}")
            return []
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
    
    def get_todos_by_date(self, user_id: str, target_date) -> List[Todo]:
        """Get todos for a specific date (by due_date or created_at)"""
        db = SessionLocal()
        try:
            from datetime import datetime, time
            user = self.user_service.get_or_create_user(user_id)
            
            # Convert date to datetime range for the full day
            start_datetime = datetime.combine(target_date, time.min)
            end_datetime = datetime.combine(target_date, time.max)
            
            # Search by both due_date and created_at
            todos = db.query(Todo).filter(
                Todo.user_id == user.id
            ).filter(
                # Either due on this date OR created on this date
                (Todo.due_date >= start_datetime) & (Todo.due_date <= end_datetime) |
                (Todo.created_at >= start_datetime) & (Todo.created_at <= end_datetime)
            ).order_by(Todo.priority.desc(), Todo.created_at.desc()).all()
            
            logger.info(f"Retrieved {len(todos)} todos for user {user_id} on date {target_date}")
            return todos
            
        except Exception as e:
            logger.error(f"Failed to get todos by date: {e}")
            return []
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
        self.calendar_processor = get_calendar_processor()
    
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
            
            # Calendar-related intents
            elif intent_name == "create_event":
                return await self._handle_create_event(user_id, entities)
            elif intent_name == "query_event":
                return await self._handle_query_event(user_id, entities)
            elif intent_name == "update_event":
                return await self._handle_update_event(user_id, entities)
            elif intent_name == "cancel_event":
                return await self._handle_cancel_event(user_id, entities)
            
            # Search-related intents
            elif intent_name == "search_by_date":
                return await self._handle_search_by_date(user_id, entities)
            elif intent_name == "search_general":
                return await self._handle_search_general(user_id, entities)
            elif intent_name == "search_by_category":
                return await self._handle_search_by_category(user_id, entities)
            
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
        # 메모 내용을 더 풍부하게 추출
        content_parts = []
        
        # 날짜/시간 정보 추가
        if entities.get("date_time"):
            content_parts.append(entities["date_time"])
        
        # 주요 아이템/행동 추가
        if entities.get("item_name"):
            item = entities["item_name"]
            # "~기" 형태면 "~러 간다"로 확장
            if item.endswith("기") and len(item) > 1:
                base = item[:-1]  # "장보" 
                content_parts.append(f"{base}러 간다")
            else:
                content_parts.append(item)
        
        # 추가 컨텍스트
        if entities.get("location"):
            content_parts.append(f"@ {entities['location']}")
        
        if entities.get("time"):
            content_parts.append(f"시간: {entities['time']}")
        
        # 최종 메모 내용 구성
        if content_parts:
            content = " ".join(content_parts)
        else:
            content = "메모 내용"
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
        
        # 메모 생성시 날짜 정보 반영
        target_date = None
        if entities.get("parsed_datetime"):
            try:
                from datetime import datetime
                target_date = datetime.fromisoformat(entities["parsed_datetime"].replace('Z', '+00:00'))
            except:
                pass
        
        memo = self.memo_service.create_memo(
            user_id=user_id,
            content=content,
            tags=tags,
            priority=priority,
            target_date=target_date,  # 특정 날짜 지정
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
    
    # Calendar intent handlers
    async def _handle_create_event(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle calendar event creation"""
        try:
            result = self.calendar_processor.process_create_event_intent(entities)
            return {
                "success": result["success"],
                "action": "create_event",
                "message": result["message"],
                "data": result.get("event_id"),
                "requires_confirmation": result.get("requires_confirmation", False)
            }
        except Exception as e:
            logger.error(f"Calendar event creation error: {e}")
            return {
                "success": False,
                "action": "create_event",
                "message": "일정 생성 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    async def _handle_query_event(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle calendar event query"""
        try:
            result = self.calendar_processor.process_query_event_intent(entities)
            return {
                "success": result["success"],
                "action": "query_event", 
                "message": result["message"],
                "data": result.get("events", [])
            }
        except Exception as e:
            logger.error(f"Calendar event query error: {e}")
            return {
                "success": False,
                "action": "query_event",
                "message": "일정 조회 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    async def _handle_update_event(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle calendar event update"""
        try:
            result = self.calendar_processor.process_update_event_intent(entities)
            return {
                "success": result["success"],
                "action": "update_event",
                "message": result["message"],
                "requires_confirmation": result.get("requires_confirmation", False)
            }
        except Exception as e:
            logger.error(f"Calendar event update error: {e}")
            return {
                "success": False,
                "action": "update_event",
                "message": "일정 수정 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    async def _handle_cancel_event(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle calendar event cancellation"""
        try:
            result = self.calendar_processor.process_cancel_event_intent(entities)
            return {
                "success": result["success"],
                "action": "cancel_event",
                "message": result["message"],
                "requires_confirmation": result.get("requires_confirmation", False)
            }
        except Exception as e:
            logger.error(f"Calendar event cancellation error: {e}")
            return {
                "success": False,
                "action": "cancel_event", 
                "message": "일정 취소 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    # Search handlers
    async def _handle_search_by_date(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle search by date (e.g., '나 내일 뭐해?')"""
        try:
            from datetime import datetime, timedelta
            
            # Parse date from entities
            date_time_str = entities.get("date_time", "")
            parsed_datetime_str = entities.get("parsed_datetime", "")
            
            # Determine the target date
            target_date = None
            if parsed_datetime_str:
                try:
                    target_date = datetime.fromisoformat(parsed_datetime_str.replace('Z', '+00:00')).date()
                except:
                    pass
            
            if not target_date:
                # Default to tomorrow if no specific date
                target_date = (datetime.now() + timedelta(days=1)).date()
            
            # Search across all data types for the target date
            results = []
            
            # Search memos
            memos = self.memo_service.get_memos_by_date(user_id, target_date)
            for memo in memos:
                content = memo.content or "내용 없음"
                results.append({
                    "type": "memo",
                    "id": str(memo.id),
                    "title": content[:30] + "..." if len(content) > 30 else content,  # Use content as title
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "created_at": memo.created_at.isoformat()
                })
            
            # Search todos  
            todos = self.todo_service.get_todos_by_date(user_id, target_date)
            for todo in todos:
                results.append({
                    "type": "todo", 
                    "id": str(todo.id),
                    "title": todo.title or "제목 없음",
                    "completed": todo.status == "completed",
                    "status": todo.status,
                    "due_date": todo.due_date.isoformat() if todo.due_date else None
                })
            
            # Search events (calendar items)
            events = self.calendar_processor.get_events_by_date(target_date)
            for event in events:
                results.append({
                    "type": "event",
                    "id": event.get("id", "unknown"),
                    "title": event.get("title", "제목 없음"),
                    "start_time": event.get("start_time"),
                    "location": event.get("location")
                })
            
            # GPT를 활용한 자연스러운 응답 생성
            date_str = target_date.strftime("%Y년 %m월 %d일")
            if results:
                message = await self._generate_natural_schedule_response(date_str, results)
            else:
                message = f"{date_str}에는 등록된 메모, 할일, 일정이 없습니다."
            
            return {
                "success": True,
                "action": "search_by_date",
                "message": message,
                "data": {
                    "target_date": target_date.isoformat(),
                    "results": results,
                    "count": len(results)
                }
            }
            
        except Exception as e:
            logger.error(f"Search by date error: {e}")
            return {
                "success": False,
                "action": "search_by_date",
                "message": f"날짜별 검색 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }
    
    async def _handle_search_general(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle general search"""
        return {
            "success": True,
            "action": "search_general", 
            "message": "일반 검색 기능은 아직 구현되지 않았습니다.",
            "data": None
        }
    
    async def _handle_search_by_category(self, user_id: str, entities: Dict) -> Dict[str, Any]:
        """Handle search by category"""
        return {
            "success": True,
            "action": "search_by_category",
            "message": "카테고리별 검색 기능은 아직 구현되지 않았습니다.", 
            "data": None
        }
    
    async def _generate_natural_schedule_response(self, date_str: str, results: list) -> str:
        """GPT를 활용해서 자연스러운 일정 응답 생성"""
        try:
            import asyncio
            
            # 결과 데이터를 간단하게 정리
            items_summary = []
            for item in results:
                if item["type"] == "memo":
                    items_summary.append(f"메모: {item['content']}")
                elif item["type"] == "todo":
                    status = "완료됨" if item["completed"] else "해야 할 일"
                    items_summary.append(f"할일: {item['title']} ({status})")
                elif item["type"] == "event":
                    items_summary.append(f"일정: {item['title']}")
            
            # GPT를 활용한 자연스러운 응답 생성
            system_prompt = """당신은 개인 비서입니다. 사용자의 일정과 메모를 자연스럽고 친근한 방식으로 알려주세요.

요구사항:
- 정중하면서도 친근한 말투 사용
- 불필요한 기호나 특수문자는 피하고 깔끔하게
- 각 항목을 자연스럽게 나열
- 실제 내용을 간단명료하게 전달
- 개인 비서처럼 자연스럽게

예시:
"내일은 다음과 같은 일정이 있으시네요.
장보러 가실 예정이시고,
오후 2시에 회의가 있습니다.
그리고 운동 계획이 있으시네요."
"""
            
            user_prompt = f"{date_str}에 다음 항목들이 있습니다: " + ", ".join(items_summary) + "\n\n이를 개인 비서처럼 자연스럽고 친근하게 알려주세요."
            
            # OpenAI API 호출
            try:
                from openai import OpenAI
                import os
                
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=200,
                        temperature=0.7
                    )
                )
                
                natural_response = response.choices[0].message.content.strip()
                return natural_response
                
            except Exception as gpt_error:
                logger.warning(f"GPT 응답 생성 실패: {gpt_error}")
                return self._generate_simple_schedule_response(date_str, results)
                
        except Exception as e:
            logger.error(f"자연스러운 응답 생성 실패: {e}")
            return self._generate_simple_schedule_response(date_str, results)
    
    def _generate_simple_schedule_response(self, date_str: str, results: list) -> str:
        """간단하고 깔끔한 기본 응답 생성"""
        lines = [f"{date_str}에 다음 항목들이 있습니다."]
        
        for item in results:
            if item["type"] == "memo":
                lines.append(f"메모로 {item['content']}")
            elif item["type"] == "todo":
                status = " (완료)" if item["completed"] else ""
                lines.append(f"할일로 {item['title']}{status}")
            elif item["type"] == "event":
                lines.append(f"일정으로 {item['title']}")
        
        return ". ".join(lines) + "이 예정되어 있습니다."

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