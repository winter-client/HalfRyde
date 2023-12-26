import requests
import pymongo
from datetime import datetime
from mongoConf import Config

# Set up MongoDB connection URL
client = pymongo.MongoClient(Config.MONGO_CONNECTION_URL)
db = client["busArrivals"]
collection = db["busArrivalData"]
favorite_stops_collection = db["favoriteBusStops"]

# Set up LTA API key
base_url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2"
headers = {
    "AccountKey": Config.LTA_API_KEY,
    "accept": "application/json",
}


# Connect to the MongoDB database
client = pymongo.MongoClient("mongodb://localhost:27017")  # Update with your MongoDB connection URL
db = client["busArrivals"]
collection = db["bus_arrival_data"]
favorite_stops_collection = db["favorite_bus_stops"]

# Index for bus_arrival_data collection
collection.create_index([("BusStopCode", pymongo.ASCENDING)])
collection.create_index([("Date", pymongo.ASCENDING)])

# Index for favorite_bus_stops collection
favorite_stops_collection.create_index([("bus_stops", pymongo.ASCENDING)])

# Global variable to store multiple savepoints
favorite_stop_savepoints = []
document_savepoints = []

def get_color(load):
    if load == "SEA":
        return "[Green] Seats Available"
    elif load == "SDA":
        return "[Amber] Standing Available"
    elif load == "LSD":
        return "[Red] Limited Standing"
    else:
        return "Unknown"


def round_to_minute(time_str):
    from datetime import datetime, timedelta
    if time_str:
        time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S+08:00")
        time_now = datetime.now()
        time_diff = time - time_now
        minutes = time_diff.seconds // 60
        return f"{minutes} mins"
    return None


def create_document(service_no, operation_availability, arrival_availability, estimated_arrival, load, feature,
                    vehicle_type, next_bus2, next_bus3):
    return {
        "ServiceNo": service_no,
        "OperationStatus": operation_availability,
        "ArrivalStatus": arrival_availability,
        "EstimatedArrival": estimated_arrival,
        "Load": load,
        "WheelchairAccessible": feature,
        "VehicleType": vehicle_type,
        "NextBus2": {
            "EstimatedArrival": next_bus2.get("EstimatedArrival") if next_bus2 else None,
            "Load": get_color(next_bus2.get("Load")) if next_bus2 else None,
            "WheelchairAccessible": next_bus2.get("Feature") if next_bus2 else None
        },
        "NextBus3": {
            "EstimatedArrival": next_bus3.get("EstimatedArrival") if next_bus3 else None,
            "Load": get_color(next_bus3.get("Load")) if next_bus3 else None,
            "WheelchairAccessible": next_bus3.get("Feature") if next_bus3 else None
        },
    }

def read_all_documents():
    return collection.find()

def read_documents_by_date(current_date):
    return collection.find({"Date": current_date})


def update_document(document_id, update_data):
    collection.update_one({"_id": document_id}, {"$set": update_data})


def delete_document(document_id):
    collection.delete_one({"_id": document_id})


def find_document_by_date(date):
    return collection.find({"Date": date})


# Add favorite bus stop into favorite bus stops list
def add_favorite_bus_stop():
    while True:
        bus_stop_code = input("Enter the bus stop code to add to favorites: ")
        if bus_stop_code.isdigit() and len(bus_stop_code) == 5: # Input validation check
            break
        else:
            print("Invalid bus stop code. Please enter a 5-digit numeric code.")

    try:
        favorite_stops = get_favorite_bus_stops()
        if bus_stop_code not in favorite_stops: # Check if bus stop code input is inside favorites list
            favorite_stops.append(bus_stop_code)
            update_favorite_bus_stops(favorite_stops)
            print(f"Bus stop {bus_stop_code} added to favorites.")
        else:
            print(f"Bus stop {bus_stop_code} is already in favorites.")
    except Exception as e:
        print(f"An error occurred while adding the bus stop: {str(e)}")

# Delete a favorite bus stop from favorites list
def delete_favorite_bus_stop():
    while True:
        bus_stop_code = input("Enter the bus stop code to delete from favorites: ")

        if not bus_stop_code.isdigit() or len(bus_stop_code) != 5: # Input Validation Check
            print("Invalid bus stop code. Please enter a 5-digit number.")
        else:
            favorite_stops = get_favorite_bus_stops() # Gets all bus stop codes from the favorites list

            if bus_stop_code in favorite_stops: # Checks if bus stop code is inside the favorites list
                favorite_stops.remove(bus_stop_code)
                update_favorite_bus_stops(favorite_stops)
                print(f"Bus stop {bus_stop_code} deleted from favorites.")
            else:
                print(f"Bus stop {bus_stop_code} is not present in favorites. Please enter a valid bus stop code.")
                continue  # Continue the loop to prompt the user for input again

            break  # Exit the loop if a valid input is provided

