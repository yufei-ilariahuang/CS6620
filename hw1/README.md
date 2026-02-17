'''
python setup_roles.py 

aws configure --profile hw1
# Paste the Access Key ID and Secret from above
# Region: us-east-2
# Output: json

export AWS_PROFILE=hw1
aws sts get-caller-identity  # Should show :user/hw1-user

python dev_create.py 
python user_list.py 
python dev_cleanup.py
'''