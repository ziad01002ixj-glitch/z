import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import traceback
import random
import itertools
import bs4  # أو from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
import hashlib

BASE = "http://139.99.63.204"
AJAX_PATH = "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE_URL = BASE + "/ints/login"
LOGIN_POST_URL = BASE + "/ints/signin"
# ======================
# 🖥️ إعداد لوحات (2 لوحة)
# ======================
# 1. الإعدادات الجديدة (تأكد منها)
# ======================
# 🖥️ إعداد اللوحة بنظام الـ API
# ======================

# ======================
# 🖥️ إعداد لوحات (4 لوحات) - تم إضافة MSI Panel
# ======================
DASHBOARD_CONFIGS = [
    {
        "name": "Ziad Panel (Old API)",
        "api_url": "http://147.135.212.197/crapi/st/viewstats",
        "token": "RFJVRkhBUzR8aXdrZE-LioVWlWREkIFSXk9ShoBOWIR2U1WKXWOEhg==",
        "type": "old_list",
        "records": 10,
        "session": requests.Session(),
        "is_logged_in": True
    },
    {
        "name": "Ziad Panel (New API)",
        "api_url": "http://147.135.212.197/crapi/bo/viewstats",
        "token": "RE5YRDRSQlWHV5NYiE-KSoVTknyJf3ldWY-JR2GWkF94dGxSRI-I",
        "type": "new_json",
        "records": 10,
        "session": requests.Session(),
        "is_logged_in": True
    },
    {
        "name": "New Dashboard API",
        "api_url": "http://51.77.216.195/crapi/dgroup/viewstats?token=SEFTNH9pk3NGdmt7aGGRSWqUZEZBYJiJQomEZmaReX2Dh4VE",
        "type": "new_format",
        "records": 10,
        "session": requests.Session(),
        "is_logged_in": True
    },
    {
        "name": "MSI Panel",
        "base_url": "http://145.239.130.45/ints",
        "login_url": "http://145.239.130.45/ints/login",
        "ajax_url": "http://145.239.130.45/ints/agent/res/data_smscdr.php",
        "username": "o_k_60",
        "password": "01002460089",
        "type": "msi_panel",
        "records": 50,
        "session": requests.Session(),
        "is_logged_in": False,
        "login_retries": 0
    },
    {
        "name": "fly palen",
        "base_url": "http://193.70.33.154/ints",
        "login_url": "http://193.70.33.154/ints/login",
        "ajax_url": "http://193.70.33.154/ints/agent/res/data_smscdr.php",
        "username": "o_k_60",
        "password": "01002460089",
        "type": "msi_panel",
        "records": 50,
        "session": requests.Session(),
        "is_logged_in": False,
        "login_retries": 0
    },
    {
    "name": "IMS Panel",
    "base_url": "https://imssms.org",
    "login_page_url": "https://imssms.org/login",
    "login_post_url": "https://imssms.org/signin",
    "dashboard_url": "https://imssms.org/agent/SMSCDRReports",
    "ajax_url": "https://imssms.org/agent/res/data_smscdr.php",
    "username": "ZIAD_ESAA",
    "password": "ESAA010024600",
    "type": "ims_panel",
    "records": 50,
    "session": requests.Session(),
    "is_logged_in": False,
    "login_retries": 0,
    "phpsessid": None,
    "sesskey": None,
    "last_login_time": 0,
    "login_interval": 120,      # تجديد الدخول كل 120 ثانية
    "last_fetch_time": None         # معرف الموضوع (اختياري)
}
]  # <-- تأكد إن القوس هنا موجود ومغلق صح

# ======================
# 🚀 تهيئة الـ API والـ Headers
# ======================
# ======================
# 🚀 تهيئة الـ API والـ Headers
# ======================

COMMON_HEADERS = {
    "User-Agent": "Albrans-API-Monitor/2.0",
    "Accept": "application/json"
}

for dash in DASHBOARD_CONFIGS:
    dash["session"].headers.update(COMMON_HEADERS)
    
    # فقط للوحات الـ API العادية نضبط ajax_url
    if dash.get('type') not in ('msi_panel', 'ims_panel'):
        dash["ajax_url"] = dash.get("api_url", "")   # <-- أضف مسافة بادئة هنا
    
    print(f"[{dash['name']}] 🚀 نظام المراقبة جاهز...")

# ======================
# ⚙️ إعدادات البوت والتحكم
# ======================
BOT_TOKEN = "6166380598:AAEpc0diJNzm6Qm6CjjEiq4gjcuICE4PYBw"
CHAT_IDS = ["-1003877396414"]
ADMIN_IDS = [5841778955]

REFRESH_INTERVAL = 7
TIMEOUT = 5  # الـ API سريع مش محتاج 100 ثانية
MAX_RETRIES = 5
RETRY_DELAY = 5

# الفهارس بناءً على القائمة اللي السيرفر بيبعتها [Service, Num, Msg, Date]
IDX_SERVICE = 0  # الخدمة
IDX_NUMBER = 1   # الرقم
IDX_SMS = 2      # الرسالة
IDX_DATE = 3     # التاريخ

DB_PATH = "bot_database.db"
SENT_MESSAGES_FILE = "sent_messages.json"
BOT_ACTIVE = True




if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set in Secrets (Environment Variables)")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")


COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "US"),
    "7": ("Russia", "🇷🇺", "RU"),
    "20": ("Egypt", "🇪🇬", "EG"),
    "27": ("South Africa", "🇿🇦", "ZA"),
    "30": ("Greece", "🇬🇷", "GR"),
    "31": ("Netherlands", "🇳🇱", "NL"),
    "32": ("Belgium", "🇧🇪", "BE"),
    "33": ("France", "🇫🇷", "FR"),
    "34": ("Spain", "🇪🇸", "ES"),
    "36": ("Hungary", "🇭🇺", "HU"),
    "39": ("Italy", "🇮🇹", "IT"),
    "40": ("Romania", "🇷🇴", "RO"),
    "41": ("Switzerland", "🇨🇭", "CH"),
    "43": ("Austria", "🇦🇹", "AT"),
    "44": ("United Kingdom", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DK"),
    "46": ("Sweden", "🇸🇪", "SE"),
    "47": ("Norway", "🇳🇴", "NO"),
    "48": ("Poland", "🇵🇱", "PL"),
    "49": ("Germany", "🇩🇪", "DE"),

    "51": ("Peru", "🇵🇪", "PE"),
    "52": ("Mexico", "🇲🇽", "MX"),
    "53": ("Cuba", "🇨🇺", "CU"),
    "54": ("Argentina", "🇦🇷", "AR"),
    "55": ("Brazil", "🇧🇷", "BR"),
    "56": ("Chile", "🇨🇱", "CL"),
    "57": ("Colombia", "🇨🇴", "CO"),
    "58": ("Venezuela", "🇻🇪", "VE"),

    "60": ("Malaysia", "🇲🇾", "MY"),
    "61": ("Australia", "🇦🇺", "AU"),
    "62": ("Indonesia", "🇮🇩", "ID"),
    "63": ("Philippines", "🇵🇭", "PH"),
    "64": ("New Zealand", "🇳🇿", "NZ"),
    "65": ("Singapore", "🇸🇬", "SG"),
    "66": ("Thailand", "🇹🇭", "TH"),

    "81": ("Japan", "🇯🇵", "JP"),
    "82": ("South Korea", "🇰🇷", "KR"),
    "84": ("Vietnam", "🇻🇳", "VN"),
    "86": ("China", "🇨🇳", "CN"),

    "90": ("Turkey", "🇹🇷", "TR"),
    "91": ("India", "🇮🇳", "IN"),
    "92": ("Pakistan", "🇵🇰", "PK"),
    "93": ("Afghanistan", "🇦🇫", "AF"),
    "94": ("Sri Lanka", "🇱🇰", "LK"),
    "95": ("Myanmar", "🇲🇲", "MM"),
    "98": ("Iran", "🇮🇷", "IR"),

    "211": ("South Sudan", "🇸🇸", "SS"),
    "212": ("Morocco", "🇲🇦", "MA"),
    "213": ("Algeria", "🇩🇿", "DZ"),
    "216": ("Tunisia", "🇹🇳", "TN"),
    "218": ("Libya", "🇱🇾", "LY"),

    "220": ("Gambia", "🇬🇲", "GM"),
    "221": ("Senegal", "🇸🇳", "SN"),
    "222": ("Mauritania", "🇲🇷", "MR"),
    "223": ("Mali", "🇲🇱", "ML"),
    "224": ("Guinea", "🇬🇳", "GN"),
    "225": ("Ivory Coast", "🇨🇮", "CI"),
    "226": ("Burkina Faso", "🇧🇫", "BF"),
    "227": ("Niger", "🇳🇪", "NE"),
    "228": ("Togo", "🇹🇬", "TG"),
    "229": ("Benin", "🇧🇯", "BJ"),

    "230": ("Mauritius", "🇲🇺", "MU"),
    "231": ("Liberia", "🇱🇷", "LR"),
    "232": ("Sierra Leone", "🇸🇱", "SL"),
    "233": ("Ghana", "🇬🇭", "GH"),
    "234": ("Nigeria", "🇳🇬", "NG"),
    "235": ("Chad", "🇹🇩", "TD"),
    "236": ("Central African Rep", "🇨🇫", "CF"),
    "237": ("Cameroon", "🇨🇲", "CM"),
    "238": ("Cape Verde", "🇨🇻", "CV"),
    "239": ("Sao Tome", "🇸🇹", "ST"),
    "240": ("Equatorial Guinea", "🇬🇶", "GQ"),
    "241": ("Gabon", "🇬🇦", "GA"),
    "242": ("Congo", "🇨🇬", "CG"),
    "243": ("DR Congo", "🇨🇩", "CD"),
    "244": ("Angola", "🇦🇴", "AO"),
    "245": ("Guinea-Bissau", "🇬🇼", "GW"),

    "248": ("Seychelles", "🇸🇨", "SC"),
    "249": ("Sudan", "🇸🇩", "SD"),
    "250": ("Rwanda", "🇷🇼", "RW"),
    "251": ("Ethiopia", "🇪🇹", "ET"),
    "252": ("Somalia", "🇸🇴", "SO"),
    "253": ("Djibouti", "🇩🇯", "DJ"),
    "254": ("Kenya", "🇰🇪", "KE"),
    "255": ("Tanzania", "🇹🇿", "TZ"),
    "256": ("Uganda", "🇺🇬", "UG"),
    "257": ("Burundi", "🇧🇮", "BI"),
    "258": ("Mozambique", "🇲🇿", "MZ"),
    "260": ("Zambia", "🇿🇲", "ZM"),
    "261": ("Madagascar", "🇲🇬", "MG"),
    "262": ("Reunion", "🇷🇪", "RE"),
    "263": ("Zimbabwe", "🇿🇼", "ZW"),
    "264": ("Namibia", "🇳🇦", "NA"),
    "265": ("Malawi", "🇲🇼", "MW"),
    "266": ("Lesotho", "🇱🇸", "LS"),
    "267": ("Botswana", "🇧🇼", "BW"),
    "268": ("Eswatini", "🇸🇿", "SZ"),
    "269": ("Comoros", "🇰🇲", "KM"),

    "350": ("Gibraltar", "🇬🇮", "GI"),
    "351": ("Portugal", "🇵🇹", "PT"),
    "352": ("Luxembourg", "🇱🇺", "LU"),
    "353": ("Ireland", "🇮🇪", "IE"),
    "354": ("Iceland", "🇮🇸", "IS"),
    "355": ("Albania", "🇦🇱", "AL"),
    "356": ("Malta", "🇲🇹", "MT"),
    "357": ("Cyprus", "🇨🇾", "CY"),
    "358": ("Finland", "🇫🇮", "FI"),
    "359": ("Bulgaria", "🇧🇬", "BG"),
    "370": ("Lithuania", "🇱🇹", "LT"),
    "371": ("Latvia", "🇱🇻", "LV"),
    "372": ("Estonia", "🇪🇪", "EE"),
    "373": ("Moldova", "🇲🇩", "MD"),
    "374": ("Armenia", "🇦🇲", "AM"),
    "375": ("Belarus", "🇧🇾", "BY"),
    "376": ("Andorra", "🇦🇩", "AD"),
    "377": ("Monaco", "🇲🇨", "MC"),
    "378": ("San Marino", "🇸🇲", "SM"),
    "380": ("Ukraine", "🇺🇦", "UA"),
    "381": ("Serbia", "🇷🇸", "RS"),
    "382": ("Montenegro", "🇲🇪", "ME"),
    "383": ("Kosovo", "🇽🇰", "XK"),
    "385": ("Croatia", "🇭🇷", "HR"),
    "386": ("Slovenia", "🇸🇮", "SI"),
    "387": ("Bosnia", "🇧🇦", "BA"),
    "389": ("North Macedonia", "🇲🇰", "MK"),

    "420": ("Czech Republic", "🇨🇿", "CZ"),
    "421": ("Slovakia", "🇸🇰", "SK"),
    "423": ("Liechtenstein", "🇱🇮", "LI"),

    "500": ("Falkland Islands", "🇫🇰", "FK"),
    "501": ("Belize", "🇧🇿", "BZ"),
    "502": ("Guatemala", "🇬🇹", "GT"),
    "503": ("El Salvador", "🇸🇻", "SV"),
    "504": ("Honduras", "🇭🇳", "HN"),
    "505": ("Nicaragua", "🇳🇮", "NI"),
    "506": ("Costa Rica", "🇨🇷", "CR"),
    "507": ("Panama", "🇵🇦", "PA"),
    "509": ("Haiti", "🇭🇹", "HT"),

    "591": ("Bolivia", "🇧🇴", "BO"),
    "592": ("Guyana", "🇬🇾", "GY"),
    "593": ("Ecuador", "🇪🇨", "EC"),
    "595": ("Paraguay", "🇵🇾", "PY"),
    "597": ("Suriname", "🇸🇷", "SR"),
    "598": ("Uruguay", "🇺🇾", "UY"),

    "670": ("Timor-Leste", "🇹🇱", "TL"),
    "673": ("Brunei", "🇧🇳", "BN"),
    "674": ("Nauru", "🇳🇷", "NR"),
    "675": ("Papua New Guinea", "🇵🇬", "PG"),
    "676": ("Tonga", "🇹🇴", "TO"),
    "677": ("Solomon Islands", "🇸🇧", "SB"),
    "678": ("Vanuatu", "🇻🇺", "VU"),
    "679": ("Fiji", "🇫🇯", "FJ"),
    "680": ("Palau", "🇵🇼", "PW"),
    "685": ("Samoa", "🇼🇸", "WS"),
    "686": ("Kiribati", "🇰🇮", "KI"),
    "687": ("New Caledonia", "🇳🇨", "NC"),
    "688": ("Tuvalu", "🇹🇻", "TV"),
    "689": ("French Polynesia", "🇵🇫", "PF"),
    "691": ("Micronesia", "🇫🇲", "FM"),
    "692": ("Marshall Islands", "🇲🇭", "MH"),

    "850": ("North Korea", "🇰🇵", "KP"),
    "852": ("Hong Kong", "🇭🇰", "HK"),
    "853": ("Macau", "🇲🇴", "MO"),
    "855": ("Cambodia", "🇰🇭", "KH"),
    "856": ("Laos", "🇱🇦", "LA"),

    "960": ("Maldives", "🇲🇻", "MV"),
    "961": ("Lebanon", "🇱🇧", "LB"),
    "962": ("Jordan", "🇯🇴", "JO"),
    "963": ("Syria", "🇸🇾", "SY"),
    "964": ("Iraq", "🇮🇶", "IQ"),
    "965": ("Kuwait", "🇰🇼", "KW"),
    "966": ("Saudi Arabia", "🇸🇦", "SA"),
    "967": ("Yemen", "🇾🇪", "YE"),
    "968": ("Oman", "🇴🇲", "OM"),
    "970": ("Palestine", "🇵🇸", "PS"),
    "971": ("UAE", "🇦🇪", "AE"),
    "972": ("Israel", "🇮🇱", "IL"),
    "973": ("Bahrain", "🇧🇭", "BH"),
    "974": ("Qatar", "🇶🇦", "QA"),
    "975": ("Bhutan", "🇧🇹", "BT"),
    "976": ("Mongolia", "🇲🇳", "MN"),
    "977": ("Nepal", "🇳🇵", "NP"),

    "992": ("Tajikistan", "🇹🇯", "TJ"),
    "993": ("Turkmenistan", "🇹🇲", "TM"),
    "994": ("Azerbaijan", "🇦🇿", "AZ"),
    "995": ("Georgia", "🇬🇪", "GE"),
    "996": ("Kyrgyzstan", "🇰🇬", "KG"),
    "998": ("Uzbekistan", "🇺🇿", "UZ"),
}


