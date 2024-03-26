#riglet Mahaveer | lolcat
from datetime import datetime, timedelta,time
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app as app
from flask import  flash,redirect,session,redirect
from .models import Attendance, Shift_time, Emp_login,Festival,late,leave,comp_off,call_duty,NewShift
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
import logging
Base = automap_base()
Base.prepare(mysql_engine, reflect=True)
MySQLAttendance = Base.classes.attendance
SessionSQLite = sessionmaker(bind=sqlite_engine)
session_sqlite = SessionSQLite()
SessionMySQL = sessionmaker(bind=mysql_engine)
logging.getLogger('sqlalchemy.dialects.mysql').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


from sqlalchemy.orm import Session
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
    existing_shift = session_sqlite.query(Shift_time).filter_by(shiftType=shift_type).first()
    print("update_or_add_shift")
    
  
    if existing_shift:
        # Update existing shift
        existing_shift.shiftIntime = in_time
        existing_shift.shift_Outtime = out_time
        print("Shift updated")
        return session_sqlite.commit()
       
    else:
        # Add new shift
        new_shift = Shift_time(
            shiftIntime=in_time,
            shift_Outtime=out_time,
            shiftType=shift_type,
        )
        session_sqlite.add(new_shift)
        

        print("New shift added")
        return session_sqlite.commit()
    
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
                session_sqlite.add(new_week_off)
            session_sqlite.commit()

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

# def shiftypdate():
#     employees = session_sqlite.query(Emp_login).all()  # Fetch all employees
    
#     for employee in employees:
#         attendance_count = len(employee.attendances)
#         print(f"Employee ID: {employee.id}, Attendance Count: {attendance_count}")
        
#         if attendance_count % 2 == 0:
#             shifts = ['8G', '8A', '8C', '8B', 'GS', '12A', '12B', '10A', 'WO']
#             current_shift_index = shifts.index(employee.shift)
#             new_shift_index = (current_shift_index + 1) % len(shifts)
#             employee.shift = shifts[new_shift_index]
#             session_sqlite.commit()
    
#     return len(employees)  

def update_freeze_status_and_remove_absences(emp_id):
    try:
        
        emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()


        thirty_days_ago = datetime.now() - timedelta(days=30)
        absent_records = session_sqlite.query(Attendance).filter(Attendance.emp_id==emp_id, or_(Attendance.attendance=='Absent',Attendance.attendance==None)).filter(Attendance.date >= thirty_days_ago).all()
        # print(f"Employee ID: {emp_id}")
        # print(f"Absent Records: {len(absent_records)}")

        
        if len(absent_records) >= 30:
            emp.freezed_account = True
            # print("Updating freeze status...")
        else:
            emp.freezed_account = False
            # print("the employee freeze has been removed")

        session_sqlite.commit()
        return f"Success: Freeze status updated and attendance records deleted for employee {emp_id}."

    except Exception as e:
        # session_sqlite.rollback()
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def delete_all_employees():
    try:
        session_sqlite.query(Attendance).delete()
        session_sqlite.commit()
        print("All employee data deleted successfully.")
    except Exception as e:
        session_sqlite.rollback()
        print("An error occurred:", str(e))
        
def read_excel_data(file_path, sheet_name=None):
    if sheet_name:
        return pd.read_excel(file_path, sheet_name, engine='openpyxl')
    else:
        return pd.read_excel(file_path, engine='openpyxl')

def read_csv_data(file_path):
    return pd.read_csv(file_path)

def addEmpShifts(file_path):
    try:
        session_sqlite.query(NewShift).delete()
        session_sqlite.commit()
        if os.path.exists(file_path):
            
            df = pd.read_excel(file_path, engine='openpyxl', header=0)
            for index, row in df.iterrows():
                emp_id = row.iloc[0]
                shift_data = row.drop(labels=['EMPID'])
                new_shift = NewShift(emp_id=emp_id)
                for day_num, shift_type in shift_data.items():
                    setattr(new_shift, str(day_num), shift_type)
                db.session.add(new_shift)
                db.session.commit()
            session['flash_message']=['File Uploaded Successfully','success']
            
        else:
            print('File Does Not Exists')
            session['flash_message']=['File Not Exists','error']

    except Exception as e:
        session['flash_message']=['File Not Uploaded','error']
        print(f"An error occurred: {e}")
        session_sqlite.rollback() 

# def addEmpShifts(file_path):
#     try:
#         if os.path.exists(file_path):
#             _, file_extension = os.path.splitext(file_path)

