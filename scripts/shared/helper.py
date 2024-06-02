import argparse
import boto3
import csv
from dateutil import parser
from datetime import datetime, timezone
class ResourceHelper:
    def __init__(self, service_name, region):
        self.service_name = service_name
        self.region = region
        self.client = boto3.client(service_name, region_name=region)
        self.alias = self._get_account_alias()
        self.aws_id_client = self._get_aws_account_id()
        self.dry_run = True

    def _get_account_alias(self):
        iam_client = boto3.client('iam')
        aliases = iam_client.list_account_aliases()['AccountAliases']
        return aliases[0] if aliases else None

    def _get_aws_account_id(self):
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity().get('Account')

    def list_resources(self, cli, method='list_functions', res='Functions', NextMarker='NextMarker', Marker='Marker', **kwargs):
        method_to_call = getattr(cli, method)

        while True:
            resp = method_to_call(**kwargs)
            yield from resp.get(res, [])

            if NextMarker not in resp:
                break

            kwargs[Marker] = resp[NextMarker]

    def put_log(self, log_data, csv_field, csv_rows):
        with open(f'logs/{self.alias}_{self.service_name}_log_{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.txt', 'w') as file:
            file.write(log_data)
        with open(f"csv/{self.alias}_{self.service_name}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            field = csv_field
            writer.writerow(field)
            writer.writerows(csv_rows)

    @staticmethod
    def time_validator(iso_time, year=2024, month=1, date=1):

        if isinstance(iso_time, datetime):
            iso_time = iso_time.isoformat()

        parsed_time = parser.isoparse(iso_time)
        time_filter = datetime(year, month, date, tzinfo=timezone.utc)

        return parsed_time < time_filter





class ArgumentParser:
    def __init__(self, arguments, description):
        self.parser = argparse.ArgumentParser(description=description)
        for arg in arguments:
            self.add_argument(arg)

    def add_argument(self, arg):
        self.parser.add_argument(*arg["flags"], **arg["options"])

    def parse_arguments(self):
        args = self.parser.parse_args()
        return args
    
    @staticmethod
    def get_dryrun_value(args):
        return args.dryrun if isinstance(args.dryrun, bool) else str(args.dryrun).lower() in ["true", "yes", "1"]
