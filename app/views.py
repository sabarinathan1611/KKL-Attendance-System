from flask_login import login_required, current_user,login_user
from . import db
from .models import Attendance,Shift_time,Backup, late, leave,notifications ,NewShift,Emp_login,user_edit,Week_off
from flask import Blueprint, render_template, request, flash, redirect, url_for,jsonify,session
import json
import datetime
import pandas as pd
from flask import current_app as app
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from .funcations import *
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func



import csv
from sqlalchemy import desc

views = Blueprint('views', __name__)
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
from flask_socketio import emit
from app import socketio
@views.route('/',methods=['POST','GET'])
@login_required
def admin():    
    print(current_user.role) 
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    else :

    # not used ,,,, used in auth itself
    # try:
    #     inshift = Shift_time.query.filter_by(id=1).first()
    #     if not inshift:
    #         file_path = os.path.join(app.config['EXCEL_FOLDER'], '01-08-23.xls')  # Use correct case 'EXCEL_FOLDER'
    #         process_excel_data(file_path)  # Call the data processing function
    #     else:
    #         print("Shift not found")

    # except Exception as e:
    #     print("Error occurred:", e)
    #     db.session.rollback()  # Rollback in case of error

    
        current_date = datetime.now().strftime('%Y-%m-%d')
        employee_attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date).all()
        # print("Current Date: ",current_date)
        # print("Data :",employee_attendance)

        # employee_attendance = Attendance.query.all()
        

        
        emp_login=Emp_login.query.order_by(Emp_login.emp_id).all()
        #employee =Attendance.query.order_by(Attendance.date)
        late_permission=late.query.order_by(late.date).all()
        leave_permission=leave.query.order_by(leave.date).all()
        notification=notifications.query.order_by(notifications.timestamp).all()
        print("notification : ",notification)
        # sihft=Shift_time.query.order_by(Shift_time.id) 
    return render_template('admin.html',emp_login=emp_login, notification=notification, attendance=employee_attendance, late_permission=late_permission, leave_permission=leave_permission)

@views.route('/edit', methods=['POST', 'GET'])
@login_required
def empEdit():
    if request.method == 'POST':
        empid = session.get('emp_id')
        name = request.form.get('name')
        dob = request.form.get('dob')
        workType = request.form.get('workType')
        phoneNumber = request.form.get('phoneNumber')
        adharNumber = request.form.get('adharNumber')
        wages_per_Day = request.form.get('wages_per_Day')
        gender = request.form.get('gender')
        address = request.form.get('address')
        dob_date = datetime.strptime(dob, '%Y-%m-%d').date()

        # Query the database for an employee with the given 'empid'
        emp = Emp_login.query.filter_by(id=empid).first()

        if emp:
            # Update the employee's data with the new information
            emp.name = name
            emp.dob = dob_date
            emp.workType = workType
            emp.phoneNumber = phoneNumber
            emp.adharNumber = adharNumber
            emp.wages_per_Day = wages_per_Day
            emp.gender = gender
            emp.address = address

            # Commit the changes to the database
            db.session.commit()
        else:
            flash('Employee not found!', 'error')

        # Redirect the user _to the 'admin' page or route.
    return redirect(url_for('views.admin'))
    
        
@views.route('/delete-emp',methods=['POST'])
@login_required
def delete_employee():
    try:
        data = request.get_json()
        print(data)
        
        if not data or 'EmpId' not in data:
            return jsonify({'error': 'Invalid request data. EmpId is missing.'}), 400

        emp_id = data['EmpId']
        

        # Check if an employee with the given emp_id exists in the database
        employee = Emp_login.query.filter_by(id=int(emp_id)).first()
        
        attendance=Attendance.query.filter_by(id=int(emp_id)).all()
        for record in attendance:
            db.session.delete(record)

        if employee is None:
            return jsonify({'error': 'Employee not found.'}), 404

        # If the employee is found, delete the record from the database
        db.session.delete(employee)
        
        db.session.commit()

        return jsonify({'message': 'Employee deleted successfully.'}), 200

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

    return "Employee deleted successfully!", 200

    
@views.route('/profile-view')
@login_required
def profileView():
    try: 
        
        employee =Emp_login.query.order_by(Emp_login.id)
        
        
    except Exception as error:
        flash(error)
    current_date = datetime.now().date()
    return render_template('profile.html',employee=employee,current_date=current_date)

@views.route('/calculate',methods=['POST','GET'])
def calculate():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    calculate_Attendance()
    # lol=Shift_time.query.filter_by(id=5).first()
    # lol.shiftIntime="14:00"
    # lol.shift_Outtime="22:00"
    # db.session.commit()
    # print(lol.shift_Outtime)
    attendance=Attendance.query.all()
    
    return redirect('/')  
# @views.route('/getshift',methods=['POST','GET'])
# def get_shift():
#     try:
#         inshift = Shift_time.query.filter_by(id=1).first()
#         if not inshift:
#             file_path = os.path.join(app.config['Excel_FOLDER'], '01-08-23.xls')
#             process_excel_data(file_path)  # Call the data processing function
#         else:
#             print("Shift not found")

#     except Exception as e:
#         print("Error occurred:", e)
#         db.session.rollback()  # Rollback in case of error
    
#     return redirect(url_for('views.viewShift'))  # Redirect to viewShift after processing
    
 # new_shift = Shift_time(shiftIntime="06:00",shift_Outtime="14:00",shiftType="8A",work_Duration="08:00")
    # db.session.add(new_shift)
    # db.session.commit()
    # emp=Attendance.query.get(2)
    # emp.inTime="08:16"
    # emp.outTime="18:56"
    # db.session.commit()
