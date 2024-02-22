from datetime import datetime, timedelta,time
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app as app
from flask import  flash,redirect,session
from .models import Attendance, Shift_time, Emp_login,Festival,late,leave,Week_off,comp_off,call_duty
from . import db
from os import path
import sched
from twilio.rest import Client
import schedule
import time
from sqlalchemy import text 
from email.mime.text import MIMEText
from twilio.base.exceptions import TwilioRestException
from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import aliased
from .task import *
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import mysql_engine,sqlite_engine
from sqlalchemy.ext.automap import automap_base
from flask import current_app
import sqlite3
scheduler = sched.scheduler(time.time, time.sleep)


def send_mail(email, subject, body):
    sender_email = "kklimited1013@gmail.com"
    receiver_email = email
    password = "hmupzeoeftrbzmkl"  # Use an App Password or enable Less Secure Apps

    # Create the email message
    message = MIMEText(body)
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print('Email sent successfully!')
        server.quit()
    except Exception as e:
        print(f'An error occurred: {str(e)}')

def send_sms(numbers_to_message, message_body):
    account_sid = 'ACb1f8718e01bcc3eacf727272ff3a7b2b'
    auth_token = '85b55f99ddcbb7a7721fd612022de3a8'
    client = Client(account_sid, auth_token)

    from_phone_number = '+12069666359'

    # Ensure numbers_to_message is iterable
    if not isinstance(numbers_to_message, (list, tuple)):
        numbers_to_message = [numbers_to_message]

    for number in numbers_to_message:
        try:
            # Validate and format the phone number
            formatted_number = validate_and_format_phone_number(number)

            # Send the SMS using the formatted number
            message = client.messages.create(
                from_=from_phone_number,
                body=message_body,
                to=formatted_number
            )

            print(f"Message SID for {formatted_number}: {message.sid}")

        except TwilioRestException as e:
            print(f"Twilio error: {e}")

def validate_and_format_phone_number(phone_number):
    
    phone_number=str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+91' + phone_number
        print("phone_number:",phone_number)

    return phone_number
    
def update_or_add_shift(shift_type, in_time, out_time):
    existing_shift = Shift_time.query.filter_by(shiftType=shift_type).first()
    print("update_or_add_shift")
    
  
    if existing_shift:
        # Update existing shift
        existing_shift.shiftIntime = in_time
        existing_shift.shift_Outtime = out_time
        print("Shift updated")
        return db.session.commit()
       
    else:
        # Add new shift
        new_shift = Shift_time(
            shiftIntime=in_time,
            shift_Outtime=out_time,
            shiftType=shift_type,
        )
        db.session.add(new_shift)
        

        print("New shift added")
        return db.session.commit()
    
def read_weekoff(file_path):
    print("Prestn",file_path)
    if os.path.exists(file_path):
        print(True)
        sheet_names = pd.ExcelFile(file_path).sheet_names

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
              
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
              
            else:
                print("Unsupported file format")
                return  # Handle unsupported format

            for index, row in df.iterrows():
                print("str(row['empid']):",row['empid'], "str(row['weekoff']):", str(row['weekoff']))
                emp_id = str(row['empid'])
                week_off = str(row['weekoff'])
                new_week_off = Week_off(
                    emp_id=emp_id,
                date=week_off
                        )
                db.session.add(new_week_off)
            db.session.commit()

def process_excel_data(file_path):
    if os.path.exists(file_path):
        sheet_names = pd.ExcelFile(file_path).sheet_names

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl', skiprows=1)
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd', skiprows=1)
            else:
                print("Unsupported file format")
                return  # Handle unsupported format

            for index, row in df.iterrows():
                shift_type = row['Shift']
                in_time_str = row['S. InTime']
                out_time_str = row['S. OutTime']

                in_time = datetime.strptime(in_time_str, '%H:%M:%S').time()
                out_time = datetime.strptime(out_time_str, '%H:%M:%S').time()
            
                print("Processing: ", shift_type)

                

                update_or_add_shift(shift_type, in_time, out_time)

