{
  "_comment": "Valores que scripts/configure-mgn.sh aplica al EC2 launch template que MGN crea por cada source server",
  "NetworkInterfaces": [
    {
      "DeviceIndex": 0,
      "SubnetId": "${target_subnet_id}",
      "Groups": ["${target_sg_id}"],
      "AssociatePublicIpAddress": false
    }
  ],
  "IamInstanceProfile": { "Arn": "${instance_profile_arn}" },
  "MetadataOptions": { "HttpTokens": "required", "HttpEndpoint": "enabled" },
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        { "Key": "Project", "Value": "${project}" },
        { "Key": "MicroLab", "Value": "09-migration-mgn" },
        { "Key": "MigratedBy", "Value": "AWS-MGN" }
      ]
    }
  ],
  "_ebs_kms_key": "${kms_key_arn}"
}
