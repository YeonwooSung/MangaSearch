# ============================================================================
# Manga Database API - Complete Sample Queries
# Base URL: http://localhost:8000
# ============================================================================

# ============================================================================
# 1. HEALTH CHECK & STATS
# ============================================================================

# Health check
curl -X GET "http://localhost:8000/health"

# Database statistics
curl -X GET "http://localhost:8000/stats"

# Year distribution
curl -X GET "http://localhost:8000/stats/year-distribution"

# Rating distribution  
curl -X GET "http://localhost:8000/stats/rating-distribution"

# ============================================================================
# 2. MANGA CRUD OPERATIONS
# ============================================================================

# Get manga by ID
curl -X GET "http://localhost:8000/manga/1"

# Get manga list with filters
curl -X GET "http://localhost:8000/manga?skip=0&limit=20&status=completed&min_rating=8.0&year=2020"

# Get manga count
curl -X GET "http://localhost:8000/manga/count?status=ongoing&min_rating=7.0"

# Create new manga
curl -X POST "http://localhost:8000/manga" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Manga",
    "native_title": "サンプル漫画",
    "romanized_title": "Sanpuru Manga",
    "description": "A sample manga for testing the API",
    "year": 2024,
    "status": "ongoing",
    "is_licensed": true,
    "has_anime": false,
    "content_rating": "PG-13",
    "type": "manga",
    "rating": 8.5,
    "author_ids": [1, 2],
    "artist_ids": [1],
    "genre_ids": [1, 2, 3],
    "tag_ids": [1, 2, 3, 4]
  }'

# Update manga
curl -X PUT "http://localhost:8000/manga/1" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 9.2,
    "status": "completed",
    "description": "Updated description with more details",
    "genre_ids": [1, 2, 3, 5]
  }'

# Delete manga
curl -X DELETE "http://localhost:8000/manga/1"

# ============================================================================
# 3. BULK OPERATIONS
# ============================================================================

# Bulk create manga
curl -X POST "http://localhost:8000/manga/bulk" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "Bulk Manga 1",
      "description": "First bulk manga",
      "year": 2024,
      "rating": 7.5,
      "author_ids": [1],
      "genre_ids": [1, 2]
    },
    {
      "title": "Bulk Manga 2", 
      "description": "Second bulk manga",
      "year": 2024,
      "rating": 8.0,
      "author_ids": [2],
      "genre_ids": [2, 3]
    }
  ]'

# Export manga data as JSON
curl -X GET "http://localhost:8000/manga/bulk/export?limit=100&offset=0&format=json"

# Export manga data as CSV
curl -X GET "http://localhost:8000/manga/bulk/export?limit=100&offset=0&format=csv" \
  --output manga_export.csv

# ============================================================================
# 4. AUTHOR MANAGEMENT
# ============================================================================

# Get authors list
curl -X GET "http://localhost:8000/authors?skip=0&limit=50"

# Search authors
curl -X GET "http://localhost:8000/authors?search=akira&limit=10"

# Get authors count
curl -X GET "http://localhost:8000/authors/count"

# Create author
curl -X POST "http://localhost:8000/authors" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Akira Toriyama"
  }'

# Get specific author
curl -X GET "http://localhost:8000/authors/1"

# Update author
curl -X PUT "http://localhost:8000/authors/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Akira Toriyama (Updated)"
  }'

# Get author manga count
curl -X GET "http://localhost:8000/authors/1/manga-count"

# Delete author
curl -X DELETE "http://localhost:8000/authors/1"

# ============================================================================
# 5. ARTIST MANAGEMENT
# ============================================================================

# Get artists list
curl -X GET "http://localhost:8000/artists?skip=0&limit=50&search=studio"

# Create artist
curl -X POST "http://localhost:8000/artists" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Studio Pierrot"
  }'

# Get specific artist
curl -X GET "http://localhost:8000/artists/1"

# Update artist
curl -X PUT "http://localhost:8000/artists/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Studio Pierrot Animation"
  }'

