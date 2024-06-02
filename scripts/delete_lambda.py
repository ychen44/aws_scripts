import sys
from datetime import datetime
import datetime
import csv
import argparse
from shared.helper import ResourceHelper, ArgumentParser

# Global constants
DEFAULT_REGION='us-east-1'
DEFAULT_YEAR_TO_FILTER = 2024
DEFAULT_MONTH_TO_FILTER = 3
DEFAULT_DATE_TO_FILTER = 1
ALWAYS_EXCLUDE = []
DRY_RUN = True
LAMBDA_TO_DELETE = []

def get_confirmation_message(args, branches_to_exclude, branches_to_delete):
    if len(branches_to_delete) < 1 and args.runtime is None:
        return f"Are you sure you want to delete ALL lambdas excluding the following affixes: {branches_to_exclude}? (y/n) "
    elif args.runtime is not None:
        return f"Are you sure you want to delete lambdas with runtime: {args.runtime}? (y/n) "
    elif len(branches_to_delete) > 0 :
        return f"Are you sure you want to delete ALL lambdas that contains the following affix: {branches_to_delete}? (y/n) "

def clean_lambda(args):
    branches_to_exclude = set(ALWAYS_EXCLUDE) | set(args.exclude)
    branches_to_delete = set(LAMBDA_TO_DELETE) | set(args.delete)
    lambda_helper = ResourceHelper(service_name='lambda', region=args.region)
    dryrun_value = args.dryrun if isinstance(args.dryrun, bool) else str(args.dryrun).lower() in ["true", "yes", "1"]
    log_data = ""
    field = ["Account", "AWS Account ID", "Resource", "Runtime", "Resource Name", "Resource Arn",  "Date Created", "Deleted"]
    rows_to_write = []

    if dryrun_value:
        print(f"Generating lambda report for {lambda_helper.alias}, to delete lambdas set --dryrun flag to false")
    elif not dryrun_value:
        confirmation = input(get_confirmation_message(args, branches_to_exclude, branches_to_delete))
        if confirmation.lower() != "y":
            print("\nScript exited. No changes were made.\n")
            exit()

    for row in lambda_helper.list_resources(lambda_helper.client, method='list_functions'):
        runtime = row["Runtime"]
        app_name = row["FunctionName"]
        function_arn = row["FunctionArn"]
        last_modified = row["LastModified"]

        if lambda_helper.time_validator(last_modified, int(args.year), int(args.month), int(args.date)):
            if  args.runtime is None and len(LAMBDA_TO_DELETE) == 0 and not any(branch in app_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f"{app_name} \n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn,  last_modified, "False"])
            elif args.runtime is not None and runtime == args.runtime and len(LAMBDA_TO_DELETE) < 1 and not any(branch in app_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f" {runtime}  {app_name} \n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn, last_modified, "False"])
            elif runtime == args.runtime and len(LAMBDA_TO_DELETE) > 0 and any(branch in app_name for branch in branches_to_delete) and not any(branch in app_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f" {runtime}  {app_name} \n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn, last_modified, "False"])

            elif len(LAMBDA_TO_DELETE) > 0 and any(branch in app_name for branch in branches_to_delete) and not any(branch in app_name for branch in branches_to_exclude) and dryrun_value:
                log_data += f" {runtime}  {app_name} \n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn, last_modified, "False"])

            elif args.runtime is None and len(LAMBDA_TO_DELETE) == 0 and not any(branch in app_name for branch in branches_to_exclude) and not dryrun_value:
                log_data += f"Deleting {app_name} ...\n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn,last_modified, "True"])
                response = lambda_helper.client.delete_function(
                        FunctionName=app_name
                    )
            elif runtime == args.runtime and not any(branch in app_name for branch in branches_to_exclude) and not dryrun_value:
                log_data += f"Deleting {app_name} ...\n"
                rows_to_write.append([lambda_helper.alias, lambda_helper.aws_id_client, "Lambda Functions", runtime, app_name, function_arn, last_modified, "True"])
                response = lambda_helper.client.delete_function(
                        FunctionName=app_name
                    )

    lambda_helper.put_log(log_data=log_data,csv_field= field, csv_rows=rows_to_write )

if __name__ == "__main__":
    description = "Script to delete Lambda functions."
    arguments = [
        {"flags": ["--region"], "options": {"help": "AWS region where the Lambda functions are located", "required": True}},
        {"flags": ["--runtime"], "options": {"help": "Lambda runtime to filter. If none is passed, resource will not get deleted. ex --runtime nodejs16.x", "default": None}},
        {"flags": ["--exclude"], "options": {"nargs": "+", "help": "Additional branches to exclude", "default": []}},
        {"flags": ["--delete"], "options": {"nargs": "+", "help": "affixes you want to filter and delete. to delete set --dryrun to false. Note: if affix matches multiple lambda names, all will be deleted", "default": []}},
        {"flags": ["--year"], "options": {"help": "Specify the year to filter out data that occurred before that year, default is 2024", "default": DEFAULT_YEAR_TO_FILTER}},
        {"flags": ["--month"], "options": {"help": "Specify the month to filter out data that occurred before that month, default is 2", "default": DEFAULT_MONTH_TO_FILTER}},
        {"flags": ["--date"], "options": {"help": "Specify the date to filter out data that occurred before that date, default is 1", "default": DEFAULT_DATE_TO_FILTER}},
        {"flags": ["--dryrun"], "options": {"help": "Only generate report, do not trigger delete. Default is always true, to delete resource set --dryrun False --runtime <the runtime to delete>", "default": DRY_RUN}},
    ]
    arg_parser = ArgumentParser(arguments, description)
    args = arg_parser.parse_arguments()
    clean_lambda(args)
