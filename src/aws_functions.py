# aws_functions.py>
from h2o_wave import ui
import boto3
import numpy as np
from .get_ec2_cost import get_instance_price
import os

# Selected regions
enabledRegions = ["us-east-1", "us-west-1", "us-east-2", "us-west-2", "ap-southeast-1", "eu-central-1", "ap-south-1"]

def init_boto3_client(service, region):
    return boto3.client(service, region_name=region,
                        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))


def get_ec2_price_hr(region, instance_type):
    # API only has us-east-1 and ap-south-1 as valid endpoints
    pricing_client = init_boto3_client('pricing', 'us-east-1')
    ec2_price = get_instance_price(region, instance_type, pricing_client)
    return ec2_price


def calc_approx_weekend_savings(cluster_name, region, nodegroups, cluster_state):
    eks_client = init_boto3_client('eks', region)
    all_ng_cost_info = []
    for ng in nodegroups:
        ng_info = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=ng
        )

        if cluster_state == "RUNNING":
            desired_size = ng_info['nodegroup']['scalingConfig']['desiredSize']
        else:
            desired_size = ng_info['nodegroup']['tags'][ng] if ng in ng_info['nodegroup']['tags'] else 2

        instance_type = ng_info['nodegroup']['instanceTypes'][0]
        ec2_price_hr = get_ec2_price_hr(region, instance_type)
        approx_daily_cost = 24 * float(ec2_price_hr) * int(desired_size)
        ng_cost_info = [instance_type, ec2_price_hr, float(approx_daily_cost), int(desired_size)]
        all_ng_cost_info.append(ng_cost_info)

    tot_daily_cost = 0.0  # float
    tot_instances = 0
    instance_types = []
    ec2_price_hr_costs = []
    for ng in all_ng_cost_info:
        tot_daily_cost += ng[2]
        tot_instances += ng[3]
        instance_types.append(ng[0])
        ec2_price_hr_costs.append(ng[1])

    tot_cluster_cost = [list(set(instance_types)), list(set(ec2_price_hr_costs)), tot_daily_cost, tot_instances]

    return tot_cluster_cost


def list_eks_clusters(selected_region):
    # Currently some regions are blocked in root account, and only enabled regions are listed here
    if selected_region == 'All':
        regions = enabledRegions
    else:
        regions = [selected_region]

    all_eks_clusters = []
    for region in regions:
        temp = []
        eks_client = init_boto3_client('eks', region)
        eks_clusters = eks_client.list_clusters(maxResults=100)
        temp.append(region)
        temp.append(eks_clusters['clusters'])
        all_eks_clusters.append(temp)
        print('[INFO] REGION: ', region, '#Clusters:', len(eks_clusters['clusters']))
    return all_eks_clusters


def get_clusters_project_tag(selected_region):
    clusters_with_projects = []
    all_eks_clusters = list_eks_clusters(selected_region)
    for item in all_eks_clusters:
        region = item[0]
        eks_client = init_boto3_client('eks', region)

        for cluster_name in item[1]:
            try:
                cluster_info = eks_client.describe_cluster(name=cluster_name)
                project = cluster_info['cluster']['tags']['Project'] if 'Project' in cluster_info['cluster']['tags'] else 'Null'
                temp = [cluster_name, region, project]
                clusters_with_projects.append(temp)
            except:
                print("[ERROR] describe_cluster", cluster_name, region)
                continue

    return clusters_with_projects


def filter_clusters_by_project(project_tag, selected_region):
    filtered_clusters_by_project = []
    clusters = np.array(get_clusters_project_tag(selected_region))
    indexes = list(zip(*np.where(clusters == project_tag)))
    for index in indexes:
        if index[1] == 2:  # Filtering only the Project tag value
            filtered_clusters_by_project.append(clusters[index[0]])
    return filtered_clusters_by_project