def calculate_Attendance(chunk_size=100):
    with app.app_context():
        total_employees = Emp_login.query.count()
        total_chunks = (total_employees + chunk_size - 1) // chunk_size

        for chunk_index in range(total_chunks):
            employees = Emp_login.query.offset(chunk_index * chunk_size).limit(chunk_size).all()
            for employee in employees:
                attendance_records = Attendance.query.filter_by(emp_id=employee.id).all()

                for attendance in attendance_records:
                    # print(attendance.employee.shift)
                    shift = Shift_time.query.filter_by(shiftType=attendance.employee.shift).first()
                    if attendance.inTime=='-':
                        inTime='-'
                    else:
                        attend_date=attendance.date.date()

                        inTime = datetime.combine(attend_date, (datetime.strptime(attendance.inTime, '%d-%m-%Y %H:%M').time()))
                        # inTime = datetime.strptime(attendance.date + ' ' + attendance.inTime, '%Y-%m-%d %H:%M:%S')

                    if attendance.outTime =='-':
                        outTime='-'
                    else:
                        attend_date=attendance.date.date()
                        outTime = datetime.combine(attend_date, (datetime.strptime(attendance.outTime, '%d-%m-%Y %H:%M').time()))

                    
                    # shiftIntime = datetime.strptime(shift.shiftIntime,'%H:%M:%S').time()
                    # shiftOuttime = datetime.strptime(shift.shift_Outtime,'%H:%M:%S').time()
                    # shiftIntime = datetime.combine(datetime.today(), shiftIntime)
                    # shiftOuttime = datetime.combine(datetime.today(), shiftOuttime)

                    
                    if inTime!='-':
                        lateBy = calculate_time_difference(shift.shiftIntime, inTime)
                        # late = calculate_time_difference('22:00', '06:01')  # sin , in
                        # late_time = datetime.strptime(lateBy, '%H:%M:%S').time()
                        if lateBy>mytime(8, 0):
                            lateBy=None
                        print(lateBy)
                    else:
                        attendance.lateBy=None
                    
                    if inTime!=None:
                        lateBy_str=attendance.lateBy
                        print(lateBy)
                        hours, minutes,seconds = map(int, lateBy_str.split(':'))
                        # print(hours * 60 + minutes >10)
                        if (hours * 60 + minutes >10):
                            attendance.attendance='Half day'


                    if outTime != None:

                        earlyGoingBy = calculate_time_difference(outTime , shift.shiftOuttime)  # out , sout
                        if earlyGoingBy>time(8, 0, 0):
                            earlyGoingBy=None

                        time_worked = calculate_time_difference(inTime, outTime)
                        if "-" in str(time_worked):
                            attendance.TotalDuration = None
                        else:
                            attendance.TotalDuration = time_worked

                        overtime_hours = calculate_time_difference(shift.shiftOuttime, outTime)
                        attendance.overtime = overtime_hours
                    else:
                        # out_time = datetime.now().strftime("%H:%M")
                        # if out_time != "00:00": 
                            # earlyGoingBy = calculate_time_difference(out_time, shiftOuttime)
                        attendance.overtime = None
                        # attendance.earlyGoingBy = earlyGoingBy
                        attendance.earlyGoingBy = None
                        # attendance.TotalDuration = calculate_time_difference_with_dates(inTime, out_time)
                        attendance.TotalDuration = None
                
        return db.session.commit()

def calculate_time_difference(time1, time2):
    # Convert time objects to strings
    time1_str = time1.strftime('%H:%M:%S')
    time2_str = time2.strftime('%H:%M:%S')

    # Convert time strings to datetime objects (without seconds)
    time1_obj = datetime.strptime(time1_str, '%H:%M:%S').time
    time2_obj = datetime.strptime(time2_str, '%H:%M:%S').time

    # Convert time objects to seconds
    seconds1 = time1_obj.hour * 3600 + time1_obj.minute * 60
    seconds2 = time2_obj.hour * 3600 + time2_obj.minute * 60

    # Calculate the difference in seconds
    difference_seconds = abs(seconds2 - seconds1)

    # Convert seconds to hours and minutes
    total_minutes = difference_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60

    # Format the difference as a time object
    formatted_difference = time(hour=int(total_hours), minute=int(minutes))
    print('\n\n\n\n\n\n\n\n\n\n\n',formatted_difference)

    return formatted_difference

# def calculate_time_difference(time1, time2):

#     # Convert time strings to datetime objects (without seconds)
#     time_format = '%H:%M:%S'

