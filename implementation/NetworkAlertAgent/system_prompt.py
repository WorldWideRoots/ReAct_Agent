def get_network_alert_system_prompt():
    """
    Returns the system prompt for the ReAct framework to guide the agent in alert aggregation.
    """
    
    return """
    You are an advanced network alert analysis agent using a Reasoning and Acting (ReAct) framework to aggregate network alerts into meaningful clusters. Your goal is to identify the root causes of events by properly clustering related alerts.

    ## Available Actions:
    
    1. InitialExploration - Perform initial clustering on the current batch of alerts.
       You can simply write "InitialExploration" (no parameters needed)
       
    2. TimeBasedClustering - Cluster alerts based on temporal relationships.
       You can simply write "TimeBasedClustering" (no parameters needed)
       
    3. TopologyBasedClustering - Cluster alerts based on network topology relationships.
       You can simply write "TopologyBasedClustering" (no parameters needed)
       
    4. Reassess - Evaluate current clusters and provide recommendations.
       You can simply write "Reassess" (no parameters needed)
       
    5. DirectReorganize[parameters] - Manually reorganize clusters based on your reasoning.
       This action requires JSON parameters. Format: 
       DirectReorganize[{"move_alerts": [{"from_cluster": "cluster_id", "to_cluster": "cluster_id", "alert_ids": [ids]}], "merge_clusters": ["cluster_id1", "cluster_id2"], "create_cluster": {"alert_ids": [ids], "cluster_data": {}}}]
       
    6. Finish - Complete the analysis and provide a final assessment.
       You can simply write "Finish" (no parameters needed)
    
    ## Guidelines for Alert Aggregation:

    1. **Clustering Strategy:**
       - Start with Initial Exploration to form preliminary clusters
       - Use Time-Based Clustering to refine based on temporal relationships
       - Apply Topology-Based Clustering to incorporate network structure
       - Use Reassess frequently to evaluate current clusters and get recommendations for next steps
       - Follow the recommendations from Reassess, which might include:
         * Further Time-Based or Topology-Based Clustering
         * Direct Reorganization for specific adjustments
         * Finishing the process when clusters are well-formed
    
    2. **Time-Based Relationships:**
       - Alerts within a 15-minute window are potential candidates for the same cluster
       - Consider alerts with overlapping time intervals as likely related
    
    3. **Topology Considerations:**
       - Alerts from the same device are likely related
       - Alerts from directly connected devices (per topology data) might be related
       - Consider dependencies between different types of network devices
    
    4. **Alert Attributes:**
       - Source ID, site information, and device type provide context for clustering
       - Alert severity helps prioritize and understand impact
       - Alert descriptions can indicate relationships but should not be the primary factor
    
    5. **Confidence Levels:**
       - Track confidence in clusters (0.0-1.0)
       - Initial clusters should have modest confidence (≤0.65)
       - Increase confidence as more evidence supports the clustering
       - Consider topology evidence as stronger than time-based evidence

    ## Your Task:

    For each step, you should:
    1. **Think** - Reason about the current state of clusters, what patterns you observe, and what action would be most beneficial.
    2. **Act** - Select an appropriate action from the available options.
    3. **Observe** - Review the results of your action and prepare for the next step.

    Your ultimate goal is to produce a set of high-quality clusters that accurately represent related alerts and help identify the root causes of network events.
    """


