from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from database import SessionLocal, engine, get_db
import os
from pathlib import Path
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path


# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Luxury Contact Form API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the frontend directory
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "../frontend"

print(f"Frontend directory: {FRONTEND_DIR}")
print(f"Frontend exists: {FRONTEND_DIR.exists()}")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=FileResponse)
async def serve_form():
    """Serve the main contact form"""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Form not found")
    return FileResponse(index_path)

@app.get("/form", response_class=FileResponse)
async def serve_form_alt():
    """Alternative endpoint for the form"""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Form not found")
    return FileResponse(index_path)

@app.post("/api/contact", response_model=schemas.ContactInquiryResponse)
async def create_contact_inquiry(
    inquiry: schemas.ContactInquiryCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new contact inquiry
    """
    try:
        db_inquiry = models.ContactInquiry(**inquiry.dict())
        db.add(db_inquiry)
        db.commit()
        db.refresh(db_inquiry)
        return db_inquiry
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating inquiry: {str(e)}"
        )

@app.get("/api/contacts", response_model=List[schemas.ContactInquiryResponse])
async def get_all_contacts(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Number of records to return"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc")
):
    """
    Get all contact inquiries with pagination and sorting
    """
    try:
        # Validate sort field
        valid_sort_fields = ["id", "full_name", "email", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Validate sort order
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"
        
        # Create order_by clause
        order_column = getattr(models.ContactInquiry, sort_by)
        if sort_order == "desc":
            order_column = desc(order_column)
        
        contacts = db.query(models.ContactInquiry)\
                    .order_by(order_column)\
                    .offset(skip)\
                    .limit(limit)\
                    .all()
        
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching contacts: {str(e)}"
        )

@app.get("/api/contacts/{contact_id}", response_model=schemas.ContactInquiryResponse)
async def get_contact_by_id(contact_id: int, db: Session = Depends(get_db)):
    """
    Get a specific contact inquiry by ID
    """
    contact = db.query(models.ContactInquiry).filter(models.ContactInquiry.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.get("/api/contacts/email/{email}", response_model=List[schemas.ContactInquiryResponse])
async def get_contacts_by_email(email: str, db: Session = Depends(get_db)):
    """
    Get all contact inquiries by email address
    """
    contacts = db.query(models.ContactInquiry)\
                .filter(models.ContactInquiry.email == email)\
                .order_by(desc(models.ContactInquiry.created_at))\
                .all()
    return contacts

@app.get("/api/contacts/search/{search_term}", response_model=List[schemas.ContactInquiryResponse])
async def search_contacts(
    search_term: str, 
    db: Session = Depends(get_db),
    field: str = Query("all", description="Search field: all, name, email, message")
):
    """
    Search contacts by various fields
    """
    try:
        query = db.query(models.ContactInquiry)
        
        if field == "name" or field == "all":
            query = query.filter(models.ContactInquiry.full_name.ilike(f"%{search_term}%"))
        elif field == "email" or field == "all":
            query = query.filter(models.ContactInquiry.email.ilike(f"%{search_term}%"))
        elif field == "message" or field == "all":
            query = query.filter(models.ContactInquiry.message.ilike(f"%{search_term}%"))
        
        contacts = query.order_by(desc(models.ContactInquiry.created_at)).all()
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching contacts: {str(e)}"
        )

@app.get("/api/stats")
async def get_contact_stats(
    db: Session = Depends(get_db),
    period: str = Query("all", description="Time period: today, week, month, all")
):
    """
    Get statistics about contact inquiries
    """
    try:
        # Base query
        query = db.query(models.ContactInquiry)
        
        # Apply time filter
        now = datetime.utcnow()
        if period == "today":
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(models.ContactInquiry.created_at >= today_start)
        elif period == "week":
            week_ago = now - timedelta(days=7)
            query = query.filter(models.ContactInquiry.created_at >= week_ago)
        elif period == "month":
            month_ago = now - timedelta(days=30)
            query = query.filter(models.ContactInquiry.created_at >= month_ago)
        
        total_contacts = query.count()
        
        # Count by contact method
        contact_methods = query.with_entities(
            models.ContactInquiry.preferred_contact_method,
            func.count(models.ContactInquiry.id)
        ).group_by(models.ContactInquiry.preferred_contact_method).all()
        
        # Recent contacts (last 5)
        recent_contacts = db.query(models.ContactInquiry)\
                          .order_by(desc(models.ContactInquiry.created_at))\
                          .limit(5)\
                          .all()
        
        return {
            "period": period,
            "total_contacts": total_contacts,
            "contact_methods": dict(contact_methods),
            "recent_contacts_count": len(recent_contacts),
            "recent_contacts": [
                {
                    "id": contact.id,
                    "name": contact.full_name,
                    "email": contact.email,
                    "created_at": contact.created_at.isoformat()
                }
                for contact in recent_contacts
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stats: {str(e)}"
        )

@app.get("/api/contacts/recent")
async def get_recent_contacts(
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of recent contacts to return")
):
    """
    Get recent contact inquiries
    """
    contacts = db.query(models.ContactInquiry)\
                .order_by(desc(models.ContactInquiry.created_at))\
                .limit(limit)\
                .all()
    
    return {
        "count": len(contacts),
        "contacts": contacts
    }

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Delete a contact inquiry (Admin function)
    """
    contact = db.query(models.ContactInquiry).filter(models.ContactInquiry.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        db.delete(contact)
        db.commit()
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting contact: {str(e)}"
        )

@app.get("/api/export/contacts")
async def export_contacts(
    db: Session = Depends(get_db),
    format: str = Query("json", description="Export format: json, csv")
):
    """
    Export all contacts in JSON or CSV format
    """
    contacts = db.query(models.ContactInquiry).order_by(desc(models.ContactInquiry.created_at)).all()
    
    if format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["ID", "Full Name", "Email", "Phone", "Contact Method", "Message", "Created At"])
        
        # Write data
        for contact in contacts:
            writer.writerow([
                contact.id,
                contact.full_name,
                contact.email,
                contact.phone_number,
                contact.preferred_contact_method,
                contact.message or "",
                contact.created_at.isoformat()
            ])
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"contacts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    else:
        return {
            "format": "json",
            "count": len(contacts),
            "contacts": contacts
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Luxury Contact Form API is running"}

# Serve CSS and JS files directly
@app.get("/style.css", response_class=FileResponse)
async def serve_css():
    css_path = FRONTEND_DIR / "style.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS not found")
    return FileResponse(css_path)

