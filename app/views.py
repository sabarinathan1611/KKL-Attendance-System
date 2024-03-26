from flask_login import login_required, current_user,login_user
from . import db
from .models import Attendance,Shift_time,Backup, late, leave,notifications ,Emp_login,user_edit,call_duty
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
from apscheduler.schedulers.background import BackgroundScheduler
from flask import send_from_directory,current_app




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
        session['flash_message']=['Unauthorized Access','error']
        return redirect(url_for('auth.logout'))
    else :
        create_dummy_attendance()
        # current_time = datetime.now().strftime('%H:%M:%S')
        current_date = datetime.now().strftime('%Y-%m-%d')
        employee_attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date).all()
        employee_attendance.sort(key=lambda x: 0 if x.attendance == 'Wrong shift' else 1)
        emp_login=Emp_login.query.order_by(Emp_login.emp_id).all()
        current_shifts=get_current_shift()
        late_permission=late.query.order_by(late.date).all()
        leave_permission=leave.query.order_by(leave.date).all()
        notification=notifications.query.order_by(notifications.timestamp).all()

        emp_login_freezed = [emp for emp in emp_login if emp.freezed_account == True]
        emp_login_active = [emp for emp in emp_login if emp.freezed_account == False]
        # create_dummy_attendance()
        # Combine the lists, placing the freezed_account=1 records at the end1
        emp_login_sorted = emp_login_active + emp_login_freezed
        
        month_attend=month_attendance()
        employee_data=month_attend[0]
        date=month_attend[1]
        backup=Backup.query.all()
        # create_dummy_attendance()
        print('curre\n\n\n',current_shifts)
        
        # session['flash_message'] = ['Logged in successfully!','success']


    return render_template('admin.html',current_shifts=current_shifts,employee_data=employee_data,backup=backup,date=date,emp_login=emp_login, notification=notification, attendance=employee_attendance, late_permission=late_permission, leave_permission=leave_permission,emp_login_sorted=emp_login_sorted)

@views.route('/delete_flash_message', methods=['POST'])
def delete_flash_message():
    delete_session()
    return jsonify({'message': 'Flash message deleted'})

@socketio.on('connect')
def handle_connect():
    print('Client Connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')    

@socketio.on('late')
@login_required
def handle_lateform_callback(lateDet):
    print('\n\nlate socket triggered\n\n\n')
    emp_id=current_user.emp_id
    # emp_name=session.get('name')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    emp_name=emp.name
    reason=lateDet['reason']
    from_time=lateDet['from_time']
    to_time=lateDet['to_time']
    status='Pending'
    approved_by='hod name'
    hr_approval='Pending'

    try:
        new_request=late(emp_id=emp_id,emp_name=emp_name,reason=reason,from_time=from_time,to_time=to_time,approved_by=approved_by,status=status,hr_approval=hr_approval)
        db.session.add(new_request)
        db.session.commit()
        print("new request : ",new_request.from_time)
        id = new_request.id
        
        recently_added_row = late.query.order_by(desc(late.id)).first()
        new_request=notifications(emp_id=emp_id,reason=reason,emp_name=emp_name,permission_type='Late',from_time=from_time,to_time=to_time,req_id=recently_added_row.id)
        db.session.add(new_request)
        db.session.commit()
        date=recently_added_row.date

        all_latedata = {'id' : id,'date':str(date),'emp_id':emp_id, 'emp_name':emp_name, 'reason':reason, 'from_time':from_time, 'to_time':to_time,'approved_by':approved_by, 'status':status, 'hr_approval':hr_approval}
        print("EMP ID : ",all_latedata['emp_id'])
        # flash('New notification','success')
        session['flash_message']=['Request Sent','success']

        emit('late', all_latedata, broadcast=True)

    except Exception as e:
        session['flash_message']=['Request Not sent','error']
        print(f"An error occurred: {str(e)}")


# @views.route('/request_disp')
# def request_disp():
#     late_permission=late.query.order_by(late.date).all()
#     leave_permission=leave.query.order_by(leave.date).all()
#     return render_template('request_disp.html',late_permission=late_permission,leave_permission=leave_permission)

