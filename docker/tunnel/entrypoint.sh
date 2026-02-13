#!/bin/sh
set -e

SSH_USER=${SSH_USER:-ec2-user}
EC2_HOST=${EC2_HOST:?EC2_HOST required}
RDS_HOST=${RDS_HOST:?RDS_HOST required}
RDS_PORT=${RDS_PORT:-5432}
SSH_KEY_PATH=${SSH_KEY_PATH:-/secrets/key.pem}

# Copy key to writable location and fix permissions (required by SSH)
cp "$SSH_KEY_PATH" /tmp/key.pem
chmod 600 /tmp/key.pem

echo "Starting SSH tunnel: ${SSH_USER}@${EC2_HOST} -> ${RDS_HOST}:${RDS_PORT}"
exec ssh -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -i /tmp/key.pem -N -L 0.0.0.0:5432:${RDS_HOST}:${RDS_PORT} ${SSH_USER}@${EC2_HOST}
