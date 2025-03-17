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


# RECOMMENDATION EXAMPLES:

## Example: Well-Formatted Reorganize with Multiple Operations
Reorganize[
1. Move alerts 1001, 1002 from unassigned to cluster_003
2. Merge clusters 001 and 004
3. Create a new cluster with alerts 2001, 2002, 2003
]

## Example: Well-Formatted Reorganize with Single Operation
Reorganize[Move alerts 1001, 1002 from unassigned to cluster_003]

## Example: Well-Formatted Simple Action
TimeBasedClustering




def _extract_recommendation(self, response_content):
    """
    Extract the recommended next action from the LLM response.
    Optimized for the new standardized format.
    """
    try:
        import re
        
        # Look for well-formatted actions
        simple_actions = ["TimeBasedClustering", "TopologyBasedClustering", "Finish"]
        
        # First look for a reorganize with multiple operations
        multi_op_pattern = r'Reorganize\s*\[\s*\n([\s\S]*?)\n\s*\]'
        multi_op_match = re.search(multi_op_pattern, response_content)
        
        if multi_op_match:
            operations_text = multi_op_match.group(1).strip()
            return f"Reorganize[{operations_text}]"
        
        # Then look for a reorganize with a single operation
        single_op_pattern = r'Reorganize\s*\[\s*(.*?)\s*\]'
        single_op_match = re.search(single_op_pattern, response_content)
        
        if single_op_match:
            operation_text = single_op_match.group(1).strip()
            return f"Reorganize[{operation_text}]"
        
        # Look for simple actions
        for action in simple_actions:
            if re.search(r'\b' + action + r'\b', response_content):
                return f"{action}[]"
        
        # Default fallback
        return "No clear action recommendation found. Consider performing Reassess[] again."
        
    except Exception as e:
        print(f"Error extracting recommendation: {str(e)}")
        return "Error extracting recommendation. Consider performing Reassess[] again."
    

