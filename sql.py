import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import sqlite3
from config import Config

class LTADataFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_bus_routes(self):
        api_url = 'http://datamall2.mytransport.sg/ltaodataservice/BusRoutes'
        all_bus_routes = []
        skip = 0
        while True:
            headers = {
                'AccountKey': self.api_key,
                'accept': 'application/json'
            }

            params = {
                '$skip': skip
            }

            try:
                response = requests.get(api_url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                if 'value' in data:
                    all_bus_routes.extend(data['value'])
                    if len(data['value']) < 500:
                        break
                    print(f"Retrieved data with $skip={skip}")
                else:
                    break
            except requests.exceptions.RequestException as e:
                print(f"An error occurred while fetching bus routes: {e}")
                return []
            except ValueError as e:
                print(f"Failed to parse the JSON response for bus routes: {e}")
                return []

            skip += 500

        return all_bus_routes

    def get_bus_services(self):
        api_url = "http://datamall2.mytransport.sg/ltaodataservice/BusServices"
        all_bus_services = []
        skip = 0
        while True:
            headers = {
                "AccountKey": self.api_key,
                "accept": "application/json"
            }

            params = {
                "$skip": skip
            }

            response = requests.get(api_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if "value" in data:
                    all_bus_services.extend(data["value"])
                    if len(data["value"]) < 500:
                        break
                    print(f"Retrieved data with $skip={skip}")
                else:
                    break
            else:
                raise Exception(f"Failed to fetch data from the API. Status code: {response.status_code}")

            skip += 500

        return all_bus_services

    def get_bus_stops(self):
        api_url = "http://datamall2.mytransport.sg/ltaodataservice/BusStops"
        all_bus_stops = []
        skip = 0
        while True:
            headers = {
                "AccountKey": self.api_key,
                "accept": "application/json"
            }

            params = {
                "$skip": skip
            }

            response = requests.get(api_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if "value" in data:
                    all_bus_stops.extend(data["value"])
                    if len(data["value"]) < 500:
                        break
                    print(f"Retrieved data with $skip={skip}")
                else:
                    break
            else:
                raise Exception(f"Failed to fetch data from the API. Status code: {response.status_code}")

            skip += 500

        return all_bus_stops


class PublicTransportDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def begin_transaction(self):
        self.conn.isolation_level = None  # Set to autocommit mode (default is DEFERRED)
        self.conn.execute('BEGIN TRANSACTION')

    def commit_transaction(self):
        self.conn.execute('COMMIT')
        self.conn.isolation_level = ''  # Set back to default (DEFERRED)

    def rollback_transaction(self):
        self.conn.execute('ROLLBACK')
        self.conn.isolation_level = ''  # Set back to default (DEFERRED)

    def create_tables(self):
        # Create the necessary tables in the database
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS BusRoutes (
                RouteID INTEGER PRIMARY KEY AUTOINCREMENT,
                ServiceNo VARCHAR(255),
                Operator TEXT, 
                Direction INT, 
                StopSequence INT, 
                BusStopCode INT, 
                Distance FLOAT, 
                WD_FirstBus TIME, 
                WD_LastBus TIME, 
                SAT_FirstBus TIME, 
                SAT_LastBus TIME, 
                SUN_FirstBus TIME, 
                SUN_LastBus TIME,
                FOREIGN KEY (BusStopCode) REFERENCES BusStops(BusStopCode),
                FOREIGN KEY (ServiceNo) REFERENCES BusServices(ServiceNo)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS BusServices (
                ServiceNo VARCHAR PRIMARY KEY , 
                Operator TEXT, 
                Direction INT, 
                Category VARCHAR(255),
                Origincode INT, 
                DestinationCode INT, 
                AM_Peak_Freq INT, 
                AM_Offpeak_Freq INT, 
                PM_Peak_Freq INT, 
                PM_Offpeak_Freq INT, 
                LoopDesc TEXT
            )
        ''')

        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS BusStops (
                        BusStopCode INTEGER PRIMARY KEY,
                        RoadName TEXT,
                        Description TEXT,
                        Latitude REAL,
                        Longitude REAL
                    )
                ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FavoriteStop (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                BusStopCode INT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FavoriteService (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ServiceNo INT
            )
        ''')

        self.conn.commit()

    def check_bus_route_exists(self, ServiceNo, BusStopCode):
        # Check if a bus route with the given ServiceNo and BusStopCode already exists in the database
        self.cursor.execute("SELECT 1 FROM BusRoutes WHERE ServiceNo = ? AND BusStopCode = ?", (ServiceNo, BusStopCode))
        return self.cursor.fetchone() is not None

    def insert_bus_route(self, ServiceNo, Operator, Direction, StopSequence, BusStopCode, Distance,
                         WD_FirstBus, WD_LastBus, SAT_FirstBus, SAT_LastBus, SUN_FirstBus, SUN_LastBus):
        self.begin_transaction()
        try:
            # Insert bus routes into the database if they don't exist
            if not self.check_bus_route_exists(ServiceNo, BusStopCode):
                self.cursor.execute('''
                    INSERT INTO BusRoutes (ServiceNo, Operator, Direction, StopSequence, BusStopCode, Distance, 
                    WD_FirstBus, WD_LastBus, SAT_FirstBus, SAT_LastBus, SUN_FirstBus, SUN_LastBus)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ServiceNo, Operator, Direction, StopSequence, BusStopCode, Distance,
                      WD_FirstBus, WD_LastBus, SAT_FirstBus, SAT_LastBus, SUN_FirstBus, SUN_LastBus))
            self.commit_transaction()
        except Exception as e:
            # Rollback the transaction in case of an exception
            print(f"An error occurred while inserting bus route: {e}")
            self.rollback_transaction()

    def check_bus_service_exists(self, ServiceNo):
        # Check if a bus service with the given ServiceNo already exists in the database
        self.cursor.execute("SELECT 1 FROM BusServices WHERE ServiceNo = ?", (ServiceNo,))
        return self.cursor.fetchone() is not None

    def insert_bus_service(self, ServiceNo, Operator, Direction, Category, OriginCode, DestinationCode,
                           AM_Peak_Freq, AM_Offpeak_Freq, PM_Peak_Freq, PM_Offpeak_Freq, LoopDesc):
        self.begin_transaction()
        try:
            # Insert bus services into the database if they don't exist
            if not self.check_bus_service_exists(ServiceNo):
                self.cursor.execute('''
                    INSERT INTO BusServices (ServiceNo, Operator, Direction, Category, OriginCode, DestinationCode, 
                    AM_Peak_Freq, AM_Offpeak_Freq, PM_Peak_Freq, PM_Offpeak_Freq, LoopDesc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ServiceNo, Operator, Direction, Category, OriginCode, DestinationCode,
                      AM_Peak_Freq, AM_Offpeak_Freq, PM_Peak_Freq, PM_Offpeak_Freq, LoopDesc))
            self.commit_transaction()
        except Exception as e:
            # Rollback the transaction in case of an exception
            print(f"An error occurred while inserting bus service: {e}")
            self.rollback_transaction()

    def check_bus_stop_exists(self, BusStopCode):
        # Check if a bus stop with the given BusStopCode already exists in the database
        self.cursor.execute("SELECT 1 FROM BusStops WHERE BusStopCode = ?", (BusStopCode,))
        return self.cursor.fetchone() is not None

    def insert_bus_stop(self, BusStopCode, RoadName, Description, Latitude, Longitude):
        self.begin_transaction()
        try:
            # Insert bus stops into the database if they don't exist
            if not self.check_bus_stop_exists(BusStopCode):
                self.cursor.execute('''
                    INSERT INTO BusStops (BusStopCode, RoadName, Description, Latitude, Longitude)
                    VALUES (?, ?, ?, ?, ?)
                ''', (BusStopCode, RoadName, Description, Latitude, Longitude))
            self.commit_transaction()
        except Exception as e:
            # Rollback the transaction in case of an exception
            print(f"An error occurred while inserting bus stop: {e}")
            self.rollback_transaction()


############### helper ###############
def retrieve_and_insert_data(data_fetcher, db, category):
    if category == "BusStops":
        bus_stop_data = data_fetcher.get_bus_stops()
        for stop in bus_stop_data:
            db.insert_bus_stop(stop['BusStopCode'], stop['RoadName'], stop['Description'], stop['Latitude'],
                               stop['Longitude'])
        print(f"Bus stops retrieved from the API and inserted into the database.")

    elif category == "BusServices":
        bus_services_data = data_fetcher.get_bus_services()
        for service in bus_services_data:
            db.insert_bus_service(service['ServiceNo'], service['Operator'], service['Direction'], service['Category'],
                                  service['OriginCode'], service['DestinationCode'], service['AM_Peak_Freq'],
                                  service['AM_Offpeak_Freq'], service['PM_Peak_Freq'], service['PM_Offpeak_Freq'],
                                  service['LoopDesc'])
        print(f"Bus services retrieved from the API and inserted into the database.")

    elif category == "BusRoutes":
        bus_routes_data = data_fetcher.get_bus_routes()
        for route in bus_routes_data:
            db.insert_bus_route(route['ServiceNo'], route['Operator'], route['Direction'],
                                route['StopSequence'], route['BusStopCode'], route['Distance'],
                                route['WD_FirstBus'], route['WD_LastBus'], route['SAT_FirstBus'],
                                route['SAT_LastBus'], route['SUN_FirstBus'], route['SUN_LastBus'])
        print(f"Bus routes retrieved from the API and inserted into the database.")


def retrieve_data_from_database(db, category, treeview):
    # Clear the existing TreeView items
    for item in treeview.get_children():
        treeview.delete(item)

    # Hard-coded column names for the TreeView widget
    bus_routes_columns = [
        "ServiceNo", "Operator", "Direction", "StopSequence", "BusStopCode", "Distance",
        "WD_FirstBus", "WD_LastBus", "SAT_FirstBus", "SAT_LastBus", "SUN_FirstBus", "SUN_LastBus"
    ]

    bus_services_columns = [
        "ServiceNo", "Operator", "Direction", "Category", "OriginCode", "DestinationCode",
        "AM_Peak_Freq", "AM_Offpeak_Freq", "PM_Peak_Freq", "PM_Offpeak_Freq", "LoopDesc"
    ]

    bus_stops_columns = [
        "BusStopCode", "RoadName", "Description", "Latitude", "Longitude"
    ]

    columns = {
        "BusStops": bus_stops_columns,
        "BusServices": bus_services_columns,
        "BusRoutes": bus_routes_columns,
    }

    selected_columns = columns.get(category, [])

    # Create a mapping of column names to integer indices
    column_mapping = {col: i for i, col in enumerate(selected_columns)}

    # Configure the TreeView headings based on the selected category
    for col in selected_columns:
        try:
            treeview.heading(column_mapping[col], text=col)
            treeview.column(column_mapping[col], width=100)
        except tk.TclError as e:
            print(f"Error configuring heading for column {col}: {e}")

    # Retrieve data from the database based on the selected category
    query = f"SELECT * FROM {category.capitalize()}"
    db.cursor.execute(query)
    data = db.cursor.fetchall()

    # Display the data in the TreeView
    for row in data:
        treeview.insert("", "end", values=row)


def sort_treeview_column(treeview, col, reverse=False):
    # Retrieve the data from the TreeView
    data = [(treeview.set(child, col), child) for child in treeview.get_children('')]

    # Sort the data in-place
    data.sort(reverse=reverse)

    # Rearrange items in the TreeView based on the sorted data
    for index, (value, child) in enumerate(data):
        treeview.move(child, '', index)


def sort_column_wrapper(treeview, col):
    # Get the current sorting order for the specified column
    current_order = column_sort_orders.get(col, None)

    if current_order is None or current_order == 'asc':
        # If current order is not set or ascending, toggle to descending
        reverse = True
        column_sort_orders[col] = 'desc'
    else:
        # If current order is descending, toggle to ascending
        reverse = False
        column_sort_orders[col] = 'asc'

    # Update the heading command to the new sorting order for the specified column
    treeview.heading(col, command=lambda c=col: sort_column_wrapper(treeview, c))

    # Sort the TreeView column for the specified column
    sort_treeview_column(treeview, col, reverse)


# Dictionary to store the sorting order for each column
column_sort_orders = {}


def filter_treeview_data(treeview, category, filter_column, filter_value):
    # Clear the existing TreeView items
    for item in treeview.get_children():
        treeview.delete(item)

    # Hard-coded column names for the TreeView widget
    bus_routes_columns = [
        "ServiceNo", "Operator", "Direction", "StopSequence", "BusStopCode", "Distance",
        "WD_FirstBus", "WD_LastBus", "SAT_FirstBus", "SAT_LastBus", "SUN_FirstBus", "SUN_LastBus"
    ]

    bus_services_columns = [
        "ServiceNo", "Operator", "Direction", "Category", "OriginCode", "DestinationCode",
        "AM_Peak_Freq", "AM_Offpeak_Freq", "PM_Peak_Freq", "PM_Offpeak_Freq", "LoopDesc"
    ]

    bus_stops_columns = [
        "BusStopCode", "RoadName", "Description", "Latitude", "Longitude"
    ]

    columns = {
        "BuStops": bus_stops_columns,
        "BusServices": bus_services_columns,
        "BusRoutes": bus_routes_columns,
    }

    selected_columns = columns.get(category, [])

    # Create a mapping of column names to integer indices
    column_mapping = {col: i for i, col in enumerate(selected_columns)}

    # Configure the TreeView headings based on the selected category
    for col in selected_columns:
        try:
            treeview.heading(column_mapping[col], text=col)
            treeview.column(column_mapping[col], width=100)
        except tk.TclError as e:
            print(f"Error configuring heading for column {col}: {e}")

    # Construct SQL query for filtering based on the specified column and value
    query = f"SELECT * FROM {category.capitalize()} WHERE {filter_column} = ?"

    # Execute the SQL query with the filter value
    db.cursor.execute(query, (filter_value,))
    data = db.cursor.fetchall()

    # Display the filtered data in the TreeView
    for row in data:
        treeview.insert("", "end", values=row)


def select_specific_bus_stop(db, bus_stop_code):
    db.cursor.execute("SELECT * FROM BusStops WHERE BusStopCode = ?", (bus_stop_code,))
    bus_stop = db.cursor.fetchone()
    if bus_stop:
        result = f"Bus Stop Details:\n"
        result += f"Bus Stop Code: {bus_stop[0]}\n"
        result += f"Road Name: {bus_stop[1]}\n"
        result += f"Description: {bus_stop[2]}\n"
        result += f"Latitude: {bus_stop[3]}\n"
        result += f"Longitude: {bus_stop[4]}\n"
    else:
        result = f"Bus Stop with the specified code was not found in the database."

    return result  # Return the result as a string


def select_bus_service(db, service_no):
    # Query the database for the specific bus service
    db.cursor.execute("SELECT * FROM BusServices WHERE ServiceNo = ?", (service_no,))
    service = db.cursor.fetchone()
    if service:
        result = f"Bus Service Details:\n"
        result += f"Service Number: {service[0]}\n"
        result += f"Operator: {service[1]}\n"
        result += f"Direction: {service[2]}\n"
        result += f"Category: {service[3]}\n"
        result += f"Origin Code: {service[4]}\n"
        result += f"Destination Code: {service[5]}\n"
        result += f"AM Peak Frequency: {service[6]}\n"
        result += f"AM Off-Peak Frequency: {service[7]}\n"
        result += f"PM Peak Frequency: {service[8]}\n"
        result += f"PM Off-Peak Frequency: {service[9]}\n"
        result += f"Loop Description: {service[10]}\n"
    else:
        result = f"Bus Service with Service Number {service_no} not found in the database."

    return result  # Return the result as a string


def is_valid_bus_stop(db, bus_stop_code):
    # Check if the bus stop exists in the database
    db.cursor.execute("SELECT 1 FROM BusStops WHERE BusStopCode = ?", (bus_stop_code,))
    return db.cursor.fetchone() is not None


def add_to_favorite_bus_stop(db, bus_stop_code):
    # Check if the bus stop is valid
    if not is_valid_bus_stop(db, bus_stop_code):
        return f"Invalid bus stop {bus_stop_code}. Unable to add to favorites."

    # Check if the bus stop is already in favorites
    db.cursor.execute("SELECT * FROM FavoriteStop WHERE BusStopCode = ?", (bus_stop_code,))
    existing_favorite = db.cursor.fetchone()

    if not existing_favorite:
        try:
            # If not, add it to favorites
            db.cursor.execute("INSERT INTO FavoriteStop (BusStopCode) VALUES (?)", (bus_stop_code,))
            db.conn.commit()  # Make sure to commit the changes to the database
            return f"Bus stop {bus_stop_code} added to favorites."
        except Exception as e:
            # Handle the exception, e.g., print an error message
            print(f"An error occurred while adding bus stop {bus_stop_code} to favorites: {e}")
            db.conn.rollback()  # Rollback the transaction in case of an error
            return f"Error adding bus stop {bus_stop_code} to favorites."
    else:
        return f"Bus stop {bus_stop_code} is already in favorites."


def is_valid_bus_service(db, service_no):
    # Check if the bus service exists in the database
    db.cursor.execute("SELECT 1 FROM BusServices WHERE ServiceNo = ?", (service_no,))
    return db.cursor.fetchone() is not None


def add_to_favorite_bus_service(db, service_no):
    # Check if the bus service is valid
    if not is_valid_bus_service(db, service_no):
        return f"Invalid bus service {service_no}. Unable to add to favorites."

    # Check if the bus service is already in favorites
    db.cursor.execute("SELECT * FROM FavoriteService WHERE ServiceNo = ?", (service_no,))
    existing_favorite = db.cursor.fetchone()

    if not existing_favorite:
        try:
            # If not, add it to favorites
            db.cursor.execute("INSERT INTO FavoriteService (ServiceNo) VALUES (?)", (service_no,))
            db.conn.commit()  # Make sure to commit the changes to the database
            return f"Bus service {service_no} added to favorites."
        except Exception as e:
            # Handle the exception, e.g., print an error message
            print(f"An error occurred while adding bus service {service_no} to favorites: {e}")
            db.conn.rollback()  # Rollback the transaction in case of an error
            return f"Error adding bus service {service_no} to favorites."
    else:
        return f"Bus service {service_no} is already in favorites."


def get_favorite_bus_stops(db):
    db.cursor.execute("SELECT * FROM FavoriteStop")
    favorite_stops = db.cursor.fetchall()
    return favorite_stops


def get_favorite_bus_services(db):
    db.cursor.execute("SELECT * FROM FavoriteService")
    favorite_services = db.cursor.fetchall()
    return favorite_services


def remove_from_favorite_bus_stop(db, bus_stop_code):
    try:
        # Remove the bus stop from favorites
        db.cursor.execute("DELETE FROM FavoriteStop WHERE BusStopCode = ?", (bus_stop_code,))
        db.conn.commit()  # Make sure to commit the changes to the database
        return f"Bus stop {bus_stop_code} removed from favorites."
    except Exception as e:
        # Handle the exception, e.g., print an error message
        print(f"An error occurred while removing bus stop {bus_stop_code} from favorites: {e}")
        db.conn.rollback()  # Rollback the transaction in case of an error
        return f"Error removing bus stop {bus_stop_code} from favorites."


def remove_from_favorite_bus_service(db, service_no):
    try:
        # Remove the bus service from favorites
        db.cursor.execute("DELETE FROM FavoriteService WHERE ServiceNo = ?", (service_no,))
        db.conn.commit()  # Make sure to commit the changes to the database
        return f"Bus service {service_no} removed from favorites."
    except Exception as e:
        # Handle the exception, e.g., print an error message
        print(f"An error occurred while removing bus service {service_no} from favorites: {e}")
        db.conn.rollback()  # Rollback the transaction in case of an error
        return f"Error removing bus service {service_no} from favorites."


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.geometry(f"{width}x{height}+{x}+{y}")


def main_menu():
    main_window = tk.Tk()
    main_window.title("Half Ryde Bot")
    main_window.geometry("400x300")  # Set the initial window size

    center_window(main_window, 400, 300)  # Center the main window

    result_label = tk.Label(main_window, text="")
    result_label.pack()

    def api_operations():
        api_window = tk.Toplevel(main_window)
        api_window.title("API Operations")
        center_window(api_window, 400, 300)  # Center the API window

        def retrieve_data(category):
            result = retrieve_and_insert_data(data_fetcher, db, category)
            result_label.config(text=f"Data retrieved and inserted for {category}")

        options = {
            "BusStops": "BusStops",
            "BusServices": "BusServices",
            "BusRoutes": "BusRoutes",
        }

        option_label = tk.Label(api_window, text="Select a category:")
        option_label.pack()

        for category, label in options.items():
            category_button = tk.Button(api_window, text=label, command=lambda cat=category: retrieve_data(cat))
            category_button.pack()

    def database_operations():
        db_window = tk.Toplevel(main_window)
        db_window.title("Database Operations")
        center_window(db_window, 1200, 500)  # Center the DB window

        # Create a TreeView widget to display the results
        columns = ("Column_1", "Column_2", "Column_3", "Column_4",
                   "Column_5", "Column_6", "Column_7", "Column_8",
                   "Column_9", "Column_10", "Column_11", "Column_12")
        treeview = ttk.Treeview(db_window, columns=columns, show="headings")
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=100)

        treeview.pack()

        def retrieve_data(category):
            # Retrieve and display the data using the TreeView widget
            retrieve_data_from_database(db, category, treeview)

        options = {
            "BusStops": "BusStops",
            "BusServices": "BusServices",
            "BusRoutes": "BusRoutes",
        }

        option_label = tk.Label(db_window, text="Select a category:")
        option_label.pack()

        for category, label in options.items():
            category_button = tk.Button(db_window, text=label, command=lambda cat=category: retrieve_data(cat))
            category_button.pack()

        # Sorting Widgets
        def sort_treeview_column(col):
            # Toggle between ascending and descending order
            current_order = treeview.heading(col)['command']
            reverse = not current_order

            # Update the heading command to the new sorting order
            treeview.heading(col, command=lambda: sort_treeview_column(col))

            # Retrieve the data from the TreeView
            data = [(treeview.set(child, col), child) for child in treeview.get_children('')]

            # Sort the data in-place
            data.sort(reverse=reverse)

            # Rearrange items in the TreeView based on the sorted data
            for index, (value, child) in enumerate(data):
                treeview.move(child, '', index)

        sort_label = tk.Label(db_window, text="Sort by column:")
        sort_label.pack(side=tk.LEFT)

        for col in columns:
            sort_button = tk.Button(db_window, text=col, command=lambda c=col: sort_treeview_column(c))
            sort_button.pack(side=tk.LEFT)

        # Filtering Widgets
        def filter_data():
            keyword = filter_entry.get()
            # Call the backend function with the filter keyword
            filter_treeview_data(treeview, category, keyword)

        filter_label = tk.Label(db_window, text="Filter by keyword:")
        filter_label.pack(side=tk.RIGHT)

        filter_entry = tk.Entry(db_window)
        filter_entry.pack(side=tk.RIGHT)

        filter_button = tk.Button(db_window, text="Filter", command=filter_data)
        filter_button.pack(side=tk.RIGHT)

    def user_selections():
        user_window = tk.Toplevel(main_window)
        user_window.title("User Selections")
        center_window(user_window, 400, 300)  # Center the User Selections window

        def select_bus_stop():
            bus_stop_window = tk.Toplevel(user_window)
            bus_stop_window.title("Select Bus Stop")
            center_window(bus_stop_window, 400, 300)  # Center the Bus Stop window

            def display_bus_stop_details():
                bus_stop_code = bus_stop_entry.get()
                result = select_specific_bus_stop(db, bus_stop_code)

                # Clear existing Text widget, if it exists
                for widget in bus_stop_window.winfo_children():
                    if isinstance(widget, tk.Text):
                        widget.destroy()

                # Create a Text widget to display multiline text
                result_text = tk.Text(bus_stop_window, height=10, width=40, state=tk.NORMAL)

                # Insert the new content
                result_text.insert(tk.END, "Bus stop details displayed:\n" + result)

                # Set the Text widget back to read-only
                result_text.configure(state=tk.DISABLED)

                result_text.pack()

            def add_to_favorites_stop():
                bus_stop_code = bus_stop_entry.get()
                result = add_to_favorite_bus_stop(db, bus_stop_code)
                messagebox.showinfo("Success, Bus stop added to favorites!", result)

            bus_stop_label = tk.Label(bus_stop_window, text="Enter Bus Stop Code:")
            bus_stop_label.pack()

            bus_stop_entry = tk.Entry(bus_stop_window)
            bus_stop_entry.pack()

            display_button = tk.Button(bus_stop_window, text="Display Bus Stop Details",
                                       command=display_bus_stop_details)
            display_button.pack()

            add_to_favorites_button = tk.Button(bus_stop_window, text="Add to Favorites",
                                                command=add_to_favorites_stop)
            add_to_favorites_button.pack()

        def target_bus_service():
            bus_service_window = tk.Toplevel(user_window)
            bus_service_window.title("Target Bus Service")
            center_window(bus_service_window, 400, 300)  # Center the Bus Service window

            def display_bus_service_details():
                service_no = bus_service_entry.get()
                result = select_bus_service(db, service_no)

                # Clear existing Text widget, if it exists
                for widget in bus_service_window.winfo_children():
                    if isinstance(widget, tk.Text):
                        widget.destroy()

                # Create a Text widget to display multiline text
                result_text = tk.Text(bus_service_window, height=10, width=40, state=tk.NORMAL)

                # Insert the new content
                result_text.insert(tk.END, "Bus service details displayed:\n" + result)

                # Set the Text widget back to read-only
                result_text.configure(state=tk.DISABLED)

                result_text.pack()

            def add_to_favorites_no():
                service_no = bus_service_entry.get()
                result = add_to_favorite_bus_service(db, service_no)
                messagebox.showinfo("Success, Bus service added to favorites!", result)

            bus_service_label = tk.Label(bus_service_window, text="Enter Bus Service Number:")
            bus_service_label.pack()

            bus_service_entry = tk.Entry(bus_service_window)
            bus_service_entry.pack()

            display_button = tk.Button(bus_service_window, text="Display Bus Service Details",
                                       command=display_bus_service_details)
            display_button.pack()

            add_to_favorites_button = tk.Button(bus_service_window, text="Add to Favorites",
                                                command=add_to_favorites_no)
            add_to_favorites_button.pack()

        def display_favorites(db):
            favorites_window = tk.Toplevel(user_window)
            favorites_window.title("Favorite Items")
            center_window(favorites_window, 400, 300)  # Center the Favorites window

            # Create a Text widget to display multiline text
            favorites_text = tk.Text(favorites_window, height=10, width=40, state=tk.NORMAL)

            # Retrieve favorite bus stops and display
            favorites_text.insert(tk.END, "Favorite Bus Stops:\n")
            favorite_bus_stops = get_favorite_bus_stops(db)
            for stop_details in favorite_bus_stops:
                # Display bus stop details
                favorites_text.insert(tk.END, f"{stop_details}\n")

            # Retrieve favorite bus services and display
            favorites_text.insert(tk.END, "\nFavorite Bus Services:\n")
            favorite_bus_services = get_favorite_bus_services(db)
            for service_details in favorite_bus_services:
                # Display bus service details
                favorites_text.insert(tk.END, f"{service_details}\n")

            # Set the Text widget back to read-only
            favorites_text.configure(state=tk.DISABLED)

            favorites_text.pack()

        def delete_favorites_window(db):
            delete_window = tk.Toplevel()
            delete_window.title("Delete Favorites")
            center_window(delete_window, 400, 300)  # Center the Delete Favorites window

            def delete_bus_stop():
                bus_stop_window = tk.Toplevel(delete_window)
                bus_stop_window.title("Delete Bus Stop from Favorites")
                center_window(bus_stop_window, 400, 300)  # Center the Delete Bus Stop window

                def delete_bus_stop_from_favorites():
                    bus_stop_code = bus_stop_entry.get()
                    result = remove_from_favorite_bus_stop(db, bus_stop_code)
                    messagebox.showinfo("Success", result)

                bus_stop_label = tk.Label(bus_stop_window, text="Enter Bus Stop Code:")
                bus_stop_label.pack()

                bus_stop_entry = tk.Entry(bus_stop_window)
                bus_stop_entry.pack()

                delete_button = tk.Button(bus_stop_window, text="Delete from Favorites",
                                          command=delete_bus_stop_from_favorites)
                delete_button.pack()

            def delete_bus_service():
                bus_service_window = tk.Toplevel(delete_window)
                bus_service_window.title("Delete Bus Service from Favorites")
                center_window(bus_service_window, 400, 300)  # Center the Delete Bus Service window

                def delete_bus_service_from_favorites():
                    service_no = bus_service_entry.get()
                    result = remove_from_favorite_bus_service(db, service_no)
                    messagebox.showinfo("Success", result)

                bus_service_label = tk.Label(bus_service_window, text="Enter Bus Service Number:")
                bus_service_label.pack()

                bus_service_entry = tk.Entry(bus_service_window)
                bus_service_entry.pack()

                delete_button = tk.Button(bus_service_window, text="Delete from Favorites",
                                          command=delete_bus_service_from_favorites)
                delete_button.pack()

            delete_bus_stop_button = tk.Button(delete_window, text="Delete Bus Stop from Favorites",
                                               command=delete_bus_stop)
            delete_bus_stop_button.pack()

            delete_bus_service_button = tk.Button(delete_window, text="Delete Bus Service from Favorites",
                                                  command=delete_bus_service)
            delete_bus_service_button.pack()

        options = {
            "BusStop": "BusStopCode",
            "BusService": "BusService",
            "Favorites": "Favorites",
            "Delete": "Delete"
        }

        option_label = tk.Label(user_window, text="Select an option:")
        option_label.pack()

        for option, label in options.items():
            category_button = tk.Button(user_window, text=label, command=lambda opt=option: option_selected(opt))
            category_button.pack()

        def option_selected(option):
            if option == "BusStop":
                select_bus_stop()
            elif option == "BusService":
                target_bus_service()
            elif option == "Favorites":
                display_favorites(db)
            elif option == "Delete":
                delete_favorites_window(db)

    main_menu_label = tk.Label(main_window, text="Main Menu")
    main_menu_label.pack()

    api_operations_button = tk.Button(main_window, text="API Operations", command=api_operations)
    api_operations_button.pack()

    database_operations_button = tk.Button(main_window, text="Database Operations", command=database_operations)
    database_operations_button.pack()

    user_selections_button = tk.Button(main_window, text="User Selections", command=user_selections)
    user_selections_button.pack()

    exit_button = tk.Button(main_window, text="Exit Program", command=main_window.destroy)
    exit_button.pack()

    main_window.mainloop()


if __name__ == "__main__":
    api_key = Config.API_KEY

    if api_key is None:
        print("API key is not set. Please set the API_KEY environment variable.")
    else:
        db = PublicTransportDatabase(Config.DATABASE_NAME)
        data_fetcher = LTADataFetcher(api_key)
        db.create_tables()

    main_menu()