# ======================
# 🎌 قاموس الأعلام المتحركة (بصيغة HTML) – هذا القاموس أرسلته أنت
# ======================
COUNTRY_MAP = {
    # Africa
    "20": ("EG", "<tg-emoji emoji-id='5222161185138292290'>🇪🇬</tg-emoji>"),  # Egypt
    "27": ("ZA", "<tg-emoji emoji-id='5224696216570309138'>🇿🇦</tg-emoji>"),  # South Africa
    "211": ("SS", "<tg-emoji emoji-id='5224618146949773268'>🇸🇸</tg-emoji>"),  # South Sudan
    "212": ("MA", "<tg-emoji emoji-id='5224530035695693965'>🇲🇦</tg-emoji>"),  # Morocco
    "213": ("DZ", "<tg-emoji emoji-id='5224260376174015500'>🇩🇿</tg-emoji>"),  # Algeria
    "216": ("TN", "<tg-emoji emoji-id='5221991375016310330'>🇹🇳</tg-emoji>"),  # Tunisia
    "218": ("LY", "<tg-emoji emoji-id='5222194286451242896'>🇱🇾</tg-emoji>"),  # Libya
    "220": ("GM", "<tg-emoji emoji-id='5221949872747330159'>🇬🇲</tg-emoji>"),  # Gambia
    "221": ("SN", "<tg-emoji emoji-id='5224358988623130949'>🇸🇳</tg-emoji>"),  # Senegal
    "222": ("MR", "<tg-emoji emoji-id='5224269666188274723'>🇲🇷</tg-emoji>"),  # Mauritania
    "223": ("ML", "<tg-emoji emoji-id='5224322352552096671'>🇲🇱</tg-emoji>"),  # Mali
    "224": ("GN", "<tg-emoji emoji-id='5222337588035073000'>🇬🇳</tg-emoji>"),  # Guinea
    "225": ("CI", "<tg-emoji emoji-id='5224455152940886669'>🇨🇮</tg-emoji>"),  # Ivory Coast
    "226": ("BF", "🇧🇫"),  # Burkina Faso (Normal Flag)
    "227": ("NE", "<tg-emoji emoji-id='5222099049846420864'>🇳🇪</tg-emoji>"),  # Niger
    "228": ("TG", "<tg-emoji emoji-id='5222408051268532030'>🇹🇬</tg-emoji>"),  # Togo
    "229": ("BJ", "<tg-emoji emoji-id='5224515905253291409'>🇧🇯</tg-emoji>"),  # Benin
    "230": ("MU", "<tg-emoji emoji-id='5224393700548814960'>🇲🇺</tg-emoji>"),  # Mauritius
    "231": ("LR", "<tg-emoji emoji-id='5224420995065983217'>🇱🇷</tg-emoji>"),  # Liberia
    "232": ("SL", "<tg-emoji emoji-id='5224420995065983217'>🇸🇱</tg-emoji>"),  # Sierra Leone
    "233": ("GH", "<tg-emoji emoji-id='5224511339703056124'>🇬🇭</tg-emoji>"),  # Ghana
    "234": ("NG", "<tg-emoji emoji-id='5224723614166691638'>🇳🇬</tg-emoji>"),  # Nigeria
    "235": ("TD", "<tg-emoji emoji-id='5222060468155204001'>🇹🇩</tg-emoji>"),  # Chad
    "236": ("CF", "<tg-emoji emoji-id='5222060468155204001'>🇨🇫</tg-emoji>"),  # Central African Republic
    "237": ("CM", "<tg-emoji emoji-id='5222234560359577687'>🇨🇲</tg-emoji>"),  # Cameroon
    "238": ("CV", "<tg-emoji emoji-id='5224567367551428669'>🇨🇻</tg-emoji>"),  # Cape Verde
    "239": ("ST", "<tg-emoji emoji-id='5221953304426198315'>🇸🇹</tg-emoji>"),  # Sao Tome
    "240": ("GQ", "<tg-emoji emoji-id='5224455152940886669'>🇬🇶</tg-emoji>"),  # Equatorial Guinea
    "241": ("GA", "<tg-emoji emoji-id='5222152195771742239'>🇬🇦</tg-emoji>"),  # Gabon
    "242": ("CG", "<tg-emoji emoji-id='5224490444687158452'>🇨🇬</tg-emoji>"),  # Congo
    "243": ("CD", "<tg-emoji emoji-id='5224490444687158452'>🇨🇩</tg-emoji>"),  # DR Congo
    "244": ("AO", "<tg-emoji emoji-id='5224379767674907895'>🇦🇴</tg-emoji>"),  # Angola
    "245": ("GW", "<tg-emoji emoji-id='5224705704153066489'>🇬🇼</tg-emoji>"),  # Guinea-Bissau
    "248": ("SC", "<tg-emoji emoji-id='5224467496676896871'>🇸🇨</tg-emoji>"),  # Seychelles
    "249": ("SD", "<tg-emoji emoji-id='5224372990216514135'>🇸🇩</tg-emoji>"),  # Sudan
    "250": ("RW", "<tg-emoji emoji-id='5222449197055227754'>🇷🇼</tg-emoji>"),  # Rwanda
    "251": ("ET", "<tg-emoji emoji-id='5224467805914542024'>🇪🇹</tg-emoji>"),  # Ethiopia
    "252": ("SO", "<tg-emoji emoji-id='5222370504664428325'>🇸🇴</tg-emoji>"),  # Somalia
    "253": ("DJ", "<tg-emoji emoji-id='5221991375016310330'>🇩🇯</tg-emoji>"),  # Djibouti
    "254": ("KE", "<tg-emoji emoji-id='5222089648163009103'>🇰🇪</tg-emoji>"),  # Kenya
    "255": ("TZ", "<tg-emoji emoji-id='5224397364155923150'>🇹🇿</tg-emoji>"),  # Tanzania
    "256": ("UG", "<tg-emoji emoji-id='5222464040462200940'>🇺🇬</tg-emoji>"),  # Uganda
    "257": ("BI", "<tg-emoji emoji-id='5224490444687158452'>🇧🇮</tg-emoji>"),  # Burundi
    "258": ("MZ", "<tg-emoji emoji-id='5222470388423864826'>🇲🇿</tg-emoji>"),  # Mozambique
    "260": ("ZM", "<tg-emoji emoji-id='5224646626877911277'>🇿🇲</tg-emoji>"),  # Zambia
    "261": ("MG", "<tg-emoji emoji-id='5222042605386217334'>🇲🇬</tg-emoji>"),  # Madagascar
    "262": ("RE", "<tg-emoji emoji-id='5222042605386217334'>🇷🇪</tg-emoji>"),  # Reunion
    "263": ("ZW", "<tg-emoji emoji-id='5222060442385397848'>🇿🇼</tg-emoji>"),  # Zimbabwe
    "264": ("NA", "<tg-emoji emoji-id='5224690826386351746'>🇳🇦</tg-emoji>"),  # Namibia
    "265": ("MW", "<tg-emoji emoji-id='5222470435668505656'>🇲🇼</tg-emoji>"),  # Malawi
    "266": ("LS", "<tg-emoji emoji-id='5224660718665607511'>🇱🇸</tg-emoji>"),  # Lesotho
    "267": ("BW", "<tg-emoji emoji-id='5224570532942329532'>🇧🇼</tg-emoji>"),  # Botswana
    "268": ("SZ", "<tg-emoji emoji-id='5224269666188274723'>🇸🇿</tg-emoji>"),  # Eswatini
    "269": ("KM", "<tg-emoji emoji-id='5222398735484466247'>🇰🇲</tg-emoji>"),  # Comoros

    # Asia
    "60": ("MY", "<tg-emoji emoji-id='5224312886444174057'>🇲🇾</tg-emoji>"),  # Malaysia
    "62": ("ID", "<tg-emoji emoji-id='5224405893960969756'>🇮🇩</tg-emoji>"),  # Indonesia
    "63": ("PH", "<tg-emoji emoji-id='5222065042295376892'>🇵🇭</tg-emoji>"),  # Philippines
    "64": ("NZ", "<tg-emoji emoji-id='5224573595254009705'>🇳🇿</tg-emoji>"),  # New Zealand
    "65": ("SG", "<tg-emoji emoji-id='5224194023224257181'>🇸🇬</tg-emoji>"),  # Singapore
    "66": ("TH", "<tg-emoji emoji-id='5224638530864556281'>🇹🇭</tg-emoji>"),  # Thailand
    "81": ("JP", "<tg-emoji emoji-id='5222390089715299207'>🇯🇵</tg-emoji>"),  # Japan
    "82": ("KR", "<tg-emoji emoji-id='5222345550904439270'>🇰🇷</tg-emoji>"),  # South Korea
    "84": ("VN", "<tg-emoji emoji-id='5222359651282071925'>🇻🇳</tg-emoji>"),  # Vietnam
    "86": ("CN", "<tg-emoji emoji-id='5224435456220868088'>🇨🇳</tg-emoji>"),  # China
    "90": ("TR", "<tg-emoji emoji-id='5224601903383457698'>🇹🇷</tg-emoji>"),  # Turkey
    "91": ("IN", "<tg-emoji emoji-id='5222300011366200403'>🇮🇳</tg-emoji>"),  # India
    "92": ("PK", "<tg-emoji emoji-id='5224637061985742245'>🇵🇰</tg-emoji>"),  # Pakistan
    "93": ("AF", "<tg-emoji emoji-id='5222096009009575868'>🇦🇫</tg-emoji>"),  # Afghanistan
    "94": ("LK", "<tg-emoji emoji-id='5224277294050192388'>🇱🇰</tg-emoji>"),  # Sri Lanka
    "95": ("MM", "<tg-emoji emoji-id='5224393700548814960'>🇲🇲</tg-emoji>"),  # Myanmar
    "98": ("IR", "<tg-emoji emoji-id='5224374154152653367'>🇮🇷</tg-emoji>"),  # Iran
    "850": ("KP", "<tg-emoji emoji-id='5222345550904439270'>🇰🇵</tg-emoji>"),  # North Korea
    "852": ("HK", "<tg-emoji emoji-id='5224435456220868088'>🇭🇰</tg-emoji>"),  # Hong Kong
    "853": ("MO", "<tg-emoji emoji-id='5224435456220868088'>🇲🇴</tg-emoji>"),  # Macau
    "855": ("KH", "<tg-emoji emoji-id='5224638530864556281'>🇰🇭</tg-emoji>"),  # Cambodia
    "856": ("LA", "<tg-emoji emoji-id='5224638530864556281'>🇱🇦</tg-emoji>"),  # Laos
    "960": ("MV", "<tg-emoji emoji-id='5224393700548814960'>🇲🇻</tg-emoji>"),  # Maldives
    "961": ("LB", "<tg-emoji emoji-id='5222194286451242896'>🇱🇧</tg-emoji>"),  # Lebanon
    "962": ("JO", "<tg-emoji emoji-id='5222229234600130045'>🇯🇴</tg-emoji>"),  # Jordan
    "963": ("SY", "<tg-emoji emoji-id='5224601903383457698'>🇸🇾</tg-emoji>"),  # Syria
    "964": ("IQ", "<tg-emoji emoji-id='5221980268230882832'>🇮🇶</tg-emoji>"),  # Iraq
    "965": ("KW", "<tg-emoji emoji-id='5222225596762830469'>🇰🇼</tg-emoji>"),  # Kuwait
    "966": ("SA", "<tg-emoji emoji-id='5224698145010624573'>🇸🇦</tg-emoji>"),  # Saudi Arabia
    "967": ("YE", "<tg-emoji emoji-id='5222300655611294950'>🇾🇪</tg-emoji>"),  # Yemen
    "968": ("OM", "<tg-emoji emoji-id='5222396686785066306'>🇴🇲</tg-emoji>"),  # Oman
    "970": ("PS", "<tg-emoji emoji-id='5222041677673282461'>🇵🇸</tg-emoji>"),  # Palestine
    "971": ("AE", "<tg-emoji emoji-id='5224565851427976312'>🇦🇪</tg-emoji>"),  # UAE
    "972": ("IL", "<tg-emoji emoji-id='5224720599099648709'>🇮🇱</tg-emoji>"),  # Israel
    "973": ("BH", "<tg-emoji emoji-id='5222225596762830469'>🇧🇭</tg-emoji>"),  # Bahrain
    "974": ("QA", "<tg-emoji emoji-id='5222225596762830469'>🇶🇦</tg-emoji>"),  # Qatar
    "975": ("BT", "<tg-emoji emoji-id='5222444378101925267'>🇧🇹</tg-emoji>"),  # Bhutan
    "976": ("MN", "<tg-emoji emoji-id='5224192257992701543'>🇲🇳</tg-emoji>"),  # Mongolia
    "977": ("NP", "<tg-emoji emoji-id='5222444378101925267'>🇳🇵</tg-emoji>"),  # Nepal
    "992": ("TJ", "<tg-emoji emoji-id='5222217865821696536'>🇹🇯</tg-emoji>"),  # Tajikistan
    "993": ("TM", "<tg-emoji emoji-id='5224256935905208951'>🇹🇲</tg-emoji>"),  # Turkmenistan
    "994": ("AZ", "<tg-emoji emoji-id='5224426544163728284'>🇦🇿</tg-emoji>"),  # Azerbaijan
    "995": ("GE", "<tg-emoji emoji-id='5222152195771742239'>🇬🇪</tg-emoji>"),  # Georgia
    "996": ("KG", "<tg-emoji emoji-id='5224426544163728284'>🇰🇬</tg-emoji>"),  # Kyrgyzstan
    "998": ("UZ", "<tg-emoji emoji-id='5222404546575219535'>🇺🇿</tg-emoji>"),  # Uzbekistan

    # Europe
    "30": ("GR", "<tg-emoji emoji-id='5222463490706389920'>🇬🇷</tg-emoji>"),  # Greece
    "31": ("NL", "<tg-emoji emoji-id='5224516489368841614'>🇳🇱</tg-emoji>"),  # Netherlands
    "32": ("BE", "<tg-emoji emoji-id='5224520754271366661'>🇧🇪</tg-emoji>"),  # Belgium
    "33": ("FR", "<tg-emoji emoji-id='5222029789203804982'>🇫🇷</tg-emoji>"),  # France
    "34": ("ES", "<tg-emoji emoji-id='5222024776976970940'>🇪🇸</tg-emoji>"),  # Spain
    "36": ("HU", "<tg-emoji emoji-id='5224691998912427164'>🇭🇺</tg-emoji>"),  # Hungary
    "39": ("IT", "<tg-emoji emoji-id='5222460101977190141'>🇮🇹</tg-emoji>"),  # Italy
    "40": ("RO", "<tg-emoji emoji-id='5222273794885826118'>🇷🇴</tg-emoji>"),  # Romania
    "41": ("CH", "<tg-emoji emoji-id='5224707263226194753'>🇨🇭</tg-emoji>"),  # Switzerland
    "43": ("AT", "<tg-emoji emoji-id='5224520754271366661'>🇦🇹</tg-emoji>"),  # Austria
    "44": ("GB", "<tg-emoji emoji-id='5224518800061245598'>🇬🇧</tg-emoji>"),  # United Kingdom
    "45": ("DK", "<tg-emoji emoji-id='5224245902134226386'>🇩🇰</tg-emoji>"),  # Denmark
    "46": ("SE", "<tg-emoji emoji-id='5222201098269373561'>🇸🇪</tg-emoji>"),  # Sweden
    "47": ("NO", "<tg-emoji emoji-id='5224465228934163949'>🇳🇴</tg-emoji>"),  # Norway
    "48": ("PL", "<tg-emoji emoji-id='5224670399521892983'>🇵🇱</tg-emoji>"),  # Poland
    "49": ("DE", "<tg-emoji emoji-id='5222165617544542414'>🇩🇪</tg-emoji>"),  # Germany
    "350": ("GI", "<tg-emoji emoji-id='5224518800061245598'>🇬🇮</tg-emoji>"),  # Gibraltar
    "351": ("PT", "<tg-emoji emoji-id='5224404094369672274'>🇵🇹</tg-emoji>"),  # Portugal
    "352": ("LU", "<tg-emoji emoji-id='5224499567197700690'>🇱🇺</tg-emoji>"),  # Luxembourg
    "353": ("IE", "<tg-emoji emoji-id='5222233374948602940'>🇮🇪</tg-emoji>"),  # Ireland
    "354": ("IS", "<tg-emoji emoji-id='5222063229819172521'>🇮🇸</tg-emoji>"),  # Iceland
    "355": ("AL", "<tg-emoji emoji-id='5224312057515486246'>🇦🇱</tg-emoji>"),  # Albania
    "356": ("MT", "<tg-emoji emoji-id='5224312057515486246'>🇲🇹</tg-emoji>"),  # Malta
    "357": ("CY", "<tg-emoji emoji-id='5224601903383457698'>🇨🇾</tg-emoji>"),  # Cyprus
    "358": ("FI", "<tg-emoji emoji-id='5224282903277482188'>🇫🇮</tg-emoji>"),  # Finland
    "359": ("BG", "<tg-emoji emoji-id='5224670399521892983'>🇧🇬</tg-emoji>"),  # Bulgaria
    "370": ("LT", "<tg-emoji emoji-id='5224245902134226386'>🇱🇹</tg-emoji>"),  # Lithuania
    "371": ("LV", "<tg-emoji emoji-id='5224245902134226386'>🇱🇻</tg-emoji>"),  # Latvia
    "372": ("EE", "<tg-emoji emoji-id='5224245902134226386'>🇪🇪</tg-emoji>"),  # Estonia
    "373": ("MD", "<tg-emoji emoji-id='5222273794885826118'>🇲🇩</tg-emoji>"),  # Moldova
    "374": ("AM", "<tg-emoji emoji-id='5224369957969603463'>🇦🇲</tg-emoji>"),  # Armenia
    "375": ("BY", "<tg-emoji emoji-id='5280820319458707404'>🇧🇾</tg-emoji>"),  # Belarus
    "376": ("AD", "<tg-emoji emoji-id='5221987861733061751'>🇦🇩</tg-emoji>"),  # Andorra
    "377": ("MC", "<tg-emoji emoji-id='5221937224068640464'>🇲🇨</tg-emoji>"),  # Monaco
    "378": ("SM", "<tg-emoji emoji-id='5224312057515486246'>🇸🇲</tg-emoji>"),  # San Marino
    "380": ("UA", "<tg-emoji emoji-id='5222250679371839695'>🇺🇦</tg-emoji>"),  # Ukraine
    "381": ("RS", "<tg-emoji emoji-id='5222145396838512729'>🇷🇸</tg-emoji>"),  # Serbia
    "382": ("ME", "<tg-emoji emoji-id='5224463399278096980'>🇲🇪</tg-emoji>"),  # Montenegro
    "383": ("XK", "<tg-emoji emoji-id='5222145396838512729'>🇽🇰</tg-emoji>"),  # Kosovo
    "385": ("HR", "<tg-emoji emoji-id='5224660718665607511'>🇭🇷</tg-emoji>"),  # Croatia
    "386": ("SI", "<tg-emoji emoji-id='5224660718665607511'>🇸🇮</tg-emoji>"),  # Slovenia
    "387": ("BA", "<tg-emoji emoji-id='5224660718665607511'>🇧🇦</tg-emoji>"),  # Bosnia
    "389": ("MK", "<tg-emoji emoji-id='5222470435668505656'>🇲🇰</tg-emoji>"),  # North Macedonia
    "420": ("CZ", "<tg-emoji emoji-id='5224499567197700690'>🇨🇿</tg-emoji>"),  # Czech Republic
    "421": ("SK", "<tg-emoji emoji-id='5222401879400528047'>🇸🇰</tg-emoji>"),  # Slovakia
    "423": ("LI", "<tg-emoji emoji-id='5224520754271366661'>🇱🇮</tg-emoji>"),  # Liechtenstein

    # Americas
    "1": ("US", "<tg-emoji emoji-id='5224321781321442532'>🇺🇸</tg-emoji>"),  # United States
    "51": ("PE", "<tg-emoji emoji-id='5224482026551258766'>🇵🇪</tg-emoji>"),  # Peru
    "52": ("MX", "<tg-emoji emoji-id='5224482026551258766'>🇲🇽</tg-emoji>"),  # Mexico
    "53": ("CU", "<tg-emoji emoji-id='5224482026551258766'>🇨🇺</tg-emoji>"),  # Cuba
    "54": ("AR", "<tg-emoji emoji-id='5224482026551258766'>🇦🇷</tg-emoji>"),  # Argentina
    "55": ("BR", "<tg-emoji emoji-id='5224688610183228070'>🇧🇷</tg-emoji>"),  # Brazil
    "56": ("CL", "<tg-emoji emoji-id='5224482026551258766'>🇨🇱</tg-emoji>"),  # Chile
    "57": ("CO", "<tg-emoji emoji-id='5224455152940886669'>🇨🇴</tg-emoji>"),  # Colombia
    "58": ("VE", "<tg-emoji emoji-id='5434009132753499322'>🇻🇪</tg-emoji>"),  # Venezuela
    "501": ("BZ", "<tg-emoji emoji-id='5224482026551258766'>🇧🇿</tg-emoji>"),  # Belize
    "502": ("GT", "<tg-emoji emoji-id='5222128302868672826'>🇬🇹</tg-emoji>"),  # Guatemala
    "503": ("SV", "<tg-emoji emoji-id='5222128302868672826'>🇸🇻</tg-emoji>"),  # El Salvador
    "504": ("HN", "<tg-emoji emoji-id='5222229234600130045'>🇭🇳</tg-emoji>"),  # Honduras
    "505": ("NI", "<tg-emoji emoji-id='5222128302868672826'>🇳🇮</tg-emoji>"),  # Nicaragua
    "506": ("CR", "<tg-emoji emoji-id='5222128302868672826'>🇨🇷</tg-emoji>"),  # Costa Rica
    "507": ("PA", "<tg-emoji emoji-id='5222111719999945107'>🇵🇦</tg-emoji>"),  # Panama
    "509": ("HT", "<tg-emoji emoji-id='5224683146984831315'>🇭🇹</tg-emoji>"),  # Haiti
    "591": ("BO", "<tg-emoji emoji-id='5224482026551258766'>🇧🇴</tg-emoji>"),  # Bolivia
    "592": ("GY", "<tg-emoji emoji-id='5224570532942329532'>🇬🇾</tg-emoji>"),  # Guyana
    "593": ("EC", "<tg-emoji emoji-id='5224191188545840926'>🇪🇨</tg-emoji>"),  # Ecuador
    "595": ("PY", "<tg-emoji emoji-id='5222152565138929235'>🇵🇾</tg-emoji>"),  # Paraguay
    "597": ("SR", "<tg-emoji emoji-id='5224567367551428669'>🇸🇷</tg-emoji>"),  # Suriname
    "598": ("UY", "<tg-emoji emoji-id='5222466849370813232'>🇺🇾</tg-emoji>"),  # Uruguay

    # Oceania
    "61": ("AU", "<tg-emoji emoji-id='5224573595254009705'>🇦🇺</tg-emoji>"),  # Australia
    "64": ("NZ", "<tg-emoji emoji-id='5224573595254009705'>🇳🇿</tg-emoji>"),  # New Zealand
    "670": ("TL", "<tg-emoji emoji-id='5224515905253291409'>🇹🇱</tg-emoji>"),  # Timor-Leste
    "673": ("BN", "<tg-emoji emoji-id='5224312886444174057'>🇧🇳</tg-emoji>"),  # Brunei
    "674": ("NR", "<tg-emoji emoji-id='5224573595254009705'>🇳🇷</tg-emoji>"),  # Nauru
    "675": ("PG", "<tg-emoji emoji-id='5224500164198149905'>🇵🇬</tg-emoji>"),  # Papua New Guinea
    "676": ("TO", "<tg-emoji emoji-id='5224573595254009705'>🇹🇴</tg-emoji>"),  # Tonga
    "677": ("SB", "<tg-emoji emoji-id='5222290588207954120'>🇸🇧</tg-emoji>"),  # Solomon Islands
    "678": ("VU", "<tg-emoji emoji-id='5222126748090512778'>🇻🇺</tg-emoji>"),  # Vanuatu
    "679": ("FJ", "<tg-emoji emoji-id='5221962676044838178'>🇫🇯</tg-emoji>"),  # Fiji
    "680": ("PW", "<tg-emoji emoji-id='5224573595254009705'>🇵🇼</tg-emoji>"),  # Palau
    "685": ("WS", "<tg-emoji emoji-id='5224660353593387686'>🇼🇸</tg-emoji>"),  # Samoa
    "686": ("KI", "<tg-emoji emoji-id='5224573595254009705'>🇰🇮</tg-emoji>"),  # Kiribati
    "687": ("NC", "<tg-emoji emoji-id='5224573595254009705'>🇳🇨</tg-emoji>"),  # New Caledonia
    "688": ("TV", "<tg-emoji emoji-id='5224573595254009705'>🇹🇻</tg-emoji>"),  # Tuvalu
    "689": ("PF", "<tg-emoji emoji-id='5224573595254009705'>🇵🇫</tg-emoji>"),  # French Polynesia
    "691": ("FM", "<tg-emoji emoji-id='5224573595254009705'>🇫🇲</tg-emoji>"),  # Micronesia
    "692": ("MH", "<tg-emoji emoji-id='5224573595254009705'>🇲🇭</tg-emoji>"),  # Marshall Islands

    # Special Flags
    "scotland": ("SCT", "<tg-emoji emoji-id='5224580312582861623'>🏴󠁧󠁢󠁳󠁣󠁴󠁿</tg-emoji>"),  # Scotland
    "wales": ("WLS", "<tg-emoji emoji-id='5224431333052264232'>🏴󠁧󠁢󠁷󠁬󠁳󠁿</tg-emoji>"),  # Wales
    "eu": ("EU", "<tg-emoji emoji-id='5222108911091331711'>🇪🇺</tg-emoji>"),  # European Union
    "un": ("UN", "<tg-emoji emoji-id='5451772687993031127'>🇺🇳</tg-emoji>"),  # United Nations
}

