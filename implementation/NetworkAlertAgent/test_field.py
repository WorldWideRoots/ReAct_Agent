import json
from typing import Dict, List, Any

# Import our classes
from NetworkAlertEnvironment import NetworkAlertEnvironment
from NetworkAlertAgent import NetworkAlertAgent
from system_prompt import get_network_alert_system_prompt

def run_alert_aggregation_example():
    """
    Example of running the network alert aggregation system.
    """
    # Sample alerts data
    sample_alerts = [
        {
            "source_id": "uselk11s1-lla-000",
            "alert_id": 845204837,
            "type": "network",
            "class": "performance",
            "object_class": "switch",
            "severity": "high",
            "description": "Switch overload detected",
            "first_event_time": 1741041666,
            "last_event_time": 1741045666,
            "last_state_change": 1741045666,
            "site": "uselk",
            "device_type": "switch"
        },
        {
            "source_id": "uselk11s1-lla-001",
            "alert_id": 845204838,
            "type": "network",
            "class": "performance",
            "object_class": "switch",
            "severity": "medium",
            "description": "Performance degradation",
            "first_event_time": 1741041766,
            "last_event_time": 1741045766,
            "last_state_change": 1741045766,
            "site": "uselk",
            "device_type": "switch"
        },
        {
            "source_id": "isikas1-sec",
            "alert_id": 845204839,
            "type": "security",
            "class": "threat",
            "object_class": "firewall",
            "severity": "high",
            "description": "Intrusion detected",
            "first_event_time": 1741041866,
            "last_event_time": 1741045866,
            "last_state_change": 1741045866,
            "site": "isikas",
            "device_type": "firewall"
        },
        {
            "source_id": "lue1vp11824",
            "alert_id": 845204840,
            "type": "system",
            "class": "resource",
            "object_class": "vm",
            "severity": "low",
            "description": "CPU usage high",
            "first_event_time": 1741042766,
            "last_event_time": 1741046766,
            "last_state_change": 1741046766,
            "site": "cloud",
            "device_type": "vm"
        }
    ]
    
    # Sample topology data
    sample_topology = {
        "uselk11s1-lla-000": {
            "L2_Topo_Type": ["uselk11s1-lla-001"],
            "L3_Topo_Type": []
        },
        "uselk11s1-lla-001": {
            "L2_Topo_Type": ["uselk11s1-lla-000"],
            "L3_Topo_Type": ["isikas1-sec"]
        },
        "isikas1-sec": {
            "L2_Topo_Type": [],
            "L3_Topo_Type": ["uselk11s1-lla-001"]
        },
        "lue1vp11824": {
            "L2_Topo_Type": [],
            "L3_Topo_Type": []
        }
    }
    
    # Create the environment
    env = NetworkAlertEnvironment(alerts=sample_alerts, topology_info=sample_topology)
    
    # Create the agent
    agent = NetworkAlertAgent(env=env)
    
    # Set valid action prefixes
    agent.set_valid_prefixes([
        "InitialExploration[",
        "TimeBasedClustering[",
        "TopologyBasedClustering[",
        "Reassess[",
        "DirectReorganize[",
        "Finish["
    ])
    
    # Get the system prompt
    system_prompt = get_network_alert_system_prompt()
    
    # Run the agent with a recommended sequence of actions
    print("Running alert aggregation with intelligent action selection...\n")
    reward, info = agent.react(
        initial_prompt=system_prompt,
        max_num_steps=8,  # Allow for more steps to include assessment phases
        to_print=True
    )
    
    # Print the final clusters
    print("\nFinal Clusters:")
    print(json.dumps(info["clusters"], indent=2))
    
    # Example of a manual step-by-step approach (alternative to using ReAct)
    def manual_aggregation_example():
        """Demonstrate a manual step-by-step approach to alert aggregation"""
        print("\nDemonstrating manual step-by-step approach...")
        
        # Reset the environment
        env.reset(alerts=sample_alerts, topology_info=sample_topology)
        
        # Step 1: Initial Exploration
        print("\nStep 1: Initial Exploration")
        obs, reward, done, info = env.step("InitialExploration[]")
        print(f"Observation: {obs}")
        
        # Step 2: Time-Based Clustering
        print("\nStep 2: Time-Based Clustering")
        obs, reward, done, info = env.step("TimeBasedClustering[]")
        print(f"Observation: {obs}")
        
        # Step 3: Assessment
        print("\nStep 3: Assessing Clusters")
        obs, reward, done, info = env.step("Reassess[]")
        print(f"Observation: {obs}")
        
        # Step 4: Follow recommendation (assuming it's Topology-Based Clustering)
        print("\nStep 4: Follow Recommendation (Topology-Based Clustering)")
        obs, reward, done, info = env.step("TopologyBasedClustering[]")
        print(f"Observation: {obs}")
        
        # Step 5: Final Assessment
        print("\nStep 5: Final Assessment")
        obs, reward, done, info = env.step("Reassess[]")
        print(f"Observation: {obs}")
        
        # Step 6: Finish
        print("\nStep 6: Finish")
        obs, reward, done, info = env.step("Finish[Alert aggregation complete]")
        print(f"Observation: {obs}")
        
        return info["clusters"]
    
    # Optionally run the manual example
    # manual_clusters = manual_aggregation_example()
    
    return info["clusters"]

if __name__ == "__main__":
    run_alert_aggregation_example()







import json
import re  # Make sure re is imported at the top level

