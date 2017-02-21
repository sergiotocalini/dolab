#!/usr/bin/env python
import os

class Config(object):
    BIND = '0.0.0.0'
    PORT = 7006
    DEBUG = False
    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(24)
    APPLICATION_ROOT = '/dolab'
    CDN_BOOTSTRAP = "//maxcdn.bootstrapcdn.com/bootstrap/3.3.7"
    CDN_FONTAWESOME = "//maxcdn.bootstrapcdn.com/font-awesome/4.7.0"
#    CDN_COMMON = ''
#    CDN_DATATABLES = ''
#    CDN_MAVAPA = ''
    DB_DEBUG = False
    DB_TYPE = 'mysql'
    DB_PORT = 3306
    DB_NAME = 'dolab'
    
class Production(Config):
    DB_HOST = 'localhost'
    DB_USER = 'app_dolab'
    DB_PASS = 'Ki!a4rahfoh5Eap'
    SECRET_KEY = 'U7p47FJaaUgexMVaCRc9zFAd'
    MAVAPA_URL = 'https://accounts.example.com'
    CLIENT_ID = 'o3h6oHqvbH12mpQ6MYp9nEPH'
    CLIENT_SECRET = 'OOUGh3EjCnepR1tNGmVJMyYu'
    REDIRECT_URI = 'https://manage.example.com/dolab/oauth/code/'
    
class Staging(Config):
    DEBUG = True
    DB_HOST = 'localhost'
    DB_USER = 'app_dolab'
    DB_PASS = '1234567890'
    MAVAPA_URL = 'https://accounts.stage.example.com'
    CLIENT_ID = 'MjjJVBFCmFsFsPYaip662z12'
    CLIENT_SECRET = 'qXOxQ0NzYdBOZ9TWChXU4112'
    REDIRECT_URI = 'https://stage.example.com/dolab/oauth/code/'
    
class Development(Config):
    DEBUG = True
    DB_HOST = 'localhost'
    DB_USER = 'app_dolab'
    DB_PASS = '1234567890'
    MAVAPA_URL = 'http://accounts.dev.example.com'
    CLIENT_ID = '8D6ZSvPLvD79fTZv4ckXGtYW'
    CLIENT_SECRET = 'eGoj25Yc8y87bCEM4ex9zrSe'
    REDIRECT_URI = 'http://dev.example.com/dolab/oauth/code/'
    
class Local(Config):
    DEBUG = True
    DB_DEBUG = True
    DB_HOST = 'localhost'
    DB_NAME = 'dolab'
    DB_USER = 'app_dolab'
    DB_PASS = '1234567890'
    MAVAPA_URL = 'http://localhost:7001/mavapa'
    CLIENT_ID = 'MjjJVBFCmFsFsPYaip662zCd'
    CLIENT_SECRET = 'qXOxQ0NzYdBOZ9TWChXU41t8'
    REDIRECT_URI = 'http://localhost:7006/dolab/oauth/code/'