def react(self, initial_prompt: str, max_num_steps: int=8, to_print: bool=False, verbose: bool=False):
    """
    Run the ReAct framework to perform alert aggregation.
    
    Simplified implementation that focuses on robustness and simplicity.
    
    Args:
        initial_prompt: The system prompt that guides the agent
        max_num_steps: Maximum number of ReAct steps to take
        to_print: Whether to print intermediate steps
        verbose: Whether to print detailed debug information
        
    Returns:
        (reward, info): Final reward and information from the environment
    """
    # Add format instructions to the initial prompt
    format_instructions = """
    # ACTION FORMAT GUIDELINES:
    
    When generating thoughts and actions, follow this format:
    
    Thought N: [Your detailed reasoning about the current state and what action to take next]
    
    Then for your action, use EXACTLY one of these formats:
    
    Action N: InitialExploration
    Action N: TimeBasedClustering
    Action N: TopologyBasedClustering
    Action N: Reassess
    Action N: Finish
    
    For reorganize actions with a SINGLE operation:
    Action N: Reorganize[Move alert 845907078 from unassigned to cluster_001]
    
    For reorganize actions with MULTIPLE operations:
    Action N: Reorganize[
    1. Move alert 845907078 from unassigned to cluster_001
    2. Move alerts 845907079, 845907080 from cluster_002 to cluster_003
    3. Create a new cluster with alerts 845907081, 845907082, 845907083
    ]
    
    Always place the entire instruction inside square brackets. For multiple operations, 
    use numbered list format with each operation on its own line.
    """
    
    enhanced_prompt = initial_prompt + "\n\n" + format_instructions
    
    # Store the conversation in messages
    self.react_messages = [{"role": "system", "content": enhanced_prompt}]
    
    # Initialize tracking variables
    n_calls = 0
    done = False
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"STARTING REACT FRAMEWORK")
        print(f"{'='*50}\n")
    
    # Begin the iterative ReAct loop
    for i in range(1, max_num_steps + 1):
        n_calls += 1
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"STEP {i}/{max_num_steps}")
            print(f"{'='*50}")
        
        # Prompt the LLM for next thought and action
        user_msg = f"""Thought {i}:

After your thought, provide your next action in one of these EXACT formats:

- Action {i}: InitialExploration
- Action {i}: TimeBasedClustering  
- Action {i}: TopologyBasedClustering
- Action {i}: Reassess
- Action {i}: Finish

Or for reorganize actions:

- Action {i}: Reorganize[Move alert 845907078 from unassigned to cluster_001]

Or for multiple reorganization operations:

- Action {i}: Reorganize[
1. Move alert 845907078 from unassigned to cluster_001
2. Create a new cluster with alerts 845907079, 845907080
]

Be sure to use the EXACT formatting shown above.
"""
        
        self.react_messages.append({"role": "user", "content": user_msg})
        
        # Call the LLM
        thought_action_response = self._llm(self.react_messages, stop=[f"\nObservation {i}:"])
        assistant_text = thought_action_response["choices"][0]["message"]["content"]
        
        if to_print:
            print(f"LLM Response {i}:\n{assistant_text}\n")
        
        # Extract thought and action using simple parsing
        thought_str = ""
        action_str = ""
        
        # Try to extract using standard format first
        if f"\nAction {i}:" in assistant_text:
            parts = assistant_text.split(f"\nAction {i}:")
            thought_str = parts[0].strip()
            action_str = parts[1].strip()
        else:
            # Fallback: look for "Action N:" pattern with any number
            action_match = re.search(r'\nAction\s+\d+:\s*(.*)', assistant_text)
            if action_match:
                action_parts = assistant_text.split(action_match.group(0))
                thought_str = action_parts[0].strip()
                action_str = action_match.group(1).strip()
            else:
                # Second fallback: just take the first line as thought, the rest as action
                lines = assistant_text.split('\n')
                thought_str = lines[0].strip()
                action_str = ' '.join(lines[1:]).strip()
        
        # Clean up the extracted action
        action_str = action_str.strip()
        if action_str.startswith('"') and action_str.endswith('"'):
            action_str = action_str[1:-1].strip()
        elif action_str.startswith("'") and action_str.endswith("'"):
            action_str = action_str[1:-1].strip()
        
        if verbose:
            print(f"• Extracted thought: {thought_str[:50]}...")
            print(f"• Extracted action: {action_str}")
        
        # Record the thought and action in the conversation
        self.react_messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
        self.react_messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
        
        # Validate the action format
        valid_action = False
        
        # Check if it's a valid action name
        for prefix in self.valid_prefixes:
            if action_str == prefix or action_str.startswith(f"{prefix}["):
                valid_action = True
                break
        
        if not valid_action:
            # If invalid, provide feedback and continue to next iteration
            obs_str = f"Invalid action: '{action_str}'. Valid actions are: {', '.join(self.valid_prefixes)}."
            self.react_messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
            if to_print:
                print(f"Observation {i}: {obs_str}")
            
            if verbose:
                print(f"! Invalid action format detected")
            
            continue
        
        # Execute the action
        try:
            if verbose:
                print(f"• Executing action: {action_str}")
            
            obs, r, done_flag, info = self._step(action_str, verbose=verbose)
            
            # Record the observation
            obs_str = f"Observation {i}: {obs}"
            self.react_messages.append({"role": "system", "content": obs_str})
            
            if to_print:
                print(f"Thought {i}: {thought_str}")
                print(f"Action {i}: {action_str}")
                print(f"Observation {i}: {obs}\n")
            
            # Check if we're done
            if done_flag:
                if verbose:
                    print(f"• Episode completed at step {i}")
                done = True
                break
                
        except Exception as e:
            # Handle any errors during execution
            error_msg = f"Error executing action: {str(e)}"
            self.react_messages.append({"role": "system", "content": f"Observation {i}: {error_msg}"})
            if to_print:
                print(f"Observation {i}: {error_msg}")
            
            if verbose:
                print(f"! Error during action execution: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # If we run out of steps without finishing, force a finish
    if not done:
        try:
            if verbose:
                print(f"\n{'='*50}")
                print(f"MAXIMUM STEPS REACHED - FORCING FINISH")
                print(f"{'='*50}\n")
            
            obs, r, done_flag, info = self._step("Finish[]", verbose=verbose)
            self.react_messages.append({"role": "system", "content": f"Observation Final: {obs}"})
            done = True
        except Exception as e:
            # Handle errors during forced finish
            error_msg = f"Error during forced finish: {str(e)}"
            self.react_messages.append({"role": "system", "content": f"Observation Final: {error_msg}"})
            
            if verbose:
                print(f"! Error during forced finish: {str(e)}")
                import traceback
                traceback.print_exc()
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"REACT FRAMEWORK COMPLETED")
        print(f"- Total calls: {n_calls}")
        print(f"- Final state: {len(self.env.current_clusters['clusters'])} clusters, {len(self.env.current_clusters['unassigned_alerts'])} unassigned alerts")
        print(f"{'='*50}\n")
    
    # Prepare return information
    info = {
        "n_calls": n_calls,
        "traj": self.react_messages,
        "clusters": self.env.current_clusters if hasattr(self.env, 'current_clusters') else None
    }
    
    return 0, info  # Return 0 reward for simplicity




