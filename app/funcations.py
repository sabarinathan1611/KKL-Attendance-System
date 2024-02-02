from datetime import datetime, timedelta
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app as app
from flask import  flash,redirect,session
from .models import Attendance, Shift_time, Emp_login,Festival,late,leave,Week_off
from . import db
from os import path
import datetime
import sched
from twilio.rest import Client
import schedule
import time
from datetime import datetime, timedelta
from sqlalchemy import text 
from email.mime.text import MIMEText
from twilio.base.exceptions import TwilioRestException
from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import aliased
from .task import *
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
    # Assuming phone_number is a string
    # Validate and format the phone number if necessary
    # Add the country code if missing

    # Example: Assuming Indian country code is +91
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
                shift_type = str(row['Shift'])
                in_time = str(row['S. InTime'])
                out_time = str(row['S. OutTime'])
            
                print("Processing: ", shift_type)

                

                update_or_add_shift(shift_type, in_time, out_time)


def calculate_Attendance(chunk_size=100):
    total_employees = Emp_login.query.count()
    total_chunks = (total_employees + chunk_size - 1) // chunk_size

    for chunk_index in range(total_chunks):
        employees = Emp_login.query.offset(chunk_index * chunk_size).limit(chunk_size).all()
        for employee in employees:
            attendance_records = Attendance.query.filter_by(emp_id=employee.id).all()

            for attendance in attendance_records:
                print(attendance.employee.shift)
                # Extract attendance information
                shift = Shift_time.query.filter_by(shiftType=attendance.employee.shift).first()
                inTime = attendance.inTime
                shiftIntime = shift.shiftIntime
                shiftOuttime = shift.shift_Outtime

                # Calculate the lateBy time
                lateBy = calculate_time_difference(shiftIntime, inTime)
                attendance.lateBy = lateBy

                if attendance.outTime != "00:00":
                    outTime = attendance.outTime

                    # Calculate the earlyGoingBy time
                    earlyGoingBy = calculate_time_difference(outTime, shiftOuttime)
                    if "-" in earlyGoingBy:
                        attendance.earlyGoingBy = "00:00"
                    else:
                        attendance.earlyGoingBy = earlyGoingBy

                    # Calculate the time duration between inTime and outTime
                    time_worked = calculate_time_difference(inTime, outTime)
                    if "-" in time_worked:
                        attendance.TotalDuration = "00:00"
                    else:
                        attendance.TotalDuration = time_worked

                    # Calculate the overtime hours
                    overtime_hours = calculate_time_difference(shiftOuttime, outTime)
                    attendance.overtime = overtime_hours
                else:
                    out_time = datetime.now().strftime("%H:%M")
                    if out_time != "00:00":  # Check for "00:00" here
                        earlyGoingBy = calculate_time_difference(out_time, shiftOuttime)
                        attendance.earlyGoingBy = earlyGoingBy
                        attendance.TotalDuration = calculate_time_difference(inTime, out_time)
                        attendance.overtime = "00:00"
            
            # Commit the changes for each attendance record
            db.session.commit()

def calculate_time_difference(time1_str, time2_str):
    #print("DEBUG - time1_str:", time1_str)
    #print("DEBUG - time2_str:", time2_str)

    # Convert time strings to datetime objects (without seconds)
    time_format = '%H:%M'
    
    try:
        if time1_str == "00:00" or time2_str == "00:00":
            return "00:00"
            
        time1 = datetime.strptime(time1_str, time_format)
        time2 = datetime.strptime(time2_str, time_format)
    except ValueError as e:
        #print("ValueError:", e)
        return "00:00"

    # Calculate time difference in seconds
    time_difference_seconds = (time2 - time1).total_seconds()

    # Convert seconds to hours and minutes
    total_minutes = time_difference_seconds // 60

    if total_minutes < 0:
        total_minutes += 24 * 60

    total_hours = total_minutes // 60
    minutes = total_minutes % 60

    formatted_difference = f"{int(total_hours)}:{int(minutes):02d}"
    return formatted_difference
    
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
    
