import json
from typing import Union, List, Dict, Any
import gym
import requests

class NetworkAlertAgent:
    """
    Agent that uses ReAct framework to perform network alert aggregation.
    This agent interacts with the NetworkAlertEnvironment to explore and cluster alerts.
    """
    
    def __init__(self, env: Union[gym.Wrapper, gym.Env], valid_prefixes=None):
        """
        Initialize the NetworkAlertAgent.
        
        Args:
            env: The NetworkAlertEnvironment to interact with
            valid_prefixes: List of valid action prefixes for ReAct
        """
        self.env = env
        
        # Define valid prefixes if not provided
        if valid_prefixes is None:
            # Use action names without brackets as the default
            # Note: The order matters - if the environment has specific
            # expected action names, these should match exactly
            self.valid_prefixes = [
                "InitialExploration",
                "TimeBasedClustering",
                "TopologyBasedClustering",
                "Reassess",
                "Reorganize",  # For natural language reorganizations
                "Finish"
            ]
            
            # To support backward compatibility with environment
            if hasattr(env, 'action_to_text'):
                # Extract valid actions from environment's action_to_text mapping
                env_actions = set(env.action_to_text.values())
                # Update valid prefixes to include any missing actions from environment
                for action in env_actions:
                    if action not in self.valid_prefixes:
                        self.valid_prefixes.append(action)
                        print(f"DEBUG: Added '{action}' from environment's action space")
                
            # Also add versions with brackets for backward compatibility
            self.valid_prefixes_with_brackets = [f"{prefix}[" for prefix in self.valid_prefixes]
        else:
            self.valid_prefixes = valid_prefixes
            self.valid_prefixes_with_brackets = [f"{prefix}[" if not prefix.endswith("[") else prefix 
                                              for prefix in valid_prefixes]
            
        # Conversation history for the ReAct framework
        self.react_messages = []
    
    def _llm(self, messages, stop=None, *args, **kwargs):
        """
        Call the LLM with the given messages.
        
        This is a placeholder implementation that should be overridden with your
        actual LLM integration (e.g., OpenAI API, Claude API, etc.)
        """
        # Default stop sequence if none provided
        if stop is None:
            stop = ["\n"]
        
        # Mock LLM response for demonstration
        # In a real implementation, this would call your LLM service
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a mock LLM response for demonstration purposes."
                    }
                }
            ]
        }
    
    def _step(self, action):
        """
        Take a step in the environment with the given action.
        
        Simplified implementation that just ensures valid action format
        and handles retry logic for timeouts.
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
                return self.env.step(action)
            except Exception as e:
                attempts += 1
                print(f"DEBUG: Error on attempt {attempts}: {str(e)}")
                if attempts == max_attempts:
                    raise Exception(f"Max retry attempts ({max_attempts}) reached: {str(e)}")
    
    def _execute_step(self, action):
        """Execute the action in the environment with retry logic."""
        attempts = 0
        max_attempts = 10
        while attempts < max_attempts:
            try:
                return self.env.step(action)
            except requests.exceptions.Timeout:
                attempts += 1
                if attempts == max_attempts:
                    raise Exception(f"Max retry attempts ({max_attempts}) reached for step action.")
                print(f"DEBUG: Timeout on attempt {attempts}, retrying...")
    
    def set_valid_prefixes(self, valid_prefixes: list):
        """Set the valid action prefixes for ReAct."""
        self.valid_prefixes = valid_prefixes
        # Also generate the bracketed versions for backward compatibility
        self.valid_prefixes_with_brackets = [f"{prefix}[" if not prefix.endswith("[") else prefix 
                                          for prefix in valid_prefixes]
    
    def reset_env(self, alerts=None, topology_info=None, valid_prefixes=None):
        """Reset the environment and optionally set new valid prefixes."""
        observation = self.env.reset(alerts=alerts, topology_info=topology_info)
        if valid_prefixes:
            self.valid_prefixes = valid_prefixes
        self.react_messages = []
        return observation
        
    def react(self, initial_prompt: str, max_num_steps: int=8, to_print: bool=False):
        """
        Run the ReAct framework to perform alert aggregation.
        
        Simplified implementation that focuses on robustness and simplicity.
        
        Args:
            initial_prompt: The system prompt that guides the agent
            max_num_steps: Maximum number of ReAct steps to take
            to_print: Whether to print intermediate steps
            
        Returns:
            (reward, info): Final reward and information from the environment
        """
        # Store the conversation in messages
        self.react_messages = [{"role": "system", "content": initial_prompt}]
        
        # Initialize tracking variables
        n_calls = 0
        done = False
        
        # Begin the iterative ReAct loop
        for i in range(1, max_num_steps + 1):
            n_calls += 1
            
            # Prompt the LLM for next thought and action
            user_msg = f"Thought {i}:"
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
                # Fallback: just take the first line as thought, the rest as action
                lines = assistant_text.split('\n')
                thought_str = lines[0].strip()
                action_str = ' '.join(lines[1:]).strip()
            
            # Clean up the extracted action
            action_str = action_str.strip()
            if action_str.startswith('"') and action_str.endswith('"'):
                action_str = action_str[1:-1].strip()
            elif action_str.startswith("'") and action_str.endswith("'"):
                action_str = action_str[1:-1].strip()
            
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
                continue
            
            # Execute the action
            try:
                obs, r, done_flag, info = self._step(action_str)
                
                # Record the observation
                obs_str = f"Observation {i}: {obs}"
                self.react_messages.append({"role": "system", "content": obs_str})
                
                if to_print:
                    print(f"Thought {i}: {thought_str}")
                    print(f"Action {i}: {action_str}")
                    print(f"Observation {i}: {obs}\n")
                
                # Check if we're done
                if done_flag:
                    done = True
                    break
                    
            except Exception as e:
                # Handle any errors during execution
                error_msg = f"Error executing action: {str(e)}"
                self.react_messages.append({"role": "system", "content": f"Observation {i}: {error_msg}"})
                if to_print:
                    print(f"Observation {i}: {error_msg}")
        
        # If we run out of steps without finishing, force a finish
        if not done:
            try:
                obs, r, done_flag, info = self._step("Finish[]")
                self.react_messages.append({"role": "system", "content": f"Observation Final: {obs}"})
                done = True
            except Exception as e:
                # Handle errors during forced finish
                error_msg = f"Error during forced finish: {str(e)}"
                self.react_messages.append({"role": "system", "content": f"Observation Final: {error_msg}"})
        
        # Prepare return information
        info = {
            "n_calls": n_calls,
            "traj": self.react_messages,
            "clusters": self.env.current_clusters if hasattr(self.env, 'current_clusters') else None
        }
        
        return 0, info  # Return 0 reward for simplicity
    
    def get_history_stats(self):
        """
        Get statistics about the agent's history and the environment's history management.
        This is helpful for debugging and understanding the state of the agent.
        
        Returns:
            dict: Statistics about the history
        """
        stats = {
            "agent_react_messages": len(self.react_messages)
        }
        
        # Try to get environment history statistics if available
        try:
            # Check if environment has the expected attributes
            if hasattr(self.env, 'react_history') and hasattr(self.env, 'function_histories'):
                env_stats = {
                    "env_react_history": len(self.env.react_history),
                    "env_function_histories": {
                        key: len(value) for key, value in self.env.function_histories.items()
                    }
                }
                stats.update(env_stats)
                
                # Add information about recent reasoning if available
                if hasattr(self.env, 'recent_reasoning'):
                    stats["env_recent_reasoning"] = {
                        key: len(value) > 0 for key, value in self.env.recent_reasoning.items()
                    }
        except Exception as e:
            stats["env_history"] = f"Not available or accessible: {str(e)}"
        
        return stats