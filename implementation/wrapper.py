import os, json
import openai 
import gymnasium as gym
import numpy as np

class LoggingWrapper(gym.Wrapper):
    def __init__(self, env, folder="ap_diagnostics_logs", file_id=None):
        super().__init__(env)
        self.trajs = []
        self.traj = {"observations": [], "actions": []}
        self.folder = folder
        self.file_id = np.random.randint(0, 10000000) if file_id is None else file_id
        self.file_path = f"{self.folder}/{self.file_id}.json"
        os.makedirs(self.folder, exist_ok=True)

    def reset(self, seed=None, alert_info=None, return_info=False, options=None, idx=None):
        output = self.env.reset(alert_info=alert_info, seed=seed, return_info=return_info, options=options, idx=idx)
        observation = output[0] if return_info else output
        self.traj = {"observations": [observation], "actions": []}
        return output

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.traj["observations"].append(obs)
        self.traj["actions"].append(action)
        if done:
            self.traj.update(info)
        return obs, reward, done, info

    def update_record(self):
        if len(self.traj["actions"]) > 0:
            self.trajs.append(self.traj)
            self.traj = {"observations": [], "actions": []}

    def write(self):
        self.update_record()
        with open(self.file_path, "w") as f:
            json.dump(self.trajs, f, indent=2)
            print(f"Saved trajs to {self.file_path}")

    def close(self):
        self.write()
