from flask import Flask, request, jsonify, session, render_template, flash, redirect, url_for
import os
from datetime import datetime
import uuid
import requests
from io import BytesIO
import boto3


app = Flask(__name__)

REGION='us-east-1'

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "deployzen-secret-key")  # Set your secret key for session management
s3 = boto3.client('s3',region_name=REGION)  # Initialize S3 client
dynamodb = boto3.resource('dynamodb',region_name=REGION)
table = dynamodb.Table('websiteurlMap')  # Your DynamoDB table

BUCKET = 'aws-bucket-deployzen'  # S3 Bucket name

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/deployment')
def deployment():
    return render_template("deployment.html")

@app.route('/my-projects')
def my_projects():
    try:
        response = table.scan()
        projects = response.get("Items", [])
        return render_template("my_projects.html", projects=projects)
    except Exception as e:
        print("Error fetching projects:", e)
        return "Error fetching your projects.", 500



@app.route("/zenhub", methods=["GET"])
def zenhub():
    try:
        # Fetch all projects where visibility is 'public'
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('visibility').eq('public')
        )
        projects = response['Items']  # List of projects

        # Render the ZenHub page and pass the public projects to the template
        return render_template("zenhub.html", projects=projects)

    except Exception as e:
        print("Error fetching public projects:", e)
        return "Error fetching public projects", 500

@app.route('/manual-deploy')
def manual_deploy():
    return render_template("manual_deploy.html")