@socketio.on('leave')
def handle_leaveform_callback(leaveDet):
    print('\n\n\nleave came\n\n\n')
    emp_id=current_user.emp_id
    # emp_name=session.get('name')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    emp_name=emp.name
    reason=leaveDet['reason']
    from_time=leaveDet['from_time']
    to_time=leaveDet['to_time']
    status='Pending'
    approved_by='Hod Name'
    hr_approval='Pending'

    try:
        new_request=leave(emp_id=emp_id,emp_name=emp_name,reason=reason,from_time=from_time,to_time=to_time,approved_by=approved_by,status=status,hr_approval=hr_approval)
        db.session.add(new_request)
        db.session.commit()
        id = new_request.id

        recently_added_row = leave.query.order_by(desc(leave.id)).first()
        new_request=notifications(emp_id=emp_id,reason=reason,emp_name=emp_name,permission_type='Leave',from_time=from_time,to_time=to_time,req_id=recently_added_row.id)
        db.session.add(new_request)
        db.session.commit()
        date=recently_added_row.date
        
        all_leaveData={'id':id,'date':str(date),'emp_id':emp_id,'emp_name':emp_name,'reason':reason,'from_time':from_time,'to_time':to_time,'approved_by':approved_by,'status':status,'hr_approval':hr_approval}
        print(all_leaveData)
        session['flash_message']=['Request Sent','success']
        # flash('New notification','success')

        emit('leave', all_leaveData, broadcast=True)

    except Exception as e:
        session['flash_message']=['Request Not sent','error']
        print(f"An error occurred: {str(e)}")


@views.route("/user_dashboard",methods=['POST','GET'])
def user_dashboard():
    if current_user.role=="admin":
        return redirect(url_for('auth.logout'))
    else:#emp_id=sess
        emp_id = current_user.emp_id
        user = Emp_login.query.filter_by(emp_id=emp_id).first()
        # date=datetime.strptime(str(user.date), "%Y-%m-%d %H:%M:%S")
        date = (user.date).strftime("%Y-%m-%d")
        attendance_details={
            'absent':0,
            'present':0,
            'half_day':0,
            'communicated':0,
            'wrong_shift':0,
            'week_off':0,
            'c_off':0,
            'wop':0
        }

        attendance_details['present']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Present').count()
        attendance_details['absent']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Absent').count()
        attendance_details['half_day']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Half day').count()
        attendance_details['communicated']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Leave').count()
        attendance_details['wrong_shift']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Wrong Shift').count()
        attendance_details['week_off']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='Week Off').count()
        attendance_details['c_off']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='C off').count()
        attendance_details['wop']=Attendance.query.filter(Attendance.emp_id==emp_id,Attendance.attendance=='wop').count()

        # employees=Attendance.query.filter_by(emp_id=emp_id).all()


        # for emp in employees:
        #     if emp.attendance=='Absent':
        #         attendance_details['absent']+=1

        #     elif emp.attendance=='half-day':
        #         attendance_details['half_day']+=1

        #     elif emp.attendance=='Wrong Shift':
        #         attendance_details['wrong_shift']+=1
            
        #     elif emp.attendance=='Leave':
        #         attendance_details['communicated']+=1
            
        #     elif emp.attendance=='Week Off':
        #         attendance_details['week_off']+=1
            
        #     elif emp.attendance=='C Off':
        #         attendance_details['c_off']+=1

        #     elif emp.attendance=='Wop':
        #         attendance_details['wop']+=1
            
        #     else:
        #         attendance_details['present']+=1
        print(attendance_details)

        late_det=False
        leave_det=False
        
        late_det=late.query.filter_by(emp_id=emp_id).all()
        leave_det=leave.query.filter_by(emp_id=emp_id).all()
        # all_permission = late.query.filter(late.date).union(leave.query.filter(leave.date)).order_by(text('date')).all()
        # flash('Logged In Successfully','success') 
        

    return render_template("emp_dashboard.html",user=user,date=date,attendance_details=attendance_details,late=late_det,leave=leave_det)

# @views.route("/attendance_upload",methods=['POST','GET'])
# @login_required
# def upload_attendance():
#     if(request.method=='POST'):
#         file=request.files['attendance']
#         filename = secure_filename(file.filename)
#         print(filename)
#         file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
#         file.save(file_path)
#         attend_excel_data(file_path)
#         flash('Attendance Uploaded','success')
#         return redirect(url_for('views.calculate'))

#     return redirect(url_for('views.admin'))


