from dashboard.config import get_s3_client
import os

def main():
    client = get_s3_client()
    bucket = os.getenv('S3_BUCKET') or os.getenv('AWS_S3_BUCKET')
    if not bucket:
        print('S3_BUCKET not set in environment; set S3_BUCKET to run this test')
        return

    # Try multiple reasonable prefixes so you can discover where objects live.
    tried = []
    configured = os.getenv('S3_PREFIX')
    candidates = [configured, 'raw-data/', '']
    for prefix in [p for p in candidates if p is not None]:
        if prefix in tried:
            continue
        tried.append(prefix)
        print(f"Listing bucket='{bucket}' prefix='{prefix or '<root>'}'")
        try:
            resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)
        except Exception as e:
            print('Error listing objects:', e)
            continue

        contents = resp.get('Contents', [])
        if contents:
            keys = [o['Key'] for o in contents]
            print('Found keys (sample):', keys)
            return

        # If no objects, show CommonPrefixes if present (folders)
        prefixes = resp.get('CommonPrefixes') or []
        if prefixes:
            print('Common prefixes (folders):', [p.get('Prefix') for p in prefixes])
            return

        print('No objects found for this prefix')

if __name__ == '__main__':
    main()
