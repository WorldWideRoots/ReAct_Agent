import time
import json
import requests
import pandas as pd
from typing import Union, List, Dict, Any, Optional
import re
import gym

class NetworkAgent:
    """
    Improved NetworkAgent that implements the ReAct paradigm
    for interacting with network environments using LLMs.
    """
    
    def __init__(self, env: Union[gym.Wrapper, gym.Env], valid_prefixes=None):
        """
        Initialize the NetworkAgent.
        
        Parameters:
        -----------
        env : gym.Env
            The environment to interact with
        valid_prefixes : list
            List of valid action prefixes (e.g., 'GetDeviceInfo', 'Finish', etc.)
        """
        self.env = env
        self.valid_prefixes = valid_prefixes or []
        
    def set_valid_prefixes(self, valid_prefixes: list):
        """Set the list of valid action prefixes."""
        self.valid_prefixes = valid_prefixes
        
    def reset_env(self, valid_prefixes: list = None, *args, **kwargs):
        """Reset the environment with specified arguments."""
        self.env.reset(*args, **kwargs)
        if valid_prefixes is not None:
            self.valid_prefixes = valid_prefixes
    
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
    
    def _step(self, action):
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
        for prefix in self.valid_prefixes:
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
        for prefix in self.valid_prefixes:
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
            
            # Check if this is a close match to a valid prefix
            for valid_prefix in self.valid_prefixes:
                if self.string_similarity(command, valid_prefix) > 0.7:  # Threshold for similarity
                    return f"{valid_prefix}[{param}]"
                    
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
        for prefix in self.valid_prefixes:
            if action.startswith(prefix + '['):
                # There must be something inside the brackets (can be empty string)
                bracket_content = action[len(prefix) + 1:-1]
                return True
                
        return False
    
    def _react(self, initial_prompt, max_num_steps=8, to_print=False):
        """
        Improved _react method with better action parsing and error handling.
        
        Parameters:
        -----------
        initial_prompt : str
            The system prompt containing instructions
        max_num_steps : int
            Maximum number of steps to execute
        to_print : bool
            Whether to print the steps for debugging
            
        Returns:
        --------
        tuple: (reward, info) where info contains trajectory and stats
        """
        # Initialize conversation with system prompt
        messages = [{"role": "system", "content": initial_prompt}]
        
        # Initialize statistics
        n_calls = 0
        n_badcalls = 0
        done = False
        
        # Execute steps
        for i in range(1, max_num_steps + 1):
            # Increment call counter
            n_calls += 1
            
            # Ask for thought
            user_msg = f"Thought {i}:"
            messages.append({"role": "user", "content": user_msg})
            
            # Get LLM response
            try:
                llm_response = self._llm(messages, stop=[f"Observation {i}:"])
                response_text = llm_response["choices"][0]["message"]["content"]
                
                # Print raw response for debugging
                if to_print:
                    print(f"Raw LLM response: {response_text}")
                
                # Extract thought and action
                thought_str = self.extract_thought(response_text, i)
                action_str = self.extract_action(response_text, i)
                
                # Add thought to messages
                messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
                
                # If no action extracted, try to get it explicitly
                if not action_str:
                    n_badcalls += 1
                    action_request_msg = f"Based on your thought, what specific action do you want to take? Please respond with 'Action {i}:' followed by one of: {', '.join([f'{a}[...]' for a in self.valid_prefixes])}"
                    messages.append({"role": "user", "content": action_request_msg})
                    retry_response = self._llm(messages)
                    retry_text = retry_response["choices"][0]["message"]["content"]
                    action_str = self.extract_action(retry_text, i)
                    
                    if not action_str:
                        # Still no action, use a default based on the environment
                        if i == 1:
                            action_str = f"GetDeviceInfo[{self.env.current_device or 'unknown'}]"
                        else:
                            action_str = "Finish[Unable to determine the issue with the available information. Please check manually.]"
                        
                # Add action to messages
                messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
                
                # Validate the action
                if self.validate_action(action_str):
                    # Execute the action
                    try:
                        obs, r, done_flag, info = self._step(action_str)
                        
                        # Format the observation
                        if isinstance(obs, (dict, list)):
                            obs_str = f"Observation {i}: {json.dumps(obs, indent=2)}"
                        else:
                            obs_str = f"Observation {i}: {obs}"
                            
                        # Print for debugging
                        if to_print:
                            print(f"Thought {i}: {thought_str}")
                            print(f"Action {i}: {action_str}")
                            print(f"{obs_str}\n")
                            
                    except Exception as e:
                        # Handle execution errors
                        obs_str = f"Observation {i}: Error executing action: {str(e)}"
                        done_flag = False
                        r = 0
                        info = {}
                        
                        if to_print:
                            print(f"Action execution error: {e}")
                else:
                    # Invalid action
                    example_actions = [f"{prefix}[example_param]" for prefix in self.valid_prefixes]
                    obs_str = f"Observation {i}: Invalid action format: '{action_str}'. Please use one of the following formats: {example_actions}"
                    done_flag = False
                    r = 0
                    info = {}
                    
                    if to_print:
                        print(f"{obs_str}")
                
                # Add observation to conversation
                messages.append({"role": "system", "content": obs_str})
                
                # Check if we're done
                if done_flag:
                    done = True
                    break
                    
            except Exception as e:
                # Handle any unexpected errors in the LLM or processing
                n_badcalls += 1
                print(f"Error in step {i}: {e}")
                messages.append({"role": "system", "content": f"Error: {str(e)}"})
        
        # If we hit max steps without finishing, force a conclusion
        if not done:
            force_finish_action = f"Finish[No conclusion within {max_num_steps} steps. Suggest manual follow-up.]"
            try:
                obs, r, done_flag, info = self._step(force_finish_action)
                messages.append({"role": "system", "content": f"Observation End: {obs}"})
            except Exception as e:
                messages.append({"role": "system", "content": f"Observation End: Error in final step: {str(e)}"})
                info = {}
                r = 0
        
        # Add trajectory and statistics to info
        info = info if 'info' in locals() and info else {}
        info.update({
            "n_calls": n_calls,
            "n_badcalls": n_badcalls,
            "traj": messages
        })
        
        if to_print:
            print(info)
        
        return r if 'r' in locals() else 0, info