@views.route('/late_approve', methods=['POST', 'GET'])
def late_approve():
    user_data = json.loads(request.data)
    id = user_data['id']
    user = late.query.filter_by(id=id).first()
    # current_user = 'hr'
    print(current_user.name)
    admin_name=current_user.name
    print("current admin: ", admin_name)
    # if current_user == 'hr':
    user.status='Approved'
    user.hr_approval = 'Approved'
    user.approved_by=admin_name
    db.session.commit()
    emp_id=user.emp_id

    # Create a JSON response
    response_data = {
        'approved_by':user.approved_by,
        'userId': emp_id,
        'hr_approval': user.hr_approval
    }
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        user.late_balance -= 1
        email=user.email
        late_balance=user.late_balance-1
        db.session.commit()
    else:
        print(f"Employee with emp_id {emp_id} not found.")
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        try:
            sub=" You Have Taken Late "
            body=" You Have Taken Late \n And You Have {} Late balance \n Have a Great Day".format(late_balance)
            send_mail(email, sub, body)
        except:
            print("Mail Not Sent")

        try:
            user=Emp_login.query.filter_by(emp_id=emp_id).first()
            phone=user.phoneNumber
            phone="+91 "+str(phone)
            print(type(phone))
            body=" You Have Taken Late permission \n And You Have {} Late balance \n Have a Great Day".format(late_balance)
            send_sms([phone],body)
        except Exception as e:
            print("Sms Not Sent",e)
    return jsonify(response_data)

@views.route('/late_decline', methods=['POST', 'GET'])
def late_decline():
    user_data = json.loads(request.data)
    id = user_data['id']
    user = late.query.filter_by(id=id).first()
    # admin_name=session.get('admin_name')
    admin_name=current_user.name
    user.status='Declined'
    user.hr_approval = 'Declined'
    user.approved_by=admin_name
    db.session.commit()
    emp_id=user.emp_id
    
    # Create a JSON response
    response_data = {
        'approved_by':user.approved_by,
        'userId': emp_id,
        'hr_approval': user.hr_approval
    }
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        late_balance=user.late_balance
        db.session.commit()
    else:
        print(f"Employee with emp_id {emp_id} not found.")
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        try:
            sub=" Your late Denied"
            body=" Your late Request Denied . Date {}".format(late_balance)
            send_mail(email, sub, body)
        except:
            print("Mail Not Sent")

        try:
            user=Emp_login.query.filter_by(emp_id=emp_id).first()
            phone=user.phoneNumber
            phone="+91 "+ str(phone)
            print(type(phone))
            body=" Your late Request Denied . Date {}".format(late_balance)
            send_sms([phone],body)
        except Exception as e:
            print("Sms Not Sent",e)

    return jsonify(response_data)


@views.route('/leave_approve',methods=['POST','GET'])
def leave_approve():
    user_data = json.loads(request.data)
    id = user_data['id']
    user = leave.query.filter_by(id=id).first()
    print(" USER : ",user)
    admin_name=current_user.name
    
    user.status='Approved'
    user.hr_approval='Approved'
    user.approved_by=admin_name
    db.session.commit()
    emp_id=user.emp_id
    response_data = {
        'approved_by':user.approved_by,
        'userId': emp_id,
        'hr_approval': user.hr_approval
    }
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        user.leave_balance -= 1
        email=user.email
        leave_balance=user.leave_balance-1
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
            user=Emp_login.query.filter_by(emp_id=emp_id).first()
            phone=user.phoneNumber
            phone="+91"+phone
            print(type(phone))
            body=" You Have Taken leave permission \n And You Have {} leave balance \n Have a Great Day".format(leave_balance)
            send_sms([phone],body)
        except Exception as e:
            print("Sms Not Sent",e)

    return jsonify(response_data)

