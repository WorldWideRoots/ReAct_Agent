import gymnasium as gym
from gymnasium.spaces import Space
from typing import Dict, Any, List, Optional

class TextSpace(Space):
    """
    A simple text space for demonstration.
    """
    def __init__(self):
        super().__init__(shape=None, dtype=None)

    def contains(self, x) -> bool:
        return isinstance(x, str)


class AlertsEnv(gym.Env):
    """
    An environment that manages alert clustering.
    """

    def __init__(self):
        super().__init__()
        # The environment state could include:
        # - current_clusters: The current (in-progress) clusters
        # - unassigned_alerts: Alerts that are not yet placed in a cluster
        # - past_clusters: Clusters from previous windows (optional)
        # - done: Whether the environment is finished

        self.current_clusters: Dict[str, Any] = {
            "clusters": [],
            "unassigned_alerts": []
        }
        self.past_clusters: Dict[str, Any] = {
            "clusters": [],
            "unassigned_alerts": []
        }
        self.done = False
        self.observation = ""
        self.steps = 0

        # For Gym compliance:
        self.action_space = self.observation_space = TextSpace()

    def _get_obs(self) -> str:
        """
        Return the current "observation" as text,
        which might just be a summary of the cluster state.
        """
        return self.observation

    def _get_info(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "done": self.done,
            # Return the cluster state, partial or full:
            "current_clusters": self.current_clusters,
            "past_clusters": self.past_clusters
        }

    def reset(
        self,
        new_alerts: Optional[List[Dict[str, Any]]] = None,
        past_clusters: Optional[Dict[str, Any]] = None,
        return_info: bool = True
    ):
        """
        Initialize environment state for a new "run" (e.g., a 30-min aggregator batch).
        new_alerts are the incoming alerts you want to cluster.
        past_clusters are any older clusters to consider merging with.
        """
        self.steps = 0
        self.done = False

        # Build fresh environment state
        if new_alerts is not None:
            self.current_clusters = {
                "clusters": [],
                "unassigned_alerts": new_alerts  # all new alerts start unassigned
            }
        if past_clusters is not None:
            self.past_clusters = past_clusters
        else:
            self.past_clusters = {"clusters": [], "unassigned_alerts": []}

        self.observation = "Environment reset. Ready for clustering actions."
        if return_info:
            return self._get_obs(), self._get_info()
        else:
            return self._get_obs()

    def step(self, action: str):
        """
        Interprets the LLM-proposed action (time-based, topology-based, reassess, finish),
        applies it, and returns (obs, reward, done, info).
        """
        self.steps += 1
        reward = 0
        done = False
        action = action.strip()

        # Simple parser to see which of the 4 major actions we have:
        if action.startswith("TimeBasedClustering"):
            self._apply_time_based()
            self.observation = "Applied time-based clustering."
        elif action.startswith("TopologyDependencyClustering"):
            self._apply_topology_dependency()
            self.observation = "Applied topology-dependency clustering."
        elif action.startswith("ReassessClustering"):
            self._apply_reassess_check()
            self.observation = "Reassessed clusters. Possibly revised them."
        elif action.startswith("Finish"):
            # Mark done
            done = True
            self.observation = "Finished clustering."
        else:
            # Unrecognized action
            self.observation = f"Unrecognized action: {action}"
        
        # If done, set self.done
        if done:
            self.done = True

        return self._get_obs(), reward, done, self._get_info()

    # -------------------------------
    # Below are placeholders for real logic
    # -------------------------------

    def _apply_time_based(self):
        """
        Placeholder for the real time-based clustering logic.
        Usually, you'd:
          - look at current_clusters["unassigned_alerts"]
          - check if they fit in existing clusters by time window
          - or create new clusters
          - minimal changes to existing clusters unless there's a time conflict
          - possibly merge with past_clusters if needed
        """
        # Example: Move all unassigned to a single cluster for demonstration
        if self.current_clusters["unassigned_alerts"]:
            new_cluster = {
                "cluster_id": f"time-{self.steps}",
                "alerts": self.current_clusters["unassigned_alerts"]
            }
            self.current_clusters["clusters"].append(new_cluster)
            self.current_clusters["unassigned_alerts"] = []

    def _apply_topology_dependency(self):
        """
        Placeholder for the real topology/dependency-based logic.
        - Possibly look at device/service relationships to unify or refine clusters.
        - Could also handle leftover unassigned alerts.
        """
        # Example: Just do a no-op or "pretend" to merge something
        pass

    def _apply_reassess_check(self):
        """
        Placeholder for a "reassess" step or a 'checking' step,
        seeing if there's leftover alerts or contradictory merges.
        Potentially triggers minimal changes or sets a status for the next step.
        """
        # Example: If there's leftover alerts, we might just reduce them or unify them
        # Here we do a simple no-op for demonstration
        pass