def assess_llm(self, temperature=0.01):
    """
    Evaluate the current state of alert clusters and provide recommendations for next steps.
    Uses LLM to assess clusters with a focus on root cause identification through temporal
    and topological relationships.
    """
    # Get the function-specific history
    history = self.function_histories.get("assess", [])
    
    # Validate current_clusters
    if not isinstance(self.current_clusters, dict):
        raise TypeError("current_clusters must be a dictionary")
        
    # Check for required keys
    if 'clusters' not in self.current_clusters or 'unassigned_alerts' not in self.current_clusters:
        raise KeyError("current_clusters must contain 'clusters' and 'unassigned_alerts' keys")
        
    # Prepare data for the LLM
    try:
        # Serialize clusters and unassigned alerts
        clusters_data = json.dumps({'clusters': self.current_clusters['clusters']}, indent=1)
        unassigned_alerts_data = json.dumps({'unassigned_alerts': self.current_clusters['unassigned_alerts']}, indent=1)
        current_alerts_batch_str = json.dumps(self.current_alerts_batch)
        topology_info_str = json.dumps(self.topology_info, separators=(',', ': '), indent=1)
        
        # Get summarized stats to help with analysis
        num_clusters = len(self.current_clusters['clusters'])
        num_unassigned = len(self.current_clusters['unassigned_alerts'])
        total_alerts = sum(len(cluster.get('alert_ids', [])) for cluster in self.current_clusters['clusters']) + num_unassigned
        
        # Calculate average confidence if available
        total_confidence = sum(float(cluster.get('confidence', 0)) for cluster in self.current_clusters['clusters'] if 'confidence' in cluster)
        avg_confidence = total_confidence / num_clusters if num_clusters > 0 else 0
        
        # Verify serialization
        if not all(isinstance(x, str) for x in [clusters_data, unassigned_alerts_data, current_alerts_batch_str, topology_info_str]):
            raise TypeError('The serialized data is not a string')
    except Exception as e:
        print(f'Error while serializing data: {e}')
        return None, history
        
    # Get previous clustering summaries for context
    clustering_context = self._get_clustering_summaries()
    
    # Create system instructions with enhanced guidance and few-shot examples
    system_instructions = f"""
    You are an advanced network alert assessment expert with the primary goal of identifying ROOT CAUSES of network events.
    
    # Current Alert Statistics:
    - Total Alerts: {total_alerts}
    - Number of Clusters: {num_clusters}
    - Unassigned Alerts: {num_unassigned}
    - Average Confidence: {avg_confidence:.2f}
    
    # Previous Clustering Steps:
    {clustering_context}
    
    # ROOT CAUSE IDENTIFICATION PRINCIPLES:
    
    1. **Temporal Causality Is Primary Evidence:**
       - First alerts in a sequence often indicate root causes
       - Alerts occurring within 15 minutes of each other may be causally related
       - Sequential patterns reveal propagation paths: root cause → symptoms
       - Always ask: "What happened FIRST?" to identify potential root causes
    
    2. **Topological Relationships Reveal Propagation Paths:**
       - Network dependencies create predictable failure patterns
       - Issues propagate FROM root cause devices TO dependent devices
       - Connected devices in the topology often share cause-effect relationships
       - Network architecture helps distinguish primary failures from secondary effects
    
    3. **Alert Content Is Secondary Evidence:**
       - Similar descriptions WITHOUT temporal/topological links often represent SEPARATE issues
       - NEVER group alerts solely based on similar descriptions or types
       - Only consider descriptions AFTER establishing temporal/topological relationships
    
    # TOPOLOGY ANALYSIS GUIDELINES:
    
    When evaluating topological relationships:
    
    1. **Direct Connections Matter Most:**
       - Devices directly connected in the topology are strong candidates for the same cluster
       - Root cause devices often have multiple dependent devices showing alerts
    
    2. **Dependency Direction Is Critical:**
       - Failures typically propagate FROM upstream TO downstream devices
       - Earlier alerts in upstream devices often indicate root causes
       - Later alerts in downstream devices often indicate symptoms
    
    3. **Common Pattern Recognition:**
       - Network device failures → connected device failures → application errors
       - Database failures → application errors → client-side alerts
       - Authentication system failures → widespread login errors
       - Storage failures → database errors → application timeouts
    
    4. **Cross-System Dependencies:**
       - Some dependencies aren't in network topology but are functional:
         - Web servers depend on databases even if connected through multiple network hops
         - Client applications depend on authentication services
         - Virtualized services depend on underlying hardware
    
    # REASSESSMENT CLUSTERING PRINCIPLES:
    
    When evaluating current clusters, apply these principles (similar to initial exploration):
    
    1. **Time-Based Grouping:**
       - Events within 15-minute windows should be examined for causal relationships
       - First alerts in a time window are potential root causes
       - Cascade patterns (failures spreading over time) indicate related events
    
    2. **Topology-Based Grouping:**
       - Connected devices in the topology likely share causal relationships
       - Network dependencies create predictable failure patterns
       - Upstream failures cause downstream symptoms
    
    3. **Alert Association Logic:**
       - Alerts should be grouped if they:
         a) Share temporal proximity (within 15 minutes) AND/OR
         b) Have topological relationships (connected/dependent devices) AND/OR
         c) Show a clear cascading pattern (device A fails → device B fails → application C errors)
       - Alerts should NOT be grouped solely based on similar descriptions or types
    
    # ASSESSMENT SEQUENCE:
    Focus your assessment in this exact order:
    
    1. **Alert-Cluster Fit Analysis:** 
       - Are there any alerts in current clusters that do NOT belong there?
       - For each cluster, identify any alerts that don't share temporal or topological relationships with the potential root cause
       - Recommend moving these alerts if they would better fit another cluster or should be unassigned
    
    2. **Cluster Merger Analysis:**
       - Are there multiple clusters that likely represent the SAME root cause event?
       - Look for clusters with overlapping time windows and connected devices in the topology
       - Recommend merging clusters that represent the same causal chain
    
    3. **Unassigned Alert Analysis:**
       - Do any unassigned alerts belong to existing clusters?
       - Look for temporal sequences and topological connections between unassigned alerts and cluster events
       - Recommend moving unassigned alerts into appropriate clusters if clear relationships exist
    
    ALL assessments must be based on TEMPORAL and TOPOLOGICAL relationships, with the primary goal of identifying root causes.
    
    # RECOMMENDATION GUIDELINES:
    
    Based on your assessment, recommend either:
    
    1. **TimeBasedClustering:** When temporal patterns aren't fully captured
       
    2. **TopologyBasedClustering:** When network dependencies aren't fully reflected
    
    3. **Reorganize:** When specific changes would better reveal root causes
       - Unlike other recommendations, Reorganize can include MULTIPLE specific operations
       - List each operation in clear, actionable language with IDs and reasoning
       - Format as a numbered list of specific operations, for example:
       
       Reorganize[
       1. Move alerts 1001, 1002 from unassigned to cluster_003 (these alerts occurred 5 minutes after router failure in cluster_003 and are from connected switches)
       2. Merge clusters 001 and 004 (cluster_001 contains router failures and cluster_004 contains downstream effects from the same root cause)
       3. Create a new cluster with alerts 2001, 2002, 2003 (these form a distinct authentication failure pattern separate from existing clusters)
       ]
    
    4. **Finish:** When all clusters effectively represent distinct root causes
    
    # ASSESSMENT EXAMPLES:
    
    ## Example 1: Alert-Cluster Fit Analysis Leading to Reorganization
    
    ### Input:
    - 2 clusters and 5 unassigned alerts
    - Cluster_001: Contains router alerts from 14:05-14:10
    - Cluster_002: Contains mixed device alerts from 14:08-14:30
    
    ### Assessment:
    
    #### Alert-Cluster Fit Analysis:
    Examining Cluster_001: All alerts are from router devices with timestamps 14:05-14:10. These share both temporal and device-type relationships. All alerts appear to belong.
    
    Examining Cluster_002: Contains alerts from 14:08-14:30, but includes three distinct device types:
    - Alerts 2001-2003: Database servers (14:08-14:10)
    - Alerts 2004-2005: Application servers (14:15-14:20)
    - Alerts 2006-2007: Network switches (14:25-14:30)
    
    The database alerts (2001-2003) have no temporal or topological relationship with the other alerts in Cluster_002. They occurred first and are from unconnected systems. These likely represent a separate root cause.
    
    #### Cluster Merger Analysis:
    No clusters appear to represent the same root cause event. Cluster_001 and Cluster_002 involve different systems with different temporal patterns.
    
    #### Unassigned Alert Analysis:
    Unassigned alerts 3001-3003 are from network switches with timestamps 14:12-14:15. Examining the topology, these switches are directly connected to the routers in Cluster_001, and the timing (7 minutes after the router alerts) suggests these are downstream effects from the router issue.
    
    ### Recommendation:
    
    Reorganize[
    1. Move database alerts 2001, 2002, 2003 from cluster_002 to a new cluster (these occurred at 14:08-14:10 and show no relationship to other alerts in cluster_002, indicating a separate root cause)
    2. Move switch alerts 3001, 3002, 3003 from unassigned to cluster_001 (these occurred 7 minutes after the router alerts in cluster_001 and are from directly connected devices, indicating downstream effects)
    ]
    
    ## Example 2: Time-Based Clustering Recommendation
    
    ### Assessment:
    
    Current clustering is primarily based on device types rather than causal relationships:
    - Cluster_001: Router devices only (timestamps 08:15-15:45)
    - Cluster_002: Switch devices only (timestamps 08:20-15:50) 
    
    This organization fails to capture temporal sequences that might reveal cause-effect relationships. The wide time spans in each cluster suggest they contain alerts from multiple unrelated incidents.
    
    Cannot effectively assess merger candidates when time-based relationships aren't captured. The current clustering by device type masks potential causal relationships across device types.
    
    ### Recommendation:
    
    TimeBasedClustering
    
    ## Example 3: Finish Recommendation
    
    ### Assessment:
    
    All clusters show excellent organization around root causes and their effects:
    - Cluster_001: Network failure starting at core router (07:05) with cascading effects to connected switches (07:08-07:12) and endpoints (07:15-07:20)
    - Cluster_002: Database failure (10:15) with subsequent application errors (10:18-10:25)
    
    Each cluster has alerts that share clear temporal and topological relationships. No alerts appear to be misplaced. All clusters represent distinct incidents with separate root causes and different affected systems. No clusters should be merged. No unassigned alerts remain.
    
    ### Recommendation:
    
    Finish
    """
    
    # Create user message
    user_message = f"""
    Please assess the current state of alert clusters with a focus on identifying root causes through temporal and topological relationships.
    
    # CURRENT ALERT BATCH:
    {current_alerts_batch_str}
    
    # CURRENT CLUSTERS:
    {clusters_data}
    
    # UNASSIGNED ALERTS:
    {unassigned_alerts_data}
    
    # TOPOLOGY INFORMATION:
    {topology_info_str}
    
    Please provide:
    1. A detailed assessment focusing on temporal sequences and network dependencies
    2. Analysis of whether current clusters reflect probable root causes and their effects
    3. A specific recommendation for the next action that will best reveal true root causes
    
    Structure your response as follows:
    
    ## Alert-Cluster Fit Analysis
    [Your detailed analysis of whether alerts in current clusters belong there]
    
    ## Cluster Merger Analysis
    [Your evaluation of whether any clusters should be merged]
    
    ## Unassigned Alert Analysis
    [Your analysis of whether any unassigned alerts should be moved to existing clusters]
    
    ## Recommendation
    [Your ONE specific next action recommendation with detailed reasoning]
    """
    
    # Prepare messages for LLM
    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_message}
    ]
    
    # Validate messages
    for msg in messages:
        if not isinstance(msg["content"], str):
            raise ValueError(f"Message content is not a string: {msg['content']}")
            
    # Add messages to function-specific history
    history += messages
    self.function_histories["assess"] = history
    
    # Call the LLM
    reply = self._llm(history, temperature=temperature, model=self.llm_model)
    
    # Validate response
    if 'choices' in reply and len(reply['choices']) > 0:
        response_content = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": response_content})
        self.function_histories["assess"] = history
        
        # Store response in recent reasoning
        self.recent_reasoning["assess"] = response_content
        
        # Create a summary for the ReAct framework
        summary = f"Assessment:\n- Evaluated {num_clusters} clusters and {num_unassigned} unassigned alerts\n"
        
        # Extract recommendation
        recommendation = self._extract_recommendation(response_content)
        summary += f"- Recommended: {recommendation}\n"
        
        # Add to ReAct history
        self.react_history.append({
            "action": "Reassess",
            "summary": summary
        })
        
        return reply, history
        
    else:
        print("Invalid response from LLM")
        return None, history


