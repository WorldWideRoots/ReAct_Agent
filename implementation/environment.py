import os, json, requests, aiohttp, time
from requests.auth import HTTPBasicAuth

import pymssql
import pandas as pd
import gymnasium as gym


class textSpace(gym.spaces.Space):
    def ccontains(self, x) -> bool:
        return isinstance(x, str)

class NetworkEnv(gym.Env):
    def __init__(self, login_tokens={}):
        super().__init__()
        self.current_alert = None
        self.current_device = None
        self.action_results = []
        self.timestamp = int(time.time())*1000
        self.steps=0
        self.answer=None
        self.observation_space = self.action_space = textSpace()
        self.login_tokens = login_tokens
        self.obs=None

    def _get_obs (self):
        return self.obs
    
    def _get_info(self):
        return {
            'steps': self.steps,
            'answer': self.answer,
            'current_device': self.current_device,
            'action_results': self.action_results
        }
    
    def refresh_login_tokens(self, login_tokens):
        self.login_tokens = login_tokens

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp

    def set_current_device(self, current_device):
        self.current_device = current_device
        

    def reset(self, device_name, alert_info, return_info, timestamp=None, login_tokens=None):
        self.current_alert = alert_info
        self.current_device = device_name
        self.answer = None
        self.obs = None
        self.steps = 0
        self.action_results = []
        if login_tokens:
            self.refresh_login_tokens(login_tokens)
        if timestamp:
            self.set_timestamp(timestamp)
        return self._get_obs(), self._get_info() if return_info else self._get_obs()
    
    def step(self, action):
        reward = 0 
        done = False
        action = action.strip()

        if self.answer is not None:
            done-True
            return self.obs, reward, done, self._get_info()
        
        self.steps += 1
        self.action_results.append({"action": action, "observation": self.obs})

        return self.obs, reward, done, self._get_info()
    

    def fetch_with_retry(self, endpoint, headers, data_params=None, retries=3, timeout=60):
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, headers=headers, params=data_params, timeout=timeout, verify=False)
                response.raise_for_status()
                data = response.json()
                return data
            except Exception as e:
                print(f"Failed to fetch data from {endpoint} with error {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(2**attempt)

    def get_DNAC_auth_token(self, dnac_ip, username, password):
        endpoint = f"https://{dnac_ip}/dna/system/api/v1/auth/token"
        headers = {"Content-Type": "application/json"}
        data = {"username": username, "password": password}
        response = requests.post(endpoint, headers=headers, data=json.dumps(data), verify=False)
        response.raise_for_status()
        data = response.json()
        return data["Token"]

    def get_DNAC_device_detail_by_id(self, dnac_ip, token, device_id, data_params:dict={}):
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/device-detail"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}
        data_params.update({'searchBy': device_id, 'identifier': "nwDeviceName"})
        try: 
            data = self.fetch_with_retry(endpoint, headers, data_params)
            return data
        except Exception as e:
            print(f"Failed to get device detail for {device_id} with error {e}")
            return None
        
    
    def get_DNAC_device_events_by_id(self, dnac_ip, token, device_id, start_time, end_time, data_params:dict={}):
        data_params.update({
            'deviceFamily': "Unified AP",
            'startTime': start_time,
            'endTime': end_time,
            'networkDeviceName': device_id
        })
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/assuranceEvents"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}
        try:
            data = self.fetch_with_retry(endpoint, headers, data_params)
            return data
        except Exception as e:
            print(f"Failed to get events for {device_id} with error {e}")
            return None
        
    def get_dnac_AP_config(self, dnac_ip, token, ethernet_macAddress:str=None):
        data_params = {'key': ethernet_macAddress} 
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/wireless/accesspoint-configuration/summary"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}
        try:
            data = self.fetch_with_retry(endpoint, headers, data_params)
            return data
        except Exception as e:
            print(f"Failed to get AP config for {ethernet_macAddress} with error {e}")
            return None
        
    
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
        if action.startwith("GetWiFiDeviceInfo[") and action.endwith("]"):
            device_id = action[len("GetWiFiDeviceInfo["): -1]
            device_info = self.get_DNAC_device_detail_by_id(self.current_device_info["dnac_ip"], self.login_tokens["dnac"], device_id)
            self.current_device_info = device_info
            self.current_device = device_info['nwDeviceName']
            self.obs = device_info
        elif action.startwith("GetWiFiDeviceConfig[") and action.endwith("]"):
            device_id = action[len("GetWiFiDeviceConfig["): -1]
            device_info = self.get_DNAC_device_detail_by_id(self.current_device_info["dnac_ip"], self.login_tokens["dnac"], device_id)
            self.current_device_info = device_info
            self.current_device = device_info['nwDeviceName']
            self.obs = self.get_dnac_AP_config(ethernet_macAddress=device_info['ethernetMac'])
        elif action.startwith("Get1hrEventsForDevice[") and action.endwith("]"):
            device_id = action[len("Get1hrEventsForDevice["): -1]
            self.obs = self.get_device_events_in_past_1hr(self.current_device_info["dnac_ip"], self.login_tokens["dnac"], device_id)
        elif action.startwith("Get2dayEventsForDevice[") and action.endwith("]"):
            device_id = action[len("Get2dayEventsForDevice["): -1]
            self.obs = self.get_device_events_in_past_2day(self.current_device_info["dnac_ip"], self.login_tokens["dnac"], device_id)
        elif action.startwith("Finish[") and action.endwith("]"):
            summary = action[len("Finish["): -1]
            self.answer - summary
            done = True
            self.obs = f"Episode finished, reward = {reward}\n"
        else: 
            self.obs = f"Invalid action {action}\n"
        self.steps += 1
        self.action_results.append({"action": action, "observation": self.obs})
        return self.obs, reward, done, self._get_info()
        
    def get_device_events_in_past_1hr(self, dnac_ip, token, device_id):
        start_time = self.timestamp - 3600000
        end_time = self.timestamp
        return self.get_DNAC_device_events_by_id(dnac_ip, token, device_id, start_time, end_time)
    
    def get_device_events_in_past_2day(self, dnac_ip, token, device_id):
        start_time = self.timestamp - 172800000
        end_time = self.timestamp
        return self.get_DNAC_device_events_by_id(dnac_ip, token, device_id, start_time, end_time)
    






    import os
import json
import time
import requests
import gymnasium as gym
from typing import Dict, Any

# Disable insecure request warnings if using self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class textSpace(gym.spaces.Space):
    """Simple text space for demonstration."""
    def __init__(self):
        super().__init__(shape=None, dtype=None)

    def contains(self, x) -> bool:
        return isinstance(x, str)


class NetworkEnv(gym.Env):
    """
    Base network environment.
    Provides common methods for fetching from Cisco DNAC with retries, plus managing tokens, etc.
    """

    def __init__(self, login_tokens: Dict[str, str] = None):
        super().__init__()
        self.current_alert = None
        self.current_device = None
        self.action_results = []
        self.timestamp = int(time.time()) * 1000
        self.steps = 0
        self.answer = None
        self.observation_space = self.action_space = textSpace()
        self.login_tokens = login_tokens or {}
        self.obs = None

    def _get_obs(self):
        return self.obs

    def _get_info(self):
        return {
            "steps": self.steps,
            "answer": self.answer,
            "current_device": self.current_device,
            "action_results": self.action_results
        }

    def refresh_login_tokens(self, login_tokens: Dict[str, str]):
        self.login_tokens = login_tokens

    def set_timestamp(self, timestamp: int):
        self.timestamp = timestamp

    def set_current_device(self, current_device: str):
        self.current_device = current_device

    def reset(
        self,
        device_name: str = None,
        alert_info: Any = None,
        return_info: bool = True,
        timestamp: int = None,
        login_tokens: Dict[str, str] = None
    ):
        """
        Custom reset. This is not the standard Gym signature, but we adapt it to your use-case.
        """
        self.current_alert = alert_info
        self.current_device = device_name
        self.answer = None
        self.obs = None
        self.steps = 0
        self.action_results = []

        if login_tokens:
            self.refresh_login_tokens(login_tokens)
        if timestamp:
            self.set_timestamp(timestamp)

        if return_info:
            return self._get_obs(), self._get_info()
        else:
            return self._get_obs()

    def step(self, action: str):
        """
        Basic step logic. Subclasses should override to parse and execute specific actions.
        """
        reward = 0
        done = False
        action = action.strip()

        if self.answer is not None:
            done = True
            return self.obs, reward, done, self._get_info()

        self.steps += 1
        self.action_results.append({"action": action, "observation": self.obs})

        return self.obs, reward, done, self._get_info()

    def fetch_with_retry(
        self,
        endpoint: str,
        headers: Dict[str, str],
        data_params: Dict[str, Any] = None,
        retries: int = 3,
        timeout: int = 60
    ):
        """Basic GET with retry logic."""
        for attempt in range(retries):
            try:
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params=data_params,
                    timeout=timeout,
                    verify=False
                )
                response.raise_for_status()
                data = response.json()
                return data
            except Exception as e:
                print(f"Attempt {attempt+1} - Failed to fetch {endpoint}: {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)

    def get_DNAC_auth_token(self, dnac_ip: str, username: str, password: str) -> str:
        """Obtain an auth token from DNAC."""
        endpoint = f"https://{dnac_ip}/dna/system/api/v1/auth/token"
        headers = {"Content-Type": "application/json"}
        payload = {"username": username, "password": password}
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("Token")


class APEnv(NetworkEnv):
    """
    An environment specialized for AP (Access Point) diagnostics with DNAC.
    Includes multiple actions that retrieve device detail, config, events, etc.
    """

    def __init__(self, login_tokens: Dict[str, str] = None):
        super().__init__(login_tokens)
        self.current_device_info = None

    def reset(self, device_info=None, *args, **kwargs):
        observation = super().reset(*args, **kwargs)
        self.current_device_info = device_info
        return observation

    def step(self, action: str):
        reward = 0
        done = False
        action = action.strip()

        # If we already have a final answer, end the episode
        if self.answer is not None:
            done = True
            return self.obs, reward, done, self._get_info()

        # Parse and execute recognized actions
        if action.startswith("GetDeviceDetail[") and action.endswith("]"):
            device_id = action[len("GetDeviceDetail[") : -1]
            self.obs = self.get_device_detail(device_id)

        elif action.startswith("GetDeviceConfig[") and action.endswith("]"):
            device_id = action[len("GetDeviceConfig[") : -1]
            self.obs = self.get_device_config(device_id)

        elif action.startswith("GetAssuranceDeviceEvents[") and action.endswith("]"):
            # Potentially parse a timeframe or device out of the brackets
            # e.g. "GetAssuranceDeviceEvents[AP-22-1B-09, past2Days]"
            content_str = action[len("GetAssuranceDeviceEvents[") : -1]
            # For simplicity, let's assume it's "deviceId,timeframe"
            parts = [p.strip() for p in content_str.split(",")]
            if len(parts) == 2:
                device_id = parts[0]
                timeframe = parts[1]
                self.obs = self.get_device_events(device_id, timeframe)
            else:
                # fallback
                device_id = content_str
                self.obs = self.get_device_events(device_id, "pastHour")

        elif action.startswith("GetWirelessDeviceConfig[") and action.endswith("]"):
            mac_address = action[len("GetWirelessDeviceConfig[") : -1]
            self.obs = self.get_wireless_ap_config(mac_address)

        elif action.startswith("Finish[") and action.endswith("]"):
            summary = action[len("Finish[") : -1]
            self.answer = summary
            done = True
            self.obs = f"Episode finished, reward = {reward}\n"

        else:
            # If it's none of the recognized actions
            self.obs = f"Invalid action: {action}\n"

        self.steps += 1
        self.action_results.append({"action": action, "observation": self.obs})
        return self.obs, reward, done, self._get_info()

    # --- Example methods mapping to DNAC endpoints ---

    def get_device_detail(self, device_id: str):
        """
        e.g., GET /dna/intent/api/v1/device-detail?searchBy=<deviceId>&identifier=uuid or nwDeviceName
        Adapting to your environment's approach.
        """
        dnac_ip = self.current_device_info.get("dnac_ip", "") if self.current_device_info else ""
        token = self.login_tokens.get("dnac", "")
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/device-detail"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}
        params = {
            "searchBy": device_id,
            "identifier": "nwDeviceName"
        }
        try:
            data = self.fetch_with_retry(endpoint, headers, params)
            return data
        except Exception as e:
            return {"error": f"get_device_detail failed for {device_id}: {str(e)}"}

    def get_device_config(self, device_id: str):
        """
        e.g., GET /dna/intent/api/v1/network-device/{deviceId}/config
        This requires the device's internal DNAC deviceId (UUID), possibly from get_device_detail.
        """
        dnac_ip = self.current_device_info.get("dnac_ip", "") if self.current_device_info else ""
        token = self.login_tokens.get("dnac", "")
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/network-device/{device_id}/config"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}

        try:
            data = self.fetch_with_retry(endpoint, headers)
            return data
        except Exception as e:
            return {"error": f"get_device_config failed for {device_id}: {str(e)}"}

    def get_device_events(self, device_id: str, timeframe: str = "pastHour"):
        """
        e.g., GET /dna/intent/api/v1/assuranceEvents for specific device, with startTime & endTime
        We'll interpret timeframe = 'pastHour', 'past2Days', etc.
        """
        dnac_ip = self.current_device_info.get("dnac_ip", "") if self.current_device_info else ""
        token = self.login_tokens.get("dnac", "")
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/assuranceEvents"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}

        # Compute startTime/endTime
        end_time = self.timestamp
        if timeframe.lower() == "past2days" or timeframe.lower() == "past2day":
            start_time = end_time - 172800000  # 2 days in ms
        else:
            start_time = end_time - 3600000  # 1 hour in ms

        params = {
            "networkDeviceName": device_id,
            "startTime": start_time,
            "endTime": end_time
        }
        try:
            data = self.fetch_with_retry(endpoint, headers, params)
            return data
        except Exception as e:
            return {"error": f"get_device_events failed for {device_id}: {str(e)}"}

    def get_wireless_ap_config(self, mac_address: str):
        """
        e.g., GET /dna/intent/api/v1/wireless/accesspoint-configuration/summary?key=<ethernetMac>
        """
        dnac_ip = self.current_device_info.get("dnac_ip", "") if self.current_device_info else ""
        token = self.login_tokens.get("dnac", "")
        endpoint = f"https://{dnac_ip}/dna/intent/api/v1/wireless/accesspoint-configuration/summary"
        headers = {"Content-Type": "application/json", "X-Auth-Token": token}
        params = {"key": mac_address}

        try:
            data = self.fetch_with_retry(endpoint, headers, params)
            return data
        except Exception as e:
            return {"error": f"get_wireless_ap_config failed for {mac_address}: {str(e)}"}