#             if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
#                 sheet_names = pd.ExcelFile(file_path).sheet_names
#             elif file_extension.lower() == '.csv':
#                 sheet_names = [None]  # For CSV, we don't need sheet names
#             else:
#                 raise ValueError("Unsupported file format")

#             data_to_insert = []

#             for sheet_name in sheet_names:
#                 if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
#                     df = pd.read_excel(file_path, sheet_name)
#                 elif file_extension.lower() == '.csv':
#                     df = pd.read_csv(file_path)
#                 else:
#                     raise ValueError("Unsupported file format")

#                 # Delete all existing shifts before inserting new ones
#                 session_sqlite.query(NewShift).delete()
                
#                 for index, row in df.iterrows():
#                     emp_id = row['emp_id']
#                     print("Processing: ", emp_id)
#                     existing_emp_shift = session_sqlite.query(NewShift).filter_by(emp_id=emp_id).first()
#                     if not existing_emp_shift:
#                         new_shift_data = {'emp_id': emp_id}
#                         for column_name, shift_type in row.items():
#                             if column_name != 'emp_id':  # Skip 'emp_id' column
#                                 new_shift_data[str(column_name)] = shift_type
                        
#                         # Create a NewShift object with the new shift data
#                         new_shift = NewShift(**new_shift_data)
#                         data_to_insert.append(new_shift)
                        
#                     else:
#                         print(f"Employee with ID {emp_id} already exists. Updating instead of inserting.")
#                         for column_name, shift_type in row.items():
#                             if column_name != 'emp_id':  # Skip 'emp_id' column
#                                 setattr(existing_emp_shift, str(column_name), shift_type)
                        
#                         # Merge the changes into the session
#                         session_sqlite.merge(existing_emp_shift)

#             if data_to_insert:
#                 with session_sqlite.begin_nested():
#                     session_sqlite.bulk_insert_mappings(NewShift, data_to_insert)
#                     session_sqlite.commit()
#                 print("Data added successfully.")
#             else:
#                 print("No new data to add.")
            
#             session_sqlite.commit()  # Commit the main transaction
#         else:
#             print("File not found")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         session_sqlite.rollback()  # Rollback changes in case of an exception


# def addEmpShifts(file_path):
#     try:
#         if os.path.exists(file_path):
#             _, file_extension = os.path.splitext(file_path)

#             if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
#                 sheet_names = pd.ExcelFile(file_path).sheet_names
#             elif file_extension.lower() == '.csv':
#                 sheet_names = [None]  # For CSV, we don't need sheet names
#             else:
#                 raise ValueError("Unsupported file format")

#             data_to_insert = []

#             for sheet_name in sheet_names:
#                 if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
#                     df = pd.read_excel(file_path, sheet_name)
#                 elif file_extension.lower() == '.csv':
#                     df = pd.read_csv(file_path)
#                 else:
#                     raise ValueError("Unsupported file format")

#                 for index, row in df.iterrows():
#                     emp_id = row['emp_id']
#                     print("Processing: ", emp_id)
#                     existing_emp_shift = session_sqlite.query(NewShift).filter_by(emp_id=emp_id).first()
#                     if not existing_emp_shift:
#                         new_shift_data = {'emp_id': emp_id}
#                         for column_name, shift_type in row.items():
#                             if column_name != 'emp_id':  # Skip 'emp_id' column
#                                 new_shift_data[str(column_name)] = shift_type
                        
#                         # Create a NewShift object with the new shift data
#                         new_shift = NewShift(**new_shift_data)
#                         data_to_insert.append(new_shift)
                        
#                     else:
#                         print(f"Employee with ID {emp_id} already exists. Updating instead of inserting.")
#                         for column_name, shift_type in row.items():
#                             if column_name != 'emp_id':  # Skip 'emp_id' column
#                                 setattr(existing_emp_shift, str(column_name), shift_type)
                        
#                         # Merge the changes into the session
#                         session_sqlite.merge(existing_emp_shift)

#             if data_to_insert:
#                 with session_sqlite.begin_nested():
#                     session_sqlite.bulk_insert_mappings(NewShift, data_to_insert)
#                     session_sqlite.commit()
#                 print("Data added successfully.")
#             else:
#                 print("No new data to add.")
            
#             session_sqlite.commit()  # Commit the main transaction
#         else:
#             print("File not found")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         session_sqlite.rollback()  # Rollback changes in case of an exception