# def schedule_function(emp_id):
#     schedule.every(2).days.at("00:00").do(count_attendance_and_update_shift, emp_id)



# while schedule.get_jobs():
#     schedule.run_pending()
#     time.sleep(1)


 


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
    
# def count_attendance_and_update_shift_periodic(emp_id):
#     # Replace employee_id_to_check with the actual employee ID you want to check
#     attendance_count = count_attendance_and_update_shift(emp_id)
#     print(f"Attendance Count for Employee ID {emp_id}: {attendance_count}")



# def run_for_all_employees():
    # Assuming Employee is your SQLAlchemy model for employees
    # employees = Employee.query.filter_by(workType='employee').all()

    # for employee in employees:
    #     count_attendance_and_update_shift_periodic(employee.id)





# def attend_excel_data(file_path):
#     if os.path.exists(file_path):
#         sheet_names = pd.ExcelFile(file_path).sheet_names

#         for sheet_name in sheet_names:
#             df = None
#             if file_path.lower().endswith('.xlsx'):
#                 df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
#             elif file_path.lower().endswith('.xls'):
#                 df = pd.read_excel(file_path, sheet_name, engine='xlrd')
#             else:
#                 print("Unsupported file format")
#                 return  # Handle unsupported format

#             for index, row in df.iterrows():
#                 empid = row['emp_id']
#                 print("Processing: ", empid)
#                 date=pd.to_datetime(row['date']) if pd.notna(row['date']) else None
#                 existing_emp = db.session.query(Employee).filter_by(id=empid).first()
#                 if  existing_emp:
                    
#                     if str(row['intime']) =="00:00" and str(row['outtime'])== "00:00":
                            
#                             existing_emp.emp_id=empid,
#                             existing_emp.inTime=str(row['intime']),
#                             existing_emp.shift_Outtime=str(row['outtime']),
#                             existing_emp.shiftType=existing_emp.attendances.shift,
#                             existing_emp.attendance='Absent',
#                             existing_emp.date=date
                        
                        
#                     else:
                                      
#                             existing_emp.emp_id=empid,
#                             existing_emp.inTime=str(row['intime']),
#                             existing_emp.shift_Outtime=str(row['outtime']),
#                             existing_emp.shiftType=existing_emp.attendances.shift,
#                             existing_emp.attendance='Present',
#                             existing_emp.date=date
                        
                       
                        

      
#     else:
#         print("File not found")
        
