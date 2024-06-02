import sys
from datetime import datetime
import datetime
import csv
import argparse
import time
from shared.helper import ResourceHelper, ArgumentParser

# Global constants
DEFAULT_REGION='us-east-1'
DEFAULT_YEAR_TO_FILTER = datetime.datetime.now().year
DEFAULT_MONTH_TO_FILTER = datetime.datetime.now().month
DEFAULT_DATE_TO_FILTER = 1
ALWAYS_EXCLUDE = ["blue-env", "green-env", "master", ]
DRY_RUN = True

def get_confirmation_message(args, branches_to_exclude):
    if args.gateway_id is None and args.gateway_name is None:
        return f"Are you sure you want to delete ALL apigateways excluding the following affixes: {branches_to_exclude}? (y/n) "
    elif args.gateway_id is not None:
        return f"Are you sure you want to delete apigateway with Id: {args.gateway_id}? (y/n) "
    elif args.gateway_name is not None:
        return f"Are you sure you want to delete ALL apigateway with the name: {args.gateway_name}? (y/n) "

def delete_custom_domain(apigateway_helper, gateway_id, gateway_name, gateway_createdDate, log_data, rows_to_write):
    log_data = ""
    retries = 0
    max_retries = 5
    print(f"Deleting gateway {gateway_id} {gateway_name} ...")
    while retries < max_retries:
        try:
            print(f"Deleting gateway {gateway_id} {gateway_name} ...")
            apigateway_helper.client.delete_rest_api(restApiId=gateway_id)
            log_data += f"Deleting apigateway: {gateway_name} \n"
            rows_to_write.append([apigateway_helper.alias, apigateway_helper.aws_id_client, "API Gateway", gateway_id, gateway_name, "not available", gateway_createdDate,  "True"])
            break
        except Exception as e:
            if "TooManyRequestsException" in str(e):
                wait_time = 2 ** retries
                print(f"Too many requests, waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                retries += 1
            elif "NotFoundException" in str(e): 
                break
            elif "BadRequestException" in str(e):
                for row in apigateway_helper.list_resources(apigateway_helper.client, method='get_domain_names',  res='items', NextMarker='position', Marker='position'):
                    domain_name = row['domainName']
                    if gateway_name in domain_name: 
                        try: 
                            print(f"Deleting gateway {gateway_id} {gateway_name} ...")
                            apigateway_helper.client.delete_domain_name(domainName=domain_name)
                            apigateway_helper.client.delete_rest_api(restApiId=gateway_id)
                            log_data += f"Deleting apigateway: {gateway_name} and custom domain name {domain_name} ...\n"
                            rows_to_write.append([apigateway_helper.alias, apigateway_helper.aws_id_client, "API Gateway", gateway_id, gateway_name, domain_name, gateway_createdDate,  "True"])
                            break
                        except Exception as e:
                            if "TooManyRequestsException" in str(e):
                                wait_time = 2 ** retries
                                print(f"Too many requests, waiting for {wait_time} seconds before retrying...")
                                time.sleep(wait_time)
                                retries += 1
            else:
                print(e)
    return log_data


def clean_apigateway(args):
    branches_to_exclude = set(ALWAYS_EXCLUDE) | set(args.exclude)
    apigateway_helper = ResourceHelper(service_name='apigateway', region=args.region)
    dryrun_value = arg_parser.get_dryrun_value(args)
    log_data = ""
    field = ["Account", "AWS Account ID", "Resource", "Resource Id", "Resource Name", "Custom Domain Name", "Date Created", "Deleted"]
    rows_to_write = []

    if dryrun_value:
        print(f"Generating apigateway report for {apigateway_helper.alias}, to delete apigateways set --dryrun to false")
    elif not dryrun_value:
        confirmation = input(get_confirmation_message(args, branches_to_exclude))
        if confirmation.lower() != "y":
            print("\nScript exited. No changes were made.\n")
            exit()

    for row in apigateway_helper.list_resources(apigateway_helper.client, method='get_rest_apis',  res='items', NextMarker='position', Marker='position'):
        gateway_id = row['id']
        gateway_name = row['name']
        gateway_createdDate = row['createdDate']

        if apigateway_helper.time_validator(gateway_createdDate, int(args.year), int(args.month), int(args.date)):
            if  args.gateway_id is None and args.gateway_name is None and not any(branch in gateway_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f"Apigateway: {gateway_id}  {gateway_name} \n"
                rows_to_write.append([apigateway_helper.alias, apigateway_helper.aws_id_client, "API Gateway", gateway_id, gateway_name, "not available", gateway_createdDate, "False"])
            elif args.gateway_id is not None and gateway_id == args.gateway_id and not any(branch in gateway_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f"Apigateway: {gateway_id}  {gateway_name} \n"
                rows_to_write.append([apigateway_helper.alias, apigateway_helper.aws_id_client, "API Gateway", gateway_id, gateway_name, "not available",  gateway_createdDate, "False"])
            elif args.gateway_name is not None and args.gateway_name in gateway_name and not any(branch in gateway_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f"Apigateway: {gateway_id}  {gateway_name}\n"
                rows_to_write.append([apigateway_helper.alias, apigateway_helper.aws_id_client, "API Gateway", gateway_id, gateway_name, "not available", gateway_createdDate, "False"])

            elif args.gateway_id is None and args.gateway_name is None and not any(branch in gateway_name for branch in branches_to_exclude) and not dryrun_value:
                    log_data += delete_custom_domain(apigateway_helper, gateway_id, gateway_name, gateway_createdDate, log_data, rows_to_write)

            elif args.gateway_id is not None and gateway_id == args.gateway_id and not any(branch in gateway_name for branch in branches_to_exclude) and not dryrun_value:                
                    log_data += delete_custom_domain(apigateway_helper, gateway_id, gateway_name, gateway_createdDate, log_data, rows_to_write)

            elif args.gateway_name is not None and args.gateway_name in gateway_name and not any(branch in gateway_name for branch in branches_to_exclude) and not dryrun_value:  
                    print("this is name is passed ")              
                    log_data += delete_custom_domain(apigateway_helper, gateway_id, gateway_name, gateway_createdDate, log_data, rows_to_write)

    apigateway_helper.put_log(log_data=log_data,csv_field= field, csv_rows=rows_to_write )

if __name__ == "__main__":
    description = "Script to delete apigateway functions."
    arguments = [
        {"flags": ["--region"], "options": {"help": "AWS region where the apigateway are located, default is us-east-1", "default": DEFAULT_REGION}},
        {"flags": ["--gateway_id"], "options": {"help": "pass in api gateway id to filter.  ex --gateway_id 9d46xxx1ce", "default": None}},
        {"flags": ["--gateway_name"], "options": {"help": "Api Gateway Name you want to Delete, you can pass in partical suffix. Note: if suffix matches multiple Gateway names, all will be deleted", "default": None}},
        {"flags": ["--exclude"], "options": {"nargs": "+", "help": "Additional branches to exclude from deletion", "default": []}},
        {"flags": ["--year"], "options": {"help": "Specify the year to filter out data that occurred before that year, default is 2024", "default": DEFAULT_YEAR_TO_FILTER}},
        {"flags": ["--month"], "options": {"help": "Specify the month to filter out data that occurred before that month, default is 2", "default": 10}},
        {"flags": ["--date"], "options": {"help": "Specify the date to filter out data that occurred before that date, default is 1", "default": DEFAULT_DATE_TO_FILTER}},
        {"flags": ["--dryrun"], "options": {"help": "Only generate report, do not trigger delete. Default is always true, to delete resource set --dryrun False --gateway_id <the gateway_id to delete>", "default": True}},
    ]
    arg_parser = ArgumentParser(arguments, description)
    args = arg_parser.parse_arguments()
    clean_apigateway(args)