@views.route('/shift')
def viewShift():
    
    records=Shift_time.query.order_by(Shift_time.id)  
    return render_template('shift.html',records=records)

@views.route('/attendance')
def readXl_update_atten():
    try:
            file_path = os.path.join(app.config['EXCEL_FOLDER'], 'attendance.xlsx')  # Use correct case 'EXCEL_FOLDER'
            attend_excel_data(file_path)  # Call the data processing function
       

    except Exception as e:
        print("Error occurred:", e)
        db.session.rollback()  # Rollback in case of error    
    return redirect(url_for('views.calculate'))

@views.route('/backup', methods=['POST', 'GET'])
def backup_data():
            

    # Retrieve all records from the Attendance table
    attendance_records = Attendance.query.all()

    # Create new Backup objects and copy data from Attendance records
    backup_records = []
    for attendance_record in attendance_records:
        backup_record = Backup(
            date=attendance_record.date,
            emp_id=attendance_record.emp_id,
            attendance=attendance_record.attendance,
            wages_per_Day=attendance_record.wages_per_Day,
            inTime=attendance_record.inTime,
            outTime=attendance_record.outTime,
            overtime=attendance_record.overtime,
            shiftType=attendance_record.shiftType,
            shiftIntime=attendance_record.shiftIntime,
            shift_Outtime=attendance_record.shift_Outtime,
            TotalDuration=attendance_record.TotalDuration,
            lateBy=attendance_record.lateBy,
            earlyGoingBy=attendance_record.earlyGoingBy,
            punchRecords=attendance_record.punchRecords
        )
        backup_records.append(backup_record)

    # Add the new Backup records to the database
    db.session.bulk_save_objects(backup_records)

    # Delete the records from the Attendance table
    for attendance_record in attendance_records:
        db.session.delete(attendance_record)

    # Commit the changes to the database
    db.session.commit()
    return redirect(url_for('views.admin'))

# @views.route('/upload_csv_page',methods=['POST','GET'])
# def upload_csv_page():
#     return render_template("upload_csv.html")

# @views.route('/upload_csv',methods=['POST','GET'])
# def upload_csv():
#     if request.method == 'POST':
#         if 'csvFile' not in request.files:
#             return "No file part"
            
#         file = request.files['csvFile']
#         if file.filename == '':
#             return "No selected file"
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             print(filename)
#             file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
#             file.save(file_path)
#             process_csv_file(file_path)
#                 # # Create a new database record with file name and current datetime
#                 # now = datetime.now()
#                 # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
#                 # data = NewShift(
#                 #     name_date_day=f"File Uploaded on {current_time}",
#                 #     filename=filename  # Add the filename to the database
#                 # )
#                 # db.session.add(data)
#                 # db.session.commit()
            
#             return redirect(url_for('views.process_csv'))
#         else:
#             return "File not allowed"
#     # I the request method is GET, render the upload form
#     return render_template('upload_csv.html')


# @views.route('/process_csv', methods=['POST','GET'])
# def process_csv():
#     # Query the database to get the latest uploaded record
#     latest_data = NewShift.query.order_by(desc(NewShift.id)).first()
    
#     if not latest_data:
#         return "No files have been uploaded yet."
    
#     latest_filename = latest_data.filename
#     csv_filepath = os.path.join(app.config['EXCEL_FOLDER'], latest_filename)

#     with open(csv_filepath, 'r') as csv_file:
#         csv_reader = csv.reader(csv_file)

#         # Skip the first row containing headers
#         next(csv_reader)  # Skip the first row

#         # Read the second row which contains the days of the week (Monday to Friday)
#         days_of_week = next(csv_reader)[2:]  # Assuming the first two columns are E.ID and Employee Name

#         for row in csv_reader:  # Reading the employee's data rows
#             employee_id = row[0]
#             employee_name = row[1]
#             shifts = row[2:]

#             # Combine the days of the week with the shifts
#             combined_shifts = days_of_week + shifts

#             # Here you can process the employee data and store it in the database
#             data_entry = NewShift(
#                 name_date_day=employee_name,
#             )

#             # Map the combined shifts to corresponding day columns dynamically
#             for day_num, shift in enumerate(combined_shifts, start=1):
#                 setattr(data_entry, f"day_{day_num}", shift)

#             db.session.add(data_entry)

#         db.session.commit()

#     return f"CSV data from {latest_filename} processed and stored in the database."

# @views.route('/del_csv')
# def del_csv():
#     db.session.query(NewShift).delete()
#     db.session.commit()
#     return redirect(url_for('upload_csv'))


@views.route('/dashboard',methods=['POST','GET'])
def dashboard():
    return render_template('dashboard.html')


@views.route('/late_form_page')
def late_form_page():
    return render_template('emp_late.html')


@views.route('/leave_form_page')
def leave_form_page():
    return render_template('emp_leave.html')


@socketio.on('connect')
def handle_connect():
    print('Client Connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')    

