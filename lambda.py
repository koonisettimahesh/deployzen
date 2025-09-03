import boto3
import zipfile
import os
import uuid
import urllib.parse
import mimetypes

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
region = os.environ.get('AWS_REGION', 'us-east-1')
table = dynamodb.Table('websiteurlMap')

def lambda_handler(event, context):
    try:
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        file_id = object_key.split('.')[0]
        unique_id = str(uuid.uuid4())[:8]


        # Download ZIP
        tmp_zip = f"/tmp/{file_id}.zip"
        s3.download_file(bucket_name, object_key, tmp_zip)

        # Generate unique bucket
        new_bucket = f"{file_id}-{str(uuid.uuid4())[:6]}".lower()

        # Create bucket
        if region == 'us-east-1':
            s3.create_bucket(Bucket=new_bucket)
        else:
            s3.create_bucket(
                Bucket=new_bucket,
                CreateBucketConfiguration={'LocationConstraint': region}
            )

        # Extract ZIP
        extract_path = f"/tmp/extracted_{unique_id}"
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # Detect GitHub-style ZIP: single folder inside
        extracted_items = os.listdir(extract_path)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_path, extracted_items[0])):
            root_folder = os.path.join(extract_path, extracted_items[0])  # GitHub ZIP
        else:
            root_folder = extract_path  # Manual Upload

        # Upload files
        for root, dirs, files in os.walk(root_folder):
            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, root_folder)
                content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

                s3.upload_file(
                    full_path,
                    new_bucket,
                    rel_path,
                    ExtraArgs={'ContentType': content_type}
                )

        # Make bucket public
        s3.put_public_access_block(
            Bucket=new_bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )

        s3.put_bucket_policy(
            Bucket=new_bucket,
            Policy=f'''{{
              "Version":"2012-10-17",
              "Statement":[{{
                  "Sid":"PublicReadGetObject",
                  "Effect":"Allow",
                  "Principal": "*",
                  "Action":["s3:GetObject"],
                  "Resource":["arn:aws:s3:::{new_bucket}/*"]
              }}]
            }}'''
        )

        # Enable static hosting
        s3.put_bucket_website(
            Bucket=new_bucket,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )

        # Save public URL
        website_url = f"http://{new_bucket}.s3-website-{region}.amazonaws.com"
        table.update_item(
    Key={'filename': object_key},
    UpdateExpression="set full_url = :u, bucket_name = :b",
    ExpressionAttributeValues={
        ':u': website_url,
        ':b': new_bucket
    }
)

        print(f"✅ Website deployed: {website_url}")
        return {
            'statusCode': 200,
            'body': f"Deployed to {website_url}"
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }