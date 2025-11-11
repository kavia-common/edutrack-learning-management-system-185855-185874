# edutrack-learning-management-system-185855-185874

Backend (Flask) quick start:
- Create a virtualenv and install requirements: pip install -r lms_backend/requirements.txt
- Copy lms_backend/.env.example to .env and fill variables (DATABASE_URL, JWT_SECRET_KEY, STRIPE_SECRET_KEY, etc.)
- Run the server: python lms_backend/run.py
- API docs available at /docs (e.g., http://localhost:3001/docs)
- WebSocket namespace: /notifications (see /api/ws/docs)
- Notifications REST endpoints are available at /api/notifications for listing and creating notifications for the current user.