# Get artist manga count
curl -X GET "http://localhost:8000/artists/1/manga-count"

# ============================================================================
# 6. PUBLISHER MANAGEMENT
# ============================================================================

# Get publishers
curl -X GET "http://localhost:8000/publishers?limit=30"

# Create publisher
curl -X POST "http://localhost:8000/publishers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Shueisha"
  }'

# Get specific publisher
curl -X GET "http://localhost:8000/publishers/1"

# Get publisher manga count
curl -X GET "http://localhost:8000/publishers/1/manga-count"

# ============================================================================
# 7. GENRE MANAGEMENT
# ============================================================================

# Get genres
curl -X GET "http://localhost:8000/genres?limit=50"

# Get popular genres
curl -X GET "http://localhost:8000/genres/popular?limit=20"

# Create genre
curl -X POST "http://localhost:8000/genres" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Isekai"
  }'

# Get specific genre
curl -X GET "http://localhost:8000/genres/1"

# Get genre manga count
curl -X GET "http://localhost:8000/genres/1/manga-count"

# ============================================================================
# 8. TAG MANAGEMENT
# ============================================================================

# Get tags
curl -X GET "http://localhost:8000/tags?skip=0&limit=100"

# Get popular tags
curl -X GET "http://localhost:8000/tags/popular?limit=50"

# Search tags
curl -X GET "http://localhost:8000/tags?search=school&limit=20"

# Create tag
curl -X POST "http://localhost:8000/tags" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Time Travel"
  }'

# Get specific tag
curl -X GET "http://localhost:8000/tags/1"

# ============================================================================
# 9. MANGA COVERS MANAGEMENT
# ============================================================================

# Get covers for a manga
curl -X GET "http://localhost:8000/manga/1/covers"

# Create manga cover
curl -X POST "http://localhost:8000/manga/covers" \
  -H "Content-Type: application/json" \
  -d '{
    "manga_id": 1,
    "type": "default",
    "url": "https://example.com/cover.jpg",
    "width": 800,
    "height": 1200
  }'

# Get specific cover
curl -X GET "http://localhost:8000/manga/covers/1"

# Update cover
curl -X PUT "http://localhost:8000/manga/covers/1" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "large",
    "url": "https://example.com/large_cover.jpg",
    "width": 1600,
    "height": 2400
  }'

# Delete cover
curl -X DELETE "http://localhost:8000/manga/covers/1"

# ============================================================================
# 10. SECONDARY TITLES MANAGEMENT
# ============================================================================

# Get secondary titles for a manga
curl -X GET "http://localhost:8000/manga/1/secondary-titles"

# Create secondary title
curl -X POST "http://localhost:8000/manga/secondary-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "manga_id": 1,
    "language_code": "en",
    "title": "Alternative English Title",
    "type": "official",
    "note": "Official English localization"
  }'

# Get specific secondary title
curl -X GET "http://localhost:8000/manga/secondary-titles/1"

# Update secondary title
curl -X PUT "http://localhost:8000/manga/secondary-titles/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Alternative Title",
    "type": "unofficial"
  }'

# ============================================================================
# 11. MANGA LINKS MANAGEMENT
# ============================================================================

# Get links for a manga
curl -X GET "http://localhost:8000/manga/1/links"

# Create manga link
curl -X POST "http://localhost:8000/manga/links" \
  -H "Content-Type: application/json" \
  -d '{
    "manga_id": 1,
    "url": "https://myanimelist.net/manga/1",
    "link_type": "official"
  }'

# Get specific link
curl -X GET "http://localhost:8000/manga/links/1"

# Update link
curl -X PUT "http://localhost:8000/manga/links/1" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://anilist.co/manga/1",
    "link_type": "database"
  }'

# ============================================================================
# 12. BASIC SEARCH
# ============================================================================

# Basic BM25 search
curl -X POST "http://localhost:8000/manga/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "action adventure",
    "limit": 20,
    "offset": 0
  }'

