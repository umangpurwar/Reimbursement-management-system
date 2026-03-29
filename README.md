# Reimbursement Management System

A role-based expense reimbursement system designed to streamline the submission, review, and approval of employee expense claims. The system implements a structured approval workflow, enabling managers and administrators to efficiently process requests while maintaining proper control and transparency.

---

## Overview

This application allows employees to submit expense claims along with supporting receipts, while managers and administrators review and take appropriate action. This project was developed as part of the Odoo Hackathon 2026, with a focus on designing a practical and scalable solution for expense management and structured approval workflows.

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
Key Concepts
1. Role-based access control (RBAC)
2. Multi-step approval workflow
3. Token-based authentication with refresh handling
4. Transaction-safe operations in backend
5. Separation of concerns between frontend and backend
6. Centralized API handling in frontend

Future Enhancements
1.Email notifications for approval updates
2. Advanced analytics and reporting
3. Improved mobile responsiveness
4. Integration with cloud storage for receipts

Conclusion

This project demonstrates a complete full-stack implementation of an expense management system with real-world features such as authentication, role-based workflows, and structured approvals. It reflects a practical approach to designing scalable and maintainable web applications.

# Screenshots

# home view

<img width="1920" height="1200" alt="Screenshot (123)" src="https://github.com/user-attachments/assets/68f1f3c8-a8d6-46f3-8d1b-8fb73df0a095" />

#login view

<img width="1920" height="1200" alt="Screenshot (124)" src="https://github.com/user-attachments/assets/9d0a2526-f77f-4845-abdf-8087d0b56757" />

# employee page

<img width="1920" height="1200" alt="Screenshot (125)" src="https://github.com/user-attachments/assets/b7957c9d-aed7-4245-a872-8166bdd918c9" />

# employee expense page

<img width="1920" height="1200" alt="Screenshot (126)" src="https://github.com/user-attachments/assets/1878c0e2-6ce2-4e1d-b629-387952292d32" />

# submit expense page

<img width="1920" height="1200" alt="Screenshot (130)" src="https://github.com/user-attachments/assets/f23babd2-55d6-42f8-b07b-629757ad31b9" />

# manager/director/cfo page 

<img width="1920" height="1200" alt="Screenshot (131)" src="https://github.com/user-attachments/assets/e0e05dc1-ea9f-45fe-9b35-dae4b0313672" />

# pending approvals , after approving or rejecting they will go away 

<img width="1920" height="1200" alt="Screenshot (132)" src="https://github.com/user-attachments/assets/6d70b90e-685a-45fe-a9cd-5f3b6d19acfd" />

# IT admin dashboard

<img width="1920" height="1200" alt="Screenshot (134)" src="https://github.com/user-attachments/assets/119cb524-871a-42ba-be4c-cd092e059c2a" />
