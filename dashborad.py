import streamlit as st
import boto3
import pandas as pd
from decimal import Decimal
import json

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

table = dynamodb.Table('customer_data')

# Set Streamlit layout to wide
st.set_page_config(layout="wide")

# Function to fetch data from DynamoDB
@st.cache_data(ttl=60)
def fetch_data():
    response = table.scan()
    data = response['Items']
    return data

# Function to update booking status
def update_booking_status(identity_card_number, status):
    table.update_item(
        Key={'identity_card_number': identity_card_number},
        UpdateExpression="set booking_status=:s",
        ExpressionAttributeValues={':s': status},
        ReturnValues="UPDATED_NEW"
    )

# Function to remove a customer
def remove_customer(identity_card_number):
    table.delete_item(
        Key={'identity_card_number': identity_card_number}
    )

# Function to add a new customer
def add_customer(data):
    table.put_item(Item=data)

# Function to fetch and display conversation
def show_conversation(identity_card_number):
    response = table.get_item(
        Key={'identity_card_number': identity_card_number},
        ProjectionExpression='conversation'
    )
    if 'Item' in response:
        conversations = response['Item'].get('conversation', [])
        # print(conversations)
        
        if conversations:
            for conv in conversations:
                conv_type = conv['type']
                message = conv['message']
                if conv_type == 'customer':
                    # Check if the message is a JSON string
                    if message.startswith('{'):
                        message_json = json.loads(message)
                        customer_message = message_json.get("text", "")
                    else:
                        customer_message = message
                    st.markdown(f'**Customer**: {customer_message}')
                elif conv_type == 'agent':
                    if message.startswith('{'):
                        message_json = json.loads(message)
                        agent_message = message_json.get("text", "")
                    else:
                        agent_message = message    
                    st.markdown(f'**Agent**: {agent_message}')
                    
                st.markdown('---')
        else:
            st.markdown("No conversations found for this customer.")
    else:
        st.error("Error fetching conversations.")

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'selected_customer_id' not in st.session_state:
    st.session_state.selected_customer_id = None
if 'selected_customers' not in st.session_state:
    st.session_state.selected_customers = []
if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None