def add_employee(file_path):
    try:

        print('/n/n/n/n/n here going')
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
                    

                    existing_emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
                    if not existing_emp:
                        data_to_insert.append({
                            'emp_id': emp_id,
                            'name': row['name'],
                            'role': row['role'],
                            'email': row['email'],
                            'phoneNumber': row['phoneNumber'],
                            'aadhar':row['adharNumber'],
                            'designation':row['designation'],
                            # 'shift': row['shift'],
                            'branch': row['branch'],
                            'gender':row['gender'],
                            'password':generate_password_hash(str(row['phoneNumber']))
                        })
                    else:
                        print(f"Employee with ID {emp_id} already exists. Updating instead of inserting.")
                        
                        # Update existing record if needed
                        existing_emp.name = row['name']
                        existing_emp.role = row['role']
                        existing_emp.designation = row['designation']
                        existing_emp.aadhar = row['adharNumber'] 
                        existing_emp.branch = row['branch'] 
                        existing_emp.email = row['email']
                        existing_emp.phoneNumber = row['phoneNumber']
                        existing_emp.gender=row['gender']
                        existing_emp.password=generate_password_hash(str(row['phoneNumber']))


            if data_to_insert:
                with session_sqlite.begin_nested():
                    session_sqlite.bulk_insert_mappings(Emp_login, data_to_insert)
                    session_sqlite.commit()
                print("Data added successfully.")
                
            else:
                print("No new data to add.")
            
            session_sqlite.commit()  # Commit the main transaction
            session['flash_message']=['File Uploaded Successfully','success']

        else:
            print("File not found")
            session['flash_message']=['File Not Exists','error']

    except Exception as e:
        session['flash_message']=['File Not Uploaded','error']
        print(f"An error occurred: {e}")
        session_sqlite.rollback()  # Rollback changes in case of an exception

def up_festival(file_path):
    try:
        # print('done')
        # Check if the file exists and is valid
        if not os.path.exists(file_path):
            flash("File does not exist", "error")
            return
        # with session_sqlite.begin():
        #     if session_sqlite.query(Festival):
        #         session_sqlite.query(Festival).delete()
        with session_sqlite.begin_nested():
            # Delete all records from the Festival table
            session_sqlite.query(Festival).delete()
        
        
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
                    # date_string=row['Public Holidays']
                    # date = datetime.strptime(date_string, "%Y-%m-%d").date()
                    # print(row['Public Holidays'])
                    add_festival = Festival(
                        holiday=row['Public Holidays'],
                        date=row['Date'],
                    )
                    session_sqlite.add(add_festival)

                except Exception as e:
                    # Handle specific errors or print more information for debugging
                    print(f"Error adding festival at index {index}: {str(e)}")
            # print('done 3')

                # Commit the changes to the database
        session_sqlite.commit()
        flash("Festivals added successfully", category="success")
    except Exception as e:
        print("festival upload error",e)
        flash(f"Error adding festivals: {str(e)}", category="error")

def check_send_sms(emp_id):
    emp = session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
    
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

# def month_attendance():
#     start_date, end_date = get_current_month_dates()

#     last_month_attendance = session_sqlite.query(Attendance).filter(
#         Attendance.date.between(start_date, end_date)
#         ).order_by(Attendance.date.asc()).all()
#     for a in last_month_attendance:
#         print(a.date)
#     employee_data = {}
#     date = set()
    
#     for record in last_month_attendance:
#         emp_id = record.emp_id
#         record_date=record.date.date().day
#         date.add(record_date)
        
#         if emp_id not in employee_data:
#             employee_data[emp_id] = []
        
#         employee_data[emp_id].append(record)

#     date = sorted(list(date))
#     print(employee_data,date)
#     return [employee_data,date]

def month_attendance():
    start_date, end_date = get_current_month_dates()

    last_month_attendance = session_sqlite.query(Attendance).filter(
    Attendance.date.between(start_date, end_date)
).order_by(Attendance.emp_id.asc(), Attendance.date.asc()).all()


    employee_data = {}
    dates = set()
    
    for record in last_month_attendance:
        emp_id = record.emp_id
        record_date = record.date.date().day
        dates.add(record_date)
        
        if emp_id not in employee_data:
            employee_data[emp_id] = []
        
        employee_data[emp_id].append(record)

    dates = sorted(list(dates))
    return employee_data, dates

# def get_last_month_dates():
#     today = datetime.today()
#     first_day_of_current_month = today.replace(day=1)
#     last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
#     first_day_of_last_month = last_day_of_last_month.replace(day=1)
#     print( ' first and last \n',first_day_of_last_month, today)
#     return first_day_of_last_month, today