class AlertsAggregatorAgent:
    def __init__(self, env: AlertsEnv, llm_callable):
        """
        env: An instance of AlertsEnv
        llm_callable: A function or method to call your LLM, e.g. openai.ChatCompletion.create(...)
        """
        self.env = env
        self.llm_callable = llm_callable
        self.conversation = []  # store the step-by-step messages

    def reset_env(
        self,
        new_alerts=None,
        past_clusters=None
    ):
        obs, info = self.env.reset(new_alerts=new_alerts, past_clusters=past_clusters)
        self.conversation = []
        self.conversation.append({"role": "system", "content": f"Environment reset: {obs}"})
        return obs, info

    def step_react(self, max_steps=10, verbose=True):
        """
        A minimal ReAct loop. For each iteration:
         - We ask the LLM: "Thought i?" 
         - LLM responds with "Thought i: ...\nAction i: <some action>"
         - We parse the action, call env.step(action), and gather observation.
         - If done => break
        """

        done = False
        for i in range(1, max_steps+1):
            # 1. Prompt LLM for next action
            user_prompt = f"Thought {i}:\n"  # we expect the LLM to respond with Thought + Action
            self.conversation.append({"role": "user", "content": user_prompt})

            # Call your LLM
            llm_response = self.llm_callable(self.conversation)
            llm_text = llm_response["content"]  # assume your LLM returns {"content": "..."} in some format

            if verbose:
                print(f"LLM response:\n{llm_text}\n")

            # 2. Parse out the Action
            # We might expect something like:
            # "Thought 1: We should do time-based first.\nAction 1: TimeBasedClustering[]"
            # Let's do a naive parse by splitting on f"\nAction {i}:"
            segments = llm_text.split(f"\nAction {i}:")
            if len(segments) != 2:
                # Fallback or error
                observation = "Invalid LLM format, can't parse action"
                done = True
                self.conversation.append({"role": "system", "content": observation})
                break

            thought_str = segments[0].strip()
            action_str = segments[1].strip()

            # 3. Execute in environment
            obs, reward, done_flag, info = self.env.step(action_str)
            done = done_flag

            # Log the step
            self.conversation.append({"role": "assistant", "content": f"Thought {i}: {thought_str}"})
            self.conversation.append({"role": "assistant", "content": f"Action {i}: {action_str}"})
            self.conversation.append({"role": "system", "content": f"Observation {i}: {obs}"})

            if verbose:
                print(f"Action {i}: {action_str}")
                print(f"Observation {i}: {obs}\n")
            
            if done:
                break

        if not done:
            # Force a finish if we haven't done so
            obs, reward, done_flag, info = self.env.step("Finish[]")
            self.conversation.append({"role": "assistant", "content": f"Action: Finish[]"})
            self.conversation.append({"role": "system", "content": f"Observation: {obs}"})
            done = True

        return self.conversation, info




import json
from typing import Dict, Any

