from flask_login import login_required, login_user, logout_user, current_user
from flask import Blueprint, render_template, request, flash, redirect, url_for,session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Attendance,Shift_time,Backup, late, leave,notifications,NewShift,Emp_login,call_duty
from . import db
import datetime
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError
import time
from datetime import datetime, timedelta
from .funcations import *



auth = Blueprint('auth', __name__)

@auth.route('/admin-login', methods=['POST', 'GET'])       # this is the overall login ....
def login():
    admin = Emp_login.query.filter_by(email='vsabarinathan1611@gmail.com').first()
    if admin:
        if request.method == 'POST':
            
            email = request.form.get('email')
            password = request.form.get('password')
            # session.clear()

            dbemail = Emp_login.query.filter_by(email=email).first()
            print(dbemail)
            if dbemail :
                if check_password_hash(dbemail.password, password):

                    login_user(dbemail, remember=True)

                    if dbemail.role == "admin":
                        session['admin_name']=dbemail.name
                        print("admin session created")
                        session['flash_message']=['Logged In Successfully','success']

                        return redirect(url_for('views.admin'))

                    elif dbemail.role == "employee":
                        session['emp_id'] = dbemail.emp_id
                        session['name'] = dbemail.name
                        session['email'] = email
                        session['phNumber']=dbemail.phoneNumber
                        session['leave_balance']=dbemail.leave_balance
                        session['late_balance']=dbemail.late_balance
                        session['flash_message']=['Logged In Successfully','success']
                        return redirect(url_for('views.user_dashboard'))
                        #return redirect(url_for('views.emp_login'))
                    
                else:
                    session['flash_message']=['Incorrect Password','error']
                    flash("Incorrect Password", category='error')
            else:
                session['flash_message']=['Incorrect Email','error']
                flash("Incorrect Email", category='error')
    else:
        # Assuming you're using Flask's generate_password_hash to hash passwords during registration
        addAdmin = Emp_login(
            name="Admin",
            email="vsabarinathan1611@gmail.com",
            phoneNumber="123456789",
            password=generate_password_hash("admin"),
            role="admin",
            designation='HR',
            emp_id='9999'
        )
        db.session.add(addAdmin)
        db.session.commit()
        print('Created Admin!')

    return render_template('login.html')

@auth.route('/login', methods=['POST', 'GET'])
def admin_login():
    
    print("session cleared")
    return render_template("login.html")

@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup',methods=['POST','GET'])
@login_required
def signup():
    if request.method == 'POST':
        # Get user input from the form
        emp_id = request.form['emp_id'] 
        name = request.form['name']
        designation = request.form['designation']
        email = request.form['email']
        ph_number = request.form['ph_number']
        aadhar = request.form['aadhar'] 
        gender = request.form['gender'] 
        address = request.form['address'] 
        branch = request.form['branch'] 
        role = request.form['role']
        # Check if a user with the same email already exists
        existing_user = Emp_login.query.filter_by(email=email).first()
        existing_id = Emp_login.query.filter_by(emp_id=emp_id).first()
        existing_aadhar = Emp_login.query.filter_by(aadhar=aadhar).first()
        if existing_user:
            session['flash_message']=['Email already exists.','error']

        elif existing_id:
            session['flash_message']=['Emp id already exists.','error']

        elif existing_aadhar:
            session['flash_message']=['Aadhar Number already exists.','error']

        else:
            # Create a new Emp_login object and add it to the database
            # new_login = Emp_login(email=email, password=generate_password_hash(ph_number), role=role,phoneNumber=ph_number, emp_id=emp_id, name=name)
            new_login = Emp_login(
                email = email,
                name = name,
                aadhar = aadhar,
                password = generate_password_hash(ph_number),
                emp_id = emp_id,
                branch=branch,
                phoneNumber=ph_number,
                role =role,
                designation=designation,
                address = address,
                gender = gender
            )
            db.session.add(new_login)
            db.session.commit()
            session['flash_message']=['Emp id Added successfully','success']

            # Redirect to a success page or perform any other necessary actions
            return redirect('/')

    # Render the signup form for GET requests
    return redirect('/')

