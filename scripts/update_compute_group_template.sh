#!/bin/bash
# Update honeycomb template from existing instance

set -e

project=<project id>
export CLOUDSDK_CORE_PROJECT=$project

zone="us-central1-a"

# get current date into $date
today=$(printf '%(%b-%d-%Y)T\n' -1 | awk '{print tolower($0)}')
# useful if you need to run it more than once on the same day
# today="$today-2"
echo "today: $today"

# get instance name
instance=$(gcloud compute instance-groups managed list-instances honeycomb-group --zone=$zone --format='json' | jq '.[0].name' -r)
echo "instance name: $instance"

echo "resizing instance group down to 0"
gcloud compute instance-groups managed resize honeycomb-group \
	--zone=$zone \
	--size 0

echo "waiting until group resize is finished"
gcloud compute instance-groups managed wait-until honeycomb-group \
	--zone=$zone \
	--stable

echo "creating new image from current disk"
gcloud compute images create $today \
	--project=$project \
	--source-disk=$instance \
	--source-disk-zone=$zone \
	--storage-location=us-central1

echo "creating new instance template"
gcloud compute instance-templates create $today \
	--project=$project \
	--machine-type=c2-standard-8 \
	--network-interface=subnet=projects/<project id>/regions/us-central1/subnetworks/<name>,no-address \
	--no-restart-on-failure \
	--maintenance-policy=TERMINATE \
	--provisioning-model=SPOT \
	--instance-termination-action=STOP \
	--service-account=compute-sa@$project.iam.gserviceaccount.com \
	--scopes=https://www.googleapis.com/auth/pubsub,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/trace.append,https://www.googleapis.com/auth/devstorage.read_write,https://www.googleapis.com/auth/spreadsheets \
	--region=us-central1 \
	--tags=has-rdp-access,iap-rdp-forwarding,iap-ssh-forwarding \
	--create-disk=auto-delete=yes,boot=yes,device-name=instance-template-1,image=projects/ut-dts-agrc-honeycomb-prod/global/images/$today,mode=rw,size=375,type=pd-balanced \
	--no-shielded-secure-boot \
	--shielded-vtpm \
	--shielded-integrity-monitoring \
	--reservation-affinity=any

echo "point group to newly created instance tempate"
gcloud compute instance-groups managed set-instance-template honeycomb-group \
	--zone=$zone \
	--template $today

echo "resizing group back up to 1"
gcloud compute instance-groups managed resize honeycomb-group \
	--zone=$zone \
	--size 1

echo "waiting until group resize is finished"
gcloud compute instance-groups managed wait-until honeycomb-group \
	--zone=$zone \
	--stable

# get new instance name
new_instance=$(gcloud compute instance-groups managed list-instances honeycomb-group --zone $zone | grep NAME: | awk '{print $2}')
echo "new instance name: $new_instance"

echo "adding default backup policy to new disk"
gcloud compute disks add-resource-policies $new_instance \
    --zone $zone \
    --resource-policies default-backup

old_template=$(gcloud compute instance-templates list --format=json | jq --arg today "$today" '.[] | select(.name != $today) | .name' -r)
echo "cleaning up old template: $old_template"
gcloud compute instance-templates delete $old_template --quiet

echo "cleaning up old disk: $instance"
gcloud compute disks delete $instance --zone=$zone --quiet

echo "cleaning up old disk image: $old_template"
gcloud compute images delete $old_template --quiet