def reorganize(self, instructions):
    """
    Implement reorganization based on natural language instructions.
    Support for multiple operations in a single instruction string.
    
    Args:
        instructions: Natural language instructions for reorganization
        
    Returns:
        list: Description of changes made
    """
    try:
        import re
        operations_performed = []
        
        print(f"DEBUG: Processing reorganize instructions: {instructions}")
        
        # Check if instructions contain numbered operations (e.g., "1. Move alerts...")
        numbered_operations = re.findall(r'(?:\d+\.\s*)([^\d]+?)(?=\d+\.|$)', instructions)
        
        if numbered_operations:
            print(f"DEBUG: Found {len(numbered_operations)} numbered operations")
            # Process each operation separately
            for op in numbered_operations:
                op = op.strip()
                if op:
                    print(f"DEBUG: Processing operation: {op}")
                    # Recursively call reorganize for each operation
                    sub_results = self.reorganize(op)
                    operations_performed.extend(sub_results)
            
            return operations_performed
        
        # If not numbered, process as a single operation
        
        # Look for cluster creation operations
        if "create" in instructions.lower() and "cluster" in instructions.lower():
            # Extract potential cluster ID
            cluster_id_match = re.search(r'cluster[_\s]*(\d+)', instructions)
            
            if cluster_id_match:
                # If a specific ID is mentioned, use it
                cluster_num = int(cluster_id_match.group(1))
                cluster_id = f"cluster_{cluster_num:03d}"
            else:
                # Otherwise create a new cluster with the next available ID
                cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
            
            # Extract alert IDs to include in the new cluster
            alert_ids = []
            # Look for large numbers that might be alert IDs (usually 6+ digits)
            potential_alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', instructions)]
            
            # Create the new cluster
            cluster_data = {
                "cluster_id": cluster_id,
                "chains of thoughts": "Manually created cluster",
                "source_ids": "",
                "alert_ids": potential_alert_ids,
                "severity": "medium",
                "confidence": 0.5,
                "time": {"start": 0, "end": 0},
                "Description": "Manually created cluster"
            }
            
            # Add the cluster to the current clusters
            self.current_clusters["clusters"].append(cluster_data)
            
            # Remove the alerts from unassigned if they're there
            for alert_id in potential_alert_ids:
                if alert_id in self.current_clusters["unassigned_alerts"]:
                    self.current_clusters["unassigned_alerts"].remove(alert_id)
            
            operations_performed.append(f"Created cluster {cluster_id} with {len(potential_alert_ids)} alerts")
        
        # Look for move operations
        elif "move" in instructions.lower() and "alert" in instructions.lower() and "to" in instructions.lower():
            # Extract alert IDs - look for 6+ digit numbers (typical for alert IDs)
            alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', instructions)]
            print(f"DEBUG: Found alert IDs to move: {alert_ids}")
            
            # Determine source and destination
            if "unassigned" in instructions.lower() and "cluster" in instructions.lower():
                # Find the cluster ID
                cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
                if cluster_matches:
                    cluster_num = int(cluster_matches[0])
                    cluster_id = f"cluster_{cluster_num:03d}"
                    print(f"DEBUG: Found cluster ID: {cluster_id}")
                    
                    # Determine direction (from unassigned to cluster or from cluster to unassigned)
                    if instructions.lower().find("unassigned") < instructions.lower().find("cluster"):
                        print(f"DEBUG: Detected move FROM unassigned TO cluster {cluster_id}")
                        # Moving from unassigned to cluster
                        self._move_from_unassigned_to_cluster(alert_ids, cluster_id)
                        operations_performed.append(f"Moved {len(alert_ids)} alerts from unassigned to {cluster_id}")
                    else:
                        print(f"DEBUG: Detected move FROM cluster {cluster_id} TO unassigned")
                        # Moving from cluster to unassigned
                        self._move_from_cluster_to_unassigned(alert_ids, cluster_id)
                        operations_performed.append(f"Moved {len(alert_ids)} alerts from {cluster_id} to unassigned")
            elif "cluster" in instructions.lower() and instructions.lower().count("cluster") >= 2:
                # Moving between clusters
                # Find source and destination cluster IDs
                cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
                if len(cluster_matches) >= 2:
                    src_cluster_id = f"cluster_{int(cluster_matches[0]):03d}"
                    dst_cluster_id = f"cluster_{int(cluster_matches[1]):03d}"
                    
                    self._move_between_clusters(alert_ids, src_cluster_id, dst_cluster_id)
                    operations_performed.append(f"Moved {len(alert_ids)} alerts from {src_cluster_id} to {dst_cluster_id}")
        
        # Look for merge operations
        elif "merge" in instructions.lower() and "cluster" in instructions.lower():
            # Find all cluster IDs mentioned
            cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
            print(f"DEBUG: Found clusters to merge: {cluster_matches}")
            
            if len(cluster_matches) >= 2:
                # Get the first two distinct cluster IDs
                cluster_ids = []
                for match in cluster_matches:
                    cluster_id = f"cluster_{int(match):03d}"
                    if cluster_id not in cluster_ids:
                        cluster_ids.append(cluster_id)
                    if len(cluster_ids) == 2:
                        break
                
                print(f"DEBUG: Merging clusters: {cluster_ids}")
                
                self._merge_clusters(cluster_ids)
                operations_performed.append(f"Merged {cluster_ids[1]} into {cluster_ids[0]}")
        
        # If nothing happened, report it
        if not operations_performed:
            operations_performed.append("No operations were identified from the instructions")
        
        return operations_performed
        
    except Exception as e:
        error_message = f"Error in reorganize function: {str(e)}"
        print(f"DEBUG: {error_message}")
        import traceback
        traceback.print_exc()
        return [error_message]
    



    # --------------------