@views.route('/leave_decline',methods=['POST','GET'])
def leave_decline():
    user = json.loads(request.data)
    id = user['id']
    user = leave.query.filter_by(id=id).first()
    print(" USER : ",user)
    # current_user='hr'
    admin_name=current_user.name
    # admin_name=session.get('admin_name')
    user.hr_approval='Declined'
    user.status='Declined'
    user.approved_by=admin_name
    db.session.commit()
    emp_id=user.emp_id
    response_data = {
        'approved_by':user.approved_by,
        'userId': emp_id,
        'hr_approval': user.hr_approval
    }
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        leave_balance=user.leave_balance
        db.session.commit()
    else:
        print(f"Employee with emp_id {emp_id} not found.")
    user=Emp_login.query.filter_by(emp_id=emp_id).first()
    if user:
        email=user.email
        try:
            sub=" Your leave Denied"
            body=" Your leave Request Denied . Date {}".format(leave_balance)
            send_mail(email, sub, body)
        except:
            print("Mail Not Sent")

        try:
            user=Emp_login.query.filter_by(emp_id=emp_id).first()
            phone=user.phoneNumber
            phone="+91"+phone
            print(type(phone))
            body=" Your leave Request Denied . Date {}".format(leave_balance)
            send_sms([phone],body)
        except Exception as e:
            print("Sms Not Sent",e)
    return jsonify(response_data)

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
    if(request.method=='POST'):

        file_type = request.form.get('filetype')
        print('Entered here 685')
        # Handle file upload
        if 'emp' in request.files:
            file = request.files['emp']
            # print(file_type,"file_type")
            # Customize response based on file_type
            # if file_type == 'attendance':
            #     try:
            #         # print("j=ubjxk")
            #         filename = secure_filename(file.filename)
            #         # print(filename)
            #         file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
            #         file.save(file_path)
            #         # print('hello')
            #         attend_excel_data(file_path)
            #         # print("babdckzub")
            #         return redirect(url_for('views.calculate'))
            #     except:
            #         flash('Oops! Something Went wrong.','error')
            
            if file_type == 'addEmployee':
                filename = secure_filename(file.filename)
                # print(filename)
                try:
                    file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
                    file.save(file_path)
                    add_employee(file_path)
                    session['flash_message']=['File Uploaded Successfully','success']

                except Exception as e:
                    print("Error type:", type(e).__name__)
                    session['flash_message']=['File Not Uploaded','error']

                return redirect(url_for('views.admin'))
            
            elif file_type == 'employeeShifts':
                filename = secure_filename(file.filename)
                try:
                    file_path=os.path.join(app.config['EXCEL_FOLDER'], filename)
                    file.save(file_path)
                    addEmpShifts(file_path)
                    session['flash_message']=['File Uploaded Successfully','success']

                except Exception as e:
                    print("Error type:", type(e).__name__)
                    session['flash_message']=['File Not Uploaded','error']

                return redirect(url_for('views.admin'))

            
            elif file_type == 'shift':
                filename = secure_filename(file.filename)
                # print(filename)
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    process_excel_data(file_path)  # Call the data processing function
                    session['flash_message']=['File Uploaded Successfully','success']


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    session['flash_message']=['File Not Uploaded','error']
                    print("Error message:", str(e))
                    db.session.rollback() 

            elif file_type=='festival':
                filename = secure_filename(file.filename)
                print(filename,'\n\n\n\nfilename')
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    up_festival(file_path)  # Call the data processing function
                    session['flash_message']=['File Uploaded Successfully','success']


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    session['flash_message']=['File Not Uploaded','error']
                    print("Error message:", str(e))
                    db.session.rollback()

            elif file_type== 'weekoff' :
                filename = secure_filename(file.filename)
                # print(filename)
                try:
                    file_path = os.path.join(app.config['EXCEL_FOLDER'], str(filename))  # Use correct case 'EXCEL_FOLDER
                    # print('nuubyv')
                    file.save(file_path)
                    read_weekoff(file_path)  # Call the data processing function
                    session['flash_message']=['File Uploaded Successfully','success']


                except Exception as e:
                    print("Error type:", type(e).__name__)
                    session['flash_message']=['File Not Uploaded','error']
                    print("Error message:", str(e))
                   
        else :
            print('No file uploaded')
            return 'No file uploaded'

    return redirect(url_for('views.admin'))

@views.route('/del_single_emp',methods=['POST'])
def del_single_emp():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    emp_id=request.form.get('empid')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    atten_emp=Attendance.query.filter_by(emp_id=emp_id).all()
    notify= notifications.query.filter_by(emp_id=emp_id).all()
    for notify in notify:
        db.session.delete(notify)
    db.session.commit()
    users=user_edit.query.filter_by(emp_id=emp_id).all()
    for user in users:
        db.session.delete(user)
    db.session.commit()

    atten_emp_count = Attendance.query.filter((Attendance.emp_id == emp_id) & ((Attendance.attendance == "Present") | (Attendance.attendance == "Half day"))).count()

    if atten_emp:
        for atten in atten_emp:
            db.session.delete(atten)
            db.session.commit()
    if emp:
        backup_entry = Backup(
            date=datetime.now(),
            email=emp.email,
            name=emp.name,
            password=emp.password,
            emp_id=emp.emp_id,
            branch=emp.branch,
            phoneNumber=emp.phoneNumber,
            role=emp.role,
            address=emp.address,
            gender=emp.gender,
            worked=atten_emp_count
        )
        db.session.add(backup_entry) 
        db.session.delete(emp)
        db.session.commit()
        print(f"Row with emp_id {emp_id} deleted successfully.")
        session['flash_message']=['Employee Deleted Succesfully','success']
    else:
        session['flash_message']=['Employee Not Deleted','error']
        print(f"Row with emp_id {emp_id} not found.")
    return redirect(url_for('views.admin'))

