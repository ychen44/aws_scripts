# Description
This repo contains some helpful scripts to clean up your AWS enviroment and/or generate csv file of your resources

# Intro
### Use Pipenv
- Install pipenv: If you haven't already installed pipenv, you can do so via pip:
  ```pip install pipenv```
- Activate the virtual environment:
  ```pipenv shell```
- Alternatively, run a command inside the virtualenv with pipenv run.
- clean up your virtual env for the project
  `pipenv --rm`
- check if virtualenv has been created for this project
- `pipenv --venv`


### Requirements
- Python 3.x
- boto3 library for AWS interaction
- dateutil library for date parsing
- An AWS account with appropriate permissions to list and delete Lambda functions
### Installation
- Ensure you have Python 3.x installed on your system.
- Install required Python libraries using pip:
``` pip install boto3 python-dateutil```
### Usage
- Configure AWS credentials using aws configure or environment variables.
- Run the script with Python:
``` python3 lambda_deletion_script.py```
- Follow the prompts to confirm deletion of Lambda functions. Functions with specified prefixes will be excluded from deletion.
  - Logs for deleted Lambda functions will be written to logs/lambda_delete_log_<timestamp>.txt.
  - Details of deleted Lambda functions will be written to CSV/Lambdas_to_delete_<timestamp>.csv.

# Scripts 

## Clean Up Lambdas 

#### Configuration

`--dryrun`: When set to `True` (default), the script generates a CSV file without deleting any resources. Set to `False` to delete resources without further confirmation.

`--region`: (Required) The AWS region to filter resources for deletion.

`--runtime`: The runtime of Lambda functions to filter for deletion (default: None).

`--exclude`: List of suffixes to filter out when deleting resources (default: "prod-a", "prod-b", "master", "rp").

`--year`: Filters out resources created before the specified year (default: 2024).

`--month`: Filters out resources created before the specified month and year (default: 2).

`--date`: Filters out resources created before the specified month, date, and year (default: 1).


#### Examples

Generate CSV file of all lambdas created before 12/1/2023 with nodejs12.x runtime in us-east-1
- `python3 scripts/delete_lambda.py --region us-east-1 --runtime nodejs12.x --exclude branch1 branch2 --year 2023 --month 10 --date 15 `

Delete all lambdas created before 12/1/2022 in us-west-2 excluding lambdas with names that includes branch1 or branch2
- `python3 scripts/delete_lambda.py --region us-west-2  --exclude branch1 branch2 --year 2022 --month 12 --date 1 --dryrun False `
