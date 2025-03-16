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


topology_based_prompt_2 ="""
You are the “topology-based clustering” function in an alert aggregation system.

Your job:

(1) Look at and understand the current clusters and any unassigned alerts.
    - These clusters may have been partially formed or updated by a time-based aggregator (or other steps).
    - Each cluster typically has:
       "cluster_id", "alerts", "confidence", possibly "start_time"/"end_time", etc.
    - "unassigned_alerts" are leftover or newly arrived alerts not yet assigned.
    - Each alert has at least:
      alert_id, source_id, type, class, obj_class, severity, description,
      first_event_time, last_event_time, last_state_change
    - Some fields (type, class, obj_class) may be empty.

(2) Multi-step ReAct pipeline awareness:
    - You are not the only aggregator. Time-based clustering or a “reassess” step
      may come before or after this topology-based step.
    - Only reorganize or break existing clusters if new topology/dependency data strongly indicates
      they belong differently. Avoid random upheaval, but do not be overly timid if adjacency is clearly relevant.

(3) Examine the partial L2/L3 neighbor data for each device in the current alerts.
    - Some devices (like AWS “lue1v...”) may have no neighbors.
    - If an alert’s “source_id” is the same or a direct neighbor of a device in an existing cluster,
      consider merging them—especially if the “description” also aligns or there are relevant site codes.

(4) Device naming schema can suggest dependencies or site-based grouping:
    - AWS instances typically start with "lue1v..." — these often have no meaningful adjacency within the local network.
      * Do not unify them merely because the alert message is similar, unless you see extremely compelling evidence.
    - Physical network devices often follow a naming scheme:
      * The first five letters = site code (e.g. "uselk", "czpcg"), indicating they might belong to the same site or region.
      * The next letter indicates device type: "s" (switch), "r" (router), "a" (Layer3 switch), "f" (firewall), "w" (Wi-Fi).
      * Some contain "controller" or "lla" in their name, meaning a L3 interface/controller or aggregator device.
    - If two devices share the same site code, or if one device’s name indicates it depends on (or is subordinate to) a device in another cluster, you can treat this as potential adjacency or dependency.
    - Examples:
      - "czpcgs1-lab-oob-a-test" => site code "czpcg", device type "s" (L2 switch).
      - "uselk11s1-lla-000" => site code "uselk", device type "s" (L2 switch), "lla" might indicate some L3 interface involvement.

(5) Adjacency vs. naming-based dependency vs. text similarity:
    - **Adjacency or site-based naming** is primary. 
      * If two devices are direct neighbors or share the same site code and device type, unify them if it makes sense, 
        especially if the descriptions do not conflict.
    - Treat AWS or “lue1v...” devices as cloud and do not unify them with local network devices just for similar messages.
    - Text similarity remains secondary. 
      * Avoid merging devices that have no adjacency (and no site-code or naming match) purely because the descriptions look similar.
      * If the naming strongly indicates a shared dependency (e.g., same site code + device type) even though partial adjacency data is incomplete, you can unify them at moderate confidence if it aligns with the problem description.

(5) Unify or Merge Based on Adjacency & Confidence:
    - For each unassigned alert, check if its source_id is the same as or a direct neighbor of any device in an existing cluster.
    - In each existing cluster, perform a per-alert analysis:
         * Determine the majority set of devices (i.e., the devices that appear as neighbors in most alerts of the cluster).
         * If an alert's source_id is not part of this majority, then treat it as an outlier.
         * Remove outlier alerts from the cluster, regardless of the overall confidence, and place them in a new cluster (capping the new cluster’s confidence at 0.75).
    - Confidence-based reorganization:
         * If a cluster’s confidence is high (≥ 0.8) due to time-based merging, do not reorganize it unless there is clear topological evidence.
         * However, if even one or two alerts in a cluster do not share the common adjacency (as determined above), lower the confidence of the cluster and separate those alerts.

      
(6) Confidence-based merging:
    - If a cluster’s confidence ≥ 0.8, treat it as fairly mature. Only reorganize or merge if the new naming or adjacency data is clearly relevant.
    - If a cluster’s confidence ≤ 0.7, you can unify or reorganize more freely if the naming schema or adjacency suggests a better grouping.
    - Brand-new single-alert cluster => confidence ≤ 0.75.
    - If you unify or reorganize, update “confidence” based on how strongly the adjacency + naming-based evidence + descriptions support that unification.

(7) Only break or reorganize existing clusters if there is a strong topological/dependency reason.
    - Minimal disruption: do NOT destroy stable clusters formed by earlier logic unless new evidence is clearly compelling.
    - If multiple clusters revolve around devices that share a site code or are direct neighbors, unify them if it does not conflict with time-based or other aggregator logic.

(8) If an alert’s device is missing adjacency or a meaningful naming pattern:
    - Create a new cluster for it at confidence ≤ 0.75.
    - If "source_id" is an AWS “lue1v…” with no neighbors, unify only if the "description" strongly suggests the same cause as a known cluster. Otherwise, keep it separate.

(9) Return final updated clusters and leftover unassigned
    - Keep merges incremental. Do not unify purely on text similarity if adjacency or naming-based evidence is lacking.
    - If you unify clusters or move an alert, revise “confidence” accordingly. 
    - A cluster with a strong naming or site-code-based link might have moderate or high confidence, 
      especially if partial adjacency also aligns.

**Your Goal**:
- Produce an **incremental** but sufficient improvement based on device topology AND naming-based dependency logic. 
- If adjacency or naming strongly indicates certain alerts belong together, unify them—even if they’re from different prior clusters (especially if those clusters have lower confidence).
- Maintain minimal disruption for high-confidence clusters unless naming or adjacency is definitively contradictory.
- Output a final “clusters” + any leftover “unassigned_alerts,” so subsequent passes (time-based, reassess, etc.) can refine further.

"""