@views.route('/del_multiple_emp',methods=['POST'])
def del_multiple_emp():
    if current_user.role == 'employee':
        return redirect(url_for('auth.logout'))
    selected_employee_ids = request.form.getlist('select')
    print("\n\n\n\n\n\n\n\n\n",selected_employee_ids)
    
    for emplo in selected_employee_ids:
        emp=Emp_login.query.filter_by(emp_id=emplo).first()
        atten_emp=Attendance.query.filter_by(emp_id=emplo).all()
        atten_emp_count = Attendance.query.filter((Attendance.emp_id == emplo) & ((Attendance.attendance == "Present") | (Attendance.attendance == "Half day"))).count()
        if emp:
            if atten_emp:
                for atten in atten_emp:
                    db.session.delete(atten)
                    db.session.commit()

            notify= notifications.query.filter_by(emp_id=emplo).all()
            for notif in notify:
                db.session.delete(notif)
            db.session.commit()

            users=user_edit.query.filter_by(emp_id=emplo).all()
            for user in users:
                db.session.delete(user)
            db.session.commit()
            
            backup_entry = Backup(
                date=datetime.now(),
                email=emp.email,
                name=emp.name,
                password=emp.password,
                emp_id=emp.emp_id,
                branch=emp.branch,
                phoneNumber=emp.phoneNumber,
                role=emp.role,
                address=emp.address,
                gender=emp.gender,
                # shift=emp.shift,
                worked=atten_emp_count
                
            )
            db.session.add(backup_entry) 
            db.session.delete(emp)
            db.session.commit()
    # for i in selected_employee_ids:
    #     emp=Emp_login.query.filter_by(emp_id=i).first()
    #     if emp: 
    #         db.session.delete(emp)
    #         db.session.commit()
    #         flash('Employees Deleted Succesfully','success')
    #         print(f"Row with emp_id {i} deleted successfully.")
    #     else:
    #         flash('Employees Not Deleted','error')
    #         print(f"Row with emp_id {i} not found.")
    # employees_deleted = Emp_login.query.filter(Emp_login.emp_id.in_(selected_employee_ids)).delete(synchronize_session=False)
    
    
    # if employees_deleted:
    #     db.session.commit()
            session['flash_message']=['Employees Deleted Successfully', 'success']
            print("Rows deleted successfully.")
        else:
            session['flash_message']=['Employee Not Deleted','error']
            print("Rows not found.")
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
    try:
        data = request.json
        print("data :",data)
        new_req=None
        emp_id=current_user.emp_id
        print(emp_id)
        user=Emp_login.query.filter_by(emp_id=emp_id).first()
        name = user.name
        newdata = data.get('new')
        data_type = data.get('type')
        olddata = data.get('old')
        if data_type=='password':
            new_req=user_edit(emp_id=emp_id, name=name, old_data='-', new_data=generate_password_hash(newdata), data_type=data_type)
        else:
            new_req=user_edit(emp_id=emp_id, name=name, old_data=olddata, new_data=newdata, data_type=data_type)
        db.session.add(new_req)
        db.session.commit()
        result={'status':True,'message':'Message Sent Successfully'}
        session['flash_message']=['Request Sent Successfully','success']

    except Exception as e:
        print("line 972",e)
        result={'status':False,'message':'Message Not Sent'}
        session['flash_message']=['Request Not Sent','success']

    return jsonify(result)
    

@views.route('/user_edit_data',methods=['POST'])
@login_required
def handle_user_editform():
    try:
        # Perform any necessary data retrieval or processing here
        # For example, let's assume you have a list of user_edit objects
        user_edits = user_edit.query.all()

        # Convert the user_edit objects to a format that can be JSON-serialized
        user_edit_data = [{'id': user.id,
                   'name': user.name,
                   'data_type': user.data_type,
                   'old_data': '-' if user.data_type == 'password' else user.old_data,
                   'new_data': '-' if user.data_type == 'password' else user.new_data,
                   'emp_id': user.emp_id} for user in user_edits]


        # Send the data as JSON
        return jsonify({'success': True, 'data': user_edit_data})

    except Exception as e:
        # Handle exceptions appropriately
        return jsonify({'success': False, 'error': str(e)})
    
