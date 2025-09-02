# test_integration.py

import pytest
from fastapi.testclient import TestClient
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, get_db

# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Initialize test database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE source (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        published_date TEXT DEFAULT (DATE('now')),
        word_count INTEGER,
        source_id INTEGER,
        FOREIGN KEY (source_id) REFERENCES source(id)
    )
    ''')
    
    # Insert test sources
    cursor.execute("INSERT INTO source (name, url) VALUES (?, ?)", 
                   ("Test Health Daily", "https://test-health.com"))
    cursor.execute("INSERT INTO source (name, url) VALUES (?, ?)", 
                   ("Test Wellness News", "https://test-wellness.com"))
    
    # Insert test articles
    cursor.execute("""
        INSERT INTO articles (title, content, published_date, word_count, source_id) 
        VALUES (?, ?, ?, ?, ?)
    """, ("Test Yoga Article", "This is test yoga content for flexibility.", "2025-08-01", 9, 1))
    
    cursor.execute("""
        INSERT INTO articles (title, content, published_date, word_count, source_id) 
        VALUES (?, ?, ?, ?, ?)
    """, ("Test HIIT Workout", "High intensity training content here.", "2025-08-02", 6, 1))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with test database"""
    def override_get_db():
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()

# ============ SOURCE TESTS ============

class TestSources:
    
    def test_get_all_sources(self, client):
        """Test getting all sources"""
        response = client.get("/api/sources")
        assert response.status_code == 200
        sources = response.json()
        assert len(sources) == 2
        assert sources[0]["name"] == "Test Health Daily"
        assert sources[1]["name"] == "Test Wellness News"
    
    def test_get_source_by_id(self, client):
        """Test getting a specific source"""
        response = client.get("/api/sources/1")
        assert response.status_code == 200
        source = response.json()
        assert source["name"] == "Test Health Daily"
        assert source["url"] == "https://test-health.com"
    
    def test_get_source_not_found(self, client):
        """Test getting non-existent source"""
        response = client.get("/api/sources/999")
        assert response.status_code == 404
        assert "Source not found" in response.json()["detail"]
    
    def test_create_source(self, client):
        """Test creating a new source"""
        new_source = {
            "name": "New Fitness Blog",
            "url": "https://newfitness.com"
        }
        response = client.post("/api/sources", json=new_source)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Source created successfully"
        assert "id" in data
        
        # Verify source was created
        response = client.get(f"/api/sources/{data['id']}")
        assert response.status_code == 200
        source = response.json()
        assert source["name"] == "New Fitness Blog"
    
    def test_create_source_missing_name(self, client):
        """Test creating source without required name"""
        response = client.post("/api/sources", json={"url": "https://test.com"})
        assert response.status_code == 422  # Validation error
    
    def test_update_source(self, client):
        """Test updating a source"""
        update_data = {"name": "Updated Health Daily"}
        response = client.put("/api/sources/1", json=update_data)
        assert response.status_code == 200
        assert response.json()["message"] == "Source updated successfully"
        
        # Verify update
        response = client.get("/api/sources/1")
        source = response.json()
        assert source["name"] == "Updated Health Daily"
    
    def test_update_source_not_found(self, client):
        """Test updating non-existent source"""
        response = client.put("/api/sources/999", json={"name": "Test"})
        assert response.status_code == 404
    
    def test_delete_source_with_articles(self, client):
        """Test deleting source that has articles (should fail)"""
        response = client.delete("/api/sources/1")
        assert response.status_code == 400
        assert "Cannot delete source with existing articles" in response.json()["detail"]
    
    def test_delete_source_success(self, client):
        """Test successfully deleting source without articles"""
        # First delete all articles from source 2
        response = client.get("/api/articles?source_id=2")
        articles = response.json()
        for article in articles:
            client.delete(f"/api/articles/{article['id']}")
        
        # Now delete the source
        response = client.delete("/api/sources/2")
        assert response.status_code == 200
        assert response.json()["message"] == "Source deleted successfully"
        
        # Verify deletion
        response = client.get("/api/sources/2")
        assert response.status_code == 404

# ============ ARTICLE TESTS ============

class TestArticles:
    
    def test_get_all_articles(self, client):
        """Test getting all articles"""
        response = client.get("/api/articles")
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) == 2
        assert articles[0]["title"] in ["Test Yoga Article", "Test HIIT Workout"]
    
    def test_get_articles_with_search(self, client):
        """Test searching articles"""
        response = client.get("/api/articles?search=yoga")
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Yoga Article"
    
    def test_get_articles_with_source_filter(self, client):
        """Test filtering articles by source"""
        response = client.get("/api/articles?source_id=1")
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) == 2
        for article in articles:
            assert article["source_id"] == 1
    
    def test_get_articles_with_pagination(self, client):
        """Test article pagination"""
        response = client.get("/api/articles?limit=1&offset=0")
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) == 1
        
        response = client.get("/api/articles?limit=1&offset=1")
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) == 1
    
    def test_get_article_by_id(self, client):
        """Test getting specific article"""
        response = client.get("/api/articles/1")
        assert response.status_code == 200
        article = response.json()
        assert article["title"] == "Test Yoga Article"
        assert article["source_name"] == "Test Health Daily"
    
    def test_get_article_not_found(self, client):
        """Test getting non-existent article"""
        response = client.get("/api/articles/999")
        assert response.status_code == 404
    
    def test_create_article(self, client):
        """Test creating a new article"""
        new_article = {
            "title": "New Test Article",
            "content": "This is new test content for our article.",
            "source_id": 1
        }
        response = client.post("/api/articles", json=new_article)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Article created successfully"
        
        # Verify article was created with correct word count
        response = client.get(f"/api/articles/{data['id']}")
        article = response.json()
        assert article["title"] == "New Test Article"
        assert article["word_count"] == 10  # Word count should be calculated
    
    def test_create_article_missing_title(self, client):
        """Test creating article without required title"""
        response = client.post("/api/articles", json={"content": "Test content"})
        assert response.status_code == 422  # Validation error
    
    def test_update_article(self, client):
        """Test updating an article"""
        update_data = {
            "title": "Updated Yoga Article",
            "content": "Updated content for yoga practice."
        }
        response = client.put("/api/articles/1", json=update_data)
        assert response.status_code == 200
        
        # Verify update and word count recalculation
        response = client.get("/api/articles/1")
        article = response.json()
        assert article["title"] == "Updated Yoga Article"
        assert article["word_count"] == 6  # New word count
    
    def test_update_article_not_found(self, client):
        """Test updating non-existent article"""
        response = client.put("/api/articles/999", json={"title": "Test"})
        assert response.status_code == 404
    
    def test_delete_article(self, client):
        """Test deleting an article"""
        response = client.delete("/api/articles/1")
        assert response.status_code == 200
        assert response.json()["message"] == "Article deleted successfully"
        
        # Verify deletion
        response = client.get("/api/articles/1")
        assert response.status_code == 404
    
    def test_delete_article_not_found(self, client):
        """Test deleting non-existent article"""
        response = client.delete("/api/articles/999")
        assert response.status_code == 404

# ============ STATISTICS TESTS ============

class TestStats:
    
    def test_get_stats(self, client):
        """Test getting database statistics"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        stats = response.json()
        
        assert stats["total_articles"] == 2
        assert stats["total_sources"] == 2
        assert stats["average_word_count"] > 0
        assert len(stats["articles_by_source"]) == 2
        
        # Check articles by source structure
        source_stats = stats["articles_by_source"][0]
        assert "name" in source_stats
        assert "article_count" in source_stats

# ============ HEALTH CHECK TESTS ============

class TestHealth:
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
        assert health["database"] == "connected"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Health & Fitness Articles API" in data["message"]
        assert data["documentation"] == "/docs"

# ============ ERROR HANDLING TESTS ============

class TestErrorHandling:
    
    def test_invalid_json(self, client):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/sources",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test POST without JSON content type"""
        response = client.post("/api/sources", data='{"name": "test"}')
        assert response.status_code == 422

# ============ INTEGRATION TESTS ============

class TestIntegration:
    
    def test_full_article_workflow(self, client):
        """Test complete article creation workflow"""
        # Create a new source
        source_data = {"name": "Integration Test Source", "url": "https://integration.test"}
        response = client.post("/api/sources", json=source_data)
        source_id = response.json()["id"]
        
        # Create article with new source
        article_data = {
            "title": "Integration Test Article",
            "content": "This is a comprehensive integration test article content.",
            "source_id": source_id
        }
        response = client.post("/api/articles", json=article_data)
        article_id = response.json()["id"]
        
        # Verify article shows up in source's articles
        response = client.get(f"/api/articles?source_id={source_id}")
        articles = response.json()
        assert len(articles) == 1
        assert articles[0]["id"] == article_id
        
        # Update the article
        response = client.put(f"/api/articles/{article_id}", 
                             json={"title": "Updated Integration Test"})
        assert response.status_code == 200
        
        # Verify statistics updated
        response = client.get("/api/stats")
        stats = response.json()
        assert stats["total_articles"] == 3  # 2 original + 1 new
        assert stats["total_sources"] == 3   # 2 original + 1 new