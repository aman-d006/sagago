# Sagago - Story Writing Platform

A full-stack story writing and sharing platform with AI-assisted story generation.

## 🚀 Features
- User authentication and profiles
- Create, read, update, and delete stories
- AI-assisted story generation
- Comments, likes, and bookmarks
- Follow other users
- Real-time notifications
- Reading list
- Analytics dashboard

## 🛠️ Tech Stack

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- Zustand for state management
- Vite as build tool

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- SQLite (development) / PostgreSQL (production)
- JWT authentication
- Groq AI integration

## 📁 Project Structure
sagago/
├── backend/ # FastAPI backend
│ ├── core/ # Core functionality
│ ├── models/ # Database models
│ ├── routers/ # API routes
│ ├── schemas/ # Pydantic schemas
│ └── scripts/ # Utility scripts
├── frontend/ # React frontend
│ ├── src/
│ │ ├── api/ # API client
│ │ ├── components/# React components
│ │ ├── pages/ # Page components
│ │ ├── stores/ # Zustand stores
│ │ └── types/ # TypeScript types
│ └── public/ # Static files
└── README.md