@socketio.on('late')
@login_required
def handle_lateform_callback(lateDet):
    emp_id=session.get('emp_id')
    emp_name=session.get('name')
    reason=lateDet['reason']
    from_time=lateDet['from_time']
    to_time=lateDet['to_time']
    status='Pending'
    approved_by='hod name'
    hr_approval='Pending'

    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        user.late_balance -= 1
        email=user.email
        late_balance=user.late_balance
        db.session.commit()
    
    else:
        print(f"Employee with emp_id {emp_id} not found.")
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        try:
            sub=" You Have Taken Late Permission "
            body=" You Have Taken Late permission \n And You Have {} Late balance \n Have a Great Day".format(late_balance)
            send_mail(email, sub, body)
        except:
            print("Mail Not Sent")

    try:
        user=Emp_login.query.filter_by(emp_id=emp_id).first()
        phone=user.phoneNumber
        body=" You Have Taken Late permission \n And You Have {} Late balance \n Have a Great Day".format(late_balance)
        send_sms(phone,body)
    except:
        print("Sms Not Sent")

    try:
        print(reason)
        new_request=late(emp_id=emp_id,emp_name=emp_name,reason=reason,from_time=from_time,to_time=to_time,approved_by=approved_by,status=status,hr_approval=hr_approval)
        db.session.add(new_request)
        db.session.commit()
        print("new request : ",new_request.from_time)
        
        recently_added_row = late.query.order_by(desc(late.id)).first()
        new_request=notifications(emp_id=emp_id,reason=reason,emp_name=emp_name,permission_type='Late',from_time=from_time,to_time=to_time,req_id=recently_added_row.id)
        db.session.add(new_request)
        db.session.commit()

        all_latedata = {'emp_id':emp_id, 'emp_name':emp_name, 'reason':reason, 'from_time':from_time, 'to_time':to_time,'approved_by':approved_by, 'status':status, 'hr_approval':hr_approval}
        print("EMP ID : ",all_latedata['emp_id'])

        emit('late', all_latedata, broadcast=True)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


# @views.route('/request_disp')
# def request_disp():
#     late_permission=late.query.order_by(late.date).all()
#     leave_permission=leave.query.order_by(leave.date).all()
#     return render_template('request_disp.html',late_permission=late_permission,leave_permission=leave_permission)

@socketio.on('leave')
def handle_leaveform_callback(leaveDet):
    emp_id=session.get('emp_id')
    emp_name=session.get('name')
    reason=leaveDet['reason']
    from_time=leaveDet['from_time']
    to_time=leaveDet['to_time']
    status='Pending'
    approved_by='Hod Name'
    hr_approval='Pending'


    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        user.leave_balance -= 1
        email=user.email
        leave_balance=user.leave_balance
        db.session.commit()
    else:
        print(f"Employee with emp_id {emp_id} not found.")
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        try:
            sub=" You Have Taken Leave "
            body=" You Have Taken Leave \n And You Have {} Leave balance \n Have a Great Day".format(leave_balance)
            send_mail(email, sub, body)
        except:
            print("Mail Not Sent")

        try:
            user=Employee.query.filter_by(emp_id=emp_id).first()
            phone=user.phoneNumber
            phone="+91"+phone
            print(type(phone))
            body=" You Have Taken leave permission \n And You Have {} leave balance \n Have a Great Day".format(leave_balance)
            send_sms([phone],body)
        except:
            print("Sms Not Sent")

    try:
        new_request=leave(emp_id=emp_id,emp_name=emp_name,reason=reason,from_time=from_time,to_time=to_time,approved_by=approved_by,status=status,hr_approval=hr_approval)
        db.session.add(new_request)
        db.session.commit()

        recently_added_row = leave.query.order_by(desc(leave.id)).first()
        new_request=notifications(emp_id=emp_id,reason=reason,emp_name=emp_name,permission_type='Leave',from_time=from_time,to_time=to_time,req_id=recently_added_row.id)
        db.session.add(new_request)
        db.session.commit()
        
        all_leaveData={'emp_id':emp_id,'emp_name':emp_name,'reason':reason,'from_time':from_time,'to_time':to_time,'approved_by':approved_by,'status':status,'hr_approval':hr_approval}
        print(all_leaveData)

        emit('leave', all_leaveData, broadcast=True)

    except Exception as e:
        print(f"An error occurred: {str(e)}")



# @views.route("/emp_login_page")
# def emp_login_page():
#     return render_template("emp_log.html")

@views.route("/emp_login",methods=['POST','GET'])
def emp_login():
    if request.method == 'POST':
        emp_id = request.form.get('emp_id') # Get the emp_id from the form
        password = request.form.get('password')  # Get the password from the form

        # Store the email and password in session variables
        
        user = Emp_login.query.filter_by(emp_id=emp_id).first()
        if user:
            if user.password == password:
                login_user(user, remember=True)
                session['emp_id'] = emp_id
                session['password'] = password
                session['name'] = user.name
                session['email'] = user.email
                session['leave_balance']=user.leave_balance
                session['late_balance']=user.late_balance
                return redirect(url_for('views.user_dashboard'))
            else:
                flash("Incorrect Password", category='error')
        else:
            flash("Incorrect Employee ID", category='error')
    return render_template("emp_log.html")

@views.route("/user_dashboard",methods=['POST','GET'])
def user_dashboard():
    if current_user.role=="admin":
        return redirect(url_for('auth.logout'))
    else:
        emp_id = session.get('emp_id')
        user = Emp_login.query.filter_by(emp_id=emp_id).first()
        # date=datetime.strptime(str(user.date), "%Y-%m-%d %H:%M:%S")
        date = (user.date).strftime("%Y-%m-%d")
    return render_template("emp_req_choice.html",user=user,date=date)

# @views.route("/attendance_upload_page",methods=['POST','GET'])
# @login_required
# def attendance_upload_page():
#     return render_template('upload_attendance.html')

@views.route("/attendance_upload",methods=['POST','GET'])
@login_required
def upload_attendance():
    if(request.method=='POST'):
        file=request.files['attendance']
        filename = secure_filename(file.filename)
        print(filename)
        file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
        file.save(file_path)
        attend_excel_data(file_path)
        return redirect(url_for('views.calculate'))

    
    return render_template('upload_attendance.html')

@views.route("/attendance_table")
@login_required
def attendance_table():
    late_permission=late.query.order_by(late.date).all()
    leave_permission=leave.query.order_by(leave.date).all()
    return render_template("admin.html",late_permission=late_permission,leave_permission=leave_permission)