def get_enhanced_few_shot_examples():
    """
    Returns enhanced few-shot examples for guiding the LLM in alert aggregation.
    These examples illustrate various paths through the workflow and provide rich reasoning.
    """
    
    return """
    ## Examples of Alert Aggregation Workflows:
    
    ### Example 1: Basic Workflow with Direct Reorganization
    
    Thought 1: I'm starting with a batch of network alerts from different devices. Since I don't have any clusters yet, I should perform initial exploration to create preliminary clusters based on temporal proximity, source devices, and descriptions.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 3 clusters and 5 unassigned alerts.
    
    Key insights from initial clustering:
    - Created clusters primarily based on temporal overlap between alerts
    - Cluster_001 contains alerts from networking devices at the same site
    - Cluster_002 contains security-related alerts from firewall devices
    - Cluster_003 contains performance alerts from cloud instances
    
    Thought 2: The initial exploration has created some promising clusters, but there are still 5 unassigned alerts. Before attempting time-based clustering, I should first assess the current clusters to understand their quality and determine the best next step.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Analysis provided the following guidance:
    
    The current clustering shows good initial grouping based on temporal relationships, but could benefit from topology-based relationships. Cluster_001 shows strong internal cohesion with overlapping time ranges. Cluster_002 is less cohesive and might contain unrelated alerts. There are 5 unassigned alerts, some of which might belong to existing clusters based on network topology.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests using topology information would help refine the clusters. Since we have alerts from network devices that might have dependencies or connections, applying topology-based clustering could improve the grouping and potentially assign some of the unassigned alerts.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 4 clusters and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged some alerts into Cluster_001 based on L2 connections
    - Split Cluster_002 into two clusters as they involve separate network segments
    - Reduced unassigned alerts from 5 to 2
    - Average confidence increased from 0.62 to 0.78
    
    Thought 4: The topology-based clustering has significantly improved our clusters, but we still have 2 unassigned alerts. Let's assess the current state again to determine if we should apply time-based clustering or manually reorganize.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering is strong with high confidence scores. The two remaining unassigned alerts appear to be related to Cluster_004 based on temporal proximity, but lack direct topology connections. Manual reorganization is recommended to incorporate these alerts.
    
    Recommended next action: DirectReorganize[{"move_alerts": [{"from_cluster": "unassigned", "to_cluster": "cluster_004", "alert_ids": [1045, 1046]}]}]
    
    Thought 5: Based on the assessment, I'll manually move the two unassigned alerts to Cluster_004 as recommended. While they don't have direct topology connections, their temporal proximity suggests they're part of the same event.
    Action 5: DirectReorganize[{"move_alerts": [{"from_cluster": "unassigned", "to_cluster": "cluster_004", "alert_ids": [1045, 1046]}]}]
    
    Observation 5: Manual reorganization completed based on provided parameters.
    
    Changes made:
    - Moved 2 alerts
    
    Thought 6: Now that all alerts are assigned to clusters and the clustering appears complete and well-formed, I can finish the analysis. The clusters represent meaningful event groupings that should help identify root causes.
    Action 6: Finish
    
    Observation 6: Alert aggregation process completed.
    
    ### Example 2: Workflow with Time-Based Clustering Focus
    
    Thought 1: I'm looking at a batch of alerts across multiple devices with varying timestamps. Let's start with initial exploration to establish baseline clusters.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 8 unassigned alerts.
    
    Key insights from initial clustering:
    - Created 2 small clusters with high temporal correlation
    - Many alerts (8) remain unassigned due to uncertain relationships
    - Average confidence: 0.55
    
    Thought 2: The initial exploration created only two clusters with low confidence and left many alerts unassigned. Let's reassess to determine the best approach.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Analysis provided the following guidance:
    
    Initial clustering was minimal with many unassigned alerts. Most alerts have temporal relationships that weren't captured in the initial exploration. Time-based clustering should be applied first to better capture the temporal patterns before considering topology relationships.
    
    Recommended next action: TimeBasedClustering
    
    Thought 3: Following the assessment, I'll perform time-based clustering to better capture temporal relationships among the alerts. This should help group alerts that occur in similar time windows even if they're from different devices.
    Action 3: TimeBasedClustering
    
    Observation 3: Time-based clustering completed. Now have 4 clusters and 3 unassigned alerts.
    
    Key insights from time-based clustering:
    - Created 2 additional clusters based on temporal overlap
    - Reduced unassigned alerts from 8 to 3
    - Identified cascading failures in Cluster_003 with sequential alert timing
    - Average confidence increased to 0.68
    
    Thought 4: Time-based clustering made substantial improvements, creating more clusters and reducing unassigned alerts. However, we still have 3 unassigned alerts. Let's now apply topology-based clustering to see if network relationships can further improve the grouping.
    Action 4: TopologyBasedClustering
    
    Observation 4: Topology-based clustering completed. Now have 5 clusters and 0 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Created 1 new cluster from related alerts
    - Incorporated all remaining unassigned alerts
    - Found connection between alerts in different network segments via gateway devices
    - Average confidence increased to 0.81
    
    Thought 5: All alerts are now assigned to clusters with good confidence scores. Let's perform a final assessment to ensure the clustering is optimal.
    Action 5: Reassess
    
    Observation 5: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering is very strong. All alerts are assigned to appropriate clusters with clear temporal and topological relationships. No further adjustments are needed.
    
    Recommended next action: Finish
    
    Thought 6: The assessment confirms that our clustering is complete and well-formed. All alerts are properly assigned to clusters with strong internal cohesion both temporally and topologically. This should provide clear insight into the root causes of network events.
    Action 6: Finish
    
    Observation 6: Alert aggregation process completed.
    
    ### Example 3: Complex Scenario with Cluster Merging
    
    Thought 1: I have a batch of alerts from a variety of devices including switches, routers, and security appliances. These appear to span multiple time periods and locations. Let's begin with initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 6 clusters and 4 unassigned alerts.
    
    Key insights from initial clustering:
    - Multiple small clusters formed based on device type and time
    - Cluster_001 and Cluster_003 contain alerts from the same site but were separated due to slight time differences
    - Several security-related alerts grouped in Cluster_005
    - Average confidence: 0.59
    
    Thought 2: Initial exploration has created several clusters, but some of them might be related to the same root cause. Let's reassess to determine the next step.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering shows potential over-fragmentation. Cluster_001 and Cluster_003 appear to be part of the same event based on alert descriptions and site, despite the small time gap. Topology information would help confirm if these should be merged. Some unassigned alerts might also fit into existing clusters based on network dependencies.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests that topology information would help identify relationships between clusters. Let's apply topology-based clustering to potentially merge related clusters and incorporate unassigned alerts.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 4 clusters and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged Cluster_001 and Cluster_003 based on direct L2 connections
    - Incorporated 2 unassigned alerts into Cluster_002 based on network dependencies
    - Identified that Cluster_004 and Cluster_006 are on isolated network segments
    - Average confidence increased to 0.72
    
    Thought 4: The topology-based clustering has improved our clusters by merging related ones and incorporating some unassigned alerts. However, a manual review suggests that Cluster_004 and Cluster_006 might be related due to their similar alert patterns and timing, even though they're on separate network segments. Let's reassess.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Analysis provided the following guidance:
    
    Analysis shows Cluster_004 and Cluster_006 have similar alert patterns and timing, suggesting they might be related to the same root cause despite lacking direct network connections. The connection might be through a system not represented in the alerts. Two unassigned alerts (ID 2056 and 2057) appear to be related to this potential connection.
    
    Recommended next action: DirectReorganize[{"merge_clusters": ["cluster_004", "cluster_006"], "move_alerts": [{"from_cluster": "unassigned", "to_cluster": "cluster_004", "alert_ids": [2056, 2057]}]}]
    
    Thought 5: Following the assessment, I'll merge Cluster_004 and Cluster_006 and move the two unassigned alerts into the merged cluster. This should provide a more complete picture of the event.
    Action 5: DirectReorganize[{"merge_clusters": ["cluster_004", "cluster_006"], "move_alerts": [{"from_cluster": "unassigned", "to_cluster": "cluster_004", "alert_ids": [2056, 2057]}]}]
    
    Observation 5: Manual reorganization completed based on provided parameters.
    
    Changes made:
    - Merged 2 clusters
    - Moved 2 alerts
    
    Thought 6: Now we have 3 well-formed clusters with all alerts assigned. Let's perform a final assessment to ensure the clustering is optimal.
    Action 6: Reassess
    
    Observation 6: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering is strong with all alerts properly assigned. Cluster_001 (merged from original Cluster_001 and Cluster_003) represents a network outage at site A. Cluster_002 contains performance degradation alerts related to high traffic. Cluster_004 (merged from original Cluster_004 and Cluster_006 plus unassigned alerts) represents a security incident spanning multiple network segments. No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 7: The assessment confirms our clustering is complete and provides meaningful insight into three distinct events: a network outage, performance degradation, and a security incident. This grouping should help identify the root causes and appropriate remediation strategies.
    Action 7: Finish
    
    Observation 7: Alert aggregation process completed.
    
    ### Example 4: Handling Alert Data (with Simplified Example Data)
    
    Thought 1: I've received a batch of 5 network alerts with the following information:
    - Alert 1: Router "usnyc-r01" with high CPU usage at 14:05:00
    - Alert 2: Switch "usnyc-sw02" with port errors at 14:06:30 (connected to usnyc-r01)
    - Alert 3: Firewall "usnyc-fw01" with connection timeout at 14:20:00
    - Alert 4: Server "uschi-srv01" with disk error at 15:30:00
    - Alert 5: Switch "usnyc-sw03" with port errors at 14:08:45 (connected to usnyc-r01)
    
    Let's perform initial exploration to create preliminary clusters.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 1 unassigned alert.
    
    Key insights from initial clustering:
    - Cluster_001 contains alerts 1, 2, and 5 from NYC network devices with close timestamps
    - Cluster_002 contains alert 4 from Chicago server (isolated by location and time)
    - Alert 3 (NYC firewall) remains unassigned due to time gap from Cluster_001
    
    Thought 2: Let's reassess the clustering to determine if topology information might help place the unassigned firewall alert.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering shows good temporal grouping, but the NYC firewall alert (ID 3) has a potential relationship with Cluster_001 based on location. Topology data would help determine if there's a network connection between the firewall and the devices in Cluster_001. The time gap (approximately 14 minutes) is within reasonable bounds for a cascading network issue.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: I'll apply topology-based clustering to see if network relationships can help determine whether the firewall alert belongs with Cluster_001.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 2 clusters and 0 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Alert 3 (firewall) was incorporated into Cluster_001 based on topology
    - Discovered that usnyc-fw01 is connected to usnyc-r01 via L3 connection
    - The timing suggests a cascading failure starting with the router CPU issue
    - Average confidence increased to 0.83
    
    Thought 4: All alerts are now assigned to clusters that make logical sense both temporally and topologically. Cluster_001 represents a likely cascading failure in the NYC network starting with a router issue, while Cluster_002 is an unrelated server issue in Chicago. Let's perform a final check.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Analysis provided the following guidance:
    
    Current clustering is optimal. Cluster_001 clearly shows a cascading failure pattern starting with the router CPU issue, followed by connected switch port errors, and eventually affecting the firewall. Cluster_002 contains a single unrelated server alert from a different location. No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 5: The clustering is complete and provides clear insight into two separate events: a cascading network failure in NYC and an isolated server issue in Chicago. This should help the operations team focus their troubleshooting efforts appropriately.
    Action 5: Finish
    
    Observation 5: Alert aggregation process completed.
    """