#     # seconds1 = time1.hour * 3600 + time1.minute * 60 + time1.second
#     # seconds2 = time2.hour * 3600 + time2.minute * 60 + time2.second
#     # difference_seconds = abs(seconds2 - seconds1)
#     time1 = datetime.strptime(str(time1), time_format).time()
#     time2 = datetime.strptime(str(time2), time_format).time()
#     seconds1 = time1.hour * 3600 + time1.minute * 60
#     seconds2 = time2.hour * 3600 + time2.minute * 60

#     # Calculate the difference in seconds
#     difference_seconds = abs(seconds2 - seconds1)

#     # Convert seconds to hours and minutes
#     total_minutes = difference_seconds // 60
#     total_hours = total_minutes // 60
#     minutes = total_minutes % 60

#     # Format the difference as a time object
#     formatted_difference = time(hour=int(total_hours), minute=int(minutes))

#     # format_time1 = datetime.combine(datetime.min, time1)
#     # format_time2 = datetime.combine(datetime.min, time2)
#     # print('\n\n\n\n\n\n\n\ndatetime 2 ',format_time2 - format_time1)

#     # total_minutes = (format_time2 - format_time1).total_seconds()//60


#     # Convert seconds to hours and minutes
#     # total_minutes = time_difference_seconds // 60

#     # total_hours = total_minutes // 60
#     # minutes = total_minutes % 60

#     # formatted_difference = f"{int(total_hours)}:{int(minutes):02d}"
#     # formatted_difference=datetime.strptime(formatted_difference,'%H:%M')
#     return (formatted_difference)  

def update_wages_for_present_employees():
    
    current_date = datetime.datetime.now().date()

  
    employees = Emp_login.query.filter_by(role='employee').all()

    for employee in employees:
        
        attendance_for_today = Attendance.query.filter_by(emp_id=employee.id, date=current_date).first()

        if attendance_for_today and attendance_for_today.attendance == 'present':
            # If the employee is present, increase the wages_per_Day by 1 for that day
            employee.wages_per_Day = str(int(employee.wages_per_Day) + 1)

   
    return db.session.commit()

def update_wages_for_present_daily_workers():
    
    current_date = datetime.datetime.now().date()

  
    employees = Emp_login.query.filter_by(role='daily').all()

    for employee in employees:
        
        attendance_for_today = Attendance.query.filter_by(emp_id=employee.id, date=current_date).first()

        if attendance_for_today and attendance_for_today.attendance == 'present':
            # If the employee is present, increase the wages_per_Day by 1 for that day
            employee.wages_per_Day = str(int(employee.wages_per_Day) + 1)

   
    return db.session.commit()


    # Calculate the time until the next Sunday
    now = datetime.now()
    days_until_sunday = (6 - now.weekday()) % 7  # Sunday is 6 in the Python datetime weekday representation
    next_sunday = now + timedelta(days=days_until_sunday)

    # Schedule the function to run on the next Sunday at midnight (00:00:00)
    next_sunday_midnight = datetime(next_sunday.year, next_sunday.month, next_sunday.day)
    scheduler.enterabs(time.mktime(next_sunday_midnight.timetuple()), 1, run_for_all_employees, ())

def shiftypdate():
    employees = Emp_login.query.all()  # Fetch all employees
    
    for employee in employees:
        attendance_count = len(employee.attendances)
        print(f"Employee ID: {employee.id}, Attendance Count: {attendance_count}")
        
        if attendance_count % 2 == 0:
            shifts = ['8G', '8A', '8C', '8B', 'GS', '12A', '12B', '10A', 'WO']
            current_shift_index = shifts.index(employee.shift)
            new_shift_index = (current_shift_index + 1) % len(shifts)
            employee.shift = shifts[new_shift_index]
            db.session.commit()
    
    return len(employees)  