def get_cluster_nodegroups_info(cluster_name, region):
    nodegroups_info = []
    eks_client = init_boto3_client('eks', region)
    node_groups = eks_client.list_nodegroups(
        clusterName=cluster_name,
        maxResults=100
    )

    for ng in node_groups['nodegroups']:
        ng_info = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=ng
        )

        if ng_info['nodegroup']['status'] != 'ACTIVE':
            raise Exception("[ERROR] Node group not active,", cluster_name, ng)

        nodegroup_info = [ng_info['nodegroup']['nodegroupName'], ng_info['nodegroup']['scalingConfig']['desiredSize'],
                          ng_info['nodegroup']['scalingConfig']['minSize'], ng_info['nodegroup']['scalingConfig']['maxSize'],
                          ng_info['nodegroup']['resources']['autoScalingGroups'][0]['name']]
        nodegroups_info.append(nodegroup_info)

    return nodegroups_info


def fetch_all_eks_info(project, selected_region):
    if project == 'All':
        all_eks_clusters = get_clusters_project_tag(selected_region)
    else:
        all_eks_clusters = filter_clusters_by_project(project, selected_region)

    print('[INFO] Fetching EKS Clusters Info Related to Project:', project)
    all_eks_info = []
    for cluster in all_eks_clusters:
        try:
            cluster_name = cluster[0]
            region = cluster[1]
            print('[INFO] EKS:', cluster_name, region)

            nodegroups_info = get_cluster_nodegroups_info(cluster_name, region)
            if len(nodegroups_info) == 0:
                continue
            eks_info = [cluster_name, region, nodegroups_info]
            all_eks_info.append(eks_info)
        except:
            print('[ERROR] Get node groups info in', cluster[0])
            continue

    return all_eks_info


def is_cluster_running(desired_sizes):
    if len(set(desired_sizes)) == 1 and desired_sizes[0] == 0:
        return False
    else:
        return True


def process_table_rows(project, selected_region):
    try:
        all_eks = fetch_all_eks_info(project, selected_region)
        rows = []
        i = 1
        for eks in all_eks:
            cluster_name = eks[0]
            region = eks[1]
            ng_names = []
            min_sizes = []
            max_sizes = []
            desired_sizes = []
            asg_names = []

            for ng in eks[2]:
                ng_names.append(ng[0])
                desired_sizes.append(ng[1])
                min_sizes.append(ng[2])
                max_sizes.append(ng[3])
                asg_names.append(ng[4])

            if is_cluster_running(desired_sizes):
                state = 'RUNNING'
            else:
                state = 'STOPPED'

            temp_wk = 0
            temp_na = 0
            temp_other = 0
            timezone = '-'
            for asg in asg_names:
                scheduled_actions = check_scheduled_actions(asg, region)
                if any('scale-down-before-weekend-by-wave-app' in sa for sa in scheduled_actions):
                    temp_wk += 1
                    scheduled_actions = np.array(scheduled_actions)
                    temp = list(zip(*np.where(scheduled_actions == 'scale-down-before-weekend-by-wave-app')))
                    timezone = scheduled_actions[temp[0][0]][4]
                elif len(scheduled_actions) != 0:
                    temp_other += 1
                else:
                    temp_na += 1

            if temp_wk != 0 and temp_other != 0:
                schedules = 'STOP-ON-WEEKENDS,OTHER'
            elif temp_wk != 0:
                schedules = 'STOP-ON-WEEKENDS'
            elif temp_other != 0:
                schedules = 'OTHER'
            else:
                schedules = 'N/A'

            cells = [str(i), cluster_name, region, str(ng_names), str(desired_sizes), str(min_sizes), str(max_sizes), state, schedules, timezone]
            rows.append(ui.table_row(name=str(i), cells=cells))
            i += 1

        return rows

    except Exception as err:
        print(err)