def get_current_month_dates():
    today = datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_current_month = first_day_of_current_month.replace(
        day=1, month=first_day_of_current_month.month + 1
    ) - timedelta(days=1)
    return first_day_of_current_month, last_day_of_current_month

def check_leave(date_str, emp_id):
    date = datetime.strptime(date_str, "%d.%m.%Y").date()
    previous_date = date - timedelta(days=1)
    previous_previous_date = previous_date - timedelta(days=1)

    previous_date_attend = session_sqlite.query(Attendance).filter_by(emp_id=emp_id, date=previous_date).first()
    previous_previous_date_attend = session_sqlite.query(Attendance).filter_by(emp_id=emp_id, date=previous_previous_date).first()

    if previous_date_attend and (previous_date_attend.attendance == 'Holiday' or previous_date_attend.attendance == 'Week Off'):
        if previous_previous_date_attend and previous_previous_date_attend.attendance == 'Leave':
            previous_date_attend.attendance = 'Leave'
            session_sqlite.commit()

# def createXL():
#     try:
#         saveFolder = current_app.config['DAY_ATTENDANCE_FOLDER']
        
#         # Connect to the SQLite database
#         sqlite_file = 'app/database.db'
#         conn = sqlite3.connect(sqlite_file)
        
#         # Read data from the 'call_duty' table
#         call_duty_df = pd.read_sql_query("SELECT * FROM call_duty", conn)
        
#         # Read data from the 'Attendance' table
#         attendance_df = pd.read_sql_query("SELECT * FROM Attendance", conn)
        
#         # Merge the dataframes with a left join to keep all rows from 'attendance_df'
#         merged_df = pd.merge(attendance_df, call_duty_df, on='emp_id', how='left', suffixes=('_attendance', '_call_duty'))
        
#         # Save the merged dataframe to Excel
#         merged_df.to_excel(os.path.join(saveFolder, "merged_data.xlsx"), index=False)
        
#         return True  # Return True if the file creation is successful
#     except Exception as e:
#         error_message = "Error creating Excel file: {}".format(str(e))
#         print(error_message)
#         return False  # Return False if an error occurs during file creation

def calculate_time_difference(time1, time2):

    seconds1 = int(time1.hour) * 3600 + int(time1.minute) * 60
    seconds2 = int(time2.hour) * 3600 + int(time2.minute) * 60
    
    difference_seconds = seconds2 - seconds1
    if '-' in str(difference_seconds):
        return None

    total_minutes = difference_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60

    time_difference=datetime(2024,1,1,total_hours,minutes,0)

    return time_difference.time()

def calculate_time_difference_total_timeduraction(time1, time2):
    time_difference = time2 - time1
    return str(time_difference)


