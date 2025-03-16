import ast
import json
import time
import gym
import requests

# --- Our previously defined alert correlation functions ---
# (For brevity, these functions use OpenAI API calls as shown in previous examples.)
# They are: initial_reasoning(), get_topology_data(), refine_clustering(), assess_impact_and_generate_recommendations()

def initial_reasoning(alerts):
    system_prompt = (
        "You are an AI event correlation agent. Your task is to perform initial reasoning on a batch of alerts "
        "that are pre-grouped by location. Each alert has metadata: timestamp, device, alert_message, and location. "
        "Analyze the alerts, identify common patterns (e.g., repeated device references, overlapping timestamps, similar error messages), "
        "and produce preliminary clusters. For alerts that seem ambiguous, flag them for later topology verification. "
        "Output your result as a JSON object with two keys: 'preliminary_clusters' (a list of clusters, each with 'cluster_id', "
        "'devices' (list), and 'notes') and 'unassigned_alerts' (a list of alert_ids).\n\n"
        "Few-shot Example:\n"
        "Input: Two alerts: {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
        "       {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
        "Output: {\"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
        "\"notes\": \"AP-001 likely dependent on Switch-1.\"} ], \"unassigned_alerts\": []}.\n\n"
        "Ensure every alert is either grouped or flagged."
    )
    
    user_prompt = (
        "Below is a batch of alerts in JSON format:\n"
        f"{json.dumps({'alerts': alerts}, indent=2)}\n\n"
        "Please analyze these alerts and output your preliminary clustering in the specified JSON format."
    )
    
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers={"Authorization": f"Bearer YOUR_API_KEY_HERE",
                                      "Content-Type": "application/json"},
                             json={
                                 "model": "gpt-4",
                                 "messages": [
                                     {"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}
                                 ],
                                 "temperature": 0.3,
                                 "max_tokens": 600
                             })
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Initial Reasoning Result ===")
    print(result)
    return result

def get_topology_data(devices):
    # Simulated topology lookup: in practice, this would call an API
    topology = {}
    for device in devices:
        if device == "Switch-1":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-001", "AP-002"]}
        elif device == "Switch-2":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-101"]}
        else:
            topology[device] = {"upstream": [], "downstream": []}
    return topology

def refine_clustering(preliminary_clusters, topology_data):
    system_prompt = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine the clustering. For each preliminary cluster, compare its devices against the topology data. "
        "If multiple clusters share a common upstream device, merge them; if the topology data indicates that a device "
        "belongs to a cluster (for example, it is downstream of the cluster's core device), adjust the cluster accordingly. "
        "Output your refined clustering as a JSON object with a 'refined_clusters' key (a list of clusters, each with "
        "'cluster_id', 'devices', and 'notes' explaining your decisions).\n\n"
        "Few-shot Example:\n"
        "Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"notes\": \"Initial cluster\"}\n"
        "Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}\n\n"
        "Ensure every alert is accounted for and provide a brief rationale for any changes."
    )
    
    user_prompt = (
        "Preliminary Clusters:\n"
        f"{json.dumps(preliminary_clusters, indent=2)}\n\n"
        "Topology Data:\n"
        f"{json.dumps(topology_data, indent=2)}\n\n"
        "Please refine the clustering using the topology data and output your result in the specified JSON format."
    )
    
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers={"Authorization": f"Bearer YOUR_API_KEY_HERE",
                                      "Content-Type": "application/json"},
                             json={
                                 "model": "gpt-4",
                                 "messages": [
                                     {"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}
                                 ],
                                 "temperature": 0.3,
                                 "max_tokens": 600
                             })
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Refined Clustering Result ===")
    print(result)
    return result

def assess_impact_and_generate_recommendations(refined_clusters):
    system_prompt = (
        "You are an AI event correlation agent. Your task now is to finalize the alert correlation by assessing "
        "each refined cluster. For each cluster, evaluate the impact by considering the number of alerts and the criticality "
        "of the devices. Assign a severity level (High, Medium, Low, or Unknown) and generate actionable recommendations "
        "for further investigation. Output your final report as a JSON object with a 'situations' key, where each situation includes:\n"
        " - situation_id\n - location (if available)\n - devices\n - severity\n - recommendations\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"severity\": \"High\", \"recommendations\": \"Check power and connectivity of Switch-1.\"} ]}\n\n"
        "Make sure every refined cluster is represented."
    )
    
    user_prompt = (
        "Below are the refined clusters from the previous step:\n"
        f"{json.dumps(refined_clusters, indent=2)}\n\n"
        "Please assess each cluster and produce the final alert correlation report in the specified JSON format."
    )
    
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers={"Authorization": f"Bearer YOUR_API_KEY_HERE",
                                      "Content-Type": "application/json"},
                             json={
                                 "model": "gpt-4",
                                 "messages": [
                                     {"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}
                                 ],
                                 "temperature": 0.3,
                                 "max_tokens": 600
                             })
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Final Alert Correlation Report ===")
    print(result)
    return result

# --- Define a Gym Environment for Alert Correlation using ReAct ---

class textSpace(gym.spaces.Space):
    def contains(self, x) -> bool:
        return isinstance(x, str)

