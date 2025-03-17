import json
import re
from typing import List, Dict, Any, Tuple, Union
import gym
from gym import spaces

class NetworkAlertEnvironment(gym.Env):
    """
    Environment for network alert aggregation using ReAct framework.
    This environment handles alert clustering and provides actions for exploring and analyzing alerts.
    """
    
    def __init__(self, alerts=None, topology_info=None, llm_model="gpt-4"):
        super(NetworkAlertEnvironment, self).__init__()
        
        # Store alerts and topology data
        self.current_alerts_batch = alerts if alerts else []
        self.topology_info = topology_info if topology_info else {}
        
        # LLM model to use for clustering
        self.llm_model = llm_model
        
        # Current state of clusters
        self.current_clusters = {"clusters": [], "unassigned_alerts": []}
        
        # History management
        self.clustering_history = []  # Raw history of all clustering operations
        self.function_histories = {   # Isolated histories for specific function types
            "initial_exploration": [],
            "time_based_clustering": [],
            "topology_based_clustering": [],
            "assess": [],
            "reorganize": []
        }
        self.react_history = []       # Summarized history for the ReAct framework
        
        # Recent reasoning from each clustering type (for context sharing)
        self.recent_reasoning = {
            "initial_exploration": "",
            "time_based_clustering": "",
            "topology_based_clustering": "",
            "assess": "",
            "reorganize": ""
        }
        
        # Define action space - using string commands for the ReAct framework
        self.action_space = spaces.Discrete(6)  # 6 possible actions
        
        # Define observation space - text-based state
        self.observation_space = spaces.Text(max_length=1000)  # Using max_length parameter instead of encoding
        
        # Action to text mapping
        self.action_to_text = {
            0: "InitialExploration",
            1: "TimeBasedClustering",
            2: "TopologyBasedClustering",
            3: "Reassess",
            4: "Reorganize",
            5: "Finish"
        }
        
        # History of actions and observations (for ReAct framework)
        self.history = []
    
    def reset(self, alerts=None, topology_info=None):
        """Reset the environment with new alerts and topology info if provided."""
        if alerts:
            self.current_alerts_batch = alerts
        if topology_info:
            self.topology_info = topology_info
            
        # Reset clusters and all histories
        self.current_clusters = {"clusters": [], "unassigned_alerts": []}
        self.clustering_history = []
        self.history = []
        self.react_history = []
        
        # Reset function-specific histories
        for key in self.function_histories:
            self.function_histories[key] = []
            
        # Reset recent reasoning
        for key in self.recent_reasoning:
            self.recent_reasoning[key] = ""
        
        # Create initial observation
        observation = self._get_observation()
        return observation
    
    def step(self, action):
        """
        Take a step in the environment using the provided action.
        
        Args:
            action: String in format "ActionName[parameters]" or just "ActionName"
        
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
            # Use simplified reorganize implementation
            operations = self.reorganize(action_params)
            
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
        
        return observation, reward, done, {"clusters": self.current_clusters}
    
    def _parse_action(self, action_str):
        """
        Parse an action string into action name and parameters.
        Handles both formats: "ActionName[parameters]" and "ActionName"
        """
        if "[" in action_str and "]" in action_str:
            action_name = action_str.split("[")[0]
            action_params = action_str.split("[")[1].split("]")[0]
            return action_name, action_params
        else:
            # No parameters provided
            return action_str, ""
    
    def _get_observation(self):
        """Generate an observation of the current state."""
        # Return a summary of current clusters and alerts
        return (f"Current state: {len(self.current_clusters['clusters'])} clusters, "
                f"{len(self.current_clusters['unassigned_alerts'])} unassigned alerts.")
                
    def _create_clustering_summary(self, clustering_type, clusters, response_content, max_length=500):
        """
        Create a concise summary of a clustering operation for the ReAct framework.
        
        Args:
            clustering_type: The type of clustering performed (e.g., "initial_exploration")
            clusters: The resulting clusters
            response_content: The LLM's response content
            max_length: Maximum length of the summary
            
        Returns:
            str: A concise summary of the clustering operation
        """
        # Extract key information from clusters
        num_clusters = len(clusters["clusters"]) if isinstance(clusters, dict) and "clusters" in clusters else 0
        num_unassigned = len(clusters["unassigned_alerts"]) if isinstance(clusters, dict) and "unassigned_alerts" in clusters else 0
        
        # Extract reasoning from LLM response
        reasoning = ""
        reasoning_markers = ["reasoning:", "rationale:", "chain of thought:", "explanation:"]
        lines = response_content.lower().split("\n")
        
        for i, line in enumerate(lines):
            for marker in reasoning_markers:
                if marker in line:
                    # Extract a few lines after the marker
                    reasoning_lines = lines[i:min(i+5, len(lines))]
                    reasoning = " ".join(reasoning_lines)
                    break
            if reasoning:
                break
                
        # If no explicit reasoning section, try to extract from the beginning
        if not reasoning and len(lines) > 3:
            reasoning = " ".join(lines[:3])
        
        # Limit reasoning length
        if len(reasoning) > max_length:
            reasoning = reasoning[:max_length] + "..."
            
        # Create a structured summary
        summary = f"{clustering_type.replace('_', ' ').title()}:\n"
        summary += f"- Created {num_clusters} clusters with {num_unassigned} unassigned alerts\n"
        
        # Add confidence information
        confidence_sum = 0
        confidence_count = 0
        for cluster in clusters.get("clusters", []):
            if "confidence" in cluster:
                confidence_sum += float(cluster["confidence"])
                confidence_count += 1
                
        if confidence_count > 0:
            avg_confidence = confidence_sum / confidence_count
            summary += f"- Average confidence: {avg_confidence:.2f}\n"
            
        # Add reasoning
        if reasoning:
            summary += f"- Key reasoning: {reasoning}\n"
            
        return summary
        
    def _get_clustering_summaries(self, max_summaries=3):
        """
        Get a combined summary of previous clustering steps for context.
        
        Args:
            max_summaries: Maximum number of summaries to include
            
        Returns:
            str: Combined summaries of previous clustering steps
        """
        # Get the most recent summaries
        recent_summaries = self.react_history[-max_summaries:] if len(self.react_history) > 0 else []
        
        if not recent_summaries:
            return "No previous clustering steps."
            
        # Combine summaries
        combined = "Previous clustering steps:\n\n"
        for entry in recent_summaries:
            if "summary" in entry:
                combined += entry["summary"] + "\n"
                
        return combined
    
    def _extract_assessment_summary(self, response_content):
        """
        Extract a concise assessment summary from the LLM response.
        
        Args:
            response_content: The full text response from the LLM
            
        Returns:
            str: A concise summary of the cluster assessment
        """
        # Look for sections that might contain the assessment
        assessment_markers = [
            "Assessment:", "Analysis:", "Evaluation:", "Current State:", 
            "Cluster Analysis:", "Cluster Quality:"
        ]
        
        lines = response_content.split('\n')
        assessment_lines = []
        in_assessment_section = False
        
        # Try to extract a structured assessment section
        for line in lines:
            line = line.strip()
            
            # Check if this line starts an assessment section
            if any(marker in line for marker in assessment_markers):
                in_assessment_section = True
                assessment_lines.append(line)
                continue
                
            # Check if we're leaving the assessment section (entering recommendation)
            if in_assessment_section and any(x in line for x in ["Recommendation:", "Next Action:", "Next Step:"]):
                in_assessment_section = False
                continue
                
            # Add lines if we're in the assessment section
            if in_assessment_section and line:
                assessment_lines.append(line)
        
        # If we couldn't find a structured section, take a portion of the response
        if not assessment_lines:
            # Take the first 30% of the response as a fallback
            words = response_content.split()
            assessment_size = max(50, min(200, len(words) // 3))
            assessment_lines = [' '.join(words[:assessment_size])]
        
        # Create a concise summary
        assessment_summary = '\n'.join(assessment_lines)
        
        return assessment_summary
    
    def _extract_recommendation(self, response_content):
        """
        Extract the recommended next action from the LLM response.
        
        Args:
            response_content: The full text response from the LLM
            
        Returns:
            str: The recommended next action
        """
        # Look for direct recommendation markers
        recommendation_markers = [
            "Recommendation:", "Next Action:", "Next Step:", "Recommended Action:",
            "I recommend", "You should", "The next step should be"
        ]
        
        # First, try to find a specific action recommendation
        action_types = ["TimeBasedClustering", "TopologyBasedClustering", "Reorganize", "Finish"]
        
        lines = response_content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Check if any of the action types are mentioned in this line
            for action in action_types:
                if action in line:
                    # For Reorganize actions, try to extract natural language instructions
                    if action == "Reorganize":
                        # Look for instructions after the action keyword
                        try:
                            instruction_start = line.find(action) + len(action)
                            instruction = line[instruction_start:].strip()
                            
                            # If we have instructions in the same line, include them
                            if instruction and len(instruction) > 2:  # More than just a character or two
                                return f"{action}[{instruction}]"
                            
                            # If no instructions on this line, look for them in the next few lines
                            for next_line in lines[lines.index(line)+1:lines.index(line)+5]:
                                if next_line.strip() and not any(marker in next_line for marker in recommendation_markers):
                                    return f"{action}[{next_line.strip()}]"
                        except:
                            pass
                    
                    # For other action types
                    return f"{action}[]"
        
        # If we couldn't find a specific action recommendation, look for general recommendation text
        for line in lines:
            line = line.strip()
            for marker in recommendation_markers:
                if marker in line:
                    # Return this line as the recommendation
                    return line
        
        # Default fallback if no clear recommendation is found
        return "No clear action recommendation found. Consider performing Reassess[] again with more detail."
    
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
        
        # Move alerts
        for alert_id in alert_ids:
            if alert_id in self.current_clusters["unassigned_alerts"]:
                # Add alert to cluster
                if isinstance(dst_cluster["alert_ids"], list):
                    dst_cluster["alert_ids"].append(alert_id)
                else:
                    # If alert_ids is a string, convert to list
                    alert_ids_str = dst_cluster["alert_ids"]
                    dst_cluster["alert_ids"] = json.loads(alert_ids_str) if isinstance(alert_ids_str, str) else [alert_ids_str]
                    dst_cluster["alert_ids"].append(alert_id)
                
                # Remove from unassigned
                self.current_clusters["unassigned_alerts"].remove(alert_id)
    
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
        
        # Move alerts
        for alert_id in alert_ids:
            current_alert_ids = src_cluster["alert_ids"]
            if isinstance(current_alert_ids, str):
                current_alert_ids = json.loads(current_alert_ids) if '[' in current_alert_ids else [current_alert_ids]
            
            if alert_id in current_alert_ids:
                # Remove from cluster
                current_alert_ids.remove(alert_id)
                src_cluster["alert_ids"] = current_alert_ids
                
                # Add to unassigned
                self.current_clusters["unassigned_alerts"].append(alert_id)
    
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
        
        # Move alerts
        for alert_id in alert_ids:
            current_alert_ids = src_cluster["alert_ids"]
            if isinstance(current_alert_ids, str):
                current_alert_ids = json.loads(current_alert_ids) if '[' in current_alert_ids else [current_alert_ids]
            
            if alert_id in current_alert_ids:
                # Remove from source cluster
                current_alert_ids.remove(alert_id)
                src_cluster["alert_ids"] = current_alert_ids
                
                # Add to destination cluster
                if isinstance(dst_cluster["alert_ids"], list):
                    dst_cluster["alert_ids"].append(alert_id)
                else:
                    # If alert_ids is a string, convert to list
                    alert_ids_str = dst_cluster["alert_ids"]
                    dst_cluster["alert_ids"] = json.loads(alert_ids_str) if isinstance(alert_ids_str, str) else [alert_ids_str]
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
            # Merge alert_ids
            base_alert_ids = base_cluster["alert_ids"]
            if isinstance(base_alert_ids, str):
                base_alert_ids = json.loads(base_alert_ids) if '[' in base_alert_ids else [base_alert_ids]
            
            cluster_alert_ids = cluster["alert_ids"]
            if isinstance(cluster_alert_ids, str):
                cluster_alert_ids = json.loads(cluster_alert_ids) if '[' in cluster_alert_ids else [cluster_alert_ids]
            
            base_alert_ids.extend(cluster_alert_ids)
            base_cluster["alert_ids"] = base_alert_ids
            
            # Merge source_ids
            base_source_ids = base_cluster["source_ids"]
            if isinstance(base_source_ids, str):
                base_source_ids = base_source_ids.split(", ")
            
            cluster_source_ids = cluster["source_ids"]
            if isinstance(cluster_source_ids, str):
                cluster_source_ids = cluster_source_ids.split(", ")
            
            base_source_ids.extend(cluster_source_ids)
            base_cluster["source_ids"] = ", ".join(set(base_source_ids))
            
            # Update time range
            base_cluster["time"]["start"] = min(base_cluster["time"]["start"], cluster["time"]["start"])
            base_cluster["time"]["end"] = max(base_cluster["time"]["end"], cluster["time"]["end"])
            
            # Update severity if needed
            if cluster["severity"] > base_cluster["severity"]:
                base_cluster["severity"] = cluster["severity"]
            
            # Update description
            base_cluster["Description"] += f" Combined with: {cluster['Description']}"
            
            # Update confidence - average of the two
            base_cluster["confidence"] = (base_cluster["confidence"] + cluster["confidence"]) / 2
            
            # Remove the merged cluster
            self.current_clusters["clusters"].remove(cluster)
    
    def _create_new_cluster(self, alert_ids, cluster_data):
        """Create a new cluster with the specified alerts."""
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
        
        # Remove alerts from unassigned if they're there
        for alert_id in alert_ids:
            if alert_id in self.current_clusters["unassigned_alerts"]:
                self.current_clusters["unassigned_alerts"].remove(alert_id)
    
    def _llm(self, messages, temperature=0.01, model=None, **kwargs):
        """
        Call the LLM with the provided messages.
        This is a placeholder - implement your actual LLM call here.
        """
        # This would call your LLM implementation (e.g., OpenAI API)
        # For now, return a mock response
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a mock LLM response for demonstration purposes."
                    }
                }
            ]
        }
    
    def initial_exploration(self, temperature=0.01):
        """
        Perform initial exploration clustering on the current batch of alerts.
        Uses a dedicated history for this function and creates a summary for the ReAct framework.
        """
        # Get the function-specific history
        history = self.function_histories.get("initial_exploration", [])
        
        # Serialize alert data
        try:
            current_alerts_batch_str = json.dumps(self.current_alerts_batch)
            if not isinstance(current_alerts_batch_str, str):
                raise TypeError('The serialized data is not a string')
        except Exception as e:
            print(f'Error while serializing current_alerts_batch: {e}')
            return None

        # Initialize conversation with system instructions
        system_instructions = f"""
        You are an advanced network engineer,
        
        [Your initial_exploration_prompt here]
        
        Here are some examples:
        
        [Your initial_exploration_fsl here]
        
        Please produce a detailed chain-of-thought that explains your reasoning, including any uncertainties and alternative approaches you considered.
        
        *** Before you finalize and return your result, please review the result once more with the clustering guide line and logic
        """

        user_message_text = f"""
        You are an advanced network engineer trying to cluster alerts in the network system in order to find the root cause of the cluster of alerts (event).
        
        This is a complete batch of alerts during the current time window:
        
        {current_alerts_batch_str}
        
        Please provide the output clusters and any unassigned alerts in JSON format:
        
        [Your clustering_output_json_format here]
        
        Let's cluster the alerts step by step, thinking through a detailed chain-of-thought that explains your reasoning, the clustering should be with intent to help identifying the root cause, including any uncertainties or alternative approaches you considered.
        """

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_message_text}
        ]

        # Validate message content
        for msg in messages:
            msg_content = msg['content']
            if not isinstance(msg_content, str):
                raise ValueError(f'This content is not str: {msg_content}')
        
        # Append messages to the function-specific history
        history += messages
        self.function_histories["initial_exploration"] = history
        
        # For demonstration purposes, mock the LLM call
        # In your actual implementation, you would call your LLM
        # reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
        
        # Mock reply for demonstration
        reply = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "clusters": [
                                {
                                    "cluster_id": "cluster_001",
                                    "chains of thoughts": "Initial exploration clustering thought process",
                                    "source_ids": "device1, device2",
                                    "alert_ids": [1, 2, 3],
                                    "severity": "high",
                                    "time": {"start": 1741041666, "end": 1741045666},
                                    "confidence": 0.65,
                                    "Description": "Initial cluster description"
                                }
                            ],
                            "unassigned_alerts": [4, 5]
                        })
                    }
                }
            ]
        }

        # Check for the response validity
        if 'choices' in reply and len(reply['choices']) > 0:
            response_content = reply['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": response_content})
            self.function_histories["initial_exploration"] = history
            
            # Store response in recent reasoning
            self.recent_reasoning["initial_exploration"] = response_content
            
            # Parse clusters from response
            try:
                self.current_clusters = json.loads(response_content)
            except Exception as e:
                print(f"Failed to load the clusters: {e}")
                
            # Create a summary for the ReAct framework
            summary = self._create_clustering_summary(
                "initial_exploration", 
                self.current_clusters,
                response_content
            )
            
            # Add to ReAct history
            self.react_history.append({
                "action": "InitialExploration",
                "summary": summary
            })
        else:
            print("Invalid response from API")
            return None

        return reply

    def time_based_clustering_llm(self, temperature=0.01):
        """
        Perform time-based clustering on the current batch of alerts.
        Uses a dedicated history for this function and creates a summary for the ReAct framework.
        """
        # Get the function-specific history
        history = self.function_histories.get("time_based_clustering", [])
        
        # Ensure current_clusters is a dictionary
        if not isinstance(self.current_clusters, dict):
            raise TypeError("current_clusters must be a dictionary")

        # Check for required keys
        if 'clusters' not in self.current_clusters or 'unassigned_alerts' not in self.current_clusters:
            raise KeyError("current_clusters must contain 'clusters' and 'unassigned_alerts' keys")

        # Serialize the data
        try:
            # Prepare cluster data and unassigned alerts
            clusters_data = json.dumps({'clusters': self.current_clusters['clusters']}, indent=1)
            unassigned_alerts_data = json.dumps({'unassigned_alerts': self.current_clusters['unassigned_alerts']}, indent=1)
            current_alerts_batch_str = json.dumps(self.current_alerts_batch)

            # Check that the serialized data is a string
            if not isinstance(clusters_data, str) or not isinstance(unassigned_alerts_data, str) or not isinstance(current_alerts_batch_str, str):
                raise TypeError('The serialized data is not a string')
        except Exception as e:
            print(f'Error while serializing current_clusters: {e}')
            return None
        
        # Build the system instructions for the LLM - using string concatenation to avoid nested f-strings
        previous_exploration = self.recent_reasoning["initial_exploration"][:500] if self.recent_reasoning["initial_exploration"] else "No previous clustering information available."
        
        system_instructions = """
        You are the 'time-based clustering' function in an alert aggregation system.
        
        Previous clustering reasoning:
        """ + previous_exploration + """
        
        Please produce a detailed chain-of-thought that explains your reasoning, including any uncertainties and alternative approaches you considered.
        """
        
        user_message_text = f"""
        This is complete batch of alerts during current time window:
        
        {current_alerts_batch_str}
        
        This is the current cluster in JSON format:
        
        {clusters_data}
        
        And here are the list of alert_ids of unassigned alerts that are currently not in any cluster (only the alert_ids are store, you can use the alert_id to retrieve the full alert info from current alerts batch):
        
        {unassigned_alerts_data}
        
        [Your time_based_clustering_instruction_prompt here]
        
        JSON output format:
        
        [Your clustering_output_json_format here]
        
        Please think through the problem step by step. Identify any uncertainty and unclearity.
        """

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_message_text}
        ]

        # Validate message content
        for msg in messages:
            msg_content = msg['content']
            if not isinstance(msg_content, str):
                raise ValueError(f'This content is not str: {msg_content}')
        
        # Append messages to the function-specific history
        history += messages
        self.function_histories["time_based_clustering"] = history
        
        # For demonstration purposes, mock the LLM call
        # In your actual implementation, you would call your LLM
        # reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
        
        # Mock reply for demonstration
        reply = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "clusters": [
                                {
                                    "cluster_id": "cluster_001",
                                    "chains of thoughts": "Time-based clustering thought process",
                                    "source_ids": "device1, device2",
                                    "alert_ids": [1, 2, 3],
                                    "severity": "high",
                                    "time": {"start": 1741041666, "end": 1741045666},
                                    "confidence": 0.70,
                                    "Description": "Time-based refined cluster description"
                                }
                            ],
                            "unassigned_alerts": [4, 5]
                        })
                    }
                }
            ]
        }

        # Check for the response validity
        if 'choices' in reply and len(reply['choices']) > 0:
            response_content = reply['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": response_content})
            self.function_histories["time_based_clustering"] = history
            
            # Store response in recent reasoning
            self.recent_reasoning["time_based_clustering"] = response_content
            
            # Parse clusters from response
            try:
                self.current_clusters = json.loads(response_content)
            except Exception as e:
                print(f"Failed to load the clusters: {e}")
                
            # Create a summary for the ReAct framework
            summary = self._create_clustering_summary(
                "time_based_clustering", 
                self.current_clusters,
                response_content
            )
            
            # Add to ReAct history
            self.react_history.append({
                "action": "TimeBasedClustering",
                "summary": summary
            })
        else:
            print("Invalid response from API")

        return reply
    
    def topology_based_clustering_llm(self, temperature=0.01):
        """
        Perform topology-based clustering on the current batch of alerts.
        Uses a dedicated history for this function and creates a summary for the ReAct framework.
        """
        # Get the function-specific history
        history = self.function_histories.get("topology_based_clustering", [])
        
        # Ensure current_clusters is a dictionary
        if not isinstance(self.current_clusters, dict):
            raise TypeError("current_clusters must be a dictionary")
            
        # Ensure topology_info is a dictionary
        if not isinstance(self.topology_info, dict):
            raise TypeError("topology_info must be a dictionary")

        # Check for required keys
        if 'clusters' not in self.current_clusters or 'unassigned_alerts' not in self.current_clusters:
            raise KeyError("current_clusters must contain 'clusters' and 'unassigned_alerts' keys")

        # Serialize the data
        try:
            # Prepare cluster data and unassigned alerts
            clusters_data = json.dumps({'clusters': self.current_clusters['clusters']}, indent=1)
            unassigned_alerts_data = json.dumps({'unassigned_alerts': self.current_clusters['unassigned_alerts']}, indent=1)
            topology_info_str = json.dumps(self.topology_info, separators=(',', ': '), indent=1)
            current_alerts_batch_str = json.dumps(self.current_alerts_batch)

            # Check that the serialized data is a string
            if not isinstance(clusters_data, str) or not isinstance(unassigned_alerts_data, str) or not isinstance(topology_info_str, str) or not isinstance(current_alerts_batch_str, str):
                raise TypeError('The serialized data is not a string')
        except Exception as e:
            print(f'Error while serializing data: {e}')
            return None
        
        # Gather context from previous clustering steps
        previous_reasoning = ""
        if self.recent_reasoning["time_based_clustering"]:
            previous_reasoning += f"Time-based clustering reasoning:\n{self.recent_reasoning['time_based_clustering'][:300]}\n\n"
        if self.recent_reasoning["initial_exploration"]:
            previous_reasoning += f"Initial exploration reasoning:\n{self.recent_reasoning['initial_exploration'][:300]}"
        
        # Build the system instructions for the LLM - using string concatenation to avoid nested f-strings
        system_instructions = """
        You are the 'topology-and-dependency-based clustering' function in an alert aggregation system.
        
        This is the topology data description:
        """ + topology_info_str + """
        
        Previous clustering reasoning:
        """ + previous_reasoning + """
        
        [Your topology_based_clustering_instruction_prompt here]
        
        Please produce a detailed chain-of-thought that explains your reasoning, including any uncertainties and alternative approaches you considered.
        
        *** Before you finalize and return your result, please review the result once more with the clustering guide line and logic.
        """
        
        user_message_text = f"""
        This is complete batch of alerts during current time window:
        
        {current_alerts_batch_str}
        
        This is the current cluster in JSON format:
        
        {clusters_data}
        
        And here are the list of alert_ids of unassigned alerts that are currently not in any cluster (only the alert_ids are store, you can use the alert_id to retrieve the full alert info from current alerts batch):
        
        {unassigned_alerts_data}
        
        JSON output format:
        
        [Your clustering_output_json_format here]
        
        Please think through the problem step by step. Identify any uncertainty and unclearity.
        """

        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_message_text}
        ]

        # Validate message content
        for msg in messages:
            msg_content = msg['content']
            if not isinstance(msg_content, str):
                raise ValueError(f'This content is not str: {msg_content}')
        
        # Append messages to the function-specific history
        history += messages
        self.function_histories["topology_based_clustering"] = history
        
        # For demonstration purposes, mock the LLM call
        # In your actual implementation, you would call your LLM
        # reply = self._llm(history, response_format={"type": "json_object"}, temperature=temperature, model=self.llm_model)
        
        # Mock reply for demonstration
        reply = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "clusters": [
                                {
                                    "cluster_id": "cluster_001",
                                    "chains of thoughts": "Topology-based clustering thought process",
                                    "source_ids": "device1, device2",
                                    "alert_ids": [1, 2, 3],
                                    "severity": "high",
                                    "time": {"start": 1741041666, "end": 1741045666},
                                    "confidence": 0.85,
                                    "Description": "Topology-based refined cluster description"
                                }
                            ],
                            "unassigned_alerts": [4, 5]
                        })
                    }
                }
            ]
        }

        # Check for the response validity
        if 'choices' in reply and len(reply['choices']) > 0:
            response_content = reply['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": response_content})
            self.function_histories["topology_based_clustering"] = history
            
            # Store response in recent reasoning
            self.recent_reasoning["topology_based_clustering"] = response_content
            
            # Parse clusters from response
            try:
                self.current_clusters = json.loads(response_content)
            except Exception as e:
                print(f"Failed to load the clusters: {e}")
                
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
    
    def assess_llm(self, temperature=0.01):
        """
        Enhanced assessment function that analyzes current clusters and provides strategic recommendations.
        Uses advanced prompting techniques and few-shot examples to guide the LLM's analysis.
        
        Returns:
            tuple: (response from LLM, updated history)
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
        You are an advanced network alert assessment system. Your task is to evaluate the current state of alert clusters
        and provide specific recommendations for next steps in the alert aggregation process.
        
        # Current Clustering Stats:
        - Total Alerts: {total_alerts}
        - Number of Clusters: {num_clusters}
        - Unassigned Alerts: {num_unassigned}
        - Average Confidence: {avg_confidence:.2f}
        
        # Previous Steps:
        {clustering_context}
        
        # Assessment Guidelines:
        
        1. Examine the current clusters focusing on:
        - Cluster coherence: Are alerts appropriately grouped based on time and topology?
        - Unassigned alerts: Could any be included in existing clusters?
        - Potential merges: Are there clusters that should be combined?
        - Potential splits: Are there clusters containing unrelated alerts?
        
        2. For each group of unassigned alerts, determine:
        - If they should be added to an existing cluster
        - If they should form a new cluster
        - What relationships exist between them
        
        3. Look for alert patterns such as:
        - Cascading failures (sequential alerts on connected devices)
        - Common root cause indicators (multiple devices with similar errors)
        - Isolated incidents vs. systemic issues
        
        # Recommendation Guidelines:
        
        After your assessment, provide ONE clear recommendation for the NEXT ACTION to take:
        
        1. TimeBasedClustering: Recommend if temporal analysis could reveal patterns missed so far. Especially useful when:
        - Many alerts have similar timestamps but weren't grouped
        - There are potential cascading failures indicated by sequential timestamps
        
        2. TopologyBasedClustering: Recommend if network relationships could improve clustering. Especially useful when:
        - Alerts are from potentially connected devices
        - Clusters might be related through network topology
        - There are cross-segment or cross-region dependencies
        
        3. Reorganize: Recommend specific changes using natural language instructions. Be precise and use this for:
        - Moving specific unassigned alerts to an existing cluster
        - Creating a new cluster with specific alerts
        - Merging specific clusters that appear related
        
        4. Finish: Recommend only when clusters are well-formed and complete. Appropriate when:
        - All alerts are assigned to meaningful clusters
        - Clusters have clear, coherent patterns
        - No obvious improvements can be made
        
        # Important: Reorganize Recommendation Format
        
        When recommending Reorganize, use SIMPLE, CLEAR language specifying exactly what should be done:
        - "Move alerts 1001, 1002 from unassigned to cluster_003."
        - "Create a new cluster with alerts 2001, 2002, 2003."
        - "Merge clusters 001 and 004."
        
        Keep reorganization instructions SIMPLE and FOCUSED. If multiple operations are needed, prioritize the most important one.
        
        # Example Assessment and Recommendations:
        
        ## Example 1: Moving Unassigned Alerts
        
        Assessment:
        The current clustering shows 3 well-formed clusters. There are 2 unassigned alerts (1001, 1002) that share temporal proximity with Cluster_001 (within 5 minutes of other alerts in that cluster) and appear to be from devices in the same network segment based on source information.
        
        Recommendation:
        Reorganize[Move alerts 1001, 1002 from unassigned to cluster_001.]
        
        ## Example 2: Creating New Cluster
        
        Assessment:
        There are 4 clusters that appear appropriate. Among the 5 unassigned alerts, 3 of them (2001, 2002, 2003) show a clear pattern of authentication failures occurring within minutes of each other, but don't relate to existing clusters. The other 2 unassigned alerts are unrelated to each other or existing clusters.
        
        Recommendation:
        Reorganize[Create a new cluster with alerts 2001, 2002, 2003.]
        
        ## Example 3: Merging Clusters
        
        Assessment:
        Clusters 002 and 004 appear to be related to the same network outage. They contain alerts from connected devices, with Cluster_002 showing router failures and Cluster_004 showing downstream switch errors occurring 3-5 minutes later. Despite the time gap, they represent the same incident and should be merged.
        
        Recommendation:
        Reorganize[Merge clusters 002 and 004.]
        
        ## Example 4: Recommending Further Clustering
        
        Assessment:
        The current clusters are primarily based on initial exploration. There are 8 unassigned alerts, most of which show timing patterns that might indicate relationships, but weren't captured in the initial grouping. Several alerts occurred within the same 10-minute window and might be related.
        
        Recommendation:
        TimeBasedClustering
        
        ## Example 5: Finishing Assessment
        
        Assessment:
        All alerts are assigned to appropriate clusters. The 5 clusters represent distinct events: a router failure with downstream impacts (Cluster_001), two separate security incidents (Clusters 002 and 003), a storage subsystem failure (Cluster_004), and a scheduled maintenance event (Cluster_005). Confidence scores are high across all clusters.
        
        Recommendation:
        Finish
        
        Be decisive and provide a single clear recommendation based on your comprehensive assessment.
        """
        
        # Create user message
        user_message = f"""
        Please assess the current state of alert clusters and provide a recommendation for the next step.
        
        CURRENT ALERT BATCH:
        {current_alerts_batch_str}
        
        CURRENT CLUSTERS:
        {clusters_data}
        
        UNASSIGNED ALERTS:
        {unassigned_alerts_data}
        
        TOPOLOGY INFORMATION:
        {topology_info_str}
        
        Please provide:
        1. A detailed assessment of the current clusters
        2. Analysis of any unassigned alerts and potential relationships
        3. A specific recommendation for the next action to take (TimeBasedClustering, TopologyBasedClustering, Reorganize with specific instructions, or Finish)
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
            Simple implementation of reorganization based on clear, specific operations.
            
            Args:
                instructions: String containing reorganization instructions
                
            Returns:
                list: Operations performed
            """
            operations_performed = []
            
            # First, look for and execute cluster creation operations
            if "create" in instructions.lower() and "cluster" in instructions.lower():
                # Extract potential cluster ID
                import re
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
            
            # Look for and execute move operations
            if "move" in instructions.lower() and "alert" in instructions.lower() and "to" in instructions.lower():
                # Extract alert IDs
                alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', instructions)]
                
                # Determine source and destination
                if "unassigned" in instructions.lower() and "cluster" in instructions.lower():
                    # Find the cluster ID
                    cluster_match = re.search(r'cluster[_\s]*(\d+)', instructions)
                    if cluster_match:
                        cluster_num = int(cluster_match.group(1))
                        cluster_id = f"cluster_{cluster_num:03d}"
                        
                        # Determine direction
                        if instructions.find("unassigned") < instructions.find("cluster"):
                            # Moving from unassigned to cluster
                            # Find the destination cluster
                            dest_cluster = None
                            for cluster in self.current_clusters["clusters"]:
                                if cluster["cluster_id"] == cluster_id:
                                    dest_cluster = cluster
                                    break
                            
                            # If the cluster exists, move alerts to it
                            if dest_cluster:
                                for alert_id in alert_ids:
                                    if alert_id in self.current_clusters["unassigned_alerts"]:
                                        # Add to cluster
                                        if "alert_ids" not in dest_cluster:
                                            dest_cluster["alert_ids"] = []
                                        dest_cluster["alert_ids"].append(alert_id)
                                        # Remove from unassigned
                                        self.current_clusters["unassigned_alerts"].remove(alert_id)
                                
                                operations_performed.append(f"Moved {len(alert_ids)} alerts from unassigned to {cluster_id}")
                        else:
                            # Moving from cluster to unassigned
                            # Find the source cluster
                            source_cluster = None
                            for cluster in self.current_clusters["clusters"]:
                                if cluster["cluster_id"] == cluster_id:
                                    source_cluster = cluster
                                    break
                            
                            # If the cluster exists, move alerts from it
                            if source_cluster and "alert_ids" in source_cluster:
                                for alert_id in alert_ids:
                                    if alert_id in source_cluster["alert_ids"]:
                                        # Remove from cluster
                                        source_cluster["alert_ids"].remove(alert_id)
                                        # Add to unassigned
                                        self.current_clusters["unassigned_alerts"].append(alert_id)
                                
                                operations_performed.append(f"Moved {len(alert_ids)} alerts from {cluster_id} to unassigned")
            
            # Look for and execute merge operations
            if "merge" in instructions.lower() and "cluster" in instructions.lower():
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
                    
                    # Find the clusters
                    clusters_to_merge = []
                    for cluster_id in cluster_ids:
                        for cluster in self.current_clusters["clusters"]:
                            if cluster["cluster_id"] == cluster_id:
                                clusters_to_merge.append(cluster)
                                break
                    
                    # If we found both clusters, merge them
                    if len(clusters_to_merge) == 2:
                        base_cluster = clusters_to_merge[0]
                        merge_cluster = clusters_to_merge[1]
                        
                        # Combine alert IDs
                        if "alert_ids" not in base_cluster:
                            base_cluster["alert_ids"] = []
                        if "alert_ids" in merge_cluster:
                            base_cluster["alert_ids"].extend(merge_cluster["alert_ids"])
                        
                        # Remove the merged cluster
                        self.current_clusters["clusters"].remove(merge_cluster)
                        
                        operations_performed.append(f"Merged {cluster_ids[1]} into {cluster_ids[0]}")
            
            # If nothing happened, report it
            if not operations_performed:
                operations_performed.append("No operations were identified from the instructions")
            
            return operations_performed
            
    def reorganize_llm(self, instructions, recent_assessment=None, temperature=0.01):
        """
        Implement reorganization based on natural language instructions.
        
        Args:
            instructions: Natural language instructions for reorganization
            recent_assessment: The most recent assessment recommendation (if available)
            temperature: Temperature for LLM sampling
            
        Returns:
            tuple: (response from LLM, updated history, changes made)
        """
        # Get the function-specific history
        history = self.function_histories.get("reorganize", [])
        
        # Validate current_clusters is a dictionary
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
            
            # Verify serialization
            if not isinstance(clusters_data, str) or not isinstance(unassigned_alerts_data, str):
                raise TypeError('The serialized data is not a string')
        except Exception as e:
            print(f'Error while serializing data: {e}')
            return None, history, None
            
        # Create system instructions with few-shot examples
        system_instructions = """
        You are a network alert clustering assistant. Your task is to implement reorganization instructions for alert clusters.
        
        Based on the current clusters and the given instructions, you will:
        1. Parse the reorganization instructions
        2. Convert them to specific operations on clusters
        3. Describe exactly what changes should be made
        
        Stick closely to the instructions provided, especially if they come from a recent assessment.
        
        EXAMPLES:
        
        Example 1:
        Current clusters: [cluster_001, cluster_002]
        Unassigned alerts: [1045, 1046]
        Assessment recommendation: "Move alerts 1045 and 1046 from unassigned to cluster_001 since they show temporal correlation."
        Reorganization instructions: "Move alerts 1045 and 1046 from unassigned to cluster_001."
        
        Operations to perform:
        1. Move alert 1045 from unassigned to cluster_001
        2. Move alert 1046 from unassigned to cluster_001
        
        Example 2:
        Current clusters: [cluster_001, cluster_002, cluster_003]
        Unassigned alerts: []
        Assessment recommendation: "Merge clusters 002 and 003 as they represent the same underlying issue."
        Reorganization instructions: "Merge clusters 002 and 003."
        
        Operations to perform:
        1. Merge cluster_002 and cluster_003 (keeping cluster_002 as the base)
        
        Example 3:
        Current clusters: [cluster_001]
        Unassigned alerts: [2001, 2002, 2003]
        Assessment recommendation: "Create a new cluster for alerts 2001 and 2002 as they represent a separate issue."
        Reorganization instructions: "Create a new cluster with alerts 2001 and 2002."
        
        Operations to perform:
        1. Create a new cluster (cluster_002)
        2. Move alerts 2001 and 2002 from unassigned to cluster_002
        
        Be precise and provide a clear list of operations to perform. Don't add operations that weren't requested.
        """
        
        # Add the recent assessment context if available
        if recent_assessment:
            recent_assessment_context = f"""
            The most recent assessment provided the following recommendation:
            {recent_assessment}
            
            Please ensure your reorganization aligns with this assessment.
            """
            system_instructions += recent_assessment_context
        
        # Create user message
        user_message = f"""
        CURRENT CLUSTERS:
        {clusters_data}
        
        UNASSIGNED ALERTS:
        {unassigned_alerts_data}
        
        REORGANIZATION INSTRUCTIONS:
        {instructions}
        
        Please provide:
        1. A clear list of operations to perform
        2. A brief explanation of why these changes make sense
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
        self.function_histories["reorganize"] = history
        
        # Call the LLM
        reply = self._llm(history, temperature=temperature, model=self.llm_model)
        
        # Validate response
        if 'choices' in reply and len(reply['choices']) > 0:
            response_content = reply['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": response_content})
            self.function_histories["reorganize"] = history
            
            # Store response in recent reasoning
            self.recent_reasoning["reorganize"] = response_content
            
            # Parse operations from the response and implement them
            try:
                changes_made = self._parse_and_implement_reorganize(response_content)
                
                # Create a summary for the ReAct framework
                summary = f"Reorganization:\n- {len(changes_made)} operations performed\n"
                for op in changes_made:
                    summary += f"- {op}\n"
                
                # Add to ReAct history
                self.react_history.append({
                    "action": "Reorganize",
                    "summary": summary
                })
                
                return reply, history, changes_made
            except Exception as e:
                print(f"Error implementing reorganization: {e}")
                return reply, history, ["Error implementing changes: " + str(e)]
        else:
            print("Invalid response from LLM")
            return None, history, None
    
    def _parse_and_implement_reorganize(self, response_content):
        """
        Parse the LLM's reorganization response and implement the specified operations.
        
        Args:
            response_content: The LLM's response content
            
        Returns:
            list: Description of changes made
        """
        changes_made = []
        print(f"DEBUG: Parsing reorganize instructions: {response_content[:100]}...")
        
        # First, try to identify and execute cluster creation operations before other operations
        # since some operations might depend on newly created clusters
        
        # Pattern for creating clusters - more flexible pattern that matches various formats
        create_pattern = r"(?:create|make|add)\s+(?:a\s+)?(?:new\s+)?cluster(?:\s+(?:with\s+id\s+|id\s+|with\s+|named\s+|called\s+)?(\w+))?(?:\s+with\s+alert[s]?\s+(\d+(?:,\s*\d+)*))?|create\s+cluster_(\d+)\s+with\s+alerts\s+(\d+(?:,\s*\d+)*)"
        
        # Look for "cluster_NNN" pattern to identify specific cluster IDs
        cluster_id_pattern = r"cluster[_\s]*(\d+)"
        
        # First, handle cluster creation operations to ensure they exist before moving alerts
        create_operations_found = False
        create_matches = re.finditer(create_pattern, response_content.lower())
        
        for match in create_matches:
            create_operations_found = True
            print(f"DEBUG: Found create match: {match.group(0)}")
            print(f"DEBUG: Match groups: {match.groups()}")
            
            # Extract cluster ID and alert IDs from different possible group patterns
            groups = match.groups()
            
            # Look for explicit cluster ID
            cluster_id = None
            
            # Check if a cluster ID is specified in the match groups
            if len(groups) >= 4 and groups[2] is not None:
                # Pattern: create cluster_123 with alerts 1,2,3
                cluster_id = f"cluster_{groups[2]}"
            elif groups[0] is not None:
                # Pattern: create a new cluster cluster_123 with alerts...
                cluster_id = groups[0]
            
            # If no explicit cluster ID found in the match, check for cluster ID pattern in context
            if not cluster_id:
                # Look for "cluster_NNN" pattern anywhere in this create command
                create_text = match.group(0)
                cluster_id_match = re.search(cluster_id_pattern, create_text)
                if cluster_id_match:
                    cluster_num = cluster_id_match.group(1)
                    cluster_id = f"cluster_{int(cluster_num):03d}"
            
            # If still no cluster ID, generate one
            if not cluster_id:
                cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
            
            # Normalize cluster ID
            if not cluster_id.startswith("cluster_") and cluster_id.isdigit():
                cluster_id = f"cluster_{int(cluster_id):03d}"
                
            # Extract alert IDs if provided in the match
            alert_ids_str = ""
            if len(groups) > 1 and groups[1] is not None:
                alert_ids_str = groups[1]
            elif len(groups) > 3 and groups[3] is not None:
                alert_ids_str = groups[3]
            
            # If no alert IDs extracted from match groups, try to find them in context
            if not alert_ids_str:
                # Find alert IDs in this sentence or nearby
                create_context = response_content[max(0, match.start() - 100):min(len(response_content), match.end() + 100)]
                alert_ids_pattern = r"alert[s]?\s+(\d+(?:,\s*\d+)*)"
                alert_match = re.search(alert_ids_pattern, create_context.lower())
                if alert_match:
                    alert_ids_str = alert_match.group(1)
            
            # Parse alert IDs if provided
            alert_ids = []
            if alert_ids_str:
                # Parse comma-separated numbers, handling potential spaces
                alert_ids = [int(aid.strip()) for aid in re.findall(r'\d+', alert_ids_str)]
            
            # If no alert IDs were found, look for numbers that appear to be alert IDs
            if not alert_ids:
                # Look for numbers with 6+ digits that could be alert IDs
                potential_alert_ids = [int(num) for num in re.findall(r'\b\d{6,}\b', create_context)]
                if potential_alert_ids:
                    alert_ids = potential_alert_ids
            
            print(f"DEBUG: Creating cluster {cluster_id} with {len(alert_ids)} alerts")
            
            # Implement the create
            try:
                cluster_data = {
                    "cluster_id": cluster_id,
                    "chains of thoughts": "Manually created cluster",
                    "source_ids": "",
                    "confidence": 0.5,
                    "severity": "medium",
                    "time": {"start": 0, "end": 0},
                    "Description": "Manually created cluster"
                }
                self._create_new_cluster(alert_ids, cluster_data)
                changes_made.append(f"Created new cluster {cluster_id} with {len(alert_ids)} alerts")
            except Exception as e:
                error_msg = f"Error creating cluster: {str(e)}"
                print(f"DEBUG: {error_msg}")
                changes_made.append(error_msg)
        
        # Now process other operations (moves, merges) AFTER clusters are created
        
        # Patterns for moves and merges
        move_pattern = r"(?:move|add)\s+alert[s]?\s+(\d+(?:,\s*\d+)*)\s+from\s+(\w+)\s+to\s+(\w+)"
        merge_pattern = r"(?:merge|combine)\s+cluster[s]?\s+(\w+)(?:\s+and|\s*,\s*)\s+(\w+)"
        
        # Find all move operations
        print(f"DEBUG: Looking for move operations")
        move_matches = re.finditer(move_pattern, response_content.lower())
        for match in move_matches:
            alert_ids_str, src_cluster, dst_cluster = match.groups()
            print(f"DEBUG: Found move match: {match.group(0)}")
            print(f"DEBUG: Alert IDs: {alert_ids_str}, From: {src_cluster}, To: {dst_cluster}")
            
            # Parse alert IDs
            alert_ids = [int(aid.strip()) for aid in re.findall(r'\d+', alert_ids_str)]
            
            # Normalize cluster names
            if src_cluster.startswith("cluster_"):
                src_cluster_id = src_cluster
            elif src_cluster.isdigit():
                src_cluster_id = f"cluster_{int(src_cluster):03d}"
            else:
                src_cluster_id = src_cluster
                
            if dst_cluster.startswith("cluster_"):
                dst_cluster_id = dst_cluster
            elif dst_cluster.isdigit():
                dst_cluster_id = f"cluster_{int(dst_cluster):03d}"
            else:
                dst_cluster_id = dst_cluster
            
            # Implement the move
            try:
                if src_cluster_id == "unassigned":
                    self._move_from_unassigned_to_cluster(alert_ids, dst_cluster_id)
                    changes_made.append(f"Moved {len(alert_ids)} alerts from unassigned to {dst_cluster_id}")
                elif dst_cluster_id == "unassigned":
                    self._move_from_cluster_to_unassigned(alert_ids, src_cluster_id)
                    changes_made.append(f"Moved {len(alert_ids)} alerts from {src_cluster_id} to unassigned")
                else:
                    self._move_between_clusters(alert_ids, src_cluster_id, dst_cluster_id)
                    changes_made.append(f"Moved {len(alert_ids)} alerts from {src_cluster_id} to {dst_cluster_id}")
            except Exception as e:
                error_msg = f"Error moving alerts: {str(e)}"
                print(f"DEBUG: {error_msg}")
                changes_made.append(error_msg)
        
        # Find all merge operations
        print(f"DEBUG: Looking for merge operations")
        merge_matches = re.finditer(merge_pattern, response_content.lower())
        for match in merge_matches:
            cluster_id1, cluster_id2 = match.groups()
            print(f"DEBUG: Found merge match: {match.group(0)}")
            print(f"DEBUG: Clusters to merge: {cluster_id1} and {cluster_id2}")
            
            # Normalize cluster names
            if cluster_id1.startswith("cluster_"):
                cluster_id1_norm = cluster_id1
            elif cluster_id1.isdigit():
                cluster_id1_norm = f"cluster_{int(cluster_id1):03d}"
            else:
                cluster_id1_norm = cluster_id1
                
            if cluster_id2.startswith("cluster_"):
                cluster_id2_norm = cluster_id2
            elif cluster_id2.isdigit():
                cluster_id2_norm = f"cluster_{int(cluster_id2):03d}"
            else:
                cluster_id2_norm = cluster_id2
            
            # Implement the merge
            try:
                self._merge_clusters([cluster_id1_norm, cluster_id2_norm])
                changes_made.append(f"Merged clusters {cluster_id1_norm} and {cluster_id2_norm}")
            except Exception as e:
                error_msg = f"Error merging clusters: {str(e)}"
                print(f"DEBUG: {error_msg}")
                changes_made.append(error_msg)
        
        # If no operations were found but there's text indicating changes
        if not changes_made and any(op in response_content.lower() for op in ["move", "merge", "create"]):
            print(f"DEBUG: No standard operations matched, trying fallback parsing")
            # Try more lenient parsing as a fallback
            fallback_changes = self._fallback_parse_reorganize(response_content)
            changes_made.extend(fallback_changes)
            
        # If still no changes made, try one more direct approach for cluster creation
        if not changes_made and "create" in response_content.lower() and "cluster" in response_content.lower():
            print(f"DEBUG: Attempting direct cluster creation pattern matching")
            # Special case for "Create a new cluster with alerts X, Y, Z"
            try:
                # Direct extraction of alert IDs
                alert_ids = [int(num) for num in re.findall(r'\d+', response_content) 
                             if len(str(num)) > 5]  # Assuming alert IDs are large numbers
                
                # Check for cluster ID specification
                cluster_id_match = re.search(r'cluster[_\s]*(\d+)', response_content)
                if cluster_id_match:
                    cluster_id = f"cluster_{int(cluster_id_match.group(1)):03d}"
                else:
                    cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
                
                print(f"DEBUG: Direct creation - Cluster ID: {cluster_id}, Alert IDs: {alert_ids[:5]}...")
                
                # Create the cluster
                cluster_data = {
                    "cluster_id": cluster_id,
                    "chains of thoughts": "Manually created cluster via direct pattern",
                    "source_ids": "",
                    "confidence": 0.5,
                    "severity": "medium",
                    "time": {"start": 0, "end": 0},
                    "Description": "Manually created cluster"
                }
                self._create_new_cluster(alert_ids, cluster_data)
                changes_made.append(f"Created new cluster {cluster_id} with {len(alert_ids)} alerts (direct method)")
            except Exception as e:
                error_msg = f"Error in direct cluster creation: {str(e)}"
                print(f"DEBUG: {error_msg}")
                changes_made.append(error_msg)
        
        return changes_made
        
    def _fallback_parse_reorganize(self, response_content):
        """
        Fallback parsing for reorganization when regex patterns fail to match.
        Looks for key phrases and tries to extract operations more liberally.
        
        Args:
            response_content: The LLM's response content
            
        Returns:
            list: Description of changes made
        """
        changes_made = []
        lines = response_content.lower().split('\n')
        print(f"DEBUG: Running fallback parser on {len(lines)} lines")
        
        # Scan for specific patterns related to cluster operations across all lines
        response_text = response_content.lower()
        
        # Detect cluster_id pattern
        cluster_ids = re.findall(r'cluster[_\s]*(\d+)', response_text)
        print(f"DEBUG: Found potential cluster IDs: {cluster_ids}")
        
        # Detect alert IDs - looking for 8-9 digit numbers (typical for alert IDs)
        alert_ids_all = [int(num) for num in re.findall(r'\b\d{6,9}\b', response_text)]
        print(f"DEBUG: Found potential alert IDs: {len(alert_ids_all)} IDs")
        
        # Process each line separately
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"DEBUG: Processing line {i}: {line[:50]}...")
            
            # Simple move operation
            if "move" in line and "alert" in line and "to" in line:
                # Extract alert IDs - look for numbers
                alert_ids = [int(n) for n in re.findall(r'\d+', line) if 100000 <= int(n) < 1000000000]  # Typical alert ID range
                
                # Skip if no alert IDs found
                if not alert_ids:
                    continue
                
                print(f"DEBUG: Found move operation with alert IDs: {alert_ids}")
                
                # Extract cluster names - look for "cluster" or "unassigned"
                if "unassigned" in line and "cluster" in line:
                    # Determine direction
                    if line.find("unassigned") < line.find("cluster"):
                        # From unassigned to cluster
                        cluster_matches = re.findall(r'cluster[_\s]*(\d+)', line)
                        if cluster_matches:
                            dst_cluster = f"cluster_{int(cluster_matches[0]):03d}"
                            try:
                                self._move_from_unassigned_to_cluster(alert_ids, dst_cluster)
                                changes_made.append(f"Moved {len(alert_ids)} alerts from unassigned to {dst_cluster} (fallback)")
                            except Exception as e:
                                error_msg = f"Error in fallback move: {str(e)}"
                                print(f"DEBUG: {error_msg}")
                                changes_made.append(error_msg)
                    else:
                        # From cluster to unassigned
                        cluster_matches = re.findall(r'cluster[_\s]*(\d+)', line)
                        if cluster_matches:
                            src_cluster = f"cluster_{int(cluster_matches[0]):03d}"
                            try:
                                self._move_from_cluster_to_unassigned(alert_ids, src_cluster)
                                changes_made.append(f"Moved {len(alert_ids)} alerts from {src_cluster} to unassigned (fallback)")
                            except Exception as e:
                                error_msg = f"Error in fallback move: {str(e)}"
                                print(f"DEBUG: {error_msg}")
                                changes_made.append(error_msg)
            
            # Simple merge operation
            elif "merge" in line and "cluster" in line:
                cluster_matches = re.findall(r'cluster[_\s]*(\d+)', line)
                if len(cluster_matches) >= 2:
                    cluster_ids = [f"cluster_{int(cid):03d}" for cid in cluster_matches[:2]]
                    try:
                        self._merge_clusters(cluster_ids)
                        changes_made.append(f"Merged clusters {cluster_ids[0]} and {cluster_ids[1]} (fallback)")
                    except Exception as e:
                        error_msg = f"Error in fallback merge: {str(e)}"
                        print(f"DEBUG: {error_msg}")
                        changes_made.append(error_msg)
            
            # Simple create operation
            elif "create" in line and "cluster" in line:
                # Look for specific cluster number for new cluster
                new_cluster_id = None
                cluster_number_match = re.search(r'cluster[_\s]*(\d+)', line)
                if cluster_number_match:
                    new_cluster_id = f"cluster_{int(cluster_number_match.group(1)):03d}"
                else:
                    # Generate a new ID if none specified
                    new_cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
                
                # Look for alert IDs in this line or next few lines
                alert_ids = []
                
                # Check current line first
                alert_ids = [int(n) for n in re.findall(r'\d+', line) if 100000 <= int(n) < 1000000000]
                
                # If no alert IDs on this line, check next few lines
                if not alert_ids:
                    search_limit = min(i + 5, len(lines))
                    for j in range(i + 1, search_limit):
                        next_line = lines[j].strip()
                        if "alert" in next_line:
                            alert_ids = [int(n) for n in re.findall(r'\d+', next_line) if 100000 <= int(n) < 1000000000]
                            if alert_ids:
                                break
                
                # If no alert IDs found after searching, look in the entire text for large numbers
                if not alert_ids and alert_ids_all:
                    print(f"DEBUG: No alert IDs found in nearby lines, using all alert IDs from text")
                    alert_ids = alert_ids_all
                
                if new_cluster_id:
                    try:
                        print(f"DEBUG: Creating new cluster {new_cluster_id} with {len(alert_ids)} alerts (fallback)")
                        cluster_data = {
                            "cluster_id": new_cluster_id,
                            "chains of thoughts": "Manually created cluster via fallback parser",
                            "source_ids": "",
                            "confidence": 0.5,
                            "severity": "medium",
                            "time": {"start": 0, "end": 0},
                            "Description": "Manually created cluster"
                        }
                        self._create_new_cluster(alert_ids, cluster_data)
                        changes_made.append(f"Created new cluster {new_cluster_id} with {len(alert_ids)} alerts (fallback)")
                    except Exception as e:
                        error_msg = f"Error in fallback cluster creation: {str(e)}"
                        print(f"DEBUG: {error_msg}")
                        changes_made.append(error_msg)
        
        # Super fallback mode - if we still haven't found any operations
        if not changes_made:
            print(f"DEBUG: No operations found in line-by-line parsing, attempting super fallback mode")
            
            # For cluster creation, if "create" and "cluster" are present anywhere
            if "create" in response_text and "cluster" in response_text:
                new_cluster_id = f"cluster_{len(self.current_clusters['clusters']) + 1:03d}"
                
                # If "cluster_004" or similar is specified anywhere
                for cluster_id in cluster_ids:
                    if int(cluster_id) > len(self.current_clusters['clusters']):
                        new_cluster_id = f"cluster_{int(cluster_id):03d}"
                        break
                
                try:
                    print(f"DEBUG: Super fallback - creating cluster {new_cluster_id} with {len(alert_ids_all)} alerts")
                    cluster_data = {
                        "cluster_id": new_cluster_id,
                        "chains of thoughts": "Manually created cluster via super fallback",
                        "source_ids": "",
                        "confidence": 0.5,
                        "severity": "medium",
                        "time": {"start": 0, "end": 0},
                        "Description": "Manually created cluster"
                    }
                    self._create_new_cluster(alert_ids_all, cluster_data)
                    changes_made.append(f"Created new cluster {new_cluster_id} with {len(alert_ids_all)} alerts (super fallback)")
                except Exception as e:
                    error_msg = f"Error in super fallback cluster creation: {str(e)}"
                    print(f"DEBUG: {error_msg}")
                    changes_made.append(error_msg)
        
        return changes_made