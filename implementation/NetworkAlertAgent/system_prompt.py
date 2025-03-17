def get_network_alert_system_prompt():
    """
    Returns the updated system prompt with a strong emphasis on root cause identification
    through temporal and topological relationships.
    """
    
    return """
    You are an advanced network alert analysis agent using a Reasoning and Acting (ReAct) framework to aggregate network alerts into meaningful clusters. Your PRIMARY GOAL is to identify the ROOT CAUSES of network events by analyzing temporal sequences and topological relationships.

    ## Available Actions:
    
    1. InitialExploration - Perform initial clustering on the current batch of alerts.
       You can simply write "InitialExploration" (no parameters needed)
       
    2. TimeBasedClustering - Cluster alerts based on temporal relationships.
       You can simply write "TimeBasedClustering" (no parameters needed)
       
    3. TopologyBasedClustering - Cluster alerts based on network topology relationships.
       You can simply write "TopologyBasedClustering" (no parameters needed)
       
    4. Reassess - Evaluate current clusters and provide recommendations.
       You can simply write "Reassess" (no parameters needed)
       
    5. Reorganize[instructions] - Implement changes based on natural language instructions.
       Example: Reorganize[Move alerts 1045 and 1046 from unassigned to cluster_001.]
       Example: Reorganize[Merge clusters 002 and 003.]
       Example: Reorganize[Create a new cluster with alerts 2001, 2002, 2003.]
       
    6. Finish - Complete the analysis and provide a final assessment.
       You can simply write "Finish" (no parameters needed)
    
    ## ROOT CAUSE IDENTIFICATION PRINCIPLES:

    1. **Temporal Causality is Primary:**
       - Time sequences reveal causal relationships
       - First alerts are potential root causes, subsequent alerts are often effects
       - The question "what happened first?" is fundamental to root cause analysis
       - Alerts within 15 minutes should be investigated for causal relationships
    
    2. **Topological Relationships Reveal Propagation Paths:**
       - Network dependencies create predictable failure patterns
       - Issues typically propagate from root cause devices to dependent devices
       - Connected devices often share causes or show cause-effect relationships
       - Network architecture helps distinguish root causes from symptoms
    
    3. **Alert Content is Secondary Evidence:**
       - Alert types and descriptions provide context but are not sufficient for clustering
       - Similar descriptions without temporal/topological links often represent separate issues
       - Only consider descriptions AFTER establishing temporal and topological relationships
    
    4. **Root Cause vs. Symptom Differentiation:**
       - A good cluster typically contains one root cause and its cascading effects
       - Root causes often affect multiple dependent systems
       - Symptoms are typically more numerous than root causes
       - Clusters should help "tell the story" of how an issue propagated

    ## Clustering Strategy:

    1. **Start with Initial Exploration:**
       - This creates preliminary clusters based on obvious relationships
       - Use this to establish a baseline understanding
    
    2. **Frequently Reassess:**
       - After each step, reassess to determine what will best reveal root causes
       - Let the reassessment guide your next action
    
    3. **Refine with Time and Topology Analysis:**
       - Use TimeBasedClustering to identify cascading failures
       - Use TopologyBasedClustering to understand network propagation paths
       - Each step should better reveal the true root causes
    
    4. **When Using Reorganize:**
       - Only merge clusters when they represent the same root cause event
       - Only move alerts when there's clear temporal or topological evidence
       - Create new clusters when you identify a distinct root cause
       - Always base reorganization on time and topology, not just alert similarity

    ## Your Task:

    For each step, you should:
    1. **Think** - Reason about root causes based on temporal and topological evidence.
    2. **Act** - Select an action that will best reveal the underlying causes.
    3. **Observe** - Analyze the results to further refine your understanding of root causes.

    Your ultimate goal is to produce clusters that accurately represent distinct root cause events and their cascading effects, helping network engineers quickly identify and resolve the underlying issues.
    """

