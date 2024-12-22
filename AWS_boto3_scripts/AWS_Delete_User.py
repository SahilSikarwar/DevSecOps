import boto3
import sys

iam_client = boto3.client(
    'iam',
    aws_access_key_id="",
    aws_secret_access_key=""
)

def delete_iam_login_profile(username):
    try:
        login_profile = iam_client.get_login_profile(UserName=username)
        print("User profile Present!")
        login_profile['LoginProfile']['PasswordResetRequired']
        iam_client.delete_login_profile(UserName=username)
        print("User profile deleted!")
    except iam_client.exceptions.NoSuchEntityException:
        print("No Login Profile Present")


def delete_iam_signing_certificate(username):
    sign_certs = iam_client.list_signing_certificates(UserName=username)
    if len(sign_certs['Certificates']) != 0:
        print(f"Number of Certs: {len(sign_certs['Certificates'])}")
        for cert in sign_certs['Certificates']:
            certID = cert['CertificateId']
            iam_client.delete_signing_certificate(
                UserName=username, CertificateId=certID)
        print("Certs deleted!")
    else:
        print("No Certs present")


def delete_iam_ssh_keys(username):
    ssh_list = iam_client.list_ssh_public_keys(UserName=username)
    if len(ssh_list['SSHPublicKeys']) != 0:
        print(f"Number of SSH Keys: {len(ssh_list['SSHPublicKeys'])}")
        for key in ssh_list['SSHPublicKeys']:
            iam_client.delete_ssh_public_key(
                UserName=username, SSHPublicKeyId=key['SSHPublicKeyId'])
            print(key['SSHPublicKeyId'])
        print("SSH keys deleted!")
    else:
        print("No SSH keys present")


def delete_iam_git_keys(username):
    git_creds = iam_client.list_service_specific_credentials(
        UserName=username, ServiceName='codecommit.amazonaws.com')
    if len(git_creds['ServiceSpecificCredentials']) != 0:
        print(
            f"Number of git Creds: {len(git_creds['ServiceSpecificCredentials'])}")
        for key in git_creds['ServiceSpecificCredentials']:
            iam_client.delete_service_specific_credential(
                UserName=username,
                ServiceSpecificCredentialId=key['ServiceSpecificCredentialId']
            )
        print("Git Creds deleted!")
    else:
        print("No Git Creds present")


def delete_iam_apache_cassandra_keyspace(username):
    apache_cred = iam_client.list_service_specific_credentials(
        UserName=username, ServiceName='cassandra.amazonaws.com')
    if len(apache_cred['ServiceSpecificCredentials']) != 0:
        print(
            f"Number of git Creds: {len(apache_cred['ServiceSpecificCredentials'])}")
        for key in apache_cred['ServiceSpecificCredentials']:
            iam_client.delete_service_specific_credential(
                UserName=username,
                ServiceSpecificCredentialId=key['ServiceSpecificCredentialId']
            )
        print("Cassandra Creds deleted!")
    else:
        print("No Cassandra Creds present")


def delete_iam_mfa_devices(username):
    mfa_devices = iam_client.list_mfa_devices(UserName=username)
    if len(mfa_devices['MFADevices']) != 0:
        print(f"Number of MFA Devices: {len(mfa_devices['MFADevices'])}")
        for mfa_device in mfa_devices['MFADevices']:
            iam_client.deactivate_mfa_device(
                UserName=username, SerialNumber=mfa_device['SerialNumber'])
        print("MFA Devices deleted!")
    else:
        print('No MFA devices present')


def delete_iam_user_policies(username):
    inline_policies = iam_client.list_user_policies(UserName=username)
    if len(inline_policies['PolicyNames']) != 0:
        print(
            f"Number of inline policies: {len(inline_policies['PolicyNames'])}")
        for policy_name in inline_policies['PolicyNames']:
            iam_client.delete_user_policy(
                UserName=username, PolicyName=policy_name)
        print("Inline Policies Deleted!")
    else:
        print("No Inline Policies present")


def delete_iam_user_attatched_policies(username):
    attached_policies = iam_client.list_attached_user_policies(
        UserName=username)
    if len(attached_policies['AttachedPolicies']) != 0:
        print(
            f"Number of inline policies: {len(attached_policies['AttachedPolicies'])}")
        for policy_name in attached_policies['AttachedPolicies']:
            iam_client.detach_user_policy(
                UserName=username, PolicyArn=policy_name['PolicyArn'])
        print("User Attached Policies detached!")
    else:
        print("No Attached user Policies present")


def delete_iam_user_group(username):
    group_membership = iam_client.list_groups_for_user(UserName=username)
    if len(group_membership['Groups']) != 0:
        print(
            f"Number of Group memberships: {len(group_membership['Groups'])}")
        for group in group_membership['Groups']:
            iam_client.remove_user_from_group(
                GroupName=group['GroupName'], UserName=username)
        print("User detached from Group Membership!")
    else:
        print("No Group attached to the user")


def delete_iam_user_access_keys(username):
    res_keys = iam_client.list_access_keys(UserName=username)
    if len(res_keys['AccessKeyMetadata']) != 0:
        print(f"Number of Access Keys: {len(res_keys['AccessKeyMetadata'])}")
        accessKeyLength = len(res_keys['AccessKeyMetadata'])
        for i in range(accessKeyLength):
            ActiveAccessKey = res_keys['AccessKeyMetadata'][i]['AccessKeyId']
            iam_client.delete_access_key(
                AccessKeyId=ActiveAccessKey, UserName=username)
        print("User Access Keys Deleted!")
    else:
        print("No Access Keys present")


def delete_iam_user(username):
    try:
        delete_user = iam_client.delete_user(UserName=username)
        if delete_user['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("User Deleted!")
    except:
        print("No such user/entity found")
        sys.exit()

# #############################################################################
# #################### Function that sums-up all above ########################
# #############################################################################

def delete_user_account(username):
# ###################### 1. Delete login profile of user if it exists #########
    delete_iam_login_profile(username)
# ###################### 2. Delete signing certificate ########################
    delete_iam_signing_certificate(username)
# # #################### 3. Delete SSH Keys ###################################
    delete_iam_ssh_keys(username)
# # #################### 4. Delete Git Keys ###################################
    delete_iam_git_keys(username)
# # #################### 5. Delete Apache Cassandra Keyspace ##################
    delete_iam_apache_cassandra_keyspace(username)
# # #################### 6. Delete MFA devices ################################
    delete_iam_mfa_devices(username)
# # #################### 7. Delete user Inline Policy from user ###############
    delete_iam_user_policies(username)
# # #################### 8. Detach user attched policy from user ##############
    delete_iam_user_attatched_policies(username)
# # #################### 9. Remove user from Group ############################
    delete_iam_user_group(username)
# # #################### 10. Delete access keys ###############################
    delete_iam_user_access_keys(username)
# # #################### 11. Finally delete the user ##########################
    delete_iam_user(username)


# #############################################################################
# ############################## Driver Code ##################################
# #############################################################################

remove_user = ['testDeleteUser']
listOfUsers = []

## paginator if you have large number of users
paginator = iam_client.get_paginator('list_users')
response_iterator = paginator.paginate()

for user in response_iterator:
    listOfUsers.extend([user_['UserName'] for user_ in user['Users']])

for user in remove_user:
    if user in listOfUsers:
        print(f"-------- For user: {user} --------")
        delete_user_account(user)
    else:
        print(f"******** User Doesn't exist: {user} ********")