def reorganize(self, instructions, verbose=False):
    """
    Implement reorganization based on natural language instructions.
    Support for multiple operations in a single instruction string.
    
    Args:
        instructions: Natural language instructions for reorganization
        verbose: Whether to print detailed debug information
        
    Returns:
        list: Description of changes made
    """
    try:
        import re
        operations_performed = []
        
        if verbose:
            print(f"\n=== Processing Reorganization Instructions ===")
            print(f"Instructions: {instructions}")
        
        # Check if instructions contain numbered operations (e.g., "1. Move alerts...")
        numbered_operations = re.findall(r'(?:\d+\.\s*)([^\d]+?)(?=\d+\.|$)', instructions)
        
        if numbered_operations:
            if verbose:
                print(f"• Found {len(numbered_operations)} numbered operations")
            
            # Process each operation separately
            for i, op in enumerate(numbered_operations):
                op = op.strip()
                if op:
                    if verbose:
                        print(f"\n--- Operation {i+1}/{len(numbered_operations)} ---")
                        print(f"• {op}")
                    
                    # Recursively call reorganize for each operation
                    sub_results = self.reorganize(op, verbose=verbose)
                    operations_performed.extend(sub_results)
            
            return operations_performed
        
        # If not numbered, process as a single operation
        
        # Look for cluster creation operations
        if "create" in instructions.lower() and "cluster" in instructions.lower():
            # Extract potential cluster ID
            cluster_id_match = re.search(r'cluster[_\s]*(\d+)', instructions)
            
            if cluster_id_match:
                # If a specific ID is mentioned, use it
                cluster_num = int(cluster_id_match.group(1))
                cluster_id = f"cluster_{cluster_num:03d}"
            else:
                # Otherwise create a new cluster with the next available ID
                cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
            
            # Extract alert IDs to include in the new cluster
            alert_ids = []
            # Look for large numbers that might be alert IDs (usually 6+ digits)
            potential_alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', instructions)]
            
            if verbose:
                print(f"• Creating cluster {cluster_id} with {len(potential_alert_ids)} alerts")
            
            # Create the new cluster
            cluster_data = {
                "cluster_id": cluster_id,
                "chains of thoughts": "Manually created cluster",
                "source_ids": "",
                "alert_ids": potential_alert_ids,
                "severity": "medium",
                "confidence": 0.5,
                "time": {"start": 0, "end": 0},
                "Description": "Manually created cluster"
            }
            
            # Add the cluster to the current clusters
            self.current_clusters["clusters"].append(cluster_data)
            
            # Remove the alerts from unassigned if they're there
            for alert_id in potential_alert_ids:
                if alert_id in self.current_clusters["unassigned_alerts"]:
                    self.current_clusters["unassigned_alerts"].remove(alert_id)
            
            operations_performed.append(f"Created cluster {cluster_id} with {len(potential_alert_ids)} alerts")
        
        # Look for move operations
        elif "move" in instructions.lower() and "alert" in instructions.lower() and "to" in instructions.lower():
            # Extract alert IDs - look for 6+ digit numbers (typical for alert IDs)
            alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', instructions)]
            
            if verbose:
                print(f"• Found {len(alert_ids)} alerts to move")
            
            # Determine source and destination
            if "unassigned" in instructions.lower() and "cluster" in instructions.lower():
                # Find the cluster ID
                cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
                if cluster_matches:
                    cluster_num = int(cluster_matches[0])
                    cluster_id = f"cluster_{cluster_num:03d}"
                    
                    # Determine direction (from unassigned to cluster or from cluster to unassigned)
                    if instructions.lower().find("unassigned") < instructions.lower().find("cluster"):
                        if verbose:
                            print(f"• Moving {len(alert_ids)} alerts FROM unassigned TO {cluster_id}")
                        
                        # Moving from unassigned to cluster
                        self._move_from_unassigned_to_cluster(alert_ids, cluster_id)
                        operations_performed.append(f"Moved {len(alert_ids)} alerts from unassigned to {cluster_id}")
                    else:
                        if verbose:
                            print(f"• Moving {len(alert_ids)} alerts FROM {cluster_id} TO unassigned")
                        
                        # Moving from cluster to unassigned
                        self._move_from_cluster_to_unassigned(alert_ids, cluster_id)
                        operations_performed.append(f"Moved {len(alert_ids)} alerts from {cluster_id} to unassigned")
            elif "cluster" in instructions.lower() and instructions.lower().count("cluster") >= 2:
                # Moving between clusters
                # Find source and destination cluster IDs
                cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
                if len(cluster_matches) >= 2:
                    src_cluster_id = f"cluster_{int(cluster_matches[0]):03d}"
                    dst_cluster_id = f"cluster_{int(cluster_matches[1]):03d}"
                    
                    if verbose:
                        print(f"• Moving {len(alert_ids)} alerts FROM {src_cluster_id} TO {dst_cluster_id}")
                    
                    self._move_between_clusters(alert_ids, src_cluster_id, dst_cluster_id)
                    operations_performed.append(f"Moved {len(alert_ids)} alerts from {src_cluster_id} to {dst_cluster_id}")
        
        # Look for merge operations
        elif "merge" in instructions.lower() and "cluster" in instructions.lower():
            # Find all cluster IDs mentioned
            cluster_matches = re.findall(r'cluster[_\s]*(\d+)', instructions)
            
            if len(cluster_matches) >= 2:
                # Get the first two distinct cluster IDs
                cluster_ids = []
                for match in cluster_matches:
                    cluster_id = f"cluster_{int(match):03d}"
                    if cluster_id not in cluster_ids:
                        cluster_ids.append(cluster_id)
                    if len(cluster_ids) == 2:
                        break
                
                if verbose:
                    print(f"• Merging {cluster_ids[1]} into {cluster_ids[0]}")
                
                self._merge_clusters(cluster_ids)
                operations_performed.append(f"Merged {cluster_ids[1]} into {cluster_ids[0]}")
        
        # If nothing happened, report it
        if not operations_performed:
            if verbose:
                print("• No operations identified from instructions")
            operations_performed.append("No operations were identified from the instructions")
        
        return operations_performed
        
    except Exception as e:
        error_message = f"Error in reorganize: {str(e)}"
        print(f"\n!!! ERROR: {error_message}")
        if verbose:
            import traceback
            traceback.print_exc()
        return [error_message]
    