def create_dummy_attendance():
    try:
        shift_times = session_sqlite.query(Shift_time).all()
        print(shift_times,'\n\n\n\n\n')

        current_shifts=get_current_shift()
        atten=session_sqlite.query(Attendance).filter_by(attendance=None).all()
        for atten in atten:
            if atten.shiftType not in current_shifts:
                CompOff=check_comp_off(atten.emp_id)
                if CompOff:
                    status=CompOff
                else:
                    status='Absent'
                atten.attendance=status
                session_sqlite.commit()

        date = retrieveDay(datetime.now().date())
        weekOffEmpIDs = session_sqlite.query(NewShift).filter(getattr(NewShift, str(date)) == 'OFF').all()
        weekOffEmpIDs_list = [empID.emp_id for empID in weekOffEmpIDs]
        weekOffEmp = session_sqlite.query(Emp_login).filter(Emp_login.emp_id.in_(weekOffEmpIDs_list)).all()
        for emp in weekOffEmp:
            attendance_status='Week Off'
            atten=session_sqlite.query(Attendance).filter(Attendance.emp_id==emp.emp_id,func.date(Attendance.date)==datetime.now().date()).first()
            if atten == None:
                dummy_atten = Attendance(
                        emp_id=emp.emp_id,
                        name=emp.name,
                        branch=emp.branch,
                        shiftType='Off',
                        attendance=attendance_status,
                        shiftIntime=None,
                        shift_Outtime=None,
                        inTime=None,
                        outTime=None,
                    )
                print('\n\n\n\n hello da \n\n\n\n')
                session_sqlite.add(dummy_atten)
                session_sqlite.commit()

        for current_shift in current_shifts:
            shift=session_sqlite.query(Shift_time).filter_by(shiftType=current_shift).first()
            
            print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n',current_shift)

            # Assuming retrieveDay returns the day of the month as an integer
            date = retrieveDay(datetime.now().date())

            # Query to retrieve NewShift records based on the current shift for the given date
            empIDs = session_sqlite.query(NewShift).filter(getattr(NewShift, str(date)) == current_shift).all()

            # Extracting employee IDs from empIDs
            empIDs_list = [empID.emp_id for empID in empIDs]
            

            # Query to retrieve employee information for the extracted employee IDs
            emp = session_sqlite.query(Emp_login).filter(Emp_login.emp_id.in_(empIDs_list)).all()


            for emp in emp:
                attendance_status=None
                update_freeze_status_and_remove_absences(emp.emp_id)

                # week_off = session_sqlite.query(Week_off).filter_by(emp_id=emp.emp_id, date=str(datetime.now().date())).first()
                leave_check = session_sqlite.query(leave).filter_by(emp_id=emp.emp_id,date=datetime.now().date(), status='Approved').first()
                # late_check = session_sqlite.query(late).filter_by(emp_id=emp_id,date=datetime.now().date(), status='Approved').first()
                holiday=check_holiday(datetime.now().date())
                if holiday:
                    attendance_status='Holiday'
                # elif week_off:
                #     attendance_status='Week Off'
                elif leave_check:
                    attendance_status = 'Leave'
                    if emp.branch=='FT':
                        status=check_ft(datetime.now().date(),emp.emp_id)
                        if status!=None:
                            attendance_status=status
                
                atten=session_sqlite.query(Attendance).filter(Attendance.emp_id==emp.emp_id,func.date(Attendance.date)==datetime.now().date()).first()
                # print('\n\n\n\n\n',atten,'\n\n\n\n')

                shiftIntime,shift_Outtime=check_shift(shift.shiftIntime,shift.shift_Outtime)

                if atten == None:
                            dummy_atten = Attendance(
                                    emp_id=emp.emp_id,
                                    name=emp.name,
                                    branch=emp.branch,
                                    shiftType=current_shift,
                                    attendance=attendance_status,
                                    shiftIntime=shiftIntime,
                                    shift_Outtime=shift_Outtime,
                                    inTime=None,
                                    outTime=None,
                                )
                            print('\n\n\n\n hello da \n\n\n\n')
                            session_sqlite.add(dummy_atten)
                            session_sqlite.commit()
                else:
                            print('\n\n\n\n\n\n',atten)
    except Exception as e:
        session['flash_message']=[e,'error']


def check_holiday(curr_date):
    is_holiday = session_sqlite.query(Festival).filter_by(date = str(curr_date)).first()
    print('\n\n\nHoliday checkup' ,curr_date)
    if is_holiday:
        print(is_holiday)
        return True
    else:
        return False

def check_shift(shiftIntime,shiftOuttime):
    print('inTime : ',shiftIntime)
    print('outTime : ',shiftOuttime)
    if shiftIntime>shiftOuttime:
        shiftIntime = datetime.combine(datetime.now().date(), shiftIntime)
        shiftOuttime = datetime.combine((datetime.now().date()+timedelta(days=1)), shiftOuttime)
    else:
        shiftIntime = datetime.combine(datetime.now().date(), shiftIntime)
        shiftOuttime = datetime.combine(datetime.now().date(), shiftOuttime)

    print('inTime : ',shiftIntime)
    print('outTime : ',shiftOuttime)


    return shiftIntime,shiftOuttime