class AlertCorrelationEnv(gym.Env):
    def __init__(self, alerts_batch):
        super().__init__()
        self.alerts_batch = alerts_batch  # raw alerts for this episode
        self.observation_space = self.action_space = textSpace()
        self.reset()
        
    def reset(self, seed=None, return_info=False, options=None):
        self.current_stage = "start"  # stages: start, preliminary, topology, refined, assessed, finished
        self.preliminary_clusters = None
        self.topology_data = None
        self.refined_clusters = None
        self.final_report = None
        self.thoughts = []
        self.obs = ("Start initial reasoning on the provided alert batch. "
                    "Use action 'initial_reasoning[]' to begin.")
        return self.obs

    def step(self, action):
        action = action.strip()
        reward = 0
        done = False
        info = {}
        
        if action.startswith("initial_reasoning[") and action.endswith("]"):
            result_str = initial_reasoning(self.alerts_batch)
            try:
                self.preliminary_clusters = json.loads(result_str)
            except Exception as e:
                print("Parsing error:", e)
                self.preliminary_clusters = {
                    "preliminary_clusters": [
                        {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"],
                         "notes": "Multiple alerts reference Switch-1."}
                    ],
                    "unassigned_alerts": []
                }
            self.current_stage = "preliminary"
            self.obs = f"Initial reasoning complete. Preliminary clusters: {json.dumps(self.preliminary_clusters)}"
        
        elif action.startswith("lookup_topology[") and action.endswith("]"):
            if self.preliminary_clusters is None:
                self.obs = "Error: Preliminary clusters not available."
            else:
                unique_devices = set()
                for cluster in self.preliminary_clusters.get("preliminary_clusters", []):
                    unique_devices.update(cluster.get("devices", []))
                unique_devices = list(unique_devices)
                self.topology_data = get_topology_data(unique_devices)
                self.current_stage = "topology"
                self.obs = f"Topology data retrieved: {json.dumps(self.topology_data)}"
        
        elif action.startswith("refine_clustering[") and action.endswith("]"):
            if self.preliminary_clusters is None or self.topology_data is None:
                self.obs = "Error: Preliminary clusters or topology data missing."
            else:
                result_str = refine_clustering(self.preliminary_clusters, self.topology_data)
                try:
                    self.refined_clusters = json.loads(result_str)
                except Exception as e:
                    print("Parsing error:", e)
                    self.refined_clusters = {
                        "refined_clusters": [
                            {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"],
                             "notes": "Merged based on topology data."}
                        ]
                    }
                self.current_stage = "refined"
                self.obs = f"Clustering refined: {json.dumps(self.refined_clusters)}"
        
        elif action.startswith("assess[") and action.endswith("]"):
            if self.refined_clusters is None:
                self.obs = "Error: Refined clusters not available."
            else:
                result_str = assess_impact_and_generate_recommendations(self.refined_clusters)
                try:
                    self.final_report = json.loads(result_str)
                except Exception as e:
                    print("Parsing error:", e)
                    self.final_report = {
                        "situations": [
                            {"situation_id": "SIT-1", "location": "Site-A", "devices": ["Switch-1", "AP-001", "AP-002"],
                             "severity": "High", "recommendations": "Investigate Switch-1 connectivity."}
                        ]
                    }
                self.current_stage = "assessed"
                self.obs = f"Final report generated: {json.dumps(self.final_report)}"
        
        elif action.startswith("finish[") and action.endswith("]"):
            done = True
            self.obs = "Episode finished."
        
        elif action.startswith("think[") and action.endswith("]"):
            thought = action[len("think["):-1]
            self.thoughts.append(thought)
            self.obs = f"Thought recorded: {thought}"
        
        else:
            self.obs = f"Invalid action: {action}"
        
        return self.obs, reward, done, info

# --- ReAct Loop Implementation for Alert Correlation ---

def react_alert_correlation(env, prompt="", to_print=True):
    """
    Simulate a ReAct loop where the agent interleaves Thought, Action, and receives Observations.
    In practice, the agent's thoughts and actions would be generated by an LLM.
    Here we use input() to simulate the interactive process.
    """
    observation = env.reset()
    if to_print:
        print("Initial Observation:", observation)
    prompt += observation + "\n"
    
    for i in range(1, 10):
        # In a full implementation, the LLM generates both thought and action.
        # Here we simulate by prompting the user.
        thought = input(f"Thought {i}: ")
        action = input(f"Action {i}: ")
        step_str = f"Thought {i}: {thought}\nAction {i}: {action}\n"
        obs, r, done, info = env.step(action)
        step_str += f"Observation {i}: {obs}\n"
        prompt += step_str
        if to_print:
            print(step_str)
        if done:
            break
    return prompt

# --- Example Usage ---
if __name__ == "__main__":
    # Define a sample batch of raw alerts (15-min window)
    raw_alerts = [
        {"alert_id": "A1", "timestamp": "2025-02-22T10:00:00", "device": "Switch-1", "location": "Site-A", "alert_message": "Switch-1 DOWN"},
        {"alert_id": "A2", "timestamp": "2025-02-22T10:01:00", "device": "AP-001", "location": "Site-A", "alert_message": "AP-001 unreachable"},
        {"alert_id": "A3", "timestamp": "2025-02-22T10:01:45", "device": "AP-002", "location": "Site-A", "alert_message": "AP-002 unreachable"},
        {"alert_id": "A4", "timestamp": "2025-02-22T10:02:00", "device": "Switch-2", "location": "Site-A", "alert_message": "Interface flapping on uplink"},
        {"alert_id": "A5", "timestamp": "2025-02-22T10:03:00", "device": "AP-101", "location": "Site-A", "alert_message": "AP-101 unstable"},
        {"alert_id": "C1", "timestamp": "2025-02-22T10:05:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service latency high"},
        {"alert_id": "C2", "timestamp": "2025-02-22T10:06:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service timeout error"}
    ]
    
    env = AlertCorrelationEnv(raw_alerts)
    print("Starting ReAct alert correlation session:")
    final_prompt = react_alert_correlation(env)
    print("Final conversation prompt:")
    print(final_prompt)












# --------------------------------
import openai
import json

# Set your OpenAI API key
openai.api_key = "YOUR_API_KEY_HERE"

### STEP 0: Pre-Grouping Alerts by Location
def pre_group_alerts(raw_alerts):
    """
    Groups raw alerts by location.
    Alerts missing a location are assigned to the 'Cloud' group.
    """
    groups = {}
    for alert in raw_alerts:
        location = alert.get("location")
        if not location:
            location = "Cloud"
        groups.setdefault(location, []).append(alert)
    return groups

