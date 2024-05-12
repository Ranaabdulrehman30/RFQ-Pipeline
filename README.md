## Deployment instructions

### Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Python](https://www.python.org/) 3.11 or greater
- Aws Account credentials already configured

### Cloning the repository

Clone this repository:

```bash
git clone https://github.com/Ranaabdulrehman30/tax-gpt-serverless
```

### Deploy the application with AWS SAM

1. 

   ```bash
   cd backend
   sam build
   ```

1. [Deploy](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html) the application into your AWS account:

   ```bash
   sam deploy --guided
   ```

1. For **Stack Name**, choose `rfp-classification`.
2. For **Bucket Name 1**, choose 'rfpsamples1"
3. For **Bucket Name 2**, choose 'rfpsamplesdoc"