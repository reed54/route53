# route53/aState

Python script _aState_ modifies/creates Route53 A records based on input from a CSV file of the following format:

> svc_name, dns_name, CertificateArn  #  Header  
serv-name, dns-name, ssl-ertificate-arn




 $ aState

>Usage: aState [OPTIONS] COMMAND [ARGS]...

>  aState Uses Route53 to modify/create A Records for public hosted zones.

> Options:  
  --profile TEXT  Use a given AWS profile.  
  --verbose       Set verbose mode.  
  --dryrun        Dryrun disables making any changes to A   records.  
  --help          Show this message and exit.  

> Commands:
   * list-a-records         List all A records for all public  hosted zones.  
* list-hosted-zones      List all hosted zones.  
* list-public-zones      List all hosted zones.  
* process-alias-changes  Change A records in public hosted   zones according...


> James Reed     
    Centennial Data Science           
 email: jdreed1954@hotmail.com  
 cell: 303-570-4927  
       