# @views.route("/late_table")
# @login_required
# def late_table():
#     late_permission=late.query.order_by(late.date).all()
#     return render_template("late_table.html",late_permission=late_permission)

# @views.route("/leave_table")
# @login_required
# def leave_table(): 
#     leave_permission=leave.query.order_by(leave.date).all()
#     return render_template("leave_table.html",leave_permission=leave_permission)

@views.route("/late_req_table")
@login_required
def late_req_table():
    notification=notifications.query.order_by(notifications.timestamp).all()
    emp_login=Emp_login.query.order_by(Emp_login.emp_id).all()
    permission_details=late.query.order_by(late.date).all()
    return render_template("req_table.html",emp_login=emp_login,notification=notification,permission=permission_details,permission_type='Late')

@views.route("/leave_req_table")
@login_required
def leave_req_table():
    notification=notifications.query.order_by(notifications.timestamp).all()
    emp_login=Emp_login.query.order_by(Emp_login.emp_id).all()
    permission_details=leave.query.order_by(leave.date).all()
    return render_template("req_table.html",emp_login=emp_login,notification=notification,permission=permission_details,permission_type='Leave')

@views.route("/today_attendance")
@login_required
def today_attendance():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    return redirect(url_for('views.admin'))

# @views.route("/yesterday_attendance")
# @login_required
# def yesterday_attendance():
#     return render_template("admin.html")

# @views.route("/month_attendance")
# @login_required
# def month_attendance():
#     return render_template("month_attendance.html")

# @views.route("/last_month_attendance")
# @login_required
# def last_month_attendance():
#     return render_template("month_attendance.html")

# @views.route('/late_req_profile/<int:emp_id>/<string:emp_name>/<string:from_time>/<string:to_time>/<string:reason>/<int:req_id>')
# @login_required
# def late_req_profile(emp_id, emp_name, from_time, to_time, reason,req_id):
#     user = Emp_login.query.order_by(Emp_login.date.desc()).first()
#     user_late=late.query.filter_by(id=req_id).first()
#     req_date=user_late.date.strftime("%d-%m-%y")
#     req_time=user_late.date.strftime("%H:%M")
#     late_details={
#         'late_balance':user.late_balance,
#         'leave_balance':user.leave_balance,
#         'approval':user_late.hr_approval,
#         'req_date':req_date,
#         'req_time':req_time,
#         'from_time':from_time,
#         'to_time':to_time,
#         'approved_by':user_late.approved_by,
#         'ph_number':user.phoneNumber,
#         'id':user.id,
#         'reason':reason,
#         'emp_id':emp_id,
#         'emp_name':emp_name
#     }
#     session['late_details']=late_details
#     return render_template("late_req_profile.html",late_details=late_details)#,late_permission_dict=late_permission_dict

# @views.route('/leave_req_profile/<int:emp_id>/<string:emp_name>/<string:from_date>/<string:to_date>/<string:reason>/<int:req_id>')
# def leave_req_profile(emp_id, emp_name, from_date, to_date, reason,req_id):
#     user = Emp_login.query.order_by(Emp_login.date.desc()).first()
#     user_leave=leave.query.filter_by(id=req_id).first()
#     leave_details={
#         'leave_balance':user.leave_balance,
#         'leave_balance':user.leave_balance,
#         'approval':user_leave.hr_approval,
#         'approved_by':user_leave.approved_by,
#         'from_date':from_date,
#         'to_date':to_date,
#         'ph_number':user.phoneNumber,
#         'id':user.id,
#         'reason':reason,
#         'emp_id':emp_id,
#         'emp_name':emp_name
#     }
#     session['leave_details']=leave_details
#     return render_template("leave_req_profile.html",leave_details=leave_details)#,late_permission_dict=late_permission_dict

# @views.route('/late_req_profile/<int:emp_id>/<string:emp_name>/<string:from_time>/<string:to_time>/<string:reason>/<int:req_id>')
# @login_required
# def late_req_profile(emp_id, emp_name, from_time, to_time, reason,req_id):
#     user = Emp_login.query.order_by(Emp_login.date.desc()).first()
#     user_late=late.query.filter_by(id=req_id).first()
#     req_date=user_late.date.strftime("%d-%m-%y")
#     req_time=user_late.date.strftime("%H:%M")
#     req_details={
#         'late_balance':user.late_balance,
#         'leave_balance':user.leave_balance,
#         'approval':user_late.hr_approval,
#         'req_date':req_date,
#         'req_time':req_time,
#         'from_time':from_time,
#         'to_time':to_time,
#         'approved_by':user_late.approved_by,
#         'permission_type':'Late',
#         'ph_number':user.phoneNumber,
#         'id':user.id,
#         'reason':reason,
#         'emp_id':emp_id,
#         'emp_name':emp_name
#     }
#     session['late_details']=req_details
#     return render_template("req_profile.html",req_details=req_details)#,late_permission_dict=late_permission_dict

# @views.route('/leave_req_profile/<int:emp_id>/<string:emp_name>/<string:from_time>/<string:to_time>/<string:reason>/<int:req_id>')
# @login_required
# def leave_req_profile(emp_id, emp_name, from_time, to_time, reason,req_id):
#     user = Emp_login.query.order_by(Emp_login.date.desc()).first()
#     user=leave.query.filter_by(id=req_id).first()
#     req_date=user.date.strftime("%d-%m-%y")
#     req_time=user.date.strftime("%H:%M")
#     req_details={
#         'late_balance':user.late_balance,
#         'leave_balance':user.leave_balance,
#         'approval':user.hr_approval,
#         'req_date':req_date,
#         'req_time':req_time,
#         'from_time':from_time,
#         'to_time':to_time,
#         'approved_by':user.approved_by,
#         'ph_number':user.phoneNumber,
#         'permission_type':'Leave',
#         'id':user.id,
#         'reason':reason,
#         'emp_id':emp_id,
#         'emp_name':emp_name
#     }
#     session['leave_details']=req_details
#     return render_template("req_profile.html",req_details=req_details)#,late_permission_dict=late_permission_dict