### STEP 1: Initial Reasoning on the Batch (Preliminary Clustering)
def initial_reasoning(alerts):
    """
    Uses the LLM to process a group of alerts (from one location)
    and produce preliminary clusters based on common patterns.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to perform initial "
        "reasoning on a batch of alerts that are pre-grouped by location. Each alert "
        "has metadata: timestamp, device, alert_message, and location. Analyze the alerts, "
        "identify common patterns (e.g., repeated mentions of a device, similar error messages, "
        "overlapping timestamps), and produce preliminary clusters. For alerts that seem ambiguous, "
        "flag them for later topology verification. Output your result as a JSON object with two keys: "
        "'preliminary_clusters' (a list of clusters, each with 'cluster_id', 'devices' [list], and 'notes') and "
        "'unassigned_alerts' (a list of alert_ids not assigned to any cluster).\n\n"
        "Few-shot Example:\n"
        "Input: Two alerts: {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
        "       {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
        "Output: {\"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
        "\"notes\": \"AP-001 likely dependent on Switch-1.\"} ], \"unassigned_alerts\": []}.\n\n"
        "Ensure every alert is either grouped or flagged."
    )
    
    user_prompt = (
        "Below is a batch of alerts in JSON format:\n"
        f"{json.dumps({'alerts': alerts}, indent=2)}\n\n"
        "Please analyze these alerts and output your preliminary clustering in the specified JSON format."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=600
    )
    
    result = response["choices"][0]["message"]["content"]
    print("=== Initial Reasoning Result ===")
    print(result)
    return result

### STEP 2: Topology Data Lookup (Function Call Simulation)
def get_topology_data(devices):
    """
    Simulated function to fetch topology data for a list of devices.
    In practice, this would make API calls to retrieve device relationships.
    """
    topology = {}
    for device in devices:
        if device == "Switch-1":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-001", "AP-002"]}
        elif device == "Switch-2":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-101"]}
        else:
            topology[device] = {"upstream": [], "downstream": []}
    return topology

### STEP 3: Integration of Topology Data & Refine Clustering
def refine_clustering(preliminary_clusters, topology_data):
    """
    Uses the LLM to merge topology data with preliminary clusters.
    The LLM reviews each cluster and adjusts groupings based on device dependencies.
    Output is a JSON object with a 'refined_clusters' key.
    """
    system_prompt = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine the clustering. For each preliminary cluster, compare its devices against the topology data. "
        "If multiple clusters share a common upstream device, merge them; if the topology data indicates that a device "
        "belongs to a cluster (for example, it is downstream of the cluster's core device), adjust the cluster accordingly. "
        "Output your refined clustering as a JSON object with a 'refined_clusters' key (a list of clusters, each with "
        "'cluster_id', 'devices', and 'notes' explaining your decisions).\n\n"
        "Few-shot Example:\n"
        "Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"notes\": \"Initial cluster\"}\n"
        "Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}\n\n"
        "Ensure every alert is accounted for and provide a brief rationale for any changes."
    )
    
    user_prompt = (
        "Preliminary Clusters:\n"
        f"{json.dumps(preliminary_clusters, indent=2)}\n\n"
        "Topology Data:\n"
        f"{json.dumps(topology_data, indent=2)}\n\n"
        "Please refine the clustering using the topology data and output your result in the specified JSON format."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=600
    )
    
    result = response["choices"][0]["message"]["content"]
    print("=== Refined Clustering Result ===")
    print(result)
    return result

### STEP 4: Assess Impact, Severity, and Generate Recommendations
def assess_impact_and_generate_recommendations(refined_clusters):
    """
    Uses the LLM to assess each refined cluster, assign severity based on impact,
    and generate recommendations. This does not yet perform deep root cause analysis
    but finalizes the grouping with impact assessment.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task now is to finalize the alert correlation by assessing "
        "each refined cluster. For each cluster, evaluate the impact by considering the number of alerts and the criticality "
        "of the devices. Assign a severity level (High, Medium, Low, or Unknown) and generate actionable recommendations "
        "for further investigation. Output your final report as a JSON object with a 'situations' key, where each situation includes:\n"
        " - situation_id\n - location (if available)\n - devices\n - severity\n - recommendations\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"severity\": \"High\", \"recommendations\": \"Check power and connectivity of Switch-1.\"} ]}\n\n"
        "Make sure every refined cluster is represented."
    )
    
    user_prompt = (
        "Below are the refined clusters from the previous step:\n"
        f"{json.dumps(refined_clusters, indent=2)}\n\n"
        "Please assess each cluster and produce the final alert correlation report in the specified JSON format."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=600
    )
    
    result = response["choices"][0]["message"]["content"]
    print("=== Final Alert Correlation Report ===")
    print(result)
    return result

### (Optional) STEP 5: Self-Validation / Examiner Step
def self_validation(final_report):
    """
    Optionally, use the LLM to review the final report to ensure every alert is assigned
    and clusters make sense. In a real system, this might be an extra pass or a second agent.
    """
    system_prompt = (
        "You are an AI examiner. Review the following final alert correlation report and check that every alert "
        "has been assigned to a cluster, and that there are no obvious discrepancies or mis-grouped alerts. If issues are found, "
        "output a list of suggestions for revision; otherwise, confirm the report is valid. Output in JSON format."
    )
    
    user_prompt = (
        "Final Alert Correlation Report:\n"
        f"{json.dumps(final_report, indent=2)}\n\n"
        "Please review and provide your assessment."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )
    
    result = response["choices"][0]["message"]["content"]
    print("=== Self-Validation Result ===")
    print(result)
    return result