@app.get("/script.js", response_class=FileResponse)
async def serve_js():
    js_path = FRONTEND_DIR / "script.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JS not found")
    return FileResponse(js_path)

@app.get("/admin.html", response_class=FileResponse)
async def serve_admin():
    """Serve the admin panel"""
    admin_path = FRONTEND_DIR / "admin.html"
    if not admin_path.exists():
        # If admin.html doesn't exist, create a simple admin interface
        return HTMLResponse(content=create_simple_admin())
    return FileResponse(admin_path)

def create_simple_admin():
    """Create a simple admin interface if admin.html doesn't exist"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Panel | Contact Inquiries</title>
        <style>
            :root { --primary: #2563eb; --success: #10b981; --danger: #ef4444; --dark: #1f2937; --light: #f3f4f6; }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: var(--light); color: var(--dark); padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; }
            .stat-number { font-size: 2em; font-weight: bold; color: var(--primary); }
            .controls { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn-primary { background: var(--primary); color: white; }
            .btn-danger { background: var(--danger); color: white; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
            th { background: #f9fafb; }
            .loading { text-align: center; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Contact Inquiries Admin Panel</h1>
                <p>Manage and view all contact submissions</p>
            </div>
            
            <div class="stats" id="statsGrid">
                <div class="loading">Loading statistics...</div>
            </div>
            
            <div class="controls">
                <button class="btn btn-primary" onclick="loadContacts()">🔄 Refresh Contacts</button>
                <button class="btn btn-primary" onclick="loadStats()">📈 Refresh Stats</button>
                <button class="btn btn-primary" onclick="exportContacts()">📥 Export CSV</button>
                <input type="text" id="searchInput" placeholder="🔍 Search contacts..." style="padding: 10px; width: 300px;">
                <button class="btn btn-primary" onclick="searchContacts()">Search</button>
            </div>
            
            <div id="contactsList">
                <div class="loading">Loading contacts...</div>
            </div>
        </div>

        <script>
            const API_BASE = '/api';
            
            async function loadStats() {
                try {
                    const response = await fetch(`${API_BASE}/stats`);
                    const stats = await response.json();
                    
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_contacts}</div>
                            <div>Total Contacts</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.recent_contacts_count}</div>
                            <div>Recent Contacts</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.contact_methods.Email || 0}</div>
                            <div>Email Preferences</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.contact_methods.Phone || 0}</div>
                            <div>Phone Preferences</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading stats:', error);
                    document.getElementById('statsGrid').innerHTML = '<div class="stat-card">Error loading stats</div>';
                }
            }
            
            async function loadContacts() {
                try {
                    const response = await fetch(`${API_BASE}/contacts?limit=100`);
                    const contacts = await response.json();
                    
                    if (contacts.length === 0) {
                        document.getElementById('contactsList').innerHTML = '<div class="stat-card">No contacts found</div>';
                        return;
                    }
                    
                    const contactsHTML = `
                        <div style="background: white; border-radius: 10px; overflow: hidden;">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>Phone</th>
                                        <th>Contact Method</th>
                                        <th>Message</th>
                                        <th>Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${contacts.map(contact => `
                                        <tr>
                                            <td>${contact.id}</td>
                                            <td><strong>${contact.full_name}</strong></td>
                                            <td>${contact.email}</td>
                                            <td>${contact.phone_number}</td>
                                            <td><span style="padding: 4px 8px; background: #e5e7eb; border-radius: 4px;">${contact.preferred_contact_method}</span></td>
                                            <td>${contact.message ? contact.message.substring(0, 30) + '...' : 'N/A'}</td>
                                            <td>${new Date(contact.created_at).toLocaleString()}</td>
                                            <td>
                                                <button class="btn btn-danger" onclick="deleteContact(${contact.id})">Delete</button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    document.getElementById('contactsList').innerHTML = contactsHTML;
                } catch (error) {
                    console.error('Error loading contacts:', error);
                    document.getElementById('contactsList').innerHTML = '<div class="stat-card">Error loading contacts</div>';
                }
            }
            
            async function searchContacts() {
                const searchTerm = document.getElementById('searchInput').value;
                if (!searchTerm) {
                    loadContacts();
                    return;
                }
                
                try {
                    const response = await fetch(`${API_BASE}/contacts/search/${searchTerm}?field=all`);
                    const contacts = await response.json();
                    
                    if (contacts.length === 0) {
                        document.getElementById('contactsList').innerHTML = '<div class="stat-card">No contacts found for "' + searchTerm + '"</div>';
                        return;
                    }
                    
                    // Reuse the same table format as loadContacts()
                    const contactsHTML = `
                        <div style="background: white; border-radius: 10px; overflow: hidden;">
                            <div style="padding: 15px; background: #f0f9ff; border-bottom: 1px solid #e5e7eb;">
                                <strong>Search Results for "${searchTerm}" (${contacts.length} found)</strong>
                                <button class="btn btn-primary" onclick="loadContacts()" style="float: right; padding: 5px 10px;">Show All</button>
                            </div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>Phone</th>
                                        <th>Contact Method</th>
                                        <th>Message</th>
                                        <th>Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${contacts.map(contact => `
                                        <tr>
                                            <td>${contact.id}</td>
                                            <td><strong>${contact.full_name}</strong></td>
                                            <td>${contact.email}</td>
                                            <td>${contact.phone_number}</td>
                                            <td><span style="padding: 4px 8px; background: #e5e7eb; border-radius: 4px;">${contact.preferred_contact_method}</span></td>
                                            <td>${contact.message ? contact.message.substring(0, 30) + '...' : 'N/A'}</td>
                                            <td>${new Date(contact.created_at).toLocaleString()}</td>
                                            <td>
                                                <button class="btn btn-danger" onclick="deleteContact(${contact.id})">Delete</button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    document.getElementById('contactsList').innerHTML = contactsHTML;
                } catch (error) {
                    console.error('Error searching contacts:', error);
                }
            }
            
            async function deleteContact(contactId) {
                if (!confirm('Are you sure you want to delete this contact?')) return;
                
                try {
                    const response = await fetch(`${API_BASE}/contacts/${contactId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        alert('Contact deleted successfully');
                        loadContacts();
                        loadStats();
                    } else {
                        alert('Error deleting contact');
                    }
                } catch (error) {
                    console.error('Error deleting contact:', error);
                    alert('Error deleting contact');
                }
            }
            
            async function exportContacts() {
                try {
                    const response = await fetch(`${API_BASE}/export/contacts?format=csv`);
                    const data = await response.json();
                    
                    // Create download link
                    const blob = new Blob([data.data], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = data.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } catch (error) {
                    console.error('Error exporting contacts:', error);
                    alert('Error exporting contacts');
                }
            }
            
            // Load data on page load
            document.addEventListener('DOMContentLoaded', () => {
                loadStats();
                loadContacts();
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)