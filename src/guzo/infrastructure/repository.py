from typing import TypeVar, Generic, Optional, List, Type
from beanie import Document
from pydantic import BaseModel

T = TypeVar("T", bound=Document)


class BaseRepository(Generic[T]):
    """Base repository class for database operations."""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get a document by ID."""
        return await self.model.get(id)
    
    async def get_all(self, limit: int = 100, skip: int = 0) -> List[T]:
        """Get all documents with pagination."""
        return await self.model.find_all().skip(skip).limit(limit).to_list()
    
    async def create(self, document: T) -> T:
        """Create a new document."""
        await document.insert()
        return document
    
    async def update(self, id: str, data: dict) -> Optional[T]:
        """Update a document by ID."""
        document = await self.get_by_id(id)
        if document:
            await document.update({"$set": data})
            return await self.get_by_id(id)
        return None
    
    async def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        document = await self.get_by_id(id)
        if document:
            await document.delete()
            return True
        return False
    
    async def find_one(self, query: dict) -> Optional[T]:
        """Find a single document matching the query."""
        return await self.model.find_one(query)
    
    async def find_many(self, query: dict, limit: int = 100) -> List[T]:
        """Find multiple documents matching the query."""
        return await self.model.find(query).limit(limit).to_list()
    
    async def count(self, query: dict = None) -> int:
        """Count documents matching the query."""
        if query:
            return await self.model.find(query).count()
        return await self.model.find_all().count()