def step(self, action, verbose=False):
    """
    Take a step in the environment using the provided action.
    
    Args:
        action: String in format "ActionName[parameters]" or just "ActionName"
        verbose: Whether to print detailed debug information
    
    Returns:
        observation: Current state of the environment
        reward: Reward for the action
        done: Whether the episode is done
        info: Additional information
    """
    # Parse the action string
    if "[" in action and "]" in action:
        action_name = action.split("[")[0]
        action_params = action.split("[")[1].split("]")[0]
    else:
        action_name = action
        action_params = ""
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"EXECUTING ACTION: {action_name}")
        if action_params:
            print(f"PARAMETERS: {action_params}")
        print(f"{'='*50}")
    
    # Execute the action
    if action_name == "InitialExploration":
        result = self.initial_exploration()
        observation = f"Initial exploration completed. Found {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts."
    
    elif action_name == "TimeBasedClustering":
        result = self.time_based_clustering_llm()
        observation = f"Time-based clustering completed. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts."
    
    elif action_name == "TopologyBasedClustering":
        result = self.topology_based_clustering_llm()
        observation = f"Topology-based clustering completed. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts."
    
    elif action_name == "Reassess":
        result, _ = self.assess_llm()
        
        # Extract recommendation from result
        if result and 'choices' in result and len(result['choices']) > 0:
            response_content = result['choices'][0]['message']['content']
            observation = f"Reassessment completed. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts.\n\n{response_content}"
        else:
            observation = f"Reassessment completed, but no clear recommendation was provided."
    
    elif action_name == "Reorganize":
        # Use reorganize with verbosity control
        operations = self.reorganize(action_params, verbose=verbose)
        
        # Format observation
        observation = "Reorganization completed.\n\n"
        observation += "Operations performed:\n"
        for op in operations:
            observation += f"- {op}\n"
        
        # Add current state
        observation += f"\nCurrent state: {len(self.current_clusters['clusters'])} clusters, {len(self.current_clusters['unassigned_alerts'])} unassigned alerts."
    
    elif action_name == "Finish":
        observation = "Alert aggregation process completed."
        
        # Add a final summary
        observation += f"\n\nFinal state: {len(self.current_clusters['clusters'])} clusters, {len(self.current_clusters['unassigned_alerts'])} unassigned alerts."
        
        return observation, 0, True, {"clusters": self.current_clusters}
    
    else:
        observation = f"Unknown action: {action_name}"
    
    # Store the action and result in history
    self.history.append({
        "action": action,
        "observation": observation
    })
    
    # Set done flag and reward
    done = False
    reward = 0
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"RESULT:")
        print(f"{len(self.current_clusters['clusters'])} clusters, {len(self.current_clusters['unassigned_alerts'])} unassigned alerts")
        print(f"{'='*50}\n")
    
    return observation, reward, done, {"clusters": self.current_clusters}


def _step(self, action, verbose=False):
    """
    Take a step in the environment with the given action.
    
    Simplified implementation that just ensures valid action format
    and handles retry logic for timeouts.
    
    Args:
        action: The action to take
        verbose: Whether to print detailed debug information
    
    Returns:
        Tuple of (observation, reward, done, info)
    """
    # Clean up action format if needed
    if "[" not in action and action in self.valid_prefixes:
        # Add empty brackets for consistency
        action = f"{action}[]"
    
    # Execute the action with retry logic
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        try:
            return self.env.step(action, verbose=verbose)
        except Exception as e:
            attempts += 1
            if verbose:
                print(f"! Attempt {attempts}/{max_attempts} failed: {str(e)}")
            if attempts == max_attempts:
                raise Exception(f"Max retry attempts ({max_attempts}) reached: {str(e)}")
            

