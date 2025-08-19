import streamlit as st
import pandas as pd
import random
import time
import snowflake.connector
import uuid

# ---- Race Constants ----
RACE_FEE = 1000  # Entry fee for the race
PRIZE_MONEY = 5000  # Prize money for the winner

# ---- Streamlit Page Configuration ----
st.set_page_config(layout="wide", page_title="Race Simulator")
st.title("🏎️ Race Simulator")
st.write("Welcome to the simulator! Enter team and car data to get started.")

# ---- Snowflake Connection Function ----
# We use Streamlit's cache to create a single, efficient connection to Snowflake.
@st.cache_resource
def get_snowflake_connection():
    """Establishes and caches a connection to Snowflake using st.secrets."""
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"]
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Snowflake. Please check your credentials in secrets.toml: {e}")
        return None

# ---- Data Loading Function ----
@st.cache_data(ttl=60) # Cache data for 60 seconds to avoid unnecessary queries
def load_data(conn):
    """Loads all team and car data from Snowflake."""
    if conn is None:
        return pd.DataFrame(), pd.DataFrame()

    teams_query = "SELECT * FROM TEAMS.TEAMS"
    cars_query = "SELECT * FROM CARS.CARS"
    
    try:
        teams_df = pd.read_sql(teams_query, conn)
        cars_df = pd.read_sql(cars_query, conn)
        return teams_df, cars_df
    except Exception as e:
        st.error(f"Failed to load data from Snowflake: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ---- Main Application Logic ----
conn = get_snowflake_connection()
teams_df, cars_df = load_data(conn)

# ---- Data Input for Teams and Cars ----
# Container for adding a new team
with st.container(border=True):
    st.header("Add a Team")
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name")
    with col2:
        budget = st.number_input("Team Budget", min_value=0, value=50000)
    
    # Button to add the new team to the Snowflake table
    if st.button("Add Team"):
        if team_name and conn:
            try:
                cursor = conn.cursor()
                # Insert data into the TEAMS table
                cursor.execute(f"INSERT INTO TEAMS.TEAMS (TEAM_ID, TEAM_NAME, MEMBERS_COUNT, BUDGET) VALUES ('{uuid.uuid4()}', '{team_name}', 0, {budget})")
                conn.commit()
                st.success(f"Team '{team_name}' has been added to Snowflake!")
                st.cache_data.clear() # Clear cache to force data reload
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to add team: {e}")

# Container for adding a new car
with st.container(border=True):
    st.header("Add a Car")
    col3, col4, col5 = st.columns(3)
    with col3:
        car_model = st.text_input("Car Model")
        top_speed = st.slider("Top Speed (km/h)", 100, 400, 250)
    with col4:
        acceleration = st.slider("Acceleration (0-100 km/h)", 1.0, 10.0, 5.0)
    with col5:
        handling = st.slider("Handling", 1.0, 10.0, 5.0)

    # Get the list of available teams for the dropdown from the loaded DataFrame
    team_list = []
    if not teams_df.empty:
        team_list = teams_df['TEAM_NAME'].unique()
    
    if len(team_list) > 0:
        assigned_team = st.selectbox("Assign to Team", team_list)
        # Button to add the new car to the Snowflake table
        if st.button("Add Car"):
            if car_model and conn:
                team_id = teams_df.loc[teams_df['TEAM_NAME'] == assigned_team, 'TEAM_ID'].iloc[0]
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"INSERT INTO CARS.CARS (CAR_ID, CAR_MODEL, TOP_SPEED, ACCELERATION, HANDLING, ASSIGNED_TEAM_ID) VALUES ('{uuid.uuid4()}', '{car_model}', {top_speed}, {acceleration}, {handling}, '{team_id}')")
                    conn.commit()
                    st.success(f"Car '{car_model}' has been added to Snowflake!")
                    st.cache_data.clear() # Clear cache to force data reload
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to add car: {e}")
    else:
        st.warning("Please add at least one team first.")

st.divider()

# ---- Data Display ----
col_view1, col_view2 = st.columns(2)
with col_view1:
    st.header("Registered Teams")
    st.dataframe(teams_df)
with col_view2:
    st.header("Registered Cars")
    st.dataframe(cars_df)

st.divider()

# ---- Race Simulation Logic ----
if st.button("🏁 Start Race", use_container_width=True, type="primary"):
    if teams_df.empty or cars_df.empty:
        st.error("You need at least one team and one car to start the race.")
    elif conn:
        st.header("Race Results")
        
        # Deduct race fee from all participating teams in a single transaction
        try:
            conn.cursor().execute(f"UPDATE TEAMS.TEAMS SET BUDGET = BUDGET - {RACE_FEE}")
            conn.commit()
        except Exception as e:
            st.error(f"Failed to deduct race fees: {e}")
            st.stop()
        
        race_results = []
        with st.spinner("The race is starting..."):
            time.sleep(2) # Simulate race duration
            
            for _, car_row in cars_df.iterrows():
                # Calculate time taken based on car stats with randomness
                time_taken = (100.0 / (car_row['TOP_SPEED'] * (1 + random.uniform(-0.1, 0.1)))) + \
                             (10.0 / (car_row['ACCELERATION'] * (1 + random.uniform(-0.1, 0.1)))) + \
                             (10.0 / (car_row['HANDLING'] * (1 + random.uniform(-0.1, 0.1))))
                
                race_results.append({
                    "Car Model": car_row['CAR_MODEL'],
                    "Team": teams_df.loc[teams_df['TEAM_ID'] == car_row['ASSIGNED_TEAM_ID'], 'TEAM_NAME'].iloc[0],
                    "Time": f"{time_taken:.2f} sec",
                    "Team ID": car_row['ASSIGNED_TEAM_ID']
                })

        # Sort results and determine the winner
        results_df = pd.DataFrame(race_results).sort_values(by="Time")
        winner_info = results_df.iloc[0]
        winner_team_id = winner_info['Team ID']
        winner_team_name = winner_info['Team']
        
        # Add prize money to the winning team's budget
        try:
            conn.cursor().execute(f"UPDATE TEAMS.TEAMS SET BUDGET = BUDGET + {PRIZE_MONEY} WHERE TEAM_ID = '{winner_team_id}'")
            conn.commit()
        except Exception as e:
            st.error(f"Failed to update winner's budget: {e}")

        # Display results and celebration effects
        st.dataframe(results_df.drop('Team ID', axis=1), use_container_width=True)
        st.balloons()
        st.success(f"🎉 Team **{winner_team_name}** wins the race! �")

        st.subheader("Updated Team Budgets")
        st.cache_data.clear() # Clear cache to force data reload
        teams_df, _ = load_data(conn) # Reload data after updates
        st.dataframe(teams_df, use_container_width=True)