@views.route('/accept_edit',methods=['POST'])
@login_required
def accept_edit():
    id=request.json.get('id')
    data=user_edit.query.filter_by(id=id).first()
    emp_id=data.emp_id
    # name=data.name
    data_type=data.data_type
    # old_data=data.get('old_data')
    new_data=data.new_data

    if data_type=='name':
        atten=Attendance.query.filter_by(emp_id=emp_id).all()
        for atten in atten:
            atten.name=new_data
            db.session.commit()

    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    # old_value=getattr(emp,data_type)
    if data_type=='password':
        setattr(emp,data_type,new_data)
    else:
        setattr(emp,data_type,new_data)
    db.session.commit()

    late_table=late.query.filter_by(emp_id=emp_id).first()
    if late_table:
        try:
            setattr(late_table,data_type,new_data)
        except:
            print('eror here at 972')
    db.session.commit()
        
    leave_table=leave.query.filter_by(emp_id=emp_id).first()
    if leave_table:
        try:
            setattr(leave_table,data_type,new_data)
        except:
            print('eror here at 972')
    db.session.commit()
    
    user=user_edit.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify("Changed Successfully")

@views.route('/decline_edit',methods=['POST'])
@login_required
def decline_edit():
    id=request.json.get('id')
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
@login_required
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
@login_required
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
                if record.outTime == None:
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


@views.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    id = data.get('id')
    
    # Assuming Emp_login is a SQLAlchemy model
    emp = Emp_login.query.filter_by(emp_id=id).first()
    current_date = datetime.now().strftime('%Y-%m-%d')
    message="message"

    attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date,Attendance.emp_id==id).first()
    
    if attendance.attendance=='Absent':
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
@login_required
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

@views.route('/bring_req_profile',methods=['POST'])
@login_required
def bring_req_profile():
    # print('hello')
    data = request.json
    req_id = data.get('id')
    permission_type = data.get('permission_type')
    print('views 1249',req_id)
    table=[]
    
    print('permission_type ',permission_type)
    if permission_type=='late':
        table=late.query.filter_by(id=req_id).first()
    if permission_type=='leave':
        table=leave.query.filter_by(id=req_id).first()

    emp_id = table.emp_id
    emp_name = table.emp_name
    from_time = table.from_time
    to_time = table.to_time
    reason = table.reason
    req_id = table.id

    notify = notifications.query.filter_by(permission_type=permission_type.capitalize(), req_id=req_id).first()
    print(notify)
    if notify:
        # If the notifications exists, delete it
        db.session.delete(notify)
        db.session.commit()
    user = Emp_login.query.filter_by(emp_id=emp_id).order_by(Emp_login.date.desc()).first()
    # print('hello')
    req_date=table.date.strftime("%d-%m-%y")
    req_time=table.date.strftime("%H:%M")
    req_details={
        'late_balance':user.late_balance,
        'leave_balance':user.leave_balance,
        'address':user.address,
        'status':table.status,
        'approval':table.hr_approval,
        # 'shift':user.shift,
        'req_date':req_date,
        'req_time':req_time,
        'from_time':from_time,
        'to_time':to_time,
        'approved_by':table.approved_by,
        'ph_number':user.phoneNumber,
        'permission_type':'Leave',
        'id':table.id,
        'reason':reason,
        'emp_id':emp_id,
        'emp_name':emp_name,
    }

    # print('hello')
    return jsonify ({'data':req_details})

@views.route('/save_attendance',methods=['POST'])
@login_required
def save_attendance():
    form_data = request.form

    for key, value in form_data.items():
        print(f"Key: {key}, Value: {value}")

    emp_id=form_data['emp_id']
    date=form_data['date']
    attendance=Attendance.query.filter_by(emp_id=emp_id,date=date).first()

    if attendance.inTime==None:
        punchIn=form_data['punchIn']
        if punchIn=='absent':
            attendance.attendance='Absent'
            db.session.commit()
        elif punchIn=='communicated':
            attendance.attendance='Leave'
            db.session.commit()
    elif attendance.lateBy:
        # hours, minutes = map(int, attendance.lateBy.split(':'))
        hours=attendance.lateBy.hour
        minutes=attendance.lateBy.minute
        # print(hours * 60 + minutes >10)
        if ((hours * 60 + minutes )>10):
            wrongShift=form_data['wrongShift'] # half-day,present
            if wrongShift=='half-day':
                attendance.attendance='Half day'
                db.session.commit()
            elif wrongShift=='Present':
                attendance.attendance='Present'
                db.session.commit()


    if attendance.outTime==None and attendance.inTime!=None:
        punchOut=form_data['punchOut'] # mis-pinch, shift-continue
        if punchOut=='mis-pinch':
            print("\n\n\n\n\n\n\n",punchOut)
            attendance.outTime=datetime(1, 1, 1, 0, 0, 0)
            # punch_out_reminder(emp_id)
            db.session.commit()
        elif punchOut=='shift-continue':
            new_req=comp_off(emp_id=emp_id,date=date)                        
            db.session.add(new_req)
            db.session.commit()

    if attendance.attendance=='Wrong Shift':
        wrongshift=form_data['wrongShift']
        if wrongshift=='wrong-shift':
            attendance.attendance='Wrong Shift'
            db.session.commit()
        elif wrongshift=='call-duty':
            new_req=call_duty(emp_id=emp_id,date=date,inTime=attendance.inTime,outTime=attendance.outTime)
            db.session.add(new_req)
            db.session.commit()
        elif wrongshift=='present':
            attendance.attendance='Present'
            db.session.commit()
        else:
            overtime=attendance.overtime  # need to write code for this.......
            print(overtime)
            db.session.commit()
    # print('\n\n\n\n Attendance saved successfully \n\n\n\n')


    return jsonify({'message': 'Attendance saved successfully'})


