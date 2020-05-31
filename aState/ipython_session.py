# coding: utf-8
import csv
from domain import DomainManager
import boto3
import click
import util


session = None
domain_manager = None

session_cfg = {}

session = boto3.Session(**session_cfg)

domain_manager = DomainManager(session)

public_hosted_zones = domain_manager.get_public_hosted_zones()
print("All my public zones: ", public_hosted_zones, "\n\n")

# Lets find all the A records for this hosted zone.
response = domain_manager.get_a_records(public_hosted_zones[0])

print("A Records response: ", response, "\n\n")
# Get Alias State (arec_name, dns_name)

alias_state = []
alias_state_fn = 'alias_state.txt'
with open(alias_state_fn) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            (arec_name, dns_name) = (row[0].strip(), row[1].strip())
            alias_state.append((arec_name, dns_name))
            #print(f'\t{row[0]} {row[1]} ')
            line_count += 1
    print(f'Processed {line_count} lines.')

    print("Alias State Tuppples: ", alias_state)

    domain_manager.list_public_hosted_zones()