def fetch_and_store_data():
    
    try:
            # create_dummy_attendance()
            # current_date = datetime.now().date()-timedelta(days=1)
            current_date = datetime.now().date()
            session_mysql = SessionMySQL()
            yesterday_date=current_date - timedelta(days=1)
            # print('\n\n\n\nyesterday date da',yesterday_date)
            

            mysql_data = session_mysql.query(MySQLAttendance).filter(
                (func.date(MySQLAttendance.time) == current_date)
            ).all()

            # print(mysql_data)

            for record in mysql_data:

                # emp=session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first()
                # if emp.freezed_account==1:
                #     emp.freezed_account==0
                #     session_sqlite.commit()
                try:
                    existing_record = session_sqlite.query(Attendance).filter(
                        and_(Attendance.emp_id == record.emp_id, func.date(Attendance.date) == current_date)
                    ).first() 

                    yesterday_atten=session_sqlite.query(Attendance).filter(
                        and_(Attendance.emp_id == record.emp_id, func.date(Attendance.date) == yesterday_date,Attendance.inTime!=None ,or_(
                Attendance.outTime == None,
                Attendance.outTime == record.time
            ))).first()
                    emp = session_sqlite.query(Emp_login).filter_by(emp_id=record.emp_id).first()
                    current_shifts=get_current_shift()
                    emp_shift=getShiftDet(datetime.now().date(),record.emp_id)
                    if yesterday_atten:
                        if yesterday_atten.outTime!=record.time:
                            print(yesterday_atten , '\n\n\n\n\n')
                            yesterday_atten.outTime=record.time
                            session_sqlite.commit()
                            print('\n\n\n\n\n\n\n\n ulla podhu 1 ',yesterday_atten.id)
                            calculate_Attendance_from_db(yesterday_atten.id)
                        
                    elif not existing_record:
                        emp_id=record.emp_id
                        # week_off = session_sqlite.query(Week_off).filter_by(emp_id=emp_id, date=str(datetime.now().date())).first()
                        shift_for_emp=session_sqlite.query(Shift_time).filter_by(shiftType=emp_shift).first()

                        time_diff=calculate_time_difference(record.time,shift_for_emp.shift_Outtime)
                        if emp_shift not in current_shifts:
                            attendance_status='Wrong Shift'
                        elif ((time_diff.hour*3600)+(time_diff.minute*60)+(time_diff.second))<7200:
                            attendance_status='Present'
                        elif check_holiday(datetime.now().date()):
                            attendance_status = 'Hp'
                        elif getShiftDet(datetime.now().date(),emp_id)=='OFF':
                            new_comp_off=comp_off(emp.emp_id,str(datetime.now()))
                            session_sqlite.add(new_comp_off)
                            session_sqlite.commit()
                            attendance_status = 'Wop'
                        else:
                            attendance_status = 'Present'
                        # print('\n\nok with 947\n\n')
                        if emp.branch=='FT':
                            status=check_ft(emp_id,current_date)
                            if status=='Week Off':
                                new_comp_off=comp_off(emp.emp_id,str(datetime.now()))
                                session_sqlite.add(new_comp_off)
                                session_sqlite.commit()
                                attendance_status='Wop'
                        # print('\n\nok with 952\n\n')

                        # emp_shift=session_sqlite.query(Emp_login).filter_by(emp_id=emp_id).first().shift
                        shift_time=session_sqlite.query(Shift_time).filter_by(shiftType=emp_shift).first()
                        
                        shiftIntime,shift_Outtime=check_shift(shift_time.shiftIntime,shift_time.shift_Outtime)
                            

                        sqlite_record = Attendance(
                                        emp_id=record.emp_id,
                                        name=emp.name,
                                        branch=emp.branch,
                                        attendance=attendance_status,
                                        shiftType=emp_shift,
                                        shiftIntime=shiftIntime,
                                        shift_Outtime=shift_Outtime,
                                        inTime=record.time,
                                        outTime=None,
                                    )
                        session_sqlite.add(sqlite_record)
                        session_sqlite.commit()
                        inserted_id = sqlite_record.id
                        print('\n\n\n\n\n\n\n\n ulla podhu 2 ',inserted_id)
                        calculate_Attendance_from_db(inserted_id)
                        
                    else:
                        if existing_record.inTime==None:
                            existing_record.inTime=record.time
                            attendance_status = 'Present'
                            if getShiftDet(datetime.now().date(),existing_record.emp_id)=='OFF':
                                new_comp_off=comp_off(emp.emp_id,str(datetime.now()))
                                session_sqlite.add(new_comp_off)
                                session_sqlite.commit()
                                attendance_status = 'Wop'
                            elif emp_shift not in current_shifts:
                                attendance_status='Wrong Shift'
                            if emp.branch=='FT':
                                status=check_ft(emp.emp_id,current_date)
                                if status=='Week Off':
                                    new_comp_off=comp_off(emp.emp_id,str(datetime.now()))
                                    session_sqlite.add(new_comp_off)
                                    session_sqlite.commit()
                                    attendance_status='Wop'
                                elif emp_shift not in current_shifts:
                                    attendance_status='Wrong Shift'
                            if check_holiday(datetime.now().date()):
                                attendance_status = 'Hp'
                            existing_record.attendance=attendance_status
                            session_sqlite.commit()
                            print('\n\n\n\n\n\n\n\n ulla podhu 3 ',existing_record.id)
                            calculate_Attendance_from_db(existing_record.id)

                        elif existing_record.inTime!=record.time and existing_record.outTime!=record.time:
                                    print('\n\n\n\n\n\n\n\n ulla podhu 4',existing_record.id)
                                    existing_record.outTime = record.time
                                    session_sqlite.commit()
                                    calculate_Attendance_from_db(existing_record.id)
                except Exception as e:
                    print(e)
                finally:
                    session_sqlite.close()

    except Exception as e:
            print("Exception:/n/n", e)

    
    
    return redirect('/')


