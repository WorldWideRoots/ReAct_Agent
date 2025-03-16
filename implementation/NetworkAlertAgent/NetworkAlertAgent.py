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
            self.valid_prefixes = [
                "InitialExploration",
                "TimeBasedClustering",
                "TopologyBasedClustering",
                "Reassess",
                "DirectReorganize",
                "Finish"
            ]
            # Also add versions with brackets for backward compatibility
            self.valid_prefixes_with_brackets = [f"{prefix}[" for prefix in self.valid_prefixes]
        else:
            self.valid_prefixes = valid_prefixes
            self.valid_prefixes_with_brackets = [f"{prefix}[" if not prefix.endswith("[") else prefix 
                                              for prefix in valid_prefixes]
            
        # Conversation history for the ReAct framework
        self.react_messages = []
    
    def _llm(self, messages, stop=None, *args, **kwargs):
        """Call the LLM with the given messages."""
        # This would call your LLM implementation (e.g., gpt_chat)
        # For demonstration purposes, we'll return a mock response
        if stop is None:
            stop = ["\n"]
        
        # Mock LLM response
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
        """Take a step in the environment with the given action."""
        attempts = 0
        while attempts < 10:
            try:
                return self.env.step(action)
            except requests.exceptions.Timeout:
                attempts += 1
                if attempts == 10:
                    raise Exception("Max retry attempts reached for step action.")
    
    def set_valid_prefixes(self, valid_prefixes: list):
        """Set the valid action prefixes for ReAct."""
        self.valid_prefixes = valid_prefixes
        # Also generate the bracketed versions for backward compatibility
        self.valid_prefixes_with_brackets = [f"{prefix}[" if not prefix.endswith("[") else prefix 
                                          for prefix in valid_prefixes]
    
    def reset_env(self, valid_prefixes: list=None, *args, **kwargs):
        """Reset the environment and optionally set new valid prefixes."""
        observation = self.env.reset(*args, **kwargs)
        if valid_prefixes:
            self.valid_prefixes = valid_prefixes
        self.react_messages = []
        return observation
    
    def react(self, initial_prompt: str, max_num_steps: int=8, to_print: bool=False):
        """
        Run the ReAct framework to perform alert aggregation.
        
        The agent leverages the environment's hierarchical history management:
        1. Environment maintains function-specific histories for each clustering type
        2. Environment provides observations that include key insights from previous steps
        3. Agent focuses on high-level reasoning through the ReAct framework
        
        Args:
            initial_prompt: The system prompt that guides the agent
            max_num_steps: Maximum number of ReAct steps to take
            to_print: Whether to print intermediate steps
            
        Returns:
            (reward, info): Final reward and information from the environment
        """
        # Store the conversation in messages
        self.react_messages = [{"role": "system", "content": initial_prompt}]
        
        # Track steps, bad calls, and done status
        n_calls, n_badcalls = 0, 0
        done = False
        
        # Begin the iterative ReAct loop
        for i in range(1, max_num_steps + 1):
            n_calls += 1
            user_msg = f"Thought {i}:"
            self.react_messages.append({"role": "user", "content": user_msg})
            
            # Call the LLM
            thought_action_response = self._llm(self.react_messages, stop=[f"\nObservation {i}:"])
            assistant_text = thought_action_response["choices"][0]["message"]["content"]
            
            if to_print:
                print(assistant_text)
            
            # Parse out Thought and Action from the LLM's output
            thought_str = "No valid thought parsed"  # Default in case parsing fails
            try:
                segments = assistant_text.split(f"\nAction {i}:")
                if len(segments) == 2:
                    thought_str = segments[0].strip()
                    action_str = segments[1].strip()
                    
                    # If the LLM repeated "Thought i:" in the text, remove it
                    if thought_str.startswith(f"Thought {i}:"):
                        thought_str = thought_str[len(f"Thought {i}:"):].strip()
                    
                    # Add them to conversation for record
                    self.react_messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
                    self.react_messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
                else:
                    # Try alternative parsing: just take first line as thought, rest as action
                    lines = assistant_text.split('\n')
                    if len(lines) > 1:
                        thought_str = lines[0].strip()
                        action_str = '\n'.join(lines[1:]).strip()
                        
                        # Add them to conversation
                        self.react_messages.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
                        self.react_messages.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
                    else:
                        raise ValueError("Assistant response not in expected Thought/Action format.")
                
            except Exception as e:
                # If parsing fails, attempt a fallback
                n_badcalls += 1
                splitted = assistant_text.strip().split("\n", 1)
                if splitted:
                    fallback_thought = splitted[0]
                else:
                    fallback_thought = "No valid thought parsed."
                
                # Re-ask specifically for the action
                action_request_msg = f"Thought {i}: {fallback_thought}\nAction {i}:"
                new_resp = self._llm(self.react_messages + [{"role": "user", "content": action_request_msg}])
                action_str = new_resp["choices"][0]["message"]["content"].strip()
            
            # Verify the action format
            valid_format = False
            
            # Check for exact matches with action names (without parameters)
            if action_str in self.valid_prefixes:
                valid_format = True
                # Add empty brackets for consistency in internal processing
                action_str = f"{action_str}[]"
            
            # Check for actions with parameters
            if not valid_format:
                for prefix in self.valid_prefixes_with_brackets:
                    if action_str.startswith(prefix) and action_str.endswith("]"):
                        valid_format = True
                        break
            
            if not valid_format:
                # Invalid action format
                obs_str = f"Invalid action: '{action_str}'. Please use one of these action names: {self.valid_prefixes}. For actions with parameters, use the format 'ActionName[parameters]'."
                self.react_messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
                if to_print:
                    print(f"Observation {i}: {obs_str}")
                continue
            
            # Execute the action in the environment
            obs, r, done_flag, info = self._step(action_str)
            
            # Format the observation
            obs_str = f"Observation {i}: {obs}"
            self.react_messages.append({"role": "system", "content": obs_str})
            
            if to_print:
                # Safely print with fallback for undefined variables
                if 'thought_str' not in locals():
                    thought_str = "No thought captured"
                print(f"Thought {i}: {thought_str}\nAction {i}: {action_str}\nObservation {i}: {obs}\n")
            
            # Check if we're done
            if done_flag:
                done = True
                break
        
        # If we run out of steps without finishing, force a finish
        if not done:
            force_finish_action = f"Finish[No conclusion within {max_num_steps} steps. Suggest manual follow-up.]"
            obs, r, done_flag, info = self._step(force_finish_action)
            self.react_messages.append({"role": "system", "content": f"Observation End: {obs}"})
            done = True
        
        # Log information
        info.update({
            "n_calls": n_calls,
            "n_badcalls": n_badcalls,
            "traj": self.react_messages
        })
        
        if to_print:
            print(info)
        
        return r, info
    
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
        except:
            stats["env_history"] = "Not available or accessible"
        
        return stats