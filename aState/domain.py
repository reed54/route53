# -*- coding: utf-8 -*-
import uuid

"""Classes for Route 53 domains."""


class DomainManager:
    """Manage a Route 53 domain."""

    def __init__(self, session):
        """Create DomainManager object."""
        self.session = session
        self.client = self.session.client('route53')

    def get_hosted_zones(self):
        """Return the hosted zones."""
        zones = []
        paginator = self.client.get_paginator('list_hosted_zones')
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                zones.append(zone)
        return zones

    def list_hosted_zones(self):
        """ Format list of All Hosted Zones"""
        zones = self.get_hosted_zones()
        print("\n\n ***************** All Hosted Zones ************************\n")
        for zone in zones:
            print("Zone: ", zone, "\n")
        return

    def get_public_hosted_zones(self):
        """Return the public hosted zones."""
        public_zones = []
        zones = self.get_hosted_zones()
        for z in zones:
            if z['Config']['PrivateZone'] == False:
                public_zones.append(z)

        return public_zones

    def list_public_hosted_zones(self):
        """ Format list of Public Hosted Zones"""
        zones = self.get_public_hosted_zones()
        print("\n\n ***************** Public Hosted Zones ************************\n")
        for zone in zones:
            print("Zone: ", zone, "\n")
        return

    def get_a_records(self, zone):
        """Return list of A records from zone."""
        a_recs = []
        response = self.client.list_resource_record_sets(
            HostedZoneId=zone['Id'],
            StartRecordName=".",
            StartRecordType='A',
            StartRecordIdentifier=' '
        )
        # Filter this Nested Dictionary and Pull out all the A records
        rrsSets = response['ResourceRecordSets']
        for rrs in rrsSets:
            # print(rrs['Type'])
            if (rrs['Type'] == 'A'):
                recO = rrs['AliasTarget']

                rec = [{'Name':                  rrs['Name'],
                        'HostedZoneId':         recO['HostedZoneId'],
                        'DNSName':              recO['DNSName'],
                        'EvaluateTargetHealth': recO['EvaluateTargetHealth']}]

                a_recs.append(rec)

        return a_recs

    def find_hosted_zone(self, domain_name):
        """Find the hosted zone need."""
        paginator = self.client.get_paginator('list_hosted_zones')
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if domain_name.endswith(zone['Name'][:-1]):
                    return zone
        return None

    def create_hosted_zone(self, domain_name):
        zone_name = '.'.join(domain_name.split('.')[-2:] + '.')
        print(zone_name)
        return self.client.create_hosted_zone(
            Name=zone_name,
            CallerReference=str(uuid.uuid4())
        )

    def create_arec_domain_record(self, zone, domain_name, endpoint):
        """Create record an A record for our resource."""

        return self.client.change_resource_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by Resource Automation.',
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': domain_name,
                        'Type': 'A',
                        'AliasTarget': {
                            'HostedZoneId': endpoint.zone,
                            'DNSName': endpoint.host,
                            'EvaluateTargetHealth': False
                        }
                    }
                }]
            }
        )
