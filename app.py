import streamlit as st
import pandas as pd
import random
import time

# ---- Race Constants ----
RACE_FEE = 1000  # Entry fee for the race
PRIZE_MONEY = 5000  # Prize money for the winner

# ---- Streamlit Page Configuration ----
st.set_page_config(layout="wide", page_title="Race Simulator")

st.title("🏎️ Race Simulator")
st.write("Welcome to the simulator! Enter team and car data to get started.")

# ---- Session State Management ----
# Initialize DataFrames to store team and car data in session state.
# This ensures data persists across user interactions.
if 'teams_df' not in st.session_state:
    st.session_state.teams_df = pd.DataFrame(columns=["TEAM_NAME", "MEMBERS_COUNT", "BUDGET"])
if 'cars_df' not in st.session_state:
    st.session_state.cars_df = pd.DataFrame(columns=["CAR_MODEL", "TOP_SPEED", "ACCELERATION", "HANDLING", "ASSIGNED_TEAM_NAME"])

# ---- Data Input for Teams and Cars ----
# Container for adding a new team
with st.container(border=True):
    st.header("Add a Team")
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name")
    with col2:
        budget = st.number_input("Team Budget", min_value=0, value=50000)
    
    # Button to add the new team to the session state DataFrame
    if st.button("Add Team"):
        if team_name:
            new_team = pd.DataFrame([{"TEAM_NAME": team_name, "MEMBERS_COUNT": 0, "BUDGET": budget}])
            st.session_state.teams_df = pd.concat([st.session_state.teams_df, new_team], ignore_index=True)
            st.success(f"Team '{team_name}' has been added!")

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

    # Get the list of available teams for the dropdown
    team_list = st.session_state.teams_df['TEAM_NAME'].unique()
    if len(team_list) > 0:
        assigned_team = st.selectbox("Assign to Team", team_list)
        # Button to add the new car to the session state DataFrame
        if st.button("Add Car"):
            if car_model:
                new_car = pd.DataFrame([{"CAR_MODEL": car_model, "TOP_SPEED": top_speed, "ACCELERATION": acceleration, "HANDLING": handling, "ASSIGNED_TEAM_NAME": assigned_team}])
                st.session_state.cars_df = pd.concat([st.session_state.cars_df, new_car], ignore_index=True)
                st.success(f"Car '{car_model}' has been added!")
    else:
        st.warning("Please add at least one team first.")

st.divider()

# ---- Data Display and Race Initiation ----
col_view1, col_view2 = st.columns(2)
with col_view1:
    st.header("Registered Teams")
    st.dataframe(st.session_state.teams_df)
with col_view2:
    st.header("Registered Cars")
    st.dataframe(st.session_state.cars_df)

st.divider()

# ---- Race Simulation Logic ----
# Button to start the race simulation
if st.button("🏁 Start Race", use_container_width=True, type="primary"):
    # Check for minimum number of teams and cars
    if st.session_state.teams_df.empty or st.session_state.cars_df.empty:
        st.error("You need at least one team and one car to start the race.")
    else:
        st.header("Race Results")
        
        # Deduct race fee from all participating teams
        st.session_state.teams_df['BUDGET'] -= RACE_FEE

        race_results = []
        with st.spinner("The race is starting..."):
            time.sleep(2) # Simulate race duration
            
            for _, car_row in st.session_state.cars_df.iterrows():
                # Calculate time taken based on car stats with randomness
                time_taken = (100.0 / (car_row['TOP_SPEED'] * (1 + random.uniform(-0.1, 0.1)))) + \
                             (10.0 / (car_row['ACCELERATION'] * (1 + random.uniform(-0.1, 0.1)))) + \
                             (10.0 / (car_row['HANDLING'] * (1 + random.uniform(-0.1, 0.1))))
                
                race_results.append({
                    "Car Model": car_row['CAR_MODEL'],
                    "Team": car_row['ASSIGNED_TEAM_NAME'],
                    "Time": f"{time_taken:.2f} sec"
                })

        # Sort results and determine the winner
        results_df = pd.DataFrame(race_results).sort_values(by="Time")
        winner_team = results_df.iloc[0]['Team']
        
        # Add prize money to the winning team's budget
        st.session_state.teams_df.loc[st.session_state.teams_df['TEAM_NAME'] == winner_team, 'BUDGET'] += PRIZE_MONEY

        # Display results and celebration effects
        st.dataframe(results_df, use_container_width=True)
        st.balloons()
        st.success(f"🎉 Team **{winner_team}** wins the race! 🎉")

        st.subheader("Updated Team Budgets")
        st.dataframe(st.session_state.teams_df, use_container_width=True)
