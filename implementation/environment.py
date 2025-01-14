import os, json, requests
import openai


# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Define textSpace class
class textSpace(gym.spaces.Space):
    def contains(self, x) -> bool:
        return isinstance(x, str)

# Define APEnv class
class APEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.current_alert = None
        self.current_device = None
        self.action_results = []
        self.steps = 0
        self.answer = None
        self.observation_space = self.action_space = textSpace()
    
    def _get_obs(self):
        return self.obs
    
    def _get_info(self):
        return {
            "steps": self.steps,
            "answer": self.answer,
            "current_device": self.current_device,
            "action_results": self.action_results,
        }
    
    def reset(self, alert_info=None, seed=None, return_info=False, options=None):
        self.obs = "Ready to diagnose. Use actions like GetDeviceInfo[], LookupTopology[], RebootDevice[], SearchThreatIntel[], and Finish[].\n"
        self.current_alert = alert_info
        self.current_device = alert_info.get("device_id") if alert_info else None
        self.action_results = []
        self.steps = 0
        self.answer = None
        observation = self._get_obs()
        info = self._get_info()
        return (observation, info) if return_info else observation
    
    def step(self, action):
        reward = 0
        done = False
        action = action.strip()
        
        if self.answer is not None:
            done = True
            return self.obs, reward, done, self._get_info()
        
        if action.startswith("GetDeviceInfo[") and action.endswith("]"):
            device_id = action[len("GetDeviceInfo["):-1]
            self.obs = self.get_device_info(device_id)
        elif action.startswith("LookupTopology[") and action.endswith("]"):
            device_id = action[len("LookupTopology["):-1]
            self.obs = self.lookup_topology(device_id)
        elif action.startswith("RebootDevice[") and action.endswith("]"):
            device_id = action[len("RebootDevice["):-1]
            self.obs = self.reboot_device(device_id)
        elif action.startswith("SearchThreatIntel[") and action.endswith("]"):
            ip_address = action[len("SearchThreatIntel["):-1]
            self.obs = self.search_threat_intel(ip_address)
        elif action.startswith("Finish[") and action.endswith("]"):
            summary = action[len("Finish["):-1]
            self.answer = summary
            done = True
            self.obs = f"Episode finished, reward = {reward}\n"
        else:
            self.obs = f"Invalid action: {action}"
        
        self.steps += 1
        self.action_results.append({"action": action, "observation": self.obs})
        
        return self.obs, reward, done, self._get_info()
    
    def get_device_info(self, device_id):
        try:
            response = requests.get(f"https://device_manager/api/device/{device_id}")
            response.raise_for_status()
            data = response.json()
            return f"Device {device_id}: Status - {data['status']}, Firmware - {data['firmware']}, Last Seen - {data['last_seen']}."
        except requests.RequestException as e:
            return f"Failed to retrieve info for Device {device_id}: {str(e)}."
    
    def lookup_topology(self, device_id):
        try:
            response = requests.get(f"https://network_structure/api/topology/{device_id}")
            response.raise_for_status()
            data = response.json()
            return f"Device {device_id} is connected to Controller {data['controller']}, Switch {data['switch']}, Neighbors {data['neighbors']}."
        except requests.RequestException as e:
            return f"Failed to retrieve topology for Device {device_id}: {str(e)}."
    
    
    def search_threat_intel(self, ip_address):
        try:
            response = requests.get(f"https://threat_intel/api/ip/{ip_address}")
            response.raise_for_status()
            data = response.json()
            return f"Threat Intel for IP {ip_address}: Reputation - {data['reputation']}, Threats - {data['threats']}."
        except requests.RequestException as e:
            return f"Failed to retrieve Threat Intel for IP {ip_address}: {str(e)}."