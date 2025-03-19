import os, json

from typing import Union

import requests

from dotenv import load_dotenv

 

import openai

import gymnasium as gym

import pandas as pd

 

from src.models import gpt_chat, gpt_completion

import src.prompts as prompts

 

load_dotenv()

 

class NetworkAgent():

    def __init__(self, env: Union[gym.Wrapper, gym.Env], valid_prefixes=None):

        self.env = env

        self.valid_prefixes=valid_prefixes

 

    def _llm(self, messages, stop=["\n"], *args, **kwargs):

        response = gpt_chat(messages, max_tokens=4000, stop=stop, *args, **kwargs)

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

   

    def set_valid_prefixes(self, valid_prefixes:list):

        self.valid_prefixes=valid_prefixes

 

    def reset_env(self, valid_prefixes:list=None, *args, **kwargs):

        self.env.reset(*args, **kwargs)

        self.valid_prefixes=valid_prefixes

 

    def _react(self,initial_prompt:str, max_num_steps:int=8,to_print:bool=False):

        """

        Iteratively prompt the LLM in ReAct style with advanced scenario format.

 

        Parameters:

        -----------

        initial_prompt : str

            The combined system/instruction + few-shot examples prompt.

 

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

           

            # We try to parse out "Thought X" and "Action X" from the LLM’s output

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

            if not any(action_str.startswith(pref) and action_str.endswith("]") for pref in self.valid_prefixes):

                # Invalid action format => we skip or record an error

                obs_str = f"Invalid action: '{action_str}'. Please use one of {self.valid_prefixes}."

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

 

class ApAnalystAgent(NetworkAgent):

    def diagnoze_one_AP(self, device_name, dnac_region, instruction=prompts.diagonize_one_AP_instruction_advanced,

                         fsl_examples=prompts.diagonize_one_AP_examples, timestamp=None, to_print:bool=False):

        full_prompt = f"{instruction}\n\nDevice to be diagnosed: {device_name}\n\n{fsl_examples}"

        valid_prefixes = [

            "GetDeviceInfo[",

            "GetDeviceConfig[",

            "Get1hrEventsForDevice[",

            "Get2dayEventsForDevice[",

            "Finish["

        ]

        _ = self.reset_env(device_name=device_name, refresh_login_tokens=True, dnac_region=dnac_region, timestamp=timestamp, valid_prefixes=valid_prefixes)

        result = self._react(full_prompt, to_print=to_print)

        return result

 

    def health_evaluation_whole_system(self):

        pass

 

    def health_evaluation_one_site(self):

        pass

    

class AlertsAggregatorAgent(NetworkAgent):

    pass