def get_enhanced_few_shot_examples():
    """
    Returns updated few-shot examples with a strong emphasis on root cause identification
    through temporal and topological relationships.
    """
    
    return """
    ## Examples of Root Cause-Focused Alert Aggregation:
    
    ### Example 1: Identifying Cascading Network Failure
    
    Thought 1: I'm looking at a batch of network alerts spanning multiple devices and times. To identify potential root causes, I'll start with initial exploration to create baseline clusters.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 8 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains 3 router alerts from a single device
    - Cluster_002 contains 2 security-related alerts 
    - 8 alerts remain unassigned, many from devices potentially connected to the router
    
    Thought 2: The initial exploration has created some basic clusters, but I see potential causal relationships that haven't been captured. Before proceeding, I should assess the current state to determine how to best reveal root causes.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 2 clusters and 8 unassigned alerts.
    
    The current clustering has identified some initial groups, but important temporal sequences aren't captured. Looking at timestamps, the router alerts in Cluster_001 occurred first (14:02-14:04), followed by several unassigned switch and server alerts (14:05-14:12) that appear to be downstream effects from the router issue. Topology information would help confirm these causal relationships.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests that topology analysis would help identify the cascade of failures from the router to dependent devices. This will help reveal how the root cause (likely in Cluster_001) propagated through the network.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 1 cluster and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged Cluster_002 into Cluster_001 based on network dependencies
    - Added 6 previously unassigned alerts to Cluster_001
    - Identified a clear causal chain from router to switches to endpoints
    - 2 alerts remain unassigned as they're from a separate network segment
    
    Thought 4: The topology-based clustering has done an excellent job of revealing the causal chain, showing how the router issue propagated to dependent devices. The merged cluster now tells a clear story of the failure cascade. Let's reassess to determine if any further refinement is needed.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Now have 1 cluster and 2 unassigned alerts.
    
    Cluster_001 now clearly shows a root cause event (router failure) and its cascading effects through the network. The temporal sequence perfectly aligns with the network topology, with failures propagating from the core router to connected switches and then to endpoints. The two remaining unassigned alerts are from a completely separate system with no temporal or topological relationship to the main incident.
    
    Recommended next action: Reorganize[Create a new cluster with alerts 9001 and 9002.]
    
    Thought 5: Based on the assessment, I'll create a new cluster for the two unassigned alerts since they represent a separate, unrelated issue with no causal connection to the main incident.
    Action 5: Reorganize[Create a new cluster with alerts 9001 and 9002.]
    
    Observation 5: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_002 with 2 alerts
    
    Current state: 2 clusters, 0 unassigned alerts.
    
    Thought 6: Now we have two well-formed clusters representing distinct root cause events: Cluster_001 capturing a router failure and its cascading effects, and Cluster_002 containing a separate, unrelated issue. All alerts are assigned, and the clusters provide clear insight into the root causes. Let's do a final assessment.
    Action 6: Reassess
    
    Observation 6: Reassessment completed. Now have 2 clusters, 0 unassigned alerts.
    
    Current clustering is excellent for root cause identification:
    - Cluster_001 clearly shows a cascading failure originating from the router (root cause) and propagating to dependent devices (symptoms)
    - Cluster_002 contains a separate, unrelated issue with no causal connection to the main incident
    - The temporal sequences perfectly align with the network topology, confirming the cause-effect relationships
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 7: The clustering is complete and optimized for root cause identification. Cluster_001 tells the complete story of a router failure and its cascading effects, while Cluster_002 captures a separate, unrelated issue. This will allow network engineers to quickly identify and address the underlying problems.
    Action 7: Finish
    
    Observation 7: Alert aggregation process completed.
    
    Final state: 2 clusters, 0 unassigned alerts.
    
    ### Example 2: Identifying Multiple Concurrent Root Causes
    
    Thought 1: I have a batch of alerts from different parts of the network. To start identifying potential root causes, I'll begin with initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 3 clusters and 7 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains 4 alerts from database servers 
    - Cluster_002 contains 3 alerts from network devices in the east data center
    - Cluster_003 contains 2 alerts from network devices in the west data center
    - 7 alerts remain unassigned, from various devices
    
    Thought 2: The initial exploration has created some basic clusters, but I need to better understand the temporal relationships to identify potential root causes. Let's reassess to determine the best next step.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 3 clusters and 7 unassigned alerts.
    
    Current clustering doesn't fully capture the temporal sequences that might reveal root causes. Looking at timestamps, there appear to be two distinct incident timelines: one starting with storage alerts at 15:02 followed by database alerts at 15:04-15:08 (including those in Cluster_001), and another starting with a core switch alert at 15:30 followed by multiple device alerts at 15:32-15:40 (including some in Clusters 002 and 003). Time-based clustering would help clarify these potential causal chains.
    
    Recommended next action: TimeBasedClustering
    
    Thought 3: The assessment indicates two distinct temporal sequences that could represent separate root causes. Time-based clustering will help clarify these causal chains and better organize the alerts based on when they occurred.
    Action 3: TimeBasedClustering
    
    Observation 3: Time-based clustering completed. Now have 2 clusters and 2 unassigned alerts.
    
    Key insights from time-based clustering:
    - Reorganized into two time-based clusters
    - Cluster_001 now contains the storage-database incident (15:02-15:08)
    - Cluster_002 now contains the network device incidents (15:30-15:40)
    - Clusters 002 and 003 from initial exploration were merged
    - 2 alerts remain unassigned (from different time periods)
    
    Thought 4: The time-based clustering has better organized the alerts around two distinct incidents, which likely represent different root causes. However, to fully understand the cause-effect relationships within each incident, we should examine the network topology.
    Action 4: TopologyBasedClustering
    
    Observation 4: Topology-based clustering completed. Now have 2 clusters and 0 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Maintained the two main clusters representing separate incidents
    - Incorporated the 2 previously unassigned alerts based on network relationships
    - Within each cluster, identified clear causal chains following network dependencies
    - Cluster_001 shows storage failure → database impact → application errors
    - Cluster_002 shows core switch failure → distribution switches → access layer
    
    Thought 5: The topology-based clustering has refined our understanding of the causal chains within each incident. Both clusters now clearly show how issues propagated through dependent systems. Let's reassess to ensure our clustering optimally reveals the root causes.
    Action 5: Reassess
    
    Observation 5: Reassessment completed. Now have 2 clusters and 0 unassigned alerts.
    
    Current clustering effectively reveals two distinct root causes:
    - Cluster_001 shows a storage subsystem failure (at 15:02) as the root cause, with cascading effects to databases and applications
    - Cluster_002 shows a core switch failure (at 15:30) as the root cause, with cascading effects to dependent network devices
    Each cluster tells a clear story of cause and effect, with temporal sequences aligning perfectly with network dependencies. No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 6: The clusters now clearly identify two separate root causes and their cascading effects. This organization will help network engineers quickly identify and address the underlying issues: a storage subsystem failure and a core switch failure. The clustering is complete and optimized for root cause analysis.
    Action 6: Finish
    
    Observation 6: Alert aggregation process completed.
    
    Final state: 2 clusters, 0 unassigned alerts.
    
    ### Example 3: Distinguishing Related Symptoms from Separate Root Causes
    
    Thought 1: I have a set of alerts from various network and application components. To start identifying potential root causes, I'll perform initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 5 clusters and 4 unassigned alerts.
    
    Key insights from initial clustering:
    - Multiple small clusters based primarily on device types
    - Clusters 001-003 contain network device alerts from the same time period
    - Clusters 004-005 contain application server alerts
    - 4 alerts remain unassigned, including some security-related alerts
    
    Thought 2: The initial clustering has created several small clusters, but they may not be organized optimally for root cause identification. Some might be related symptoms rather than separate root causes. Let's reassess to determine how to better organize them.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 5 clusters and 4 unassigned alerts.
    
    Current clustering appears to be fragmenting what might be related issues. Looking at the timestamps, Clusters 001, 002, and 003 all contain alerts from an overlapping 10-minute period (09:15-09:25). Furthermore, the topology data suggests these devices are interconnected. These may be symptoms of a single root cause rather than separate incidents. Topology-based clustering would help clarify these relationships.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests that some clusters might represent related symptoms rather than separate root causes. Topology-based clustering will help identify network dependencies and better organize alerts based on cause-effect relationships.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 3 clusters and 2 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged Clusters 001, 002, and 003 into a single cluster (now Cluster_001) based on network dependencies
    - Identified a clear propagation path from core router (original Cluster_001) to distribution switches (original Cluster_002) to access switches (original Cluster_003)
    - Cluster_002 (formerly 004) and Cluster_003 (formerly 005) remain separate as they represent application issues with no clear network connection to the first incident
    - 2 security alerts remain unassigned
    
    Thought 4: The topology-based clustering has significantly improved our understanding of the network issue by showing how it propagated through the infrastructure. We now have a clearer picture of potential root causes. Let's reassess to determine if further refinement is needed.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Now have 3 clusters and 2 unassigned alerts.
    
    Current clustering is improved but could be further refined for root cause identification:
    - Cluster_001 now clearly shows a network issue cascading from core to edge
    - Clusters 002 and 003 contain application alerts, but examining their timestamps reveals they occurred 5-15 minutes after the network issues in Cluster_001
    - The topology doesn't show direct connections, but the temporal sequence suggests these application issues might be downstream effects from the network problem
    
    Recommended next action: TimeBasedClustering
    
    Thought 5: The assessment suggests that the application issues might be downstream effects of the network problem, based on the timing. Time-based clustering will help clarify these temporal relationships and potentially identify cause-effect patterns across different systems.
    Action 5: TimeBasedClustering
    
    Observation 5: Time-based clustering completed. Now have 2 clusters and 2 unassigned alerts.
    
    Key insights from time-based clustering:
    - Merged Cluster_002 into Cluster_001 based on temporal sequence
    - Identified that application alerts in former Cluster_002 occurred 5-10 minutes after the core network alerts
    - Kept Cluster_003 (now Cluster_002) separate as its timing doesn't align with the main incident
    - 2 security alerts remain unassigned, with timestamps outside both incident windows
    
    Thought 6: The time-based clustering has further improved our understanding by revealing that some application issues were likely caused by the network problem, despite no direct network connections in the topology data. Let's reassess to determine our next step.
    Action 6: Reassess
    
    Observation 6: Reassessment completed. Now have 2 clusters and 2 unassigned alerts.
    
    Current clustering effectively reveals root causes and their effects:
    - Cluster_001 now shows a complete picture of a network failure and its impacts, including some application effects
    - Cluster_002 represents a separate application issue unrelated to the network problem
    - The 2 unassigned security alerts have similar timestamps (10:45-10:50) and appear related to each other, but are completely separate from both main incidents
    
    Recommended next action: Reorganize[Create a new cluster with alerts 8001 and 8002.]
    
    Thought 7: Based on the assessment, I'll create a new cluster for the security alerts since they represent a separate issue with a distinct timeframe.
    Action 7: Reorganize[Create a new cluster with alerts 8001 and 8002.]
    
    Observation 7: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_003 with 2 alerts
    
    Current state: 3 clusters, 0 unassigned alerts.
    
    Thought 8: Now we have three well-formed clusters, each representing a distinct root cause: Cluster_001 capturing a network failure and its cascading effects including application impacts, Cluster_002 containing a separate application issue, and Cluster_003 representing security-related issues. Let's do a final assessment.
    Action 8: Reassess
    
    Observation 8: Reassessment completed. Now have 3 clusters, 0 unassigned alerts.
    
    Current clustering is excellent for root cause identification:
    - Cluster_001 clearly shows a network failure originating at the core (root cause at 09:15) and propagating to both network and application components (symptoms from 09:18-09:30)
    - Cluster_002 represents a separate application issue with a different root cause
    - Cluster_003 contains security alerts representing a third distinct incident
    - The temporal and topological relationships within each cluster confirm the cause-effect patterns
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 9: The clustering is complete and optimized for root cause identification. Each cluster represents a distinct incident with a clear root cause and associated symptoms. This organization will allow network engineers to quickly identify and address three separate underlying problems.
    Action 9: Finish
    
    Observation 9: Alert aggregation process completed.
    
    Final state: 3 clusters, 0 unassigned alerts.
    
    ### Example 4: Identifying Subtle Causal Relationships
    
    Thought 1: I have a set of alerts from a diverse environment with different systems and locations. To begin identifying potential root causes, I'll start with initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 2 clusters and 12 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains database server alerts from location A
    - Cluster_002 contains web server alerts from location B
    - 12 alerts remain unassigned, from various systems and locations
    
    Thought 2: The initial exploration created some basic clusters, but many alerts remain unassigned. To better understand the causal relationships, I should reassess the current state.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have A clusters and 12 unassigned alerts.
    
    Current clustering doesn't capture the full picture of root causes. Looking at timestamps across all alerts, there appears to be a sequence starting with network alerts at 07:02-07:05 (currently unassigned), followed by database alerts at 07:08-07:15 (Cluster_001), and finally web server alerts at 07:20-07:30 (Cluster_002 plus some unassigned). Despite being in different locations, the timing suggests a potential causality chain that should be investigated with topology information.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment suggests a potential causal chain across different systems and locations. Topology-based clustering will help identify if there are network dependencies that explain this temporal sequence.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 3 clusters and 5 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Created a new Cluster_003 containing the early network alerts
    - Maintained Clusters 001 and 002 as separate
    - Identified that some network components in location A (Cluster_003) are connected to the database servers (Cluster_001)
    - Found no direct connections between locations A and B
    - Assigned some previously unassigned alerts based on device relationships
    - 5 alerts remain unassigned with no clear topology relationships
    
    Thought 4: The topology-based clustering has identified some network relationships but hasn't fully explained the temporal sequence across locations. Let's examine the time patterns in more detail.
    Action 4: TimeBasedClustering
    
    Observation 4: Time-based clustering completed. Now have 2 clusters and 3 unassigned alerts.
    
    Key insights from time-based clustering:
    - Merged Clusters 001 and 003 based on clear temporal sequence and topology connections
    - Cluster_001 now shows the full progression: network issues → database impact
    - Kept Cluster_002 (web servers) separate as the topology doesn't show a direct connection
    - Incorporated 2 previously unassigned alerts from location A into Cluster_001
    - 3 alerts remain unassigned, all from a third location C
    
    Thought 5: The time-based clustering has improved our understanding of the cause-effect relationship within location A, showing how network issues led to database problems. However, the potential relationship with location B's web servers hasn't been explained by either time or topology alone. Let's reassess.
    Action 5: Reassess
    
    Observation 5: Reassessment completed. Now have 2 clusters and 3 unassigned alerts.
    
    Current clustering has identified one clear root cause in location A (network issue leading to database problems). After closer examination of alert details, we can see the web server alerts in location B (Cluster_002) are reporting database connectivity errors to the same databases in location A. While there's no direct network link in the topology, there's a functional dependency: the web servers depend on the databases. This explains the temporal sequence: network issues → database problems → web server errors.
    
    Recommended next action: Reorganize[Merge clusters 001 and 002.]
    
    Thought 6: Based on the assessment, I'll merge Clusters 001 and 002 since the web server issues are downstream effects of the database problems, which were themselves caused by network issues. Despite no direct network connection, the functional dependency and clear temporal sequence indicate a single causal chain.
    Action 6: Reorganize[Merge clusters 001 and 002.]
    
    Observation 6: Reorganization completed.
    
    Operations performed:
    - Merged clusters cluster_001 and cluster_002
    
    Current state: 1 cluster, 3 unassigned alerts.
    
    Thought 7: Now we have a single cluster representing the complete cause-effect chain across locations, from the original network issue to the database problems to the web server errors. The 3 unassigned alerts from location C still need to be addressed. Let's reassess.
    Action 7: Reassess
    
    Observation 7: Reassessment completed. Now have 1 cluster and 3 unassigned alerts.
    
    Current clustering effectively captures the main incident spanning locations A and B, showing the complete causal chain from the network root cause through to the application impacts. The 3 unassigned alerts from location C occurred at a completely different time (14:30-14:45) and show no relationship to the main incident. They appear to be a separate issue involving a storage system in location C.
    
    Recommended next action: Reorganize[Create a new cluster with alerts 9001, 9002, and 9003.]
    
    Thought 8: I'll create a new cluster for the location C alerts since they represent a completely separate issue with no causal connection to the main incident.
    Action 8: Reorganize[Create a new cluster with alerts 9001, 9002, and 9003.]
    
    Observation 8: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_002 with 3 alerts
    
    Current state: 2 clusters, 0 unassigned alerts.
    
    Thought 9: We now have two well-formed clusters, each representing a distinct root cause: Cluster_001 capturing the cross-location incident from network to database to web applications, and Cluster_002 containing the separate storage issue in location C. Let's do a final assessment.
    Action 9: Reassess
    
    Observation 9: Reassessment completed. Now have 2 clusters, 0 unassigned alerts.
    
    Current clustering is excellent for root cause identification:
    - Cluster_001 reveals a complex but single root cause (network failure in location A) with cascading effects across systems and locations
    - Cluster_002 represents a completely separate storage issue in location C
    - The subtle dependency between web servers and databases was correctly identified despite no direct network connection in the topology
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 10: The clustering is complete and optimized for root cause identification. We've identified a complex causal chain spanning multiple locations and systems, revealing how a network issue propagated through functional dependencies to impact web services. The second cluster correctly isolates an unrelated issue. This organization will help engineers quickly understand and address the underlying problems.
    Action 10: Finish
    
    Observation 10: Alert aggregation process completed.
    
    Final state: 2 clusters, 0 unassigned alerts.
    
    ### Example 5: Handling Concurrent but Independent Root Causes
    
    Thought 1: I have alerts from a large enterprise network with multiple data centers. To start identifying root causes, I'll perform initial exploration.
    Action 1: InitialExploration
    
    Observation 1: Initial exploration completed. Found 4 clusters and 10 unassigned alerts.
    
    Key insights from initial clustering:
    - Cluster_001 contains router alerts from data center A
    - Cluster_002 contains switch alerts from data center A
    - Cluster_003 contains database alerts from data center B
    - Cluster_004 contains application server alerts from data center B
    - 10 alerts remain unassigned, from various systems across both data centers
    
    Thought 2: The initial exploration has created several clusters based on device types and locations, but they may not be optimally organized around root causes. Let's reassess to determine how to better identify cause-effect relationships.
    Action 2: Reassess
    
    Observation 2: Reassessment completed. Now have 4 clusters and 10 unassigned alerts.
    
    Current clustering needs refinement to better reveal root causes. Looking at timestamps and locations:
    - Clusters 001 and 002 in data center A: Router alerts (06:02-06:05) preceded switch alerts (06:07-06:12)
    - Clusters 003 and 004 in data center B: Database alerts (08:45-08:50) preceded application alerts (08:52-09:00)
    - The unassigned alerts include some from both time periods and locations
    This suggests two separate incidents with their own causal chains. Topology-based clustering would help confirm these relationships.
    
    Recommended next action: TopologyBasedClustering
    
    Thought 3: The assessment indicates two separate incidents in different data centers with their own temporal sequences. Topology-based clustering will help clarify the network dependencies within each data center and better organize alerts around their respective root causes.
    Action 3: TopologyBasedClustering
    
    Observation 3: Topology-based clustering completed. Now have 2 clusters and 3 unassigned alerts.
    
    Key insights from topology-based clustering:
    - Merged Clusters 001 and 002 into a single cluster (now Cluster_001) based on network dependencies in data center A
    - Merged Clusters 003 and 004 into a single cluster (now Cluster_002) based on dependencies in data center B
    - Added most unassigned alerts to their respective clusters based on location and network relationships
    - Identified clear propagation paths within each data center
    - 3 alerts remain unassigned from a third location (data center C)
    
    Thought 4: The topology-based clustering has significantly improved our understanding by creating two distinct clusters, each representing a separate incident with its own root cause and propagation path. Let's reassess to determine our next steps.
    Action 4: Reassess
    
    Observation 4: Reassessment completed. Now have 2 clusters and 3 unassigned alerts.
    
    Current clustering effectively captures two distinct root causes:
    - Cluster_001 shows a clear causal chain in data center A: router failure → switch issues → endpoint impacts
    - Cluster_002 shows a clear causal chain in data center B: database failure → application errors → user-facing impacts
    - The 3 unassigned alerts are from data center C (11:30-11:35) and appear to be a third separate incident involving a storage system failure
    
    Recommended next action: Reorganize[Create a new cluster with alerts 7001, 7002, and 7003.]
    
    Thought 5: Based on the assessment, I'll create a new cluster for the data center C alerts since they represent a third, unrelated incident with its own root cause.
    Action 5: Reorganize[Create a new cluster with alerts 7001, 7002, and 7003.]
    
    Observation 5: Reorganization completed.
    
    Operations performed:
    - Created new cluster cluster_003 with 3 alerts
    
    Current state: 3 clusters, 0 unassigned alerts.
    
    Thought 6: We now have three well-formed clusters, each representing a distinct root cause in a different data center. Let's perform a final assessment to ensure our clustering optimally reveals these root causes.
    Action 6: Reassess
    
    Observation 6: Reassessment completed. Now have 3 clusters, 0 unassigned alerts.
    
    Current clustering is excellent for root cause identification:
    - Cluster_001 clearly identifies a router failure in data center A as the root cause of a cascading network issue
    - Cluster_002 clearly identifies a database failure in data center B as the root cause of application problems
    - Cluster_003 identifies a storage system failure in data center C
    - Each cluster represents a completely independent incident with its own root cause and effects
    - The temporal sequences within each cluster confirm the cause-effect relationships
    No further adjustments needed.
    
    Recommended next action: Finish
    
    Thought 7: The clustering is complete and optimized for root cause identification. We've identified three separate incidents, each with its own clear root cause and progression of effects. This organization will allow network engineers to efficiently investigate and resolve each underlying issue independently.
    Action 7: Finish
    
    Observation 7: Alert aggregation process completed.
    
    Final state: 3 clusters, 0 unassigned alerts.
    """