def time_based_clustering_llm(
    llm_callable,
    current_clusters: Dict[str, Any],
    time_threshold_minutes: int = 10
) -> Dict[str, Any]:
    """
    Calls the LLM to perform a time-based clustering pass.

    Parameters:
    -----------
    llm_callable : function
        A callable that accepts a list of Chat-like messages and returns a dict 
        with a "content" key containing the LLM's response (raw string).

    current_clusters : dict
        A dictionary of the form:
        {
          "clusters": [
            {
              "cluster_id": str,
              "alerts": [
                {
                  "alert_id": str,
                  "source_id": str,
                  "type": str,
                  "class": str,
                  "obj_class": str,
                  "severity": str,
                  "description": str,
                  "first_event_time": int,
                  "last_event_time": int,
                  "last_state_change": int
                  // ... other fields as needed
                }
              ],
              "confidence": float
            }
          ],
          "unassigned_alerts": [
            { ... } // same structure as above
          ]
        }

    time_threshold_minutes : int
        The window (in minutes) for deciding if an unassigned alert belongs with 
        a given cluster's time range.

    Returns:
    --------
    updated_clusters : dict
        The updated structure in the same format, including confidence scores 
        for each cluster. Minimally changed unless necessary.
    """

    # 1) Build the system instructions for the LLM
    system_instructions = f"""
    You are the 'time-based clustering' function in an alert aggregation system.
    Your job:
    1) Look at current clusters and unassigned alerts.
    2) Decide if an unassigned alert belongs in an existing cluster, based on whether
       its [first_event_time, last_event_time] interval overlaps significantly with 
       the cluster's bounding interval (within ~{time_threshold_minutes} minutes).
    3) If it doesn't fit, create a new cluster for it.
    4) Only break or reorganize existing clusters if there's a strong time conflict
       or if you find they truly don't belong together.
    5) For each cluster, maintain or update a 'confidence' (0.0 to 1.0) 
       indicating how certain you are that these alerts belong together.
       - If an unassigned alert's time range strongly overlaps with the cluster 
         and the 'description' is semantically similar, you could raise or keep
         a high confidence.
       - If it's a borderline match, reduce confidence somewhat, or keep it moderate.
    6) Use 'description' text if times are borderline. 
       If the 'description' strongly hints they are related, you can unify them 
       and keep or slightly raise the confidence. 
       If 'description' is different, you might not merge or might lower confidence.
    7) Minimal disruption: Do NOT destroy or drastically alter existing clusters 
       unless there's a clear reason (conflicting time intervals or a mismatch in data).
    8) Return the final structure in strict JSON of this form:
       {{
         "clusters": [
           {{
             "cluster_id": "...",
             "alerts": [...],
             "confidence": <some float>
           }},
           ...
         ],
         "unassigned_alerts": [...]
       }}
    9) Each alert object has these fields:
       - alert_id, source_id, type, class, obj_class, severity, description,
         first_event_time, last_event_time, last_state_change
       Some fields (type, class, obj_class) might be empty or missing. That's okay.
    10) If you do unify or merge clusters, adjust the 'confidence' accordingly.
    """

    # 2) Prepare the user/context message
    # We'll present the current cluster data in JSON form
    user_message_text = (
        "Below is the current cluster state in JSON. Please apply time-based logic "
        f"with a ~{time_threshold_minutes} minute threshold:\n\n"
        + json.dumps(current_clusters, indent=2)
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_message_text}
    ]

    # 3) Call the LLM
    llm_response = llm_callable(messages)
    raw_text = llm_response.get("content", "")

    # 4) Parse the LLM's output as JSON
    # The LLM should return JSON, but it might include extra commentary. 
    # We'll do a naive parse, with a fallback if we fail.
    # (Production code might attempt more robust extraction or ask LLM to reformat.)
    try:
        updated_clusters = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: if there's a decode error, keep the current clusters as-is
        updated_clusters = current_clusters

    # 5) Return the result
    return updated_clusters




time_based_new_prompt1 = """
You are the "time-based clustering" function in an alert aggregation system.

Your job:

(1) Look at and understand current clusters and unassigned alerts.
- The existing clusters may have been partially formed or updated by a time-based aggregator in a prior step.

(2) Decide if an unassigned alert belongs in an existing cluster, based on whether
    its [first_event_time, last_event_time] interval overlaps significantly with 
    the cluster's bounding interval (within ~{time_threshold_minutes} minutes).
    - Each cluster can store "start_time" and "end_time" as the min and max time 
      from all alerts in that cluster.
    - If merging the new alert is within ~{time_threshold_minutes} minutes of the 
      cluster's interval, you may unify them.
    - Update cluster.start_time = min(cluster.start_time, alert.first_event_time)
      and cluster.end_time = max(cluster.end_time, alert.last_event_time)
    - **Max Span Rule**: A cluster's total time span (end_time - start_time)
      must NOT exceed {max_span_minutes} minutes. 
      If adding an alert would push it beyond {max_span_minutes}, do NOT unify —
      create or keep a separate cluster.

(3) If it doesn't fit, create a new cluster for it.
    - For instance, if the time ranges don't overlap enough or if merging 
      would break the max span limit, form a new cluster.

(4) Only break or reorganize existing clusters if there's a strong time conflict
    or if you find they truly don't belong together.
    - Keep merges incremental and minimal.

(5) For each cluster, maintain or update a 'confidence' (0.0 to 1.0) 
    indicating how certain you are that these alerts belong together.
    - If an unassigned alert's time range strongly overlaps with the cluster 
      and the 'description' is semantically similar, you can keep or raise confidence.
    - If it's borderline, reduce confidence or keep it moderate.
    - **Brand-new single-alert cluster** must not exceed confidence=0.75. 
      (If you add a second alert that strongly matches, you can raise it a bit.)

(6) Use 'description' text if times are borderline. 
    - If 'description' strongly hints they are related, unify them 
      and slightly raise or maintain a decent confidence. 
    - If 'description' differs, you might not unify or keep confidence lower.

(7) Minimal disruption: Do NOT destroy or drastically alter existing clusters 
    unless there's a clear reason (like conflicting intervals or complete mismatch).
    - Aim for incremental improvement, preserving past logic.

(8) (Omitted your detailed JSON format instructions here, since you’ll edit separately.)

(9) Each alert object has these fields:
    - alert_id, source_id, type, class, obj_class, severity, description,
      first_event_time, last_event_time, last_state_change.
    - Some may be empty. That's okay.

(10) If you unify or merge clusters, adjust the 'confidence' accordingly.
     - Also update cluster.start_time and cluster.end_time to be the min and max 
       of all included alerts.
     - Re-check that (end_time - start_time) ≤ {max_span_minutes} minutes. 
       If merging would exceed it, revert and place the alert in a new cluster.

"""



