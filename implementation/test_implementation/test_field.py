import gym
import time
import json
import requests
import pandas as pd
from typing import Union, List, Dict, Any, Optional
from requests.auth import HTTPBasicAuth

# Secure credential handling
import os
USERNAME = os.environ.get('API_USERNAME', 'default_username')
PASSWORD = os.environ.get('API_PASSWORD', 'default_password')

# Helper class for text space in gym
class textSpace:
    def __init__(self):
        pass
    
    def sample(self):
        return ""

class NetworkEnv(gym.Env):
    def __init__(self, login_tokens={}):
        super().__init__()
        self.current_alert = None
        self.current_device = None
        self.action_results = []
        self.timestamp = int(time.time()*1000)
        self.steps = 0
        self.answer = None
        self.observation_space = self.action_space = textSpace()
        self.login_tokens = login_tokens
        self.dnac_geopage = None
        self.netbrain_url = None
        self.sevone_url = None
   
    def _get_obs(self):
        return self.obs
   
    def _get_info(self):
        return {
            "steps": self.steps,
            "answer": self.answer,
            "current_device": self.current_device,
            "action_results": self.action_results,
        }
   
    def refresh_login_tokens(self):
        # more login token can be added if there is further need, however do notice that: try not to add excessive tokens
        if self.dnac_geopage is None: 
            raise ValueError('Please make sure the dnac geo location is set!')
        dnac_token = self.get_DNAC_auth_token()
        netbrain_token = self.get_netbrain_auth_token()
        sevone_token = self.get_SevOne_auth()
        self.login_tokens.update({'DNAC': dnac_token, 'NetBrain': netbrain_token, 'SevOne': sevone_token})
   
    def get_dnac_geopage(self, region):
        if region.lower() == 'europe': 
            return 'https://nlamem1-dna.merck.com/'
        elif region.lower() == 'america': 
            return 'https://usktcm1-dna.merck.com/'
        elif region.lower() == 'asia': 
            return 'https://sgskcm1-dna.merck.com/'
        raise ValueError('Currently Cisco Catalyst Center runs only for Europe, America and Asia (Specify one of these three)')
   
    def set_dnac_geopage(self, dnac_region):
        self.dnac_geopage = self.get_dnac_geopage(dnac_region)
 
    def set_timestamp(self, time_value):
        # make sure the timestamp is in milisecond
        self.timestamp = time_value
   
    def set_current_device(self, device_name):
        self.current_device = device_name
 
    def reset(self, device_name=None, alert_info=None, return_info=False,
              dnac_region=None, netbrain_url="https://netbrain.merck.com/", 
              sevone_url="https://sevone.merck.com/",
              empty_login_tokens=True, refresh_login_tokens=False, timestamp=None):
        self.set_dnac_geopage(dnac_region=dnac_region)
        self.netbrain_url = netbrain_url
        self.sevone_url = sevone_url
        self.timestamp = timestamp if timestamp else int(time.time()*1000)
        if empty_login_tokens: 
            self.login_tokens = {}
        if refresh_login_tokens: 
            self.refresh_login_tokens()
        self.obs = "Ready to diagnose. Use actions like GetDeviceInfo[], LookupAssociatedEvents[], and Finish[].\n"
        self.current_alert = alert_info
        self.current_device = device_name
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
       
        if action.startswith("GetWiFiDeviceInfo[") and action.endswith("]"):
            device_id = action[len("GetWiFiDeviceInfo["):-1]
            self.obs = self.get_dnac_devices_detail_by_id(device_id=device_id)
        elif action.startswith("LookupWiFiAssociatedEvents[") and action.endswith("]"):
            device_id = action[len("LookupWiFiAssociatedEvents["):-1]
            self.obs = self.get_dnac_devices_events_by_id(device_name=device_id)
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
   
    # -------------------------------  Retrieval Tools  --------------------------------------
    def fetch_with_retry(self, endpoint, headers, data_params=None, retries=3, timeout_value=60):
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, params=data_params, headers=headers, timeout=timeout_value, verify=False)
                response.raise_for_status()
                data = response.json()
                return data['response']
            except requests.exceptions.Timeout as e:
                print(f"Timeout error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep((1.5) ** attempt)  # backoff for API
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep((1.5) ** attempt)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for URL: {endpoint}. Error: {e}")
                if attempt < retries - 1:
                    time.sleep((1.5) ** attempt)  # backoff for API
                else:
                    print(f"All retries failed for URL: {endpoint}")
                    return None 
                
    # API methods implementation (simplified for brevity)
    def get_DNAC_auth_token(self, username=None, password=None):
        # Simplified implementation
        username = username or USERNAME
        password = password or PASSWORD
        return "mock_dnac_token"  # Replace with actual implementation
        
    def get_netbrain_auth_token(self, username=None, password=None):
        # Simplified implementation  
        username = username or USERNAME
        password = password or PASSWORD
        return "mock_netbrain_token"  # Replace with actual implementation
        
    def get_SevOne_auth(self, username=None, password=None):
        # Simplified implementation
        username = username or USERNAME
        password = password or PASSWORD
        return "mock_sevone_token"  # Replace with actual implementation
        
    def get_dnac_devices_detail_by_id(self, device_id, data_params=None, identifier="nwDeviceName", *args, **kwargs):
        # Simplified mock implementation
        # In production, this would call the actual API
        return {
            "nwDeviceName": device_id,
            "connectivityStatus": 1,
            "ipAddress": "192.168.1.100",
            "softwareVersion": "8.10.151.0",
            "location": "Building 1, Floor 2",
            "ethernetMac": "00:11:22:33:44:55"
        }
        
    def get_dnac_devices_events_by_id(self, device_name=None, limit=10, 
                                      start_time=None, end_time=None, 
                                      data_params=None, *args, **kwargs):
        # Simplified mock implementation
        # In production, this would call the actual API
        if device_name is None: 
            raise ValueError('Please provide a specific device in its device name')
            
        return [
            {"eventId": "123", "severity": "CRITICAL", "type": "AP_DOWN", "timestamp": int(time.time()*1000)},
            {"eventId": "124", "severity": "MAJOR", "type": "HIGH_CPU", "timestamp": int(time.time()*1000) - 3600000}
        ]

    def get_dnac_AP_config(self, ethernet_macAddress=None, *args, **kwargs):
        # Simplified mock implementation
        return {
            "controllerName": "WLC_Main",
            "channel": "36",
            "tx_power": "high",
            "ssid": "CorporateWiFi",
            "security": "WPA2-Enterprise"
        }

# Enhanced AP Environment
class APEnv(NetworkEnv):
    def __init__(self, login_tokens={}):
        super().__init__(login_tokens)
        self.current_device_info = None
   
    def reset(self, device_info=None, *args, **kwargs):
        observation = super().reset(*args, **kwargs)
        self.current_device_info = device_info
        return observation
 
    def step(self, action):
        reward = 0
        done = False
        action = action.strip()
        
        if self.answer is not None:
            done = True
            return self.obs, reward, done, self._get_info()
            
        if action.startswith("GetDeviceInfo[") and action.endswith("]"):
            device_id = action[len("GetDeviceInfo["):-1]
            print(f'Getting device info for: {device_id}')
            device_info = self.get_dnac_devices_detail_by_id(device_id=device_id)
            self.current_device_info = device_info
            self.current_device = device_info['nwDeviceName']
            self.obs = device_info
            
        elif action.startswith("GetDeviceConfig[") and action.endswith("]"):
            device_id = action[len("GetDeviceConfig["):-1]
            device_info = self.get_dnac_devices_detail_by_id(device_id=device_id)
            self.current_device_info = device_info
            self.current_device = device_info['nwDeviceName']
            self.obs = self.get_dnac_AP_config(ethernet_macAddress=device_info['ethernetMac'])         
            
        elif action.startswith("Get1hrEventsForDevice[") and action.endswith("]"):
            device_id = action[len("Get1hrEventsForDevice["):-1]
            self.obs = self.get_device_events_in_past_1hr(device_name=device_id)
            
        elif action.startswith("Get2dayEventsForDevice[") and action.endswith("]"):
            device_id = action[len("Get2dayEventsForDevice["):-1]
            self.obs = self.get_device_events_in_past_2d(device_name=device_id)
            
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
       
    def get_device_events_in_past_1hr(self, device_name):
        return self.get_dnac_devices_events_by_id(
            start_time=int((self.timestamp-3600000)/1000), 
            end_time=int(self.timestamp/1000), 
            device_name=device_name, 
            limit=20
        )
   
    def get_device_events_in_past_2d(self, device_name):
        return self.get_dnac_devices_events_by_id(
            start_time=int((self.timestamp-172800000)/1000), 
            end_time=int(self.timestamp/1000), 
            device_name=device_name, 
            limit=20
        )

# Network Agent Implementation with GPT integration
class NetworkAgent:
    def __init__(self, env: Union[gym.Wrapper, gym.Env], valid_prefixes=None):
        self.env = env
        self.valid_prefixes = valid_prefixes or []
 
    def _llm(self, messages, stop=None, *args, **kwargs):
        """
        This is a placeholder for the LLM call. You'll need to replace this
        with your actual implementation using OpenAI, Azure, or other LLM APIs.
        """
        # Placeholder response
        response = {
            "choices": [{
                "message": {
                    "content": "Thought 1: I need to check the device information first.\nAction 1: GetDeviceInfo[AP12345]"
                }
            }]
        }
        return response
 
    def _step(self, action):
        attempts = 0
        while attempts < 10:
            try:
                return self.env.step(action)
            except requests.exceptions.Timeout:
                attempts += 1
                if attempts == 10:
                    raise Exception("Max retry attempts reached for step action.")
   
    def set_valid_prefixes(self, valid_prefixes: list):
        self.valid_prefixes = valid_prefixes
 
    def reset_env(self, valid_prefixes: list = None, *args, **kwargs):
        self.env.reset(*args, **kwargs)
        if valid_prefixes is not None:
            self.valid_prefixes = valid_prefixes
 
    def _react(self, initial_prompt: str, max_num_steps: int = 8, to_print: bool = False):
        """Implementation of ReAct paradigm with the LLM"""
        # Implementation as in your original code
        # Removed for brevity - refer to original NetworkAgent._react method
        messages = [{"role": "system", "content": initial_prompt}]
        n_calls, n_badcalls = 0, 0
        done = False
       
        # We begin the iterative ReAct loop
        for i in range(1, max_num_steps + 1):
            n_calls += 1
            user_msg = f"Thought {i}:"
            messages.append({"role": "user", "content": user_msg})
           
            # Call the LLM
            thought_action_response = self._llm(messages, stop=[f"\nObservation {i}:"])
            assistant_text = thought_action_response["choices"][0]["message"]["content"]
           
            if to_print:
                print(assistant_text)
           
            # We try to parse out "Thought X" and "Action X" from the LLM's output
            try:
                segments = assistant_text.split(f"\nAction {i}:")
                if len(segments) == 2:
                    thought_str = segments[0].strip()
                    action_str = segments[1].strip()
                    
                    # If the LLM repeated "Thought i:" in the text, remove it
                    if thought_str.startswith(f"Thought {i}:"):
                        thought_str = thought_str[len(f"Thought {i}:"):].strip()
                    
                    # Add them to conversation for record
                    messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
                    messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
                
                else:
                    raise ValueError("Assistant response not in expected Thought/Action format.")
           
            except Exception as e:
                # If parsing fails, attempt a fallback
                n_badcalls += 1
                # Take the first line as thought, re-ask for action
                splitted = assistant_text.strip().split("\n", 1)
                if splitted:
                    fallback_thought = splitted[0]
                else:
                    fallback_thought = "No valid thought parsed."
                
                # We re-ask specifically for the action
                action_request_msg = f"Thought {i}: {fallback_thought}\nAction {i}:"
                new_resp = self._llm(messages + [{"role": "user", "content": action_request_msg}])
                action_str = new_resp["choices"][0]["message"]["content"].strip()
           
            # Verify the action format
            if not any(action_str.startswith(pref) and action_str.endswith("]") for pref in self.valid_prefixes):
                # Invalid action format
                obs_str = f"Invalid action: '{action_str}'. Please use one of {self.valid_prefixes}."
                messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
                if to_print:
                    print(f"Observation {i}: {obs_str}")
                continue
           
            # Run the environment step
            obs, r, done_flag, info = self._step(action_str)
            # Format the observation
            obs_str = f"Observation {i}: {obs}"
            messages.append({"role": "system", "content": obs_str})
           
            if to_print:
                print(f"Thought {i}: {thought_str}\nAction {i}: {action_str}\nObservation {i}: {obs}\n")
           
            # Check if we're done
            if done_flag:
                done = True
                break
       
        # If we finished all steps without done, forcibly finish
        if not done:
            force_finish_action = f"Finish[No conclusion within {max_num_steps} steps. Suggest manual follow-up.]"
            obs, r, done_flag, info = self._step(force_finish_action)
            messages.append({"role": "system", "content": f"Observation End: {obs}"})
            done = True
       
        # Info logging
        info.update({
            "n_calls": n_calls,
            "n_badcalls": n_badcalls,
            "traj": messages
        })
       
        if to_print:
            print(info)
        
        return r, info

# The ApAnalystAgent implementation with diagnose_one_AP method
class APAnalystAgent(NetworkAgent):
    def __init__(self, env: APEnv):
        valid_prefixes = [
            "GetDeviceInfo[", 
            "GetDeviceConfig[", 
            "Get1hrEventsForDevice[", 
            "Get2dayEventsForDevice[", 
            "Finish["
        ]
        super().__init__(env, valid_prefixes)
        
    def diagnose_one_AP(self, 
                        ap_name: str, 
                        dnac_region: str = "europe", 
                        max_steps: int = 8, 
                        to_print: bool = True):
        """
        Diagnose a single Access Point using the ReAct paradigm
        
        Parameters:
        -----------
        ap_name : str
            The name of the access point to diagnose
        dnac_region : str
            Region for DNAC (europe, america, asia)
        max_steps : int
            Maximum number of steps for the ReAct loop
        to_print : bool
            Whether to print diagnostic steps
            
        Returns:
        --------
        dict: Diagnosis information including trajectory and conclusion
        """
        # Reset the environment with the AP name
        self.env.reset(
            device_name=ap_name,
            dnac_region=dnac_region,
            refresh_login_tokens=True
        )
        
        # Use the appropriate instruction for the AP analysis
        instruction = self._get_ap_instruction()
        
        # Run the ReAct loop
        _, info = self._react(
            initial_prompt=instruction,
            max_num_steps=max_steps,
            to_print=to_print
        )
        
        # Extract the diagnosis from the answer in the environment
        diagnosis = self.env._get_info().get("answer", "No diagnosis provided")
        
        return {
            "ap_name": ap_name,
            "diagnosis": diagnosis,
            "steps": self.env.steps,
            "trajectory": info.get("traj", [])
        }
        
    def _get_ap_instruction(self):
        """Get the instruction prompt for AP diagnosis"""
        # Using the advanced instruction from your code
        return """
You are an advanced network engineer tasked with diagnosing and analyzing potential issues for Access Points (APs). Your objective is to identify any potential issues and to evaluate the condition/health/status of the for Cisco Access Points.

You will diagnose network devices using interleaving Thought, Action, and Observation steps. Thought can reason about the current situation, which leads to an action. And the action will return an observation, which you will reason and think about for insights that lead to next action.

Action can be one of the following types:

1. GetDeviceInfo[device_name]
   - Retrieves basic data about the device (AP or WLC).
   - Returns JSON with fields like:
     - "nwDeviceName"
     - "connectivityStatus" (<=0 ⇒ device is DOWN, >0 ⇒ device is UP)
     - "ipAddress"
     - "softwareVersion"
     - "location"
     - "ethernetMac"

2. GetDeviceConfig[device_name]
   - Retrieves the AP's wireless configuration (radio frequency info, SSIDs, etc.).
   - Also reveals the controller that this AP is connected to, if any.

3. Get1hrEventsForDevice[device_name]
   - Retrieves the last 1 hour's assurance events (AP_DOWN, AUTH_FAILURES, etc.).

4. Get2dayEventsForDevice[device_name]
   - Retrieves the last 2 days' assurance events.

5. Finish[summary]
   - Ends the diagnostic session with an actionable recommendation.

ReAct Format:
- "Thought X": your chain-of-thought.
- "Action X": one of the five actions above.
- "Observation X": the environment's returned JSON/text.

Key Points:
- If you suspect the AP's controller might be relevant, first call GetDeviceConfig[theAP] to learn controllerName, then call GetDeviceInfo[thatControllerName] (or events on that controller) if needed.
- If connectivityStatus <= 0 in GetDeviceInfo, that device is effectively DOWN.
- You can do up to 8 steps total.
- Provide an actionable suggestion in Finish[...].

As an advanced network engineer, you should:
- Use technical language and thorough reasoning.
- Start by gathering basic information about the device.
- Check for recent events to identify immediate issues.
- Examine the device's configuration for potential problems.
- Conclude with a comprehensive diagnosis summary.
"""

# Example usage
if __name__ == "__main__":
    # Create the environment
    ap_env = APEnv()
    
    # Create the agent
    agent = APAnalystAgent(ap_env)
    
    # Run a diagnosis
    result = agent.diagnose_one_AP("AP12345", dnac_region="europe")
    
    # Print the diagnosis
    print(f"Diagnosis: {result['diagnosis']}")


# ------------------
def is_valid_action(action_str, valid_prefixes):
    """
    Improved action validation that handles edge cases and whitespace issues.
    
    Parameters:
    -----------
    action_str : str
        The action string to validate
    valid_prefixes : list
        List of valid action prefixes
        
    Returns:
    --------
    bool: Whether the action is valid
    """
    # Strip any whitespace
    action_str = action_str.strip()
    
    # Check if the action ends with "]"
    if not action_str.endswith("]"):
        return False
    
    # Check if the action starts with any of the valid prefixes
    for prefix in valid_prefixes:
        if action_str.startswith(prefix):
            # Extract the parameter part
            param_start = len(prefix)
            param_end = len(action_str) - 1  # Exclude the closing bracket
            
            # Make sure there's an actual parameter
            if param_end > param_start:
                return True
                
    return False

# Enhanced version of the parse_thought_action function
def parse_thought_action(response_text, step_index):
    """
    More robust parsing of thought and action from LLM response.
    
    Parameters:
    -----------
    response_text : str
        The raw text response from the LLM
    step_index : int
        The current step number
        
    Returns:
    --------
    tuple: (thought_str, action_str)
    """
    import re
    
    # Clean up the text
    response_text = response_text.strip()
    
    # Look for thought pattern with flexible whitespace
    thought_pattern = rf"Thought\s*{step_index}\s*:(.*?)(?:\nAction\s*{step_index}\s*:|$)"
    thought_match = re.search(thought_pattern, response_text, re.DOTALL)
    
    # Look for action pattern with flexible whitespace
    action_pattern = rf"Action\s*{step_index}\s*:(.*?)$"
    action_match = re.search(action_pattern, response_text, re.DOTALL)
    
    # Extract thought
    thought_str = ""
    if thought_match:
        thought_str = thought_match.group(1).strip()
    else:
        # Fallback: take first line or section
        lines = response_text.split('\n')
        if lines:
            thought_str = lines[0].strip()
            if thought_str.startswith(f"Thought {step_index}:"):
                thought_str = thought_str[len(f"Thought {step_index}:"):].strip()
    
    # Extract action
    action_str = ""
    if action_match:
        action_str = action_match.group(1).strip()
    
    return thought_str, action_str

# Here's how to modify the _react method to use these improved functions
def improved_react(self, initial_prompt, max_num_steps=8, to_print=False):
    """
    Enhanced _react method with better action parsing.
    """
    messages = [{"role": "system", "content": initial_prompt}]
    n_calls, n_badcalls = 0, 0
    done = False
    
    for i in range(1, max_num_steps + 1):
        n_calls += 1
        user_msg = f"Thought {i}:"
        messages.append({"role": "user", "content": user_msg})
        
        # Call the LLM
        thought_action_response = self._llm(messages, stop=[f"\nObservation {i}:"])
        assistant_text = thought_action_response["choices"][0]["message"]["content"]
        
        if to_print:
            print(f"Raw LLM response: {assistant_text}")
        
        # Use improved parsing
        thought_str, action_str = parse_thought_action(assistant_text, i)
        
        # If action parsing failed, try a fallback approach
        if not action_str:
            n_badcalls += 1
            # Re-ask specifically for the action
            action_request_msg = f"Thought {i}: {thought_str}\nAction {i}:"
            new_resp = self._llm(messages + [{"role": "user", "content": action_request_msg}])
            action_str = new_resp["choices"][0]["message"]["content"].strip()
        
        # Add thought and action to conversation history
        messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
        messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
        
        # Improved action validation
        if not is_valid_action(action_str, self.valid_prefixes):
            # Provide helpful error message with examples
            example_actions = [f"{prefix}example_param]" for prefix in self.valid_prefixes]
            obs_str = (f"Invalid action format: '{action_str}'. "
                      f"Please use one of the following formats: {example_actions}")
            messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
            if to_print:
                print(f"Observation {i}: {obs_str}")
            continue
        
        # Execute the action in the environment
        try:
            obs, r, done_flag, info = self._step(action_str)
            obs_str = f"Observation {i}: {obs}"
        except Exception as e:
            # Handle execution errors gracefully
            obs_str = f"Observation {i}: Error executing action: {str(e)}"
            if to_print:
                print(f"Action execution error: {e}")
        
        messages.append({"role": "system", "content": obs_str})
        
        if to_print:
            print(f"Thought {i}: {thought_str}")
            print(f"Action {i}: {action_str}")
            print(f"Observation {i}: {obs if 'obs' in locals() else 'error'}\n")
        
        # Check if we're done
        if 'done_flag' in locals() and done_flag:
            done = True
            break
    
    # If we finished all steps without done, forcibly finish
    if not done:
        force_finish_action = f"Finish[No conclusion within {max_num_steps} steps. Suggest manual follow-up.]"
        try:
            obs, r, done_flag, info = self._step(force_finish_action)
            messages.append({"role": "system", "content": f"Observation End: {obs}"})
        except Exception as e:
            messages.append({"role": "system", "content": f"Observation End: Error in final step: {str(e)}"})
    
    # Info logging
    info = info if 'info' in locals() else {}
    info.update({
        "n_calls": n_calls,
        "n_badcalls": n_badcalls,
        "traj": messages
    })
    
    if to_print:
        print(info)
    
    return r if 'r' in locals() else 0, info


def normalize_action_string(action_str):
    """
    Clean up and normalize action strings from LLM to handle common formatting issues.
    
    This function addresses several common patterns where LLMs incorrectly format actions:
    1. Double "Action X:" prefixes
    2. Missing brackets in Finish actions
    3. Extraneous text in action strings
    
    Parameters:
    -----------
    action_str : str
        The raw action string from the LLM
        
    Returns:
    --------
    str: Properly formatted action string
    """
    import re
    
    # Strip whitespace first
    action_str = action_str.strip()
    
    # 1. Remove duplicate "Action X:" prefixes
    action_prefix_pattern = r'^Action\s+\d+:\s+'
    action_str = re.sub(action_prefix_pattern, '', action_str)
    
    # 2. Handle Finish action without brackets
    if action_str.startswith('Finish') and '[' not in action_str:
        # Extract everything after "Finish"
        content = action_str[len('Finish'):].strip()
        # If content doesn't start with '[', wrap everything in brackets
        if content and not content.startswith('['):
            return f'Finish["{content}"]'
    
    # 3. If it has a valid prefix but no closing bracket, add one
    valid_prefixes = ['GetDeviceInfo', 'GetDeviceConfig', 'Get1hrEventsForDevice', 
                      'Get2dayEventsForDevice', 'Finish']
    
    for prefix in valid_prefixes:
        if action_str.startswith(prefix) and '[' in action_str and ']' not in action_str:
            return f"{action_str}]"
    
    # Return the cleaned action string
    return action_str


# Enhanced version of the parse_thought_action function
def parse_thought_action(response_text, step_index):
    """
    More robust parsing of thought and action from LLM response.
    
    Parameters:
    -----------
    response_text : str
        The raw text response from the LLM
    step_index : int
        The current step number
        
    Returns:
    --------
    tuple: (thought_str, action_str)
    """
    import re
    
    # Clean up the text
    response_text = response_text.strip()
    
    # Look for thought pattern with flexible whitespace
    thought_pattern = rf"(?:Thought\s*{step_index}\s*:)?(.*?)(?:Action\s*{step_index}\s*:|$)"
    thought_match = re.search(thought_pattern, response_text, re.DOTALL)
    
    # Look for action pattern with flexible whitespace
    action_pattern = rf"Action\s*{step_index}\s*:(.*?)$"
    action_match = re.search(action_pattern, response_text, re.DOTALL)
    
    # Extract thought
    thought_str = ""
    if thought_match:
        thought_str = thought_match.group(1).strip()
    else:
        # Fallback: take first line or section
        lines = response_text.split('\n')
        if lines:
            thought_str = lines[0].strip()
            if thought_str.startswith(f"Thought {step_index}:"):
                thought_str = thought_str[len(f"Thought {step_index}:"):].strip()
    
    # Extract action
    action_str = ""
    if action_match:
        action_str = action_match.group(1).strip()
        # Apply normalization to fix common formatting issues
        action_str = normalize_action_string(action_str)
    
    return thought_str, action_str


def is_valid_action(action_str, valid_prefixes):
    """
    Improved action validation that handles edge cases and whitespace issues.
    
    Parameters:
    -----------
    action_str : str
        The action string to validate
    valid_prefixes : list
        List of valid action prefixes
        
    Returns:
    --------
    bool: Whether the action is valid
    """
    # Apply normalization first to fix formatting issues
    action_str = normalize_action_string(action_str)
    
    # Strip any whitespace
    action_str = action_str.strip()
    
    # Check if the action ends with "]"
    if not action_str.endswith("]"):
        return False
    
    # Check if the action starts with any of the valid prefixes
    for prefix in valid_prefixes:
        if action_str.startswith(prefix):
            # Extract the parameter part
            param_start = len(prefix)
            param_end = len(action_str) - 1  # Exclude the closing bracket
            
            # Make sure the parameter is properly enclosed in brackets
            if not action_str[param_start:param_start+1] == "[":
                return False
                
            # Make sure there's an actual parameter
            if param_end > param_start + 1:
                return True
                
    return False