def attend_excel_data(file_path):
    print('Attending Excel Data')
    if os.path.exists(file_path):
        sheet_names = pd.ExcelFile(file_path).sheet_names

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
            else:
                print("Unsupported file format")
                return  # Handle unsupported format

            for index, row in df.iterrows():
                empid = row['emp_id']
                print("Processing: ", empid)

                
                
                emp = db.session.query(Emp_login).filter_by(emp_id=empid).first()
                #print(emp)
                shift_times = Shift_time.query.all()
                current_time = datetime.now().time()
                current_date = datetime.now().date()
                # = None
                for shift in shift_times:
                        # shift_start_time = datetime.strptime(%H:%M:%S,'%H:%M:%S').time()
                        # shift_end_time = datetime.strptime(shift.shift_Outtime,'%H:%M:%S').time()
                        shift_start_time=shift.shiftIntime.strftime('%H:%M:%S')
                        shift_end_time=shift.shift_Outtime.strftime('%H:%M:%S')
                        if shift_start_time <= current_time <= shift_end_time:
                            current_shift = shift.shiftType
                            break
                #print(current_shift,":current_shift")
                
                shift_type = emp.shift
                #print("shift_type:",shift_type)
                shitfTime = Shift_time.query.filter_by(shiftType=emp.shift).first()
                #print("shitfTime:",shitfTime)
                
                today_date = datetime.now().strftime("%d.%m.%Y")
                #print("today_date",today_date)
                is_holiday = Festival.query.filter(Festival.date == today_date).first()
                #print(is_holiday,"is_holiday")
                
                week_off = Week_off.query.filter_by(emp_id=empid, date=today_date).order_by(Week_off.date.desc()).first()
                print(week_off)
                if is_holiday:
                    attendance_status = 'Holiday'
                else:
                    if str(row['intime']) == "-":
                        leave_check = db.session.query(leave).filter_by(emp_id=empid,date=today_date, status='Approved').first()
                        late_check = db.session.query(late).filter_by(emp_id=empid,date=today_date, status='Approved').first()

                        if leave_check or late_check:
                            attendance_status = 'Leave'
                        elif week_off:
                            attendance_status='Week Off'
                        else:
                            # if emp.branch=='FT':
                                # check_ft(today_date,empid)
                            c_off=comp_off.query.filter_by(emp_id=empid).first()
                            if c_off:
                                attendance_status='C Off'
                                db.session.delete(c_off)
                                db.session.commit()
                            else:
                                check_leave(today_date,empid)
                                attendance_status = 'Absent'
                    else:
                        if current_shift != emp.shift:
                            attendance_status='Wrong Shift'
                        elif week_off:
                            attendance_status='Wop'
                            new_req=comp_off(emp_id=empid,date=today_date)                        
                            db.session.add(new_req)
                            db.session.commit()
                        else:
                            attendance_status = 'Present'   

                branch=Emp_login.query.filter_by(emp_id=empid).first().branch

                intime=row['intime']
                outtime=row['outtime']

            
                # print("attendance_status",attendance_status)
                attendance = Attendance(
                    emp_id=empid,
                    name=emp.name,
                    inTime=intime,
                    outTime=outtime,
                    branch=branch,
                    shiftType=shift_type,
                    attendance=attendance_status,
                    shiftIntime=shitfTime.shiftIntime,
                    shift_Outtime=shitfTime.shift_Outtime,
                )
                db.session.add(attendance)
                update_freeze_status_and_remove_absences(empid)
        db.session.commit()
    else:
        print("File not found")

def update_freeze_status_and_remove_absences(emp_id):
    try:
        
        emp = Emp_login.query.filter_by(emp_id=emp_id).first()


        thirty_days_ago = datetime.now() - timedelta(days=30)
        absent_records = Attendance.query.filter_by(emp_id=emp_id, attendance='Absent').filter(Attendance.date >= thirty_days_ago).all()

        # print(f"Employee ID: {emp_id}")
        # print(f"Absent Records: {len(absent_records)}")

        
        if len(absent_records) >= 1:
            emp.freezed_account = True
            # print("Updating freeze status...")
        else:
            emp.freezed_account = False
            # print("the employee freeze has been removed")

        db.session.commit()
        return f"Success: Freeze status updated and attendance records deleted for employee {emp_id}."

    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def delete_all_employees():
    try:
        db.session.query(Attendance).delete()
        db.session.commit()
        print("All employee data deleted successfully.")
    except Exception as e:
        db.session.rollback()
        print("An error occurred:", str(e))
        
def read_excel_data(file_path, sheet_name=None):
    if sheet_name:
        return pd.read_excel(file_path, sheet_name, engine='openpyxl')
    else:
        return pd.read_excel(file_path, engine='openpyxl')

def read_csv_data(file_path):
    return pd.read_csv(file_path)

