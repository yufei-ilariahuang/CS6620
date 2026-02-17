
usage: plots S3 bucket size change

3 lambdas:
1. driver lanbda
2. size-tracking lambda
3. plotting lambda

others:
1. S3 bucket: 'TestBucket'
2. dynamodb : 'S3-object-size-history' (store size of all bucket size ind)

Part1:
'create.py': creates TestBucket and S3-object-size-history

Part2:
'size-tracking' lambda: size_tracking_lambda.py
1. triggered by s3 events(object creation/update/deletion in TestBucket)
2. whenever triggered:
    (1) computes the total size of all objects in TestBucket bucket('totalSize')
    (2) writes 'totalSize' into the S3-object-size-history table. 
    (3) stores the timestamp when the size is computed ('timeStamp')
    (4) store the total number of objects in the bucket at that time('nObject')
    (5) store the bucket name into the table('bucketName')

Part3:
'plotting' lambda: plotting_lambda.py
1. when triggered: query (scan not allowed) items from the 'S3-object-size-history' table, use 'matplotlib' for ploting
    (1) plots the change of 'totalSize' in the last 10 seconds
    (2) plots a line that indicates the maximum size any bucket has ever gotten out of all the items in the table (not just last 10 seconds).       
        a. The Y axis is the size, X is the timestamp. 
        b. The unit and step of the axes are up to you. 
    (3) plot store into object 'plot' in 'TestBucket'
    (4) expose a REST API from 'plotting' lambda so that it can be called synchronously.

Part4:
'driver' lambda: driver_lambda.py (be invoked manually in the AWS console, can manually download the plot from the bucket)
1. Create object `assignment1.txt` in 'TestBucket'. The content of the object will be a string "Empty Assignment 1". (size: 19 bytes)
2. Update object `assignment1.txt` by updating its content to "Empty Assignment 2222222222" (size: 28 bytes)
3. Delete object `assignment1.txt` (size: 0)
4. Create object `assignment2.txt` in the bucket. The content is a string "33" (size: 2 bytes)
5. Sleep for some time between the operations, so that the dots in the plot won't be too close to each other.
6. call the API exposed for the plotting lambda.


Demo:
1. python create.p

2. size-tracking lambda
(1) Create the function:

Lambda → Create function → Author from scratch
Name: size-tracking, Runtime: Python 3.12
Create function, then paste this code and Deploy

(2) permissions

Configuration → Permissions → click the role name
Add permissions → Attach policies → add AmazonS3ReadOnlyAccess + AmazonDynamoDBFullAccess

(3) S3 trigger:

Configuration → Triggers → Add trigger → S3
Bucket: testbucket-lia-hw2
Event types: check All object create events + Object deletion
Acknowledge the warning → Add

3. plotting lambda

(1) Create the function:

Lambda → Create function → Author from scratch
Name: plotting, Runtime: Python 3.12, Architecture: x86_64
Paste code → Deploy

(2) Add matplotlib layer:

Configuration → Layers → Add a layer → arn:aws:lambda:us-west-1:389226936064:layer:matplotlib-layer:3


(3)Add permissions:

Configuration → Permissions → click role → attach AmazonS3FullAccess + AmazonDynamoDBReadOnlyAccess

(4) Increase timeout (matplotlib can be slow):

Configuration → General configuration → Edit → set timeout to 30 seconds

(5)Add Function URL (this is your REST API endpoint):

Configuration → Function URL → Create function URL
Auth type: NONE
Copy the URL — you'll need it for the driver lambda in Part 4

4.