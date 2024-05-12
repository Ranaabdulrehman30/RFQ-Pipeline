import os
import boto3
import json
from zipfile import ZipFile
import tempfile
from PyPDF2 import PdfFileReader, PdfFileWriter
import re
import codecs

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Get the bucket and key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Check if the uploaded file is a .zip file
    if not key.endswith('.zip'):
        print("Uploaded file is not a .zip file.")
        return
    
    # Extract the folder name from the ZIP file name
    folder_name = os.path.splitext(os.path.basename(key))[0]
    
    # Create a temporary directory to extract the files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download the ZIP file to the temporary directory
        zip_file_path = os.path.join(tmpdir, 'uploaded_file.zip')
        s3_client.download_file(bucket_name, key, zip_file_path)
        
        # Extract files from the ZIP file preserving the directory structure
        with ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        
        # Upload extracted files to the destination buckets
        dest_bucket_name = 'rfpsamplesdoc'
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                file_path = os.path.join(root, file)
                dest_prefix = f'staging/{folder_name}/{root[len(tmpdir)+1:]}/'
                s3_client.upload_file(file_path, dest_bucket_name, os.path.join(dest_prefix, file))
        
        print("Files extracted and uploaded successfully.")
    
    
    bucket_name = "rfpsamplesdoc"
    prefix = f"staging/{folder_name}/{folder_name}/"

    # Initialize file_types dictionary for the current folder
    file_types = {
        "PWS": [],
        "SOW": [],
        "SOO": [],
        "IFO": [],
        "IFPP": [],
        "PRICING": [],
        "TO": [],
        "RFQ": [],
        "Unclassified": []
    }
    
    # List objects in the S3 bucket under the specified prefix and update file_types dictionary
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
    if 'Contents' in response:
        for obj in response['Contents']:
            file_key = obj['Key']
            if file_key.count('/') == prefix.count('/') and not file_key.endswith('.DS_Store'):
                filename = os.path.basename(file_key)
                detected_types = detect_file_type(filename)
                for detected_type in detected_types:
                    file_types[detected_type].append(filename)

    print("File types:")
    print(file_types)

    document_name = None
    
    classified_documents = []
    unclassified_documents = []

    if "RFQ" in file_types and file_types["RFQ"]:
        rfq_files = file_types["RFQ"]
        for file in rfq_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)
    elif "TO" in file_types and file_types["TO"]:
        to_files = file_types["TO"]
        for file in to_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)
    elif "IFPP" in file_types and file_types["IFPP"]:
        ifpp_files = file_types["IFPP"]
        for file in ifpp_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)
    elif "IFO" in file_types and file_types["IFO"]:
        ifo_files = file_types["IFO"]
        for file in ifo_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)
    elif "PWS" in file_types and file_types["PWS"]:
        pws_files = file_types["PWS"]
        for file in pws_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)
    elif "SOW" in file_types and file_types["SOW"]:
        sow_files = file_types["SOW"]
        for file in sow_files:
            if os.path.splitext(file)[1].lower() == '.pdf':
                classified_documents.append(file)

    # Add documents to classified or unclassified list
    for file_type, files in file_types.items():
        for file in files:
            if file.endswith('.pdf'):
                if file_type in ["RFQ", "TO", "IFPP", "IFO", "PWS", "SOW"]:
                    classified_documents.append(file)
                else:
                    unclassified_documents.append(file)
    dest_folder_1 = "classified"
    dest_folder_2 = "unclassified"

    print(classified_documents)
    # Upload classified documents
    for document in classified_documents:
        document_path = f"staging/{folder_name}/{folder_name}/{document}"
        dest_key = f"staging/{folder_name}/{dest_folder_1}/{document}.pdf"
        print(document)
        s3_client.copy_object(Bucket=bucket_name, Key=dest_key, CopySource={'Bucket': bucket_name, 'Key': document_path})
        print("Classification Successful")
    print(unclassified_documents)
    # Upload unclassified documents
    for document in unclassified_documents:
        print(document)
        document_path = f"staging/{folder_name}/{folder_name}/{document}"
        dest_key = f"staging/{folder_name}/{dest_folder_2}/{document}.pdf"
        s3_client.copy_object(Bucket=bucket_name, Key=dest_key, CopySource={'Bucket': bucket_name, 'Key': document_path})
        print("UNClassification Successful")
    # Return the document names
    return json.dumps({"classified_documents": classified_documents, "unclassified_documents": unclassified_documents})


def detect_file_type(filename):
    # Updated patterns for different file types with specificity
    file_type_patterns = {
        "PWS": [
            r"PWS",
            r"Attach \d+ PWS\.pdf$",
            r"Performance work Statement"
        ],
        "SOW": [
            r"SOW",
            r"statement of work"
        ],
        "SOO": [
            r"SOO",
            r"Statement of Objectives",
            r"- Statement of Objectives"
            
        ],
        "IFO": [
            r"Attach 1 Instructions to Offerors",
        ],
        "PRICING": [
            r"PRICING",
            r"price",
            r"PRICE",
            r"cost",
            r"RFQ-Pricing",
            r"Pricing_Sheet",
        ],
        "RFQ": [
            r"RFQ",
            r"\b12314421Q0103\.pdf$",
            r"\bRFQ for GSA Instructions to Offerors Rev 3724.1709850270536\b",
            r"\bSA\b",
            r"\b70RTAC24Q00000011_SF1449.1708446019729\b",
            r"SOLb",
            r"Synopsis Services",
            r"bSolicitation",
            r"\bv4 JD\b",
            r"\bRequest for Quote\b",
            r"request for quote",
            r"\bBPA.17\b",
            r"\bRFP\b",
            r"\bA. LOGMOD BaSE FY23 ITO_EC_Phase 2 Final\b",
            r"ifo",
            r"ITO",
            r"ito",
            r"RFQ1635549"
        ],
        "TO": [
            r"TO",
            r"Task Order",
            r"TORFP 7"
        ],
        "IFPP": [
            r"IFPP",
            r"Instructions for Proposal Preparation"
        ],
    }

    detected_types = []

    # Check each pattern list against the filename
    for file_type, patterns in file_type_patterns.items():
        for pattern in patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                detected_types.append(file_type)
                break  # Stop checking more patterns once a match is found

    if not detected_types:
        detected_types.append("Unclassified")  # If no match, classify as Unclassified
        
    return detected_types