# -------------------
def _move_from_cluster_to_unassigned(self, alert_ids, src_cluster_id):
    """Move alerts from a specific cluster to unassigned."""
    # Find the source cluster
    src_cluster = None
    for cluster in self.current_clusters["clusters"]:
        if cluster["cluster_id"] == src_cluster_id:
            src_cluster = cluster
            break
    
    if not src_cluster:
        raise ValueError(f"Source cluster {src_cluster_id} not found")
    
    # Ensure alert_ids in the source cluster is a list
    if "alert_ids" not in src_cluster:
        src_cluster["alert_ids"] = []
    
    # Convert string representation of a list to an actual list if needed
    if isinstance(src_cluster["alert_ids"], str):
        try:
            # Try to parse as JSON
            src_cluster["alert_ids"] = json.loads(src_cluster["alert_ids"])
        except json.JSONDecodeError:
            # Fallback: handle string formats like "[1,2,3]" or "1, 2, 3"
            clean_str = src_cluster["alert_ids"].strip('[]').replace(' ', '')
            if clean_str:  # Only split if there's content
                src_cluster["alert_ids"] = [int(aid) for aid in clean_str.split(',') if aid]
            else:
                src_cluster["alert_ids"] = []
    
    # Ensure unassigned_alerts is a list
    if isinstance(self.current_clusters["unassigned_alerts"], str):
        try:
            # Try to parse as JSON
            self.current_clusters["unassigned_alerts"] = json.loads(self.current_clusters["unassigned_alerts"])
        except json.JSONDecodeError:
            # Fallback: handle string formats like "[1,2,3]" or "1, 2, 3"
            clean_str = self.current_clusters["unassigned_alerts"].strip('[]').replace(' ', '')
            if clean_str:  # Only split if there's content
                self.current_clusters["unassigned_alerts"] = [int(aid) for aid in clean_str.split(',') if aid]
            else:
                self.current_clusters["unassigned_alerts"] = []
    
    # Move alerts
    for alert_id in alert_ids:
        if alert_id in src_cluster["alert_ids"]:
            # Remove from cluster
            src_cluster["alert_ids"].remove(alert_id)
            # Add to unassigned
            self.current_clusters["unassigned_alerts"].append(alert_id)

def _move_from_unassigned_to_cluster(self, alert_ids, dst_cluster_id):
    """Move alerts from unassigned to a specific cluster."""
    # Find the destination cluster
    dst_cluster = None
    for cluster in self.current_clusters["clusters"]:
        if cluster["cluster_id"] == dst_cluster_id:
            dst_cluster = cluster
            break
    
    if not dst_cluster:
        raise ValueError(f"Destination cluster {dst_cluster_id} not found")
    
    # Ensure alert_ids in the destination cluster is a list
    if "alert_ids" not in dst_cluster:
        dst_cluster["alert_ids"] = []
    
    # Convert string representation of a list to an actual list if needed
    if isinstance(dst_cluster["alert_ids"], str):
        try:
            # Try to parse as JSON
            dst_cluster["alert_ids"] = json.loads(dst_cluster["alert_ids"])
        except json.JSONDecodeError:
            # Fallback: handle string formats like "[1,2,3]" or "1, 2, 3"
            clean_str = dst_cluster["alert_ids"].strip('[]').replace(' ', '')
            if clean_str:  # Only split if there's content
                dst_cluster["alert_ids"] = [int(aid) for aid in clean_str.split(',') if aid]
            else:
                dst_cluster["alert_ids"] = []
    
    # Ensure unassigned_alerts is a list
    if isinstance(self.current_clusters["unassigned_alerts"], str):
        try:
            # Try to parse as JSON
            self.current_clusters["unassigned_alerts"] = json.loads(self.current_clusters["unassigned_alerts"])
        except json.JSONDecodeError:
            # Fallback: handle string formats like "[1,2,3]" or "1, 2, 3"
            clean_str = self.current_clusters["unassigned_alerts"].strip('[]').replace(' ', '')
            if clean_str:  # Only split if there's content
                self.current_clusters["unassigned_alerts"] = [int(aid) for aid in clean_str.split(',') if aid]
            else:
                self.current_clusters["unassigned_alerts"] = []
    
    # Move alerts
    for alert_id in alert_ids:
        if alert_id in self.current_clusters["unassigned_alerts"]:
            # Add to cluster
            dst_cluster["alert_ids"].append(alert_id)
            # Remove from unassigned
            self.current_clusters["unassigned_alerts"].remove(alert_id)