@views.route('/emp_details')
@login_required
def emp_details():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    emp_login=Emp_login.query.order_by(Emp_login.emp_id).all()
    
    # Separate the records with freezed_account=1 and freezed_account=0
    emp_login_freezed = [emp for emp in emp_login if emp.freezed_account == 1]
    emp_login_active = [emp for emp in emp_login if emp.freezed_account == 0]
    
    # Combine the lists, placing the freezed_account=1 records at the end
    emp_login_sorted = emp_login_active + emp_login_freezed
    print(emp_login_sorted)

    return render_template('emp_details.html',emp_login=emp_login_sorted)

@views.route('/late_req_profile')
@login_required
def late_req_profile():

    emp_id = request.args.get('emp_id')
    emp_name = request.args.get('emp_name')
    from_time = request.args.get('from_time')
    to_time = request.args.get('to_time')
    reason = request.args.get('reason')
    req_id = request.args.get('req_id')
    back_page=request.args.get('back_page')

    notify = notifications.query.filter_by(permission_type='Late', emp_id=emp_id,from_time=from_time,to_time=to_time,reason=reason).first()
    print(notify)
    if notify:
        # If the notifications exists, delete it
        db.session.delete(notify)
        db.session.commit()

    user = Emp_login.query.filter_by(emp_id=emp_id).order_by(Emp_login.date.desc()).first()
    user_late=late.query.filter_by(id=req_id).first()
    req_date=user_late.date.strftime("%d-%m-%y")
    req_time=user_late.date.strftime("%H:%M")
    req_details={
        'late_balance':user.late_balance,
        'leave_balance':user.leave_balance,
        'approval':user_late.hr_approval,
        'req_date':req_date,
        'req_time':req_time,
        'from_time':from_time,
        'to_time':to_time,
        'approved_by':user_late.approved_by,
        'permission_type':'Late',
        'ph_number':user.phoneNumber,
        'id':user_late.id,
        'reason':reason,
        'emp_id':emp_id,
        'emp_name':emp_name,
        'back_page':back_page
    }
    session['details']=req_details
    return render_template("req_profile.html",req_details=req_details,permission_type='Late')#,late_permission_dict=late_permission_dict

@views.route('/leave_req_profile')
@login_required
def leave_req_profile():
    emp_id = request.args.get('emp_id')
    emp_name = request.args.get('emp_name')
    from_time = request.args.get('from_time')
    to_time = request.args.get('to_time')
    reason = request.args.get('reason')
    req_id = request.args.get('req_id')
    back_page=request.args.get('back_page')

    notify = notifications.query.filter_by(permission_type='Leave', emp_id=emp_id,from_time=from_time,to_time=to_time,reason=reason).first()
    print(notify)
    if notify:
        # If the notifications exists, delete it
        db.session.delete(notify)
        db.session.commit()

    # if(request.args.get("notify_id")):
    #     notify_id=request.args.get("notify_id")
    #     permission=request.args.get('permission')
    #     print("Notify id : ", notify_id)
    #     print("permission : ",permission)
    #     notify = notifications.query.filter_by(permission=permission, id=notify_id).first()
    #     print(notify)
    #     if notify:
    #         # If the notifications exists, delete it
    #         db.session.delete(notify)
    #         db.session.commit()
    
    user = Emp_login.query.filter_by(emp_id=emp_id).order_by(Emp_login.date.desc()).first()
    user_leave=leave.query.filter_by(id=req_id).first()
    req_date=user_leave.date.strftime("%d-%m-%y")
    req_time=user_leave.date.strftime("%H:%M")
    req_details={
        'late_balance':user.late_balance,
        'leave_balance':user.leave_balance,
        'approval':user_leave.hr_approval,
        'req_date':req_date,
        'req_time':req_time,
        'from_time':from_time,
        'to_time':to_time,
        'approved_by':user_leave.approved_by,
        'ph_number':user.phoneNumber,
        'permission_type':'Leave',
        'id':user_leave.id,
        'reason':reason,
        'emp_id':emp_id,
        'emp_name':emp_name,
        'back_page':back_page
    }
    session['details']=req_details
    return render_template("req_profile.html",req_details=req_details,permission_type='Leave')#,late_permission_dict=late_permission_dict


# @views.route('/late_req_approve',methods=['POST','GET'])
# def late_req_approve():
#     late_details=session.get('late_details')
#     return render_template("late_req_profile.html",late_details=late_details)

# @views.route('/late_req_decline',methods=['POST','GET'])
# def late_req_decline():
#     late_details=session.get('late_details')
#     return render_template("late_req_profile.html",late_details=late_details)

# @views.route('/leave_approve',methods=['POST','GET'])
# def leave_approve():
#     user = json.loads(request.data)
#     userID = user['userId']
#     user = leave.query.filter_by(emp_id=userID).first()
#     print(" USER : ",user)
#     current_user='hr'
#     if current_user=='hr':
#         user.hr_approval='Approved'
#         user.approved_by=userID
#         db.session.commit()
#         print("Hr Approval ", user.hr_approval)
#         print("Status ", user.status)
#         emit('leave_hr_approval_update', {'userId': userID, 'hr_approval': user.hr_approval}, broadcast=True)

