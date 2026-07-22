# LOSTFOUND - AI-Powered Missing Person & Pet Locator

## 🚀 Overview

LOSTFOUND is a production-ready Django web application that leverages AI (CLIP + FAISS) to help locate missing family members and pets through visual similarity search.

## ✨ Features

- **AI Visual Search**: Upload a photo and find visually similar cases using OpenAI CLIP and FAISS
- **Case Management**: Create and manage Lost/Found cases with multiple images
- **Interactive Map**: Leaflet.js map showing case locations with customizable pins
- **Detective System**: Verified detectives can be assigned to cases and post investigation updates
- **Role-Based Access**: User, Detective, and Admin roles with appropriate permissions
- **Dark/Light Mode**: Modern glassmorphism UI with theme toggle
- **No External CSS Frameworks**: Pure custom CSS with modern features

## 🛠️ Tech Stack

- **Backend**: Django 4.2+, Python 3.11+
- **Database**: SQLite (development), PostgreSQL (production)
- **AI/ML**: PyTorch, Transformers (CLIP), FAISS, OpenCV, Pillow
- **Frontend**: HTML5, Custom CSS3, Vanilla JavaScript
- **Maps**: Leaflet.js + OpenStreetMap

## 📦 Installation

### 1. Clone and Setup Environment

```bash
cd /workspace
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## 📁 Project Structure

```
/workspace/
├── lostfound/                    # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions (no forms.py)
│   ├── urls.py                   # URL routing
│   ├── ai_engine.py              # CLIP + FAISS implementation
│   ├── static/css/main.css       # Custom CSS (black & white only)
│   └── templates/lostfound/      # HTML templates
├── lostfound_project/            # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── media/                        # User uploads
├── requirements.txt
└── manage.py
```

## 🎨 Design System

The UI uses a **strict black and white color palette** with:
- Glassmorphism effects
- Smooth animations
- CSS Grid and Flexbox layouts
- Dark/Light mode toggle
- Custom components (cards, buttons, badges, modals, toasts)

## 🔑 Key Models

- `Profile`: Extended user profile with role (USER/DETECTIVE/ADMIN)
- `Case`: Lost/Found cases with location data
- `CaseImage`: Images with CLIP embeddings
- `DetectiveApplication`: Detective verification requests
- `CaseAssignment`: Detective-to-case assignments
- `InvestigationUpdate`: Timeline updates for cases
- `Blog`: Platform articles
- `Notification`: User notifications

## 🤖 AI Pipeline

```
Upload Image → Generate CLIP Embedding → Store in FAISS Index
                                              ↓
User Search Image → Generate Embedding → FAISS Similarity Search → Return Matches with % Score
```

## 📝 Usage Examples

### Creating a Case (via HTML Form)

```html
<form method="POST" enctype="multipart/form-data" action="{% url 'create_case' %}">
    {% csrf_token %}
    <input type="text" name="title" required>
    <select name="case_type">
        <option value="LOST">Lost</option>
        <option value="FOUND">Found</option>
    </select>
    <input type="file" name="images" multiple accept="image/*">
    <input type="hidden" name="latitude" id="latitude">
    <input type="hidden" name="longitude" id="longitude">
    <button type="submit">Create Case</button>
</form>
```

### AI Visual Search

1. Navigate to `/ai-search/`
2. Upload a query image
3. View top 10 matches with similarity percentages

## 🔐 Authentication

- Registration: `/register/`
- Login: `/login/`
- Logout: `/logout/`
- Dashboard: `/dashboard/`

## 👥 User Roles

- **USER**: Can create cases, report sightings, request detectives
- **DETECTIVE**: Verified users who can be assigned cases and post updates
- **ADMIN**: Manages detective approvals, case assignments, blog posts

## 🗺️ Interactive Map

Visit `/map/` to see all cases pinned on an interactive Leaflet map:
- Red pins: Lost cases
- Green pins: Found cases

## 📊 API Endpoints

- `GET /api/cases/` - List cases (JSON)
- Filter by `?type=LOST` or `?type=FOUND`

## 🚨 Important Notes

1. **No Django Forms**: All form handling is done via raw HTML forms and `request.POST`/`request.FILES` in views
2. **No Bootstrap**: Pure custom CSS with modern techniques
3. **No DRF**: Standard Django views with JSON responses where needed
4. **AI Model**: CLIP model downloads on first use (~500MB)

## 🛡️ Security Considerations

- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Use PostgreSQL in production
- Configure proper `ALLOWED_HOSTS`
- Enable HTTPS
- Implement rate limiting for AI searches

## 📄 License

Built for educational and humanitarian purposes.

---

**LOSTFOUND** - Reuniting families through AI technology. ❤️
