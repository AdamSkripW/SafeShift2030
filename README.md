# 3 Body Problem Project

This is a full-stack application with an Angular frontend and Flask backend.

## Project Structure

```
project-root/
│
├── frontend/         # Angular app
│   ├── src/
│   ├── angular.json
│   ├── package.json
│   └── ...
│
├── backend/          # Flask app
│   ├── app/
│   ├── requirements.txt
│   ├── run.py
│   └── ...
│
├── README.md
└── .gitignore
```

## Getting Started

### Backend Setup (Flask)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the Flask server:
   ```bash
   python run.py
   ```

The backend will be running on `http://localhost:5000`

### Frontend Setup (Angular)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be running on `http://localhost:4200`

## API Endpoints

- `GET /api/health` - Health check endpoint
- `GET /api/` - Welcome message

## Technologies Used

### Frontend
- Angular 17
- TypeScript
- RxJS

### Backend
- Flask 3.0
- Flask-CORS
- Python 3.x

## Development

- Frontend runs on port 4200
- Backend runs on port 5000
- CORS is enabled for cross-origin requests

## License

This project is licensed under the MIT License.