def scale_cluster(cluster_name, region, nodegroups, state):
    eks_client = init_boto3_client('eks', region)
    if state == 'stop_eks':
        for ng in nodegroups:
            ng_info = eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng
            )
            ng_arn = ng_info['nodegroup']['nodegroupArn']
            desired_size = ng_info['nodegroup']['scalingConfig']['desiredSize']

            eks_client.update_nodegroup_config(
                clusterName=cluster_name,
                nodegroupName=ng,
                scalingConfig={
                    'minSize': 0,
                    'desiredSize': 0
                }
            )

            waiter = eks_client.get_waiter('nodegroup_active')
            waiter.wait(
                clusterName=cluster_name,
                nodegroupName=ng
            )

            eks_client.tag_resource(
                resourceArn=ng_arn,
                tags={
                    ng: str(desired_size)
                }
            )

    else:  # start eks
        for ng in nodegroups:
            ng_info = eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng
            )
            ng_arn = ng_info['nodegroup']['nodegroupArn']
            past_desired_size = ng_info['nodegroup']['tags'][ng] if ng in ng_info['nodegroup']['tags'] else 2

            eks_client.update_nodegroup_config(
                clusterName=cluster_name,
                nodegroupName=ng,
                scalingConfig={
                    'desiredSize': int(past_desired_size)
                }
            )

            waiter = eks_client.get_waiter('nodegroup_active')
            waiter.wait(
                clusterName=cluster_name,
                nodegroupName=ng
            )

            eks_client.untag_resource(
                resourceArn=str(ng_arn),
                tagKeys=[ng]
            )
        return past_desired_size


def set_scheduled_actions_on_cluster(cluster_name, region, nodegroups, timezone, state):
    eks_client = init_boto3_client('eks', region)
    if state == 'RUNNING':
        for ng in nodegroups:
            ng_info = eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng
            )
            desired_size = ng_info['nodegroup']['scalingConfig']['desiredSize']
            asg_name = ng_info['nodegroup']['resources']['autoScalingGroups'][0]['name']
            set_scheduled_actions_on_asg(asg_name, region, desired_size, timezone)

    else:  # STOPPED
        for ng in nodegroups:
            ng_info = eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng
            )
            desired_size = ng_info['nodegroup']['tags'][ng] if ng in ng_info['nodegroup']['tags'] else 2
            asg_name = ng_info['nodegroup']['resources']['autoScalingGroups'][0]['name']
            set_scheduled_actions_on_asg(asg_name, region, desired_size, timezone)


def set_scheduled_actions_on_asg(asg_name, region, desired_size, timezone):
    autoscaling_client = init_boto3_client('autoscaling', region)
    autoscaling_client.put_scheduled_update_group_action(
        AutoScalingGroupName=asg_name,
        ScheduledActionName='scale-down-before-weekend-by-wave-app',
        Recurrence='0 0 * * SAT',
        MinSize=0,
        DesiredCapacity=0,
        TimeZone=timezone
    )
    autoscaling_client.put_scheduled_update_group_action(
        AutoScalingGroupName=asg_name,
        ScheduledActionName='scale-up-after-weekend-by-wave-app',
        Recurrence='0 0 * * MON',
        DesiredCapacity=int(desired_size),
        TimeZone=timezone
    )


def check_scheduled_actions(asg_name, region):
    autoscaling_client = init_boto3_client('autoscaling', region)
    response = autoscaling_client.describe_scheduled_actions(
        AutoScalingGroupName=asg_name,
        MaxRecords=100
    )
    scheduled_actions = []
    if len(response['ScheduledUpdateGroupActions']) != 0:
        for item in response['ScheduledUpdateGroupActions']:
            action = [item['AutoScalingGroupName'], item['ScheduledActionName'], item['Recurrence'], item['DesiredCapacity'], item['TimeZone']]
            scheduled_actions.append(action)

    return scheduled_actions  # 2D Array


def delete_schedule_actions_asg(asg_name, region):
    autoscaling_client = init_boto3_client('autoscaling', region)
    autoscaling_client.delete_scheduled_action(
        AutoScalingGroupName=asg_name,
        ScheduledActionName='scale-down-before-weekend-by-wave-app'
    )
    autoscaling_client.delete_scheduled_action(
        AutoScalingGroupName=asg_name,
        ScheduledActionName='scale-up-after-weekend-by-wave-app'
    )


def delete_schedule_actions_cluster(cluster_name, region, nodegroups):
    eks_client = init_boto3_client('eks', region)
    for ng in nodegroups:
        ng_info = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=ng
        )
        asg_name = ng_info['nodegroup']['resources']['autoScalingGroups'][0]['name']
        delete_schedule_actions_asg(asg_name, region)


def get_cluster_aws_link(cluster_name, region_name):
    cluster_url = f"https://{region_name}.console.aws.amazon.com/eks/home?region={region_name}#/clusters/{cluster_name}".format(region_name=region_name, cluster_name=cluster_name)
    return cluster_url
