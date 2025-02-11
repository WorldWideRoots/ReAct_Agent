import requests
from typing import Union
import gymnasium as gym
import pandas as pd

class APAnalystAgent():
    def __init__(self, env: Union[gym.Env, gym.Wrapper]):
        self.env = env
        
    def _llm(self, messages, stop=["\n"], *args, **kwargs):
        response = gpt_chat(messages,max_tokens=100,stop=stop,*args,**kwargs)
        return response
    
    def _step(self, action):
        attempts = 0
        while attempts < 10:
            try:
                return self.env.step(action)
            except Exception as e:
                attempts += 1
                if attempts == 10:
                    raise e
    
    def reset_env(self, *args, **kwargs):
        return self.env.reset(*args, **kwargs)
    
    def _react(self, initial_prompt, device_name, max_num_steps=8, to_print=False):
        messages = [{'role': 'system', 'content': initial_prompt}]
        n_calls, n_badcalls = 0, 0
        done = False

        valid_action_prefixes = [
            'GetWiFiDeviceInfo[', 'GetWiFiDeviceConfig[', 'Get1hrEventsForDevice[', 'Get2dayEventsForDevice[', 'Finish['
        ]

        for i in range(1, max_num_steps+1):
            n_calls += 1
            prompt_thought = f"Thought {i}:"
            messages.append({'role': 'user', 'content': prompt_thought})
            thought_action_response = self._llm(messages, stop=[f"\nObservation {i}:"])
            assistant_response = thought_action_response.choices[0]['message']['content'].replace('\n\n', '\n')
            if to_print:
                print(assistant_response)
            try:
                thought_action_split = assistant_response.split(f'\nAction {i}:')
                if len(thought_action_split) == 2:
                    thought, action = thought_action_split
                    thought = thought.strip()
                    action = action.strip()
                    if action.startwith(f'Action {i}:'):
                        action = action[len(f'Action {i}:'):]
                    messages.append({'role': 'assistant', 'content': f"Thought {i}: {thought}"})
                    messages.append({'role': 'assistant', 'content': f"Action {i}: {action}"})
                else:
                    raise Exception("Assistant response not in expected format")
            except Exception as e:
                n_badcalls += 1
                n_calls += 1
                last_thought = assistant_response.strip().split('\n')[0]
                action_response = self._llm(messages + [{'role': 'user', 'content': f"Thought {i}: {last_thought}\nAction {i}"}])
                action = action_response.choices[0]['message']['content'].strip()

            if action.lower().startswith("action"):
                action = action.split(": ", 1)[1]

            if any(action.startswith(prefix) and action.endswith("]") for prefix in valid_action_prefixes):
                if device_name not in action:
                    action_prefix = action.split("[")[0]
                    action = f"{action_prefix}[{device_name}]"
            else: 
                self.obs = f"Invalid action {action}\n"
                messages.append({'role': 'system', 'content': f"Observation {i}: {self.obs}"})
                if to_print:
                    print(f"Observation {i}: {self.obs}")             
                continue

            obs, r, done, info = self._step(action)
            observation_content = f"Observation {i}: {obs}"
            messages.append({'role': 'system', 'content': observation_content})

            step_str = f"Thought {i}: {thought}\nAction {i}: {action}\nObservation {i}: {obs}"
            if to_print:
                print(step_str)

            if done:
                break
        
        if not done:
            obs, r, done, info = self._step("Finish[Summary of diagonostics for device {device_name}]")

        if to_print:
            print(info, "\n")
        
        info.update({"n_calls": n_calls, "n_badcalls": n_badcalls, "traj": messages})

        return r, info
    
    def diagnoze_one_AP(self, device_name, timestamp, instruction, few_shot_learning_examples, to_print=False):
        initial_prompt = f"{instruction}\n\nDevice to be diagnosed: {device_name}\n\n{few_shot_learning_examples}"
        _ = self.reset_env(timestamp=timestamp, device_name=device_name)
        return self._react(initial_prompt, device_name, to_print=to_print)
    



    import gymnasium as gym
from typing import Union, Dict, Any
import time

