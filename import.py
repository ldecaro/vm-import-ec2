import os
import time
import threading
import boto3

# Create an EC2 client and resource
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')

# Create an S3 resource
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')

def find_vmdk_files(bucket_name, prefix):
    """
    Find VMDK files in an S3 bucket within a given prefix.

    Args:
        bucket_name (str): The name of the S3 bucket.
        prefix (str): The prefix (folder path) within the bucket.

    Returns:
        list: A list of VMDK file keys (paths) found within the prefix.
    """
    #s3 = boto3.client('s3')
    vmdk_files = []
    start_after = ''

    while True:
        # Call the list_objects_v2 method with the Delimiter parameter, the prefix, and the StartAfter parameter
        response = s3_client.list_objects_v2(Bucket=bucket_name, Delimiter='/', Prefix=prefix, StartAfter=start_after)

        # Extract the object keys (file paths) from the response
        object_keys = [obj['Key'] for obj in response.get('Contents', [])]

        # Filter the object keys to include only VMDK files
        vmdk_files.extend([key for key in object_keys if key.endswith('.vmdk')])

        # Check if there are more objects to retrieve
        if response.get('IsTruncated'):
            # Set the start_after value to the last object key in the current response
            start_after = object_keys[-1]
        else:
            break

    return vmdk_files

def import_vmware_vm(bucket_name, prefix, instance_type, instance_ids, ami_ids):
    print(f"Importing VMware VM: {prefix} from {bucket_name}/{prefix}")

    # List all VMDK files in the S3 folder
    bucket = s3_resource.Bucket(bucket_name)
    vmdk_files = find_vmdk_files(bucket_name, prefix)
    if not vmdk_files:
        print(f"No VMDK files found for prefix: {prefix}. Skipping import for this prefix.")
        return
    print(f"Found {len(vmdk_files)} VMDK files in {prefix}:")
    for file in vmdk_files:
        print(file)

    # Import the VMware VM as an AMI
    disk_containers = [
        {
            'Description': 'VMware disk',
            'Format': 'vmdk',
            'UserBucket': {
                'S3Bucket': bucket_name,
                'S3Key': vmdk_file
            }
        } for vmdk_file in vmdk_files
    ]

    import_task = ec2_client.import_image(
        Description=f'Imported from VMware VM {prefix}',
        DiskContainers=disk_containers
    )
    import_task_id = import_task['ImportTaskId']
    print(f"Import task ID: {import_task_id}")

    # Wait for the import task to complete
    print(f"Waiting for AMI import to complete...")
    while True:
        import_task_description = ec2_client.describe_import_image_tasks(ImportTaskIds=[import_task_id])['ImportImageTasks'][0]
        if import_task_description['Status'] == 'completed':
            ami_id = import_task_description['ImageId']
            break
        time.sleep(15)
    print(f"AMI {ami_id} created from VMware VM {prefix}")
    ami_ids.append(ami_id)  # Add the AMI ID to the list

    # Launch an EC2 instance from the imported AMI
    instance = ec2_resource.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        MaxCount=1,
        MinCount=1
    )[0]
    print(f"Waiting for instance {instance.id} to be running...")
    instance.wait_until_running()
    print(f"Launched instance {instance.id} from AMI {ami_id}")
    instance_ids.append(instance.id)  # Add the instance ID to the list

def main(bucket_name, instance_type):
    # List all folders in the S3 bucket
    #bucket = s3_resource.Bucket(bucket_name)
    # Initialize an empty list to store prefixes
    # Call the list_objects_v2 method with the Delimiter parameter
    """ response = s3_client.list_objects_v2(Bucket=bucket_name, Delimiter='/')

    # Extract the prefixes (folder paths) from the response
    prefixes = [prefix.get('Prefix') for prefix in response.get('CommonPrefixes', [])]

    # Print the prefixes
    for prefix in prefixes:
        print(prefix)
    """
    # Initialize an empty list to store prefixes
    prefixes = []

    # Set the initial start_after value to an empty string
    start_after = ''

    while True:
        # Call the list_objects_v2 method with the Delimiter parameter and the StartAfter parameter
        response = s3_client.list_objects_v2(Bucket=bucket_name, Delimiter='/', StartAfter=start_after)

        # Extract the prefixes from the response and append them to the list
        prefixes.extend([prefix.get('Prefix') for prefix in response.get('CommonPrefixes', [])])

        # Check if there are more prefixes to retrieve
        if response.get('IsTruncated'):
            # Set the start_after value to the last prefix in the current response
            start_after = prefixes[-1]
        else:
            break

    # Print the prefixes
    for prefix in prefixes:
        print(prefix)

    #print(f"Found {len(prefixes)} folders in {bucket_name}")

    # Create a thread for each folder
    threads = []
    instance_ids = []
    ami_ids = []
    thread_count = 1
    for prefix in prefixes:
        thread = threading.Thread(target=import_vmware_vm, args=(bucket_name, prefix, instance_type, instance_ids, ami_ids))
        print(f"Thread {thread_count}: Starting with parameters: bucket_name={bucket_name}, prefix={prefix}, instance_type={instance_type}")
        threads.append(thread)
        thread.start()
        thread_count += 1

    # Wait for threads to complete and print AMI/Instance IDs as they are created
    while threads:
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
        print("AMI IDs:")
        for ami_id in ami_ids:
            print(ami_id)
        print("Instance IDs:")
        for instance_id in instance_ids:
            print(instance_id)
        time.sleep(300)

if __name__ == "__main__":
    bucket_name = input("Enter the S3 bucket name: ")
    instance_type = input("Enter the EC2 instance type (e.g., t2.micro): ")
    main(bucket_name, instance_type)
