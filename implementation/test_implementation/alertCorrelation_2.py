import json
import time
import gym
import requests

# ---------- Helper Functions Using OpenAI API Calls ----------

def initial_reasoning(alerts):
    """
    Uses the LLM to process a 15-minute batch of alerts (pre-grouped by location)
    and produce preliminary clusters along with a detailed chain-of-thought.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to analyze a batch of alerts "
        "that are pre-grouped by location. Each alert includes metadata: timestamp, device, alert_message, and location. "
        "Before taking any action, please provide a detailed chain-of-thought that explains your reasoning, including any uncertainties "
        "or alternative approaches you considered. Then, group related alerts into preliminary clusters. For each cluster, output a dictionary with:\n"
        "  - 'cluster_id': a unique identifier\n"
        "  - 'devices': a list of devices in the cluster\n"
        "  - 'alert_ids': a list of alert IDs belonging to the cluster\n"
        "  - 'notes': a brief explanation (e.g., 'AP-001 likely dependent on Switch-1').\n"
        "Also output an 'unassigned_alerts' key with any alert IDs that do not clearly fit into any cluster.\n\n"
        "Few-shot Example:\n"
        "Input: Two alerts:\n"
        "  {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
        "  {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
        "Output: {\"chain_of_thought\": \"I see both alerts reference Switch-1; AP-001 may be dependent on Switch-1.\",\n"
        "         \"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
        "\"alert_ids\": [\"A1\", \"A2\"], \"notes\": \"AP-001 likely dependent on Switch-1.\"} ],\n"
        "         \"unassigned_alerts\": []}\n\n"
        "Ensure your chain-of-thought covers alternative possibilities before finalizing your grouping."
    )
    
    user_prompt = (
        "Below is a batch of alerts in JSON format:\n"
        f"{json.dumps({'alerts': alerts}, indent=2)}\n\n"
        "Please produce your chain-of-thought and preliminary clusters as specified."
    )
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer YOUR_API_KEY_HERE",  # Replace with your key
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,
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
    In production, this would query a live topology API.
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
    refining the grouping. The model is asked to first explain its reasoning.
    """
    system_prompt = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine your clustering. Before making any changes, please provide a detailed chain-of-thought explaining "
        "whether you plan to merge clusters or add additional devices based on the topology data. Then output your refined "
        "clustering as a JSON object with a key 'refined_clusters'. Each cluster should include:\n"
        "  - 'cluster_id'\n  - 'devices' (list)\n  - 'alert_ids' (list)\n  - 'notes'\n\n"
        "Few-shot Example:\n"
        "Input Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"alert_ids\": [\"A1\", \"A2\"], "
        "\"notes\": \"Initial cluster\"}\n"
        "Input Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"chain_of_thought\": \"Since AP-002 is downstream of Switch-1, I will merge it into the cluster.\",\n"
        "         \"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}\n\n"
        "Ensure every alert is accounted for and explain your reasoning."
    )
    
    user_prompt = (
        "Preliminary Clusters:\n" + json.dumps(preliminary_clusters, indent=2) + "\n\n" +
        "Topology Data:\n" + json.dumps(topology_data, indent=2) + "\n\n" +
        "Please refine the clustering and include your chain-of-thought in the output."
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
            "temperature": 0.5,
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
    For each situation, the report includes:
      - situation_id
      - location
      - alerts (list of alert IDs)
      - devices (list of devices involved)
      - main_issue_devices (device(s) causing the problem)
      - severity (High, Medium, Low, or Unknown)
      - recommendations (actionable next steps)
      - notes (explanation)
      - time_range (e.g., "10:00-10:15")
    The model is asked to first detail its chain-of-thought before finalizing the report.
    """
    system_prompt = (
        "You are an AI event correlation agent. Your task is to finalize the alert correlation report by assessing "
        "each refined cluster. Before finalizing, please provide a detailed chain-of-thought describing any uncertainties "
        "and your rationale for determining severity and recommendations. Then, output your final report as a JSON object "
        "with a key 'situations'. Each situation should include:\n"
        "  - 'situation_id'\n  - 'location'\n  - 'alerts' (list of alert IDs)\n  - 'devices' (list of devices)\n"
        "  - 'main_issue_devices' (list of key devices)\n  - 'severity'\n  - 'recommendations'\n  - 'notes'\n  - 'time_range'\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"chain_of_thought\": \"Based on the critical role of Switch-1 and the number of alerts, I assign High severity.\",\n"
        "         \"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"alerts\": [\"A1\", \"A2\", \"A3\"], "
        "\"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], \"main_issue_devices\": [\"Switch-1\"], \"severity\": \"High\", "
        "\"recommendations\": \"Check power and connectivity of Switch-1.\", \"notes\": \"Switch-1 failure impacting dependent APs.\", "
        "\"time_range\": \"10:00-10:15\"} ]}\n\n"
        "Ensure every refined cluster is represented and your reasoning is clear."
    )
    
    user_prompt = (
        "Below are the refined clusters:\n" +
        json.dumps(refined_clusters, indent=2) + "\n\n" +
        "Please produce the final alert correlation report and include your chain-of-thought in the output."
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
            "temperature": 0.5,
            "max_tokens": 600
        }
    )
    result = response.json()["choices"][0]["message"]["content"]
    print("=== Final Alert Correlation Report ===")
    print(result)
    return result

def external_evaluation(chain_of_thought, current_output):
    """
    Simulated external evaluation function.
    It examines the chain-of-thought and current output to provide corrective suggestions.
    """
    if "Alert A4" in chain_of_thought and "Switch-2" not in current_output:
        return "Hint: It appears Alert A4 might be mis-grouped; check if it should be in a cluster with Switch-2."
    if len(chain_of_thought.split()) < 20:
        return "Hint: Your chain-of-thought is very brief. Consider elaborating on your reasoning."
    return "Evaluation passed: Your reasoning appears consistent."

# ---------- Gym Environment Definition with Dynamic Feedback and External Evaluation ----------

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
        self.thoughts = []  # stores chain-of-thought entries
        self.obs = (
            "Start initial reasoning on the provided alert batch. "
            "Use action 'initial_reasoning[]' to begin. "
            "If uncertain, record your thought with 'think[<your thought>]' and use 'feedback[<your query>]' "
            "or 'review[<your query>]' to request external evaluation."
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
            feedback_response = external_evaluation(" ".join(self.thoughts), self.obs)
            self.obs = f"Feedback received: {feedback_response}"
            return self.obs, reward, done, info

        # External Review action
        if action.startswith("review[") and action.endswith("]"):
            query = action[len("review["):-1]
            evaluation = external_evaluation(" ".join(self.thoughts), self.obs)
            self.obs = f"External evaluation: {evaluation}"
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
    The agent can also issue 'feedback[...]' and 'review[...]' actions to receive dynamic feedback.
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
    print("Starting ReAct alert correlation session with dynamic feedback and external evaluation:")
    final_prompt = react_alert_correlation(env)
    print("Final conversation prompt:")
    print(final_prompt)


# ------------------------
import json
import time
import gym
import requests

# Replace with your actual API key.
API_KEY = "YOUR_API_KEY_HERE"

# ---------- Utility: Function to make a ChatCompletion call with conversation history ----------
def chat_completion_call(conversation, max_tokens=600, temperature=0.5):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": conversation,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    )
    reply = response.json()["choices"][0]["message"]["content"]
    return reply

# ---------- Function: Initial Reasoning with Conversation History ----------
def initial_reasoning(alerts, history=None):
    """
    Uses the LLM to process a batch of alerts and produce preliminary clusters,
    including a detailed chain-of-thought.
    """
    if history is None:
        # Initialize conversation with system instructions.
        history = [
            {"role": "system", "content": (
                "You are an AI event correlation agent. Your task is to analyze a batch of alerts "
                "that are pre-grouped by location. Each alert includes metadata: timestamp, device, alert_message, and location. "
                "Before taking any action, please provide a detailed chain-of-thought that explains your reasoning, including any uncertainties "
                "or alternative approaches you considered. Then, group related alerts into preliminary clusters. For each cluster, output a dictionary with:\n"
                "  - 'cluster_id': a unique identifier\n"
                "  - 'devices': a list of devices in the cluster\n"
                "  - 'alert_ids': a list of alert IDs belonging to the cluster\n"
                "  - 'notes': a brief explanation.\n"
                "Also output an 'unassigned_alerts' key with any alert IDs that do not clearly fit into any cluster.\n\n"
                "Few-shot Example:\n"
                "Input: Two alerts: {\"alert_id\": \"A1\", \"device\": \"Switch-1\", \"alert_message\": \"Switch-1 DOWN\"} and\n"
                "       {\"alert_id\": \"A2\", \"device\": \"AP-001\", \"alert_message\": \"AP-001 unreachable\"}.\n"
                "Output: {\"chain_of_thought\": \"I see both alerts reference Switch-1; AP-001 may be dependent on Switch-1.\",\n"
                "         \"preliminary_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], "
                "\"alert_ids\": [\"A1\", \"A2\"], \"notes\": \"AP-001 likely dependent on Switch-1.\"} ],\n"
                "         \"unassigned_alerts\": []}"
            )}
        ]
    # Append the user's prompt.
    user_message = {
        "role": "user",
        "content": "Below is a batch of alerts in JSON format:\n" + json.dumps({'alerts': alerts}, indent=2) +
                   "\nPlease produce your chain-of-thought and preliminary clusters as specified."
    }
    history.append(user_message)
    
    # Make the API call
    reply = chat_completion_call(history)
    history.append({"role": "assistant", "content": reply})
    print("=== Initial Reasoning Result ===")
    print(reply)
    return reply, history

# ---------- Function: Topology Data Lookup (Simulated) ----------
def get_topology_data(devices):
    """
    Simulated function to fetch topology data for a list of devices.
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

# ---------- Function: Refine Clustering with Conversation History ----------
def refine_clustering(preliminary_clusters, topology_data, history):
    """
    Uses the LLM to integrate topology data with the preliminary clusters,
    refining the grouping. The assistant should include its chain-of-thought.
    """
    system_message = (
        "You are an AI event correlation agent. Now integrate the provided topology data with the preliminary clusters "
        "to refine your clustering. Before making any changes, provide a detailed chain-of-thought explaining whether you plan "
        "to merge clusters or add additional devices based on the topology data. Then, output your refined clustering as a JSON object "
        "with a key 'refined_clusters'. Each cluster should include: 'cluster_id', 'devices', 'alert_ids', and 'notes'.\n\n"
        "Few-shot Example:\n"
        "Input Preliminary Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\"], \"alert_ids\": [\"A1\", \"A2\"], "
        "\"notes\": \"Initial cluster\"}\n"
        "Input Topology Data: {\"Switch-1\": {\"downstream\": [\"AP-001\", \"AP-002\"]}}\n"
        "Output: {\"chain_of_thought\": \"Since AP-002 is downstream of Switch-1, I will merge it into the cluster.\",\n"
        "         \"refined_clusters\": [ {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Merged AP-002 into Cluster-1 because it is downstream of Switch-1.\"} ]}"
    )
    history.append({"role": "system", "content": system_message})
    
    user_message = {
        "role": "user",
        "content": "Preliminary Clusters:\n" + json.dumps(preliminary_clusters, indent=2) +
                   "\nTopology Data:\n" + json.dumps(topology_data, indent=2) +
                   "\nPlease refine the clustering and include your chain-of-thought in the output."
    }
    history.append(user_message)
    
    reply = chat_completion_call(history)
    history.append({"role": "assistant", "content": reply})
    print("=== Refined Clustering Result ===")
    print(reply)
    return reply, history

# ---------- Function: Assess Impact and Generate Final Report with Conversation History ----------
def assess_impact_and_generate_recommendations(refined_clusters, history):
    """
    Uses the LLM to produce the final alert correlation report.
    Each situation should include situation_id, location, alerts, devices, main_issue_devices,
    severity, recommendations, notes, and time_range. The assistant must provide its chain-of-thought first.
    """
    system_message = (
        "You are an AI event correlation agent. Your task is to finalize the alert correlation report by assessing "
        "each refined cluster. Before finalizing, please provide a detailed chain-of-thought describing any uncertainties "
        "and your rationale for determining severity and recommendations. Then, output your final report as a JSON object "
        "with a key 'situations'. Each situation should include:\n"
        "  - 'situation_id'\n  - 'location'\n  - 'alerts' (list)\n  - 'devices' (list)\n"
        "  - 'main_issue_devices' (list)\n  - 'severity'\n  - 'recommendations'\n  - 'notes'\n  - 'time_range'\n\n"
        "Few-shot Example:\n"
        "Input Refined Cluster: {\"cluster_id\": \"Cluster-1\", \"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], "
        "\"alert_ids\": [\"A1\", \"A2\", \"A3\"], \"notes\": \"Devices connected via Switch-1.\"}\n"
        "Output: {\"chain_of_thought\": \"Based on the number of alerts and the critical role of Switch-1, I assign High severity.\",\n"
        "         \"situations\": [ {\"situation_id\": \"SIT-1\", \"location\": \"Site-A\", \"alerts\": [\"A1\", \"A2\", \"A3\"], "
        "\"devices\": [\"Switch-1\", \"AP-001\", \"AP-002\"], \"main_issue_devices\": [\"Switch-1\"], \"severity\": \"High\", "
        "\"recommendations\": \"Check power and connectivity of Switch-1.\", \"notes\": \"Switch-1 failure impacting dependent APs.\", "
        "\"time_range\": \"10:00-10:15\"} ]}"
    )
    history.append({"role": "system", "content": system_message})
    
    user_message = {
        "role": "user",
        "content": "Refined Clusters:\n" + json.dumps(refined_clusters, indent=2) +
                   "\nPlease produce the final alert correlation report and include your chain-of-thought."
    }
    history.append(user_message)
    
    reply = chat_completion_call(history)
    history.append({"role": "assistant", "content": reply})
    print("=== Final Alert Correlation Report ===")
    print(reply)
    return reply, history

# ---------- External Evaluation Function ----------
def external_evaluation(chain_of_thought, current_output):
    """
    Simulated external evaluation function that reviews the chain-of-thought and current output.
    """
    if "Alert A4" in chain_of_thought and "Switch-2" not in current_output:
        return "Hint: It appears Alert A4 might be mis-grouped; check if it should be in a cluster with Switch-2."
    if len(chain_of_thought.split()) < 20:
        return "Hint: Your chain-of-thought is very brief. Consider elaborating on your reasoning."
    return "Evaluation passed: Your reasoning appears consistent."

# ---------- Gym Environment Definition with Conversation History ----------
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
        self.thoughts = []  # stores chain-of-thought entries from the agent
        # Initialize conversation history with a system message.
        self.conversation = [
            {"role": "system", "content": (
                "You are an AI event correlation agent. "
                "Follow the instructions carefully and generate a detailed chain-of-thought before each action. "
                "If uncertain, use feedback[...] or review[...] actions to request external evaluation."
            )}
        ]
        self.obs = (
            "Start initial reasoning on the provided alert batch. "
            "Use action 'initial_reasoning[]' to begin."
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
            # Combine all stored chain-of-thought from self.thoughts.
            combined_thought = " ".join(self.thoughts)
            feedback_response = external_evaluation(combined_thought, self.obs)
            self.obs = f"Feedback received: {feedback_response}"
            # Log as an assistant message.
            self.conversation.append({"role": "assistant", "content": self.obs})
            return self.obs, reward, done, info
        
        # External Review action
        if action.startswith("review[") and action.endswith("]"):
            query = action[len("review["):-1]
            combined_thought = " ".join(self.thoughts)
            evaluation = external_evaluation(combined_thought, self.obs)
            self.obs = f"External evaluation: {evaluation}"
            self.conversation.append({"role": "assistant", "content": self.obs})
            return self.obs, reward, done, info
        
        # Record a thought
        if action.startswith("think[") and action.endswith("]"):
            thought = action[len("think["):-1]
            self.thoughts.append(thought)
            self.obs = f"Thought recorded: {thought}"
            self.conversation.append({"role": "assistant", "content": self.obs})
            return self.obs, reward, done, info
        
        # Each primary action appends a user message, then gets an assistant response.
        if action.startswith("initial_reasoning[") and action.endswith("]"):
            # Append the action as a user message.
            self.conversation.append({"role": "user", "content": action})
            result_str = initial_reasoning(self.alerts_batch, history=self.conversation)[0]
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
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        elif action.startswith("lookup_topology[") and action.endswith("]"):
            self.conversation.append({"role": "user", "content": action})
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
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        elif action.startswith("refine_clustering[") and action.endswith("]"):
            self.conversation.append({"role": "user", "content": action})
            if self.preliminary_clusters is None or self.topology_data is None:
                self.obs = "Error: Preliminary clusters or topology data missing."
            else:
                result_str, self.conversation = refine_clustering(self.preliminary_clusters, self.topology_data, self.conversation)
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
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        elif action.startswith("assess[") and action.endswith("]"):
            self.conversation.append({"role": "user", "content": action})
            if self.refined_clusters is None:
                self.obs = "Error: Refined clusters not available."
            else:
                result_str, self.conversation = assess_impact_and_generate_recommendations(self.refined_clusters, self.conversation)
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
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        elif action.startswith("finish[") and action.endswith("]"):
            self.conversation.append({"role": "user", "content": action})
            done = True
            self.obs = "Episode finished."
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        else:
            self.obs = f"Invalid action: {action}"
            self.conversation.append({"role": "assistant", "content": self.obs})
        
        return self.obs, reward, done, info

# ---------- ReAct Loop Simulation with Conversation History ----------

def react_alert_correlation(env, prompt="", to_print=True):
    """
    Simulate a ReAct loop where the agent interleaves Thought and Action steps.
    The agent can also issue 'feedback[...]' and 'review[...]' actions to receive dynamic feedback.
    All messages (system, user, assistant) are stored in the conversation history.
    """
    observation = env.reset()
    if to_print:
        print("Initial Observation:", observation)
    prompt += observation + "\n"
    
    for i in range(1, 10):
        thought = input(f"Thought {i}: ")
        env.step(f"think[{thought}]")  # record the thought in the conversation
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
    print("Starting ReAct alert correlation session with full conversation history, dynamic feedback, and external evaluation:")
    final_prompt = react_alert_correlation(env)
    print("Final conversation prompt:")
    print(final_prompt)