# Gets favorite bus stops from MongoDB Database
def get_favorite_bus_stops():
    favorites = favorite_stops_collection.find_one({"_id": "favorites"})
    return favorites.get("bus_stops", []) if favorites else []

# Updates favorite bus stops list into MongoDB Database
def update_favorite_bus_stops(bus_stops):
    favorite_stops_collection.update_one(
        {"_id": "favorites"},
        {"$set": {"bus_stops": bus_stops}},
        upsert=True
    )

# Retrieves and displays favorite bus stops list from MongoDB Database.
def display_favorite_bus_stops():
    favorite_stops = get_favorite_bus_stops()
    print("Favorite Bus Stops:")
    for stop in favorite_stops:
        print(stop)
    print()

# Fetches the bus arrival info from LTA DataMall
def get_bus_arrival_info():
    # Always assume the user wants to search by bus stop
    while True:
        bus_stop_code = input("Enter Bus Stop Code: ")
        if bus_stop_code.isdigit() and len(bus_stop_code) == 5: # Input Validation Check (all digits + no. of digits = 5)
            break
        else:
            print("Invalid Bus Stop Code. It must be a 5-digit number. Please try again.")

    service_no = input("Enter Service Number (press Enter to skip): ")
    params = {
        "BusStopCode": bus_stop_code,
        "ServiceNo": service_no,
    }
    # Makes the HTTP GET request to the LTA API
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        services = data.get("Services", [])

        for service in services:
            current_date = datetime.now().strftime("%Y-%m-%d")
            # Creates a document to store all Bus Arrival Info
            bus_arrival_info = create_document(
                service.get("ServiceNo"),
                "Bus is in operation" if service.get("NextBus", {}).get(
                    "EstimatedArrival") else "Bus is NOT in operation",
                "Arrival data is available" if service.get("NextBus", {}).get(
                    "EstimatedArrival") else "Arrival data is NOT available (No Est. Available)",
                round_to_minute(service.get("NextBus", {}).get("EstimatedArrival")),
                get_color(service.get("NextBus", {}).get("Load")),
                service.get("NextBus", {}).get("Feature"),
                service.get("NextBus", {}).get("Type"),
                service.get("NextBus2", {}),
                service.get("NextBus3", {})
            )
            bus_arrival_info["Date"] = current_date
            # Inserts the document into the MongoDB Database
            document_id = collection.insert_one(bus_arrival_info).inserted_id

            # Print Statements for Bus Arrival
            print(f"Service Number: {service.get('ServiceNo')}")
            print(f"Operation Status: {bus_arrival_info['OperationStatus']}")
            print(f"Arrival Status: {bus_arrival_info['ArrivalStatus']}")

            print("\nArriving Bus:")
            print(f"   - Arriving In: {bus_arrival_info['EstimatedArrival']}")
            print(f"   - Load: {bus_arrival_info['Load']}")
            print(f"   - Wheelchair Accessible: {bus_arrival_info['WheelchairAccessible']}")

            print("\nNext Bus 2:")
            print(f"   - Arriving In: {round_to_minute(bus_arrival_info['NextBus2']['EstimatedArrival'])}")
            print(f"   - Load: {bus_arrival_info['NextBus2']['Load']}")
            print(f"   - Wheelchair Accessible: {bus_arrival_info['NextBus2']['WheelchairAccessible']}")

            print("\nNext Bus 3:")
            print(f"   - Arriving In: {round_to_minute(bus_arrival_info['NextBus3']['EstimatedArrival'])}")
            print(f"   - Load: {bus_arrival_info['NextBus3']['Load']}")
            print(f"   - Wheelchair Accessible: {bus_arrival_info['NextBus3']['WheelchairAccessible']}")

            print(f"\nDocument inserted with ID: {document_id}\n")
    else:
        print(f"Request failed with status code {response.status_code}")


def create_savepoint():
    global favorite_stop_savepoints
    favorite_stops = get_favorite_bus_stops()
    favorite_stop_savepoints.append(favorite_stops.copy())
    print(f"Savepoint {len(favorite_stop_savepoints)} created.")