def react(self, initial_prompt: str, max_num_steps: int=8, to_print: bool=False, verbose=False):
    """
    Run the ReAct framework to perform alert aggregation.
    
    Args:
        initial_prompt: The system prompt that guides the agent
        max_num_steps: Maximum number of ReAct steps to take
        to_print: Whether to print intermediate steps
        verbose: Whether to print detailed debug information
        
    Returns:
        (reward, info): Final reward and information from the environment
    """
    # Rest of implementation...
    
    try:
        obs, r, done_flag, info = self._step(action_str, verbose=verbose)
        
        # Rest of implementation...



user_message = f"""
Please assess the current state of alert clusters with a focus on identifying root causes through temporal and topological relationships.

# CURRENT ALERT BATCH:
{current_alerts_batch_str}

# CURRENT CLUSTERS:
{clusters_data}

# UNASSIGNED ALERTS:
{unassigned_alerts_data}

# TOPOLOGY INFORMATION:
{topology_info_str}

Please provide:
1. A detailed assessment focusing on temporal sequences and network dependencies
2. Analysis of whether current clusters reflect probable root causes and their effects
3. A specific recommendation for the next action that will best reveal true root causes

Structure your response as follows:

## Alert-Cluster Fit Analysis
[Your detailed analysis of whether alerts in current clusters belong there]

## Cluster Merger Analysis
[Your evaluation of whether any clusters should be merged]

## Unassigned Alert Analysis
[Your analysis of whether any unassigned alerts should be moved to existing clusters]

## Recommendation
[Your recommendation in ONE of these EXACT formats:]

TimeBasedClustering

TopologyBasedClustering

Finish

Reorganize[Move alert 845907078 from unassigned to cluster_001]

Reorganize[
1. Move alert 845907078 from unassigned to cluster_001
2. Move alerts 845907079, 845907080 from cluster_002 to cluster_003
3. Create a new cluster with alerts 845907081, 845907082, 845907083
]

Be sure to use the EXACT formatting shown above, especially for the Reorganize action.
"""

# ----------------------
def assess_llm(self, temperature=0.01):
    """
    Evaluate current clusters and provide recommendations.
    """
    # [Most of the existing function remains unchanged]
    
    # After getting the LLM response and extracting recommendation:
    if 'choices' in reply and len(reply['choices']) > 0:
        response_content = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": response_content})
        self.function_histories["assess"] = history
        
        # Store response in recent reasoning
        self.recent_reasoning["assess"] = response_content
        
        # Extract recommendation
        recommendation = self._extract_recommendation(response_content)
        
        # Create a summary
        summary = f"Assessment:\n- Evaluated {num_clusters} clusters and {num_unassigned} unassigned alerts\n"
        summary += f"- Recommended: {recommendation}\n"
        
        # Add to ReAct history
        self.react_history.append({
            "action": "Reassess",
            "summary": summary
        })
        
        # If reorganization is recommended, automatically trigger it
        if recommendation.startswith("Reorganize["):
            # Call the reorganize function with the assessment and recommendation
            self.reorganize_complete_state(response_content, recommendation)
        
        return reply, history
    

def reorganize_complete_state(self, assessment_content, recommendation=None, temperature=0.01):
    """
    Request and implement a complete new clustering state based on assessment.
    
    Args:
        assessment_content: The full content of the assessment
        recommendation: The specific recommendation (optional)
    """
    # Create message history for this function
    history = self.function_histories.get("reorganize", [])
    
    # Create a system message explaining the task
    system_message = """
    You are a network alert clustering expert. Your task is to create a complete new clustering state based 
    on the assessment provided. Output the entire clustering as a valid JSON object that can be directly used 
    to replace the current clusters.
    """
    
    # Create a user message with the assessment and request for complete clustering
    user_message = f"""
    Here is an assessment of the current alert clusters:
    
    {assessment_content}
    
    Based on this assessment, provide the complete new state of all clusters and unassigned alerts.
    Output the result as a valid JSON object with the following structure:
    
    {{
      "clusters": [
        {{
          "cluster_id": "cluster_001",
          "chains of thoughts": "Reasoning behind this cluster",
          "source_ids": "source device IDs",
          "alert_ids": [list of alert IDs that should be in this cluster],
          "severity": "severity level",
          "time": {{"start": timestamp, "end": timestamp}},
          "confidence": confidence value,
          "Description": "Description of the cluster"
        }},
        // Additional clusters...
      ],
      "unassigned_alerts": [list of alert IDs that should remain unassigned]
    }}
    
    Ensure all alert IDs are properly assigned based on the assessment.
    """
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # Add to history
    history += messages
    self.function_histories["reorganize"] = history
    
    # Call the LLM with JSON response format
    reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
    
    # Process the response
    if 'choices' in reply and len(reply['choices']) > 0:
        clustering_json = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": clustering_json})
        self.function_histories["reorganize"] = history
        
        try:
            # Save the old state for reporting changes
            old_state = {
                "num_clusters": len(self.current_clusters["clusters"]),
                "num_unassigned": len(self._ensure_list_format(self.current_clusters["unassigned_alerts"]))
            }
            
            # Parse and validate the new clustering
            new_clusters = json.loads(clustering_json)
            
            # Ensure proper format of alert_ids
            if "clusters" in new_clusters:
                for cluster in new_clusters["clusters"]:
                    if "alert_ids" in cluster:
                        cluster["alert_ids"] = self._ensure_list_format(cluster["alert_ids"])
            
            if "unassigned_alerts" in new_clusters:
                new_clusters["unassigned_alerts"] = self._ensure_list_format(new_clusters["unassigned_alerts"])
            
            # Replace current clusters with new clusters
            self.current_clusters = new_clusters
            
            # Calculate the new state
            new_state = {
                "num_clusters": len(self.current_clusters["clusters"]),
                "num_unassigned": len(self._ensure_list_format(self.current_clusters["unassigned_alerts"]))
            }
            
            # Create summary of changes
            operations_summary = [
                f"Complete reorganization: {old_state['num_clusters']} → {new_state['num_clusters']} clusters, {old_state['num_unassigned']} → {new_state['num_unassigned']} unassigned alerts"
            ]
            
            # Add to ReAct history
            self.react_history.append({
                "action": "Reorganize",
                "summary": f"Complete cluster reorganization: {new_state['num_clusters']} clusters, {new_state['num_unassigned']} unassigned"
            })
            
            return operations_summary
            
        except Exception as e:
            error_msg = f"Error applying new clustering state: {str(e)}"
            print(f"\n!!! ERROR: {error_msg}")
            return [f"Error: {error_msg}"]
    
    return ["No valid clustering data received"]