def _ensure_list_format(self, alert_ids_value):
    """Convert various alert_ids formats to a proper list."""
    if alert_ids_value is None:
        return []
        
    if isinstance(alert_ids_value, list):
        return alert_ids_value
        
    if isinstance(alert_ids_value, str):
        try:
            # Try to parse as JSON
            return json.loads(alert_ids_value)
        except json.JSONDecodeError:
            # Fallback: handle string formats like "[1,2,3]" or "1, 2, 3"
            clean_str = alert_ids_value.strip('[]').replace(' ', '')
            if clean_str:  # Only split if there's content
                return [int(aid) for aid in clean_str.split(',') if aid]
            else:
                return []
                
    # For any other type, try conversion
    return list(alert_ids_value)


def reorganize(self, instructions, verbose=False):
    """
    Implement reorganization based on natural language instructions.
    Support for multiple operations in a single instruction string.
    """
    try:
        import re
        operations_performed = []
        
        if verbose:
            print(f"\n=== Processing Reorganization Instructions ===")
            print(f"Instructions: {instructions}")
        
        # Check if instructions contain numbered operations
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
            
            # Ensure unassigned_alerts is a list
            self.current_clusters["unassigned_alerts"] = self._ensure_list_format(self.current_clusters["unassigned_alerts"])
            
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
    

def _move_between_clusters(self, alert_ids, src_cluster_id, dst_cluster_id):
    """Move alerts from one cluster to another."""
    # Find source and destination clusters
    src_cluster = None
    dst_cluster = None
    
    for cluster in self.current_clusters["clusters"]:
        if cluster["cluster_id"] == src_cluster_id:
            src_cluster = cluster
        if cluster["cluster_id"] == dst_cluster_id:
            dst_cluster = cluster
    
    if not src_cluster:
        raise ValueError(f"Source cluster {src_cluster_id} not found")
    if not dst_cluster:
        raise ValueError(f"Destination cluster {dst_cluster_id} not found")
    
    # Ensure alert_ids in the source cluster is a list
    if "alert_ids" not in src_cluster:
        src_cluster["alert_ids"] = []
    
    # Convert string representation of a list to an actual list if needed
    src_cluster["alert_ids"] = self._ensure_list_format(src_cluster["alert_ids"])
    
    # Ensure alert_ids in the destination cluster is a list
    if "alert_ids" not in dst_cluster:
        dst_cluster["alert_ids"] = []
    
    # Convert string representation of a list to an actual list if needed
    dst_cluster["alert_ids"] = self._ensure_list_format(dst_cluster["alert_ids"])
    
    # Move alerts
    for alert_id in alert_ids:
        if alert_id in src_cluster["alert_ids"]:
            # Remove from source cluster
            src_cluster["alert_ids"].remove(alert_id)
            # Add to destination cluster
            dst_cluster["alert_ids"].append(alert_id)