# @views.route('/check_user_request')
# def check_user_request():
#     emp_id = request.json
#     late_det=late.query.filter_by(emp_id=emp_id).all()
#     leave_det=leave.query.filter_by(emp_id=emp_id).all()
#     return jsonify ({'late_det':late_det,'leave_det':leave_det})

# @views.route('get_chart')
# @login_required
# def get_chart():
#     chartDet={
#         'total_present':0,
#         'kkl_employee':0,
#         'dr_employee':0,
#         'ft_employee':0,
#     }
#     current_date=datetime.now()
#     today = current_date.strftime('%Y-%m-%d')
#     attendance = Attendance.query.filter(Attendance.inTime != None, Attendance.outTime == None).all()
#     chartDet['total_present']=len(attendance)
#     chartDet['kkl_employee']=Attendance.query.filter(Attendance.branch=='KKL',Attendance.inTime != None, Attendance.outTime == None).count()
#     chartDet['dr_employee']=Attendance.query.filter(Attendance.branch=='DR',Attendance.inTime != None, Attendance.outTime == None).count()
#     chartDet['ft_employee']=Attendance.query.filter(Attendance.branch=='FT',Attendance.inTime != None, Attendance.outTime == None).count()


#     return jsonify (chartDet)


# @views.route('get_chart')
# @login_required
# def get_chart():
#     chartDet={
#         'total_present':[],
#         'kkl_employee':[],
#         'dr_employee':[],
#         'ft_employee':[],
#     }
#     current_date=datetime.now()
#     today = current_date.strftime('%Y-%m-%d')
#     chartDet['total_present'] = Attendance.query.filter(Attendance.inTime != None, Attendance.outTime == None).all()
#     # chartDet['total_present']=len(attendance)
#     chartDet['kkl_employee']=Attendance.query.filter(Attendance.branch=='KKL',Attendance.inTime != None, Attendance.outTime == None).all()
#     chartDet['dr_employee']=Attendance.query.filter(Attendance.branch=='DR',Attendance.inTime != None, Attendance.outTime == None).all()
#     chartDet['ft_employee']=Attendance.query.filter(Attendance.branch=='FT',Attendance.inTime != None, Attendance.outTime == None).all()

#     return jsonify (chartDet)

@views.route('get_chart')
@login_required
def get_chart():
    chartDet = {
        'total_present': [],
        'kkl_employee': [],
        'dr_employee': [],
        'ft_employee': [],
    }
    current_date = datetime.now()
    today = current_date.strftime('%Y-%m-%d')

    # Convert Attendance objects to dictionaries
    total_present_attendance = [{'emp_id': attendance.emp_id, 'name': attendance.name, 'outTime': attendance.outTime, 'branch': attendance.branch} for attendance in Attendance.query.filter(Attendance.inTime != None, Attendance.outTime == None).all()]
    kkl_employee_attendance = [{'emp_id': attendance.emp_id, 'name': attendance.name, 'outTime': attendance.outTime, 'branch': attendance.branch} for attendance in Attendance.query.filter(Attendance.branch == 'KKL', Attendance.inTime != None, Attendance.outTime == None).all()]
    dr_employee_attendance = [{'emp_id': attendance.emp_id, 'name': attendance.name, 'outTime': attendance.outTime, 'branch': attendance.branch} for attendance in Attendance.query.filter(Attendance.branch == 'DR', Attendance.inTime != None, Attendance.outTime == None).all()]
    ft_employee_attendance = [{'emp_id': attendance.emp_id, 'name': attendance.name, 'outTime': attendance.outTime, 'branch': attendance.branch} for attendance in Attendance.query.filter(Attendance.branch == 'FT', Attendance.inTime != None, Attendance.outTime == None).all()]

    # Assign the converted dictionaries to the chartDet dictionary
    chartDet['total_present'] = total_present_attendance
    chartDet['kkl_employee'] = kkl_employee_attendance
    chartDet['dr_employee'] = dr_employee_attendance
    chartDet['ft_employee'] = ft_employee_attendance

    return jsonify(chartDet)