# @views.route('/leave_decline',methods=['POST','GET'])
# def leave_decline():
#     user = json.loads(request.data)
#     userID = user['userId']
#     user = leave.query.filter_by(emp_id=userID).first()
#     print(" USER : ",user)
#     current_user='hr'
#     if current_user=='hr':
#         user.hr_approval='Declined'
#         user.status='Declined'
#         db.session.commit()
#         print("Hr Approval ", user.hr_approval)
#         print("Status ", user.status)
#         emit('leave_hr_approval_update', {'userId': userID, 'hr_approval': user.hr_approval}, broadcast=True)

@views.route('/late_approve', methods=['POST', 'GET'])
def late_approve():
    user_data = json.loads(request.data)
    userID = user_data['userId']
    user = late.query.filter_by(id=userID).first()
    # current_user = 'hr'
    print(current_user.name)
    admin_name=current_user.name
    print("current admin: ", admin_name)
    # if current_user == 'hr':
    user.status='Approved'
    user.hr_approval = 'Approved'
    user.approved_by=admin_name
    db.session.commit()
    # Create a JSON response
    response_data = {
        'approved_by':user.approved_by,
        'userId': userID,
        'hr_approval': user.hr_approval
    }
    return jsonify(response_data)

@views.route('/late_decline', methods=['POST', 'GET'])
def late_decline():
    user_data = json.loads(request.data)
    userID = user_data['userId']
    user = late.query.filter_by(id=userID).first()
    # admin_name=session.get('admin_name')
    admin_name=current_user.name
    user.status='Declined'
    user.hr_approval = 'Declined'
    user.approved_by=admin_name
    db.session.commit()
    
    # Create a JSON response
    response_data = {
        'approved_by':user.approved_by,
        'userId': userID,
        'hr_approval': user.hr_approval
    }
    return jsonify(response_data)


@views.route('/leave_approve',methods=['POST','GET'])
def leave_approve():
    user_data = json.loads(request.data)
    userID = user_data['userId']
    user = leave.query.filter_by(id=userID).first()
    print(" USER : ",user)
    admin_name=current_user.name
    
    user.status='Approved'
    user.hr_approval='Approved'
    user.approved_by=admin_name
    db.session.commit()
    response_data = {
        'approved_by':user.approved_by,
        'userId': userID,
        'hr_approval': user.hr_approval
    }
    return jsonify(response_data)

@views.route('/leave_decline',methods=['POST','GET'])
def leave_decline():
    user = json.loads(request.data)
    userID = user['userId']
    user = leave.query.filter_by(id=userID).first()
    print(" USER : ",user)
    # current_user='hr'
    admin_name=current_user.name
    # admin_name=session.get('admin_name')
    user.hr_approval='Declined'
    user.status='Declined'
    user.approved_by=admin_name
    db.session.commit()
    response_data = {
        'approved_by':user.approved_by,
        'userId': userID,
        'hr_approval': user.hr_approval
    }
    return jsonify(response_data)

# @views.route("/req_notify")
# def req_notify():
#     notify_id=request.args.get("notify_id")
#     permission=request.args.get('permission')
#     print("Notify id : ", notify_id)
#     print("permission : ",permission)
#     notify = notifications.query.filter_by(permission=permission, id=notify_id).first()
#     print(notify)
#     if notify:
#         # If the notifications exists, delete it
#         db.session.delete(notify)
#         db.session.commit()

#     # Redirect to a different page after handling the notification
#     return redirect(url_for('views.' + permission.lower() + '_req_table'))

@views.route("/addemp",methods=['POST','GET'])
@login_required
def upload_emp():
    if(request.method=='POST'):
        file=request.files['emp']
        filename = secure_filename(file.filename)
        print(filename)
        file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
        file.save(file_path)
        add_employee(file_path)
        return redirect(url_for('views.admin'))
    return render_template("addrmp.html")




@views.route('/festival-upload',methods=['POST',"GET"])
def upload_festival():
    if request.method == 'POST':
        file=request.files['excel']
        filename = secure_filename(file.filename)
        print(filename)
        file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
        file.save(file_path)
        up_festival(file_path)
        #return redirect(url_for('views.admin'))
    return render_template("uploadfesti.html")

@views.route('/getshift',methods = ['POST'])
def getshift():
    get_signal = request.get_json()
    signal = get_signal.get('get', False)

    if signal:
        # Assuming Shift_time has attributes like 'id', 'start_time', 'end_time', etc.
        shift_times = Shift_time.query.order_by(Shift_time.id).all()

        # Convert Shift_time objects to dictionaries
        shift_list = [{"id": shift.id, "shiftIntime": shift.shiftIntime, "shiftOuttime": shift.shift_Outtime,"shiftName":shift.shiftType} for shift in shift_times]

        return jsonify({"res": shift_list})

    return jsonify({"error": "Invalid request"})


@views.route('/uploadselect', methods=['POST'])
def upload_select():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    print('dei enda')
    if(request.method=='POST'):

        file_type = request.form.get('filetype')

        # Handle file upload
        if 'emp' in request.files:
            file = request.files['emp']
            print(file_type,"file_type")
            # Customize response based on file_type
            if file_type == 'attendance':
                # print("j=ubjxk")
                filename = secure_filename(file.filename)
                print(filename)
                file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
                file.save(file_path)
                # print('hello')
                attend_excel_data(file_path)
                # print("babdckzub")
                return redirect(url_for('views.calculate'))
            
            elif file_type == 'addEmployee':
                filename = secure_filename(file.filename)
                print(filename)
                file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
                file.save(file_path)
                add_employee(file_path)
                return redirect(url_for('views.admin'))
            
            elif file_type == 'shift':
                filename = secure_filename(file.filename)
                print(filename)
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    process_excel_data(file_path)  # Call the data processing function


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    print("Error message:", str(e))
                    db.session.rollback() 

            elif file_type=='festival':
                filename = secure_filename(file.filename)
                print(filename)
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    up_festival(file_path)  # Call the data processing function


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    print("Error message:", str(e))
                    db.session.rollback()

            elif file_type== 'weekoff' :
                filename = secure_filename(file.filename)
                print(filename)
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    read_weekoff(file_path)  # Call the data processing function


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    print("Error message:", str(e))
                   
        else :
            print('bjsdbcihbs')
            return 'No file uploaded'

    return redirect(url_for('views.admin'))

