import time
import json
import requests
import pandas as pd
from typing import Union, List, Dict, Any, Optional
import re
import gym

class NetworkAgent:
    """
    A completely redesigned NetworkAgent that implements the ReAct paradigm
    for interacting with network environments using LLMs.
    """
    
    def __init__(self, env: Union[gym.Wrapper, gym.Env], valid_actions=None):
        """
        Initialize the NetworkAgent.
        
        Parameters:
        -----------
        env : gym.Env
            The environment to interact with
        valid_actions : list
            List of valid action prefixes (e.g., 'GetDeviceInfo', 'Finish', etc.)
        """
        self.env = env
        self.valid_actions = valid_actions or []
        
    def set_valid_actions(self, valid_actions: list):
        """Set the list of valid action prefixes."""
        self.valid_actions = valid_actions
        
    def reset_env(self, *args, **kwargs):
        """Reset the environment with specified arguments."""
        return self.env.reset(*args, **kwargs)
    
    def _llm(self, messages, stop=None, *args, **kwargs):
        """
        Call the LLM with the specified messages.
        
        This is a placeholder that should be implemented in a subclass or
        overridden with the actual LLM implementation.
        """
        # Placeholder response for testing
        return {
            "choices": [{
                "message": {
                    "content": "Thought 1: I need to check device info first.\nAction 1: GetDeviceInfo[test-device]"
                }
            }]
        }
    
    def extract_action(self, text, step_number):
        """
        Extract the action from the LLM response text.
        
        This function looks for patterns like "Action X: Command[param]"
        and handles various formatting inconsistencies.
        
        Parameters:
        -----------
        text : str
            The LLM response text
        step_number : int
            The current step number
            
        Returns:
        --------
        str: The extracted action string, or None if no action is found
        """
        # Clean up the input text
        text = text.strip()
        
        # First try to find action with the exact step number
        action_pattern = rf"Action\s*{step_number}\s*:(.*?)(?:\n|$)"
        action_match = re.search(action_pattern, text, re.DOTALL)
        
        if action_match:
            # Extract the action part
            action_text = action_match.group(1).strip()
            
            # Filter out any duplicated "Action X:" prefixes
            action_prefix_pattern = r'^Action\s+\d+:\s+'
            action_text = re.sub(action_prefix_pattern, '', action_text)
            
            # Check for common patterns and fix them
            return self.normalize_action(action_text)
            
        # If no match with step number, try to find any action-like pattern
        general_action_pattern = r"(?:Action|Execute|Run|Do)(?:\s*\d+)?(?:\s*:)?\s*([A-Za-z]+\[[^\]]*\])"
        general_match = re.search(general_action_pattern, text, re.DOTALL)
        
        if general_match:
            return general_match.group(1).strip()
            
        # If still no match, look for known command keywords
        for prefix in self.valid_actions:
            keyword_pattern = rf"{prefix}\[[^\]]*\]"
            keyword_match = re.search(keyword_pattern, text, re.DOTALL)
            if keyword_match:
                return keyword_match.group(0).strip()
                
        # No valid action found
        return None
    
    def extract_thought(self, text, step_number):
        """
        Extract the thought from the LLM response text.
        
        Parameters:
        -----------
        text : str
            The LLM response text
        step_number : int
            The current step number
            
        Returns:
        --------
        str: The extracted thought string
        """
        # Clean up the input text
        text = text.strip()
        
        # Try to find thought with the exact step number
        thought_pattern = rf"Thought\s*{step_number}\s*:(.*?)(?:Action|$)"
        thought_match = re.search(thought_pattern, text, re.DOTALL)
        
        if thought_match:
            return thought_match.group(1).strip()
            
        # If no match with step number, take everything before "Action" as the thought
        parts = text.split("Action", 1)
        if len(parts) > 1:
            return parts[0].strip()
            
        # If no "Action" keyword, use the whole text as thought
        return text.strip()
    
    def normalize_action(self, action_text):
        """
        Clean up and normalize action strings from LLM.
        
        This handles various cases where the LLM might generate improperly
        formatted actions.
        
        Parameters:
        -----------
        action_text : str
            The action text extracted from the LLM response
            
        Returns:
        --------
        str: A properly formatted action string
        """
        # Strip any leading/trailing whitespace
        action_text = action_text.strip()
        
        # Handle Finish action without brackets
        if action_text.startswith('Finish') and '[' not in action_text:
            # Extract everything after "Finish"
            content = action_text[len('Finish'):].strip()
            # Format it properly
            return f'Finish["{content}"]'
            
        # Handle other actions without proper bracket format
        for prefix in self.valid_actions:
            if action_text.startswith(prefix) and '[' not in action_text:
                # If there's content after the prefix, put it in brackets
                content = action_text[len(prefix):].strip()
                if content:
                    return f"{prefix}[{content}]"
                else:
                    return f"{prefix}[unknown]"
                    
            # Fix missing closing bracket
            elif action_text.startswith(prefix) and '[' in action_text and ']' not in action_text:
                return f"{action_text}]"
                
        # If it looks like a valid action but doesn't match our prefixes, try to fix it
        action_pattern = r"([A-Za-z0-9]+)(?:\[([^\]]*)\])?"
        match = re.match(action_pattern, action_text)
        
        if match:
            command = match.group(1)
            param = match.group(2) if match.group(2) else ""
            
            # Check if this is a close match to a valid action
            for valid_action in self.valid_actions:
                if self.string_similarity(command, valid_action) > 0.7:  # Threshold for similarity
                    return f"{valid_action}[{param}]"
                    
        # No fixes needed or possible, return as is
        return action_text
    
    def string_similarity(self, s1, s2):
        """
        Calculate a simple similarity score between two strings.
        Used for fuzzy matching command names.
        
        Returns a value between 0 (completely different) and 1 (identical)
        """
        # Convert to lowercase for case-insensitive comparison
        s1, s2 = s1.lower(), s2.lower()
        
        # If one is contained in the other, that's a strong signal
        if s1 in s2 or s2 in s1:
            return 0.8
            
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        
        # Divide by the length of the longer string
        return matches / max(len(s1), len(s2))
    
    def validate_action(self, action):
        """
        Check if an action is valid according to the environment's expected format.
        
        Parameters:
        -----------
        action : str
            The action string to validate
            
        Returns:
        --------
        bool: Whether the action is valid
        """
        if not action:
            return False
            
        # Must end with closing bracket
        if not action.endswith(']'):
            return False
            
        # Must start with a valid prefix
        for prefix in self.valid_actions:
            if action.startswith(prefix + '['):
                # There must be something inside the brackets (can be empty string)
                bracket_content = action[len(prefix) + 1:-1]
                return True
                
        return False
    
    def execute_action(self, action):
        """
        Execute an action in the environment with retry logic.
        
        Parameters:
        -----------
        action : str
            The action to execute
            
        Returns:
        --------
        tuple: (observation, reward, done, info)
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                return self.env.step(action)
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Max retry attempts reached for action: {action}")
            except Exception as e:
                print(f"Error executing action: {e}")
                # Return a formatted error message as the observation
                return f"Error: {str(e)}", 0, False, {}
    
    def diagnose_one(self, device_name, max_steps=8, to_print=True, **env_kwargs):
        """
        Diagnose a network device using the ReAct paradigm.
        
        Parameters:
        -----------
        device_name : str
            The name of the device to diagnose
        max_steps : int
            Maximum number of steps for the ReAct loop
        to_print : bool
            Whether to print diagnostic steps
        env_kwargs : dict
            Additional keyword arguments for environment reset
            
        Returns:
        --------
        dict: Diagnosis information including trajectory and conclusion
        """
        # Get the instruction prompt
        instruction = self._get_instruction()
        
        # Add the device to be diagnosed
        instruction += f"\n\nDevice to be diagnosed: {device_name}\n"
        
        # Reset the environment
        env_kwargs['device_name'] = device_name
        observation = self.reset_env(**env_kwargs)
        
        # Run the ReAct loop
        result = self.react(
            initial_prompt=instruction,
            max_steps=max_steps,
            to_print=to_print
        )
        
        # Extract the diagnosis from result
        diagnosis = self.env._get_info().get("answer", "No diagnosis provided")
        
        return {
            "device_name": device_name,
            "diagnosis": diagnosis,
            "steps": self.env.steps,
            "trajectory": result.get("trajectory", [])
        }
    
    def _get_instruction(self):
        """
        Get the instruction prompt for the agent.
        This should be implemented in a subclass.
        """
        return ""
    
    def react(self, initial_prompt, max_steps=8, to_print=False):
        """
        Execute the ReAct loop with the LLM.
        
        Parameters:
        -----------
        initial_prompt : str
            The system prompt containing instructions
        max_steps : int
            Maximum number of steps to execute
        to_print : bool
            Whether to print the steps for debugging
            
        Returns:
        --------
        dict: Results including trajectory and stats
        """
        # Initialize conversation with system prompt
        messages = [{"role": "system", "content": initial_prompt}]
        
        # Initialize statistics
        stats = {
            "steps": 0,
            "valid_actions": 0,
            "invalid_actions": 0,
            "parse_failures": 0
        }
        
        # Trajectory to return
        trajectory = []
        
        # Flag to track if we're done
        done = False
        
        # Execute steps
        for i in range(1, max_steps + 1):
            # Increment step counter
            stats["steps"] += 1
            
            # Ask for thought
            user_msg = f"Thought {i}:"
            messages.append({"role": "user", "content": user_msg})
            
            # Get LLM response
            llm_response = self._llm(messages, stop=[f"Observation {i}:"])
            response_text = llm_response["choices"][0]["message"]["content"]
            
            # Print raw response for debugging
            if to_print:
                print(f"Raw LLM response: {response_text}")
            
            # Extract thought and action
            thought = self.extract_thought(response_text, i)
            action = self.extract_action(response_text, i)
            
            # Add to messages
            messages.append({"role": "assistant", "content": f"Thought {i}: {thought}"})
            
            # If no action extracted, ask again specifically for the action
            if not action:
                stats["parse_failures"] += 1
                action_prompt = f"Based on your thought, what specific action should be taken? Please respond with 'Action {i}:' followed by one of these commands: {', '.join([f'{a}[...]' for a in self.valid_actions])}."
                messages.append({"role": "user", "content": action_prompt})
                retry_response = self._llm(messages)
                retry_text = retry_response["choices"][0]["message"]["content"]
                action = self.extract_action(retry_text, i)
                
                if not action:
                    # Still no action, provide a default based on the current step
                    if i == 1:
                        default_action = f"GetDeviceInfo[{self.env.current_device}]"
                    else:
                        default_action = f"Finish[Unable to determine root cause. Please investigate manually.]"
                    
                    action = default_action
                    messages.append({"role": "system", "content": f"No valid action found. Using default: {action}"})
            
            # Add action to messages
            messages.append({"role": "assistant", "content": f"Action {i}: {action}"})
            
            # Validate the action
            if self.validate_action(action):
                stats["valid_actions"] += 1
                
                # Execute the action
                observation, reward, done_flag, info = self.execute_action(action)
                
                # Format the observation
                if isinstance(observation, dict) or isinstance(observation, list):
                    observation_text = json.dumps(observation, indent=2)
                else:
                    observation_text = str(observation)
                    
                # Add observation to messages
                observation_msg = f"Observation {i}: {observation_text}"
                messages.append({"role": "system", "content": observation_msg})
                
                # Update trajectory
                trajectory.append({
                    "step": i,
                    "thought": thought,
                    "action": action,
                    "observation": observation_text
                })
                
                # Print for debugging
                if to_print:
                    print(f"Thought {i}: {thought}")
                    print(f"Action {i}: {action}")
                    print(f"Observation {i}: {observation_text}\n")
                
                # Check if we're done
                if done_flag:
                    done = True
                    break
            else:
                # Invalid action
                stats["invalid_actions"] += 1
                
                # Provide feedback on expected format
                example_actions = ", ".join([f"{prefix}[param]" for prefix in self.valid_actions])
                error_msg = f"Observation {i}: Invalid action format: '{action}'. Please use one of: {example_actions}"
                messages.append({"role": "system", "content": error_msg})
                
                if to_print:
                    print(f"Invalid action: {action}")
                    print(f"Error message: {error_msg}\n")
        
        # If we hit max steps without finishing, force a conclusion
        if not done and stats["steps"] >= max_steps:
            force_action = f"Finish[Diagnosis incomplete within {max_steps} steps. Based on available information: issue appears to be related to connectivity or configuration.]"
            observation, reward, done_flag, info = self.execute_action(force_action)
            
            messages.append({"role": "system", "content": f"Max steps reached. Forced conclusion: {force_action}"})
            messages.append({"role": "system", "content": f"Observation Final: {observation}"})
            
            trajectory.append({
                "step": stats["steps"] + 1,
                "thought": "Maximum steps reached without conclusion.",
                "action": force_action,
                "observation": str(observation)
            })
        
        # Return results
        return {
            "trajectory": trajectory,
            "messages": messages,
            "stats": stats
        }


class APAnalystAgent(NetworkAgent):
    """
    Specialized NetworkAgent for analyzing Access Points.
    """
    def __init__(self, env):
        valid_actions = [
            "GetDeviceInfo",
            "GetDeviceConfig",
            "Get1hrEventsForDevice",
            "Get2dayEventsForDevice",
            "Finish"
        ]
        super().__init__(env, valid_actions)
    
    def _get_instruction(self):
        """
        Get the specialized instruction prompt for AP analysis.
        """
        return """