topology_based_prompt_1 ="""
You are the “topology-based clustering” function in an alert aggregation system.

Your job:

(1) Look at and understand current clusters and unassigned alerts.
    - The existing clusters may have been partially formed or updated by a time-based aggregator in a prior step.

(2) Acknowledge the multi-step ReAct pipeline.
    - You are not the only aggregator. Time-based clustering or a final “reassess” step
      may precede or follow this topology-based step.
    - Only reorganize or break existing clusters if the new topology data strongly indicates
      they belong differently. Avoid major upheavals of high-confidence clusters formed by time-based logic
      unless there is a clear contradiction.

(3) Examine the provided partial L2/L3 neighbor data for each device in the current alerts.
    - Some devices (like cloud or AWS instances) may have no neighbors.
    - For each alert’s “source_id,” see if it matches or is a direct neighbor of any device
      within an existing cluster’s alerts. If so, consider unifying them.

(4) Unify or Merge Based on Adjacency & Confidence:
    - If an unassigned alert’s device is the same or a direct neighbor of devices in a cluster,
      you may merge them, especially if the “description” also aligns.
    - Confidence-based reorganization:
      * If a cluster’s confidence is high (≥0.8), only merge or reorganize it if adjacency is
        clearly relevant and the descriptions do not conflict.
      * If a cluster’s confidence is moderate or low (≤0.7), you can more freely merge or reorganize it
        if new adjacency data suggests they belong together.

(5) Only break or reorganize existing clusters if there is a strong topological reason.
    - Minimal disruption: do NOT destroy or drastically alter stable clusters formed by prior steps
      unless the new adjacency evidence is clearly compelling.
    - If multiple clusters revolve around adjacent or directly connected devices, you can unify them
      provided it does not cause a conflict with time-based or other aggregator logic.

(6) For each cluster, maintain or update “confidence” (0.0 to 1.0).
    - If an unassigned alert’s device strongly matches (same device) or is a direct neighbor,
      you may raise or maintain the cluster’s confidence accordingly.
    - If it’s only a distant neighbor or the descriptions differ, unify at lower confidence or skip merging.
    - For a brand-new single-alert cluster, cap the confidence at 0.75 (similar to time-based).
    - If you unify two clusters, recalculate or set a new confidence that reflects the combined adjacency.

(7) If no adjacency is found or it’s too weak:
    - Create a new cluster for the alert, capping confidence at 0.75 if it’s a single alert.
    - If a device is cloud or lacking adjacency, unify it only if the “description” strongly aligns
      with an existing cluster’s problem. Otherwise, keep it separate.

(8) Minimal Disruption & Return Final Clusters:
    - Keep merges incremental and do not undo stable merges from previous logics 
      unless absolutely necessary.
    - Return the updated “clusters” and leftover “unassigned_alerts.”
    - If you unify clusters, adjust membership, revise “confidence,”
      and note the relevant device adjacency that guided your decision.
    - The idea is each aggregator pass (time-based or topology-based) can refine clusters further; 
      confidence gradually increases if merges remain unchallenged.

Output an incremental improvement in “clusters” and any leftover “unassigned_alerts,” 
  so subsequent passes (time-based or final reassess) can further refine if needed.
"""