# Pseudocode for an LLM call, adjust as needed
def gpt_chat(messages, max_tokens=100, stop=None, *args, **kwargs):
    """
    A mock function representing a GPT chat completion call.
    Replace with your actual call to openai.ChatCompletion.create(...) or similar.
    """
    # For demonstration, we just echo the last user message
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Thought 1: Example reasoning\nAction 1: Finish[No real content]"
                }
            }
        ]
    }

class APAnalystAgent():
    def __init__(self, env: Union[gym.Env, gym.Wrapper]):
        self.env = env

    def _llm(self, messages, stop=["\n"], *args, **kwargs):
        # Here you'd integrate your actual LLM call
        response = gpt_chat(messages, max_tokens=100, stop=stop, *args, **kwargs)
        return response

    def _step(self, action: str):
        attempts = 0
        while attempts < 10:
            try:
                return self.env.step(action)
            except Exception as e:
                attempts += 1
                if attempts == 10:
                    raise e

    def reset_env(self, *args, **kwargs):
        return self.env.reset(*args, **kwargs)

    def _react(self, initial_prompt: str, device_name: str, max_num_steps: int = 8, to_print: bool = False):
        messages = [{'role': 'system', 'content': initial_prompt}]
        n_calls, n_badcalls = 0, 0
        done = False

        valid_prefixes = [
            'GetDeviceDetail[',
            'GetDeviceConfig[',
            'GetAssuranceDeviceEvents[',
            'GetWirelessDeviceConfig[',
            'Finish['
        ]

        for i in range(1, max_num_steps + 1):
            n_calls += 1
            prompt_thought = f"Thought {i}:"
            messages.append({'role': 'user', 'content': prompt_thought})
            thought_action_response = self._llm(messages, stop=[f"\nObservation {i}:"])
            assistant_content = thought_action_response["choices"][0]["message"]["content"]

            if to_print:
                print(assistant_content)

            # Try parsing "Thought X:\nAction X:"
            try:
                segments = assistant_content.split(f"\nAction {i}:")
                if len(segments) == 2:
                    thought = segments[0].strip()
                    action = segments[1].strip()
                    # If the LLM repeated "Thought {i}:" remove that
                    if thought.startswith(f"Thought {i}:"):
                        thought = thought[len(f"Thought {i}:"):].strip()

                    messages.append({'role': 'assistant', 'content': f"Thought {i}: {thought}"})
                    messages.append({'role': 'assistant', 'content': f"Action {i}: {action}"})
                else:
                    raise ValueError("Assistant response not in expected 'Thought/Action' format.")

            except Exception as e:
                # Attempt fallback / re-ask for action
                n_badcalls += 1
                last_thought = assistant_content.strip().split('\n')[0]
                action_prompt = f"Thought {i}: {last_thought}\nAction {i}:"
                new_resp = self._llm(messages + [{'role': 'user', 'content': action_prompt}])
                action = new_resp["choices"][0]["message"]["content"].strip()

            # Validate prefix
            # E.g. "GetDeviceDetail[AP-11-3A-45]"
            if not any(action.startswith(pref) and action.endswith("]") for pref in valid_prefixes):
                obs = f"Invalid action prefix or format: {action}"
                messages.append({'role': 'system', 'content': f"Observation {i}: {obs}"})
                if to_print:
                    print(f"Observation {i}: {obs}")
                continue  # Move on, though you could do more robust error handling

            # Make sure the device_name is included if needed (like your old code). Optional.
            # For now, assume the LLM passes correct device IDs.

            obs, r, done, info = self._step(action)
            obs_str = f"Observation {i}: {obs}"
            messages.append({'role': 'system', 'content': obs_str})

            if to_print:
                print(f"Thought {i}: {thought}\nAction {i}: {action}\nObservation {i}: {obs}")

            if done:
                break

        if not done:
            # Force finish
            action = f"Finish[Diagnostic session ended for {device_name}]"
            obs, r, done, info = self._step(action)
            messages.append({'role': 'system', 'content': f"Observation End: {obs}"})

        if to_print:
            print(info, "\n")

        info.update({"n_calls": n_calls, "n_badcalls": n_badcalls, "traj": messages})
        return r, info

    def diagnose_one_AP(
        self,
        device_name: str,
        timestamp: int,
        instruction: str,
        few_shot_learning_examples: str,
        to_print: bool = False
    ):
        initial_prompt = f"{instruction}\n\nDevice: {device_name}\n\n{few_shot_learning_examples}"
        _ = self.reset_env(device_name=device_name, timestamp=timestamp)
        return self._react(initial_prompt, device_name, to_print=to_print)