def _merge_clusters(self, cluster_ids):
    """Merge multiple clusters into one."""
    if len(cluster_ids) < 2:
        return
    
    # Find the clusters to merge
    clusters_to_merge = []
    for cluster_id in cluster_ids:
        for cluster in self.current_clusters["clusters"]:
            if cluster["cluster_id"] == cluster_id:
                clusters_to_merge.append(cluster)
                break
    
    if len(clusters_to_merge) < 2:
        return
    
    # Use the first cluster as the base
    base_cluster = clusters_to_merge[0]
    
    # Merge other clusters into the base cluster
    for cluster in clusters_to_merge[1:]:
        # Merge alert_ids using our helper function
        base_cluster["alert_ids"] = self._ensure_list_format(base_cluster.get("alert_ids", []))
        cluster_alert_ids = self._ensure_list_format(cluster.get("alert_ids", []))
        
        base_cluster["alert_ids"].extend(cluster_alert_ids)
        
        # Merge source_ids - handle both string and list formats
        if "source_ids" in base_cluster:
            if isinstance(base_cluster["source_ids"], str):
                if base_cluster["source_ids"].startswith("[") and base_cluster["source_ids"].endswith("]"):
                    try:
                        base_source_ids = json.loads(base_cluster["source_ids"])
                    except:
                        base_source_ids = [s.strip() for s in base_cluster["source_ids"].strip("[]").split(",")]
                else:
                    base_source_ids = [s.strip() for s in base_cluster["source_ids"].split(",")]
            else:
                base_source_ids = list(base_cluster["source_ids"])
        else:
            base_source_ids = []
            
        if "source_ids" in cluster:
            if isinstance(cluster["source_ids"], str):
                if cluster["source_ids"].startswith("[") and cluster["source_ids"].endswith("]"):
                    try:
                        cluster_source_ids = json.loads(cluster["source_ids"])
                    except:
                        cluster_source_ids = [s.strip() for s in cluster["source_ids"].strip("[]").split(",")]
                else:
                    cluster_source_ids = [s.strip() for s in cluster["source_ids"].split(",")]
            else:
                cluster_source_ids = list(cluster["source_ids"])
        else:
            cluster_source_ids = []
        
        base_source_ids.extend(cluster_source_ids)
        
        # Remove duplicates and format as string or list based on original format
        unique_sources = list(set(source for source in base_source_ids if source))
        if isinstance(base_cluster.get("source_ids", ""), str):
            base_cluster["source_ids"] = ", ".join(unique_sources)
        else:
            base_cluster["source_ids"] = unique_sources
        
        # Update time range
        if "time" in base_cluster and "time" in cluster:
            base_cluster["time"]["start"] = min(base_cluster["time"]["start"], cluster["time"]["start"])
            base_cluster["time"]["end"] = max(base_cluster["time"]["end"], cluster["time"]["end"])
        
        # Update severity if needed - handle both string and number formats
        if "severity" in cluster and "severity" in base_cluster:
            base_severity = base_cluster["severity"]
            cluster_severity = cluster["severity"]
            
            # Convert to numbers for comparison if they're strings
            if isinstance(base_severity, str) and base_severity.isdigit():
                base_severity = int(base_severity)
            if isinstance(cluster_severity, str) and cluster_severity.isdigit():
                cluster_severity = int(cluster_severity)
                
            if cluster_severity > base_severity:
                base_cluster["severity"] = cluster["severity"]  # Keep original format
        
        # Update description
        if "Description" in base_cluster and "Description" in cluster:
            base_cluster["Description"] += f" Combined with: {cluster['Description']}"
        
        # Update confidence - handle both string and number formats
        if "confidence" in base_cluster and "confidence" in cluster:
            base_confidence = base_cluster["confidence"]
            cluster_confidence = cluster["confidence"]
            
            # Convert to numbers for calculation if they're strings
            if isinstance(base_confidence, str):
                base_confidence = float(base_confidence)
            if isinstance(cluster_confidence, str):
                cluster_confidence = float(cluster_confidence)
                
            avg_confidence = (base_confidence + cluster_confidence) / 2
            
            # Keep original format (string or number)
            if isinstance(base_cluster["confidence"], str):
                base_cluster["confidence"] = str(avg_confidence)
            else:
                base_cluster["confidence"] = avg_confidence
        
        # Remove the merged cluster
        self.current_clusters["clusters"].remove(cluster)

def _create_new_cluster(self, alert_ids, cluster_data):
    """Create a new cluster with the specified alerts."""
    # Ensure alert_ids is a list
    alert_ids = self._ensure_list_format(alert_ids)
    
    # Create a new cluster with the provided data
    new_cluster = {
        "cluster_id": cluster_data.get("cluster_id", f"cluster_{len(self.current_clusters['clusters']) + 1}"),
        "chains of thoughts": cluster_data.get("chains_of_thoughts", "Manually created cluster"),
        "source_ids": cluster_data.get("source_ids", ""),
        "alert_ids": alert_ids,
        "severity": cluster_data.get("severity", "medium"),
        "time": cluster_data.get("time", {"start": 0, "end": 0}),
        "confidence": cluster_data.get("confidence", 0.5),
        "Description": cluster_data.get("Description", "Manually created cluster")
    }
    
    # Add the new cluster
    self.current_clusters["clusters"].append(new_cluster)
    
    # Ensure unassigned_alerts is a list
    self.current_clusters["unassigned_alerts"] = self._ensure_list_format(self.current_clusters["unassigned_alerts"])
    
    # Remove alerts from unassigned if they're there
    for alert_id in alert_ids:
        if alert_id in self.current_clusters["unassigned_alerts"]:
            self.current_clusters["unassigned_alerts"].remove(alert_id)