@views.route('/del_single_emp',methods=['POST'])
def del_single_emp():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    emp_id=request.form.get('empid')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    if emp: 
        db.session.delete(emp)
        db.session.commit()
        print(f"Row with emp_id {emp_id} deleted successfully.")
    else:
        print(f"Row with emp_id {emp_id} not found.")
    return redirect(url_for('views.admin'))

@views.route('/del_multiple_emp',methods=['POST'])
def del_multiple_emp():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    selected_employee_ids = request.form.getlist('select')
    print(selected_employee_ids)
    for i in selected_employee_ids:
        emp=Emp_login.query.filter_by(emp_id=i).first()
        if emp: 
            db.session.delete(emp)
            db.session.commit()
            print(f"Row with emp_id {i} deleted successfully.")
        else:
            print(f"Row with emp_id {i} not found.")
    return redirect(url_for('views.admin'))

@views.route('/edit_employee',methods=['POST'])
def edit_employee():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    emp_id=request.form.get('empid')
    emp_type=request.form.get('editType')
    value=request.form.get('new_value')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    attenName=Attendance.query.filter_by(emp_id=emp_id).all()
    if emp and attenName:
        if emp_type != value:
            setattr(emp,emp_type,value)
            if emp_type=='name':
                for attenName in attenName:
                    setattr(attenName,emp_type,value)
            db.session.commit()
            print(f"Employee with emp_id {emp_id} updated successfully.")
        else:
            print("The value is already assigned.")
    else:
        print(f"Row with emp_id {emp_id} not found.")
    return redirect(url_for('views.admin'))


@views.route('/user-edit',methods=['POST'])
@login_required
def handle_user_editform_callback():
    data = request.json
    print("data :",data)
    new_req=None
    emp_id=data.get('ID')
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    name = user.name
    if data.get('newName'):
        print('new Name')
        newdata = data.get('newName')
        olddata = data.get('oldName')
        new_req=user_edit(emp_id=emp_id, name=name, old_data=olddata, new_data=newdata, data_type='name')

    elif data.get('newDate'):
        print('new Date')
        newdata = data.get('newDate')
        olddata = data.get('oldDate')
        new_req=user_edit(emp_id=emp_id, name=name, old_data=olddata, new_data=newdata, data_type='date')


    elif data.get('newEmail'):
        print('new email')
        newdata=data.get('newEmail')
        olddata=data.get('oldemail')
        new_req=user_edit(emp_id=emp_id, name=name, old_data=olddata, new_data=newdata, data_type='email')

    elif data.get('newMobileNumber'):
        print('new number')
        newdata=data.get('newMobileNumber')
        olddata=data.get('oldphone')
        new_req=user_edit(emp_id=emp_id, name=name, old_data=olddata, new_data=newdata, data_type='phoneNumber')
    else:
        print("data not received properly")

    db.session.add(new_req)
    db.session.commit()
    return jsonify({'data':"request received"})
    

@views.route('/user_edit_data',methods=['POST'])
@login_required
def handle_user_editform():
    try:
        # Perform any necessary data retrieval or processing here
        # For example, let's assume you have a list of user_edit objects
        user_edits = user_edit.query.all()

        # Convert the user_edit objects to a format that can be JSON-serialized
        user_edit_data = [{'id': user.id,'name':user.name, 'data_type': user.data_type, 'old_data': user.old_data, 'new_data': user.new_data, 'emp_id': user.emp_id} for user in user_edits]

        # Send the data as JSON
        return jsonify({'success': True, 'data': user_edit_data})

    except Exception as e:
        # Handle exceptions appropriately
        return jsonify({'success': False, 'error': str(e)})
    
@views.route('/accept_edit',methods=['POST'])
@login_required
def accept_edit():
    data=request.json
    id=data.get('id')
    emp_id=data.get('emp_id')
    name=data.get('name')
    data_type=data.get('data_type')
    old_data=data.get('old_data')
    new_data=data.get('new_data')

    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    old_value=getattr(emp,data_type)
    if old_data==old_value:
        setattr(emp,data_type,new_data)
    else:
        print("data not matched")
    
    user=user_edit.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify("Changed Successfully")

@views.route('/decline_edit',methods=['POST'])
@login_required
def decline_edit():
    data=request.json
    id=data.get('id')
    user=user_edit.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify("Request Declined")

# @views.route('/send_message', methods=['POST'])
# def send_message():
    # data = request.json
    # id = data.get('id')
    
    # # Assuming Emp_login is a SQLAlchemy model
    # emp = Emp_login.query.filter_by(emp_id=id).first()
    
    # if emp:
    #     Phonenum = emp.phoneNumber
    #     email = emp.email
    #     sub='Miss punch'
    #     message = f"""
    #     Dear {emp.name}:
    #     It is a gentle reminder to you,
    #     You have missed to keep the punch in the biometric machine
    #     """
    #     print("Phone number:", Phonenum)
    #     #send_mail(email=email, body=message,subject=sub)
    #     send_sms(Phonenum ,message)
        
    #     # Send a JSON response
    #     return jsonify({"data": "Message sent"})
    # else:
    #     # Send a JSON response indicating the employee was not found
    #     return jsonify({"error": "Employee not found"})
