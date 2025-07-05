# oneSix Freelance Platform API

A Django-based REST API for the oneSix freelancing platform, allowing users to create profiles, manage portfolios, search for freelancers, and communicate via messaging.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Future Plans](#future-plans)
- [Contributing](#contributing)
- [License](#license)

## Overview
oneSix is a backend API for a freelancing platform where users can register, create and manage their profiles and portfolios, search for freelancers based on skills, location, or ratings, and communicate through a messaging system. The API is built using Django and Django REST Framework, with API documentation via Swagger and ReDoc.

## Features
- **User Management**: Register, log in, and update user profiles (email, bio, skills, etc.).
- **Public Profiles**: View user profiles and portfolios publicly without authentication (sensitive fields like email and phone number are excluded).
- **Freelancer Search**: Search freelancers by keywords, skills, location, or minimum rating, with sorting by rating, orders, or join date.
- **Portfolio Management**: Authenticated users can create and update their portfolio items.
- **Messaging**: Send and receive messages with file attachments (max 1GB).
- **Job Management**: Create and manage job listings with images (max 2MB) and reviews.
- **Order Management**: Handle orders, deliveries (max 1GB), and assign freelancers.
- **API Documentation**: Interactive Swagger UI for testing endpoints.

## Tech Stack
- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL (recommended)
- **API Documentation**: DRF-YASG (Swagger)
- **Frontend**: React (planned)
- **Environment**: Python 3.8+

## Installation
1. **Clone the Repository**:
   ```
   git clone https://github.com/yourusername/oneSix-Freelance-Platform-API.git
   cd oneSix-Freelance-Platform-API
   ```

2. **Create a Virtual Environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the project root and add:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:password@localhost:5432/onesix_db
   ```

5. **Run Migrations**:
   ```
   python manage.py migrate
   ```

6. **Create a Superuser** (optional):
   ```
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:
   ```
   python manage.py runserver
   ```

8. **Access Swagger UI**:
   Open `http://127.0.0.1:8000/swagger/` in your browser to view API documentation.

8. **Access ReDoc UI**:
   Open `http://127.0.0.1:8000/redoc/` in your browser to view API documentation.

## API Endpoints
| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/categories/` | GET, POST | List or create job categories | None (GET), JWT (POST) |
| `/api/v1/jobs/` | GET, POST | List or create job listings | None (GET), JWT (POST) |
| `/api/v1/jobs/<job:pk>/` | GET | View a job detail | None |
| `/api/v1/jobs/<job:pk>/reviews/` | GET, POST | List or create reviews for a job | None (GET), JWT (POST) |
| `/api/v1/jobs/<job:pk>/images/` | GET, POST | List or create images for a job | None (GET), JWT (POST) |
| `/api/v1/job-price/` | GET, POST | List or create job prices | None (GET), JWT (POST) |
| `/api/v1/carts/` | GET, POST | List or create carts | JWT |
| `/api/v1/carts/<cart:pk>/items/` | GET, POST | List or create cart items | JWT |
| `/api/v1/orders/` | GET, POST | List or create orders | JWT |
| `/api/v1/orders/<order:pk>/` | GET | View order details | JWT |
| `/api/v1/deliveries/` | POST | Submit a delivery for an order | JWT |
| `/api/v1/profiles/` | GET, POST | List or create user profiles | None (GET), JWT (POST) |
| `/api/v1/profiles/<profile:pk>/` | GET | View a user's public profile | None |
| `/api/v1/profiles/search/` | GET | Search freelancers | None |
| `/api/v1/portfolio/` | POST | Create a portfolio item | JWT |
| `/api/v1/portfolio/my/` | GET | List authenticated user's portfolio items | JWT |
| `/api/v1/portfolio/<int:pk>/` | GET | View a portfolio item publicly | None |
| `/api/v1/message/` | GET, POST | List or create messages | JWT |
| `/api/v1/custom-offers/` | GET, POST | List or create custom offers | JWT |

*Note*: Authentication endpoints (e.g., `/api/v1/auth/`) are handled by Djoser and excluded from this list. Visit `http://127.0.0.1:8000/swagger/` or `http://127.0.0.1:8000/redoc/` for full details.

## Testing
1. **Register a User**:
   - Use `/api/v1/auth/users/` to create a user (via Djoser).
   - Example: `curl -X POST "http://127.0.0.1:8000/api/v1/auth/users/" -d '{"email": "user@example.com", "password": "password123"}'`

2. **View Public Profile**:
   - Access `/api/v1/profiles/<profile:pk>/` without authentication.
   - Example: `curl -X GET "http://127.0.0.1:8000/api/v1/profiles/1/"`

3. **Search Freelancers**:
   - Use `/api/v1/profiles/search/` with query parameters.
   - Example: `curl -X GET "http://127.0.0.1:8000/api/v1/profiles/search/?keyword=developer&skills=Python"`

4. **Create a Job**:
   - Use `/api/v1/jobs/` with JWT token.
   - Example: `curl -X POST "http://127.0.0.1:8000/api/v1/jobs/" -H "Authorization: JWT <token>" -d '{"name": "Web Design", "description": "Design a website"}'`

5. **Send a Message**:
   - Use `/api/v1/message/` with JWT token and optional file attachment.
   - Example: `curl -X POST "http://127.0.0.1:8000/api/v1/message/" -H "Authorization: JWT <token>" -F "receiver=2" -F "content=Hello"`

## Future Plans
- Integrate Stripe for payment processing.
- Add WebSocket support for real-time messaging.
- Implement notifications for messages, orders, and deliveries.
- Support username-based URLs and login with username or email.
- Add dispute resolution and revision tracking for orders.
- Enable real-time chat with typing indicators and read receipts.
- Integrate a rating and review system with detailed analytics.

## Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please ensure code follows PEP 8 and includes tests.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
___
# Author
[MD Mahmudul Hasan] (https://github.com/mmahmudul7)
