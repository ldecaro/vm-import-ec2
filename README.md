# vm-import-ec2
A script that can be used to import VMs at scale using EC2
The `import.py` script is designed to import VMware virtual machine disk files (VMDK) from an Amazon S3 bucket and create Amazon Machine Images (AMIs) from them. It then launches Amazon Elastic Compute Cloud (EC2) instances using the newly created AMIs. Here's a breakdown of what the script does:

1. It imports the necessary Python modules, including `os`, `time`, `threading`, and `boto3` (the AWS SDK for Python).

2. It creates clients and resources for EC2 and S3 services using `boto3`.

3. The `find_vmdk_files` function searches for VMDK files within a given S3 bucket and prefix (folder path). It returns a list of VMDK file keys (paths) found.

4. The `import_vmware_vm` function performs the following tasks:

    - Lists all VMDK files in the specified S3 bucket and prefix using `find_vmdk_files`.
    - Imports the VMware VM as an AMI using the `import_image` method of the EC2 client.
    - Waits for the import task to complete and retrieves the newly created AMI ID.
    - Launches an EC2 instance from the imported AMI using the specified instance type.
    - Appends the AMI ID and instance ID to separate lists.

5. The main function does the following:

    - Lists all prefixes (folder paths) in the specified S3 bucket.
    - Creates a separate thread for each prefix, calling the `import_vmware_vm` function with the bucket name, prefix, instance type, and lists to store AMI and instance IDs.
    - Waits for all threads to complete and prints the AMI and instance IDs as they are created.

To use the script, follow these steps:

1. Make sure you have the AWS CLI installed and configured with your AWS credentials.

2. Run the script with Python: `python import.py`

3. When prompted, enter the name of the S3 bucket containing the VMware VM disk files.

4. Enter the desired EC2 instance type (e.g., `t2.micro`) for the instances to be launched.

5. The script will start importing the VMware VMs from the S3 bucket and launching EC2 instances. It will print the AMI and instance IDs as they are created.

Note: This script assumes that you have the necessary permissions to access the S3 bucket and create AMIs and EC2 instances in your AWS account. Additionally, be aware of the costs associated with running EC2 instances and storing data in S3, as you will be charged for these resources.