def calculate_Attendance_from_db(id):
    try:
            attendance = session_sqlite.query(Attendance).filter_by(id=id).first()
            inTime=attendance.inTime
            outTime=attendance.outTime

            if inTime != None:
                lateBy = calculate_time_difference(attendance.shiftIntime, inTime)
            else:
                attendance.lateBy = None
            attendance.lateBy=lateBy

            if lateBy != None:
                lateBy_str = str(lateBy)
                # print('\n\n\n\n\nlate: ',lateBy)


                hours, minutes, seconds = map(int, lateBy_str.split(':'))
                if (hours * 60 + minutes > 10):
                    attendance.attendance = 'Half day'

            if outTime is not None:
                if outTime ==datetime(1,1,1,0,0,0):
                    outTime=attendance.shift_Outtime
                attendance.earlyGoingBy = calculate_time_difference(outTime, attendance.shift_Outtime)
                time_worked = calculate_time_difference_total_timeduraction(inTime, outTime)
                attendance.TotalDuration = time_worked
                
                overtime_hours = calculate_time_difference(attendance.shift_Outtime, outTime)
                attendance.overtime = overtime_hours
            else:
                attendance.overtime = None
                attendance.earlyGoingBy = None
                attendance.TotalDuration = None
            # print('attendance.lateBy',attendance.lateBy)
            # print('attendance.overtime',attendance.overtime)
            # print('attendance.earlyGoingBy',attendance.earlyGoingBy)
            # print('attendance.TotalDuration',attendance.TotalDuration)

            session_sqlite.commit()
            # session_sqlite.close()


    except Exception as e:
            print("Exception:", e)

def check_comp_off(emp_id):
    compOff = session_sqlite.query(comp_off).filter_by(emp_id=emp_id,flag=False).first()
    if compOff:
        compOff.flag=True
        session_sqlite.commit()
        return 'C Off'
    else:
        return None

def check_ft(today_date, emp_id):
    today_date=datetime.now().date()
    yesterday_date = today_date - timedelta(days=1)
    two_before_date = today_date - timedelta(days=2)
    three_before_date = today_date - timedelta(days=3)
    four_before_date = today_date - timedelta(days=4)
    # print('\n\n\n yesterday date here',today_date,yesterday_date)

    yesterday_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=yesterday_date).first()
    if yesterday_attend and (yesterday_attend.attendance=='Present' or yesterday_attend.attendance=='Half day' ):
        two_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=two_before_date).first()
        if two_before_attend and (two_before_attend.attendance=='Present' or two_before_attend.attendance=='Half day'):
            two_before_attend_s_continue=session_sqlite.query(comp_off).filter_by(emp_id=emp_id,date=two_before_attend)
            yesterday_attend_s_continue=session_sqlite.query(comp_off).filter_by(emp_id=emp_id,date=yesterday_attend)
            if two_before_attend_s_continue or yesterday_attend_s_continue:
                if two_before_attend_s_continue:
                    session_sqlite.delete(two_before_attend_s_continue)
                if yesterday_attend_s_continue:
                    session_sqlite.delete(yesterday_attend_s_continue)
                session_sqlite.commit()
                three_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=three_before_date).first()
                if three_before_attend.attendance=='Week Off':
                    return 'Rest'
                elif four_before_attend.attendance=='Rest':
                    return 'Week Off'
            three_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=three_before_date).first()
            if three_before_attend and (three_before_attend.attendance=='Present' or three_before_attend.attendance=='Half day'):    
                four_before_attend=session_sqlite.query(Attendance).filter_by(emp_id=emp_id,date=four_before_date).first()
                if four_before_attend.attendance and four_before_attend.attendance=='Week Off':
                    return 'Rest'
                elif four_before_attend.attendance=='Rest':
                    return 'Week Off'
                
    # print('eng dhan problem')
    return None 