# Advanced search with filters
curl -X POST "http://localhost:8000/manga/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "romance school",
    "min_rating": 7.0,
    "max_rating": 10.0,
    "year_from": 2010,
    "year_to": 2024,
    "genres": ["Romance", "School Life"],
    "status": "completed",
    "limit": 30
  }'

# Search suggestions
curl -X GET "http://localhost:8000/manga/search/suggestions?query=naru&limit=5"

# ============================================================================
# 13. FUZZY SEARCH
# ============================================================================

# Advanced fuzzy search with all options
curl -X POST "http://localhost:8000/manga/search/fuzzy" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "attack on titna",
    "search_fields": ["all"],
    "fuzzy_distance": 3,
    "boost_exact_matches": true,
    "min_similarity": 0.3,
    "min_rating": 8.0,
    "year_from": 2009,
    "year_to": 2023,
    "status": "completed",
    "limit": 20
  }'

# Fuzzy search suggestions
curl -X GET "http://localhost:8000/manga/search/fuzzy/suggestions?query=narto&limit=10&fuzzy_distance=2"

# Field-specific fuzzy search
curl -X GET "http://localhost:8000/manga/search/fuzzy/field/title?query=demon slyer&fuzzy_distance=2&limit=15"

# Description-only fuzzy search
curl -X GET "http://localhost:8000/manga/search/fuzzy/field/description?query=magic scool&fuzzy_distance=3&limit=10"

# ============================================================================
# 14. PYTHON REQUESTS EXAMPLES
# ============================================================================

# Python examples using requests library
cat > sample_queries.py << 'EOF'
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Health check
response = requests.get(f"{BASE_URL}/health")
print("Health Check:", response.json())

# 2. Get manga list with filters
params = {
    "skip": 0,
    "limit": 10,
    "status": "ongoing",
    "min_rating": 8.0
}
response = requests.get(f"{BASE_URL}/manga", params=params)
print("Manga List:", len(response.json()), "items")

# 3. Create new manga
manga_data = {
    "title": "Python Test Manga",
    "description": "Created via Python requests",
    "year": 2024,
    "rating": 8.5,
    "author_ids": [1],
    "genre_ids": [1, 2]
}
response = requests.post(f"{BASE_URL}/manga", json=manga_data)
if response.status_code == 200:
    new_manga = response.json()
    print("Created manga ID:", new_manga["id"])

# 4. Fuzzy search
search_data = {
    "query": "one peice",  # Typo intentional
    "search_fields": ["title"],
    "fuzzy_distance": 2,
    "limit": 5
}
response = requests.post(f"{BASE_URL}/manga/search/fuzzy", json=search_data)
results = response.json()
print("Fuzzy search results:", len(results))
for result in results:
    print(f"- {result['title']} (score: {result['relevance_score']:.2f})")

# 5. Get popular genres
response = requests.get(f"{BASE_URL}/genres/popular", params={"limit": 10})
popular_genres = response.json()
print("Popular genres:")
for genre in popular_genres:
    print(f"- {genre['name']}: {genre['manga_count']} manga")

# 6. Get database statistics
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print("Database stats:")
print(f"- Total manga: {stats['total_manga']}")
print(f"- Total authors: {stats['total_authors']}")
print(f"- Average rating: {stats['avg_rating']:.2f}")

EOF

# ============================================================================
# 15. COMPLEX WORKFLOW EXAMPLES
# ============================================================================

# Complete workflow: Create author, create manga, search, update
echo "=== Complete Workflow Example ==="

