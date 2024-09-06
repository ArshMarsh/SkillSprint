# Frontend and Demo
Demo: https://www.youtube.com/watch?v=d4NBrPLczlQ
Frontend: https://github.com/Atherrrrr/SkillSprint-ui

# Skillsprint Backend Setup

This guide will help you set up and deploy the backend environment for the Skillsprint project. Follow these steps to clone the repository, configure AWS resources, and deploy the backend using AWS Amplify.

## Prerequisites

- **AWS CLI**: Install the AWS CLI and configure it with your AWS credentials. Instructions can be found [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).
- **Node.js and NPM**: Ensure you have Node.js and NPM installed. Install Node.js from [here](https://nodejs.org/).
- **AWS Amplify CLI**: Install the Amplify CLI globally using NPM.
  ```bash
  npm install -g @aws-amplify/cli
  ```

## Setup Instructions

1. **Clone the Repository**

   Clone the Skillsprint repository to your local machine.
   ```bash
   git clone https://github.com/your-username/skillsprint.git
   cd skillsprint
   ```

2. **Configure AWS Amplify**

   Initialize the Amplify project. This will set up the Amplify environment and connect it to your AWS account.
   amplify configure
  

   Follow the prompts to sign in to the AWS Management Console, create a new IAM user, and configure the Amplify CLI with the user’s credentials.

3. **Install Project Dependencies**

   Install the required dependencies for the project.
   npm install


4. **Deploy the Backend**

   Deploy the backend resources using AWS Amplify.
   amplify push

   This will create and configure all necessary AWS resources, such as API Gateway, Lambda functions, and DynamoDB tables, based on the provided files.

5. **Verify Deployment**

   Ensure that the backend has been successfully deployed by checking the Amplify Console or the AWS Management Console for the created resources.

## Additional Configuration

- **Environment Variables**: If your Lambda functions or other services require specific environment variables, set them up in the AWS Management Console under the respective service settings.
- **IAM Permissions**: Verify that the IAM roles associated with your Amplify project have the correct permissions for accessing DynamoDB, Lambda, and other AWS resources.

## Common Issues

- **Permissions Errors**: Ensure that your AWS CLI is configured with appropriate permissions to create and manage AWS resources.
- **Deployment Failures**: Check the logs in the Amplify Console or AWS CloudWatch for detailed error messages.
