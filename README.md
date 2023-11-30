# Deduplication of entities in tables using embeddings

## Setup

Configure venv and install dependencies

```bash
python3 -m venv .venv 
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
Run the following command to start the server
```bash
python deduplicate.py
```

web interface will be available at `http://locahost:8899` (but you will see it in console output)

One you fill all the fields and click on 'Submit' button, you will see the results in the 'output' section

NOTE: First run will be a bit longer as it needs to cache the model
