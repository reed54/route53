# coding: utf-8
import boto3
lb_client = boto3.client('elbv2')
lb_client.describe_load_balancers()
lbs = lb_client.describe_load_balancers()
lbs
lbs['LoadBalancers']
len(lbs['LoadBalancers'])
lbs['LoadBalancers']['LoadBalancerArn']
lbs['LoadBalancers'][0]
lb = lbs['LoadBalancers'][0]
lb
lb['DNSName']
for l in lbs:
    print(l)
    
lbs
lbs = lbs['LoadBalancers']
lbs
for lb in lbs:
    print(lb)
    
rlb = []
if (rlb == ""):
    print("*** empty ***")
    
if (rlb == " "):
    print("*** empty ***")
    
if (len(rlb) == 0):
    print("*** empty ***")
    
lbs
