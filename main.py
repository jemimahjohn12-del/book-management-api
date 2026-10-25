from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
app = FastAPI(
    title="Book Management API",
    description="A simple back-end REST API built with FastAPI to manage a collection of books.",
    version="1.0.0"
)
# In-memory database
books_db: Dict[int, dict] = {}
id_counter = 1
# Pydantic Model for Book Creation/Full Update
class BookModel(BaseModel):
    title: str = Field(..., min_length=1, 
max_length=100, examples=["The Hobbit"])
    author: str = Field(..., min_length=1, max_length=50, examples=["J.R.R. Tolkien"])
    publication_year: int = Field(..., gt=0, le=2026, examples=[1937])
    genre: str = Field(..., min_length=1, max_length=30, examples=["Fantasy"])
# Pydantic Model for Partial Updates (PATCH) - Optional Challenge
class BookUpdateModel(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    author: Optional[str] = Field(None, min_length=1, max_length=50)
    publication_year: Optional[int] = Field(None, gt=0, le=2026)
    genre: Optional[str] = Field(None, min_length=1, max_length=30)
# Helper function to format response data
def format_book(book_id: int, book_data: dict) -> dict:
    return {"id": book_id, **book_data}
# 1. POST: Create a new book
@app.post("/books", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_book(book: BookModel):
    global id_counter
    new_book = book.model_dump()
    books_db[id_counter] = new_book
    response = format_book(id_counter, new_book)
    id_counter += 1
    return response
# 2. GET: Retrieve all books (with filtering, 
# 2. GET: Retrieve all books (with filtering, searching, and pagination limits)
@app.get("/books", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_books(
    genre: Optional[str] = Query(None, description="Filter books by genre"),
    search: Optional[str] = Query(None, description="Search books by title or author keyword"),
    limit: Optional[int] = Query(None, ge=1, description="Limit the number of results returned")
):
    results = []
    for book_id, book_data in books_db.items():
        # Filter by genre
        if genre and book_data.get("genre", "").lower() != genre.lower():
            continue
        # Search by title or author (Optional Challenge)
        if search:
            search_lower = search.lower()
            if (
                search_lower not in book_data["title"].lower()
                and search_lower not in book_data["author"].lower()
            ):
                continue
        results.append(format_book(book_id, book_data))
    # Apply results limit (Optional Challenge)
    if limit:
        results = results[:limit]
    return results
# 3. GET: Retrieve a single book by ID
@app.get("/books/{book_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_book_by_id(book_id: int = Path(..., description="The ID of the book to retrieve", ge=1)):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with ID {book_id} not found"
        )
    return format_book(book_id, books_db[book_id])
# 4. PUT: Update a full book record
@app.put("/books/{book_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_book(book_id: int, updated_book: BookModel):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with ID {book_id} not found"
        )
    books_db[book_id] = updated_book.model_dump()
    return format_book(book_id, books_db[book_id])
# 5. PATCH: Partial update (Optional Challenge)
@app.patch("/books/{book_id}", response_model=dict, status_code=status.HTTP_200_OK)
def patch_book(book_id: int, patch_data: BookUpdateModel):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with ID {book_id} not found"
        )
    stored_book_data = books_db[book_id]
    update_data = patch_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        stored_book_data[key] = value
    books_db[book_id] = stored_book_data
    return format_book(book_id, books_db[book_id])
# 6. DELETE: Remove a book record
@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with ID {book_id} not found"
        )
    del books_db[book_id]
    return {"message": f"Book with ID {book_id} has been successfully deleted."}