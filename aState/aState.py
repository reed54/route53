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
verbose = False
dryrun = False


@click.group()
@click.option('--profile', default=None,
              help="Use a given AWS profile.")
# @click.option('--verbose', is_flag=True,
#               help="Set verbose mode.")
# @click.option('--dryrun', is_flag=True, default=False,
#               help="Dryrun disables making any changes to A records.")
def cli(profile):
    """aState Uses Route53 to modify/create A Records for public hosted zones."""
    global session, domain_manager, verbose
    if (verbose):
        print("CLI, verbose: ", verbose)
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


@cli.command('list-a-records')
def list_a_records():
    """List all A records for all public hosted zones."""
    p_zones = domain_manager.get_public_hosted_zones()
    if (verbose):
        print("Public Zones: ", p_zones)
    for z in p_zones:
        print("Zone Id: ", z['Id'])
        arecs = domain_manager.get_a_records(z)
        for ar in arecs:
            print("\t\tA Record: ", ar)

    return


def read_alias_state_file(fn):
    """ Read CSV file containing the desired state """
    state = []
    alias_state_fn = fn
    with open(alias_state_fn) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                if (verbose):
                    print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                (arec_name, dns_name) = (row[0].strip(), row[1].strip())
                state.append((arec_name, dns_name))
                if (verbose):
                    print(f'\t{row[0]} {row[1]} ')
                line_count += 1

    return state


@cli.command('process-alias-changes')
@click.argument('filename', default='./alias_state.txt')
def process_alias_changes(filename):
    """Change A records in public hosted zones according to input file."""
    if (verbose):
        print("***** process-alias-changes *****")
        print("Alias FN: ", filename)

    tobe_alias_state = read_alias_state_file(filename)

    line_count = len(tobe_alias_state)
    if (verbose):
        print(f'Processed {line_count} lines.')

    print("Alias State Tuppples: ")
    for t in tobe_alias_state:
        print("\t\t", t)

    return


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
