{
  "stagingAreaSubnetId": "${staging_subnet_id}",
  "associateDefaultSecurityGroup": false,
  "replicationServersSecurityGroupsIDs": ["${replication_sg_id}"],
  "replicationServerInstanceType": "${replication_instance}",
  "useDedicatedReplicationServer": false,
  "defaultLargeStagingDiskType": "GP3",
  "ebsEncryption": "CUSTOM",
  "ebsEncryptionKeyArn": "${kms_key_arn}",
  "bandwidthThrottling": ${bandwidth_throttle},
  "dataPlaneRouting": "${use_private_ip ? "PRIVATE_IP" : "PUBLIC_IP"}",
  "createPublicIP": ${use_private_ip ? "false" : "true"},
  "stagingAreaTags": {
    "Project": "${project}",
    "MicroLab": "09-mgn-migration",
    "Purpose": "mgn-staging"
  }
}
