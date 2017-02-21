#!/usr/bin/env python
from datetime import date, datetime
from pony.orm import *

db = Database()
    
class Minion(db.Entity):
    _table_ = "minions"
    id = PrimaryKey(int, auto=True)
    name = Required(unicode, unique=True)
    type = Required(unicode, default="unknown")
    serial = Optional(unicode, nullable=True)
    product = Optional(unicode, nullable=True)
    cpu_arch = Optional(unicode, nullable=True)
    cpu_model = Optional(unicode, nullable=True)
    kernel = Optional(unicode, nullable=True)
    kernel_release = Optional(unicode, nullable=True)
    mem_total = Optional(unicode, nullable=True)
    os = Optional(unicode, nullable=True)
    os_family = Optional(unicode, nullable=True)
    os_release = Optional(unicode, nullable=True)
    version = Optional(unicode, nullable=True)
    key = Required(unicode, nullable=True)
    status = Required(bool, default=True)
    last_seen = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    master = Required('Master')
    tasks = Set('Task')

class Master(db.Entity):
    _table_ = "masters"
    id = PrimaryKey(int, auto=True)
    name = Required(unicode)
    type = Required(unicode, default="SaltStack")
    api_host = Required(unicode)
    api_user = Required(unicode)
    api_pass = Required(unicode)
    status = Required(bool, default=True)
    last_seen = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    minions = Set(Minion)

class Job(db.Entity):
    _table_ = 'jobs'
    id = PrimaryKey(int, auto=True)
    user = Required('User')
    start_time = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    end_time = Optional(datetime)
    fun = Required(unicode)
    args = Optional(unicode)
    status = Optional(unicode, nullable=True)
    tasks = Set('Task', cascade_delete=True)
    
class Task(db.Entity):
    _table_ = 'jobs_tasks'
    id = PrimaryKey(int, auto=True)
    jid = Optional(unicode)
    fun = Required(unicode)
    args = Optional(unicode)
    start_time = Optional(datetime, sql_type='TIMESTAMP')
    expired = Required(bool, default=False)
    minion = Required(Minion)
    job = Required(Job)

class User(db.Entity):
    _table_ = "users"
    id = PrimaryKey(int, auto=True)
    userid = Required(unicode)
    displayname = Required(unicode)
    email = Required(unicode, unique=True)
    password = Optional(unicode, nullable=True)
    avatar = Required(unicode)
    status = Required(bool, default=False)
    admin = Required(bool, default=False)
    created_on = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    last_seen = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    jobs = Set(Job, cascade_delete=True)
    providers = Set('Provider')

class Provider(db.Entity):
    _table_ = 'providers'
    id = PrimaryKey(int, auto=True)
    name = Required(unicode, unique=True)
    type = Required(unicode, default="Amazon EC2")
    api = Optional(unicode, nullable=True)
    access = Required(unicode)
    secret = Required(unicode)
    owner = Optional(User)
    instances = Set('Instance')
    payments = Set('Payment')
    @db_session
    def last_payment(self):
        last = select(p.amount for p in Payment
                      if p.provider == self
                      and p.datetime == max(p.datetime for p in Payment
                                            if p.provider == self)).get()
        if not last:
            return 0.00
        return last

class Instance(db.Entity):
    _table_ = 'instances'
    id = PrimaryKey(int, auto=True)
    name = Optional(unicode)
    instance = Required(unicode)
    state = Optional(unicode, nullable=True)
    type = Optional(unicode, nullable=True)
    region = Optional(unicode)
    address_private = Optional(unicode)
    address_public = Optional(unicode)
    hypervisor = Optional(unicode)
    hypervisor_type = Optional(unicode)
    provider = Required(Provider)

class Payment(db.Entity):
    _table_ = 'payments'
    id = PrimaryKey(int, auto=True)
    datetime = Required(datetime)
    invoice = Optional(unicode)
    instrument = Optional(unicode)
    method = Optional(unicode)
    amount = Optional(float)
    provider = Required(Provider)

class Function(db.Entity):
    _table_ = 'functions'
    id = PrimaryKey(int, auto=True)
    fun = Required(unicode)
    args = Required(bool, default=True)
    type = Required(unicode, default='SaltStack')
    
class Config(db.Entity):
    _table_ = 'configs'
    id = PrimaryKey(int, auto=True)
    key = Required(unicode, unique=True)
    value = Required(unicode)
    