topology_based_prompt_3 = """
You are the “topology-based clustering” function in an alert aggregation system.

Your job:

(1) Look at and understand the current clusters and unassigned alerts.
    - The current state consists of:
         • "clusters": a list of clusters, each with "cluster_id", "alerts", "confidence", and optionally "start_time"/"end_time".
         • "unassigned_alerts": alerts not yet placed in any cluster.
    - Each alert has at least:
         alert_id, source_id, type, class, obj_class, severity, description,
         first_event_time, last_event_time, last_state_change.
    - Some fields (e.g., type, class, obj_class) may be empty.

(2) Acknowledge that you operate within a multi-step ReAct pipeline.
    - Previous steps (e.g., time-based clustering) or future “reassess” steps may have influenced the current clusters.
    - Only reorganize or break existing clusters if new topology/dependency data clearly indicates a different grouping.
    - Avoid major upheavals, especially for clusters with high confidence, unless topology data strongly contradicts them.

(3) Examine the provided partial L2/L3 neighbor data for each device in the current alerts.
    - For each alert’s "source_id", check the neighbor data to determine which devices are directly connected (neighbors) at layer L2 or L3.
    - Note: Some devices (for example, AWS cloud instances whose names begin with "lue1v") may have no neighbors.

(4) Leverage device naming and dependency information:
    - Device names follow specific schemas that may imply site codes or device roles.
    - For example, names like "uselk11s1-lla-000" or "czpcgs1-lab-oob-a-test" indicate physical network devices with site codes and type markers.
    - In contrast, names starting with "lue1v" indicate AWS/cloud instances, which should not be grouped solely based on similar alert messages.
    - Use naming-based hints only to support topological evidence—not as the primary criterion.

(5) Merge alerts based on topology (adjacency) and confidence:
    - For each unassigned alert, check if its "source_id" is the same as or a direct neighbor (per the provided L2/L3 data) of any device in an existing cluster.
    - **IMPORTANT:** Topology is the primary driver. If the neighbor data does not show a direct connection, do not merge—even if the alert descriptions or device names appear similar.
    - Use text similarity (e.g., similar "description") only as a secondary factor when the topology data is ambiguous.
    - If merging is justified by clear neighbor relationships, update the cluster by adding the alert and recalculating the cluster’s bounding attributes.
    - Adjust the cluster’s "confidence" based on the strength of the topological connection:
         • If the cluster’s confidence is high (≥ 0.8), reorganize it only if the topology evidence is overwhelmingly strong.
         • If the cluster’s confidence is moderate or low (≤ 0.7), you may merge more freely if the neighbor data supports it.
         • For a brand-new cluster formed with a single alert, cap the confidence at 0.75.

(6) Reorganize clusters only when there is strong topological or dependency evidence:
    - Do not merge alerts or clusters solely on similar alert descriptions if the topology data does not confirm a direct neighbor relationship.
    - If multiple clusters contain devices that are directly connected (or share the same site code via naming), merge them—but only if the merger does not disrupt high-confidence clusters.
    - If an alert in a cluster does not share the expected topological relationship with the majority of devices (i.e., it is an outlier), remove it and place it in a separate cluster.

(7) If an alert’s device shows no meaningful adjacency (or the neighbor data is missing/negative):
    - Create a new cluster for that alert, again capping confidence at 0.75 for a single-alert cluster.
    - For cloud devices (e.g., names starting with "lue1v"), do not merge them with local network clusters solely because of text similarity.

(8) Minimal Disruption & Incremental Improvement:
    - Maintain existing clusters as much as possible; only adjust or reorganize if the topology data clearly demands it.
    - The merging process should be incremental. If a cluster is stable and has high confidence, do not reorganize it unless there is clear, compelling topological evidence.
    - If you unify clusters or move an alert, recalculate or update "confidence" to reflect the strength of the combined adjacency and naming-based evidence.

(9) Example:
    - Suppose the topology data indicates:
         • "deviceA" neighbors: ["deviceB", "deviceC"]
         • "deviceB" neighbors: ["deviceA"]
         • "deviceC" neighbors: ["deviceA"]
         • "deviceD" has no listed neighbors.
    - If alerts come from devices A, B, and D, even if the alert messages are similar, merge only the alerts from devices A and B. 
    - Do not merge the alert from device D with the others because its source_id is not a neighbor.
    - In such a case, the merged cluster for A and B may have a high confidence (e.g., 0.85), while device D would either remain unassigned or form a new cluster with confidence ≤ 0.75.

**Your Goal**:
- Produce an updated set of clusters that reflects strong topological and dependency relationships.
- Prioritize the provided L2/L3 neighbor data as the primary basis for merging alerts.
- Use device naming schema as a supporting factor for inferring dependencies, but do not merge solely on similar alert messages.
- Update each cluster's "confidence" to reflect how strongly the devices are connected.
- Return an incremental improvement in "clusters" and any leftover "unassigned_alerts" so that subsequent passes (time-based, reassess, etc.) can further refine the grouping.
"""



