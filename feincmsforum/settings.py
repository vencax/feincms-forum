# -*- coding: utf-8 -*-
from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

TOPIC_PAGE_SIZE = get('DJANGOBB_TOPIC_PAGE_SIZE', 10)
FORUM_PAGE_SIZE = get('DJANGOBB_FORUM_PAGE_SIZE', 20)
SEARCH_PAGE_SIZE = get('DJANGOBB_SEARCH_PAGE_SIZE', 20)
USERS_PAGE_SIZE = get('DJANGOBB_USERS_PAGE_SIZE', 20)
DEFAULT_TIME_ZONE = get('DJANGOBB_DEFAULT_TIME_ZONE', 3)
SIGNATURE_MAX_LINES = get('DJANGOBB_SIGNATURE_MAX_LINES', 3)
READ_TIMEOUT = get('DJANGOBB_READ_TIMEOUT', 3600 * 24 * 7)
NOTICE = get('DJANGOBB_NOTICE', '')
USER_ONLINE_TIMEOUT = get('DJANGOBB_USER_ONLINE_TIMEOUT', 15)
EMAIL_DEBUG = get('DJANGOBB_FORUM_EMAIL_DEBUG', False)
POST_USER_SEARCH = get('DJANGOBB_POST_USER_SEARCH', 1)

# how many seconds is a post updateable or deletable by a user 0=forever
POST_MODIF_DEATHLINE = 1 * 60 * 60

# AUTHORITY Extension
AUTHORITY_SUPPORT = get('DJANGOBB_AUTHORITY_SUPPORT', True)
AUTHORITY_STEP_0 = get('DJANGOBB_AUTHORITY_STEP_0', 0)
AUTHORITY_STEP_1 = get('DJANGOBB_AUTHORITY_STEP_1', 10)
AUTHORITY_STEP_2 = get('DJANGOBB_AUTHORITY_STEP_2', 25)
AUTHORITY_STEP_3 = get('DJANGOBB_AUTHORITY_STEP_3', 50)
AUTHORITY_STEP_4 = get('DJANGOBB_AUTHORITY_STEP_4', 75)
AUTHORITY_STEP_5 = get('DJANGOBB_AUTHORITY_STEP_5', 100)
AUTHORITY_STEP_6 = get('DJANGOBB_AUTHORITY_STEP_6', 150)
AUTHORITY_STEP_7 = get('DJANGOBB_AUTHORITY_STEP_7', 200)
AUTHORITY_STEP_8 = get('DJANGOBB_AUTHORITY_STEP_8', 300)
AUTHORITY_STEP_9 = get('DJANGOBB_AUTHORITY_STEP_9', 500)
AUTHORITY_STEP_10 = get('DJANGOBB_AUTHORITY_STEP_10', 1000)

# SMILE Extension
SMILES_SUPPORT = get('DJANGOBB_SMILES_SUPPORT', True)
EMOTION_SMILE = '<span class="ei_smile">&nbsp</span>'
EMOTION_NEUTRAL = '<span class="ei_neutral">&nbsp</span>'
EMOTION_SAD = '<span class="ei_sad">&nbsp</span>'
EMOTION_BIG_SMILE = '<span class="ei_big_smile">&nbsp</span>'
EMOTION_YIKES = '<span class="ei_yikes">&nbsp</span>'
EMOTION_WINK = '<span class="ei_wink">&nbsp</span>'
EMOTION_HMM = '<span class="ei_hmm">&nbsp</span>'
EMOTION_TONGUE = '<span class="ei_tongue">&nbsp</span>'
EMOTION_LOL = '<span class="ei_lol">&nbsp</span>'
EMOTION_MAD = '<span class="ei_mad">&nbsp</span>'
EMOTION_ROLL = '<span class="ei_roll">&nbsp</span>'
EMOTION_COOL = '<span class="ei_cool">&nbsp</span>'
SMILES = ((r'(:|=)\)', EMOTION_SMILE), #:), =)
          (r'(:|=)\|',  EMOTION_NEUTRAL), #:|, =| 
          (r'(:|=)\(', EMOTION_SAD), #:(, =(
          (r'(:|=)D', EMOTION_BIG_SMILE), #:D, =D
          (r':o', EMOTION_YIKES), # :o, :O
          (r';\)', EMOTION_WINK), # ;\ 
          (r':/|:unsure:', EMOTION_HMM), #:/
          (r':P', EMOTION_TONGUE), # :P
          (r':lol:', EMOTION_LOL),
          (r':mad:', EMOTION_MAD),
          (r':rolleyes:', EMOTION_ROLL),
          (r':cool:', EMOTION_COOL)
         )
SMILES = get('DJANGOBB_SMILES', SMILES)