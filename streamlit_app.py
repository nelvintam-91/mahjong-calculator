import streamlit as st
import pandas as pd
import sqlite3
from streamlit_option_menu import option_menu


# --- RESULT TILES ---
def results_tile(name, amount):
    if amount > 0:
        color = "#10b981"  # Green
    elif amount == 0:
        color = "#808080"  #Grey
    else:
        color = "#ef4444"  # Red
    formatted_amount = f"${abs(amount):,.2f}"
    sign = "+" if amount > 0 else "-" if amount < 0 else ""

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 180;
        ">
            <div style="
                font-size: 14px;
                color: #64748b;
                font-weight: 500;
                margin-bottom: 8px;
            ">{name}</div>
            <div style="
                font-size: 32px;
                color: {color};
                font-weight: 700;
            ">{sign}{formatted_amount}</div>
        </div>
    """, unsafe_allow_html=True)


# --- DATABASE CONNECTION ---
DB_NAME = 'mahjong_app.db'
TABLE_NAME = 'game_log'

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Winner TEXT,
        Loser1 TEXT,
        Loser2 TEXT,
        Loser3 TEXT,
        WinType TEXT,
        Points INTEGER
        )
    ''')
    return conn

conn = get_connection()

# --- DATABASE INTERACTIONS ---
def add_row(conn, winner, loser1, loser2, loser3, win_type, points):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} (Winner, Loser1, Loser2, Loser3, WinType, Points) VALUES (?, ?, ?, ?, ?, ?)", 
            (winner, loser1, loser2, loser3, win_type, points)
        )
        conn.commit()
        st.success(f'Game added successfully. Congrats {winner}!')
    except Exception as e:
        st.error(f"Error adding row: {e}")

def get_data(conn):
    try:
        query = f"SELECT * FROM {TABLE_NAME} ORDER BY ID"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return pd.DataFrame()
    
def del_data(conn):
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    reset_data(conn)

def reset_data(conn):
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Winner TEXT,
        Loser1 TEXT,
        Loser2 TEXT,
        Loser3 TEXT,
        WinType TEXT,
        Points INTEGER
        )
    ''')
    conn.commit()    

def mahjong_remove_last_line():
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {TABLE_NAME} WHERE ID = (SELECT MAX(ID) FROM {TABLE_NAME})"
        )
        conn.commit()
    except Exception as e:
        pass

def award_innocent_bystander(conn):
    try:
        query = f"""
                    WITH Losers AS (SELECT Loser1 AS LoserName
                        FROM {TABLE_NAME} 
                        WHERE WinType = '自摸'
                    UNION ALL
                    SELECT Loser2
                        FROM {TABLE_NAME} 
                        WHERE WinType = '自摸'
                    UNION ALL
                    SELECT Loser3
                        FROM {TABLE_NAME}
                        WHERE WinType = '自摸')
                    ,Losers2 AS (                    
                    SELECT LoserName
                          ,COUNT(LoserName) AS LossCount
                        FROM Losers
                        GROUP BY LoserName)
                    SELECT *
                        FROM Losers2
                        WHERE LossCount = (SELECT MAX(LossCount) FROM Losers2)        
                 """
        df = pd.read_sql(query, conn)
        max_self_draw_loss_count = df.iloc[0]['LossCount']
        max_self_draw_loss_name = df['LoserName'].to_list()
        return max_self_draw_loss_count, max_self_draw_loss_name
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None, None 

def award_arch_nemesis(conn):
    try:
        query = f"""
                    WITH ARCHN1 AS (
                    SELECT Winner
                          ,Loser1
                          ,CASE WHEN Winner < Loser1 THEN Winner || '-' || Loser1 ELSE Loser1 || '-' || Winner END AS alpha_pair
                        FROM {TABLE_NAME} 
                        WHERE WinType <> '自摸')
                    ,ARCHN2 AS (                    
                    SELECT alpha_pair
                          ,COUNT(alpha_pair) AS LossCount
                        FROM ARCHN1
                        GROUP BY alpha_pair)
                    SELECT *
                        FROM ARCHN2
                        WHERE LossCount = (SELECT MAX(LossCount) FROM ARCHN2)    
                 """
        df = pd.read_sql(query, conn)
        max_arch_nemesis_count = df.iloc[0]['LossCount']
        max_arch_nemesis_name = df['alpha_pair'].to_list()
        return max_arch_nemesis_count, max_arch_nemesis_name     
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None, None  


def award_big(conn):
    try:
        query = f"""
                    WITH BIG_PTS AS (
                    SELECT Winner
                          ,AVG(Points) AS Avg_Pts
                        FROM {TABLE_NAME} 
                        GROUP BY Winner)
                    SELECT *
                        FROM BIG_PTS
                        WHERE Avg_Pts = (SELECT MAX(Avg_Pts) FROM BIG_PTS)    
                 """
        df = pd.read_sql(query, conn)
        big_boy_count = df.iloc[0]['Avg_Pts']
        big_boy_name = df['Winner'].to_list()
        return big_boy_count, big_boy_name     
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None, None  

def award_charity(conn):
    try:
        query = f"""
                    WITH CHARITY AS (
                    SELECT Loser1
                          ,COUNT(Loser1) AS Charity_Count
                        FROM {TABLE_NAME} 
                        WHERE WinType <> '自摸'
                        GROUP BY Loser1
                        )
                    SELECT *
                        FROM CHARITY
                        WHERE Charity_Count = (SELECT MAX(Charity_Count) FROM CHARITY)    
                 """
        df = pd.read_sql(query, conn)
        charity_count = df.iloc[0]['Charity_Count']
        charity_name = df['Loser1'].to_list()
        return charity_count, charity_name     
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None, None  


def award_selfdraw(conn):
    try:
        query = f"""
                    WITH SELFDRAW AS (
                    SELECT Winner
                          ,COUNT(Winner) AS SD_Count
                        FROM {TABLE_NAME} 
                        WHERE WinType = '自摸'
                        GROUP BY Winner
                        )
                    SELECT *
                        FROM SELFDRAW
                        WHERE SD_Count = (SELECT MAX(SD_Count) FROM SELFDRAW)    
                 """
        df = pd.read_sql(query, conn)
        self_draw_count = df.iloc[0]['SD_Count']
        self_draw_name = df['Winner'].to_list()
        return self_draw_count, self_draw_name     
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None, None 



# --- PAGE FUNCTIONS ---
def page_home():
    st.title(":material/calculate: Mahjong Calculator")

    st.write("Active Players")
    with st.form("active_player_form"):
        st.pills("Select 4 players",
                       st.session_state['base_player_list_dedup'],
                       key="selected_players",
                       selection_mode='multi',
                       default=None,
                       width='content'
                      )
        confirm_button = st.form_submit_button(label=':material/person_check: Confirm')
        if len(st.session_state['selected_players']) == 4 and confirm_button:
            var1, var2, var3, var4 = st.session_state['selected_players']    
            st.success(f'Active: {var1},{var2},{var3},{var4}')
        else:
            text_filler = 'Please select four players'
            st.error(f':red[{text_filler}]')

    st.divider()
    st.write("Add Game Results")
    with st.form("game_result_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([1,1,1,1])

        if len(st.session_state['selected_players']) != 4:
            players_list = ['(blank)','(blank)','(blank)','(blank)']
        else:
            players_list = st.session_state['selected_players']

        with col1:
            winner = st.pills("Winner",
                        players_list,
                        selection_mode='single',
                        default=None,
                        width='stretch'
                        )

        with col2:
            loser = st.pills("Loser (leave blank if 自摸)",
                        players_list,
                        selection_mode='single',
                        default=None,
                        width='stretch'
                        ) 

        with col3:
            win_type = st.pills("Type",
                        ['出銃','包自摸','自摸'],
                        selection_mode='single',
                        default=None
                        ,width='stretch'
                        )   

        with col4:
            points = st.pills("Points",
                        [3,4,5,6,7,8,9,10],
                        selection_mode='single',
                        default=None,
                        width='stretch'
                        )    
    
        #Submit and delete last game buttons
        colA, colB = st.columns([3,1])
        with colB:
            OK_confirm_game_button = st.form_submit_button(":material/add_box: Add Game")

        with colA:
            DEL_last_game_button = st.form_submit_button(":material/backspace: Undo Last Game")

        if OK_confirm_game_button:
            if winner == loser:
                text_filler = 'Winner cannot have same name as Loser'
                st.error(f':red[{text_filler}]')
            elif win_type == None:
                text_filler = 'Win Type cannot be empty'
                st.error(f':red[{text_filler}]')
            elif points == None:
                text_filler = 'Points cannot be empty'
                st.error(f':red[{text_filler}]')
            elif loser == None and win_type != '自摸':
                text_filler = 'Loser cannot be nameless'
                st.error(f':red[{text_filler}]')
            elif win_type == '自摸':
                loser1 = [x for x in st.session_state['selected_players'] if x != winner][0]
                loser2 = [x for x in st.session_state['selected_players'] if x != winner][1]
                loser3 = [x for x in st.session_state['selected_players'] if x != winner][2]
                add_row(conn, winner, loser1, loser2, loser3, win_type, points)
            else:
                loser1 = loser
                loser2 = None
                loser3 = None        
                add_row(conn, winner, loser1, loser2, loser3, win_type, points)

        if DEL_last_game_button:
            if len(get_data(conn)) > 0:
                mahjong_remove_last_line()
                st.success('Deleted successfully.')
            else:
                st.success('No lines to delete.')

    #Calculation of winnings/losings
    st.divider()
    st.write("Overall Results")
    mahjong_calculator()
    total_amount_df = pd.DataFrame(st.session_state['calculator_master'])
    if len(st.session_state['calculator_master']) > 0:
        overall_results = total_amount_df.groupby('Player')['Amount'].sum().round(2).reset_index()
        overall_results_dict = overall_results.to_dict('records') 
        for x in range(0, len(overall_results_dict)):
            name = overall_results_dict[x]['Player']
            amount = overall_results_dict[x]['Amount']
            results_tile(name, amount)

        st.divider()
        st.write("Game by Game Results")
        st.write(get_data(conn))
        
    else:
        st.success('No games recorded')


        
    #Reset database
    st.divider()
    with st.form("reset_form"):
        RESET_game_button = st.form_submit_button(":material/reset_settings: DOUBLE CLICK TO RESET")
        try:
            if RESET_game_button:
                del_data(conn)
                st.success('Game results have been reset.')
        except:
            pass

        

def page_player_settings():
    st.title(":material/person: Players")

    st.write("Add/Remove Players")
    player_name_label = "Insert Player Name"
    with st.form("add_player_form"):
        col1, col2, col3 = st.columns([7,1,1])
               
        with col1:
            new_player_name = st.text_input(player_name_label,
                                            placeholder=player_name_label,
                                            label_visibility='collapsed')

        with col2:    
            ADD_button_player_name = st.form_submit_button(":material/person_add: Add")

        with col3:
            RESET_button_player_name = st.form_submit_button(":material/reset_settings: Reset")
        
        if ADD_button_player_name:
            new_player_name_cleansed = new_player_name.strip().upper()
            if 'base_player_list' not in st.session_state:
                st.session_state['base_player_list'] = ['NEL','WAI','CAM','BOS','LIL','LIS','AMA','JEN']
            st.session_state['base_player_list'].append(new_player_name_cleansed)
            st.success(f'Welcome to the den, {new_player_name_cleansed}.')

        if RESET_button_player_name:
            st.session_state['base_player_list'] = ['NEL','WAI','CAM','BOS','LIL','LIS','AMA','JEN']
            st.success(f'Reset to default players.')

    st.session_state['base_player_list_dedup'] = list(set(st.session_state['base_player_list']))
    st.session_state['base_player_list_dedup'].sort()
    st.session_state['player_df'] = pd.DataFrame(st.session_state['base_player_list_dedup'], columns=["Name"]) 
    st.dataframe(st.session_state['player_df'])    

def page_point_scoring():
    st.title(":material/settings: Settings")
    
    with st.form("multiplier_form"):
        multiplier = st.selectbox(
                            "Multiplier",
                            [0.10,0.15,0.20],
                            index=None,
                            placeholder='Multiplier'
        )

        confirm_button_points = st.form_submit_button("OK")
        if confirm_button_points:
            st.session_state['multipler'] = multiplier
            st.success(f"Multipler set to ${abs(st.session_state['multipler']):,.2f}")
    st.write(f"Multiplier is currently set to ${abs(st.session_state['multipler']):,.2f}")


    default_scoring = {
        "Points": [3,4,5,6,7,8,9,10],
        "SelfDraw": [4,8,12,16,24,32,48,64],
        "OutRight": [8,16,24,32,48,64,96,128]
    }

    default_scoring_df = pd.DataFrame(default_scoring)
    st.write(default_scoring_df)

def mahjong_calculator():
    st.session_state['calculator_master'] = []
    st.session_state['game_master'] = get_data(conn).to_dict(orient='records')
    for x in range(len(st.session_state['game_master'])):
        winner_x = st.session_state['game_master'][x]['Winner']
        loser1_x = st.session_state['game_master'][x]['Loser1']
        loser2_x = st.session_state['game_master'][x]['Loser2']
        loser3_x = st.session_state['game_master'][x]['Loser3']
        win_type_x = st.session_state['game_master'][x]['WinType']
        points_x = st.session_state['game_master'][x]['Points']

        if win_type_x == '自摸':
            winner_x_entry = {'Player': winner_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*3.00}
            loser1_x_entry = {'Player': loser1_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*-1.00}
            loser2_x_entry = {'Player': loser2_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*-1.00}
            loser3_x_entry = {'Player': loser3_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*-1.00}
            st.session_state['calculator_master'].append(winner_x_entry)
            st.session_state['calculator_master'].append(loser1_x_entry)
            st.session_state['calculator_master'].append(loser2_x_entry)
            st.session_state['calculator_master'].append(loser3_x_entry)
        elif win_type_x == '包自摸':
            winner_x_entry = {'Player': winner_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*3.00}
            loser1_x_entry = {'Player': loser1_x, 'Amount': default_scoring_df.iloc[points_x-3]['SelfDraw']*st.session_state['multipler']*-3.00}
            st.session_state['calculator_master'].append(winner_x_entry)
            st.session_state['calculator_master'].append(loser1_x_entry)
        else:
            winner_x_entry = {'Player': winner_x, 'Amount': default_scoring_df.iloc[points_x-3]['OutRight']*st.session_state['multipler']*1.00}
            loser1_x_entry = {'Player': loser1_x, 'Amount': default_scoring_df.iloc[points_x-3]['OutRight']*st.session_state['multipler']*-1.00}
            st.session_state['calculator_master'].append(winner_x_entry)
            st.session_state['calculator_master'].append(loser1_x_entry)

def page_awards():
    st.title(":material/crown: Awards")
    st.divider()

    #Innocent Bystander
    max_self_draw_loss_count, max_self_draw_loss_name_list = award_innocent_bystander(conn)
    max_self_draw_loss_name = ''
    for x in range(0,len(max_self_draw_loss_name_list)):
        if x == 0:
            max_self_draw_loss_name = max_self_draw_loss_name_list[x]
        else:
            max_self_draw_loss_name += f', {max_self_draw_loss_name_list[x]}'

    st.subheader(':material/assist_walker: Innocent Bystander')
    st.write(f'Number of Games: {max_self_draw_loss_count} | Players: {max_self_draw_loss_name}')
    st.divider()

    #Arch Nemesis
    max_arch_nemesis_count, max_arch_nemesis_name_list = award_arch_nemesis(conn)
    max_arch_nemesis_name = ''
    for x in range(0,len(max_arch_nemesis_name_list)):
        if x == 0:
            max_arch_nemesis_name = max_arch_nemesis_name_list[x]
        else:
            max_arch_nemesis_name += f', {max_arch_nemesis_name_list[x]}'   
    st.subheader(':material/sports_kabaddi: Arch Nemesis')
    st.write(f'Number of Games: {max_arch_nemesis_count} | Players: {max_arch_nemesis_name}')
    st.divider()

    #Go Big or Go Home
    big_boy_count, big_boy_name_list = award_big(conn)
    big_boy_name = ''
    for x in range(0,len(big_boy_name_list)):
        if x == 0:
            big_boy_name = big_boy_name_list[x]
        else:
            big_boy_name += f', {big_boy_name_list[x]}'   
    st.subheader(':material/trending_up: Go Big or Go Home')
    st.write(f'Average Points: {big_boy_count:,.2f} | Players: {big_boy_name}')
    st.divider()

    #Charity Champion
    charity_count, charity_name_list = award_charity(conn)
    charity_name = ''
    for x in range(0,len(charity_name_list)):
        if x == 0:
            charity_name = charity_name_list[x]
        else:
            charity_name += f', {charity_name_list[x]}'   
    st.subheader(':material/volunteer_activism: Charity Champion')
    st.write(f'Games donated: {charity_count:,.2f} | Players: {charity_name}')   
    st.divider()

    #Self Draw King/Queen
    self_draw_count, self_draw_name_list = award_selfdraw(conn)
    self_draw_name = ''
    for x in range(0,len(self_draw_name_list)):
        if x == 0:
            self_draw_name = self_draw_name_list[x]
        else:
            self_draw_name += f', {self_draw_name_list[x]}'   
    st.subheader(':material/self_improvement: Self Draw King/Queen')
    st.write(f'Games won: {self_draw_count:,.2f} | Players: {self_draw_name}')   





# --- MAIN APP ---
def main():
    selected = option_menu(
        menu_title=None,
        options=["Calc", "User", "Menu", "Award"],
        icons=["calculator", "person", "gear", "award"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#b5b0b0"},
            "icon": {"color": "#043801", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#787474",
            },
            "nav-link-selected": {"background-color": "green"},
        }
    )

    if selected == "Calc":
        page_home()
        st.divider()
        st.caption('V1.1.0 © Nelvin Tam')
    elif selected == "User":
        page_player_settings()
        st.divider()
        st.caption('V1.1.0 © Nelvin Tam')
    elif selected == "Menu":
        page_point_scoring()
        st.divider()
        st.caption('V1.1.0 © Nelvin Tam')
    elif selected == "Award":
        page_awards()
        st.divider()
        st.caption('V1.1.0 © Nelvin Tam')
    

if __name__ == "__main__":
    #Set up session state tables
    if 'base_player_list_dedup' not in st.session_state:
        st.session_state['base_player_list_dedup'] = ['NEL','WAI','CAM','BOS','LIL','LIS','AMA','JEN']
    st.session_state['base_player_list_dedup'].sort()
    if 'base_player_list' not in st.session_state:
        st.session_state['base_player_list'] = st.session_state['base_player_list_dedup'] 
    if 'game_master' not in st.session_state:
        st.session_state['game_master'] = []  
    if 'multipler' not in st.session_state:
        st.session_state['multipler'] = 0.15
    if 'calculator_master' not in st.session_state:
        st.session_state['calculator_master'] = []  



    #Default scoring system
    default_scoring = {
        "Points": [3,4,5,6,7,8,9,10],
        "SelfDraw": [4,8,12,16,24,32,48,64],
        "OutRight": [8,16,24,32,48,64,96,128]
    }
    default_scoring_df = pd.DataFrame(default_scoring)

    main()
