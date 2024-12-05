from decimal import Decimal

import pycountry

MIN_BAT_COUNT = 2
MIN_KEEPER_COUNT = 1
MIN_ALL_R_COUNT = 1
MIN_BOW_COUNT = 2

state_code_to_name = {
    "IN-AP": "Andhra Pradesh",
    "IN-AR": "Arunachal Pradesh",
    "IN-AS": "Assam",
    "IN-BR": "Bihar",
    "IN-CT": "Chhattisgarh",
    "IN-GA": "Goa",
    "IN-GJ": "Gujarat",
    "IN-HR": "Haryana",
    "IN-HP": "Himachal Pradesh",
    "IN-JH": "Jharkhand",
    "IN-KA": "Karnataka",
    "IN-KL": "Kerala",
    "IN-MP": "Madhya Pradesh",
    "IN-MH": "Maharashtra",
    "IN-MN": "Manipur",
    "IN-ML": "Meghalaya",
    "IN-MZ": "Mizoram",
    "IN-NL": "Nagaland",
    "IN-OR": "Odisha",
    "IN-PB": "Punjab",
    "IN-RJ": "Rajasthan",
    "IN-SK": "Sikkim",
    "IN-TN": "Tamil Nadu",
    "IN-TG": "Telangana",
    "IN-TR": "Tripura",
    "IN-UP": "Uttar Pradesh",
    "IN-UT": "Uttarakhand",
    "IN-WB": "West Bengal",
    "IN-AN": "Andaman and Nicobar Islands",
    "IN-CH": "Chandigarh",
    "IN-DH": "Dadra and Nagar Haveli and Daman and Diu",
    "IN-DL": "Delhi",
    "IN-JK": "Jammu and Kashmir",
    "IN-LA": "Ladakh",
    "IN-LD": "Lakshadweep",
    "IN-PY": "Puducherry"
}

alpha_2_country_codes = {}

for country in pycountry.countries:
    alpha_2_country_codes[country.alpha_2] = country.name

country_code_to_states = {
    'IN': set(state_code_to_name.keys())
}

MATCH_STATUS_NOT_STARTED = "not_started"
MATCH_STATUS_STARTED = "started"
MATCH_STATUS_COMPLETED = "completed"

PLAYER_ROLE_BATSMAN = "batsman"
PLAYER_ROLE_KEEPER = "keeper"
PLAYER_ROLE_BOWLER = "bowler"
PLAYER_ROLE_ALLROUNDER = "all_rounder"

PLATFORM_FEES = Decimal("0.12")
MAX_USER_TEAM_COUNT = 10
MEGA_USER_TEAM_COUNT = 10
HEAD_TO_HEAD_USER_TEAM_COUNT = 1
TAKES_ALL_USER_TEAM_COUNT = 2

ADVANCED_TEAM_CREATE_DAYS = 3

boolean_mapping = {
    'true': True,
    'false': False,
}

CONTEST_STATUS_NOT_STARTED = "not_started"
CONTEST_STATUS_STARTED = "started"
CONTEST_STATUS_COMPLETED = "completed"
CONTEST_STATUS_CANCELLED = "cancelled"

REWARD_PENDING = 'pending'
REWARD_APPLIED = 'applied'
RC_WALLET = 'wallet_balance'
RC_CONTEST = 'join_contest'
RC_SIGNUP = 'signup'