def add_employee(file_path):
    try:
        if os.path.exists(file_path):
            _, file_extension = os.path.splitext(file_path)

            if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
                sheet_names = pd.ExcelFile(file_path).sheet_names
            elif file_extension.lower() == '.csv':
                sheet_names = [None]  # For CSV, we don't need sheet names
            else:
                raise ValueError("Unsupported file format")

            data_to_insert = []

            for sheet_name in sheet_names:
                if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
                    df = read_excel_data(file_path, sheet_name)
                elif file_extension.lower() == '.csv':
                    df = read_csv_data(file_path)
                else:
                    raise ValueError("Unsupported file format")

                for index, row in df.iterrows():
                    emp_id = row['emp_id']
                    print("Processing: ", emp_id)
                    

                    existing_emp = db.session.query(Emp_login).filter_by(id=emp_id).first()
                    if not existing_emp:
                        data_to_insert.append({
                            'emp_id': emp_id,
                            'name': row['name'],
                            'role': row['designation'],
                            'email': row['email'],
                            'phoneNumber': row['phoneNumber'],
                            'shift': row['shift'],
                            'branch': row['branch'],
                            'gender':row['gender'],
                            'password':generate_password_hash("lol")
                        })
                    else:
                        print(f"Employee with ID {emp_id} already exists. Updating instead of inserting.")
                        
                        # Update existing record if needed
                        existing_emp.name = row['name']
                        existing_emp.role = row['designation']
                        existing_emp.email = row['email']
                        existing_emp.phoneNumber = row['phoneNumber']
                        existing_emp.shift = row['shift']
                        existing_emp.gender=row['gender']
                        existing_emp.password=generate_password_hash("lol")


            if data_to_insert:
                with db.session.begin_nested():
                    db.session.bulk_insert_mappings(Emp_login, data_to_insert)
                    db.session.commit()
                print("Data added successfully.")
                
            else:
                print("No new data to add.")
            
            db.session.commit()  # Commit the main transaction
        else:
            print("File not found")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()  # Rollback changes in case of an exception

def up_festival(file_path):
    try:
        # print('done')
        # Check if the file exists and is valid
        if not os.path.exists(file_path):
            flash("File does not exist", "error")
            return
        # with db.session.begin():
        #     if db.session.query(Festival):
        #         db.session.query(Festival).delete()
        db.session.commit()
        with db.session.begin():
            # Delete all records from the Festival table
            db.session.query(Festival).delete()
        
        
        # print('done 1')
        sheet_names = pd.ExcelFile(file_path).sheet_names

        # Use a context manager for database operations
        

        # print('done 2')

        # Iterate through each sheet in the Excel file
        for sheet_name in sheet_names:
            df = None
            # Read data from the Excel file based on the file extension
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
            else:
                raise ValueError("Unsupported file format. Only .xlsx and .xls files are supported.")
            print(df)
            # Iterate through rows in the DataFrame and add records to the Festival table
            for index, row in df.iterrows():
                try:
                    # print(row['Public Holidays'])
                    add_festival = Festival(
                        holiday=row['Public Holidays'],
                        date=row['Date'],
                    )
                    db.session.add(add_festival)
                except Exception as e:
                    # Handle specific errors or print more information for debugging
                    print(f"Error adding festival at index {index}: {str(e)}")
            # print('done 3')

                # Commit the changes to the database
        db.session.commit()
        flash("Festivals added successfully", category="success")
    except Exception as e:
        print("festival upload error",e)
        flash(f"Error adding festivals: {str(e)}", category="error")

def check_send_sms(emp_id):
    emp = Emp_login.query.filter_by(emp_id=emp_id).first()
    
    if emp:
        Phonenum = emp.phoneNumber
        email = emp.email
        sub='Miss punch'
        message = f"""
        Dear {emp.name}:
        It is a gentle reminder to you,
        You have missed to keep the punch in the biometric machine
        """
        print("Phone number:", Phonenum)
        send_mail(email=email, body=message,subject=sub)
        send_sms(Phonenum ,message)

def check_date_format(date):
    str(date).replace('/','-')
    str(date).replace('.','-')
    # print(date.date())
check_date_format('2022/12/02 12:20:00')

def month_attendance():
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
        record_date=record.date.date().day
        # print(str(record_date)[:10])
        date.add(record_date)
        
        # If emp_id is not in t8e dictionary, create a new list for that emp_id
        if emp_id not in employee_data:
            employee_data[emp_id] = []
        
        # Append the record to the list for that emp_id
        employee_data[emp_id].append(record)

        # print(employee_data[emp_id])
        # print(date)
    date = list(date)
    return [employee_data,date]
    #return render_template('month_attendance.html', employee_data=employee_data,date=date)