@views.route('/start',methods =['POST',"GET"])
@login_required
def start():
    create_dummy_attendance() 
    scheduler = BackgroundScheduler()
    shifts=Shift_time.query.all()
    print("\n\n\n\n\n\n\n\n\n\n\n\n",shifts)
    # scheduler.add_job(create_dummy_attendance, trigger='interval', seconds=10)
    try:
        scheduler.add_job(fetch_and_store_data, trigger='interval', seconds=10)
    except Exception as e:
        print('background scheduler error' ,e)
        
    for shift in shifts:
        shift_time = shift.shiftIntime
        hour = shift_time.hour
        print("\n\n\n\n\n\n\n\n\n\n",hour)
        scheduler.add_job(call_fun, trigger='cron', hour=hour, minute='15')

    scheduler.start()
    return redirect('/')

def call_fun():
    out_time_reminder_email()
    out_time_reminder_message()

@views.route('/createXL', methods=['GET', 'POST'])
@login_required
def createFile():
    if createXL():
        return redirect(url_for('views.downloadXL'))
    else:
        return "Error creating Excel file"
    

@views.route('/downloadXL', methods=['GET', 'POST'])
@login_required
def downloadXL():
    saveFolder = current_app.config['DAY_ATTENDANCE_FOLDER']
    return send_from_directory(saveFolder, "merged_data.xlsx", as_attachment=True)

@views.route('/del_atten', methods=['GET', 'POST'])
@login_required
def del_atten():
    atten=Attendance.query.all()
    if atten:
        for atten in atten:
            db.session.delete(atten)
            db.session.commit()
    return redirect('/')

@views.route('/unfreeze',methods=['POST','GET'])
@login_required
def unfreeze():
    data=request.json
    emp_id=data.get('emp_id')
    print(emp_id)
    
    # atten=Attendance.query.filter_by(emp_id=emp_id).first()
    # print(atten.emp_id.freezed_account,'\n\n\n')
    emp=Emp_login.query.filter_by(emp_id=emp_id).first()
    if emp:
        if emp.freezed_account==True:
            emp.freezed_account=False
            db.session.commit()
            flash('Employee Unfreezed Successfully','success')
            return jsonify("Unfreezed")
        else:
            flash('Already Unfreezed')
            return jsonify("Already freezed",emp_id)

    else:
        flash('Employee Not exists')
        return jsonify("Employee Not exists",emp_id)

@views.route('/searchEmployee',methods=['POST'])
@login_required
def searchEmployee():
    data=request.json
    print(data)
    emp_id=data['emp_id']
    startDate=data['startDate']
    endDate=data['endDate']
    
    empData={
        'emp_id' :emp_id,
        'name' :'',
        'gender':'',
        'present':0,
        'absent':0, 
        'wrongShift':0, 
        'halfDay':0, 
        'weekOff':0, 
        'wop':0, 
        'holiday':0, 
        'hp':0, 
        'callDuty':0, 
        'leave':0, 
        'rest':0
    }

    if startDate and endDate:
        last_month_attendance = session_sqlite.query(Attendance).filter(Attendance.date.between(startDate, endDate), Attendance.emp_id==emp_id).all()
    else:
        last_month_attendance = session_sqlite.query(Attendance).filter_by(emp_id=emp_id).all()
    empData['gender']=Emp_login.query.filter_by(emp_id=emp_id).first().gender
    empData['name']=Emp_login.query.filter_by(emp_id=emp_id).first().name
    empData['present'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Present'])
    empData['absent'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Absent'])
    empData['wrongShift'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Wrong Shift'])
    empData['halfDay'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Half day'])
    empData['weekOff'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Week Off'])
    empData['wop'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Wop'])
    empData['holiday'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Holiday'])
    empData['hp'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Hp'])
    empData['callDuty'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Call Duty'])
    empData['leave'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Leave'])
    empData['rest'] = len([attendance for attendance in last_month_attendance if attendance.attendance == 'Rest'])


    return jsonify(empData)