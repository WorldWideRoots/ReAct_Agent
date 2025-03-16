import json
from typing import Dict, List, Any

# Import our classes
from NetworkAlertEnvironment import NetworkAlertEnvironment
from NetworkAlertAgent import NetworkAlertAgent
from system_prompt import get_network_alert_system_prompt

def run_alert_aggregation_example():
    """
    Example of running the network alert aggregation system.
    """
    # Sample alerts data
    sample_alerts = [
        {
            "source_id": "uselk11s1-lla-000",
            "alert_id": 845204837,
            "type": "network",
            "class": "performance",
            "object_class": "switch",
            "severity": "high",
            "description": "Switch overload detected",
            "first_event_time": 1741041666,
            "last_event_time": 1741045666,
            "last_state_change": 1741045666,
            "site": "uselk",
            "device_type": "switch"
        },
        {
            "source_id": "uselk11s1-lla-001",
            "alert_id": 845204838,
            "type": "network",
            "class": "performance",
            "object_class": "switch",
            "severity": "medium",
            "description": "Performance degradation",
            "first_event_time": 1741041766,
            "last_event_time": 1741045766,
            "last_state_change": 1741045766,
            "site": "uselk",
            "device_type": "switch"
        },
        {
            "source_id": "isikas1-sec",
            "alert_id": 845204839,
            "type": "security",
            "class": "threat",
            "object_class": "firewall",
            "severity": "high",
            "description": "Intrusion detected",
            "first_event_time": 1741041866,
            "last_event_time": 1741045866,
            "last_state_change": 1741045866,
            "site": "isikas",
            "device_type": "firewall"
        },
        {
            "source_id": "lue1vp11824",
            "alert_id": 845204840,
            "type": "system",
            "class": "resource",
            "object_class": "vm",
            "severity": "low",
            "description": "CPU usage high",
            "first_event_time": 1741042766,
            "last_event_time": 1741046766,
            "last_state_change": 1741046766,
            "site": "cloud",
            "device_type": "vm"
        }
    ]
    
    # Sample topology data
    sample_topology = {
        "uselk11s1-lla-000": {
            "L2_Topo_Type": ["uselk11s1-lla-001"],
            "L3_Topo_Type": []
        },
        "uselk11s1-lla-001": {
            "L2_Topo_Type": ["uselk11s1-lla-000"],
            "L3_Topo_Type": ["isikas1-sec"]
        },
        "isikas1-sec": {
            "L2_Topo_Type": [],
            "L3_Topo_Type": ["uselk11s1-lla-001"]
        },
        "lue1vp11824": {
            "L2_Topo_Type": [],
            "L3_Topo_Type": []
        }
    }
    
    # Create the environment
    env = NetworkAlertEnvironment(alerts=sample_alerts, topology_info=sample_topology)
    
    # Create the agent
    agent = NetworkAlertAgent(env=env)
    
    # Set valid action prefixes
    agent.set_valid_prefixes([
        "InitialExploration[",
        "TimeBasedClustering[",
        "TopologyBasedClustering[",
        "Reassess[",
        "DirectReorganize[",
        "Finish["
    ])
    
    # Get the system prompt
    system_prompt = get_network_alert_system_prompt()
    
    # Run the agent with a recommended sequence of actions
    print("Running alert aggregation with intelligent action selection...\n")
    reward, info = agent.react(
        initial_prompt=system_prompt,
        max_num_steps=8,  # Allow for more steps to include assessment phases
        to_print=True
    )
    
    # Print the final clusters
    print("\nFinal Clusters:")
    print(json.dumps(info["clusters"], indent=2))
    
    # Example of a manual step-by-step approach (alternative to using ReAct)
    def manual_aggregation_example():
        """Demonstrate a manual step-by-step approach to alert aggregation"""
        print("\nDemonstrating manual step-by-step approach...")
        
        # Reset the environment
        env.reset(alerts=sample_alerts, topology_info=sample_topology)
        
        # Step 1: Initial Exploration
        print("\nStep 1: Initial Exploration")
        obs, reward, done, info = env.step("InitialExploration[]")
        print(f"Observation: {obs}")
        
        # Step 2: Time-Based Clustering
        print("\nStep 2: Time-Based Clustering")
        obs, reward, done, info = env.step("TimeBasedClustering[]")
        print(f"Observation: {obs}")
        
        # Step 3: Assessment
        print("\nStep 3: Assessing Clusters")
        obs, reward, done, info = env.step("Reassess[]")
        print(f"Observation: {obs}")
        
        # Step 4: Follow recommendation (assuming it's Topology-Based Clustering)
        print("\nStep 4: Follow Recommendation (Topology-Based Clustering)")
        obs, reward, done, info = env.step("TopologyBasedClustering[]")
        print(f"Observation: {obs}")
        
        # Step 5: Final Assessment
        print("\nStep 5: Final Assessment")
        obs, reward, done, info = env.step("Reassess[]")
        print(f"Observation: {obs}")
        
        # Step 6: Finish
        print("\nStep 6: Finish")
        obs, reward, done, info = env.step("Finish[Alert aggregation complete]")
        print(f"Observation: {obs}")
        
        return info["clusters"]
    
    # Optionally run the manual example
    # manual_clusters = manual_aggregation_example()
    
    return info["clusters"]

if __name__ == "__main__":
    run_alert_aggregation_example()