def get_last_month_dates():
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month, today

def check_leave(date_str, emp_id):
    date = datetime.strptime(date_str, "%d.%m.%Y").date()
    previous_date = date - timedelta(days=1)
    previous_previous_date = previous_date - timedelta(days=1)

    previous_date_attend = Attendance.query.filter_by(emp_id=emp_id, date=previous_date).first()
    previous_previous_date_attend = Attendance.query.filter_by(emp_id=emp_id, date=previous_previous_date).first()

    if previous_date_attend and (previous_date_attend.attendance == 'Holiday' or previous_date_attend.attendance == 'Week Off'):
        if previous_previous_date_attend and previous_previous_date_attend.attendance == 'Leave':
            previous_date_attend.attendance = 'Leave'
            db.session.commit()

def createXL():
    try:
        saveFolder = current_app.config['DAY_ATTENDANCE_FOLDER']
        
        # Connect to the SQLite database
        sqlite_file = 'app/database.db'
        conn = sqlite3.connect(sqlite_file)
        
        # Read data from the 'call_duty' table
        call_duty_df = pd.read_sql_query("SELECT * FROM call_duty", conn)
        
        # Read data from the 'Attendance' table
        attendance_df = pd.read_sql_query("SELECT * FROM Attendance", conn)
        
        # Merge the dataframes with a left join to keep all rows from 'attendance_df'
        merged_df = pd.merge(attendance_df, call_duty_df, on='emp_id', how='left', suffixes=('_attendance', '_call_duty'))
        
        # Save the merged dataframe to Excel
        merged_df.to_excel(os.path.join(saveFolder, "merged_data.xlsx"), index=False)
        
        return True  # Return True if the file creation is successful
    except Exception as e:
        error_message = "Error creating Excel file: {}".format(str(e))
        print(error_message)
        return False  # Return False if an error occurs during file creation


Base = automap_base()
Base.prepare(mysql_engine, reflect=True)

# Define MySQL model
MySQLAttendance = Base.classes.Attendance

SessionSQLite = sessionmaker(bind=sqlite_engine)
session_sqlite = SessionSQLite()

from sqlalchemy.orm import Session
def fetch_and_store_data():
    
        SessionMySQL = sessionmaker(bind=mysql_engine)
        SessionSQLite = sessionmaker(bind=sqlite_engine)
        try:
            current_date = datetime.now().date()
            # current_date = (datetime.now() - timedelta(days=1)).date()
            # print("n\n\n\n\n\n\current date:", current_date)
            session_mysql = SessionMySQL()
            session_sqlite = SessionSQLite()

            mysql_data = session_mysql.query(MySQLAttendance).filter(
                (func.date(MySQLAttendance.time) == current_date)
            ).all()

            print(mysql_data)

            for record in mysql_data:
                
                existing_record = session_sqlite.query(Attendance).filter(
                    and_(Attendance.emp_id == record.emp_id, func.date(Attendance.inTime) == current_date)
                ).first()
                    
                

                if not existing_record:
                    # print('\n\n\n\n\n akjbcsbdv \n\n\n\n\n')
                    emp = session_sqlite.query(Emp_login).filter_by(emp_id=record.emp_id).first()
                    print("\n\n\n\n\n\n ",emp.emp_id,'\n\n\n\n')
                    # emp=Emp_login.query.filter_by(emp_id=record.emp_id).first()
                    # print('\n\n\n\n\n akjbcsbdv \n\n\n\n\n')
                    shiftTime = session_sqlite.query(Shift_time).filter_by(shiftType=emp.shift).first()
                    
                    # shiftTime=Shift_time.query.filter_by(shiftType=emp.shiftType).first()
                    print('\n\n\n\n\n akjbcsbdv \n\n\n\n\n')
                    # First instance, update inTime
                    sqlite_record = Attendance(
                        emp_id=record.emp_id,
                        name=emp.name,
                        branch=emp.branch,
                        shiftType=emp.shift,
                        shiftIntime=shiftTime.shiftIntime,
                        shift_Outtime=shiftTime.shift_Outtime,
                        inTime=record.time,
                        outTime=None,
                    )
                    session_sqlite.add(sqlite_record)
                    session_sqlite.commit()
                    print('\n\n\n\n',sqlite_record.id)
                    calculate_Attendance_from_db(sqlite_record.id)

                else:
                    if existing_record.inTime!=record.time:
                    # If inTime is already set, update outTime
                        existing_record.outTime = record.time
                        session_sqlite.add(existing_record)
                        session_sqlite.commit()
                        calculate_Attendance_from_db(existing_record.id)

            session_mysql.close()

            session_sqlite.close()

        except Exception as e:
            print("Exception:", e)