if st.session_state.page == "add_customer":
    
    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
    st.header("Add New Customer")
    with st.form(key='add_customer_form'):
        full_name = st.text_input("Full Name")
        identity_card_options = ["Adhar Card", "Passport", "Voter Id", "Other"]
        identity_card = st.selectbox("Identity Card", identity_card_options)
        other_identity_card = st.text_input("Please specify the identity card type") if identity_card == "Other" else None

        identity_card_number = st.text_input("Identity Card Number")
        age = st.number_input("Age", min_value=18, max_value=100)
        phone_number = st.text_input("Phone Number")
        room_type_options = ["Standard", "Deluxe", "Suite", "Other"]
        room_type = st.selectbox("Room Type", room_type_options)
        other_room_type = st.text_input("Please specify the room type") if room_type == "Other" else None

        number_of_rooms = st.number_input("Number of Rooms", min_value=1, max_value=10)
        check_in_date = st.date_input("Check-in Date")
        check_out_date = st.date_input("Check-out Date")
        food_service = st.selectbox("Food Service", ["Yes", "No"])
        total_bill_amount = st.number_input("Total Bill Amount", min_value=0.0, format="%f")

        payment_option_options = ["UPI", "Debit Card", "Credit Card", "Other"]
        payment_option = st.selectbox("Payment Option", payment_option_options)
        other_payment_option = st.text_input("Please specify the payment option") if payment_option == "Other" else None

        col1, col2, col3 = st.columns([0.5, 6, 0.33])

        with col1:
            submit_button = st.form_submit_button("Submit")
        with col3:
            back_button = st.form_submit_button("Back")

        st.markdown(
        """
        <style>
        .stButton>button {
            background-color: #007bff;
            color: white;
            margin-bottom: 0px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        @media (max-width: 768px) {
            .stButton>button {
                width: 100%; /* Full width for small screens */
            }
        }
        @media (min-width: 769px) {
            .stButton>button {
                width: auto; /* Auto width for larger screens */
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

        
        if submit_button:
            new_customer_data = {
                "identity_card_number": identity_card_number,
                "full_name": full_name,
                "age": Decimal(str(age)),
                "identity_card": other_identity_card if identity_card == "Other" else identity_card,
                "phone_number": phone_number,
                "room_type": other_room_type if room_type == "Other" else room_type,
                "number_of_rooms": Decimal(str(number_of_rooms)),
                "check_in_date": str(check_in_date),
                "check_out_date": str(check_out_date),
                "food_service": food_service,
                "total_bill_amount": Decimal(str(total_bill_amount)),
                "payment_option": other_payment_option if payment_option == "Other" else payment_option,
                "booking_status": "Pending"
            }
            add_customer(new_customer_data)
            st.cache_data.clear()  # Clear cached data to fetch updated data
            st.success("Customer added successfully!")
            st.session_state.page = "home"
            st.rerun()  # Full page refresh

        if back_button:
            st.session_state.page = "home"
            st.rerun()

elif st.session_state.page == "show_conversation":
    
    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
    st.title('Customer Conversation')

    # Fetch and display conversation for selected customer
    if st.session_state.selected_customer_id:
        show_conversation(st.session_state.selected_customer_id)
    else:
        st.warning("Please select a customer to view conversations.")
    
    st.markdown(
        """
        <style>
        .stButton>button {
            background-color: #007bff;
            color: white; /* Text color */
            margin-bottom: 0px;
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow text */
            text-overflow: ellipsis; /* Show ellipsis for overflow */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("Back"):
        st.session_state.page = "home"
        st.rerun()

else:
    # Layout using columns
    title_column, filter_name_id, filter_status = st.columns([3, 1, 1])

    # Title column
    with title_column:
        st.title('*Booking Dashboard*')

    # Fetch data
    data = fetch_data()
    df = pd.DataFrame(data)

    with filter_name_id:
        search_term = st.text_input("Search by Name or ID")

    # Filter data based on search term (case-insensitive)
    if search_term:
        search_term_lower = search_term.lower()  # Convert search term to lowercase
        df = df[df.apply(lambda row: search_term_lower in row['full_name'].lower() or
                                        search_term_lower in row['identity_card_number'].lower(), axis=1)]

    with filter_status:
        filter_status = st.selectbox('Filter by Booking Status', ['All', 'Pending', 'Booked', 'Not Booked'])

    if filter_status != 'All':
        df = df[df['booking_status'].str.lower() == filter_status.lower()]

    # Create a container for the buttons at the top right
    cols = st.columns([3, 2,3, 11, 2, 2])  # Adjust column widths for button placement
    with cols[4]:
        approve_button = st.button('Approve')
    with cols[5]:  # Adjusted index for the decline button
        decline_button = st.button('Decline')
    with cols[0]:
        add_button = st.button('Add Customer')
    with cols[1]:
        remove_button = st.button('Remove')
    with cols[2]:
        conversation_button = st.button('Show Conversation')    

    # Reorder columns as specified
    df = df[[
        "identity_card_number", "full_name", "age", "identity_card",
        "phone_number", "room_type", "number_of_rooms", "check_in_date",
        "check_out_date", "food_service", "total_bill_amount",
        "payment_option", "booking_status"
    ]]

    # Display table headers with improved CSS styling
    st.markdown(
        """
        <style>
        .table-header {
            font-weight: bold;
            font-size: 18px;
            text-align: center;
            padding: 7px 0; /* Padding adjusted for better header appearance */
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow text */
            text-overflow: ellipsis; /* Show ellipsis for overflow */
            margin-bottom: 4px; /* Margin bottom added */
        }
        .table-data {
            text-align: center;
            max-width: 100%;
        }
        .status-box {
            border-radius: 5px;
            color: white;
            text-align: center;
            font-weight: bold;
            padding: 15px 10px;
        }
        .status-pending {
            background-color: orange;
        }
        .status-booked {
            background-color: green;
        }
        .status-not-booked {
            background-color: red;
        }
        .stButton>button {
            background-color: #007bff; 
            color: white; /* Text color */
            margin-bottom: 0px;
            width: 100%; /* Make buttons full width */
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow text */
            text-overflow: ellipsis; /* Show ellipsis for overflow */
        }
        .row-divider {
            border-top: 1px solid rgba(0, 0,0, 0.5); 
            margin: 5px 0;
        }
        .header-divider {
            border-top: 3px solid rgba(0, 0,0, 0.5); 
            margin: 5px 0;
        }
        body {
            font-size: 16px;
            background-color:  #e9ecef;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display table headers
    cols = st.columns(len(df.columns) + 1)  # +1 for the Select column

    # Select column header
    cols[0].markdown('<div class="table-header">Select</div>', unsafe_allow_html=True)

    # Other headers
    header_labels = {
        "identity_card_number": "ID",
        "full_name": "Name",
        "age": "Age",
        "identity_card": "ID Card",
        "phone_number": "Phone",
        "room_type": "Room Type",
        "number_of_rooms": "Rooms",
        "check_in_date": "Check-In",
        "check_out_date": "Check-Out",
        "food_service": "Food",
        "total_bill_amount": "Bill",
        "payment_option": "Payment",
        "booking_status": "Status"
    }

    for i, col in enumerate(df.columns):
        cols[i+1].markdown(f'<div class="table-header">{header_labels.get(col, col)}</div>', unsafe_allow_html=True)
        
    st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)
    
    # Display table rows with checkboxes
    for idx, row in df.iterrows():
        cols = st.columns(len(df.columns) + 1)

        # Centered checkbox in Select column
        checkbox_id = f"checkbox_{row['identity_card_number']}"
        selected = cols[0].checkbox(" ", key=checkbox_id, help='', on_change=lambda: None)

        if selected:
            if checkbox_id not in st.session_state.selected_customers:
                st.session_state.selected_customers.append(checkbox_id)
        else:
            if checkbox_id in st.session_state.selected_customers:
                st.session_state.selected_customers.remove(checkbox_id)

        for i, col in enumerate(df.columns):
            if col == "booking_status":
                if row[col] == "Pending":
                    cols[i+1].markdown('<div class="status-box status-pending"></div>', unsafe_allow_html=True)
                elif row[col] == "Booked":
                    cols[i+1].markdown('<div class="status-box status-booked"></div>', unsafe_allow_html=True)
                else:
                    cols[i+1].markdown('<div class="status-box status-not-booked"></div>', unsafe_allow_html=True)
           
            elif col in ["age", "number_of_rooms"]:
                cols[i+1].markdown(f'<div class="table-data" style="max-width: 80px; overflow: hidden; text-overflow: ellipsis;">{row[col]}</div>', unsafe_allow_html=True)
            else:
                cols[i+1].markdown(f'<div class="table-data">{row[col]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

    # Function to handle button click
    def handle_button_click(status):
        for idx, row in df.iterrows():
            checkbox_id = f"checkbox_{row['identity_card_number']}"
            if checkbox_id in st.session_state.selected_customers:
                update_booking_status(row['identity_card_number'], status)
        st.session_state.selected_customers.clear()  # Clear selected customers after action
        st.cache_data.clear()  # Clear cached data to fetch updated data
        st.rerun()  # Full page refresh

    # Function to handle remove button click
    def handle_remove_button_click():
        for idx, row in df.iterrows():
            checkbox_id = f"checkbox_{row['identity_card_number']}"
            if checkbox_id in st.session_state.selected_customers:
                remove_customer(row['identity_card_number'])
        st.session_state.selected_customers.clear()  # Clear selected customers after action
        st.cache_data.clear()  # Clear cached data to fetch updated data
        st.rerun()  # Full page refresh

    # Handle button clicks
    if approve_button:
        handle_button_click('Booked')

    if decline_button:
        handle_button_click('Not Booked')

    if remove_button:
        handle_remove_button_click()

    # Handle add customer button click
    if add_button:
        st.session_state.page = "add_customer"
        st.rerun()
        
    # Check if conversation button is clicked
    if conversation_button:
        selected_rows = st.session_state.selected_customers

        if len(selected_rows) == 1:
            # Get identity card number of selected customer
            selected_customer_id = selected_rows[0].split('_')[1]  # Extract identity card number from session state
            print(selected_customer_id)
            # Set selected customer ID
            st.session_state.selected_customer_id = selected_customer_id
            st.session_state.page = "show_conversation"
            st.rerun()
        else:
            # Show warning if no rows or more than one row is selected
            if len(selected_rows) == 0:
                st.warning("Please select a customer to view the conversation.")
            else:
                st.warning("Please select exactly one customer to view the conversation.")
