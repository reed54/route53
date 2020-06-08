#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""aState: Modify/Add "A" record to PUBLIC Hosted zone

    Input comes from text file.  The format of this file is:
arec_name, dns_name

Where:

arec_name is the name of the A record, and
dns_name is the full path to the DNS in this A record
- Input value <arg1>
- Input avlue <arg2>

High-level logic:
    If <arec_name> record does not exist, create with type=A, dns_name is <dns_name>

    ELSE if <arec_name> record existing value AND <dns_name> <> dns in A record, then update <arec_name>
        record value with <dns_name>
"""

import boto3
import click
import csv

from aState.domain import DomainManager
import aState.util

session = None
domain_manager = None
_verbose = False
_dryrun = False


@click.group()
@click.option('--profile', default=None,
              help="Use a given AWS profile.")
@click.option('--verbose', is_flag=True, default=False,
              help="Set verbose mode.")
@click.option('--dryrun', is_flag=True, default=False,
              help="Dryrun disables making any changes to A records.")
def cli(profile, verbose, dryrun):
    """aState Uses Route53 to modify/create A Records for public hosted zones."""

    global session, domain_manager, _verbose, _dryrun
    if verbose:
        _verbose = True
    if dryrun:
        _dryrun = True
    if (_verbose):
        print("CLI, verbose: ", _verbose)
        print("CLI, dryrun: ", _dryrun)

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile

    session = boto3.Session(**session_cfg)
    domain_manager = DomainManager(session)


@cli.command('list-public-zones')
def list_public_zones():
    """List all hosted zones."""
    domain_manager.list_public_hosted_zones()
    return


@cli.command('list-hosted-zones')
def list_hosted_zones():
    """List all hosted zones."""
    domain_manager.list_hosted_zones()
    return


def get_a_records():
    """Return all A records for all public hosted zones."""
    p_zones = domain_manager.get_public_hosted_zones()
    arecs = []

    for z in p_zones:
        arecs.append(domain_manager.get_a_records(z))

    arecs = [item for item in arecs[0]]
    return arecs


@cli.command('list-a-records')
def list_a_records():
    """List all A records for all public hosted zones."""

    if (_verbose):
        print("\t\tlist-a-records")
    arecs = get_a_records()
    for ar in arecs:
        print("\t\tA Record: ", ar)

    return


def read_alias_state_file(fn):
    """ Read CSV file containing the desired state """
    state = []
    skipped = 0
    alias_state_fn = fn

    with open(alias_state_fn) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                if (_verbose):
                    print(f'Column names are {", ".join(row)}')

            else:
                (arec_name, dns_name, cert_id) = (
                    row[0].strip(), row[1].strip(), row[2].strip())
                if (dns_name.find('none') > 0):
                    skipped += 1
                    if(_verbose):
                        print("SKIPPED - record number, dns-name: ",
                              line_count, dns_name)
                else:
                    state.append((arec_name, dns_name, cert_id))

            line_count += 1

    if (_verbose):
        print("read_alias_state_file,   records read: ", line_count)
        print("                      records skipped: ", skipped)
        print("            records in returned state: ", len(state))

    return state


def fix_lb(lb_dns_name, certArn):
    """
     1. Add SSL Certificate to Listener entry (on port 443).  
       Certificate ARN is in CSV.

     2. Update listener protocol from TCP to HTTPS.
    """
    #lb_client = boto3.client('elbv2')
    lb_client = boto3.client('elb')

    lbs = lb_client.describe_load_balancers()
    lbs = lbs['LoadBalancers']

    # Find lb that matches lb_dns_name
    rlb = []

    for lb in lbs:
        if (lb['DNSName'] == lb_dns_name):
            rlb = lb
            break

    if (len(rlb) == 0):
        print("LB with DNSName {} not found.".format(lb_dns_name))

    listeners = lb_client.describe_listeners(
        LoadBalancerArn=rlb['LoadBalancerArn'])

    # Get listener ARNs
    listeners = listeners['Listeners']
    l_arns = []

    for l in listeners:
        arn = l['ListenerArn']
        port = l['Port']
        if (port == 443):
            # Add SSL certificate to this arn
            res_cert = lb_client.modify_listener(
                ListenerArn=arn,
                Certificates=[
                    {
                        'CertificateArn': certArn,  # This comes from the csv
                        'IsDefault': True
                    }
                ]
            )
            print("update listener with certArn: ", res_cert)

    return


@cli.command('process-alias-changes')
@click.argument('service_name')
@click.argument('lb_dns_name')
@click.argument('filename', default='./svc_lb_mapping.csv', type=click.Path(exists=True))
def process_alias_changes(service_name, lb_dns_name, filename):
    """Change A records in public hosted zones according to input file."""
    def get_current_index(nA, cArecs):
        idx = -1
        numArecs = len(cArecs)
        cAname = [r[0]['Name'] for r in cArecs]

        for k in range(numArecs):
            if (nA == cAname[k]):
                idx = k
                break

        return(idx)

    if (_verbose):
        print("***** process-alias-changes *****")
        print("Alias FN: ", filename)

    newState = read_alias_state_file(filename)
    public_zone = domain_manager.get_public_hosted_zones()[0]
    dns_suffix = public_zone['Name']
    lb_dns_name = f'{lb_dns_name}.'
    hosting_zone_id = public_zone['Id'].split('/')[2]
    print(f'Hosting Zone id: {hosting_zone_id}')

    """
    Now get the A records to compare with the new state
    nXxx = newState values  (nAname, nDnsName)
    cXxx = current state    (cAname, cDnsName)
    """

    print("newState RECORDS : ")
    for t in newState:
        print("\t\t", t)

    # Create lists of cId and cDns
    cArecs = get_a_records()
    cAname = [rec[0]['Name'] for rec in cArecs]
    cDnsName = [rec[0]['DNSName'] for rec in cArecs]
    cHzone = [rec[0]['HostedZoneId'] for rec in cArecs]

    if (_verbose):
        print("PROCESS_ALIAS_CHANGES :\n")
        print("\t\t   cArecs :\n", cArecs, "\n")
        print("\t\t   cAname :\n", cAname, "\n")
        print("\t\t cDnsName :\n", cDnsName, "\n")
        print("\t\t   cHzone :\n", cHzone, "\n")

    numNewState = len(newState)
    for i in range(numNewState):  # cycle over newState records
        nAname, nDnsName, nCertArn = newState[i]
        full_dns_name = f'{nDnsName}.{dns_suffix}'
        if service_name == nAname:
            idx = get_current_index(full_dns_name, cArecs)
            if (idx < 0):
                # Create New A Record
                print("\n\nState RECORD: ", i, "Create new A record.",
                      newState[i])
                resp = create_a_record(
                    hosting_zone_id, cArecs[0], full_dns_name, nAname, lb_dns_name, nCertId)
                print("Response: ", resp)

            else:
                if (lb_dns_name == cDnsName[idx]):
                    # No change A record remains unchanged.
                    print("\n\nState RECORD: ", i, "No change.",
                          newState[i])
                else:
                    # Update existing A Record
                    print("\n\nnewState RECORD: ", i, "Update existing A record.",
                          newState[i])
                    resp = create_a_record(
                        hosting_zone_id,
                        cArecs[idx],
                        full_dns_name,
                        nAname,
                        lb_dns_name,
                        nCertId)

                    print("Response: ", resp)
                    #
                    # Fix load_balancer
                    # Add SSL Certificate to listener entr (port 443)
                    #       Certificate in static file
                    #
                    # Update listener from TCP to HTTPS
                    # certificate ID (nCertID)
                    # LB is lb_dns_name
                    lb_resp = fix_lb(lb_dns_name, nCertArn)
    return


def create_a_record(hosting_zone_id, arec0, domain_name, domain, lb_dns_name, nCertId):
    """Create new or modified A record."""

    arec = arec0[0]
    hostedZoneId = arec['HostedZoneId']

    # Prepare Batch
    changeBatch = {
        'Comment': 'Created by aState.',
        'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                    'Name': f'{domain_name}',
                    'Type': 'A',
                    'AliasTarget': {
                        'HostedZoneId': hostedZoneId,
                        'DNSName': lb_dns_name,
                        'EvaluateTargetHealth': False
                    }
                    }
        }]
    }
    print("\t************** create_a_record **************\n")
    print("\t\t Domain Name: ", domain_name)
    print("\t\t      Domain: ", domain)
    print("\t\t  HostZoneId: ", hostedZoneId)
    print("\t\tChange Batch: ", changeBatch)

    if _dryrun == False:
        response = domain_manager.client.change_resource_record_sets(
            HostedZoneId=hosting_zone_id, ChangeBatch=changeBatch)
        return response
    return 0


def create_cf_doamin_record(self, zone, domain_name, cf_domain):
    """Create record set for our website."""

    return self.client.change_resource_sets(
        HostedZoneId=zone['Id'],
        ChangeBatch={
            'Comment': 'Created by Webotron.',
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': domain_name,
                    'Type': 'A',
                    'AliasTarget': {
                        'HostedZoneId': 'Z2FDTNDATAQYW2',
                        'DNSName': cf_domain,
                        'EvaluateTargetHealth': False
                    }
                }
            }]
        }
    )


if __name__ == '__main__':
    cli()