# def calculate_Attendance_from_db(id):
#     with app.app_context():
#         try:
#             attendance = Attendance.query.filter_by(id=id).first()
#             shift = Shift_time.query.filter_by(shiftType=attendance.employee.shift).first()
#             if attendance.inTime == '-':
#                 inTime = '-'
#             else:
#                 attend_date = attendance.date.date()
#                 inTime = datetime.combine(attend_date, (datetime.strptime(attendance.inTime, '%d-%m-%Y %H:%M').time()))
                
#             if attendance.outTime == '-':
#                 outTime = '-'
#             else:
#                 attend_date = attendance.date.date()
#                 outTime = datetime.combine(attend_date, (datetime.strptime(attendance.outTime, '%d-%m-%Y %H:%M').time()))
                
#             if inTime != '-':
#                 lateBy = calculate_time_difference(shift.shiftIntime, inTime)
#                 if lateBy > mytime(8, 0):
#                     lateBy = None
#                 print(lateBy)
#             else:
#                 attendance.lateBy = None
                
#             if inTime is not None:
#                 lateBy_str = attendance.lateBy
#                 print(lateBy)
#                 hours, minutes, seconds = map(int, lateBy_str.split(':'))
#                 if (hours * 60 + minutes > 10):
#                     attendance.attendance = 'Half day'
                    
#             if outTime is not None:
#                 earlyGoingBy = calculate_time_difference(outTime, shift.shiftOuttime)
#                 if earlyGoingBy > time(8, 0, 0):
#                     earlyGoingBy = None
#                 time_worked = calculate_time_difference(inTime, outTime)
#                 if "-" in str(time_worked):
#                     attendance.TotalDuration = None
#                 else:
#                     attendance.TotalDuration = time_worked
#                 overtime_hours = calculate_time_difference(shift.shiftOuttime, outTime)
#                 attendance.overtime = overtime_hours
#             else:
#                 attendance.overtime = None
#                 attendance.earlyGoingBy = None
#                 attendance.TotalDuration = None
                
#             db.session.commit()
            
#         except Exception as e:
#             print("Exception:", e)


def calculate_Attendance_from_db(id):
    try:
        attendance = session_sqlite.query(Attendance).filter_by(id=id).first()
        shift = session_sqlite.query(Shift_time).filter_by(shiftType=attendance.shiftType).first()
        inTime=attendance.inTime
        print('\n\n\n\n\n\nintime :',inTime)
        outTime=attendance.outTime
        print('\n\n\n\n\n\nintime :',outTime)

        if inTime != None:
            lateBy = calculate_time_difference(shift.shiftIntime, inTime.time())
            if lateBy > mytime(8, 0):
                lateBy = None
            print('\n\n\n\n\nlate: ',lateBy)
        else:
            attendance.lateBy = None

        if inTime is not None:
            lateBy_str = attendance.lateBy
            print('\n\n\n\n\nlate: ',lateBy)

            hours, minutes, seconds = map(int, lateBy_str.split(':'))
            if (hours * 60 + minutes > 10):
                attendance.attendance = 'Half day'

        if outTime is not None:
            earlyGoingBy = calculate_time_difference(outTime.time(), shift.shift_Outtime)
            if earlyGoingBy > time(8, 0, 0):
                earlyGoingBy = None
            time_worked = calculate_time_difference(inTime.time(), outTime.time())
            if "-" in str(time_worked):
                attendance.TotalDuration = None
            else:
                attendance.TotalDuration = time_worked
            overtime_hours = calculate_time_difference(shift.shift_Outtime, outTime.time())
            attendance.overtime = overtime_hours
        else:
            attendance.overtime = None
            attendance.earlyGoingBy = None
            attendance.TotalDuration = None

        session_sqlite.commit()


    except Exception as e:
        print("Exception:", e)