#!/usr/bin/env python3
"""
SSH tunnel test to forward RDS port via EC2 bastion and run tests/test_db.py.

Usage:
  - Set environment variable EC2_SSH_KEY to the full path of your private key (.pem),
    or export EC2_SSH_USER if username is different from ec2-user.
  - Run: .venv\Scripts\python.exe tests\tunnel_test.py

This script sets DB_HOST/DB_PORT to the local tunnel endpoint and runs the
existing test script so no changes are required to tests/test_db.py.
"""
import os
import runpy

try:
    from sshtunnel import SSHTunnelForwarder
except Exception:
    raise SystemExit("sshtunnel is required. Install with: pip install sshtunnel paramiko")

# EC2 public IP or DNS name
EC2_HOST = os.getenv('EC2_HOST', '3.139.90.56')
SSH_USER = os.getenv('EC2_SSH_USER', 'ec2-user')
SSH_KEY = os.getenv('EC2_SSH_KEY')  # full path to your .pem file

if not SSH_KEY:
    raise SystemExit("Set EC2_SSH_KEY environment variable to the path of your private key (.pem)")

RDS_HOST = os.getenv('RDS_HOST', 'my-demo-pdbg.crqi4u0wcrqu.us-east-2.rds.amazonaws.com')
RDS_PORT = int(os.getenv('RDS_PORT', '5432'))
LOCAL_PORT = int(os.getenv('TUNNEL_LOCAL_PORT', '6543'))

# Ensure local imports resolve
os.environ['PYTHONPATH'] = os.getcwd()

print(
    f"Starting SSH tunnel to {EC2_HOST} (user={SSH_USER}), forwarding remote "
    f"{RDS_HOST}:{RDS_PORT} to localhost:{LOCAL_PORT}"
)
with SSHTunnelForwarder(
    (EC2_HOST, 22),
    ssh_username=SSH_USER,
    ssh_pkey=SSH_KEY,
    remote_bind_address=(RDS_HOST, RDS_PORT),
    local_bind_address=('127.0.0.1', LOCAL_PORT),
) as tunnel:
    local_port = tunnel.local_bind_port
    print('Tunnel established on 127.0.0.1:%s' % local_port)

    # Point local DB client to the tunnel
    os.environ['DB_HOST'] = '127.0.0.1'
    os.environ['DB_PORT'] = str(local_port)

    # Run the existing DB test which uses dashboard.db.get_engine()
    runpy.run_path('tests/test_db.py', run_name='__main__')

print('Tunnel closed')