# ======================
# 🆔 استخراج معرفات الإيموجي المميزة من COUNTRY_MAP
# ======================
def extract_emoji_id(html_string):
    """استخراج emoji-id من كود <tg-emoji>"""
    if not html_string:
        return None
    match = re.search(r"emoji-id=['\"](\d+)['\"]", html_string)
    return match.group(1) if match else None

# بناء قاموس يربط مختصر الدولة (EG, US, ...) بمعرف الإيموجي المميز
FLAG_EMOJI_IDS = {}
for country_code, (short, html_flag) in COUNTRY_MAP.items():
    if html_flag and 'emoji-id' in html_flag:
        emoji_id = extract_emoji_id(html_flag)
        if emoji_id:
            FLAG_EMOJI_IDS[short] = emoji_id
# ======================
# 🌍 قاموس الأعلام المتحركة (Telegram Animated Emojis)
# ======================
# ======================
# 🌍 قاموس الأعلام المتحركة (بصيغة HTML جاهزة)
# ======================
ANIMATED_FLAGS_HTML = {
    # أفريقيا
    "EG": "<tg-emoji emoji-id='5222161185138292290'>🇪🇬</tg-emoji>",  # مصر
    "ZA": "<tg-emoji emoji-id='5224696216570309138'>🇿🇦</tg-emoji>",  # جنوب أفريقيا
    "MA": "<tg-emoji emoji-id='5224530035695693965'>🇲🇦</tg-emoji>",  # المغرب
    "DZ": "<tg-emoji emoji-id='5224260376174015500'>🇩🇿</tg-emoji>",  # الجزائر
    "TN": "<tg-emoji emoji-id='5221991375016310330'>🇹🇳</tg-emoji>",  # تونس
    "LY": "<tg-emoji emoji-id='5222194286451242896'>🇱🇾</tg-emoji>",  # ليبيا
    "SD": "<tg-emoji emoji-id='5224372990216514135'>🇸🇩</tg-emoji>",  # السودان
    "NG": "<tg-emoji emoji-id='5224723614166691638'>🇳🇬</tg-emoji>",  # نيجيريا
    "GH": "<tg-emoji emoji-id='5224511339703056124'>🇬🇭</tg-emoji>",  # غانا
    "KE": "<tg-emoji emoji-id='5222089648163009103'>🇰🇪</tg-emoji>",  # كينيا
    
    # آسيا
    "SA": "<tg-emoji emoji-id='5224698145010624573'>🇸🇦</tg-emoji>",  # السعودية
    "AE": "<tg-emoji emoji-id='5224565851427976312'>🇦🇪</tg-emoji>",  # الإمارات
    "KW": "<tg-emoji emoji-id='5222225596762830469'>🇰🇼</tg-emoji>",  # الكويت
    "QA": "<tg-emoji emoji-id='5222225596762830469'>🇶🇦</tg-emoji>",  # قطر
    "BH": "<tg-emoji emoji-id='5222225596762830469'>🇧🇭</tg-emoji>",  # البحرين
    "OM": "<tg-emoji emoji-id='5222396686785066306'>🇴🇲</tg-emoji>",  # عمان
    "JO": "<tg-emoji emoji-id='5222229234600130045'>🇯🇴</tg-emoji>",  # الأردن
    "PS": "<tg-emoji emoji-id='5222041677673282461'>🇵🇸</tg-emoji>",  # فلسطين
    "IQ": "<tg-emoji emoji-id='5221980268230882832'>🇮🇶</tg-emoji>",  # العراق
    "SY": "<tg-emoji emoji-id='5224601903383457698'>🇸🇾</tg-emoji>",  # سوريا
    "LB": "<tg-emoji emoji-id='5222194286451242896'>🇱🇧</tg-emoji>",  # لبنان
    "YE": "<tg-emoji emoji-id='5222300655611294950'>🇾🇪</tg-emoji>",  # اليمن
    "TR": "<tg-emoji emoji-id='5224601903383457698'>🇹🇷</tg-emoji>",  # تركيا
    "IR": "<tg-emoji emoji-id='5224374154152653367'>🇮🇷</tg-emoji>",  # إيران
    "PK": "<tg-emoji emoji-id='5224637061985742245'>🇵🇰</tg-emoji>",  # باكستان
    "IN": "<tg-emoji emoji-id='5222300011366200403'>🇮🇳</tg-emoji>",  # الهند
    "CN": "<tg-emoji emoji-id='5224435456220868088'>🇨🇳</tg-emoji>",  # الصين
    "JP": "<tg-emoji emoji-id='5222390089715299207'>🇯🇵</tg-emoji>",  # اليابان
    "KR": "<tg-emoji emoji-id='5222345550904439270'>🇰🇷</tg-emoji>",  # كوريا الجنوبية
    "TH": "<tg-emoji emoji-id='5224638530864556281'>🇹🇭</tg-emoji>",  # تايلاند
    "MY": "<tg-emoji emoji-id='5224312886444174057'>🇲🇾</tg-emoji>",  # ماليزيا
    "ID": "<tg-emoji emoji-id='5224405893960969756'>🇮🇩</tg-emoji>",  # إندونيسيا
    "PH": "<tg-emoji emoji-id='5222065042295376892'>🇵🇭</tg-emoji>",  # الفلبين
    "VN": "<tg-emoji emoji-id='5222359651282071925'>🇻🇳</tg-emoji>",  # فيتنام
    
    # أوروبا
    "GB": "<tg-emoji emoji-id='5224518800061245598'>🇬🇧</tg-emoji>",  # بريطانيا
    "FR": "<tg-emoji emoji-id='5222029789203804982'>🇫🇷</tg-emoji>",  # فرنسا
    "DE": "<tg-emoji emoji-id='5222165617544542414'>🇩🇪</tg-emoji>",  # ألمانيا
    "IT": "<tg-emoji emoji-id='5222460101977190141'>🇮🇹</tg-emoji>",  # إيطاليا
    "ES": "<tg-emoji emoji-id='5222024776976970940'>🇪🇸</tg-emoji>",  # إسبانيا
    "NL": "<tg-emoji emoji-id='5224516489368841614'>🇳🇱</tg-emoji>",  # هولندا
    "BE": "<tg-emoji emoji-id='5224520754271366661'>🇧🇪</tg-emoji>",  # بلجيكا
    "CH": "<tg-emoji emoji-id='5224707263226194753'>🇨🇭</tg-emoji>",  # سويسرا
    "AT": "<tg-emoji emoji-id='5224520754271366661'>🇦🇹</tg-emoji>",  # النمسا
    "SE": "<tg-emoji emoji-id='5222201098269373561'>🇸🇪</tg-emoji>",  # السويد
    "NO": "<tg-emoji emoji-id='5224465228934163949'>🇳🇴</tg-emoji>",  # النرويج
    "DK": "<tg-emoji emoji-id='5224245902134226386'>🇩🇰</tg-emoji>",  # الدنمارك
    "FI": "<tg-emoji emoji-id='5224282903277482188'>🇫🇮</tg-emoji>",  # فنلندا
    "PL": "<tg-emoji emoji-id='5224670399521892983'>🇵🇱</tg-emoji>",  # بولندا
    "UA": "<tg-emoji emoji-id='5222250679371839695'>🇺🇦</tg-emoji>",  # أوكرانيا
    "RO": "<tg-emoji emoji-id='5222273794885826118'>🇷🇴</tg-emoji>",  # رومانيا
    "GR": "<tg-emoji emoji-id='5222463490706389920'>🇬🇷</tg-emoji>",  # اليونان
    "PT": "<tg-emoji emoji-id='5224404094369672274'>🇵🇹</tg-emoji>",  # البرتغال
    "IE": "<tg-emoji emoji-id='5222233374948602940'>🇮🇪</tg-emoji>",  # أيرلندا
    
    # الأمريكتين
    "US": "<tg-emoji emoji-id='5224321781321442532'>🇺🇸</tg-emoji>",  # أمريكا
    "CA": "<tg-emoji emoji-id='5224637061985742245'>🇨🇦</tg-emoji>",  # كندا
    "MX": "<tg-emoji emoji-id='5224482026551258766'>🇲🇽</tg-emoji>",  # المكسيك
    "BR": "<tg-emoji emoji-id='5224688610183228070'>🇧🇷</tg-emoji>",  # البرازيل
    "AR": "<tg-emoji emoji-id='5224482026551258766'>🇦🇷</tg-emoji>",  # الأرجنتين
    "CO": "<tg-emoji emoji-id='5224455152940886669'>🇨🇴</tg-emoji>",  # كولومبيا
    "PE": "<tg-emoji emoji-id='5224482026551258766'>🇵🇪</tg-emoji>",  # بيرو
    "VE": "<tg-emoji emoji-id='5434009132753499322'>🇻🇪</tg-emoji>",  # فنزويلا
    "CL": "<tg-emoji emoji-id='5224482026551258766'>🇨🇱</tg-emoji>",  # تشيلي
    
    # أوقيانوسيا
    "AU": "<tg-emoji emoji-id='5224573595254009705'>🇦🇺</tg-emoji>",  # أستراليا
    "NZ": "<tg-emoji emoji-id='5224573595254009705'>🇳🇿</tg-emoji>",  # نيوزيلندا
}