@views.route('/fetch_emp_details',methods=['POST'])
def fetch_emp_details():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    form_data = request.form
    emp_id=form_data['empid']
    editType=form_data['editType']
    value=Emp_login.query.filter_by(emp_id=emp_id).first()

    print(form_data)

    response_data = {'value': getattr(value,editType)}

    return jsonify(response_data)

@views.route('/send_message_data',methods=['GET'])
def send_message_data():
    try:
        print('hi')
        currentShift=request.args.get('currentShift')
        lastShift=request.args.get('lastShift')
        lastShift_db =Shift_time.query.filter_by(shiftType=lastShift).first()
        session['lastShift']=lastShift_db.shift_Outtime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Assuming 'shift' is an attribute of the Attendance model
        last_shift_db = db.session.query(Attendance).filter(
            func.DATE(Attendance.date) == current_date,
            Attendance.shiftType == lastShift
        ).all()
        
        if last_shift_db:
            for record in last_shift_db:
                if record.outTime == '-':
                    check_send_sms(record.emp_id)
                    
    except Exception as e:
        print(e)
    return jsonify('received')


# @views.route('/send_continue_message',methods=['POST'])
# def send_continue_message():

#     data = request.json
#     id = data.get('id')
#     print("Continue", id)
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date,Attendance.emp_id==id).first()
#     print("befor :",attendance.attendance)
#     attendance.attendance='O.T'
#     db.session.commit()
#     print("after :",attendance.attendance)

#     today = datetime.now()

#     # Calculate the date for the next day
#     next_day = today + timedelta(days=1)

#     # week_off=Week_off.query.all()
#     existing_week_off=Week_off.query.filter_by(emp_id=id,date=next_day).first()
#     if not (existing_week_off):
#         new_req=Week_off(emp_id=id,date=next_day)
#         db.session.add(new_req)
#         db.session.commit()
#     else:
#         print("week_off for ,",id," on ",next_day," is exist")
        
#         # Send a JSON response
#     return jsonify({"data": "Message sent"})


def get_last_month_dates():
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month, today

@views.route('/month_attendance',methods=['POST','GET'])
def month_attendance():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    start_date, end_date = get_last_month_dates()

    # Query the database for last month's attendance up to the current date
    last_month_attendance = db.session.query(Attendance).filter(
        Attendance.date.between(start_date, end_date)
    ).all()
    # print(start_date,end_date)

    # Create a dictionary to store attendance records for each emp_id
    employee_data = {}
    date = set()
    
    for record in last_month_attendance:
        emp_id = record.emp_id
        record_date=record.date
        # print(str(record_date)[:10])
        date.add(str(record_date)[8:10])
        
        # If emp_id is not in t8e dictionary, create a new list for that emp_id
        if emp_id not in employee_data:
            employee_data[emp_id] = []
        
        # Append the record to the list for that emp_id
        employee_data[emp_id].append(record)

        # print(employee_data[emp_id])
        # print(date)
    date = list(date)
    print(date)
    return render_template('month_attendance.html', employee_data=employee_data,date=date)


@views.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    id = data.get('id')
    
    # Assuming Emp_login is a SQLAlchemy model
    emp = Emp_login.query.filter_by(emp_id=id).first()
    current_date = datetime.now().strftime('%Y-%m-%d')
    message="message"

    attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date,Attendance.emp_id==id).first()
    
    if attendance.attendance=='Leave':
        message = f"""
        Dear {emp.name}:
        It is a gentle reminder to you,
        You have Taken Leave today  (Date: {current_date}). 
        """
        
    if attendance.attendance=='O.T':
        message = f"""
        Dear {emp.name}:
        It is a gentle reminder to you,
        Your O.T has been canceled today (Date: {current_date})
        """
        attendance.attendance='Present'
    db.session.commit()
    
    if emp:
        Phonenum = emp.phoneNumber
        email = emp.email
        sub='Miss punch'
        # message = f"""
        # Dear {emp.name}:
        # It is a gentle reminder to you,
        # You have missed to keep the punch in the biometric machine
        # """
        print("Phone number:", Phonenum)
        #send_mail(email=email, body=message,subject=sub)
        send_sms(Phonenum ,message)
        
        # Send a JSON response
        return jsonify({"data": "Message sent"})
    else:
        # Send a JSON response indicating the employee was not found
        return jsonify({"error": "Employee not found"})




@views.route('/send_continue_message',methods=['POST'])
def send_continue_message():
    data = request.json
    id = data.get('id')
    print("Continue", id)
    current_date = datetime.now().strftime('%Y-%m-%d')
    attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date,Attendance.emp_id==id).first()
    print("befor :",attendance.attendance)
    if attendance.attendance=='Present':
        attendance.attendance='O.T'
    elif attendance.attendance=='Leave':
        attendance.attendance='Present'
    elif attendance.attendance=='Wrong Shift':
        attendance.attendance='Present'
    db.session.commit()
    print("after :",attendance.attendance)

    today = datetime.now()

    # Calculate the date for the next day
    next_day = today + timedelta(days=1)

    # week_off=Week_off.query.all()
    existing_week_off=Week_off.query.filter_by(emp_id=id,date=next_day).first()
    if not (existing_week_off):
        new_req=Week_off(emp_id=id,date=next_day)
        db.session.add(new_req)
        db.session.commit()
    else:
        print("week_off for ,",id," on ",next_day," is exist")
        
        # Send a JSON response
    return jsonify({"data": "Message sent"})