@app.route('/github-deploy')
def github_deploy():
    return render_template("github_deploy.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]  # Get the uploaded file from the request

    # Check if the file is a ZIP file
    if not file.filename.endswith(".zip"):
        return "Only ZIP files are allowed", 400  # Return an error if the file is not a ZIP

    # Get user info (email, name, user_id) from session
    user_id = session.get("userid")
    email = session.get("email")
    name = session.get("name")
    
    # if not user_id or not email or not name:
    #     return "User not logged in", 401  # If no user info is found in session

    # Get the project details from the form
    project_name = request.form.get("project_name")
    description = request.form.get("description")
    visibility = request.form.get("visibility", "private")  # Default to "private" if no visibility is selected

    if not project_name:
        return "Project name is required", 400  # If no project name is provided, return an error

    # Generate a short ID (first 6 characters of a UUID)
    short_id = str(uuid.uuid4())[:6]

    # Construct the filename in the desired format: shortid_projectname_userid.zip
    filename = f"{short_id}{project_name}.zip"

    # Get the current time for uploaded_time and last_updated
    uploaded_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_updated = uploaded_time  # Initially set last_updated to the same time as uploaded_time

    # Set the bucket name
    bucket_name = BUCKET  # The name of your S3 bucket

    try:
        # Upload the ZIP file to the S3 bucket with the new filename
        s3.upload_fileobj(file, BUCKET, filename)

        # Construct the short URL and set full URL as "Pending..."
        short_url = f"http://32.199.53.91:5000/s/{short_id}"  # Replace with your domain/IP
        full_url = "Pending..."

        # Save the file details to DynamoDB
        table.put_item(Item={
            'filename': filename,
            'short_id': short_id,
            'short_url': short_url,
            'full_url': full_url,
            #'email': email,
            #'name': name,
            'project_name': project_name,
            'description': description,
            'visibility': visibility,
            #'userid': user_id,
            'uploaded_time': uploaded_time,
            'bucket_name': bucket_name,
            'last_updated': last_updated
        })

        # Respond with a success message
        return f"""
            ✅ Uploaded!<br>
            🌍 Short URL: <a href="{short_url}" target="_blank">{short_url}</a><br>
            📦 Waiting for Lambda to process and deploy your website...
        """
    
    except Exception as e:
        print("Error uploading file:", e)
        return "Error uploading file to S3", 500  # Handle any errors during the upload process


@app.route("/deploy-github", methods=["POST"])
def deploy_github():
    repo_url = request.form.get("public_url")
    if not repo_url:
        return "GitHub repo URL is required", 400

    try:
        # Strip the ".git" part and split the URL to extract user and repo
        repo_url = repo_url.strip().rstrip('.git')  # Remove any trailing '.git'
        
        parts = repo_url.strip('/').split('/')
        if len(parts) < 2:
            return "Invalid GitHub repo URL", 400

        user, repo = parts[-2], parts[-1]  # Extract username and repository name
        
        # Construct the URL to download the zip from the GitHub repo
        zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/main.zip"

        # Download the ZIP file
        r = requests.get(zip_url)
        if r.status_code != 200:
            return f"Failed to download ZIP from {zip_url}", 400

        # Get user info (email, name, user_id) from session
        user_id = session.get("userid")
        email = session.get("email")
        name = session.get("name")
        
        # if not user_id or not email or not name:
        #     return "User not logged in", 401  # If no user info is found in session

        # Get the project details from the form
        project_name = request.form.get("project_name")
        description = request.form.get("description")
        visibility = request.form.get("visibility", "private")  # Default to "private" if no visibility is selected

        if not project_name:
            return "Project name is required", 400  # If no project name is provided, return an error

        # Generate a short ID (first 6 characters of a UUID)
        short_id = str(uuid.uuid4())[:6]
        
        # Construct the filename in the desired format: shortid_projectname_userid.zip
        filename = f"{short_id}{project_name}.zip"

        # Get the current time for uploaded_time and last_updated
        uploaded_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_updated = uploaded_time  # Initially set last_updated to the same time as uploaded_time

        # Set the bucket name
        bucket_name = BUCKET  # The name of your S3 bucket

        # Upload ZIP to S3
        s3.upload_fileobj(BytesIO(r.content), BUCKET, filename)

        # Construct the short URL and set full URL as "Pending..."
        short_url = f"http://32.199.53.91:5000/s/{short_id}"  # Replace with your domain/IP
        full_url = "Pending..."

        # Save the file details to DynamoDB
        table.put_item(Item={
            'filename': filename,
            'short_id': short_id,
            'short_url': short_url,
            'full_url': full_url,
            #'email': email,
            'name': name,
            'project_name': project_name,
            'description': description,
            'visibility': visibility,
            #'userid': user_id,
            'uploaded_time': uploaded_time,
            'bucket_name': bucket_name,
            'last_updated': last_updated
        })

        # Respond with a success message
        return f"""
            ✅ GitHub repo deployed!<br>
            🌍 Short URL: <a href="{short_url}" target="_blank">{short_url}</a><br>
            📦 Lambda is processing the repo now. Refresh Showcase soon!
        """

    except Exception as e:
        print("Error in GitHub Deploy:", e)
        return "Error processing GitHub repo", 500
    

@app.route("/s/<short_id>")
def redirect_short(short_id):
    try:
        response = table.scan(
            FilterExpression="short_id = :sid",
            ExpressionAttributeValues={":sid": short_id}
        )
        items = response.get("Items", [])
        if items and items[0]["full_url"] != "Pending...":
            return redirect(items[0]["full_url"], code=302)
        elif items:
            return "Deployment still in progress. Try again in a moment.", 202
        else:
            return "Short URL not found", 404
    except Exception as e:
        print("Error:", e)
        return "Server error", 500

@app.route("/delete/<filename>", methods=["POST"])
def delete_project(filename):
    try:
        # Get the DynamoDB item
        response = table.get_item(Key={"filename": filename})
        item = response.get("Item")

        if not item:
            flash("Project not found in database.", "error")
            return redirect(url_for("my_projects"))

        # Always delete the uploaded ZIP from the main bucket only
        main_bucket = "aws-bucket-deployzen"
        try:
            s3.delete_object(Bucket=main_bucket, Key=filename)
        except Exception as e:
            print(f"Could not delete ZIP from main bucket: {e}")

        # If there's a separate hosting bucket, delete its contents and the bucket
        site_bucket = item.get("bucket_name")
        if site_bucket and site_bucket != main_bucket:
            try:
                objects = s3.list_objects_v2(Bucket=site_bucket)
                if "Contents" in objects:
                    s3.delete_objects(
                        Bucket=site_bucket,
                        Delete={"Objects": [{"Key": obj["Key"]} for obj in objects["Contents"]]}
                    )
                s3.delete_bucket(Bucket=site_bucket)
            except Exception as e:
                print(f"Could not delete hosting bucket: {e}")

        # Delete record from DynamoDB
        table.delete_item(Key={"filename": filename})
        flash("Project deleted from all sources.", "success")

    except Exception as e:
        print("Error during deletion:", e)
        flash("Failed to delete project completely.", "error")

    return redirect(url_for("my_projects"))




# ---------------- GitHub OAuth ----------------

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
GITHUB_CALLBACK_URL = "http://32.199.53.91:5000/github-callback"


@app.route('/github-login')
def github_login():
    next_url = request.args.get("next", "/")

    # Allow only local paths
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/"

    session["oauth_next"] = next_url

    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_CALLBACK_URL}"
        "&scope=read:user%20user:email"
    )

    return redirect(github_auth_url)

@app.route('/github-callback')
def github_callback():
    code = request.args.get('code')

    if not code:
        return "GitHub authorization failed.", 400

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_CALLBACK_URL
        },
        headers={"Accept": "application/json"}
    )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return "Unable to obtain GitHub access token.", 400

    user_response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json"
        }
    )

    user_data = user_response.json()

    session['github_user'] = {
        "login": user_data.get("login"),
        "name": user_data.get("name"),
        "avatar_url": user_data.get("avatar_url")
    }

    next_url = session.pop("oauth_next", "/")
    return redirect(next_url)

@app.route('/github-logout')
def github_logout():
    session.pop('github_user', None)
    return redirect(url_for('home'))

@app.route('/api/github-user')
def github_user():
    user = session.get('github_user')

    if user:
        return jsonify({
            "logged_in": True,
            "user": user
        })

    return jsonify({
        "logged_in": False
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