def step(self, action, verbose=False):
    """
    Take a step in the environment using the provided action.
    """
    # [Initial parsing code remains the same]
    
    # Execute the action
    if action_name == "InitialExploration":
        # [Unchanged]
    
    elif action_name == "TimeBasedClustering":
        # [Unchanged]
    
    elif action_name == "TopologyBasedClustering":
        # [Unchanged]
    
    elif action_name == "Reassess":
        result, _ = self.assess_llm()
        
        # Extract recommendation from result
        if result and 'choices' in result and len(result['choices']) > 0:
            response_content = result['choices'][0]['message']['content']
            
            # Extract recommendation to check if reorganization was triggered
            recommendation = self._extract_recommendation(response_content)
            
            if recommendation.startswith("Reorganize["):
                # Reorganization was automatically triggered by assess_llm
                observation = f"Assessment completed with automatic reorganization. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts.\n\n{response_content}"
            else:
                observation = f"Assessment completed. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts.\n\n{response_content}"
        else:
            observation = f"Assessment completed, but no clear recommendation was provided."
    
    elif action_name == "Finish":
        # [Unchanged]
    
    else:
        observation = f"Unknown action: {action_name}. Valid actions are: InitialExploration, TimeBasedClustering, TopologyBasedClustering, Reassess, Finish."
    
    # [Rest of the function remains unchanged]


## Available Actions:

1. InitialExploration - Perform initial clustering on the current batch of alerts.
   You can simply write "InitialExploration" (no parameters needed)
   
2. TimeBasedClustering - Cluster alerts based on temporal relationships.
   You can simply write "TimeBasedClustering" (no parameters needed)
   
3. TopologyBasedClustering - Cluster alerts based on network topology relationships.
   You can simply write "TopologyBasedClustering" (no parameters needed)
   
4. Reassess - Evaluate current clusters and provide recommendations.
   You can simply write "Reassess" (no parameters needed)
   IMPORTANT: If you recommend reorganization, the system will automatically implement those changes.
   You do NOT need to follow up with separate reorganization actions.
   
5. Finish - Complete the analysis and provide a final assessment.
   You can simply write "Finish" (no parameters needed)



def assess_llm(self, temperature=0.01):
    """
    Evaluate current clusters and provide recommendations.
    If reorganization is recommended, it is automatically applied.
    """
    # [Existing code to prepare data and call LLM]
    
    # After getting LLM response
    if 'choices' in reply and len(reply['choices']) > 0:
        response_content = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": response_content})
        self.function_histories["assess"] = history
        
        # Store response in recent reasoning
        self.recent_reasoning["assess"] = response_content
        
        # Extract recommendation using the _extract_recommendation method
        recommendation = self._extract_recommendation(response_content)
        
        # Create a summary for the ReAct framework
        summary = f"Assessment:\n- Evaluated {num_clusters} clusters and {num_unassigned} unassigned alerts\n"
        summary += f"- Recommended: {recommendation}\n"
        
        # Check if reorganization is recommended
        if recommendation.startswith("Reorganize["):
            print(f"Detected reorganization recommendation: {recommendation}")
            # Call reorganize_complete_state with the assessment content
            try:
                operations = self.reorganize_complete_state(response_content, recommendation)
                
                # Update the response to indicate reorganization was performed
                response_content += "\n\n## Reorganization Automatically Applied:\n"
                for op in operations:
                    response_content += f"- {op}\n"
                
                # Update summary
                summary += "- Reorganization automatically applied\n"
                
                # Create modified result to return
                observation = f"Assessment completed with automatic reorganization. Now have {len(self.current_clusters['clusters'])} clusters and {len(self.current_clusters['unassigned_alerts'])} unassigned alerts.\n\n{response_content}"
                modified_reply = {"choices": [{"message": {"content": observation}}]}
                
                # Add to ReAct history
                self.react_history.append({
                    "action": "Reassess",
                    "summary": summary
                })
                
                return modified_reply, history
            except Exception as e:
                print(f"Error in automatic reorganization: {str(e)}")
                # Continue without reorganization if it fails
        
        # Add to ReAct history (for non-reorganization cases)
        self.react_history.append({
            "action": "Reassess",
            "summary": summary
        })
        
        return reply, history
    


    elif action_name == "Reorganize":
    print("\n⚠️ WARNING: Agent attempted to use deprecated 'Reorganize' action directly.")
    observation = "Unknown action: Reorganize. Valid actions are: InitialExploration, TimeBasedClustering, TopologyBasedClustering, Reassess, Finish."



    def _safe_json_parse(self, json_str):
    """Safely parse JSON, handling common formatting issues."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"First 100 chars: {json_str[:100]}...")
        
        # Try to fix common issues (only if needed)
        try:
            # Sometimes the response has Markdown formatting or other text before/after the JSON
            # Try to extract just the JSON part using regex
            import re
            json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|(\{[\s\S]*\})'
            json_match = re.search(json_pattern, json_str)
            
            if json_match:
                for group in json_match.groups():
                    if group:
                        cleaned_json = group.strip()
                        print(f"Found JSON match: {cleaned_json[:50]}...")
                        return json.loads(cleaned_json)
            
            # If that didn't work, try a more aggressive approach
            # Find the first { and the last }
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                extracted_json = json_str[start_idx:end_idx+1]
                print(f"Extracted JSON between braces: {extracted_json[:50]}...")
                return json.loads(extracted_json)
                
            raise ValueError("Could not extract valid JSON")
        except Exception as inner_e:
            print(f"Failed to recover JSON: {inner_e}")
            # Return the previous clustering state instead of raising an exception
            return self.current_clusters
        


def topology_based_clustering_llm(self, temperature=0.01):
    """
    Perform topology-based clustering on the current batch of alerts.
    Uses a dedicated history for this function and creates a summary for the ReAct framework.
    """
    # [Keep existing setup code]
    
    # Call the LLM
    reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
    
    # Check for the response validity
    if 'choices' in reply and len(reply['choices']) > 0:
        response_content = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": response_content})
        self.function_histories["topology_based_clustering"] = history
        
        # Store response in recent reasoning
        self.recent_reasoning["topology_based_clustering"] = response_content
        
        # Parse clusters from response with safer parsing
        try:
            # Use safe JSON parsing
            parsed_clusters = self._safe_json_parse(response_content)
            
            # Only update if parsing succeeded
            if parsed_clusters:
                # Ensure consistent format
                if "clusters" in parsed_clusters:
                    for cluster in parsed_clusters["clusters"]:
                        if "alert_ids" in cluster:
                            cluster["alert_ids"] = self._ensure_list_format(cluster["alert_ids"])
                
                if "unassigned_alerts" in parsed_clusters:
                    parsed_clusters["unassigned_alerts"] = self._ensure_list_format(parsed_clusters["unassigned_alerts"])
                
                self.current_clusters = parsed_clusters
            else:
                print("Warning: Could not parse topology clustering results, keeping previous state")
                
        except Exception as e:
            print(f"Failed to load the clusters: {e}")
            print("Keeping previous clustering state")
            # Don't update current_clusters if parsing fails
        
        # Create a summary for the ReAct framework
        summary = self._create_clustering_summary(
            "topology_based_clustering", 
            self.current_clusters,
            response_content
        )
        
        # Add to ReAct history
        self.react_history.append({
            "action": "TopologyBasedClustering",
            "summary": summary
        })
    else:
        print("Invalid response from API")
    
    return reply


# Add this to the user message in topology_based_clustering_llm, time_based_clustering_llm, and initial_exploration
"""
IMPORTANT: Your response MUST be ONLY valid JSON in the specified format. 
Do not include any explanatory text, markdown formatting, or anything outside of the JSON object.
"""



def reorganize_complete_state(self, assessment_content, recommendation=None, temperature=0.01):
    """
    Request and implement a complete new clustering state based on assessment.
    """
    # Initialize history properly
    if "reorganize" not in self.function_histories:
        self.function_histories["reorganize"] = []
    history = self.function_histories["reorganize"]
    
    # Extract specific instructions from recommendation if provided
    instructions = ""
    if recommendation and recommendation.startswith("Reorganize["):
        instructions = recommendation[len("Reorganize["):-1].strip()
    
    # Create a system message explaining the task
    system_message = """
    You are a network alert clustering expert. Your task is to create a complete new clustering state based 
    on the assessment provided. Output the entire clustering as a valid JSON object that can be directly used 
    to replace the current clusters.
    
    IMPORTANT: Ensure ALL alerts from the original state are included in your new state, either in clusters or as unassigned.
    DO NOT lose any alerts during reorganization. Your output must contain exactly the same set of alert IDs as the input.
    """
    
    # Create a user message with the assessment and request for complete clustering
    user_message = f"""
    Here is an assessment of the current alert clusters:
    
    {assessment_content}
    
    Based on this assessment, provide the complete new state of all clusters and unassigned alerts.
    {f"Specifically implement these changes: {instructions}" if instructions else ""}
    
    Output the result as a valid JSON object with the following structure:
    
    {{
      "clusters": [
        {{
          "cluster_id": "cluster_001",
          "chains of thoughts": "Reasoning behind this cluster",
          "source_ids": "source device IDs",
          "alert_ids": [list of alert IDs that should be in this cluster],
          "severity": "severity level",
          "time": {{"start": timestamp, "end": timestamp}},
          "confidence": confidence value,
          "Description": "Description of the cluster"
        }},
        // Additional clusters...
      ],
      "unassigned_alerts": [list of alert IDs that should remain unassigned]
    }}
    
    Ensure ALL alerts from the original state are included in your output, either in clusters or as unassigned.
    Your output must be ONLY valid JSON with no additional text or explanation.
    """
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # Add to history
    history += messages
    self.function_histories["reorganize"] = history
    
    # Call the LLM with JSON response format
    reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
    
    # Process the response
    if 'choices' in reply and len(reply['choices']) > 0:
        clustering_json = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": clustering_json})
        self.function_histories["reorganize"] = history
        
        try:
            # Save the old state for reporting changes and validation
            old_state = {
                "num_clusters": len(self.current_clusters["clusters"]),
                "num_unassigned": len(self._ensure_list_format(self.current_clusters["unassigned_alerts"]))
            }
            
            # Get the complete set of alert IDs from current state
            current_alert_ids = set()
            # Add alert IDs from clusters
            for cluster in self.current_clusters["clusters"]:
                if "alert_ids" in cluster:
                    alert_ids = self._ensure_list_format(cluster["alert_ids"])
                    current_alert_ids.update(alert_ids)
            # Add unassigned alert IDs
            current_alert_ids.update(self._ensure_list_format(self.current_clusters["unassigned_alerts"]))
            
            # Parse and validate the new clustering
            new_clusters = json.loads(clustering_json)
            
            # Ensure proper format of alert_ids
            if "clusters" in new_clusters:
                for cluster in new_clusters["clusters"]:
                    if "alert_ids" in cluster:
                        cluster["alert_ids"] = self._ensure_list_format(cluster["alert_ids"])
            
            if "unassigned_alerts" in new_clusters:
                new_clusters["unassigned_alerts"] = self._ensure_list_format(new_clusters["unassigned_alerts"])
            else:
                new_clusters["unassigned_alerts"] = []
            
            # Verify all alerts are accounted for
            new_alert_ids = set()
            # Add alert IDs from new clusters
            for cluster in new_clusters.get("clusters", []):
                if "alert_ids" in cluster:
                    new_alert_ids.update(cluster["alert_ids"])
            # Add new unassigned alert IDs
            new_alert_ids.update(new_clusters.get("unassigned_alerts", []))
            
            # Check for missing alerts
            missing_alerts = current_alert_ids - new_alert_ids
            if missing_alerts:
                print(f"Warning: {len(missing_alerts)} alerts were not included in the new clustering state")
                print(f"Missing alerts: {missing_alerts}")
                # Add missing alerts to unassigned
                new_clusters["unassigned_alerts"] = list(new_clusters.get("unassigned_alerts", [])) + list(missing_alerts)
                print(f"Added missing alerts to unassigned")
            
            # Check for extra alerts (shouldn't happen, but for completeness)
            extra_alerts = new_alert_ids - current_alert_ids
            if extra_alerts:
                print(f"Warning: {len(extra_alerts)} extra alerts that weren't in the original state")
                # We could remove them, but it might be better to keep them in case they're valid
            
            # Replace current clusters with new clusters
            self.current_clusters = new_clusters
            
            # Calculate the new state
            new_state = {
                "num_clusters": len(self.current_clusters["clusters"]),
                "num_unassigned": len(self._ensure_list_format(self.current_clusters["unassigned_alerts"]))
            }
            
            # Create summary of changes
            operations_summary = [
                f"Complete reorganization: {old_state['num_clusters']} → {new_state['num_clusters']} clusters, {old_state['num_unassigned']} → {new_state['num_unassigned']} unassigned alerts"
            ]
            
            # Add to ReAct history
            self.react_history.append({
                "action": "Reorganize",
                "summary": f"Complete cluster reorganization: {new_state['num_clusters']} clusters, {new_state['num_unassigned']} unassigned"
            })
            
            return operations_summary
            
        except Exception as e:
            error_msg = f"Error applying new clustering state: {str(e)}"
            print(f"\n!!! ERROR: {error_msg}")
            return [f"Error: {error_msg}"]
    
    return ["No valid clustering data received"]