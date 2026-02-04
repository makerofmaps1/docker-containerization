FROM postgis/postgis:15-3.3

# install Python in the container
# for running data loading script
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-pandas \
    && rm -rf /var/lib/apt/lists/*

# additional Python dependencies
RUN pip3 install openpyxl psycopg2-binary

# copy initialization scripts
COPY database/init.sql /docker-entrypoint-initdb.d/01-init.sql
COPY database/load_data.py /docker-entrypoint-initdb.d/load_data.py
COPY database/02-load_data.sh /docker-entrypoint-initdb.d/02-load_data.sh

# Make scripts executable
RUN chmod +x /docker-entrypoint-initdb.d/02-load_data.sh
RUN chmod +x /docker-entrypoint-initdb.d/load_data.py