def process_csv_file(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row

        for row in csv_reader:
            employee_id, employee_name, *shifts = row

            # Create a new NewShift instance and set its attributes
            new_shift_entry = Shift_time(
                name_date_day=employee_name,
                filename=file_path,
                monday=shifts[0],
                tuesday=shifts[1],
                wednesday=shifts[2],
                thursday=shifts[3],
                friday=shifts[4]
            )

            # Set the day_* attributes dynamically
            for day_num, shift in enumerate(shifts[5:], start=1):
                setattr(new_shift_entry, f"day_{day_num}", shift)

            # Add the new entry to the database session
            db.session.add(new_shift_entry)

        # Commit the changes to the database
        db.session.commit()




def attend_excel_data(file_path):
    print('hello world')
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
                print(emp)
                shift_times = Shift_time.query.all()
                current_time = datetime.now().time()
                current_date = datetime.now().date()
                current_shift = None
                for shift in shift_times:
                        shift_start_time = datetime.strptime(shift.shiftIntime, '%H:%M').time()
                        shift_end_time = datetime.strptime(shift.shift_Outtime, '%H:%M').time()
                        if shift_start_time <= current_time <= shift_end_time:
                            current_shift = shift.shiftType
                            break
                print(current_shift,":current_shift")
                
                shift_type = emp.shift
                print("shift_type:",shift_type)
                shitfTime = Shift_time.query.filter_by(shiftType=emp.shift).first()
                print("shitfTime:",shitfTime)
                # Check if today's date is a holiday
                today_date = datetime.now().strftime("%d.%m.%Y")
                print("today_date",today_date)
                is_holiday = Festival.query.filter(Festival.date == today_date).all()
                print(is_holiday,"is_holiday")
                
                week_off=Week_off.query.all()
                # festival_alias = aliased(Festival)

                # is_holiday = (
                #     db.session.query(Festival)
                #     .join(festival_alias, func.DATE(Attendance.date) == today_date)
                #     .all()
                # )
                if is_holiday:
                    attendance_status = 'Holiday'
                else:
                    # for week_off in week_off:
                    #     emp_id=week_off.emp_id
                    #     if(row['emp_id']==emp_id):
                    #         current_date = datetime.now().strftime('%Y-%m-%d')
                    #         print("current_date:",current_date)
                    #         attendance = Attendance.query.filter(func.DATE(Attendance.date) == current_date,Attendance.emp_id==emp_id).first()
                    #         print("befor :",attendance.attendance)
                    #         attendance.attendance='Wrong Shift'
                    
                    if str(row['intime']) == "-":
                        leave_check = db.session.query(leave).filter_by(emp_id=empid, status='Approved').first()
                        late_check = db.session.query(late).filter_by(emp_id=empid, status='Approved').first()
                        
                        

                        # Check if either leave or late is approved
                        if leave_check or late_check:
                            attendance_status = 'Communicated'
                        else:
                            attendance_status = 'Leave'
                    else:
                        if current_shift != emp.shift:
                            attendance_status='Wrong Shift'
                        else:
                            attendance_status = 'Present'

                    '''
                    if str(row['outtime']) == '-':
                        
                       shiftOuttime = session['lastShift']
                       shiftOuttime = datetime.strptime(shiftOuttime, "%H:%M")
                       shiftOuttime = shiftOuttime.time()
                    #    print("shift out Time",shiftOuttime)
                       #print(shiftOuttime)
                       current_time = datetime.now().time()
                       print("Current Time",current_time)
                    #    current_time_str = datetime.now().strftime("%H:%M")
                    #    if shiftOuttime > current_time + timedelta(minutes=10):
                       print("shift out Time",shiftOuttime)
                       print("current time ",(datetime.combine(datetime.today(), current_time)))
                       time_with_10_minutes_added = (datetime.combine(datetime.today(), shiftOuttime) + timedelta(minutes=5)).time()
                       print("time_with_10_minutes_added time ",time_with_10_minutes_added)
                       if current_time > time_with_10_minutes_added:
                           print("hello")
                        #    print(send_alter.apply_async(countdown=1))
                       else:
                           print("\n\n\n\nits lower in time\n\n\n")
                    else:
                        print("out time gave")
                    '''
                    
            
                print("attendance_status",attendance_status)
                attendance = Attendance(
                    emp_id=empid,
                    name=emp.name,
                    inTime=str(row['intime']),
                    outTime=str(row['outtime']),
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
        # Get the employee
        emp = Emp_login.query.filter_by(emp_id=emp_id).first()

        # Get the last 30 days absence records for the employee, including the current date
        thirty_days_ago = datetime.now() - timedelta(days=30)
        absent_records = Attendance.query.filter_by(emp_id=emp_id, attendance='Leave').filter(Attendance.date >= thirty_days_ago).all()

        print(f"Employee ID: {emp_id}")
        print(f"Absent Records: {len(absent_records)}")

        # If the employee has been continuously absent for 30 days, update freeze status and delete attendance records
        if len(absent_records) >= 1:
            emp.freezed_account = True
            print("Updating freeze status...")
        else:
            emp.freezed_account = False
            print("the employee freeze has been removed")

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
        print('done')
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
        
        
        print('done 1')
        sheet_names = pd.ExcelFile(file_path).sheet_names

        # Use a context manager for database operations
        

        print('done 2')

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
                    print(row['Public Holidays'])
                    add_festival = Festival(
                        holiday=row['Public Holidays'],
                        date=row['Date'],
                    )
                    db.session.add(add_festival)
                except Exception as e:
                    # Handle specific errors or print more information for debugging
                    print(f"Error adding festival at index {index}: {str(e)}")
            print('done 3')

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