# examiner_prompt (the "reassess" step)

examiner_prompt = """
DO NOT SUMMARIZE OR ALTER THESE INSTRUCTIONS; USE THEM EXACTLY AS PROVIDED:

You are the 'reassess' function in an alert aggregation system. You have the current cluster state, and you also see which alerts are unassigned.

Your tasks:
1) Examine the current clusters for potential mismatches or outliers. This can include:
   - Alerts that obviously belong to a different cluster or appear entirely unrelated
   - Clusters that might actually be merged if they share overlapping time or topological dependencies
   - Overly large clusters that can be split
2) Check if any unassigned alerts might in fact belong to an existing cluster.
3) Provide suggestions on how to fix the clustering. For each suggestion:
   - Indicate which alerts or clusters should be merged, split, or moved.
   - If no changes are needed, state "No changes recommended."
4) Also indicate the recommended “next action” for the pipeline:
   - "time_based_clustering"
   - "topology_based_clustering"
   - "reorganize"
   - "finish" (if everything looks good)
   - or "no_action" (equivalent to “everything looks good”)

Return your suggestions in plain text, but structure your recommendations in a short JSON snippet at the very end of your answer. For example:

SUGGESTED_REORGANIZATION = {
  "actions": [
     {
       "type": "merge",
       "clusters": ["cluster_002", "cluster_003"]
     },
     {
       "type": "move_alert",
       "alert_id": 845198105,
       "from_cluster": "cluster_002",
       "to_cluster": "cluster_005"
     }
  ],
  "recommended_next_action": "reorganize"
}

Remember that your goal is to ensure proper clustering to help identify the root causes of these alerts. Provide chain-of-thought reasoning in your text but ensure your final answer is consistent with these instructions.
"""

