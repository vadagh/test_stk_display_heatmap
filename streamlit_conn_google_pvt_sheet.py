import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
import io # Required for reading string data as a file

# Authenticate and connect to Google Sheets
def connect_to_gsheet(creds_json, spreadsheet_name, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", 
             'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", 
             "https://www.googleapis.com/auth/drive"]
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(spreadsheet_name)  
    return spreadsheet.worksheet(sheet_name)  # Access specific sheet by name

# Google Sheet credentials and details
SPREADSHEET_NAME = 'Stock Dashboard'
SHEET_NAME = 'AAPL'
CREDENTIALS_FILE = 'C:/Users/srinu/sandbox/py/credentials.json'

# Connect to the Google Sheet
sheet_by_name = connect_to_gsheet(CREDENTIALS_FILE, SPREADSHEET_NAME, sheet_name=SHEET_NAME)


#st.title("Simple Data Entry using Streamlit")
# Read Data from Google Sheets
def read_data():
    data = sheet_by_name.get_all_records()  # Get all records from Google Sheet
    return pd.DataFrame(data)

df = read_data()

st.set_page_config(layout="wide") # Optional: Use wide layout for better graph display

st.title("Stock Price Analysis")
st.markdown("---")

# --- PLACEHOLDER DATA LOADING ---
# IMPORTANT: Replace this section with your actual data loading logic.
# For demonstration, I'm creating a sample DataFrame that mimics your data structure
# if it were properly delimited.

# Define your data as a string (this is where you'd paste your correctly delimited data)
# Example of what your data *should* look like for easy parsing:

# If your data is truly structured with Date, Open, High, Low, Close without spaces in between,
# parsing it is much harder. Please provide it with delimiters.
# Assuming the example format above (comma-separated):
try:
    df = df

    # Convert 'Date' column to datetime objects
    # Handle potential mixed formats if your data has variations like 13:05:00 vs 16:00:00
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Drop rows where Date conversion failed
    df.dropna(subset=['Date'], inplace=True)

    # Sort by date for proper time series plotting
    df = df.sort_values(by='Date').reset_index(drop=True)

except Exception as e:
    st.error(f"Error loading or parsing data: {e}")
    st.info("Please ensure your data is correctly delimited (e.g., comma-separated) and try again.")
    st.stop() # Stop the app if data loading fails

# --- End of PLACEHOLDER DATA LOADING ---


if not df.empty:
    st.subheader("Raw Data Preview")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")

    st.subheader("Historical Stock Prices")

    # Define the columns to plot
    # You can select 'Open', 'High', 'Low', 'Close' or all of them
    price_columns = ['Open', 'High', 'Low', 'Close']
    available_price_columns = [col for col in price_columns if col in df.columns]

    if 'Date' not in df.columns:
        st.warning("The DataFrame does not contain a 'Date' column. Cannot plot time series.")
    elif not available_price_columns:
        st.warning("The DataFrame does not contain any price columns ('Open', 'High', 'Low', 'Close').")
    else:
        # Allow user to select which price columns to view
        selected_prices = st.multiselect(
            "Select Price Type(s) to Display:",
            options=available_price_columns,
            default=['Close'] if 'Close' in available_price_columns else available_price_columns[0]
        )

        if selected_prices:
            # Create a long-form DataFrame suitable for Plotly Express when plotting multiple lines
            # This is optional, you can also plot multiple lines by passing a list to `y`
            # However, for clearer legends and interactivity, melting is often preferred.
            df_melted = df.melt(id_vars=['Date'], value_vars=selected_prices,
                                var_name='Price Type', value_name='Value')

            # Create the interactive line plot using Plotly Express
            fig = px.line(df_melted,
                          x='Date',
                          y='Value',
                          color='Price Type', # This will create a separate line for each selected price type
                          title='Stock Price Over Time',
                          labels={'Date': 'Date', 'Value': 'Price ($)'},
                          hover_data={'Value': ':.2f', 'Price Type': True})

            fig.update_layout(hovermode="x unified") # Improves hover experience
            fig.update_xaxes(
                rangeslider_visible=True, # Add a range slider for easy zooming
                rangeselector=dict( # Add pre-set date ranges
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )
            # Display the Plotly chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Please select at least one price type to display the graph.")
else:
    st.info("No data available to plot. Please ensure your data is correctly loaded.")

st.markdown("---")
st.write("This app displays historical stock prices. Replace the placeholder data section with your actual data source.")



#heatmap for closed price

st.set_page_config(layout="wide") # Use wide layout for better graph display

st.title("Close Price Heatmap")
st.markdown("---")

# --- PLACEHOLDER DATA LOADING ---
# IMPORTANT: Replace the content of 'data_string' with your actual,
# correctly delimited (e.g., comma-separated) data.

try:
    df = df

    # Convert 'Date' column to datetime objects
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df.dropna(subset=['Date'], inplace=True) # Drop rows where Date conversion failed

    # Ensure 'Close' column is numeric
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df.dropna(subset=['Close'], inplace=True) # Drop rows where Close conversion failed

    if 'Close' not in df.columns:
        st.error("The DataFrame does not contain a 'Close' column. Cannot draw heatmap.")
        st.stop()

    # Extract Year and Month for the heatmap
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.strftime('%b') # Abbreviated month name (e.g., Jan, Feb)

    # Define the order of months for the X-axis
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Pivot the table for the heatmap:
    # rows are years, columns are months, values are the mean Close prices
    heatmap_data = df.pivot_table(index='Year', columns='Month', values='Close', aggfunc='mean')

    # Reindex columns to ensure months are in chronological order
    
    heatmap_data = heatmap_data.sort_index(ascending=False)
    heatmap_data = heatmap_data.reindex(columns=month_order)
    st.dataframe(heatmap_data.head(), use_container_width=True)
    sorted_years_desc = heatmap_data.index.astype(str).tolist()

except Exception as e:
    st.error(f"Error loading or parsing data: {e}")
    st.info("Please ensure your data is correctly delimited (e.g., comma-separated) and includes 'Date' and 'Close' columns.")
    st.stop() # Stop the app if data loading fails

# --- End of PLACEHOLDER DATA LOADING ---


if not df.empty and 'Close' in df.columns and not heatmap_data.empty:
    st.subheader("Raw Data Preview (first 5 rows)")
    st.dataframe(df.head(), use_container_width=True)

    st.markdown("---")

    st.subheader("Average Monthly Close Price Heatmap")
    st.write("This heatmap displays the **average Close price** for each month, organized by year. Darker colors indicate lower average prices, while brighter colors indicate higher average prices. Empty cells mean no data was available for that specific month and year.")

    # Create the heatmap
    fig = px.imshow(heatmap_data,
                    labels=dict(x="Month", y="Year", color="Avg. Close Price"),
                    x=heatmap_data.columns, # Months (already ordered)
                    y=heatmap_data.index.astype(str), # Years (as strings for display)
                    color_continuous_scale=px.colors.sequential.Plasma, # A good color scale for price
                    aspect="auto", # Adjust aspect ratio
                    title="Average Close Price Heatmap (Year vs. Month)")

    fig.update_xaxes(side="top") # Move month labels to the top for better readability
    fig.update_layout(
        height=600 # Adjust height as needed
    )
    
    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No data available to plot the heatmap, or 'Close' column is missing/invalid. Please check your data.")

st.markdown("---")
st.write("This app visualizes average monthly close prices. Remember to replace the placeholder data section with your actual, correctly formatted dataset.")