You are an advanced network engineer tasked with diagnosing and analyzing potential issues for Access Points (APs). Your objective is to identify any potential issues and to evaluate the condition/health/status of the Cisco Access Points.

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
- "Thought X": your chain-of-thought reasoning.
- "Action X": one of the five actions above with exact syntax.
- "Observation X": the environment's returned JSON/text.

Key Points:
- If you suspect the AP's controller might be relevant, first call GetDeviceConfig[theAP] to learn controllerName, then call GetDeviceInfo[thatControllerName] if needed.
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

    def diagnose_ap(self, ap_name, dnac_region="europe", max_steps=8, to_print=True):
        """
        Diagnose an Access Point.
        
        Parameters:
        -----------
        ap_name : str
            The name of the access point to diagnose
        dnac_region : str
            The DNA Center region (europe, america, asia)
        max_steps : int
            Maximum number of steps for the ReAct loop
        to_print : bool
            Whether to print diagnostic steps
            
        Returns:
        --------
        dict: Diagnosis information
        """
        return self.diagnose_one(
            device_name=ap_name,
            max_steps=max_steps,
            to_print=to_print,
            dnac_region=dnac_region,
            refresh_login_tokens=True
        )


# Example usage:
if __name__ == "__main__":
    # This is just a dummy example to show how to use the agent
    from your_env_module import APEnv
    
    # Create environment
    env = APEnv()
    
    # Create agent
    agent = APAnalystAgent(env)
    
    # Run diagnosis
    result = agent.diagnose_ap("example-ap-01", dnac_region="europe")
    
    # Print diagnosis
    print(f"Diagnosis: {result['diagnosis']}")