### Main Orchestration Function
def main():
    # Raw alerts from a 15-minute window (example data)
    raw_alerts = [
        {"alert_id": "A1", "timestamp": "2025-02-22T10:00:00", "device": "Switch-1", "location": "Site-A", "alert_message": "Switch-1 DOWN"},
        {"alert_id": "A2", "timestamp": "2025-02-22T10:01:00", "device": "AP-001", "location": "Site-A", "alert_message": "AP-001 unreachable"},
        {"alert_id": "A3", "timestamp": "2025-02-22T10:01:45", "device": "AP-002", "location": "Site-A", "alert_message": "AP-002 unreachable"},
        {"alert_id": "A4", "timestamp": "2025-02-22T10:02:00", "device": "Switch-2", "location": "Site-A", "alert_message": "Interface flapping on uplink"},
        {"alert_id": "A5", "timestamp": "2025-02-22T10:03:00", "device": "AP-101", "location": "Site-A", "alert_message": "AP-101 unstable"},
        {"alert_id": "C1", "timestamp": "2025-02-22T10:05:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service latency high"},
        {"alert_id": "C2", "timestamp": "2025-02-22T10:06:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service timeout error"}
    ]
    
    # STEP 0: Pre-Group alerts by location (assign missing locations to 'Cloud')
    grouped_alerts = pre_group_alerts(raw_alerts)
    final_reports = {}
    
    # Process each group (each location)
    for location, alerts in grouped_alerts.items():
        print(f"\n===== Processing Group: {location} =====")
        # STEP 1: Initial Reasoning to obtain preliminary clusters
        initial_result_str = initial_reasoning(alerts)
        try:
            preliminary_clusters = json.loads(initial_result_str)
        except Exception as e:
            print("Error parsing initial reasoning result as JSON. Using simulated result. Error:", e)
            preliminary_clusters = {
                "preliminary_clusters": [
                    {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"], "notes": "Multiple alerts reference Switch-1."}
                ],
                "unassigned_alerts": []
            }
        
        # Collect unique devices for topology lookup
        unique_devices = set()
        for cluster in preliminary_clusters.get("preliminary_clusters", []):
            unique_devices.update(cluster.get("devices", []))
        unique_devices = list(unique_devices)
        
        # STEP 2: Request Topology Data for these devices
        topology_data = get_topology_data(unique_devices)
        
        # STEP 3: Integrate Topology Data & Refine Clustering
        refined_result_str = refine_clustering(preliminary_clusters, topology_data)
        try:
            refined_clusters = json.loads(refined_result_str)
        except Exception as e:
            print("Error parsing refined clustering result as JSON. Using simulated result. Error:", e)
            refined_clusters = {
                "refined_clusters": [
                    {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"], "notes": "Merged based on topology data."}
                ]
            }
        
        # STEP 4: Assess Impact, Severity, and Generate Recommendations
        final_report_str = assess_impact_and_generate_recommendations(refined_clusters)
        try:
            final_report = json.loads(final_report_str)
        except Exception as e:
            print("Error parsing final report as JSON. Using simulated result. Error:", e)
            final_report = {
                "situations": [
                    {
                        "situation_id": "SIT-1",
                        "location": location,
                        "devices": ["Switch-1", "AP-001", "AP-002"],
                        "severity": "High",
                        "recommendations": "Investigate Switch-1 power and connectivity."
                    }
                ]
            }
        
        # (Optional) STEP 5: Self-Validation / Examiner Step
        validation_result = self_validation(final_report)
        
        final_reports[location] = final_report
    
    # Consolidate and display final reports across all groups
    print("\n===== Consolidated Final Alert Correlation Reports =====")
    print(json.dumps(final_reports, indent=2))

if __name__ == "__main__":
    main()



# -------------------------------- -------------------- another attempt ----------------------------
def pre_group_alerts(raw_alerts):
    """
    Groups raw alerts by location. If an alert is missing a location,
    it is assigned to the 'Cloud' group.
    """
    groups = {}
    for alert in raw_alerts:
        location = alert.get("location") or "Cloud"
        groups.setdefault(location, []).append(alert)
    return groups

import json
import requests

def initial_reasoning(alerts):
    """
    Uses the LLM to process a 15-minute batch of alerts (pre-grouped by location)
    and produce preliminary clusters.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to analyze a batch of alerts "
        "that are pre-grouped by location. Each alert includes the following metadata: "
        "timestamp, device, alert_message, and location. Identify common patterns among these alerts "
        "by looking for repeated device names, overlapping timestamps, and similar error messages. "
        "Group related alerts into preliminary clusters. For each cluster, output a dictionary with: \n"
        "  - 'cluster_id': a unique identifier\n"
        "  - 'devices': a list of devices in the cluster\n"
        "  - 'alert_ids': a list of alert IDs belonging to the cluster\n"
        "  - 'notes': a brief explanation (e.g., 'AP-001 appears dependent on Switch-1'). \n"
        "Also output an 'unassigned_alerts' key with a list of alert IDs that do not clearly fit any cluster.\n\n"
        "Few-shot Example:\n"
        "Input: Two alerts:\n"
        "  {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
        "  {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
        "Output: {\"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
        "\"alert_ids\": [\"A1\", \"A2\"], \"notes\": \"AP-001 likely dependent on Switch-1.\"} ], \"unassigned_alerts\": []}.\n\n"
        "Ensure every alert is either grouped or flagged."
    )
    
    user_prompt = (
        "Below is a batch of alerts in JSON format:\n"
        f"{json.dumps({'alerts': alerts}, indent=2)}\n\n"
        "Please produce preliminary clusters as specified."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer YOUR_API_KEY_HERE", "Content-Type": "application/json"},
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Initial Reasoning Result ===")
    print(result)
    return result

def get_topology_data(devices):
    """
    Simulated function to fetch topology data for a list of devices.
    In a production system, this would query a live topology API.
    """
    topology = {}
    for device in devices:
        if device == "Switch-1":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-001", "AP-002"]}
        elif device == "Switch-2":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-101"]}
        else:
            topology[device] = {"upstream": [], "downstream": []}
    return topology


def refine_clustering(preliminary_clusters, topology_data):
    """
    Uses the LLM to integrate topology data with preliminary clusters, refining groupings.
    """
    system_prompt = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine the clustering. For each preliminary cluster, compare its 'devices' against the topology data. "
        "If the topology indicates that additional devices belong to the cluster (e.g., they are downstream of the core device), "
        "include them. Also, if two clusters share a common upstream device, merge them. Output your result as a JSON object "
        "with a key 'refined_clusters'. Each cluster should include: 'cluster_id', 'devices' (list), 'alert_ids' (list), and 'notes'.\n\n"
        "Few-shot Example:\n"
        "Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"alert_ids\": [\"A1\", \"A2\"], "
        "\"notes\": \"Initial cluster\"}\n"
        "Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}\n\n"
        "Ensure every alert is accounted for and provide a brief rationale for any changes."
    )
    
    user_prompt = (
        "Preliminary Clusters:\n" + json.dumps(preliminary_clusters, indent=2) + "\n\n" +
        "Topology Data:\n" + json.dumps(topology_data, indent=2) + "\n\n" +
        "Please refine the clustering using the topology data and output your result in the specified JSON format."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer YOUR_API_KEY_HERE", "Content-Type": "application/json"},
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Refined Clustering Result ===")
    print(result)
    return result

def assess_impact_and_generate_recommendations(refined_clusters):
    """
    Uses the LLM to produce the final alert correlation report.
    For each situation, the report should include:
      - situation_id
      - location
      - alerts (list of alert IDs)
      - devices (list of devices involved)
      - main_issue_devices (device(s) causing the issue)
      - severity (High/Medium/Low/Unknown)
      - recommendations (actionable steps)
      - notes (explanation)
      - time_range (e.g., "10:00-10:15")
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to finalize the alert correlation report by assessing "
        "each refined cluster. For each cluster, evaluate the impact by considering the number of alerts and the devices involved. "
        "Identify the main issue device(s) if possible, assign a severity level (High, Medium, Low, or Unknown), and generate actionable "
        "recommendations. Also, include the time range of the alerts (assume the current window is 10:00-10:15). \n\n"
        "Output your final report as a JSON object with a key 'situations', where each situation includes:\n"
        "  - 'situation_id'\n  - 'location'\n  - 'alerts' (list of alert IDs)\n  - 'devices' (list of devices)\n"
        "  - 'main_issue_devices' (list of key devices)\n  - 'severity'\n  - 'recommendations'\n  - 'notes'\n  - 'time_range'\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"alerts\": [\"A1\", \"A2\", \"A3\"], "
        "\"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], \"main_issue_devices\": [\"Switch-1\"], \"severity\": \"High\", "
        "\"recommendations\": \"Check power and connectivity of Switch-1.\", \"notes\": \"Switch-1 failure impacting dependent APs.\", "
        "\"time_range\": \"10:00-10:15\"} ]}\n\n"
        "Ensure every refined cluster is represented."
    )
    
    user_prompt = (
        "Below are the refined clusters:\n" +
        json.dumps(refined_clusters, indent=2) + "\n\n" +
        "Please produce the final alert correlation report in the specified JSON format."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer YOUR_API_KEY_HERE", "Content-Type": "application/json"},
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Final Alert Correlation Report ===")
    print(result)
    return result


import gym

class textSpace(gym.spaces.Space):
    def contains(self, x) -> bool:
        return isinstance(x, str)

class AlertCorrelationEnv(gym.Env):
    def __init__(self, alerts_batch):
        super().__init__()
        self.alerts_batch = alerts_batch  # raw alerts for this window
        self.observation_space = self.action_space = textSpace()
        self.reset()
        
    def reset(self, seed=None, return_info=False, options=None):
        self.current_stage = "start"  # stages: start, preliminary, topology, refined, assessed, finished
        self.preliminary_clusters = None
        self.topology_data = None
        self.refined_clusters = None
        self.final_report = None
        self.thoughts = []
        self.obs = ("Start initial reasoning on the provided alert batch. "
                    "Use action 'initial_reasoning[]' to begin.")
        return self.obs

    def step(self, action):
        action = action.strip()
        reward = 0
        done = False
        info = {}
        
        if action.startswith("initial_reasoning[") and action.endswith("]"):
            result_str = initial_reasoning(self.alerts_batch)
            try:
                self.preliminary_clusters = json.loads(result_str)
            except Exception as e:
                print("Parsing error in initial reasoning:", e)
                self.preliminary_clusters = {
                    "preliminary_clusters": [
                        {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"],
                         "alert_ids": ["A1", "A2", "A3"], "notes": "Multiple alerts reference Switch-1."}
                    ],
                    "unassigned_alerts": []
                }
            self.current_stage = "preliminary"
            self.obs = f"Initial reasoning complete. Preliminary clusters: {json.dumps(self.preliminary_clusters)}"
        
        elif action.startswith("lookup_topology[") and action.endswith("]"):
            if self.preliminary_clusters is None:
                self.obs = "Error: Preliminary clusters not available."
            else:
                unique_devices = set()
                for cluster in self.preliminary_clusters.get("preliminary_clusters", []):
                    unique_devices.update(cluster.get("devices", []))
                unique_devices = list(unique_devices)
                self.topology_data = get_topology_data(unique_devices)
                self.current_stage = "topology"
                self.obs = f"Topology data retrieved: {json.dumps(self.topology_data)}"
        
        elif action.startswith("refine_clustering[") and action.endswith("]"):
            if self.preliminary_clusters is None or self.topology_data is None:
                self.obs = "Error: Preliminary clusters or topology data missing."
            else:
                result_str = refine_clustering(self.preliminary_clusters, self.topology_data)
                try:
                    self.refined_clusters = json.loads(result_str)
                except Exception as e:
                    print("Parsing error in refined clustering:", e)
                    self.refined_clusters = {
                        "refined_clusters": [
                            {"cluster_id": "Cluster-1", "devices": ["Switch-1", "AP-001", "AP-002"],
                             "alert_ids": ["A1", "A2", "A3"], "notes": "Merged based on topology data."}
                        ]
                    }
                self.current_stage = "refined"
                self.obs = f"Clustering refined: {json.dumps(self.refined_clusters)}"
        
        elif action.startswith("assess[") and action.endswith("]"):
            if self.refined_clusters is None:
                self.obs = "Error: Refined clusters not available."
            else:
                result_str = assess_impact_and_generate_recommendations(self.refined_clusters)
                try:
                    self.final_report = json.loads(result_str)
                except Exception as e:
                    print("Parsing error in final assessment:", e)
                    self.final_report = {
                        "situations": [
                            {
                                "situation_id": "SIT-1",
                                "location": "Site-A",
                                "alerts": ["A1", "A2", "A3"],
                                "devices": ["Switch-1", "AP-001", "AP-002"],
                                "main_issue_devices": ["Switch-1"],
                                "severity": "High",
                                "recommendations": "Investigate Switch-1 connectivity.",
                                "notes": "Switch-1 failure impacting dependent APs.",
                                "time_range": "10:00-10:15"
                            }
                        ]
                    }
                self.current_stage = "assessed"
                self.obs = f"Final report generated: {json.dumps(self.final_report)}"
        
        elif action.startswith("finish[") and action.endswith("]"):
            done = True
            self.obs = "Episode finished."
        
        elif action.startswith("think[") and action.endswith("]"):
            thought = action[len("think["):-1]
            self.thoughts.append(thought)
            self.obs = f"Thought recorded: {thought}"
        
        else:
            self.obs = f"Invalid action: {action}"
        
        return self.obs, reward, done, info

def react_alert_correlation(env, prompt="", to_print=True):
    """
    Simulate a ReAct loop where the agent interleaves Thought and Action steps.
    In a production system, an LLM would generate these steps. Here, we use input() for demonstration.
    """
    observation = env.reset()
    if to_print:
        print("Initial Observation:", observation)
    prompt += observation + "\n"
    
    for i in range(1, 10):
        thought = input(f"Thought {i}: ")
        action = input(f"Action {i}: ")
        step_str = f"Thought {i}: {thought}\nAction {i}: {action}\n"
        obs, r, done, info = env.step(action)
        step_str += f"Observation {i}: {obs}\n"
        prompt += step_str
        if to_print:
            print(step_str)
        if done:
            break
    return prompt

# ---------- Example Usage ----------
if __name__ == "__main__":
    # Sample batch of raw alerts (15-minute window)
    raw_alerts = [
        {"alert_id": "A1", "timestamp": "2025-02-22T10:00:00", "device": "Switch-1", "location": "Site-A", "alert_message": "Switch-1 DOWN"},
        {"alert_id": "A2", "timestamp": "2025-02-22T10:01:00", "device": "AP-001", "location": "Site-A", "alert_message": "AP-001 unreachable"},
        {"alert_id": "A3", "timestamp": "2025-02-22T10:01:45", "device": "AP-002", "location": "Site-A", "alert_message": "AP-002 unreachable"},
        {"alert_id": "A4", "timestamp": "2025-02-22T10:02:00", "device": "Switch-2", "location": "Site-A", "alert_message": "Interface flapping on uplink"},
        {"alert_id": "A5", "timestamp": "2025-02-22T10:03:00", "device": "AP-101", "location": "Site-A", "alert_message": "AP-101 unstable"},
        {"alert_id": "C1", "timestamp": "2025-02-22T10:05:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service latency high"},
        {"alert_id": "C2", "timestamp": "2025-02-22T10:06:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service timeout error"}
    ]
    
    env = AlertCorrelationEnv(raw_alerts)
    print("Starting ReAct alert correlation session:")
    final_prompt = react_alert_correlation(env)
    print("Final conversation prompt:")
    print(final_prompt)


# ---------------------------- with dynamic feedback loop ----------------------------
import json
import time
import gym
import requests

# ---------- Helper Functions Using OpenAI API Calls ----------

def initial_reasoning(alerts):
    """
    Uses the LLM to process a 15-minute batch of alerts (pre-grouped by location)
    and produce preliminary clusters.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to analyze a batch of alerts "
        "that are pre-grouped by location. Each alert includes the following metadata: "
        "timestamp, device, alert_message, and location. Identify common patterns among these alerts "
        "by looking for repeated device names, overlapping timestamps, and similar error messages. "
        "Group related alerts into preliminary clusters. For each cluster, output a dictionary with: \n"
        "  - 'cluster_id': a unique identifier\n"
        "  - 'devices': a list of devices in the cluster\n"
        "  - 'alert_ids': a list of alert IDs belonging to the cluster\n"
        "  - 'notes': a brief explanation (e.g., 'AP-001 likely dependent on Switch-1'). \n"
        "Also output an 'unassigned_alerts' key with a list of alert IDs that do not clearly fit any cluster.\n\n"
        "Few-shot Example:\n"
        "Input: Two alerts:\n"
        "  {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
        "  {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
        "Output: {\"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
        "\"alert_ids\": [\"A1\", \"A2\"], \"notes\": \"AP-001 likely dependent on Switch-1.\"} ], \"unassigned_alerts\": []}.\n\n"
        "Ensure every alert is either grouped or flagged."
    )
    
    user_prompt = (
        "Below is a batch of alerts in JSON format:\n"
        f"{json.dumps({'alerts': alerts}, indent=2)}\n\n"
        "Please produce preliminary clusters as specified."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer YOUR_API_KEY_HERE",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Initial Reasoning Result ===")
    print(result)
    return result

def get_topology_data(devices):
    """
    Simulated function to fetch topology data for a list of devices.
    In production, this function would query a live topology API.
    """
    topology = {}
    for device in devices:
        if device == "Switch-1":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-001", "AP-002"]}
        elif device == "Switch-2":
            topology[device] = {"upstream": ["Core-Router-A"], "downstream": ["AP-101"]}
        else:
            topology[device] = {"upstream": [], "downstream": []}
    return topology

def refine_clustering(preliminary_clusters, topology_data):
    """
    Uses the LLM to integrate topology data with the preliminary clusters,
    refining the grouping.
    """
    system_prompt = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine the clustering. For each preliminary cluster, compare its 'devices' against the topology data. "
        "If the topology indicates that additional devices belong to the cluster (e.g., they are downstream of the core device), "
        "include them. Also, if two clusters share a common upstream device, merge them. Output your result as a JSON object "
        "with a key 'refined_clusters'. Each cluster should include: 'cluster_id', 'devices' (list), 'alert_ids' (list), and 'notes'.\n\n"
        "Few-shot Example:\n"
        "Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"alert_ids\": [\"A1\", \"A2\"], "
        "\"notes\": \"Initial cluster\"}\n"
        "Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}\n\n"
        "Ensure every alert is accounted for and provide a brief rationale for any changes."
    )
    
    user_prompt = (
        "Preliminary Clusters:\n" + json.dumps(preliminary_clusters, indent=2) + "\n\n" +
        "Topology Data:\n" + json.dumps(topology_data, indent=2) + "\n\n" +
        "Please refine the clustering using the topology data and output your result in the specified JSON format."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer YOUR_API_KEY_HERE",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Refined Clustering Result ===")
    print(result)
    return result

def assess_impact_and_generate_recommendations(refined_clusters):
    """
    Uses the LLM to produce the final alert correlation report.
    For each situation, include:
      - situation_id
      - location
      - alerts (list of alert IDs)
      - devices (list of devices involved)
      - main_issue_devices (device(s) causing the problem)
      - severity (High, Medium, Low, or Unknown)
      - recommendations (actionable next steps)
      - notes (explanation)
      - time_range (e.g., "10:00-10:15")
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to finalize the alert correlation report by assessing "
        "each refined cluster. For each cluster, evaluate the impact by considering the number of alerts and the devices involved. "
        "Identify the main issue device(s) if possible, assign a severity level (High, Medium, Low, or Unknown), and generate actionable "
        "recommendations for further investigation. Also, include the time range of the alerts (assume the current window is 10:00-10:15). \n\n"
        "Output your final report as a JSON object with a key 'situations', where each situation includes:\n"
        "  - 'situation_id'\n  - 'location'\n  - 'alerts' (list of alert IDs)\n  - 'devices' (list of devices)\n"
        "  - 'main_issue_devices' (list of key devices)\n  - 'severity'\n  - 'recommendations'\n  - 'notes'\n  - 'time_range'\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], \"alert_ids\": [\"A1\", \"A2\", \"A3\"], "
        "\"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"alerts\": [\"A1\", \"A2\", \"A3\"], "
        "\"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], \"main_issue_devices\": [\"Switch-1\"], \"severity\": \"High\", "
        "\"recommendations\": \"Check power and connectivity of Switch-1.\", \"notes\": \"Switch-1 failure impacting dependent APs.\", "
        "\"time_range\": \"10:00-10:15\"} ]}\n\n"
        "Ensure every refined cluster is represented."
    )
    
    user_prompt = (
        "Below are the refined clusters:\n" +
        json.dumps(refined_clusters, indent=2) + "\n\n" +
        "Please produce the final alert correlation report in the specified JSON format."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer YOUR_API_KEY_HERE",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Final Alert Correlation Report ===")
    print(result)
    return result

def examiner_feedback(query):
    """
    Simulated examiner function. Given a query from the model (e.g., uncertainties about grouping),
    it returns a clarifying response.
    """
    if "uncertain" in query.lower():
        return "Hint: Consider verifying if the devices share a common upstream dependency."
    elif "dependency" in query.lower():
        return "Hint: Devices with the same upstream node (e.g., Switch-1) likely belong together."
    else:
        return "No additional feedback available."

# ---------- Gym Environment Definition ----------

class textSpace(gym.spaces.Space):
    def contains(self, x) -> bool:
        return isinstance(x, str)

class AlertCorrelationEnv(gym.Env):
    def __init__(self, alerts_batch):
        super().__init__()
        self.alerts_batch = alerts_batch  # raw alerts for this window
        self.observation_space = self.action_space = textSpace()
        self.reset()
        
    def reset(self, seed=None, return_info=False, options=None):
        self.current_stage = "start"  # stages: start, preliminary, topology, refined, assessed, finished
        self.preliminary_clusters = None
        self.topology_data = None
        self.refined_clusters = None
        self.final_report = None
        self.thoughts = []
        self.obs = (
            "Start initial reasoning on the provided alert batch. "
            "Use action 'initial_reasoning[]' to begin. "
            "If uncertain at any step, use 'feedback[<your query>]' to request clarification."
        )
        return self.obs

    def step(self, action):
        action = action.strip()
        reward = 0
        done = False
        info = {}
        
        # Dynamic Feedback action
        if action.startswith("feedback[") and action.endswith("]"):
            query = action[len("feedback["):-1]
            feedback_response = examiner_feedback(query)
            self.obs = f"Feedback received: {feedback_response}"
            return self.obs, reward, done, info
        
        if action.startswith("initial_reasoning[") and action.endswith("]"):
            result_str = initial_reasoning(self.alerts_batch)
            try:
                self.preliminary_clusters = json.loads(result_str)
            except Exception as e:
                print("Parsing error in initial reasoning:", e)
                self.preliminary_clusters = {
                    "preliminary_clusters": [
                        {
                            "cluster_id": "Cluster-1",
                            "devices": ["Switch-1", "AP-001", "AP-002"],
                            "alert_ids": ["A1", "A2", "A3"],
                            "notes": "Multiple alerts reference Switch-1."
                        }
                    ],
                    "unassigned_alerts": []
                }
            self.current_stage = "preliminary"
            self.obs = f"Initial reasoning complete. Preliminary clusters: {json.dumps(self.preliminary_clusters)}"
        
        elif action.startswith("lookup_topology[") and action.endswith("]"):
            if self.preliminary_clusters is None:
                self.obs = "Error: Preliminary clusters not available."
            else:
                unique_devices = set()
                for cluster in self.preliminary_clusters.get("preliminary_clusters", []):
                    unique_devices.update(cluster.get("devices", []))
                unique_devices = list(unique_devices)
                self.topology_data = get_topology_data(unique_devices)
                self.current_stage = "topology"
                self.obs = f"Topology data retrieved: {json.dumps(self.topology_data)}"
        
        elif action.startswith("refine_clustering[") and action.endswith("]"):
            if self.preliminary_clusters is None or self.topology_data is None:
                self.obs = "Error: Preliminary clusters or topology data missing."
            else:
                result_str = refine_clustering(self.preliminary_clusters, self.topology_data)
                try:
                    self.refined_clusters = json.loads(result_str)
                except Exception as e:
                    print("Parsing error in refined clustering:", e)
                    self.refined_clusters = {
                        "refined_clusters": [
                            {
                                "cluster_id": "Cluster-1",
                                "devices": ["Switch-1", "AP-001", "AP-002"],
                                "alert_ids": ["A1", "A2", "A3"],
                                "notes": "Merged based on topology data."
                            }
                        ]
                    }
                self.current_stage = "refined"
                self.obs = f"Clustering refined: {json.dumps(self.refined_clusters)}"
        
        elif action.startswith("assess[") and action.endswith("]"):
            if self.refined_clusters is None:
                self.obs = "Error: Refined clusters not available."
            else:
                result_str = assess_impact_and_generate_recommendations(self.refined_clusters)
                try:
                    self.final_report = json.loads(result_str)
                except Exception as e:
                    print("Parsing error in final assessment:", e)
                    self.final_report = {
                        "situations": [
                            {
                                "situation_id": "SIT-1",
                                "location": "Site-A",
                                "alerts": ["A1", "A2", "A3"],
                                "devices": ["Switch-1", "AP-001", "AP-002"],
                                "main_issue_devices": ["Switch-1"],
                                "severity": "High",
                                "recommendations": "Investigate Switch-1 connectivity.",
                                "notes": "Switch-1 failure impacting dependent APs.",
                                "time_range": "10:00-10:15"
                            }
                        ]
                    }
                self.current_stage = "assessed"
                self.obs = f"Final report generated: {json.dumps(self.final_report)}"
        
        elif action.startswith("finish[") and action.endswith("]"):
            done = True
            self.obs = "Episode finished."
        
        elif action.startswith("think[") and action.endswith("]"):
            thought = action[len("think["):-1]
            self.thoughts.append(thought)
            self.obs = f"Thought recorded: {thought}"
        
        else:
            self.obs = f"Invalid action: {action}"
        
        return self.obs, reward, done, info

# ---------- ReAct Loop Simulation ----------

def react_alert_correlation(env, prompt="", to_print=True):
    """
    Simulate a ReAct loop where the agent interleaves Thought and Action steps.
    The agent can also issue 'feedback[...]' actions if it needs dynamic input.
    """
    observation = env.reset()
    if to_print:
        print("Initial Observation:", observation)
    prompt += observation + "\n"
    
    for i in range(1, 10):
        thought = input(f"Thought {i}: ")
        action = input(f"Action {i}: ")
        step_str = f"Thought {i}: {thought}\nAction {i}: {action}\n"
        obs, r, done, info = env.step(action)
        step_str += f"Observation {i}: {obs}\n"
        prompt += step_str
        if to_print:
            print(step_str)
        if done:
            break
    return prompt

# ---------- Example Usage ----------

if __name__ == "__main__":
    # Sample batch of raw alerts (15-minute window)
    raw_alerts = [
        {"alert_id": "A1", "timestamp": "2025-02-22T10:00:00", "device": "Switch-1", "location": "Site-A", "alert_message": "Switch-1 DOWN"},
        {"alert_id": "A2", "timestamp": "2025-02-22T10:01:00", "device": "AP-001", "location": "Site-A", "alert_message": "AP-001 unreachable"},
        {"alert_id": "A3", "timestamp": "2025-02-22T10:01:45", "device": "AP-002", "location": "Site-A", "alert_message": "AP-002 unreachable"},
        {"alert_id": "A4", "timestamp": "2025-02-22T10:02:00", "device": "Switch-2", "location": "Site-A", "alert_message": "Interface flapping on uplink"},
        {"alert_id": "A5", "timestamp": "2025-02-22T10:03:00", "device": "AP-101", "location": "Site-A", "alert_message": "AP-101 unstable"},
        {"alert_id": "C1", "timestamp": "2025-02-22T10:05:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service latency high"},
        {"alert_id": "C2", "timestamp": "2025-02-22T10:06:00", "device": "Cloud-Server-1", "location": None, "alert_message": "Service timeout error"}
    ]
    
    env = AlertCorrelationEnv(raw_alerts)
    print("Starting ReAct alert correlation session with dynamic feedback:")
    final_prompt = react_alert_correlation(env)
    print("Final conversation prompt:")
    print(final_prompt)
