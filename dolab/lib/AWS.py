#!/usr/bin/env python
import boto3

class EC2():
    def __init__(self, **kwargs):
        self.options = kwargs.copy()
        self.options.setdefault('region', 'us-east-1')
        self.api = None
        self.login()

    def login(self, **kwargs):
        self.options.update(kwargs)
        self.api = boto3.resource('ec2', region_name=self.options['region'],
                                  aws_access_key_id=self.options['access'],
                                  aws_secret_access_key=self.options['secret'])
        return self.api

    def switch_region(self, region):
        self.login(region=region)
    
    def get_regions(self, **kwargs):
        if not self.api:
            return None
        regions = self.api.meta.client.describe_regions()
        return regions['Regions']
    
    def get_instances_from_region(self, instanceid=None):
        if not self.api:
            return None
        qfilter = {}
        if instanceid:
            qfilter = {
                'Filters' : [ {'Name': 'instance-id', 'Values': [instanceid]} ],
            }
        try:
            output = []
            for i in self.api.instances.filter(**qfilter):
                name = ''
                for x in i.tags:
                    if x['Key'] == 'Name':
                        name = x['Value']
                        break
                instance = {
                    'name': name,
                    'instance': i.id,
                    'state': i.state['Name'],
                    'type': i.instance_type,
                    'region': i.placement['AvailabilityZone'],
                    'address_private': i.private_ip_address,
                    'address_public': i.public_ip_address,
                    'hypervisor': i.hypervisor,
                    'hypervisor_type': i.virtualization_type,
                }
                output.append(instance)
            return output
        except:
            return []

    def get_instances(self, instanceid=None):
        output = []
        current_region = self.options['region']
        for i in self.get_regions():
            self.switch_region(i['RegionName'])
            output += self.get_instances_from_region(instanceid)

        self.switch_region(current_region)
        return output
