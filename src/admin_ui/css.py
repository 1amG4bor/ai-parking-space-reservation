# pylint: disable=trailing-whitespace
def get_custom_style():
    """Return custom CSS styles for the admin UI."""

    return """
    <style>
    /* Custom Navbar style*/
    .stAppHeader {{ background-color: #FCCB36; color: black; }}

    /* Green Button Styling */
    .st-key-success-btn .stButton>button {{
        background-color: green;
        color: white;
    }}
    .st-key-success-btn .stButton>button:disabled {{
        background-color: lightgrey;
        cursor: not-allowed;
    }}
    
    /* Red Button Styling */
    .st-key-danger-btn .stButton>button {{
        background-color: red;
        color: white;
    }}
    .st-key-danger-btn .stButton>button:disabled {{ 
        background-color: grey;
        cursor: not-allowed;
    }}

    /* Left aligned columns */
    div[data-testid="stHorizontalBlock"] .stColumn {{
        display: flex;
        justify-content: flex-start;
    }}

    /* Reservation status styling */
    .reservation-status {{
        width: fit-content; padding: 0 20px;
        border: 1px solid gray;
        border-radius: 5px;
        padding: 6px 42px;
        margin-bottom: 10px;
        font-weight: bold;
    }}

    /* Data Fetch in-progress */
    

</style>
"""