# 1. Create author
AUTHOR_RESPONSE=$(curl -s -X POST "http://localhost:8000/authors" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Author"}')
AUTHOR_ID=$(echo $AUTHOR_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Author ID: $AUTHOR_ID"

# 2. Create genre
GENRE_RESPONSE=$(curl -s -X POST "http://localhost:8000/genres" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Genre"}')
GENRE_ID=$(echo $GENRE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Genre ID: $GENRE_ID"

# 3. Create manga with author and genre
MANGA_RESPONSE=$(curl -s -X POST "http://localhost:8000/manga" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Workflow Test Manga\",
    \"description\": \"Testing complete workflow\",
    \"year\": 2024,
    \"rating\": 8.0,
    \"author_ids\": [$AUTHOR_ID],
    \"genre_ids\": [$GENRE_ID]
  }")
MANGA_ID=$(echo $MANGA_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Manga ID: $MANGA_ID"

# 4. Add cover to manga
curl -s -X POST "http://localhost:8000/manga/covers" \
  -H "Content-Type: application/json" \
  -d "{
    \"manga_id\": $MANGA_ID,
    \"type\": \"default\",
    \"url\": \"https://example.com/test-cover.jpg\",
    \"width\": 600,
    \"height\": 900
  }" > /dev/null
echo "Added cover to manga"

# 5. Search for the created manga
SEARCH_RESULT=$(curl -s -X POST "http://localhost:8000/manga/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Workflow Test",
    "limit": 5
  }')
echo "Search found manga: $(echo $SEARCH_RESULT | python3 -c "import sys, json; results=json.load(sys.stdin); print(len(results), 'results')")"

# 6. Get complete manga details
curl -s -X GET "http://localhost:8000/manga/$MANGA_ID" | python3 -m json.tool

echo "=== Workflow Complete ==="

# ============================================================================
# 16. PERFORMANCE TESTING QUERIES
# ============================================================================

# Test pagination performance
echo "=== Performance Test ==="
time curl -s -X GET "http://localhost:8000/manga?skip=0&limit=100" > /dev/null
time curl -s -X GET "http://localhost:8000/manga?skip=1000&limit=100" > /dev/null
time curl -s -X GET "http://localhost:8000/manga?skip=10000&limit=100" > /dev/null

# Test search performance
time curl -s -X POST "http://localhost:8000/manga/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "action adventure magic", "limit": 100}' > /dev/null

# Test fuzzy search performance
time curl -s -X POST "http://localhost:8000/manga/search/fuzzy" \
  -H "Content-Type: application/json" \
  -d '{"query": "actoin adventur magik", "fuzzy_distance": 3, "limit": 100}' > /dev/null

# ============================================================================
# 17. ERROR HANDLING EXAMPLES
# ============================================================================

# Test error responses
echo "=== Error Handling Tests ==="

# 404 - Not found
curl -X GET "http://localhost:8000/manga/999999"

# 400 - Bad request (invalid rating)
curl -X POST "http://localhost:8000/manga" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Invalid Manga",
    "rating": 15.0
  }'

# 400 - Empty search query
curl -X GET "http://localhost:8000/manga/search/suggestions?query="

# 400 - Invalid fuzzy distance
curl -X POST "http://localhost:8000/manga/search/fuzzy" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "fuzzy_distance": 10
  }'

# ============================================================================
# 18. BATCH OPERATIONS FOR TESTING
# ============================================================================

# Create multiple authors in batch
echo "=== Batch Operations ==="
for i in {1..5}; do
  curl -s -X POST "http://localhost:8000/authors" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Batch Author $i\"}" > /dev/null
  echo "Created Author $i"
done

# Create multiple genres in batch
for genre in "Action" "Romance" "Comedy" "Drama" "Sci-Fi"; do
  curl -s -X POST "http://localhost:8000/genres" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$genre\"}" > /dev/null
  echo "Created Genre: $genre"
done

echo "=== All Sample Queries Complete ==="

# ============================================================================
# 19. API DOCUMENTATION QUERIES
# ============================================================================

# Access Swagger UI
echo "Swagger UI: http://localhost:8000/docs"

# Access ReDoc
echo "ReDoc: http://localhost:8000/redoc"

# Get OpenAPI schema
curl -X GET "http://localhost:8000/openapi.json" | python3 -m json.tool > openapi_schema.json
