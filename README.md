# Reimbursement Management System

A role-based expense reimbursement system designed to streamline the submission, review, and approval of employee expense claims. The system implements a structured approval workflow, enabling managers and administrators to efficiently process requests while maintaining proper control and transparency.

---

## Overview

This application allows employees to submit expense claims along with supporting receipts, while managers and administrators review and take appropriate action. It demonstrates a practical implementation of role-based access control, multi-step approvals, and full-stack integration between a Django REST backend and a Vue frontend.

---

## Features

### Authentication
- JWT-based authentication using access and refresh tokens  
- Secure login and logout functionality  

### Expense Management
- Submit expenses with amount, category, description, and date  
- Upload receipts for each expense  
- OCR-based extraction to auto-fill expense details  
- Optional currency conversion before submission  

### Expense Tracking
- View all submitted expenses  
- Track expense status (pending, approved, rejected)  
- Clear and structured expense history  

### Approval Workflow
- Multi-level approval system  
  - Step 1: Manager approval  
  - Step 2: Admin approval for high-value expenses  
- Only the assigned approver can take action  
- Supports approve and reject actions with validation  

### Dashboard
- Displays total expenses and aggregated amount  
- Shows pending approvals for managers  
- Provides quick navigation to core features  

### Role-Based Access Control
- Employee:
  - Submit and view own expenses  
- Manager/Admin:
  - View pending approvals  
  - Approve or reject requests  

---

## Technology Stack

### Backend
- Django  
- Django REST Framework  
- SimpleJWT for authentication  

### Frontend
- Vue 3 (Composition API with script setup)  
- Axios for API communication  
- Vue Router for navigation and route protection  

---

## Project Structure
reimbursement-management-system/
├── backend/
├── frontend/



---

## Setup Instructions

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver

cd frontend
npm install
npm run dev

Environment Configuration

Create a .env file inside the frontend directory:
VITE_API_BASE_URL=http://127.0.0.1:8000/api/

```

API Endpoints (Overview)
Authentication
POST /api/token/
POST /api/token/refresh/
Expenses
POST /api/expenses/
GET /api/expenses/my/
Approvals
GET /api/approvals/pending/
PATCH /api/approvals/{id}/action/
Receipts
POST /api/receipts/scan/
POST /api/receipts/convert/

Key Concepts
Role-based access control (RBAC)
Multi-step approval workflow
Token-based authentication with refresh handling
Transaction-safe operations in backend
Separation of concerns between frontend and backend
Centralized API handling in frontend

Future Enhancements
Email notifications for approval updates
Advanced analytics and reporting
Improved mobile responsiveness
Integration with cloud storage for receipts

Conclusion

This project demonstrates a complete full-stack implementation of an expense management system with real-world features such as authentication, role-based workflows, and structured approvals. It reflects a practical approach to designing scalable and maintainable web applications.
