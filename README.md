A web-based ticket management system built using Django that enables teams to efficiently create, assign, update, and track support tickets with role-based access control.
This application is designed to streamline issue tracking, improve collaboration, and maintain transparency across support workflows.

Features
User Authentication & Authorization
Secure login and logout
Role-based access control (Admin, Support Agent, User)

Ticket Management
Create support tickets
Update ticket status (Open, In Progress, Resolved, Closed)
Add comments and updates to tickets

Role-Based Access
Admin
Manage users and roles
Assign tickets to agents
Support Agent
View and resolve assigned tickets

User
Create and track their own tickets

Ticket Tracking
View ticket history and current status
Filter tickets based on status and priority

Web-Based Interface
Clean and intuitive UI
Accessible from any browser

Tech Stack
Backend: Django (Python)
Frontend: HTML, CSS, Bootstrap
Database: SQLite (default) / PostgreSQL (optional)
Authentication: Django Authentication System
Version Control: Git & GitHub

Project Structure
SERVICEDESKPROJECT
│
├── servicedeskapp/             
├── servicedeskproject/          
├── static/             
├── db.sqlite3          
├── manage.py

Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/your-username/ticket-management-system.git
cd ticket-management-system

2️⃣ Create a Virtual Environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run Migrations
python manage.py migrate

5️⃣ Create Superuser
python manage.py createsuperuser

6️⃣ Start the Development Server
python manage.py runserver


Access the application at:
http://127.0.0.1:8000/

User Roles & Permissions
Role	Permissions
Admin	Manage users, assign tickets, view all tickets
Support Agent	View and resolve assigned tickets
User	Create and track personal tickets

Use Cases
IT support ticket handling
Customer support systems
Internal issue tracking for teams
Helpdesk management solutions

Author
Fathima Nourin
ECE Graduate | Django Developer Intern
