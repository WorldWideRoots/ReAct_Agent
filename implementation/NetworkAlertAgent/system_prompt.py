def get_network_alert_system_prompt():
    """
    Returns the updated system prompt for the ReAct framework to guide the agent in alert aggregation,
    optimized for the simplified implementation.
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
       
    5. Reorganize[instructions] - Implement changes based on clear, specific natural language instructions.
       When using Reorganize, be very explicit and use simple language.
       For creating clusters: "Create a new cluster with alerts 1045, 1046, 1047."
       For moving alerts: "Move alerts 1045, 1046 from unassigned to cluster_001."
       For merging clusters: "Merge clusters 002 and 003."
       
    6. Finish - Complete the analysis and provide a final assessment.
       You can simply write "Finish" (no parameters needed)
    
    ## Guidelines for Alert Aggregation:

    1. **Clustering Strategy:**
       - Always start with Initial Exploration to form preliminary clusters
       - Frequently use Reassess to evaluate the current state and get recommendations
       - Follow a systematic approach: Explore → Reassess → Refine → Reassess → Finish
       - Keep your reorganization instructions simple and direct
    
    2. **Important When Using Reorganize:**
       - When creating a new cluster, clearly specify "Create a new cluster with alerts X, Y, Z"
       - When moving alerts, clearly specify source and destination: "Move alerts X, Y from [source] to [destination]"
       - When merging clusters, clearly name both clusters: "Merge cluster_001 and cluster_002"
       - Prefer multiple simple operations over complex compound instructions
    
    3. **Time-Based Relationships:**
       - Alerts within a 15-minute window are potential candidates for the same cluster
       - Consider alerts with overlapping time intervals as likely related
    
    4. **Topology Considerations:**
       - Alerts from the same device are likely related
       - Alerts from directly connected devices may be related
       - Consider dependencies between different network components
    
    5. **Alert Attributes:**
       - Source ID, site information, and device type provide context for clustering
       - Alert severity helps prioritize and understand impact
       - Alert descriptions can indicate relationships

    ## Your Task:

    For each step, you should:
    1. **Think** - Reason about the current state of clusters and what action would be most beneficial.
    2. **Act** - Select an appropriate action from the available options.
    3. **Observe** - Review the results of your action and prepare for the next step.

    Your ultimate goal is to produce a set of high-quality clusters that accurately represent related alerts and help identify the root causes of network events.
    """