def get_current_shift():
    now = datetime.now().time()
    # now=datetime(2024,2,2,5,0,0).time()
    # print(now)
    # current_time = datetime.strptime(now.strftime('%H:%M:%S'), '%H:%M:%S').time()
    shift_times = session_sqlite.query(Shift_time).all()
    shifts=[]
    for shift in shift_times:
        start=shift.shiftIntime
        end=shift.shift_Outtime
        
        if start < end:
            if start <= now < end:
                print(start , '<', now , '<', end)
                shifts.append(shift.shiftType)
        else: # Over midnight
            if start <= now or now < end:
                print(start , '<', now , '<', end)
                shifts.append(shift.shiftType)
    # print(shifts,'\n\n\n\n\n\n')
    return shifts
            

def out_time_reminder_email():
    todaydate = datetime.now().date()
    yesterday = (datetime.now() - timedelta(days=1)).date()

    last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == todaydate) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()
    yesterday_last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == yesterday) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()

    # print("\n\n\n\n\n\n\n\ninside the code")
    # print(last_shift)
    # print(yesterday_last_shift)

    if last_shift:
        for i in last_shift:
            emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
            print("\n\n\n\n\n\n\n\n\nemailid",emailid)
            if emailid:
                email = emailid.email
                subject = "Out Time Missing"
                body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                send_mail(email, subject, body)

    if yesterday_last_shift:
        for i in yesterday_last_shift:
            emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
            print("\n\n\n\n\n\n\n\n\nemailid",emailid)
            if emailid:
                email = emailid.email
                subject = "Out Time Missing"
                body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                send_mail(email, subject, body)

def out_time_reminder_message():
    todaydate = datetime.now().date()
    yesterday = (datetime.now() - timedelta(days=1)).date()

    last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == todaydate) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()
    yesterday_last_shift = session_sqlite.query(Attendance).filter((func.DATE(Attendance.date) == yesterday) & (Attendance.inTime != None) & (Attendance.outTime == None)).all()

    # print("\n\n\n\n\n\n\n\ninside the code")
    # print(last_shift)
    # print(yesterday_last_shift)

    if last_shift:
        for i in last_shift:
            number = []
            emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
            # print("\n\n\n\n\n\n\n\n\nemailid",emailid)
            if emailid:
                try:
                    number.append(emailid.phoneNumber)
                    message_body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                    send_sms(number, message_body)
                except:
                    print('exception sending sms')

    if yesterday_last_shift:
        number = []
        for i in yesterday_last_shift:
            emailid = session_sqlite.query(Emp_login).filter_by(emp_id=i.emp_id).first()
            # print("\n\n\n\n\n\n\n\n\nemailid",emailid)
            if emailid:
                number.append(emailid.phoneNumber)
                message_body = f"Dear Employee,\n\nYour out time is missing for today's shift. Please make sure to record your out time before leaving the premises.\n\nBest regards,\nKanchi Karpooram Limited"
                # print("list of numbers ",number)
                send_sms(number, message_body)
                
def createXL():
    try:
        saveFolder = current_app.config['DAY_ATTENDANCE_FOLDER']
        
        # Connect to the SQLite database
        sqlite_file = 'app/database.db'
        conn = sqlite3.connect(sqlite_file)
        
        # Get today's date
        today_date = datetime.now().date()
        
        # Read data from the 'call_duty' table
        call_duty_df = pd.read_sql_query("SELECT * FROM call_duty WHERE DATE(date) = ?", conn, params=(today_date,))
        
        # Read data from the 'Attendance' table
        attendance_df = pd.read_sql_query("SELECT * FROM Attendance WHERE DATE(date) = ?", conn, params=(today_date,))
        
        # Merge the dataframes with a left join to keep all rows from 'attendance_df'
        merged_df = pd.merge(attendance_df, call_duty_df, on='emp_id', how='left', suffixes=('_attendance', '_call_duty'))
        
        # Save the merged dataframe to Excel
        merged_df.to_excel(os.path.join(saveFolder, "merged_data.xlsx"), index=False)
        
        return True  # Return True if the file creation is successful
    except Exception as e:
        error_message = "Error creating Excel file: {}".format(str(e))
        return False
    

def retrieveDay(date):
    day = str(date.day)  
    if day.startswith('0'):  
        day = day[1:]  
    return day 


def getShiftDet(date,emp_id):
    day=retrieveDay(date)

    shiftData=session_sqlite.query(NewShift).filter(NewShift.emp_id==emp_id).first()
    if shiftData:
        shift=getattr(shiftData,str(day))
        return shift
    else:
        print('Shift Not Found')
        return None

def delete_session():
    if 'flash_message' in session:
        session.pop('flash_message')