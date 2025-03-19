def _react(self, initial_prompt:str, max_num_steps:int=8, to_print:bool=False):
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
    
    # Import regex at the beginning to avoid repeated imports
    import re
   
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
            print(f"DEBUG: Raw LLM response: {assistant_text}")
       
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

                # Clean the action string - remove any prefix and ensure it's just the command
                clean_action_str = action_str
                # Remove any leading "Action X:" if present
                if clean_action_str.startswith(f"Action {i}:"):
                    clean_action_str = clean_action_str[len(f"Action {i}:"):].strip()
                
                # Look for the actual command syntax in the action string
                command_match = re.search(r'(GetDeviceInfo\[.+?\]|GetDeviceConfig\[.+?\]|Get1hrEventsForDevice\[.+?\]|Get2dayEventsForDevice\[.+?\]|Finish\[.+?\])', clean_action_str)
                
                if command_match:
                    # If we found a valid command pattern, use just that
                    clean_action_str = command_match.group(1)
                    if to_print:
                        print(f"DEBUG: Extracted command: {clean_action_str}")
                else:
                    # No valid command found, report error
                    obs_str = f"Invalid action: '{action_str}'. Please use one of {self.valid_prefixes}."
                    messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
                    if to_print:
                        print(f"DEBUG: No valid command found. Observation {i}: {obs_str}")
                    continue

            else:
                raise ValueError("Assistant response not in expected Thought/Action format.")
       
        except Exception as e:
            # If parsing fails, we attempt a fallback or re-ask
            n_badcalls += 1
            if to_print:
                print(f"DEBUG: Exception in parsing: {e}")
                
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
            
            # Try to extract a valid command from the fallback action
            command_match = re.search(r'(GetDeviceInfo\[.+?\]|GetDeviceConfig\[.+?\]|Get1hrEventsForDevice\[.+?\]|Get2dayEventsForDevice\[.+?\]|Finish\[.+?\])', action_str)
            if command_match:
                clean_action_str = command_match.group(1)
                if to_print:
                    print(f"DEBUG: Extracted command from fallback: {clean_action_str}")
            else:
                # Still no valid command, report error and continue
                obs_str = f"Invalid action: '{action_str}'. Please use one of {self.valid_prefixes}."
                messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
                if to_print:
                    print(f"DEBUG: No valid command in fallback. Observation {i}: {obs_str}")
                continue
       
        # Now validate and step with the clean action string
        if not any(clean_action_str.startswith(pref) and clean_action_str.endswith("]") for pref in self.valid_prefixes):
            # Invalid action format => we skip or record an error
            obs_str = f"Invalid action: '{action_str}'. Please use one of {self.valid_prefixes}."
            messages.append({"role": "system", "content": f"Observation {i}: {obs_str}"})
            if to_print:
                print(f"DEBUG: Action validation failed. Observation {i}: {obs_str}")
            # We won't call env.step if invalid
            continue
       
        # Now let's run the environment step with this action
        if to_print:
            print(f"DEBUG: Sending to environment: {clean_action_str}")
            
        obs, r, done_flag, info = self._step(clean_action_str)
        
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
        if to_print:
            print(f"DEBUG: Forcing finish: {force_finish_action}")
            
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
        print(f"DEBUG: Final info: {info}")

    return r, info