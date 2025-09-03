# 🚀 DeployZen – Fast, Easy, Automated Deployment

DeployZen is a **cloud-based platform** that simplifies static website deployment for students and developers.  
It allows users to upload a **ZIP file** or connect a **GitHub repository**, and automatically handles hosting using AWS services like **S3, Lambda, DynamoDB, Cognito, and EC2**.  
The frontend is built with **HTML, CSS, and Tailwind**, while the backend uses **Flask (Python)**.  

## 📌 Features
- ⚡ Quick and seamless static website deployment  
- 📂 Upload via ZIP file or GitHub repository  
- 🔄 Automated deployment with AWS Lambda  
- 🗄 Metadata storage using DynamoDB  
- 🔑 Secure authentication with AWS Cognito  
- 🌍 Public project showcase via **ZenHub**  
- 🤖 Built-in chatbot using Amazon Lex for guidance  

## 🏗 Architecture & Workflow
1. **Amazon Cognito** – User authentication, signup, login, and email verification  
2. **Amazon EC2** – Hosts the Flask backend app  
3. **Amazon S3** – Stores uploaded files and serves static websites  
4. **AWS Lambda** – Handles unzipping, deployment, and bucket creation automatically  
5. **Amazon DynamoDB** – Stores project metadata (IDs, filenames, URLs)  
6. **GitHub Integration** – Deploy directly from repositories  
7. **Amazon Lex** – Chatbot support for user guidance  

## 🔧 Tech Stack
- **Backend:** Flask (Python)  
- **Frontend:** HTML, Tailwind CSS  
- **Cloud Services:** AWS EC2, S3, Lambda, DynamoDB, Cognito, Lex  
- **Others:** UUID (for short URLs), GitHub API  

## 📂 Deployment Flow
1. **Manual Deployment (ZIP Upload)**  
   - User uploads a `.zip` file → stored in S3 → Lambda unzips & deploys → DynamoDB stores metadata → URL generated.  

2. **GitHub Deployment**  
   - User pastes repo link → backend fetches ZIP → uploads to S3 → Lambda processes deployment.  

3. **Showcase (ZenHub)**  
   - Public projects are displayed on the ZenHub page.  

## 🎯 Objectives
- Simplify static site deployment for students and beginners  
- Eliminate manual AWS setup (buckets, hosting, permissions)  
- Provide fast, automated hosting with minimal effort  

## 📊 Future Enhancements
- Add analytics & usage dashboards  
- Support for more file types and frameworks  
- Advanced chatbot with AI-based assistance  

## 👨‍💻 Team Members
- G.L. Sudhitha  
- G.N.R.L. Jayanthi  
- I. Amrutha Varshini  
- Koonisetti Mahesh  
- J. DYNS. Gowrish  
- **M. Bharghav Sai**  

---

### ✅ Conclusion
DeployZen makes **static website hosting beginner-friendly** by automating AWS services behind the scenes.  
It provides a scalable, user-friendly, and production-ready solution for **students, developers, and educators** who want to deploy projects without diving into complex cloud setups.  