def rollback_to_savepoint():
    global favorite_stop_savepoints
    while True:
        try:
            rollback_number = int(input("Enter the rollback number: "))
            if 1 <= rollback_number <= len(favorite_stop_savepoints):
                # Clear savepoints that occurred after the specified rollback point
                favorite_stop_savepoints = favorite_stop_savepoints[:rollback_number]

                new_favorite_stops = favorite_stop_savepoints[rollback_number - 1]
                update_favorite_bus_stops(new_favorite_stops)
                print(f"Rolled back to Savepoint {rollback_number}.")
                break  # Exit the loop if the input is valid
            else:
                print("Invalid rollback number for favorite bus stops.")
        except ValueError:
            print("Invalid input. Please enter a valid rollback number.")
        except Exception as e:
            print(f"An error occurred during the rollback: {str(e)}")


def create_savepoint_for_documents():
    global document_savepoints
    documents = list(read_all_documents())
    document_savepoints.append(documents.copy())
    print(f"Document Savepoint {len(document_savepoints)} created.")

def rollback_documents_to_savepoint():
    global document_savepoints
    while True:
        try:
            rollback_number = int(input("Enter the rollback number: "))
            if 1 <= rollback_number <= len(document_savepoints):
                document_savepoints = document_savepoints[:rollback_number]
                new_documents = document_savepoints[rollback_number - 1]
                # Clear the current documents and insert the documents from the savepoint
                collection.delete_many({})
                if new_documents:
                    collection.insert_many(new_documents)
                print(f"Bus arrival documents rolled back to Savepoint {rollback_number}.")
                break  # Exit the loop if the input is valid
            else:
                print("Invalid rollback number for bus arrival documents.")
        except ValueError:
            print("Invalid input. Please enter a valid rollback number.")
        except Exception as e:
            print(f"An error occurred during the rollback: {str(e)}")


try:
    while True:
        print("======= Welcome to Half Ryd Bot  =======")
        print("1. Get Bus Arrival Information")
        print("2. Display All Bus Arrival Documents")
        print("3. Add Favorite Bus Stop")
        print("4. Delete Favorite Bus Stop")
        print("5. Display Favorite Bus Stops")
        print("6. Create Savepoint for Bus Arrival Documents")
        print("7. Rollback to Savepoint for Bus Arrival Documents")
        print("8. Create Savepoint for Favorite Bus Stops")
        print("9. Rollback to Savepoint for Favorite Bus Stops")
        print("0. Exit")

        choice = input("Enter your choice (0-9): ")

        if choice == "1":
            get_bus_arrival_info()

        elif choice == "2":
            view_option = input("Enter 'A' to view all documents or 'D' to view by date: ").upper()
            if view_option == "A":
                # Display all documents
                documents = read_all_documents()
                if documents.count() > 0:
                    print("All Bus Arrival Documents:")
                    for document in documents:
                        print(document)
                        print()
                else:
                    print("No bus arrival documents found.")

            elif view_option == "D":
                # Get user input for the date
                date_str = input("Enter the date (YYYY-MM-DD): ")
                try:
                    # Locate and display documents based on date
                    documents = read_documents_by_date(date_str)
                    if documents.count() > 0:
                        print(f"Bus Arrival History for {date_str}:")
                        for document in documents:
                            print(document)
                            print()
                    else:
                        print(f"No bus arrival history found for {date_str}")
                except ValueError:
                    print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
            else:
                print("Invalid option. Please enter 'A' or 'D'.")


        elif choice == "3":
            # Add favorite bus stop
            add_favorite_bus_stop()


        elif choice == "4":
            # Delete favorite bus stop
            delete_favorite_bus_stop()


        elif choice == "5":
            # Display favorite bus stops
            display_favorite_bus_stops()


        elif choice == "6":
            # Create a savepoint for bus arrival documents
            create_savepoint_for_documents()


        elif choice == "7":
            # Rollback to a specific savepoint for bus arrival documents
            rollback_documents_to_savepoint()


        elif choice == "8":
            # Create a savepoint for favorite bus stops
            create_savepoint()


        elif choice == "9":
            # Rollback to a specific savepoint for favorite bus stops
            rollback_to_savepoint()


        elif choice == "0":
            # Exit the program
            break
        else:
            print("Invalid choice. Please enter a number between 0 and 9.")


except ValueError:
    print("Invalid input. Please enter a valid rollback number.")

except Exception as e:
    print(f"An error occurred: {str(e)}")

# Close the MongoDB connection
client.close()