# ======================
# 🎯 قاموس أيقونات الخدمات المتحركة
# ======================
SERVICE_ANIMATIONS = {
    # واتساب
    "whatsapp": "<tg-emoji emoji-id='5334998226636390258'>📞</tg-emoji>",
    "ws": "<tg-emoji emoji-id='5334998226636390258'>📞</tg-emoji>",
    "واتساب": "<tg-emoji emoji-id='5334998226636390258'>📞</tg-emoji>",
    "واتس": "<tg-emoji emoji-id='5334998226636390258'>📞</tg-emoji>",
    
    # فيسبوك
    "facebook": "<tg-emoji emoji-id='5323261730283863478'>💬</tg-emoji>",
    "fb": "<tg-emoji emoji-id='5323261730283863478'>💬</tg-emoji>",
    "فيسبوك": "<tg-emoji emoji-id='5323261730283863478'>💬</tg-emoji>",
    
    # تيليجرام
    "telegram": "<tg-emoji emoji-id='5330237710655306682'>👉</tg-emoji>",
    "tg": "<tg-emoji emoji-id='5330237710655306682'>👉</tg-emoji>",
    "تيليجرام": "<tg-emoji emoji-id='5330237710655306682'>👉</tg-emoji>",
    "تلي": "<tg-emoji emoji-id='5330237710655306682'>👉</tg-emoji>",
    
    # انستغرام
    "instagram": "<tg-emoji emoji-id='5319160079465857105'>📷</tg-emoji>",
    "ig": "<tg-emoji emoji-id='5319160079465857105'>📷</tg-emoji>",
    "انستقرام": "<tg-emoji emoji-id='5319160079465857105'>📷</tg-emoji>",
    "انستا": "<tg-emoji emoji-id='5319160079465857105'>📷</tg-emoji>",
    
    # تويتر
    "twitter": "<tg-emoji emoji-id='5319301418700414976'>🐦</tg-emoji>",
    "x": "<tg-emoji emoji-id='5319301418700414976'>🐦</tg-emoji>",
    "تويتر": "<tg-emoji emoji-id='5319301418700414976'>🐦</tg-emoji>",
    
    # جوجل
    "google": "<tg-emoji emoji-id='5334842116222099861'>🔍</tg-emoji>",
    "gmail": "<tg-emoji emoji-id='5334842116222099861'>📧</tg-emoji>",
    "جوجل": "<tg-emoji emoji-id='5334842116222099861'>🔍</tg-emoji>",
    
    # تيك توك
    "tiktok": "<tg-emoji emoji-id='5334981420986302132'>🎵</tg-emoji>",
    "تيك توك": "<tg-emoji emoji-id='5334981420986302132'>🎵</tg-emoji>",
    "تيك": "<tg-emoji emoji-id='5334981420986302132'>🎵</tg-emoji>",
    
    # سناب شات
    "snapchat": "<tg-emoji emoji-id='5334870552508237962'>👻</tg-emoji>",
    "سناب": "<tg-emoji emoji-id='5334870552508237962'>👻</tg-emoji>",
    
    # أمازون
    "amazon": "<tg-emoji emoji-id='5334991167190933654'>📦</tg-emoji>",
    "امازون": "<tg-emoji emoji-id='5334991167190933654'>📦</tg-emoji>",
    
    # أبل
    "apple": "<tg-emoji emoji-id='5334982396943074428'>🍎</tg-emoji>",
    "icloud": "<tg-emoji emoji-id='5334982396943074428'>☁️</tg-emoji>",
    "ابل": "<tg-emoji emoji-id='5334982396943074428'>🍎</tg-emoji>",
    
    # مايكروسوفت
    "microsoft": "<tg-emoji emoji-id='5334841225296085027'>🪟</tg-emoji>",
    "مايكروسوفت": "<tg-emoji emoji-id='5334841225296085027'>🪟</tg-emoji>",
    
    # لينكد إن
    "linkedin": "<tg-emoji emoji-id='5334914036540174635'>💼</tg-emoji>",
    "لينكد": "<tg-emoji emoji-id='5334914036540174635'>💼</tg-emoji>",
    
    # أوبر
    "uber": "<tg-emoji emoji-id='5334852154100023358'>🚗</tg-emoji>",
    "اوبر": "<tg-emoji emoji-id='5334852154100023358'>🚗</tg-emoji>",
    
    # نتفلكس
    "netflix": "<tg-emoji emoji-id='5334893147408462016'>🎬</tg-emoji>",
    "نتفلكس": "<tg-emoji emoji-id='5334893147408462016'>🎬</tg-emoji>",
    
    # سبوتيفاي
    "spotify": "<tg-emoji emoji-id='5334986448268754952'>🎧</tg-emoji>",
    "سبوتيفاي": "<tg-emoji emoji-id='5334986448268754952'>🎧</tg-emoji>",
    
    # باي بال
    "paypal": "<tg-emoji emoji-id='5334856472902303601'>💰</tg-emoji>",
    "باي بال": "<tg-emoji emoji-id='5334856472902303601'>💰</tg-emoji>",
    
    # يوتيوب
    "youtube": "<tg-emoji emoji-id='5334872359940327681'>▶️</tg-emoji>",
    "يوتيوب": "<tg-emoji emoji-id='5334872359940327681'>▶️</tg-emoji>",
    
    # ديسكورد
    "discord": "<tg-emoji emoji-id='5334856339125906569'>🎮</tg-emoji>",
    "ديسكورد": "<tg-emoji emoji-id='5334856339125906569'>🎮</tg-emoji>",
    
    # بنوك ودفع
    "stc": "<tg-emoji emoji-id='5334868571674804933'>💳</tg-emoji>",
    "stcpay": "<tg-emoji emoji-id='5334868571674804933'>💳</tg-emoji>",
    "بنك": "<tg-emoji emoji-id='5334868571674804933'>🏦</tg-emoji>",
}

def get_service_icon(service_code, message_text=""):
    """الحصول على أيقونة الخدمة المتحركة"""
    service_lower = service_code.lower() if service_code else ""
    message_lower = message_text.lower() if message_text else ""
    
    # 1. البحث في الكود المختصر (زي #WP, #FB)
    for key, icon in SERVICE_ANIMATIONS.items():
        if key in service_lower:
            return icon
    
    # 2. البحث في نص الرسالة
    for key, icon in SERVICE_ANIMATIONS.items():
        if key in message_lower:
            return icon
    
    # 3. أيقونة افتراضية للمصادر المجهولة - HTML سليم
    return "<tg-emoji emoji-id='5334998226636390258'>🔮</tg-emoji>"  # من غير أقواس معقوفة
# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة)
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
# ======================
# 🧠 إنشاء قاعدة البيانات (مع جداول جديدة)
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    
    # 2. جدول الكومبو العام (محدث بدعم الخدمة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            service TEXT DEFAULT '',
            numbers TEXT NOT NULL,
            UNIQUE(country_code, service)
        )
    ''')
    
    # 3. جدول سجلات الـ OTP
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )
    ''')
    
    # 4. جدول لوحات التحكم (Dashboards)
    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_url TEXT,
            ajax_path TEXT,
            login_page TEXT,
            login_post TEXT,
            username TEXT,
            password TEXT
        )
    ''')
    
    # 5. جدول إعدادات البوت العامة
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # 6. جدول الكومبو الخاص (يمكن ترقيته لاحقاً لدعم الخدمة إن أردت)
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')

    # 7. جدول قنوات الاشتراك الإجباري
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )
    ''')

    # 8. جدول معرفات الشات
    c.execute('''
        CREATE TABLE IF NOT EXISTS broadcast_chats (
            chat_id TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- ترقية الجدول القديم إن وجد (نقل البيانات مع خدمة فارغة) ---
    # التحقق من وجود جدول combos القديم (بدون service)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='combos_old'")
    if not c.fetchone():
        # إعادة تسمية الجدول القديم إذا كان موجوداً
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='combos'")
        if c.fetchone():
            # جدول combos موجود مسبقاً، تحقق مما إذا كان به عمود service
            c.execute("PRAGMA table_info(combos)")
            columns = [col[1] for col in c.fetchall()]
            if 'service' not in columns:
                # جدول قديم، انقل البيانات إلى الجدول الجديد
                c.execute("ALTER TABLE combos RENAME TO combos_old")
                # أنشئ الجدول الجديد (سبق إنشاؤه أعلاه) ولكننا نحتاج لاستعلام منفصل هنا لأنه تم إنشاؤه بالفعل
                # بدلاً من ذلك، نقوم بإدراج البيانات من القديم مع service = ''
                c.execute('''
                    INSERT INTO combos (country_code, service, numbers)
                    SELECT country_code, '', numbers FROM combos_old
                ''')
                c.execute("DROP TABLE combos_old")
    
    # --- تهيئة البيانات الافتراضية ---
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_channel', '')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_enabled', '0')")

    # 🔄 نقل القناة القديمة (إن وُجدت) تلقائيًا إلى الجدول الجديد
    c.execute("SELECT value FROM bot_settings WHERE key = 'force_sub_channel'")
    old_channel = c.fetchone()
    if old_channel and old_channel[0].strip():
        channel = old_channel[0].strip()
        c.execute("SELECT 1 FROM force_sub_channels WHERE channel_url = ?", (channel,))
        if not c.fetchone():
            try:
                enabled = 1
                c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, ?)",
                          (channel, "القناة الأساسية", enabled))
            except: pass

    # 🚀 نقل معرفات الشات الموجودة في الملف حالياً إلى قاعدة البيانات تلقائياً
    initial_chats = ["-1003877396414"]
    for cid in initial_chats:
        c.execute("INSERT OR IGNORE INTO broadcast_chats (chat_id) VALUES (?)", (cid,))

    conn.commit()
    conn.close()

init_db()

# ==========================================
# 📢 دوال إدارة معرفات الشات (الجديدة)
# ==========================================

def get_all_broadcast_chats():
    """جلب جميع معرفات الشات المسجلة من قاعدة البيانات"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT chat_id FROM broadcast_chats")
        chats = [row[0] for row in c.fetchall()]
        conn.close()
        return chats
    except Exception as e:
        print(f"Error fetching chats: {e}")
        return []

def add_broadcast_chat(chat_id):
    """إضافة معرف شات جديد للجدول"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # INSERT OR IGNORE تمنع تكرار نفس المعرف
        c.execute("INSERT OR IGNORE INTO broadcast_chats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding chat: {e}")
        return False

def delete_broadcast_chat(chat_id):
    """حذف معرف شات من الجدول"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM broadcast_chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False

# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة)
# ======================


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    """
    يحفظ أو يحدّث بيانات المستخدم باستخدام استعلام واحد (INSERT OR REPLACE).
    هذا يمنع أخطاء التزامن (race conditions) في البيئات متعددة الخيوط.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # نحتاج إلى جلب البيانات القديمة التي لا نريد تغييرها إذا لم يتم توفيرها
    # هذا يمنع مسح البيانات القيمة مثل country_code عند استدعاء الدالة بمعلومات أساسية فقط
    existing_data = get_user(user_id)
    if existing_data:
        # إذا لم يتم توفير country_code جديد، استخدم القديم
        if country_code is None:
            country_code = existing_data[4]
        # إذا لم يتم توفير assigned_number جديد، استخدم القديم
        if assigned_number is None:
            assigned_number = existing_data[5]
        # إذا لم يتم توفير private_combo_country جديد، استخدم القديم
        if private_combo_country is None:
            private_combo_country = existing_data[7]

    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (
        user_id,
        username,
        first_name,
        last_name,
        country_code,
        assigned_number,
        user_id, # يُستخدم في COALESCE لجلب حالة الحظر القديمة
        private_combo_country
    ))
    conn.commit()
    conn.close()


def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1
    
def is_maintenance_mode():
    return not BOT_ACTIVE

def set_maintenance_mode(status):
    global BOT_ACTIVE
    BOT_ACTIVE = not status
    
def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(country_code, service='', user_id=None):
    """
    جلب أرقام كومبو معين.
    إذا تم تمرير user_id، يبحث في الكومبوهات الخاصة أولاً.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # البحث في الكومبوهات الخاصة (إذا طلب)
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    
    # البحث في الكومبوهات العامة مع مراعاة الخدمة
    c.execute("SELECT numbers FROM combos WHERE country_code=? AND service=?", (country_code, service))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, service='', user_id=None):
    """
    حفظ كومبو. إذا user_id موجود، يحفظ في الخاص.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("REPLACE INTO combos (country_code, service, numbers) VALUES (?, ?, ?)",
                  (country_code, service, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, service='', user_id=None):
    """
    حذف كومبو.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
    else:
        c.execute("DELETE FROM combos WHERE country_code=? AND service=?", (country_code, service))
    conn.commit()
    conn.close()

def get_all_combos():
    """
    جلب جميع الكومبوهات العامة مع معلومات الخدمة.
    تعيد قائمة من tuples (country_code, service)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code, service FROM combos ORDER BY country_code, service")
    rows = c.fetchall()
    conn.close()
    return rows  # كل عنصر هو (country_code, service)

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # استخدمنا LIKE و علامات % عشان ندور على الرقم في أي مكان داخل النص المخزن
    c.execute("SELECT user_id FROM users WHERE assigned_number LIKE ?", (f'%{number}%',))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row
# --- دوال إدارة قنوات الاشتراك الإجباري (متعددة) ---
def get_all_force_sub_channels(enabled_only=True):
    """جلب القنوات (المفعلة فقط أو جميعها)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    """إضافة قناة جديدة (لا تسمح بالتكرار)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # قناة مكررة
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    """حذف قناة بالرقم التعريفي"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    """تفعيل/تعطيل قناة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()
# ======================
# 🔐 دوال الاشتراك الإجباري
# ======================
def force_sub_check(user_id):
    """التحقق من اشتراك المستخدم في **جميع** القنوات المُفعَّلة"""
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True  # لا توجد قنوات → لا يوجد تحقق

    for _, url, _ in channels:
        try:
            # توحيد التنسيق: @xxx بدل https://t.me/xxx
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue  # تجاهل الروابط غير الصحيحة
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"[!] خطأ في التحقق من القناة {url}: {e}")
            return False  # أي فشل = غير مشترك
    return True

def force_sub_markup():
    """إنشاء زر لكل قناة مُفعَّلة + زر التحقق"""
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None

    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f" {desc}" if desc else " اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ Check your subscription", callback_data="check_sub"))
    return markup
# ======================
# 🤖 إنشاء بوت Telegram
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🎮 وظائف البوت التفاعلي
# ======================
def is_admin(user_id):
    return user_id in ADMIN_IDS
    
    
# ======================
# ⌨️ لوحة المفاتيح الرئيسية (Reply Keyboard)
# ======================
def main_reply_keyboard():
    """إنشاء لوحة المفاتيح الرئيسية التي تظهر أسفل الشاشة"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "📞 Get Number",
        "📢 Channel",
        "🙏 Help",
        "🌿 Method"
    ]
    markup.add(*buttons)
    return markup
    
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Maintenance Mode Check
    if is_maintenance_mode() and not is_admin(user_id):
        maintenance_caption = (
            "<b>❍─── <u>𝐖𝐞𝐥𝐜𝐨𝐦 𝐭𝐨 𝐒𝐏𝐄𝐄𝐃</u> ───❍</b>\n\n"
            "<b>⚠️ Sorry, dear user</b>\n"
            "<b>The bot is currently in maintenance mode to update services..</b>\n\n"
            "<b>⏳ Please try again later.</b>\n"
            "<b>────────────────────</b>"
        )
        maintenance_photo = "https://i.ibb.co/2352v1FN/file-000000004f20720aaa70039fcd26faab-1.png"
        try:
            bot.send_photo(chat_id, maintenance_photo, caption=maintenance_caption, parse_mode="HTML")
        except:
            bot.send_message(chat_id, maintenance_caption, parse_mode="HTML")
        return

    # 2. Banned Users Check
    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 Sorry, you have been banned from using the bot.</b>", parse_mode="HTML")
        return

    # 3. Force Subscribe Check
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            photo_url = "https://i.ibb.co/cc0NFv1f/IMG-20260117-085419-964.jpg"
            caption = (
                "🔐 <b>𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 | Required</b>\n"
                "•━━━━━━━━━━━━━━━━━━•\n\n"
                "<b>• You must join our channels to use the bot.</b>\n"
                "<b>• Please subscribe to the channels below.</b>\n\n"
                "<b>• After subscribing, click (Verify) to continue.</b>\n\n"
                "•━━━━━━━━━━━━━━━━━━•\n"
                "<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ : @o_k_60</b>"
            )
            bot.send_photo(chat_id, photo_url, caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, "<b>🔒 Force subscription is enabled but no channels added!</b>", parse_mode="HTML")
        return

    # 4. Save new user and notify admin (كما هي)
    if not get_user(user_id):
        save_user(
            user_id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )
        for admin in ADMIN_IDS:
            try:
                caption = (
                    f"🆕 <b>New user started the bot:</b>\n"
                    f"<b>🆔:</b> <code>{user_id}</code>\n"
                    f"<b>👤:</b> @{message.from_user.username or 'None'}\n"
                    f"<b>Name:</b> {message.from_user.first_name or ''}"
                )
                bot.send_message(admin, caption, parse_mode="HTML")
            except:
                pass

    # 5. إرسال رسالة الترحيب الجديدة مع لوحة المفاتيح الرئيسية
    welcome_text = "🎉 Welcome! You have full access now ✅"
    bot.send_message(
        chat_id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_reply_keyboard()  # إرسال الكيبورد الرئيسي
    )
    
    
# ======================
# 🎮 معالجات أزرار الـ Reply Keyboard
# ======================

@bot.message_handler(func=lambda message: message.text == "📞 Get Number")
def handle_get_number(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # إعادة التحقق من الصلاحيات (لأنه قد يكون تغير منذ آخر /start)
    if is_maintenance_mode() and not is_admin(user_id):
        bot.reply_to(message, "⚠️ البوت في وضع الصيانة حالياً.", parse_mode="HTML")
        return
    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 You are banned.</b>", parse_mode="HTML")
        return
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            photo_url = "https://i.ibb.co/cc0NFv1f/IMG-20260117-085419-964.jpg"
            caption = (
                "🔐 <b>𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 | Required</b>\n"
                "•━━━━━━━━━━━━━━━━━━•\n\n"
                "<b>• You must join our channels to use the bot.</b>\n"
                "<b>• Please subscribe to the channels below.</b>\n\n"
                "<b>• After subscribing, click (Verify) to continue.</b>\n\n"
                "•━━━━━━━━━━━━━━━━━━•\n"
                "<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ : @o_k_60</b>"
            )
            bot.send_photo(chat_id, photo_url, caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, "<b>🔒 Force subscription is enabled but no channels added!</b>", parse_mode="HTML")
        return

    # إذا كان المستخدم مسموحاً له، نعرض قائمة الدول
    # هذا هو الكود الذي كان موجوداً في /start سابقاً، ولكن بدون إعادة إرسال الكيبورد الرئيسي
    # نرسل رسالة جديدة تحتوي على الدول مع Inline Keyboard
    show_countries_menu(user_id, chat_id)


def show_countries_menu(user_id, chat_id):
    """دالة مساعدة لعرض قائمة الدول (Inline Keyboard)"""
    # بناء قائمة الدول بنفس الطريقة القديمة
    inline_keyboard = []
    all_buttons = []

    user_data = get_user(user_id)
    private_combo = user_data[7] if user_data else None
    all_combos = get_all_combos()

    # Private combo first
    if private_combo and private_combo in COUNTRY_MAP:
        short, _ = COUNTRY_MAP[private_combo]
        name, flag, _ = COUNTRY_CODES.get(private_combo, (private_combo, "🌍", ""))
        btn = {
            "text": f"{name} (Private)",
            "callback_data": f"country_{private_combo}_",
        }
        if short in FLAG_EMOJI_IDS:
            btn["icon_custom_emoji_id"] = FLAG_EMOJI_IDS[short]
        all_buttons.append(btn)

    # Public combos
    for code, service in all_combos:
        if code in COUNTRY_MAP:
            short, _ = COUNTRY_MAP[code]
            name, flag, _ = COUNTRY_CODES.get(code, (code, "🌍", ""))
            button_text = f"{name}" + (f"/{service}" if service else "")
            btn = {
                "text": button_text,
                "callback_data": f"country_{code}_{service}",
            }
            if short in FLAG_EMOJI_IDS:
                btn["icon_custom_emoji_id"] = FLAG_EMOJI_IDS[short]
            all_buttons.append(btn)

    # Divide buttons into rows of 2
    for i in range(0, len(all_buttons), 2):
        inline_keyboard.append(all_buttons[i:i+2])

    # Admin panel button (if admin)
    if is_admin(user_id):
        admin_btn = {
            "text": "🔐 Admin Panel",
            "callback_data": "admin_panel",
        }
        inline_keyboard.append([admin_btn])

    reply_markup = json.dumps({"inline_keyboard": inline_keyboard})

    # ✅ النص الجديد مع الإيموجي المتحرك
    fancy_text = "<tg-emoji emoji-id='6109472342973352814'>🌍</tg-emoji> <b>Available countries:</b>"

    bot.send_message(
        chat_id,
        fancy_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


@bot.message_handler(func=lambda message: message.text == "📢 Channel")
def handle_channel(message):
    channel_link = "https://t.me/speed010speedd"
    bot.reply_to(message, f"📢 Our channel: {channel_link}")


@bot.message_handler(func=lambda message: message.text == "🙏 Help")
def handle_help(message):
    help_text = (
        "Customer service is not always online 24 hours a day. "
        "When they go online, they will reply to your questions as soon as possible.\n"
        "------------------\n"
        "💁🏼‍♀️ Online customer service @o_k_60"
    )
    bot.reply_to(message, help_text)


@bot.message_handler(func=lambda message: message.text == "🌿 Method")
def handle_method(message):
    whatsapp_link = "https://whatsapp.com/channel/0029VbBhLc3L2ATxZdcDGI3K"
    bot.reply_to(message, f"🌿 WhatsApp Channel: {whatsapp_link}")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified, you can now use the bot.", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't subscribed yet", show_alert=True)
        # Resend force subscribe message
        markup = force_sub_markup()
        if markup:
            photo_url = "https://i.ibb.co/cc0NFv1f/IMG-20260117-085419-964.jpg"
            caption = (
                "🔐 <b>𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 | Required</b>\n"
                "•━━━━━━━━━━━━━━━━━━•\n\n"
                "<b>• You must join our channels to use the bot.</b>\n"
                "<b>• Please subscribe to the channels below.</b>\n\n"
                "<b>• After subscribing, click (Verify) to continue.</b>\n\n"
                "•━━━━━━━━━━━━━━━━━━•\n"
                "<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ : @o_k_60</b>"
            )
            bot.send_photo(
                call.message.chat.id,
                photo_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=markup
            )
            
            
def get_animated_flag_by_code(country_code):
    """إرجاع العلم المتحرك لرمز الدولة إن وجد، وإلا العلم العادي"""
    # الحصول على المختصر من COUNTRY_MAP (مثل "EG" من "20")
    short = COUNTRY_MAP.get(country_code, (None, None))[0]
    if short and short in ANIMATED_FLAGS_HTML:
        return ANIMATED_FLAGS_HTML[short]
    # إذا لم نجد، نرجع العلم العادي من COUNTRY_CODES
    return COUNTRY_CODES.get(country_code, ("", "🌍", ""))[1]

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        bot.send_message(chat_id, "<b>🔒 You must subscribe to the channels to use the bot.</b>", parse_mode="HTML", reply_markup=markup)
        return

    parts = call.data.split("_", 2)
    country_code = parts[1]
    service = parts[2] if len(parts) > 2 else ''
    
    available_numbers = get_available_numbers(country_code, service, user_id)
    
    if not available_numbers:
        error_msg = "<b>❌ نعتذر، لا توجد أرقام متاحة حالياً لهذه الدولة.</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 العودة لاختيار دولة أخرى", callback_data="back_to_countries"))
        bot.edit_message_text(error_msg, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        return

    count_to_pick = min(3, len(available_numbers))
    selected_numbers = random.sample(available_numbers, count_to_pick)
    
    old_user = get_user(user_id)
    if old_user and old_user[5]:
        for old_num in old_user[5].split(','):
            release_number(old_num)
    
    numbers_to_save = ",".join(selected_numbers)
    for num in selected_numbers:
        assign_number_to_user(user_id, num)
        
    save_user(user_id, country_code=country_code, assigned_number=numbers_to_save)
    
    # الحصول على اسم الدولة والعلم المتحرك
    name = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))[0]
    flag = get_animated_flag_by_code(country_code)
    service_display = f"/{service}" if service else ""
    
    msg_text = (
        f"<b>{flag} {name}{service_display} - New Numbers:</b>\n\n"
        f"<b> Status :</b> <tg-emoji emoji-id='6120673192479560513'>⏳</tg-emoji> Waiting for SMS\n"
        f"<i>𝐏𝐫𝐞𝐬𝐬 𝐭𝐡𝐞 𝐧𝐮𝐦𝐛𝐞𝐫 𝐭𝐨 𝐜𝐨𝐩𝐲 <tg-emoji emoji-id='6111423679759911578'>📋</tg-emoji></i>"
    )

    markup = types.InlineKeyboardMarkup()
    for num in selected_numbers:
        markup.add(types.InlineKeyboardButton(
            text=f" {num}",
            copy_text=types.CopyTextButton(text=str(num)),
            icon_custom_emoji_id="6120858395764331610"  # أيقونة 📞 متحركة
        ))

    markup.add(types.InlineKeyboardButton(
        text=" Change Number",
        callback_data=f"change_num_{country_code}_{service}",
        icon_custom_emoji_id="5264727218734524899",
        style="danger"
    ))
    markup.add(types.InlineKeyboardButton(
        text=" Change Country",
        callback_data="back_to_countries",
        icon_custom_emoji_id="5352759161945867747"
    ))

    try:
        bot.edit_message_text(msg_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    user_id = call.from_user.id
    data = call.data.replace("change_num_", "")
    if '_' in data:
        country_code, service = data.split('_', 1)
    else:
        country_code = data
        service = ''

    available_numbers = get_available_numbers(country_code, service, user_id)
    
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ لا توجد أرقام متاحة.", show_alert=True)
        return

    count_to_pick = min(3, len(available_numbers))
    selected_numbers = random.sample(available_numbers, count_to_pick)

    old_user = get_user(user_id)
    if old_user and old_user[5]:
        for old_num in old_user[5].split(','):
            release_number(old_num)
        
    numbers_to_save = ",".join(selected_numbers)
    for num in selected_numbers:
        assign_number_to_user(user_id, num)
        
    save_user(user_id, assigned_number=numbers_to_save)

    # الحصول على اسم الدولة والعلم المتحرك
    name = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))[0]
    flag = get_animated_flag_by_code(country_code)
    service_display = f"/{service}" if service else ""

    msg_text = (
        f"<b>{flag} {name}{service_display} - New Numbers:</b>\n\n"
        f"<b> Status :</b> <tg-emoji emoji-id='6120673192479560513'>⏳</tg-emoji> Waiting for SMS\n"
        f"<i>𝐏𝐫𝐞𝐬𝐬 𝐭𝐡𝐞 𝐧𝐮𝐦𝐛𝐞𝐫 𝐭𝐨 𝐜𝐨𝐩𝐲 <tg-emoji emoji-id='6111423679759911578'>📋</tg-emoji></i>"
    )

    markup = types.InlineKeyboardMarkup()
    for num in selected_numbers:
        markup.add(types.InlineKeyboardButton(
            text=f" {num}",
            copy_text=types.CopyTextButton(text=str(num)),
            icon_custom_emoji_id="6120858395764331610"
        ))

    markup.add(types.InlineKeyboardButton(
        text=" Change Number",
        callback_data=f"change_num_{country_code}_{service}",
        icon_custom_emoji_id="5264727218734524899",
        style="danger"
    ))
    markup.add(types.InlineKeyboardButton(
        text=" Change Country",
        callback_data="back_to_countries",
        icon_custom_emoji_id="5352759161945867747"
    ))

    try:
        bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id, "✅ تم تغيير الـ 3 أرقام")
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Build countries menu with premium emojis and service names
    inline_keyboard = []
    all_buttons = []

    user_data = get_user(user_id)
    private_combo = user_data[7] if user_data else None
    all_combos = get_all_combos()  # الآن تعيد قائمة من (country_code, service)

    # Private combo first (لا يدعم الخدمة حالياً)
    if private_combo and private_combo in COUNTRY_MAP:
        short, _ = COUNTRY_MAP[private_combo]
        name, flag, _ = COUNTRY_CODES.get(private_combo, (private_combo, "🌍", ""))
        btn = {
            "text": f"{name} (Private)",
            "callback_data": f"country_{private_combo}_",  # خدمة فارغة
        }
        if short in FLAG_EMOJI_IDS:
            btn["icon_custom_emoji_id"] = FLAG_EMOJI_IDS[short]
        all_buttons.append(btn)

    # Public combos (مع الخدمة)
    for code, service in all_combos:
        if code in COUNTRY_MAP:
            short, _ = COUNTRY_MAP[code]
            name, flag, _ = COUNTRY_CODES.get(code, (code, "🌍", ""))
            # نص الزر: اسم الدولة + اسم الخدمة إذا موجودة
            button_text = f"{name}" + (f"/{service}" if service else "")
            btn = {
                "text": button_text,
                "callback_data": f"country_{code}_{service}",
            }
            if short in FLAG_EMOJI_IDS:
                btn["icon_custom_emoji_id"] = FLAG_EMOJI_IDS[short]
            all_buttons.append(btn)

    # Divide buttons into rows of 2
    for i in range(0, len(all_buttons), 2):
        inline_keyboard.append(all_buttons[i:i+2])

    # Admin panel button (if admin)
    if is_admin(user_id):
        admin_btn = {
            "text": "🔐 Admin Panel",
            "callback_data": "admin_panel",
        }
        inline_keyboard.append([admin_btn])

    reply_markup = json.dumps({"inline_keyboard": inline_keyboard})

    # ✅ نفس النص الجديد هنا أيضاً
    fancy_text = "<tg-emoji emoji-id='6109472342973352814'>🌍</tg-emoji> <b>Available countries:</b>"

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=fancy_text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error editing message: {e}")
        bot.answer_callback_query(call.id)

# ======================
# 🔐 لوحة التحكم الإدارية (محدثة)
# ======================
user_states = {}

def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    
    # 1. زر حالة البوت
    status_icon = "🟢" if not is_maintenance_mode() else "🔴"
    status_text = "الآن: يعمل بنجاح" if not is_maintenance_mode() else "الآن: قيد الصيانة"
    markup.add(types.InlineKeyboardButton(f"{status_icon} {status_text} {status_icon}", callback_data="toggle_maintenance"))
    
    # 2. قسم إدارة الكومبوهات
    markup.row(
        types.InlineKeyboardButton("📥 إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف كومبو", callback_data="admin_del_combo")
    )
    
    # 3. قسم الإحصائيات والتقارير
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report")
    )
    
    # 4. قسم الإذاعة (Broadcast)
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    
    # 5. قسم إدارة المستخدمين
    markup.row(
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info")
    )
    
    # 6. قسم الإعدادات المتقدمة (تم إضافة زر إدارة قنوات الإرسال هنا)
    markup.row(
        types.InlineKeyboardButton("🔗 إشتراك", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo"),
        types.InlineKeyboardButton("🖥️ اللوحات", callback_data="admin_dashboards")
    )
    # الزر الجديد تحتهم مباشرة بشكل عريض ومميز
    markup.row(
        types.InlineKeyboardButton("📢 إدارة قنوات الإرسال (Chat IDs)", callback_data="manage_broadcast_chats")
    )

    # 7. زر الخروج
    markup.add(types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back_to_countries"))
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    # التحقق من الرتبة أولاً
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ عذراً، هذا القسم للمطورين فقط.", show_alert=True)
        return

    # النص المنسق فخم جداً
    admin_text = (
        "<b>❍─── <u>𝐋𝐎𝐆𝐈𝐍 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</u> ───❍</b>\n\n"
        "<b>👋 مرحباً بك يا مطور في لوحة التحكم.</b>\n\n"
        "<b>⚙️ يمكنك التحكم في كامل وظائف البوت من هنا.</b>\n"
        "<b>⚠️ تنبيه: أي تغيير في الإعدادات يؤثر على المستخدمين فوراً.</b>\n\n"
        "<b>────────────────────</b>\n"
        "<b>إحصائيات سريعة:</b>\n"
        "<b>• حالة السيرفر: <u>Online</u> ✅</b>\n"
        f"<b>• الوقت الحالي: <u>{datetime.now().strftime('%H:%M')}</u></b>\n"
        "<b>────────────────────</b>"
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=admin_main_menu(),
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Admin Panel Error: {e}")

    
# ======================
# 📌 ميزة الاشتراك الإجباري في لوحة الإدارة
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id):
        return

    channels = get_all_force_sub_channels(enabled_only=False)
    text = "⚙️ إدارة قنوات الاشتراك الإجباري:\n"
    text += f"إجمالي القنوات: {len(channels)}\n"
    text += "──────────────────\n"

    markup = types.InlineKeyboardMarkup()
    for ch_id, url, desc in channels:
        # جلب الحالة بدقة
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (ch_id,))
        enabled = c.fetchone()[0]
        conn.close()
        status = "✅" if enabled else "❌"
        btn_text = f"{status} {desc or url[:25]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"edit_force_ch_{ch_id}"))

    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def handle_maintenance_toggle(call):
    if not is_admin(call.from_user.id): return
    
    # عكس الحالة الحالية
    current_status = is_maintenance_mode()
    set_maintenance_mode(not current_status) # دالة الحفظ
    
    new_status_text = "🔓 تم فتح البوت للجميع" if current_status else "🔒 تم قفل البوت (وضع الصيانة)"
    
    # إشعار سريع للأدمن
    bot.answer_callback_query(call.id, new_status_text, show_alert=True)
    
    # تحديث اللوحة فوراً ليتغير شكل الزر
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())
    
# --- إضافة قناة جديدة ---
@bot.callback_query_handler(func=lambda call: call.data == "add_force_ch")
def add_force_ch_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_force_ch_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (مثل: https://t.me/xxx أو @xxx):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_force_ch_url")
def add_force_ch_step2(message):
    url = message.text.strip()
    if not (url.startswith("@") or url.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    user_states[message.from_user.id] = {"step": "add_force_ch_desc", "url": url}
    bot.reply_to(message, "أدخل وصفًا للقناة (أو اترك فارغًا):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_force_ch_desc")
def add_force_ch_step3(message):
    data = user_states[message.from_user.id]
    url = data["url"]
    desc = message.text.strip()
    if add_force_sub_channel(url, desc):
        bot.reply_to(message, f"✅ تم إضافة القناة:\n{url}\nالوصف: {desc or '—'}")
    else:
        bot.reply_to(message, "❌ القناة موجودة مسبقًا!")
    del user_states[message.from_user.id]


# --- تعديل/حذف قناة فردية ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_force_ch_"))
def edit_force_ch(call):
    if not is_admin(call.from_user.id):
        return
    try:
        ch_id = int(call.data.split("_", 3)[3])
    except:
        return
    # جلب بيانات القناة
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (ch_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "❌ القناة غير موجودة!", show_alert=True)
        return

    url, desc, enabled = row
    status = "مفعلة" if enabled else "معطلة"
    text = f"🔧 إدارة القناة:\nالرابط: {url}\nالوصف: {desc or '—'}\nالحالة: {status}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل الوصف", callback_data=f"edit_desc_{ch_id}"))
    if enabled:
        markup.add(types.InlineKeyboardButton("❌ تعطيل", callback_data=f"toggle_ch_{ch_id}"))
    else:
        markup.add(types.InlineKeyboardButton("✅ تفعيل", callback_data=f"toggle_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==========================================
# 📢 إدارة معرفات الشات (Chat IDs) من لوحة الإدارة
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "manage_broadcast_chats")
def manage_chats_ui(call):
    if not is_admin(call.from_user.id): return
    chats = get_all_broadcast_chats()
    text = "<b>📋 قائمة قنوات الإرسال الحالية:</b>\n\n"
    if not chats:
        text += "🚫 لا توجد قنوات مسجلة حالياً."
    else:
        for idx, cid in enumerate(chats, 1):
            text += f"{idx}- <code>{cid}</code>\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ إضافة معرف Chat ID", callback_data="add_new_chat_id"))
    if chats:
        markup.row(types.InlineKeyboardButton("🗑️ حذف معرف", callback_data="delete_chat_prompt"))
    markup.row(types.InlineKeyboardButton("🔙 العودة للأدمن", callback_data="admin_panel"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "add_new_chat_id")
def ask_for_chat_id(call):
    msg = bot.send_message(call.message.chat.id, "<b>ارسل الـ Chat ID الجديد الآن (يجب أن يبدأ بـ -100):</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, save_new_chat_id_step)

def save_new_chat_id_step(message):
    chat_id = message.text.strip()
    if chat_id.startswith("-"):
        if add_broadcast_chat(chat_id):
            bot.reply_to(message, f"✅ تم إضافة المعرف <code>{chat_id}</code> بنجاح!", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ هذا المعرف موجود بالفعل.")
    else:
        bot.reply_to(message, "❌ صيغة المعرف غير صحيحة.")

@bot.callback_query_handler(func=lambda call: call.data == "delete_chat_prompt")
def delete_chat_prompt(call):
    msg = bot.send_message(call.message.chat.id, "<b>ارسل الـ Chat ID الذي تريد حذفه بدقة:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_delete_chat)

def process_delete_chat(message):
    chat_id = message.text.strip()
    delete_broadcast_chat(chat_id)
    bot.reply_to(message, f"🗑️ تم حذف المعرف <code>{chat_id}</code> من القائمة.", parse_mode="HTML")
    

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_ch_"))
def toggle_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    toggle_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "🔄 تم تغيير حالة القناة", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def del_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    if delete_force_sub_channel(ch_id):
        bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل الحذف!", show_alert=True)
    admin_force_sub(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_desc_step1(call):
    ch_id = int(call.data.split("_", 2)[2])
    user_states[call.from_user.id] = f"edit_desc_{ch_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"edit_force_ch_{ch_id}"))
    bot.edit_message_text("أدخل الوصف الجديد:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), str) and user_states[msg.from_user.id].startswith("edit_desc_"))
def edit_desc_step2(message):
    try:
        ch_id = int(user_states[message.from_user.id].split("_")[2])
        desc = message.text.strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET description = ? WHERE id = ?", (desc, ch_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ تم تحديث الوصف!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("📤 أرسل ملف الكومبو بصيغة TXT", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id):
        return
    if user_states.get(message.from_user.id) != "waiting_combo_file":
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!")
            return

        first_num = clean_number(lines[0])
        country_code = None
        for code in COUNTRY_CODES:
            if first_num.startswith(code):
                country_code = code
                break
        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة من الأرقام!")
            return

        # تخزين البيانات مؤقتاً لاستكمالها في الخطوة التالية
        user_states[message.from_user.id] = {
            'step': 'waiting_service_name',
            'country_code': country_code,
            'numbers': lines
        }

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تخطي (بدون خدمة)", callback_data="skip_service"))
        bot.reply_to(
            message, 
            f"✅ تم التعرف على الدولة: {COUNTRY_CODES[country_code][1]} {COUNTRY_CODES[country_code][0]}\n"
            "الرجاء إدخال اسم الخدمة (مثل WS, Tel, Ins) أو اضغط تخطي:",
            reply_markup=markup
        )

    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "skip_service")
def skip_service_callback(call):
    if call.from_user.id not in user_states or not isinstance(user_states[call.from_user.id], dict) or user_states[call.from_user.id].get('step') != 'waiting_service_name':
        bot.answer_callback_query(call.id, "⚠️ لا توجد عملية معلقة")
        return
    data = user_states[call.from_user.id]
    country_code = data['country_code']
    numbers = data['numbers']
    service = ''  # خدمة فارغة
    
    save_combo(country_code, numbers, service)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.edit_message_text(
        f"✅ تم حفظ الكومبو لدولة {flag} {name}\n🔢 عدد الأرقام: {len(numbers)}",
        call.message.chat.id,
        call.message.message_id
    )
    del user_states[call.from_user.id]

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get('step') == 'waiting_service_name')
def handle_service_name(message):
    data = user_states[message.from_user.id]
    country_code = data['country_code']
    numbers = data['numbers']
    service = message.text.strip()
    
    save_combo(country_code, numbers, service)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.reply_to(
        message,
        f"✅ تم حفظ الكومبو لدولة {flag} {name} / {service}\n🔢 عدد الأرقام: {len(numbers)}"
    )
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    combos = get_all_combos()  # الآن تعيد قائمة (country_code, service)
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!")
        return
    markup = types.InlineKeyboardMarkup()
    for code, service in combos:
        if code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[code]
            service_txt = f"/{service}" if service else ""
            markup.add(types.InlineKeyboardButton(
                f"{flag} {name}{service_txt}",
                callback_data=f"del_combo_{code}_{service}"
            ))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("اختر الكومبو للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    data = call.data.replace("del_combo_", "")
    if '_' in data:
        code, service = data.split('_', 1)
    else:
        code = data
        service = ''
    delete_combo(code, service)
    name, flag, _ = COUNTRY_CODES.get(code, ("Unknown", "🌍", ""))
    service_txt = f"/{service}" if service else ""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(f"✅ تم حذف الكومبو: {flag} {name}{service_txt}", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        return
    total_users = len(get_all_users())
    combos = get_all_combos()
    total_numbers = sum(len(get_combo(code, service)) for code, service in combos)
    otp_count = len(get_otp_logs())
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(
        f"📊 إحصائيات البوت:\n"
        f"👥 المستخدمين النشطين: {total_users}\n"
        f"🌐 الدول المضافة: {len(combos)}\n"
        f"📞 إجمالي الأرقام: {total_numbers}\n"
        f"🔑 إجمالي الأكواد المستلمة: {otp_count}",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id):
        return
    try:
        report = "📊 تقرير شامل عن البوت\n" + "="*40 + "\n\n"
        # المستخدمون
        report += "👥 المستخدمون:\n"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        for u in users:
            status = "محظور" if u[6] else "نشط"
            report += f"ID: {u[0]} | @{u[1] or 'N/A'} | الرقم: {u[5] or 'N/A'} | الحالة: {status}\n"
        report += "\n" + "="*40 + "\n\n"
        # الأكواد
        report += "🔑 سجل الأكواد:\n"
        c.execute("SELECT * FROM otp_logs")
        logs = c.fetchall()
        for log in logs:
            user_info = get_user_info(log[5]) if log[5] else None
            user_tag = f"@{user_info[1]}" if user_info and user_info[1] else f"ID:{log[5] or 'N/A'}"
            report += f"الرقم: {log[1]} | الكود: {log[2]} | المستخدم: {user_tag} | الوقت: {log[4]}\n"
        conn.close()
        report += "\n" + "="*40 + "\n\n"
        report += "تم إنشاء التقرير في: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لحظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لفك حظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"✅ تم فك حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة للإرسال للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    bot.reply_to(message, f"✅ تم الإرسال إلى {success}/{len(users)} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, "أرسل الرسالة:")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, "").startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"✅ تم الإرسال للمستخدم {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود!")
            return
        status = "محظور" if user[6] else "نشط"
        info = f"👤 معلومات المستخدم:\n"
        info += f"🆔: {user[0]}\n"
        info += f".Username: @{user[1] or 'N/A'}\n"
        info += f"الاسم: {user[2] or ''} {user[3] or ''}\n"
        info += f"الرقم المخصص: {user[5] or 'N/A'}\n"
        info += f"الحالة: {status}"
        bot.reply_to(message, info)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "set_force_sub_channel")
def admin_set_force_sub_channel_step2(message):
    channel = message.text.strip()
    if not (channel.startswith("@") or channel.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    set_setting("force_sub_channel", channel)
    bot.reply_to(message, f"✅ تم تعيين القناة: {channel}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_enable_force_sub")
def admin_enable_force_sub(call):
    set_setting("force_sub_enabled", "1")
    bot.answer_callback_query(call.id, "✅ تم تفعيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_disable_force_sub")
def admin_disable_force_sub(call):
    set_setting("force_sub_enabled", "0")
    bot.answer_callback_query(call.id, "❌ تم تعطيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

# ======================
# 🖥️ ميزة لوحات الأرقام المتعددة
# ======================
def get_dashboards():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM dashboards")
    rows = c.fetchall()
    conn.close()
    return rows

def save_dashboard(base_url, ajax_path, login_page, login_post, username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO dashboards (base_url, ajax_path, login_page, login_post, username, password)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (base_url, ajax_path, login_page, login_post, username, password))
    conn.commit()
    conn.close()

def delete_dashboard(dash_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM dashboards WHERE id=?", (dash_id,))
    conn.commit()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "admin_dashboards")
def admin_dashboards(call):
    if not is_admin(call.from_user.id):
        return
    dashboards = get_dashboards()
    markup = types.InlineKeyboardMarkup()
    if dashboards:
        for d in dashboards:
            markup.add(types.InlineKeyboardButton(f"لوحة {d[0]}", callback_data=f"view_dashboard_{d[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة لوحة", callback_data="add_dashboard"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("🖥️ لوحات الأرقام:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_dashboard_"))
def view_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    dashboards = get_dashboards()
    dash = next((d for d in dashboards if d[0] == dash_id), None)
    if not dash:
        bot.answer_callback_query(call.id, "❌ اللوحة غير موجودة!")
        return
    text = f"لوحة {dash_id}:\nBase: {dash[1]}\nUsername: {dash[5]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_dashboard_{dash_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_dashboards"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_dashboard_"))
def del_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    delete_dashboard(dash_id)
    bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    admin_dashboards(call)

@bot.callback_query_handler(func=lambda call: call.data == "add_dashboard")
def add_dashboard_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_dash_base"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_dashboards"))
    bot.edit_message_text("أدخل Base URL:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_dash_base")
def add_dashboard_step2(message):
    user_states[message.from_user.id] = {"step": "ajax", "base": message.text}
    bot.reply_to(message, "أدخل AJAX Path:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "ajax")
def add_dashboard_step3(message):
    user_states[message.from_user.id]["ajax"] = message.text
    user_states[message.from_user.id]["step"] = "login_page"
    bot.reply_to(message, "أدخل Login Page URL:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "login_page")
def add_dashboard_step4(message):
    user_states[message.from_user.id]["login_page"] = message.text
    user_states[message.from_user.id]["step"] = "login_post"
    bot.reply_to(message, "أدخل Login POST URL:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "login_post")
def add_dashboard_step5(message):
    user_states[message.from_user.id]["login_post"] = message.text
    user_states[message.from_user.id]["step"] = "username"
    bot.reply_to(message, "أدخل Username:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "username")
def add_dashboard_step6(message):
    user_states[message.from_user.id]["username"] = message.text
    user_states[message.from_user.id]["step"] = "password"
    bot.reply_to(message, "أدخل Password:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "password")
def add_dashboard_step7(message):
    data = user_states[message.from_user.id]
    save_dashboard(
        data["base"],
        data["ajax"],
        data["login_page"],
        data["login_post"],
        data["username"],
        message.text
    )
    bot.reply_to(message, "✅ تم إضافة اللوحة بنجاح!")
    del user_states[message.from_user.id]

# ======================
# 👤 ميزة كومبو برايفت
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة كومبو برايفت", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح كومبو برايفت", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("👤 كومبو برايفت:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for code in get_all_combos():
            if code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[code]
                buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"select_private_{uid}_{code}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_private_"))
def select_private_combo(call):
    parts = call.data.split("_")
    uid = int(parts[2])
    country_code = parts[3]
    save_user(uid, private_combo_country=country_code)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.answer_callback_query(call.id, f"✅ تم تعيين كومبو برايفت لـ {uid} - {flag} {name}", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user_id")
def del_private_combo_step2(message):
    try:
        uid = int(message.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(message, f"✅ تم مسح الكومبو البرايفت للمستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    del user_states[message.from_user.id]

# ======================
# 🆕 دالة جديدة: جلب الأرقام المتاحة (غير المستخدمة) مع دعم private
# ======================
def get_available_numbers(country_code, service='', user_id=None):
    all_numbers = get_combo(country_code, service, user_id)
    if not all_numbers:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()
    available = [num for num in all_numbers if num not in used_numbers]
    return available

# ======================
# 🔄 الدالة المعدلة لإرسال OTP للمستخدم + الجروب
# ======================
# 🔄 الدالة المعدلة لإرسال OTP للمستخدم + الجروب
def send_otp_to_user_and_group(date_str, number, sms, service_api=None, thread_id=None):
    try:
        # تأخير عشوائي
        time.sleep(random.uniform(1.0, 3.0))

        # استخراج البيانات الأساسية
        otp_code = extract_otp(sms)
        country_name, country_flag, country_code = get_country_info(number)  # <-- 3 قيم هنا (صح)
        
        # ✅ معالجة الخدمة مع الأيقونة (أضيفت هنا)
        service = service_api if service_api else detect_service(sms)
        service_icon = get_service_icon(service, sms)
        service_display = f"{service_icon} {service}"

        # تسجيل العملية في القاعدة
        try:
            user_id = get_user_by_number(number)
            log_otp(number, otp_code, sms, user_id)
        except:
            user_id = None

        # ───── إرسال خاص للمستخدم ─────
        if user_id:
            try:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("👤 Owner", url="https://t.me/o_k_60"),
                    types.InlineKeyboardButton("📢 Channel", url="https://t.me/speed010speedd")
                )
                bot.send_message(
                    user_id,
                    (f"<b><u>✨ SPEED OTP Received ✨</u></b>\n\n"
                     f"🌍 <b>Country:</b> {country_name} {country_flag}\n"
                     f"⚙ <b>Service:</b> {service_display}\n"  # <-- الآن service_display معرف
                     f"☎ <b>Number:</b> <code>{number}</code>\n"
                     f"🕒 <b>Time:</b> {date_str}\n\n"
                     f"🔐 <b>Code:</b> <code>{otp_code}</code>"),
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception as e:
                if "Too Many Requests" in str(e):
                    print(f"⚠️ ضغط إرسال للمستخدم {user_id}.. سيتم التخطي للجروب")

        # ───── إرسال للجروب ─────
        text = format_message(date_str, number, sms)
        
        for attempt in range(3):
            try:
                if send_to_telegram_group(text, otp_code, sms, thread_id=thread_id):
                    print(f"✅ [SUCCESS] GROUP | {number}" + (f" (thread: {thread_id})" if thread_id else ""))
                    break
                else:
                    break
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"⚠️ تليجرام مضغوط.. محاولة {attempt+1} للرقم {number} بعد 6 ثواني")
                    time.sleep(6)
                    continue
                else:
                    print(f"❌ [ERROR] GROUP | {e}")
                    break

    except Exception as e:
        print(f"⚠️ Error in sending Thread: {e}")

# ======================
# 📡 دوال الاتصال بالـ Dashboard (كما هي من الملف الأصلي)
# ======================
# ======================
# 📡 دوال الاتصال بالـ API (نظام Albrans المطور)
# ======================

# لم نعد بحاجة لعمل headers معقدة ولا لمحاكاة متصفح أندرويد لأن الـ API مخصص للبرمجة
session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "Albrans-Monitor/2.0"
})

def retry_request(func, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    """دالة إعادة المحاولة في حالة وقوع خطأ في الشبكة"""
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️ محاولة {attempt + 1}/{max_retries} فشلت.. انتظار {retry_delay} ثانية")
                time.sleep(retry_delay)
            else:
                print(f"❌ فشلت جميع المحاولات بعد {max_retries} مرات.")
                raise
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            raise

# 🛑 دالة login_for_dashboard لم تعد مستخدمة في نظام الـ API 
# ولكن سنبقيها كـ "دالة فارغة" إذا كان الـ Loop يناديها لتجنب الأخطاء
def login_for_dashboard(dash):
    # في نظام الـ API التوكن هو تسجيل الدخول
    dash["is_logged_in"] = True
    return True

def build_api_url_for_dashboard(dash):
    """بناء رابط الطلب بناءً على التاريخ الحالي والتوكن"""
    # التاريخ يبدأ من بداية اليوم (00:00:00) لضمان جلب كل جديد
    start_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
    
    # بناء الرابط حسب التنسيق الذي أرسله المشرف
    # لاحظ أننا استخدمنا dt1 فقط لأن dt2 السيرفر بيعتبرها "الآن" لو سبناها فاضية
    params = {
        "token": dash["token"],
        "dt1": start_date,
        "dt2": "", 
        "records": dash["records"]
    }
    
    # تحويل القاموس لرابط Query String
    query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    return f"{dash['api_url']}?{query_string}"

def fetch_api_json_for_dashboard(dash, url):
    """جلب بيانات الـ JSON ومعالجة الأخطاء الشائعة"""
    FETCH_TIMEOUT = 15 

    def do_fetch():
        r = dash["session"].get(url, timeout=FETCH_TIMEOUT)
        
        if r.status_code == 200:
            try:
                return r.json()
            except:
                print(f"[{dash['name']}] ❌ فشل في تحليل الـ JSON")
                return None
        elif r.status_code == 503:
            print(f"[{dash['name']}] ⚠️ السيرفر مضغوط (503).")
            return None
        else:
            print(f"[{dash['name']}] ❌ خطأ سيرفر: {r.status_code}")
            return None

    try:
        return retry_request(do_fetch, max_retries=2, retry_delay=3)
    except:
        return None

def extract_rows_from_json(j):
    """
    توحيد شكل بيانات الـ API
    يدعم dict / list / aaData / data / rows
    """
    if j is None:
        return []

    # أشهر مفاتيح APIs
    for key in ("data", "rows", "aaData", "aa_data"):
        if isinstance(j, dict) and key in j and isinstance(j[key], list):
            return j[key]

    # لو رجع List مباشر
    if isinstance(j, list):
        return j

    # آخر حل: أي قيمة List داخل dict
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v

    return []

def fetch_data():
    if not DASHBOARD_CONFIGS:
        return []

    dash = DASHBOARD_CONFIGS[0]
    today = datetime.now().strftime('%Y-%m-%d 00:00:00')

    try:
        url = (
            f"{dash['api_url']}?"
            f"token={dash['token']}&"
            f"dt1={quote_plus(today)}&"
            f"records={dash['records']}"
        )
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            return extract_rows_from_json(r.json())
    except Exception as e:
        print(f"❌ API Error: {e}")

    return []

def clean_html(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def clean_number(number):
    if not number:
        return ""
    number = re.sub(r'\D', '', str(number))
    return number

def row_to_tuple(row, dash_type):
    """تحويل الصف إلى بيانات موحدة بناءً على نوع اللوحة"""
    try:
        if dash_type == "msi_panel":
            # تنسيق MSI Panel (قائمة)
            if len(row) >= 6:
                date_str = str(row[0]) if row[0] else ""
                number = str(row[2]) if row[2] else ""
                message = str(row[5]) if row[5] else ""
                key = f"{number}_{message}_{date_str}"
                return date_str, number, message, key
            return "", "", "", None

        elif dash_type == "ims_panel":
            # تنسيق IMS Panel (قائمة من 6 عناصر)
            if len(row) >= 6:
                date_str = str(row[0]) if row[0] else ""
                number = str(row[2]) if row[2] else ""
                sender = str(row[3]) if row[3] else ""
                message = str(row[5]) if row[5] else ""
                
                # ✅ إذا كان الـ message فارغ، استخدم sender فقط
                if not message and sender:
                    full_message = sender
                elif message and sender:
                    full_message = f"{sender} {message}".strip()
                else:
                    full_message = message or sender or ""
                    
                # ✅ المفتاح يشمل التاريخ (زي الكود الصغير)
                key = f"{number}_{full_message}_{date_str}"
                return date_str, number, full_message, key
            return "", "", "", None

        elif dash_type == "new_format":
            # التنسيق الجديد (قاموس)
            date_str = str(row.get('dt', ''))
            number   = str(row.get('num', ''))
            sms      = str(row.get('message', ''))
            key      = f"{number}_{sms}_{date_str}"
            return date_str, number, sms, key

        elif dash_type == "new_json":
            # التنسيق الثاني (قاموس)
            date_str = str(row.get('dt', ''))
            number   = str(row.get('num', ''))
            sms      = str(row.get('message', ''))
            key      = f"{number}_{sms}_{date_str}"
            return date_str, number, sms, key

        else:  # old_list (افتراضي)
            # التنسيق القديم (قائمة) [Service, Number, Msg, Date]
            if len(row) >= 4:
                service  = str(row[0])
                number   = str(row[1])
                sms      = str(row[2])
                date_str = str(row[3])
                key      = f"{number}_{sms}_{date_str}"
                return date_str, number, sms, key
            return "", "", "", None
    except Exception:
        return "", "", "", None

def get_country_info(number):
    """الحصول على معلومات الدولة مع العلم المتحرك الجاهز"""
    number = number.strip().replace("+", "").replace(" ", "").replace("-", "")

    for code, (name, flag, short) in COUNTRY_CODES.items():
        if number.startswith(code):
            # نحاول نرجع العلم المتحرك الجاهز إذا كان موجوداً
            animated_html = ANIMATED_FLAGS_HTML.get(short)
            if animated_html:
                return name, animated_html, short  # نرجع HTML جاهز بدلاً من الـ ID
            else:
                return name, flag, short  # نرجع العلم العادي

    return "Unknown", "🌍", "UN"


def mask_number(number):
    number = number.strip()
    if len(number) > 8:
        return number[:4] + "⁦⁦•••" + number[-4:]
    return number

def extract_otp(message):
    patterns = [
        r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s]+[‎]?(\d{3,8}(?:[- ]\d{3,4})?)',
        r'(\d{3})[- ](\d{3,4})',
        r'\b(\d{4,8})\b',
        r'[‎](\d{3,8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return ''.join(match.groups())
            return match.group(1).replace(' ', '').replace('-', '')
    all_numbers = re.findall(r'\d{4,8}', message)
    if all_numbers:
        return all_numbers[0]
    return "N/A"

def detect_service(message):
    message_lower = message.lower()

    # القاموس الأساسي (زي ما هو)
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام", "تلي"],
        "#TW": ["twitter", "تويتر", "x"],
        "#GG": ["google", "gmail", "جوجل", "جميل"],
        "#DC": ["discord", "ديسكورد"],
        "#LN": ["line", "لاين"],
        "#VB": ["viber", "فايبر"],
        "#SK": ["skype", "سكايب"],
        "#SC": ["snapchat", "سناب"],
        "#TT": ["tiktok", "تيك توك", "تيك"],
        "#AMZ": ["amazon", "امازون"],
        "#APL": ["apple", "ابل", "icloud"],
        "#MS": ["microsoft", "مايكروسوفت"],
        "#IN": ["linkedin", "لينكد"],
        "#UB": ["uber", "اوبر"],
        "#AB": ["airbnb", "ايربنب"],
        "#NF": ["netflix", "نتفلكس"],
        "#SP": ["spotify", "سبوتيفاي"],
        "#YT": ["youtube", "يوتيوب"],
        "#GH": ["github", "جيت هاب"],
        "#PT": ["pinterest", "بنتريست"],
        "#PP": ["paypal", "باي بال"],
        "#BK": ["booking", "بوكينج"],
        "#TL": ["tala", "تالا"],
        "#OLX": ["olx", "اوليكس"],
        "#STC": ["stcpay", "stc"],
    }

    # ✅ التحقق الأساسي (زي ما هو)
    for service_code, keywords in services.items():
        for keyword in keywords:
            if keyword in message_lower:
                return service_code

    # ✅ Fallback ذكي من صيغة رسالة OTP نفسها
    if "code" in message_lower or "verification" in message_lower:
        if "telegram" in message_lower:
            return "#TG"
        if "whatsapp" in message_lower:
            return "#WP"
        if "facebook" in message_lower:
            return "#FB"
        if "instagram" in message_lower:
            return "#IG"
        if "google" in message_lower or "gmail" in message_lower:
            return "#GG"
        if "twitter" in message_lower or "x.com" in message_lower:
            return "#TW"

    #  آخر حل
    return "Unknown"

def delete_message_after_delay(chat_id, message_id, delay=72000):
    """تحذف الرسالة بعد مرور delay ثانية"""
    time.sleep(delay)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ فشل حذف الرسالة: {e}")

# ----------------------------
def clean_text_for_html(text):
    """تنظيف النص بالكامل من أي أحرف تسبب مشاكل في HTML"""
    if not text:
        return ""
    
    text = str(text)
    
    # استبدال الرموز الخاصة
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    
    # إزالة أي أحرف تحكم أو غير مطبوعة
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # إزالة كل الأحرف اللي ممكن تسبب مشاكل
    text = re.sub(r'[^\x20-\x7E\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', text)
    
    return text
    

def send_to_telegram_group(text, otp_code, full_sms, thread_id=None):
    try:
        # تنظيف النصوص قبل الاستخدام
        clean_full_sms = clean_text_for_html(full_sms)
        clean_otp = clean_text_for_html(otp_code)
        
        # تجهيز الكيبورد مع الأيموجي المتحرك والألوان
        base_keyboard = {
            "inline_keyboard": [
                # الصف الأول - زر الكود (أزرق)
                [
                    {
                        "text": f" {clean_otp}", 
                        "copy_text": {"text": clean_otp},
                        "icon_custom_emoji_id": "5330115548900501467",  # 🔑 متحرك
                        "style": "success"  # أزرق
                    }
                ],
                
                # الصف الثاني - زر نسخ الرسالة (أزرق)
                [
                    {
                        "text": " Copy Message", 
                        "copy_text": {"text": clean_full_sms},
                        "icon_custom_emoji_id": "6109268074328754542",  # 📋 متحرك
                        "style": "success"  # أزرق
                    }
                ],
                
                # الصف الثالث - رابطين جنب بعض
                [
                    {
                        "text": " Channel", 
                        "url": "https://t.me/speed010speedd",
                        "icon_custom_emoji_id": "5247176827016847212",  # 💬 متحرك
                        "style": "danger"  # أخضر
                    },
                    {
                        "text": " Bot Panel", 
                        "url": "https://t.me/LolzFack_bot",
                        "icon_custom_emoji_id": "5372981976804366741",  # 🤖 متحرك
                        "style": "danger"  # أحمر
                    }
                ],
                
                # الصف الرابع - رابط المطور
                [
                    {
                        "text": " Developer", 
                        "url": "https://t.me/o_k_60",
                        "icon_custom_emoji_id": "5323598687648107382",  # 👨‍💻 متحرك
                        "style": "primary"  # أزرق
                    }
                ]
            ]
        }

        # باقي الكود زي ما هو...
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        success_count = 0
        
        broadcast_list = get_all_broadcast_chats()
        
        if not broadcast_list:
            print("⚠️ قائمة جروبات الإرسال فارغة في الداتا بيز!")
            return False

        for chat_id in broadcast_list:
            try:
                # المحاولة الأولى بـ HTML
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(base_keyboard)
                }
                if thread_id:
                    payload["message_thread_id"] = thread_id

                resp = requests.post(url, json=payload, timeout=15)
                
                if resp.status_code == 200:
                    print(f"✅ [SUCCESS] تم الإرسال للجروب: {chat_id}")
                    success_count += 1
                else:
                    # لو فشل HTML، نبعت رسالة بديلة من غير أكواد HTML
                    print(f"⚠️ فشل بـ HTML، جاري الإرسال بدون HTML...")
                    
                    service_code = detect_service(full_sms)
                    plain_text = re.sub(r'<[^>]+>', '', text)
                    
                    if '🔮' in plain_text:
                        plain_text = plain_text.replace('🔮', f'[{service_code}]')
                    else:
                        parts = plain_text.split()
                        if len(parts) >= 3:
                            for i, part in enumerate(parts):
                                if part.startswith('#'):
                                    if i+1 < len(parts):
                                        parts[i+1] = f'[{service_code}]'
                                    break
                            plain_text = ' '.join(parts)
                    
                    payload2 = {
                        "chat_id": chat_id,
                        "text": plain_text,
                        "reply_markup": json.dumps(base_keyboard)  # نفس الكيبورد مع الأيموجي والألوان
                    }
                    if thread_id:
                        payload2["message_thread_id"] = thread_id
                    
                    resp2 = requests.post(url, json=payload2, timeout=15)
                    
                    if resp2.status_code == 200:
                        print(f"✅ [SUCCESS] تم الإرسال بدون HTML: {chat_id}")
                        success_count += 1
                    else:
                        print(f"⚠️ [FAILED] فشل حتى بدون HTML: {resp2.text}")
                        
            except Exception as e:
                print(f"❌ [ERROR] خطأ في الإرسال لـ {chat_id}: {e}")

        return success_count > 0
        
    except Exception as e:
        print(f"❌ [ERROR] في send_to_telegram_group: {e}")
        return False



def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")   # مهم جداً
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def format_message(date_str, number, sms):
    """تنسيق الرسالة مع العلم المتحرك وأيقونة الخدمة"""
    try:
        # جلب المعلومات
        country_name, flag_display, country_code = get_country_info(number)
        masked_num = mask_number(number)
        
        # استخدم النص الأصلي للكشف عن الخدمة والأيقونة (مش المنضف)
        service_code = detect_service(sms)  # استخدم sms الأصلي
        service_icon = get_service_icon(service_code, sms)  # استخدم sms الأصلي
        
        # نظف النص بس للعرض (لو عاوز)
        clean_sms_for_display = clean_text_for_html(sms)
        
        message = (
            f"\n"
            f" {flag_display} #{country_code} {service_icon} {masked_num} \n"
            f""
        )
        return message
    except Exception as e:
        print(f"⚠️ خطأ في format_message: {e}")
        return f"\n {flag_display} #{country_code} {masked_num} \n"

# ======================
# 🔄 الحلقة الرئيسية (معدلة لدعم لوحات متعددة)
# ======================
# ======================
# 🔄 دوال التشغيل الآمنة (محمية ضد التوقف)
# ======================

def run_bot():
    """تشغيل البوت مع خاصية إعادة الاتصال التلقائي"""
    print("[*] Starting bot with infinity polling...")
    while True:
        try:
            # infinity_polling بيعيد الاتصال لوحده لو النت فصل
            # timeout=60 بيخلي الاتصال مفتوح لفترة أطول عشان ميقطعش بسرعة
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Bot Polling Crashed: {e}")
            time.sleep(5)  # استراحة قصيرة قبل إعادة المحاولة

# ============================================================
# 🔄 المراقبة والجلب (Main Loop) - النسخة المحدثة لجميع اللوحات
# ============================================================
# ======================
# 📡 دوال خاصة بلوحة MSI Panel
# ======================

def login_to_msi_panel(dash):
    """تسجيل الدخول إلى لوحة MSI"""
    try:
        print(f"[{dash['name']}] 🔑 محاولة تسجيل الدخول...")
        
        # تحميل صفحة الدخول
        response = dash["session"].get(dash["base_url"], timeout=20)
        
        if response.status_code != 200:
            print(f"[{dash['name']}] ❌ فشل في تحميل الصفحة")
            return False
        
        # استخراج استمارة الدخول
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        
        if not form:
            print(f"[{dash['name']}] ❌ لم يتم العثور على استمارة الدخول")
            return False
        
        # تجهيز بيانات الدخول
        payload = {}
        for tag in form.find_all('input'):
            name = tag.get('name')
            if not name:
                continue
            
            placeholder = tag.get('placeholder', '').lower()
            if 'user' in placeholder or 'name' in placeholder:
                payload[name] = dash['username']
            elif 'pass' in placeholder:
                payload[name] = dash['password']
            elif 'ans' in placeholder or 'captcha' in placeholder:
                # حل الكابتشا إذا وجدت
                captcha_text = soup.find(string=re.compile(r'\d+\s*[+*]\s*\d+'))
                if captcha_text:
                    payload[name] = solve_msi_captcha(captcha_text)
                else:
                    payload[name] = "0"
            else:
                # القيم الافتراضية
                payload[name] = tag.get('value', '')
        
        # تحديد رابط إرسال الاستمارة
        post_url = form.get('action')
        if post_url and not post_url.startswith('http'):
            post_url = dash['base_url'].rstrip('/') + '/' + post_url.lstrip('/')
        else:
            post_url = dash['base_url'] + '/signin'
        
        # إرسال طلب الدخول
        login_response = dash["session"].post(post_url, data=payload, timeout=20)
        
        # التحقق من نجاح الدخول
        if "dashboard" in login_response.url.lower() or "logout" in login_response.text.lower():
            print(f"[{dash['name']}] ✅ تم تسجيل الدخول بنجاح")
            dash["is_logged_in"] = True
            dash["login_retries"] = 0
            return True
        else:
            print(f"[{dash['name']}] ❌ فشل تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def solve_msi_captcha(captcha_text):
    """حل الكابتشا الرياضية للوحة MSI"""
    match = re.search(r'(\d+)\s*([+*])\s*(\d+)', captcha_text)
    if match:
        n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
        return str(n1 + n2 if op == '+' else n1 * n2)
    return "0"

def build_msi_ajax_params():
    """بناء معاملات طلب AJAX - تجلب رسائل اليوم فقط"""
    # بداية اليوم (00:00:00)
    start_datetime = datetime.combine(date.today(), datetime.min.time())
    # نهاية اليوم (23:59:59)
    end_datetime = datetime.combine(date.today(), datetime.max.time())
    
    return {
        "fdate1": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "fdate2": end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "sEcho": "1",
        "iDisplayLength": "500",
        "_": int(time.time() * 1000)
    }

def fetch_msi_sms(dash):
    """جلب رسائل SMS من لوحة MSI"""
    try:
        if not dash.get("is_logged_in", False):
            if not login_to_msi_panel(dash):
                return []
        
        params = build_msi_ajax_params()
        response = dash["session"].get(
            dash["ajax_url"],
            params=params,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('aaData', [])
        else:
            # لو الجلسة انتهت، نحاول نسجل دخول مرة ثانية
            if response.status_code == 403 or "login" in response.url.lower():
                dash["is_logged_in"] = False
                dash["login_retries"] += 1
                if dash["login_retries"] < 3:
                    return fetch_msi_sms(dash)
            return []
            
    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في جلب البيانات: {e}")
        return []

def process_msi_row(row):
    """معالجة صف من بيانات MSI وتحويله للتنسيق الموحد"""
    try:
        if len(row) >= 6:
            date_str = str(row[0])      # التاريخ والوقت
            number = str(row[2])         # رقم الهاتف
            sender = str(row[3])          # اسم المرسل
            message = str(row[5])          # نص الرسالة
            
            # دمج اسم المرسل مع الرسالة للكشف الأفضل عن الخدمة
            full_message = f"{sender} {message}"
            
            # إنشاء مفتاح فريد
            key = f"{number}_{full_message}_{date_str}"
            
            return date_str, number, full_message, key
    except:
        pass
    return None, None, None, None
    
    
def extract_sesskey_from_page(html_text):
    try:
        patterns = [
            r'data_smscdr\.php\?.*?sesskey=([^&\'"]+)',
            r'sesskey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'var\s+sesskey\s*=\s*["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if len(match) >= 10:
                        return match
        return None
    except:
        return None

def login_to_ims_panel(dash):
    """تسجيل الدخول إلى لوحة IMS"""
    try:
        print(f"[{dash['name']}] 🔑 محاولة تسجيل الدخول...")
        session = dash["session"]
        # جلب صفحة الدخول
        resp = session.get(dash["login_page_url"], timeout=30)
        if resp.status_code != 200:
            print(f"[{dash['name']}] ❌ فشل جلب صفحة الدخول")
            return False

        soup = BeautifulSoup(resp.text, 'html.parser')
        # استخراج etkk
        etkk_input = soup.find('input', {'name': 'etkk'})
        if not etkk_input:
            print(f"[{dash['name']}] ❌ لم يتم العثور على etkk")
            return False
        etkk_value = etkk_input.get('value')

        # حل الكابتشا (مجموع رقمين)
        captcha_element = soup.find(string=re.compile(r'What is (\d+)\s*\+\s*(\d+)\s*=', re.IGNORECASE))
        if not captcha_element:
            print(f"[{dash['name']}] ❌ لم يتم العثور على الكابتشا")
            return False
        match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_element)
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = str(num1 + num2)

        payload = {
            'username': dash['username'],
            'password': dash['password'],
            'capt': captcha_answer,
            'etkk': etkk_value
        }

        # إرسال طلب الدخول
        login_resp = session.post(dash['login_post_url'], data=payload, timeout=30, allow_redirects=True)

        # التحقق من النجاح (يجب أن تحتوي الـ URL على agent/SMSDashboard أو agent/SMSCDRReports)
        if not ("agent/SMSDashboard" in login_resp.url or "agent/SMSCDRReports" in login_resp.url):
            print(f"[{dash['name']}] ❌ فشل تسجيل الدخول - تحقق من البيانات")
            return False

        print(f"[{dash['name']}] ✅ تم تسجيل الدخول بنجاح!")
        # تخزين PHPSESSID
        for cookie in session.cookies:
            if cookie.name == "PHPSESSID":
                dash["phpsessid"] = cookie.value
                break

        dash["is_logged_in"] = True
        dash["last_login_time"] = time.time()
        dash["login_retries"] = 0
        return True

    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في تسجيل الدخول: {e}")
        return False
        
        
def ensure_ims_logged_in(dash):
    current_time = time.time()
    
    # لو في جلسة قديمة والوقت لسه مخلص
    if dash.get("is_logged_in") and dash.get("session"):
        time_since_login = current_time - dash.get("last_login_time", 0)
        if time_since_login < dash.get("login_interval", 120):
            # حتى لو الوقت مخلص، نتأكد إن الجلسة لسه شغالة باختبار sesskey
            if test_ims_session_valid(dash):
                return True
            else:
                print(f"[{dash['name']}] ⚠️ الجلسة منتهية، إعادة تسجيل دخول...")
                return login_to_ims_panel(dash)
    
    # لو مفيش جلسة أو الوقت خلص
    return login_to_ims_panel(dash)
    
    
def test_ims_session_valid(dash):
    """اختبار سريع لصحة الجلسة بمحاولة جلب sesskey"""
    try:
        session = dash["session"]
        resp = session.get(dash["dashboard_url"], timeout=15)
        if resp.status_code == 200:
            sesskey = extract_sesskey_from_page(resp.text)
            if sesskey:
                dash["sesskey"] = sesskey
                return True
        return False
    except:
        return False

def fetch_new_sesskey(dash):
    """جلب sesskey جديد من صفحة dashboard"""
    try:
        if not dash.get("session"):
            return False
            
        print(f"[{dash['name']}] 🔄 جلب sesskey جديد...")
        response = dash["session"].get(dash["dashboard_url"], timeout=30)

        if response.status_code == 200:
            new_sesskey = extract_sesskey_from_page(response.text)
            if new_sesskey:
                dash["sesskey"] = new_sesskey
                print(f"[{dash['name']}] ✅ تم تحديث sesskey: {new_sesskey[:10]}...")
                return True
        print(f"[{dash['name']}] ❌ فشل جلب sesskey")
        return False
    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في جلب sesskey: {e}")
        return False
    
    
def fetch_ims_sms(dash):
    """جلب رسائل SMS من لوحة IMS - نسخة محسنة زي الكود الصغير"""
    try:
        # التأكد من تسجيل الدخول أولاً
        if not ensure_ims_logged_in(dash):
            print(f"[{dash['name']}] ❌ فشل تسجيل الدخول")
            return []

        # جلب sesskey جديد
        if not fetch_new_sesskey(dash):
            print(f"[{dash['name']}] ⚠️ فشل جلب sesskey، إعادة تسجيل الدخول...")
            dash["is_logged_in"] = False
            return []

        session = dash["session"]
        
        # إعداد رؤوس AJAX
        ajax_headers = {
            'User-Agent': COMMON_HEADERS['User-Agent'],
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': dash["dashboard_url"],
        }
        session.headers.update(ajax_headers)

        # ✅ تحديد تاريخ البداية بناءً على last_fetch_time (زي الكود الصغير)
        last_fetch = dash.get("last_fetch_time")
        if last_fetch:
            # حول النص إلى datetime إذا لزم الأمر
            if isinstance(last_fetch, str):
                try:
                    last_fetch = datetime.strptime(last_fetch, "%Y-%m-%d %H:%M:%S")
                except:
                    last_fetch = datetime.now() - timedelta(minutes=5)
            
            # ✅ الأهم: نضيف ثانية واحدة فقط (زي الكود الصغير)
            fdate1 = (last_fetch + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{dash['name']}] 📅 آخر وقت معروف: {last_fetch}, نجلب من: {fdate1}")
        else:
            # أول مرة: آخر 3 أيام
            start_date = date.today() - timedelta(days=3)
            fdate1 = datetime.combine(start_date, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{dash['name']}] 📅 أول مرة، نجلب من: {fdate1}")
        
        fdate2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{dash['name']}] 🔍 جلب رسائل من {fdate1} إلى {fdate2}")

        params = {
            "fdate1": fdate1,
            "fdate2": fdate2,
            "sesskey": dash["sesskey"],
            "sEcho": "1",
            "iDisplayStart": "0",
            "iDisplayLength": dash.get("records", 50),
            "_": str(int(time.time() * 1000))
        }

        response = session.get(dash["ajax_url"], params=params, timeout=30)

        if response.status_code == 200:
            try:
                data = response.json()
                rows = data.get('aaData', [])
                print(f"[{dash['name']}] 📊 تم جلب {len(rows)} رسالة")
                
                # ✅ تحديث last_fetch_time فقط إذا في رسائل جديدة
                if rows:
                    # نجيب أقصى وقت من الرسائل (زي الكود الصغير)
                    max_time = None
                    for row in rows:
                        try:
                            if len(row) > 0 and row[0]:
                                msg_time = datetime.strptime(str(row[0]), "%Y-%m-%d %H:%M:%S")
                                if max_time is None or msg_time > max_time:
                                    max_time = msg_time
                        except:
                            pass
                    
                    if max_time:
                        dash["last_fetch_time"] = max_time
                        print(f"[{dash['name']}] ✅ تم تحديث last_fetch_time إلى: {max_time}")
                
                return rows
            except json.JSONDecodeError:
                print(f"[{dash['name']}] ⚠️ استجابة غير JSON، الجلسة منتهية.")
                dash["is_logged_in"] = False
                dash["sesskey"] = None
                return []
        elif response.status_code == 403:
            print(f"[{dash['name']}] 🚫 خطأ 403: غير مصرح، الجلسة منتهية.")
            dash["is_logged_in"] = False
            dash["sesskey"] = None
            return []
        else:
            print(f"[{dash['name']}] ⚠️ استجابة غير متوقعة: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في جلب الرسائل: {e}")
        traceback.print_exc()
        return []
        
        
def main_loop():
    print("🚀 Monitoring started (Optimized Multi-Format Mode)...")
    print("📊 اللوحات النشطة:")
    for dash in DASHBOARD_CONFIGS:
        print(f"   • {dash['name']} - النوع: {dash.get('type', 'standard')}")
    
    sent = set()  # مجموعة لتخزين الرسائل المرسلة

    while True:
        for dash in DASHBOARD_CONFIGS:
            try:
                rows = []
                
                # معالجة خاصة حسب نوع اللوحة
                if dash.get('type') == 'msi_panel':
                    rows = fetch_msi_sms(dash)
                    
                elif dash.get('type') == 'ims_panel':
                    rows = fetch_ims_sms(dash)
                    # لا حاجة لتحديث last_fetch_time هنا لأنه تم في fetch_ims_sms
                    # فقط للتأكد من عدم وجود مشكلة
                    if rows and dash.get('last_fetch_time') is None:
                        # في حالة غريبة لم يتم التحديث، نستخدم آخر وقت من الرسائل
                        try:
                            last_date = None
                            for row in rows:
                                if row and len(row) > 0 and row[0]:
                                    try:
                                        msg_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                                        if last_date is None or msg_time > last_date:
                                            last_date = msg_time
                                    except:
                                        pass
                            if last_date:
                                dash["last_fetch_time"] = last_date
                                print(f"[{dash['name']}] 📅 تم تعيين last_fetch_time من الرسائل: {last_date}")
                        except Exception as e:
                            print(f"[{dash['name']}] ⚠️ خطأ في تعيين last_fetch_time: {e}")
                            
                else:
                    # معالجة لوحات API العادية
                    params = {"records": dash.get('records', 10)}
                    
                    if dash.get('token') and "?" not in dash['api_url']:
                        params["token"] = dash['token']
                    
                    response = dash["session"].get(
                        dash['api_url'], 
                        params=params, 
                        timeout=TIMEOUT
                    )
                    
                    if response.status_code != 200:
                        continue
                        
                    result = response.json()
                    
                    # تحديد مكان البيانات في الـ JSON
                    if dash.get('type') == 'new_format':
                        rows = result.get('data', [])
                    elif dash.get('type') == 'new_json':
                        rows = result.get('rows', [])
                    else:
                        rows = result if isinstance(result, list) else result.get('data', [])

                if not rows:
                    continue

                # معالجة الرسائل (نأخذ آخر 'records' رسالة)
                for row in rows[-dash.get('records', 10):]:
                    try:
                        date_str, number, message, old_key = row_to_tuple(row, dash.get('type', 'old_list'))
                        
                        # ✅ التحقق من صحة البيانات قبل استخدامها
                        if not date_str or not number or not message:
                            continue
                        
                        # ✅ استخدم old_key من row_to_tuple (اللي فيه التاريخ) كمفتاح فريد
                        unique_key = old_key
                        
                        # ✅ لو old_key مش موجود لسبب ما، أنشئ واحد
                        if not unique_key:
                            message_hash = hashlib.md5(message.encode('utf-8')).hexdigest()[:10]
                            unique_key = f"{number}_{message_hash}_{date_str}"
                        
                        # التحقق من أن المفتاح غير مكرر والرقم صالح
                        if unique_key and unique_key not in sent and number and len(str(number)) > 5:
                            print(f"📩 [{dash['name']}] رسالة جديدة: {number} - التاريخ: {date_str}")
                            
                            # استخراج الخدمة للإرسال فقط (ليس للمفتاح)
                            service = detect_service(message)
                            
                            # تمرير thread_id من إعدادات اللوحة (إن وجد)
                            thread_id = dash.get('thread_id')
                            
                            # تشغيل الإرسال في ثريد منفصل
                            threading.Thread(
                                target=send_otp_to_user_and_group,
                                args=(date_str, number, message),
                                kwargs={'service_api': service, 'thread_id': thread_id},
                                daemon=True
                            ).start()
                            
                            # إضافة المفتاح للمجموعة
                            sent.add(unique_key)
                            print(f"   ✅ تمت إضافة المفتاح: {unique_key}")
                            
                            # تأخير بسيط بين الرسائل
                            time.sleep(0.5)
                        else:
                            if unique_key in sent:
                                print(f"   ⏭️ رسالة مكررة: {unique_key}")
                            
                    except Exception as e:
                        print(f"⚠️ خطأ في معالجة صف: {e}")
                        continue

            except Exception as e:
                print(f"⚠️ خطأ في اللوحة [{dash.get('name')}]: {e}")
                continue
        
        # تنظيف الذاكرة - الحفاظ على آخر 2000 رسالة فقط
        if len(sent) > 2000:
            # حول إلى قائمة، خذ آخر 1000، ثم حول kembali إلى set
            sent_list = list(sent)
            sent = set(sent_list[-1000:])
            print(f"🧹 تم تنظيف مجموعة الرسائل القديمة. الحجم الجديد: {len(sent)}")
        
        # انتظار قبل الدورة التالية
        time.sleep(REFRESH_INTERVAL)

# ============================================================
# 🏁 تشغيل البوت والمراقب
# ============================================================

if __name__ == "__main__":
    # تأكد أنك وضعت دالة row_to_tuple المحدثة قبل هذا الجزء
    
    try:
        # تشغيل استقبال أوامر البوت (infinity_polling) في خلفية منفصلة
        bot_thread = threading.Thread(
            target=lambda: bot.infinity_polling(timeout=60, long_polling_timeout=60), 
            daemon=True
        )
        bot_thread.start()
        print("🤖 Telegram Bot is running in background...")
    except Exception as e:
        print(f"❌ Bot Thread Error: {e}")

    # تشغيل الحلقة الأساسية لمراقبة اللوحات
    main_loop()
    