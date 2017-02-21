#!/usr/bin/env python
import requests

class SaltStack():
    def __init__(self, **kwargs):
        self.auth_cookies = None
        kwargs.setdefault('api_host', 'http://localhost:8000')
        kwargs.setdefault('api_user', 'saltdev')
        kwargs.setdefault('api_pass', 'saltdev')
        kwargs.setdefault('api_eauth', 'pam')
        kwargs.setdefault('api_timeout', 120)
        self.options = {}
        self.options = kwargs.copy()
        self.login()

    def login(self, **kwargs):
        self.options.update(kwargs)
        headers = {'Accept': 'application/json'}
        data = {
            'username': self.options['api_user'],
            'password': self.options['api_pass'],
            'eauth': self.options['api_eauth']
        }
        try:
            r = requests.post('%(api_host)s/login' %(self.options),
                              headers=headers, data=data)
            self.auth_cookies = r.cookies
            return r.cookies
        except:
            return None

    def logout(self):
        if not self.auth_cookies:
            return None
        headers = {'Accept': 'application/json'}
        try:
            r = requests.post('%(api_host)s/logout' %(self.options),
                              headers=headers, cookies=self.auth_cookies)
            return True
        except:
            return None            

    def run_job(self, **kwargs):
        if kwargs.has_key('fun') and kwargs.has_key('tgt'):
            if not self.auth_cookies:
                return None
            headers = {'Accept': 'application/json'}
            required = ['tgt', 'fun']
            data = {
                'client': kwargs.get('client', 'local_async'),
                'expr_form': kwargs.setdefault('tgt_type', 'glob'),
                'arg': kwargs.get('arg', []),
                'tgt': kwargs['tgt'], 'fun': kwargs['fun']
            }
            try:
                r = requests.post('%s/jobs' %(self.options['api_host']),
                                  headers=headers, cookies=self.auth_cookies,
                                  timeout=self.options['api_timeout'],
                                  data=data)
                return r.json()['return'][0]
            except:
                return None
        return None

    def get_job(self, jid):
        if not self.auth_cookies:
            return None
        headers = {'Accept': 'application/json'}
        try:
            r = requests.get('%s/jobs/%s' %(self.options['api_host'], jid),
                             headers=headers, cookies=self.auth_cookies,
                             timeout=self.options['api_timeout'])

            content = r.json()
            if not content['info'][0]['Target'] == 'unknown-target':
                data = {
                    'fun': content['info'][0]['Function'],
                    'arg': content['info'][0]['Arguments'],
                    'minions': content['info'][0]['Minions'],
                    'start_time': content['info'][0]['StartTime'],
                    'tgt': content['info'][0]['Target'],
                    'tgt-type': content['info'][0]['Target-type'],
                    'result': content['info'][0]['Result']
                }
                return data
            else:
                return None
        except:
            return None
        
    def get_keys(self):
        if not self.auth_cookies:
            return None
        headers = {'Accept': 'application/json'}
        try:
            r = requests.get('%(api_host)s/keys' %(self.options),
                             headers=headers, cookies=self.auth_cookies,
                             timeout=self.options['api_timeout'])
            res = r.json()['return']
            res.pop('local')
            return res
        except:
            return None

    def get_minions(self, mid=None):
        if not self.auth_cookies:
            return None
        headers = {'Accept': 'application/json'}
        try:
            if mid:
                url = '%s/minions/%s' %(self.options['api_host'], mid)
            else:
                url = '%s/minions' %(self.options['api_host'])
                
            r = requests.get(url, headers=headers, cookies=self.auth_cookies)
            return r.json()['return'][0]
        except:
            return None

