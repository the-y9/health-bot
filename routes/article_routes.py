from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from contextlib import contextmanager

router = APIRouter(prefix="/articles", tags=["articles"])

DATABASE = 'database.db'

# Pydantic models for request/response validation
class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = ""
    published_date: Optional[str] = None
    source_id: Optional[int] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published_date: Optional[str] = None
    source_id: Optional[int] = None

class Article(ArticleBase):
    id: int
    word_count: int
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Database connection management
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ============ ARTICLE ENDPOINTS ============

@router.post("/", response_model=dict, status_code=201)
async def create_article(article: ArticleCreate):
    """Insert a new article"""
    try:
        # Calculate word count
        content = article.content or ""
        word_count = len(content.split()) if content else 0
        
        # Default to source_id = 1 if not specified (as per instructions)
        source_id = article.source_id if article.source_id is not None else 1
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO articles (title, content, published_date, word_count, source_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                article.title,
                content,
                article.published_date,
                word_count,
                source_id
            ))
            db.commit()
            
            article_id = cursor.lastrowid
            return {"id": article_id, "message": "Article created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Article])
async def get_articles(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get all articles with optional filtering"""
    try:
        with get_db() as db:
            # Build query
            query = '''
                SELECT a.*, s.name as source_name, s.url as source_url
                FROM articles a
                LEFT JOIN source s ON a.source_id = s.id
            '''
            params = []
            
            # Add filters
            conditions = []
            if source_id:
                conditions.append('a.source_id = ?')
                params.append(source_id)
            
            if search:
                conditions.append('(a.title LIKE ? OR a.content LIKE ?)')
                params.extend([f'%{search}%', f'%{search}%'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY a.published_date DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            if offset:
                query += ' OFFSET ?'
                params.append(offset)
            
            articles = db.execute(query, params).fetchall()
            return [dict(article) for article in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{article_id}", response_model=Article)
async def get_article(article_id: int):
    """Get a single article by ID"""
    try:
        with get_db() as db:
            article = db.execute('''
                SELECT a.*, s.name as source_name, s.url as source_url
                FROM articles a
                LEFT JOIN source s ON a.source_id = s.id
                WHERE a.id = ?
            ''', (article_id,)).fetchone()
            
            if article is None:
                raise HTTPException(status_code=404, detail="Article not found")
            return dict(article)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{article_id}", response_model=dict)
async def update_article(article_id: int, article: ArticleUpdate):
    """Update an article"""
    try:
        with get_db() as db:
            # Check if article exists
            existing = db.execute('SELECT id FROM articles WHERE id = ?', (article_id,)).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Build update query dynamically
            fields = []
            params = []
            
            if article.title is not None:
                fields.append('title = ?')
                params.append(article.title)
            
            if article.content is not None:
                fields.append('content = ?')
                fields.append('word_count = ?')
                word_count = len(article.content.split()) if article.content else 0
                params.extend([article.content, word_count])
            
            if article.published_date is not None:
                fields.append('published_date = ?')
                params.append(article.published_date)
            
            if article.source_id is not None:
                fields.append('source_id = ?')
                params.append(article.source_id)
            
            if not fields:
                raise HTTPException(status_code=400, detail="No valid fields to update")
            
            params.append(article_id)
            query = f'UPDATE articles SET {", ".join(fields)} WHERE id = ?'
            
            db.execute(query, params)
            db.commit()
            
            return {"message": "Article updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{article_id}", response_model=dict)
async def delete_article(article_id: int):
    """Delete an article"""
    try:
        with get_db() as db:
            # Check if article exists
            existing = db.execute('SELECT id FROM articles WHERE id = ?', (article_id,)).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Article not found")
            
            db.execute('DELETE FROM articles WHERE id = ?', (article_id,))
            db.commit()
            
            return {"message": "Article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))