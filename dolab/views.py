#!/usr/bin/env python
import os
import arrow
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from functools import wraps
from flask import Flask, request, render_template, g, jsonify, json
from flask import url_for, abort, flash, redirect, session
from lib import *
from mavapa import mavapa, get_user_data

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(os.environ['APP_SETTINGS'])
app.secret_key = app.config['SECRET_KEY']
app.register_blueprint(mavapa, url_prefix='/oauth')
if not app.config.has_key('CDN_DOLAB'):
    app.config['CDN_DOLAB'] = '%s/static' %app.config.get('APPLICATION_ROOT', '')
if app.config['DB_TYPE'] == 'mysql':
    db.bind(app.config['DB_TYPE'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT'], db=app.config['DB_NAME'],
            user=app.config['DB_USER'], passwd=app.config['DB_PASS'])
    db.generate_mapping(create_tables=True)
else:
    print('Database doesn\'t tested')
    exit(0)
sql_debug(app.config.get('DB_DEBUG', False))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = session['access_token'] if 'access_token' in session else None
        user = session['user'] if 'user' in session else None
        if access_token is None or user is None:
            return redirect(url_for('mavapa.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def active_user(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if not session['user'].get('status', False):
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_func

def admin_required(f):
    @wraps(f)
    @db_session    
    def decorated_func(*args, **kwargs):
        if not session['user'].get('admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_func

@db_session
def post_login():
    user = get_data('User', userid=session['user']['id'])
    if not user:
        user = User(userid=session['user']['id'],
                    email=session['user']['email'],
                    avatar=session['user']['avatar'],
                    displayname=session['user']['displayname'])
    else:
        user.set(email=session['user']['email'],
                 avatar=session['user']['avatar'],
                 displayname=session['user']['displayname'])
    session['user']['admin'] = user.admin
    session['user']['status'] = user.status
    commit()

@app.route('/fresh_u/')
def fresh_user():
    post_login()
    return redirect(url_for('index'))

@app.before_request
@db_session
def before_request():
    refresh_user = False
    if 'access_token' not in session:
        return
    if 'last_update' not in session:
        session['last_update'] = datetime.now()
        refresh_user = True
    else:
        if (datetime.now() - session['last_update']).seconds > 60:
            refresh_user = True
            session['last_update'] = datetime.now()
    if 'user' in session and refresh_user:
        mavapa_user = get_user_data(session)
        if mavapa_user:
            user = get_data('User', email=session['user']['email'])
            if user:
                session['user']['admin'] = user.admin
                session['user']['status'] = user.status
                user.last_seen = datetime.now()
                commit()
            else:
                post_login()
        else:
            return redirect(url_for('logout'))

@db_session
def get_data(table, **kwargs):
    if kwargs:
        return eval(table).get(**kwargs)
    else:
        return select(o for o in eval(table))

@db_session
def minion_update(minion):
    only = ['api_host', 'api_user', 'api_pass']
    params = minion.master.to_dict(only=only)
    api = SaltStack(**params)
    raw = api.get_minions(minion.name)
    if raw:
        os = raw[minion.name].get('os', '')
        os_release = raw[minion.name].get('osrelease', '')
        if os == 'Windows':
            os_release = raw[minion.name].get('osfullname', '')
            os_release = os_release.replace('Microsoft Windows ', '')
        data = {
            'cpu_arch': raw[minion.name].get('cpuarch', ''),
            'cpu_model': raw[minion.name].get('cpu_model', ''),
            'kernel': raw[minion.name].get('kernel', ''),
            'kernel_release': raw[minion.name].get('kernelrelease', ''),
            'mem_total': str(raw[minion.name].get('mem_total', '')),
            'os': os, 'os_release': os_release,
            'os_family': raw[minion.name].get('os_family', ''),
            'serial': raw[minion.name].get('serialnumber', ''),
            'type': raw[minion.name].get('virtual', 'unknown'),
            'version': raw[minion.name].get('saltversion', ''),
            'product': raw[minion.name].get('productname', ''),
            'last_seen': datetime.now()
        }
        minion.set(**data)
        commit()
        return True
    return False    
    
@app.context_processor
def custom_tools():
    def time_humanize(value):
        if isinstance(value, datetime):
            local = arrow.Arrow.fromdatetime(value)
        else:
            local = arrow.Arrow.fromdate(value)
        return local.humanize()

    def date_format(value, fmt='%d/%m/%Y'):
        local = '-'
        if value:
            if isinstance(value, datetime):
                local = datetime.strftime(value, fmt)
            else:
                local = date.strftime(value, fmt)
        return local
                
    return dict(data=get_data, ago=time_humanize, dformat=date_format)
    
@app.route('/')
@login_required
@active_user
def index():
    return render_template('index.html')

@app.route('/admin', defaults={'mod': 'general'})
@app.route('/admin/<mod>')
@login_required
@active_user
@admin_required
@db_session
def admin(mod):
    if mod == 'users':
        return render_template('admin_users.html')
    elif mod == 'cloud':
        return render_template('admin_cloud.html')
    elif mod == 'infra':
        return render_template('admin_infra.html')
    else:
        return render_template('admin_general.html')

@app.route('/cloud')
@login_required
@active_user
@db_session
def cloud():
    return render_template('cloud.html')

@app.route('/infra')
@login_required
@active_user
@db_session
def infra():
    return render_template('infra.html')

@app.route('/profile')
@login_required
@active_user
def profile():
    return render_template('index.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/logout')
def logout():
    return redirect(url_for('mavapa.logout'))

@app.route('/unauthorized')
def unauthorized():
    if not session['user'].get('status', False):
        return render_template('unauthorized.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/api/masters', methods=['GET', 'POST', 'DELETE'])
@db_session
def api_masters():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if qfilter:
        master = get_data('Master', **qfilter)
        if request.method == 'GET':
            if master:
                if session.get('account'):
                    data = master.to_dict()
                else:
                    data = master.to_dict()
                return jsonify(datetime=datetime.now(), data=[data])
        elif request.method == 'POST':
            content = request.get_json(silent=True)
            content['last_seen'] = datetime.now()
            if master:
                master.set(**content)
                commit()
            else:
                Master(**content)
                commit()
        elif request.method == 'DELETE':
            if master:
                master.delete()
                commit()
            else:
                abort(404)
    else:
        abort(400)
    return jsonify(datetime=datetime.now())

@app.route('/api/keys')
@db_session
def api_keys():
    args = request.args.to_dict()
    yes = ["yes", "true", "t", "1"]
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if qfilter:
        master = get_data('Master', **qfilter)
        if request.method == 'GET':
            if master:
                only = ['api_host', 'api_user', 'api_pass']
                params = master.to_dict(only=only)
                api = SaltStack(**params)
                keys = api.get_keys()
                data = []
                if keys:
                    minions = [z.name for z in get_data('Minion')]
                    for i in keys:
                        for x in keys[i]:
                            obj = {'name':x, 'register':False}
                            if i == 'minions_rejected':
                                obj['status'] = 'rejected'
                            elif i == 'minions_denied':
                                obj['status'] = 'denied'
                            elif i == 'minions_pre':
                                obj['status'] = 'pending'
                            else:
                                obj['status'] = 'managed'
                                
                            if x in minions:
                                obj['register'] = True
                            data.append(obj)
            return jsonify(datetime=datetime.now(), data=data)

    return jsonify(datetime=datetime.now())

@app.route('/api/minions', methods=['GET', 'POST', 'DELETE', 'PUT'])
@db_session
def api_minions():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if qfilter:
        minion = get_data('Minion', **qfilter)
        if request.method == 'GET':
            if minion:
                if session.get('account'):
                    data = minion.to_dict(related_objects=True)
                else:
                    data = minion.to_dict(related_objects=True)
                data['master'] = data['master'].name
                return jsonify(datetime=datetime.now(), data=[data])
        elif request.method == 'POST':
            content = request.get_json(silent=True)
            if minion:
                minion.set(**content)
                commit()
            else:
                Minion(**content)
                commit()
        elif request.method == 'DELETE':
            if minion:
                minion.delete()
                commit()
            else:
                abort(404)
        elif request.method == 'PUT':
            if minion:
                minion_update(minion)
            else:
                abort(404)
    else:
        abort(400)
    return jsonify(datetime=datetime.now())    

@app.route('/api/providers', methods=['GET', 'POST', 'DELETE', 'PUT'])
@db_session
def api_providers():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if request.method == 'GET':
        provider = get_data('Provider', **qfilter)
        if provider:
            return jsonify(datetime=datetime.now(), data=[provider.to_dict()])
    return jsonify(datetime=datetime.now())    

@app.route('/api/instances', methods=['GET', 'POST', 'DELETE', 'PUT'])
@db_session
def api_instances():
    yes = ["yes", "true", "t", "1"]
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if request.method == 'GET':
        if qfilter:
            provider = get_data('Provider', **qfilter)
            if provider:
                params = provider.to_dict()
                api = EC2(**params)
                instances = api.get_instances()
                if instances:
                    comp = [(x.instance, x.provider.id) for x in get_data('Instance')]
                    for i in instances:
                        i['register'] = False
                        if (i['instance'], provider.id) in comp:
                            i['register'] = True
            return jsonify(datetime=datetime.now(), data=instances)
    elif request.method == 'POST':
        content = request.get_json(silent=True)
        if qfilter.get('id', '') == 'new':
            Instance(**content)
            commit()
        else:
            instance = get_data('Instance', **qfilter)
            if instance:
                instance.set(**content)
                commit()
    return jsonify(datetime=datetime.now())

@app.route('/api/jobs', methods=['GET', 'POST'])
@db_session
def api_jobs():
    if request.method == 'GET':
        args = request.args.to_dict()
        qfilter = dict((x, args[x]) for x in args if x in ['id'])
        if qfilter:
            job = get_data('Job', **qfilter)
            if job:
                data = job.to_dict()
                data['user'] = job.user.to_dict(exclude=['password'])
                data['tasks'] = []
                for x in job.tasks:
                    minion = {
                        'id': x.minion.id, 'name': x.minion.name,
                        'master': {'id': x.minion.master.id,
                                   'name':x.minion.master.name}
                    }
                    task = {
                        'id': x.id, 'fun': x.fun, 'args': x.args,
                        'jid': x.jid, 'minion': minion,
                        'expired': x.expired, 'start_time': x.start_time,
                    }
                    data['tasks'].append(task)
                return jsonify(datetime=datetime.now(), data=[data])
    elif request.method == 'POST':
        if session['user']:
            master_attr = ['api_host', 'api_user', 'api_pass']
            content = request.get_json(silent=True)
            job = Job(user=get_data('User', email=session['user']['email']),
                      fun=content['fun'], args=','.join(content['args']))
            for i in content['minions']:
                minion = get_data('Minion', id=i)
                params = minion.master.to_dict(only=master_attr)
                api = SaltStack(**params)
                res = api.run_job(tgt=minion.name, fun=content['fun'],
                                  arg=content['args'])
                if res:
                    Task(minion=minion,
                         fun=content['fun'], args=','.join(content['args']),
                         job=job, jid=res['jid'])
            commit()
            data = {'job': job.id, 'tasks': [x.id for x in job.tasks]}
            return jsonify(datetime=datetime.now(), data=data)
        else:
            abort(401)
    return jsonify(datetime=datetime.now())    

@app.route('/api/payments', methods=['GET', 'POST', 'PUT'])
@db_session
def api_payments():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id'])
    if request.method == 'GET':
        if qfilter:
            payment = get_data('Payment', **qfilter)
            if payment:
                data = [payment.to_dict()]
                return jsonify(datetime=datetime.now(), data=[data])
            else:
                abort(404)
        else:
            abort(400)
    elif request.method == 'PUT':
        if qfilter:
            payment = get_data('Payment', **qfilter)
            if payment:
                content = request.get_json(silent=True)
                payment.set(**content)
                commit()
            else:
                abort(404)
        else:
            abort(400)
    elif request.method == 'POST':
        content = request.get_json(silent=True)
        print(content)
        Payment(**content)
        commit()
    elif request.method == 'DELETE':
        if qfilter:
            payment = get_data('Payment', **qfilter)
            if payment:
                payment.delete()
                commit()
            else:
                abort(404)
        else:
            abort(400)
    return jsonify(datetime=datetime.now())

@app.route('/api/tasks')
@db_session
def api_tasks():
    if session['user']:
        args = request.args.to_dict()
        qfilter = dict((x, args[x]) for x in args if x in ['id'])
        if qfilter:
            task = get_data('Task', **qfilter)
            if request.method == 'GET':
                if task:
                    monly = ['api_host', 'api_user', 'api_pass']
                    params = task.minion.master.to_dict(only=monly)
                    api = SaltStack(**params)
                    data = task.to_dict()
                    data['args'] = data['args'].split(',')
                    res = api.get_job(task.jid)
                    if res:
                        output = res['result'][task.minion.name]['return']
                        if not isinstance(output, dict):
                            res['result'][task.minion.name]['return'] = {
                                data['args'][0]: output,
                            }
                    data['return'] = res
                    return jsonify(datetime=datetime.now(), data=[data])
        else:
            abort(400)
    else:
        abort(401)
    return jsonify(datetime=datetime.now())

@app.route('/api/users', methods=['GET', 'POST'])
@db_session
def api_users():
    if request.method == 'GET':
        args = request.args.to_dict()
        qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
        if qfilter:
            user = get_data('User', **qfilter)
            if user:
                data = [user.to_dict(exclude="password")]
                return jsonify(datetime=datetime.now(), data=data)
    elif request.method == 'POST':
        args = request.args.to_dict()
        qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
        if qfilter:
            user = get_data('User', **qfilter)
            if user:
                content = request.get_json(silent=True)
                user.set(**content)
                commit()
        else:
            abort(400)
    return jsonify(datetime=datetime.now())

@app.route('/api/stats/cloud/<mod>')
@db_session
def api_stats_cloud(mod='providers'):
    args = request.args.to_dict()
    raw = []
    if mod == "payments":
        last = args.get('last', 12)
        today = date.today()
        dlimit = today.replace(day=1) + relativedelta(months=-int(last))
        group = args.get('group_by', 'type')
        if group == 'type':
            types = distinct(o.type for o in Provider)
            rows = select(
                (p.datetime.year, p.datetime.month,
                 p.provider.type, sum(p.amount))
                for p in Payment  if p.datetime > dlimit
            ).order_by(-1, -2, -3)
            res = {}
            for year, month, ptype, amount in rows:
                period = str(datetime.strptime('%s-%s' %(year,month),
                                               '%Y-%m').date())
                if not res.has_key(period):
                    res[period] = {}
                    for x in types:
                        res[period][x] = 0
                res[period][ptype] += round(amount, 2)
            raw = sorted(res.items(), key= lambda key: key[0], reverse=True)
    elif mod == "instances":
        group = args.get('group_by', 'provider_type')
        if group == 'provider_type':
            raw = select((i.provider.type, count(i)) for i in Instance)
        elif group == 'provider':
            raw = select((i.provider.name, count(i)) for i in Instance)
        elif group == 'type':
            raw = select((i.type, count(i)) for i in Instance)
            
        raw = [{'name': x[0], 'value': x[1]} for x in raw]
        
    return jsonify(datetime=datetime.now(), data=raw)

@app.route('/api/stats/infra/<mod>')
@db_session
def api_stats_infra(mod='masters'):
    args = request.args.to_dict()
    group_by = args.get('group_by')
    raw = []
    if mod == 'masters':
        if group_by == 'type':
            raw = select((m.type, count(m)) for m in Master)
    elif mod == 'minions':
        if group_by == 'os':
            raw = select((m.os, count(m)) for m in Minion)
        elif group_by == 'type':
            raw = select((m.type, count(m)) for m in Minion)
        elif group_by == 'master':
            raw = select((m.master.name, count(m)) for m in Minion)
    return jsonify(datetime=datetime.now(),
                   data=[{'name':i[0],'value':i[1]} for i in raw])

if __name__ == "__main__":
    app.run('0.0.0.0', 7006)