def examiner_llm(self, history=[], temperature=0.01):
    if not isinstance(self.current_clusters, dict):
        raise TypeError("current_clusters must be a dictionary")

    if 'clusters' not in self.current_clusters or 'unassigned_alerts' not in self.current_clusters:
        raise KeyError("current_clusters must contain 'clusters' and 'unassigned_alerts' keys")

    # Serialize data for the prompt
    try:
        clusters_data = json.dumps({'clusters': self.current_clusters['clusters']}, indent=1)
        unassigned_alerts_data = json.dumps({'unassigned_alerts': self.current_clusters['unassigned_alerts']}, indent=1)
        current_alerts_batch_str = json.dumps(self.current_alerts_batch)

    except Exception as e:
        print(f'Error while serializing current_clusters: {e}')
        return None, history

    system_instructions = prompts.examiner_prompt  # This is the string above

    user_message_text = f"""
    This is complete batch of alerts during current time window:
    {current_alerts_batch_str}

    This is the current cluster in JSON format:
    {clusters_data}

    And here are the list of alert_ids of unassigned alerts that are currently not in any cluster:
    {unassigned_alerts_data}

    Please think through the problem step by step.
    Identify any uncertainty and unclear reasoning.
    Then suggest reorganizations if needed, and specify the recommended next action.
    """

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_message_text}
    ]

    history += messages

    # Make the LLM call
    reply = self._llm(history, temperature=temperature, model=self.llm_model)
    if 'choices' in reply and len(reply['choices']) > 0:
        answer = reply['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": answer})
        return answer, history
    else:
        print("Invalid response from API")
        return None, history


answer, history = self.examiner_llm(history)

# Now parse the suggestions out of the text
# Typically you'd do something like a regex to find the substring from:
#  SUGGESTED_REORGANIZATION = { ... } 
# Or parse a final JSON block if you trust the LLM to format valid JSON.

if answer is not None:
    # find the block after 'SUGGESTED_REORGANIZATION = '
    # load it as JSON
    import re
    match = re.search(r'SUGGESTED_REORGANIZATION\s*=\s*(\{.*\})', answer, flags=re.DOTALL)
    if match:
        suggestion_str = match.group(1)
        try:
            suggestions = json.loads(suggestion_str)
            # e.g. suggestions['actions'], suggestions['recommended_next_action']
        except:
            suggestions = None

    # If suggestions is not None, proceed to handle them


def reorganize_clusters(self, suggestions):
    """
    suggestions is a dict that might look like:
    {
      "actions": [
         {
           "type": "merge",
           "clusters": ["cluster_002", "cluster_003"]
         },
         {
           "type": "move_alert",
           "alert_id": 845198105,
           "from_cluster": "cluster_002",
           "to_cluster": "cluster_005"
         }
      ],
      "recommended_next_action": "reorganize"  # or "time_based_clustering", etc.
    }
    """
    if "actions" not in suggestions:
        return self.current_clusters  # no changes

    actions = suggestions["actions"]
    # Keep a quick reference so we can find clusters by ID easily
    clusters_by_id = {c["cluster_id"]: c for c in self.current_clusters["clusters"]}

    for action in actions:
        atype = action.get("type")
        
        if atype == "merge":
            # e.g. merges multiple clusters into the first cluster
            cluster_ids_to_merge = action.get("clusters", [])
            if len(cluster_ids_to_merge) < 2:
                continue
            primary_cluster_id = cluster_ids_to_merge[0]
            for cid in cluster_ids_to_merge[1:]:
                if cid not in clusters_by_id:
                    continue
                # Move all alerts from the cluster cid to the primary cluster
                # Then remove cid from the self.current_clusters
                src_cluster = clusters_by_id[cid]
                primary_cluster = clusters_by_id[primary_cluster_id]

                # combine alert_ids, source_ids, etc.
                # be sure to unify them uniquely (no duplicates)
                primary_cluster["alert_ids"] = list(set(primary_cluster["alert_ids"] + src_cluster["alert_ids"]))
                primary_cluster["source_ids"] = list(set(primary_cluster["source_ids"] + src_cluster["source_ids"]))

                # remove the cluster cid from the list
                self.current_clusters["clusters"] = [c for c in self.current_clusters["clusters"] 
                                                     if c["cluster_id"] != cid]
                # Also remove from dictionary
                clusters_by_id.pop(cid, None)

            # Recompute bounding time or confidence if needed ...
            # e.g.:
            # primary_cluster["time"]["start"] = min( your new min time among all alerts )
            # primary_cluster["time"]["end"]   = max( your new max time among all alerts )
            # possibly re-set "confidence" if you want to.

        elif atype == "move_alert":
            # e.g. move a single alert from one cluster to another
            alert_id = action.get("alert_id")
            from_cid = action.get("from_cluster")
            to_cid = action.get("to_cluster")
            if (from_cid in clusters_by_id) and (to_cid in clusters_by_id):
                from_cluster = clusters_by_id[from_cid]
                to_cluster   = clusters_by_id[to_cid]

                # remove alert from 'from_cluster'
                from_cluster["alert_ids"] = [aid for aid in from_cluster["alert_ids"] if aid != alert_id]

                # add alert to 'to_cluster'
                if alert_id not in to_cluster["alert_ids"]:
                    to_cluster["alert_ids"].append(alert_id)

                # recalc times, confidence, etc., as needed

        # you can add more action types, like "split", etc.

    return self.current_clusters


answer, history = self.examiner_llm(history)
if answer:
    # parse JSON instructions from answer
    suggestions = parse_suggestions_from(answer)
    if not suggestions:
        # no reorg suggestions, maybe just move on
        pass
    else:
        next_action = suggestions.get("recommended_next_action", "no_action")
        if next_action == "reorganize":
            self.current_clusters = self.reorganize_clusters(suggestions)
        elif next_action == "time_based_clustering":
            # call your time_based_clustering_llm(...)
            pass
        elif next_action == "topology_based_clustering":
            # call your topology_based_clustering_llm(...)
            pass
        elif next_action == "finish":
            # call your finish() or just end
            pass
        else:
            # no_action or something else
            pass


def finish(self):
    print("==== FINAL CLUSTERS ====")
    print(json.dumps(self.current_clusters, indent=2))
    # Potentially do more logging, or return self.current_clusters
    return self.current_clusters

def finish_llm(self, history=[], temperature=0.01):
    system_instructions = """
    You are the final summarizer. Summarize the final clusters and hypothesize the potential root cause(s).
    """
    user_message_text = f"""
    The final clusters are:
    {json.dumps(self.current_clusters, indent=2)}
    Please produce a short summary in plain text.
    """

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_message_text}
    ]
    history += messages
    reply = self._llm(history, temperature=temperature, model=self.llm_model)
    if 'choices' in reply and len(reply['choices']) > 0:
        answer = reply['choices'][0]['message']['content']
        print("=== Final summary ===")
        print(answer)
    return self.current_clusters