def _react(
    self,
    initial_prompt: str,
    device_name: str,
    max_num_steps: int = 8,
    to_print: bool = False
):
    """
    Iteratively prompt the LLM in ReAct style with advanced scenario format.

    Parameters:
    -----------
    initial_prompt : str
        The combined system/instruction + few-shot examples prompt.

    device_name : str
        The AP device name or ID we are investigating.

    max_num_steps : int
        Maximum ReAct steps (Thought/Action pairs).

    to_print : bool
        Whether to print the steps/observations for debugging.

    Returns:
    --------
    (reward, info): 
        reward is the final reward from the environment (often 0).
        info is a dict containing logs like "traj" (the conversation messages).
    """
    
    # We store the conversation in 'messages'. 
    # initial_prompt should include the instructions + few-shot examples.
    messages = [{"role": "system", "content": initial_prompt}]
    
    # We'll track the steps, bad calls, done, etc.
    n_calls, n_badcalls = 0, 0
    done = False
    
    # The environment is reset with the device name (and possibly other info)
    # This is optional if your environment needs a reset.
    # e.g.:
    _ = self.reset_env(device_name=device_name)
    
    # Valid action prefixes in your environment
    valid_prefixes = [
        "GetDeviceInfo[",
        "GetDeviceConfig[",
        "Get1hrEventsForDevice[",
        "Get2dayEventsForDevice[",
        "Finish["
    ]
    
    # We begin the iterative ReAct loop
    for i in range(1, max_num_steps + 1):
        n_calls += 1
        
        # We prompt the LLM to produce "Thought i:" plus an action
        # The user message is just "Thought i:" so LLM responds in the ReAct style
        user_msg = f"Thought {i}:"
        messages.append({"role": "user", "content": user_msg})
        
        # Call the LLM
        thought_action_response = self._llm(messages, stop=[f"\nObservation {i}:"])
        assistant_text = thought_action_response["choices"][0]["message"]["content"]
        
        if to_print:
            print(assistant_text)
        
        # We try to parse out "Thought X" and "Action X" from the LLM’s output
        try:
            # The LLM ideally returns:
            #   "Thought i: ...\nAction i: <action>"
            # We'll split on f"\nAction {i}:"
            segments = assistant_text.split(f"\nAction {i}:")
            if len(segments) == 2:
                # e.g. segments[0] => "Thought i: ..."
                # segments[1] => "GetDeviceInfo[AP-XYZ]"
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
            # If parsing fails, we attempt a fallback or re-ask
            n_badcalls += 1
            # e.g. take the first line as thought, re-ask for action
            splitted = assistant_text.strip().split("\n", 1)
            if splitted:
                fallback_thought = splitted[0]
            else:
                fallback_thought = "No valid thought parsed."

            # We re-ask specifically for the action
            action_request_msg = f"Thought {i}: {fallback_thought}\nAction {i}:"
            new_resp = self._llm(messages + [{"role": "user", "content": action_request_msg}])
            action_str = new_resp["choices"][0]["message"]["content"].strip()
        
        # We have an action_str, let's verify it
        if not any(action_str.startswith(pref) and action_str.endswith("]") for pref in valid_prefixes):
            # Invalid action format => we skip or record an error
            obs_str = f"Invalid action: '{action_str}'. Please use one of {valid_prefixes}."
            messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
            if to_print:
                print(f"Observation {i}: {obs_str}")
            # We won't call env.step if invalid
            continue
        
        # Now let's run the environment step with this action
        obs, r, done_flag, info = self._step(action_str)
        # Format the observation as well
        obs_str = f"Observation {i}: {obs}"
        messages.append({"role": "system", "content": obs_str})
        
        if to_print:
            print(f"Thought {i}: {thought_str}\nAction {i}: {action_str}\nObservation {i}: {obs}\n")
        
        # If done_flag is True, the environment indicates we're finished
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
