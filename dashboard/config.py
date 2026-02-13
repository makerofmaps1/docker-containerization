import os
import logging
import boto3
import json

logger = logging.getLogger(__name__)


def get_db_config():
    """Get DB config from environment variables or Secrets Manager.

    Order of precedence:
      1. Environment variables (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`)
      2. Secrets Manager when `USE_SECRETS_MANAGER=true` and `AWS_SECRET_NAME` set
    """

    # 1) Environment variables (preferred)
    env_cfg = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    if all([env_cfg['host'], env_cfg['dbname'], env_cfg['username'], env_cfg['password']]):
        return env_cfg

    # 2) Secrets Manager (production)
    if os.getenv('USE_SECRETS_MANAGER', 'false').lower() == 'true':
        secret_name = os.getenv('AWS_SECRET_NAME')
        if not secret_name:
            logger.error('USE_SECRETS_MANAGER=true but AWS_SECRET_NAME is not set')
        else:
            client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            try:
                response = client.get_secret_value(SecretId=secret_name)
                return json.loads(response['SecretString'])
            except Exception:
                logger.exception('Failed to fetch secret from Secrets Manager')

    # If nothing found, return env_cfg (may contain None values)
    return env_cfg


def get_s3_client():
    """Get S3 client (works in both local and cloud)"""
    return boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