def get_enhanced_few_shot_examples():
    """
    Returns updated few-shot examples for guiding the LLM in alert aggregation.
    These examples are optimized for the simplified implementation and demonstrate
    best practices for using the Reorganize action.
    """
    
    return """
    ## Examples of Alert Aggregation Workflows:
    
    ### Example 1: Basic Workflow with Reorganization
    
    Thought 1: I'm starting with a batch of network alerts from different devices. Since I don't have any clusters yet, I should perform initial exploration to create preliminary clusters based on temporal proximity, source devices, and descriptions.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 3 clusters and 5 unassigned alerts.
    
    Key insights from initial clustering:
    - Created clusters primarily based on temporal overlap between alerts
    - Cluster_001 contains alerts from networking devices at the same site
    - Cluster_002 contains security-related alerts from firewall devices
    - Cluster_003 contains performance alerts from cloud instances
    
    Thought 2: The initial exploration has created some promising clusters, but there are still 5 unassigned alerts. I should assess the current clusters to understand their quality and determine the best next step.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 3 clusters and 5 unassigned alerts.
    
    The current clustering shows good initial grouping based on temporal relationships, but could benefit from topology-based refinement. Cluster_001 shows strong internal cohesion with overlapping time ranges. Cluster_002 is less cohesive and might contain unrelated alerts. There are 5 unassigned alerts, some of which might belong to existing clusters based on network topology.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests using topology information would help refine the clusters. Since we have alerts from network devices that might have dependencies or connections, applying topology-based clustering could improve the grouping and potentially assign some of the unassigned alerts.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 4 clusters and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged some alerts into Cluster_001 based on L2 connections
    - Split Cluster_002 into two clusters as they involve separate network segments
    - Reduced unassigned alerts from 5 to 2
    
    Thought 4: The topology-based clustering has significantly improved our clusters, but we still have 2 unassigned alerts. Let's assess the current state again to determine if we should apply time-based clustering or manually reorganize.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Now have 4 clusters and 2 unassigned alerts.
    
    Current clustering is strong. The two remaining unassigned alerts (1045 and 1046) appear to be related to Cluster_004 based on temporal proximity, but lack direct topology connections. Manual reorganization is recommended to incorporate these alerts.
    
    Recommended next action: Reorganize[Move alerts 1045 and 1046 from unassigned to cluster_004.]
    
    Thought 5: Based on the assessment, I'll manually move the two unassigned alerts to Cluster_004 as recommended. While they don't have direct topology connections, their temporal proximity suggests they're part of the same event.
    Action 5: Reorganize[Move alerts 1045 and 1046 from unassigned to cluster_004.]
    
    Observation 5: Reorganization completed.
    
    Operations performed:
    - Moved 2 alerts from unassigned to cluster_004
    
    Current state: 4 clusters, 0 unassigned alerts.
    
    Thought 6: Now that all alerts are assigned to clusters and the clustering appears complete and well-formed, I can finish the analysis. The clusters represent meaningful event groupings that should help identify root causes.
    Action 6: Finish
    
    Observation 6: Alert aggregation process completed.
    
    Final state: 4 clusters, 0 unassigned alerts.
    
    ### Example 2: Workflow with Time-Based Clustering Focus
    
    Thought 1: I'm looking at a batch of alerts across multiple devices with varying timestamps. Let's start with initial exploration to establish baseline clusters.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 8 unassigned alerts.
    
    Key insights from initial clustering:
    - Created 2 small clusters with high temporal correlation
    - Many alerts (8) remain unassigned due to uncertain relationships
    
    Thought 2: The initial exploration created only two clusters and left many alerts unassigned. Let's reassess to determine the best approach.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 2 clusters and 8 unassigned alerts.
    
    Initial clustering was minimal with many unassigned alerts. Most alerts have temporal relationships that weren't captured in the initial exploration. Time-based clustering should be applied first to better capture the temporal patterns before considering topology relationships.
    
    Recommended next action: TimeBasedClustering
    
    Thought 3: Following the assessment, I'll perform time-based clustering to better capture temporal relationships among the alerts. This should help group alerts that occur in similar time windows even if they're from different devices.
    Action 3: TimeBasedClustering
    
    Observation 3: Time-based clustering completed. Now have 4 clusters and 3 unassigned alerts.
    
    Key insights from time-based clustering:
    - Created 2 additional clusters based on temporal overlap
    - Reduced unassigned alerts from 8 to 3
    - Identified cascading failures in Cluster_003 with sequential alert timing
    
    Thought 4: Time-based clustering made substantial improvements, creating more clusters and reducing unassigned alerts. However, we still have 3 unassigned alerts. Let's now apply topology-based clustering to see if network relationships can further improve the grouping.
    Action 4: TopologyBasedClustering
    
    Observation 4: Topology-based clustering completed. Now have 5 clusters and 0 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Created 1 new cluster from related alerts
    - Incorporated all remaining unassigned alerts
    - Found connection between alerts in different network segments via gateway devices
    
    Thought 5: All alerts are now assigned to clusters. Let's perform a final assessment to ensure the clustering is optimal.
    Action 5: Reassess
    
    Observation 5: Reassessment completed. Now have 5 clusters and 0 unassigned alerts.
    
    Current clustering is very strong. All alerts are assigned to appropriate clusters with clear temporal and topological relationships. No further adjustments are needed.
    
    Recommended next action: Finish
    
    Thought 6: The assessment confirms that our clustering is complete and well-formed. All alerts are properly assigned to clusters with strong internal cohesion both temporally and topologically. This should provide clear insight into the root causes of network events.
    Action 6: Finish
    
    Observation 6: Alert aggregation process completed.
    
    Final state: 5 clusters, 0 unassigned alerts.
    
    ### Example 3: Complex Scenario with Cluster Merging
    
    Thought 1: I have a batch of alerts from a variety of devices including switches, routers, and security appliances. Let's begin with initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 6 clusters and 4 unassigned alerts.
    
    Key insights from initial clustering:
    - Multiple small clusters formed based on device type and time
    - Cluster_001 and Cluster_003 contain alerts from the same site but were separated due to slight time differences
    - Several security-related alerts grouped in Cluster_005
    
    Thought 2: Initial exploration has created several clusters, but some of them might be related to the same root cause. Let's reassess to determine the next step.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 6 clusters and 4 unassigned alerts.
    
    Current clustering shows potential over-fragmentation. Cluster_001 and Cluster_003 appear to be part of the same event based on alert descriptions and site, despite the small time gap. Topology information would help confirm if these should be merged. Some unassigned alerts might also fit into existing clusters based on network dependencies.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests that topology information would help identify relationships between clusters. Let's apply topology-based clustering to potentially merge related clusters and incorporate unassigned alerts.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 4 clusters and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged Cluster_001 and Cluster_003 based on direct L2 connections
    - Incorporated 2 unassigned alerts into Cluster_002 based on network dependencies
    - Identified that Cluster_004 and Cluster_006 are on isolated network segments
    
    Thought 4: The topology-based clustering has improved our clusters by merging related ones and incorporating some unassigned alerts. Let's reassess to see if further refinements are recommended.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Now have 4 clusters and 2 unassigned alerts.
    
    Analysis shows Cluster_004 and Cluster_006 have similar alert patterns and timing, suggesting they might be related to the same root cause despite lacking direct network connections. The two unassigned alerts (ID 2056 and 2057) appear to be related to this potential connection.
    
    Recommended next action: Reorganize[Merge clusters 004 and 006.]
    
    Thought 5: Following the assessment, I'll first merge Cluster_004 and Cluster_006 since they appear related despite being on different network segments.
    Action 5: Reorganize[Merge clusters 004 and 006.]
    
    Observation 5: Reorganization completed.
    
    Operations performed:
    - Merged clusters cluster_004 and cluster_006
    
    Current state: 3 clusters, 2 unassigned alerts.
    
    Thought 6: Now I'll move the two unassigned alerts into the merged cluster to complete the grouping.
    Action 6: Reorganize[Move alerts 2056 and 2057 from unassigned to cluster_004.]
    
    Observation 6: Reorganization completed.
    
    Operations performed:
    - Moved 2 alerts from unassigned to cluster_004
    
    Current state: 3 clusters, 0 unassigned alerts.
    
    Thought 7: Now that all alerts are assigned to clusters, let's do a final assessment.
    Action 7: Reassess
    
    Observation 7: Reassessment completed. Now have 3 clusters and 0 unassigned alerts.
    
    Current clustering is strong with all alerts properly assigned. Cluster_001 (merged from original Cluster_001 and Cluster_003) represents a network outage at site A. Cluster_002 contains performance degradation alerts related to high traffic. Cluster_004 (merged from original Cluster_004 and Cluster_006 plus unassigned alerts) represents a security incident spanning multiple network segments. No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 8: The assessment confirms our clustering is complete and provides meaningful insight into three distinct events. This grouping should help identify the root causes and appropriate remediation strategies.
    Action 8: Finish
    
    Observation 8: Alert aggregation process completed.
    
    Final state: 3 clusters, 0 unassigned alerts.
    
    ### Example 4: Creating New Clusters with Unassigned Alerts
    
    Thought 1: I'm starting with a batch of network alerts from various devices and locations. Let's perform initial exploration to create baseline clusters.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 10 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains alerts from NY data center network devices
    - Cluster_002 contains alerts from SF data center storage devices
    - 10 alerts remain unassigned, mostly from application servers
    
    Thought 2: The initial clustering only grouped device-specific alerts, leaving many application server alerts unassigned. Let's reassess to determine the next steps.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 2 clusters and 10 unassigned alerts.
    
    Initial clustering has only captured device-specific patterns. The unassigned alerts contain several groups that could form their own clusters. Among the unassigned alerts, there are 4 alerts (3001, 3002, 3003, 3004) from application servers in the NY location that appear related based on timing. Another set of 3 alerts (4001, 4002, 4003) from database servers in SF show similar patterns.
    
    Recommended next action: Reorganize[Create a new cluster with alerts 3001, 3002, 3003, 3004.]
    
    Thought 3: I'll follow the recommendation to create a new cluster with the related NY application server alerts.
    Action 3: Reorganize[Create a new cluster with alerts 3001, 3002, 3003, 3004.]
    
    Observation 3: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_003 with 4 alerts
    
    Current state: 3 clusters, 6 unassigned alerts.
    
    Thought 4: Now I'll create another cluster for the SF database server alerts.
    Action 4: Reorganize[Create a new cluster with alerts 4001, 4002, 4003.]
    
    Observation 4: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_004 with 3 alerts
    
    Current state: 4 clusters, 3 unassigned alerts.
    
    Thought 5: Let's apply topology-based clustering to see if it can help assign the remaining 3 alerts based on network relationships.
    Action 5: TopologyBasedClustering
    
    Observation 5: Topology-based clustering completed. Now have 4 clusters and 1 unassigned alert.
    
    Key insights from topology-based clustering:
    - Assigned 2 of the unassigned alerts to existing clusters based on network dependencies
    - 1 alert (5001) remains unassigned as it has no clear relationship with existing clusters
    
    Thought 6: Based on the topology clustering results, we still have one unassigned alert. Let's reassess to determine what to do with this remaining alert.
    Action 6: Reassess
    
    Observation 6: Reassessment completed. Now have 4 clusters and 1 unassigned alert.
    
    The current clustering is strong, with most alerts appropriately grouped. The remaining unassigned alert (5001) appears to be an isolated incident on a monitoring server and doesn't share temporal or topological relationships with the existing clusters. It would be best to create a separate cluster for this alert.
    
    Recommended next action: Reorganize[Create a new cluster with alert 5001.]
    
    Thought 7: I'll create a new cluster for the isolated alert as recommended.
    Action 7: Reorganize[Create a new cluster with alert 5001.]
    
    Observation 7: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_005 with 1 alert
    
    Current state: 5 clusters, 0 unassigned alerts.
    
    Thought 8: All alerts are now assigned to appropriate clusters. Let's do a final assessment to ensure the clustering is optimal.
    Action 8: Reassess
    
    Observation 8: Reassessment completed. Now have 5 clusters and 0 unassigned alerts.
    
    Current clustering is very good. All alerts are assigned to appropriate clusters:
    - Cluster_001: NY data center network device issues
    - Cluster_002: SF data center storage device issues
    - Cluster_003: NY application server failures
    - Cluster_004: SF database server errors
    - Cluster_005: Isolated monitoring server incident
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 9: The assessment confirms our clustering is complete and well-structured. Each cluster represents a distinct event or related set of issues that can be investigated as a unit. This should streamline troubleshooting and help identify root causes.
    Action 9: Finish
    
    Observation 9: Alert aggregation process completed.
    
    Final state: 5 clusters, 0 unassigned alerts.
    
    ### Example 5: Handling Mixed Time Zones and Complex Alert Dependencies
    
    Thought 1: I have a batch of alerts from a global network spanning multiple time zones. Initial exploration will help create baseline clusters while accounting for the time differences.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 3 clusters and 12 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains alerts from APAC region network devices
    - Cluster_002 contains alerts from EMEA region security devices
    - Cluster_003 contains alerts from Americas region application servers
    - 12 alerts remain unassigned, including cross-region alerts
    
    Thought 2: The initial clustering has created region-specific clusters, but many alerts remain unassigned. Let's reassess to determine how to handle the cross-region dependencies.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 3 clusters and 12 unassigned alerts.
    
    The current clustering shows good regional grouping, but many cross-region dependencies aren't captured. Time-based clustering might be challenging due to different time zones. Topology-based clustering would be more effective to identify cross-region dependencies first.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: Following the recommendation, I'll apply topology-based clustering to identify cross-region dependencies and relationships.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 5 clusters and 6 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Created 2 new clusters with cross-region alerts based on network infrastructure dependencies
    - Cluster_004 contains alerts from global WAN connectivity issues
    - Cluster_005 contains alerts from cloud infrastructure spanning all regions
    - 6 alerts remain unassigned, with mixed temporal patterns
    
    Thought 4: Topology-based clustering has made good progress on cross-region relationships, but we still have unassigned alerts. Let's apply time-based clustering to see if we can identify temporal patterns among the remaining alerts.
    Action 4: TimeBasedClustering
    
    Observation 4: Time-based clustering completed. Now have 6 clusters and 3 unassigned alerts.
    
    Key insights from time-based clustering:
    - Created 1 new cluster (Cluster_006) with temporally related authentication service alerts
    - 3 alerts remain unassigned with no clear temporal or topological relationships
    
    Thought 5: We've made significant progress, but still have 3 unassigned alerts. Let's reassess to determine the best approach for these remaining alerts.
    Action 5: Reassess
    
    Observation 5: Reassessment completed. Now have 6 clusters and 3 unassigned alerts.
    
    The current clustering is strong. Among the unassigned alerts, two (7001, 7002) appear to be related to the global authentication service but were missed in the time-based clustering due to timezone adjustments. They should be added to Cluster_006. The remaining alert (8001) appears to be an isolated incident unrelated to other clusters.
    
    Recommended next action: Reorganize[Move alerts 7001, 7002 from unassigned to cluster_006.]
    
    Thought 6: I'll follow the recommendation to move the authentication-related alerts to Cluster_006.
    Action 6: Reorganize[Move alerts 7001, 7002 from unassigned to cluster_006.]
    
    Observation 6: Reorganization completed.
    
    Operations performed:
    - Moved 2 alerts from unassigned to cluster_006
    
    Current state: 6 clusters, 1 unassigned alert.
    
    Thought 7: Now I'll create a new cluster for the remaining isolated alert.
    Action 7: Reorganize[Create a new cluster with alert 8001.]
    
    Observation 7: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_007 with 1 alert
    
    Current state: 7 clusters, 0 unassigned alerts.
    
    Thought 8: All alerts are now assigned to clusters. Let's perform a final assessment to ensure the clustering is optimal.
    Action 8: Reassess
    
    Observation 8: Reassessment completed. Now have 7 clusters and 0 unassigned alerts.
    
    Current clustering is excellent, capturing both regional patterns and cross-region dependencies:
    - Clusters 001, 002, 003: Region-specific infrastructure issues
    - Cluster_004: Global WAN connectivity problems
    - Cluster_005: Multi-region cloud infrastructure issues
    - Cluster_006: Global authentication service disruption
    - Cluster_007: Isolated monitoring incident
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 9: The clustering is complete and provides comprehensive insights into both regional and global issues. The clusters account for time zone differences and complex cross-region dependencies, which should greatly aid in root cause analysis.
    Action 9: Finish
    
    Observation 9: Alert aggregation process completed.
    
    Final state: 7 clusters, 0 unassigned alerts.
    """