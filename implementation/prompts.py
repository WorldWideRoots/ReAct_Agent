potential_prompts = """
Scenario 1: AP is reported offline unexpectedly
Context: A network engineer sees an AP (named AP-11-3A-45) has gone offline. They want to check the device detail, the AP-specific config, and gather recent events.

Thought 1:
We have an AP offline alert for AP-11-3A-45. First, I'll retrieve basic device details from DNAC.
Action 1: GetDeviceDetail[AP-11-3A-45]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-11-3A-45",
    "managementIpAddress": "10.10.22.70",
    "macAddress": "F8:7B:7A:12:34:56",
    "location": "Building-A-Floor-3",
    "softwareVersion": "17.3.1",
    "reachabilityStatus": "Unreachable",
    "reachabilityFailureReason": "SNMP Timeout"
  }
}

Thought 2:
The AP is unreachable per DNAC. Let me see if there's a specific wireless config that might have changed.
Action 2: GetWirelessDeviceConfig[F8:7B:7A:12:34:56]
Observation 2: {
  "response": {
    "radioFrequencyParameters": {
      "channel": 36,
      "channelWidth": 20,
      "txPowerLevel": 3
    },
    "ssidDetails": [
      { "ssidName": "CorpWiFi", "securityMode": "WPA2" },
      { "ssidName": "GuestWiFi", "securityMode": "WPA2" }
    ],
    "apMode": "Local"
  }
}

Thought 3:
Channel is 36, power level 3, looks normal. Let me check the last hour of events to see if there's a critical reason it went unreachable.
Action 3: GetAssuranceDeviceEvents[AP-11-3A-45, pastHour]
Observation 3: {
  "response": [
    {
      "timestamp": 1681224000000,
      "eventId": "AP_DOWN",
      "severity": "CRITICAL",
      "issueCategory": "Connectivity",
      "message": "AP has lost connection to WLC"
    },
    {
      "timestamp": 1681224100000,
      "eventId": "RRM_CHANNEL_CHANGE",
      "severity": "INFO",
      "issueCategory": "Config",
      "message": "Dynamic channel change triggered"
    }
  ]
}

Thought 4:
We see an AP_DOWN event. Possibly a radio or controller issue. The RRM channel change also occurred right before. That might have caused the radio to reboot or get stuck. I'll conclude the diagnosis.
Action 4: Finish[AP-11-3A-45 is unreachable. Recent AP_DOWN event after an RRM channel change. Recommend checking WLC logs or radio health.]
Observation 4: Episode finished, reward = 0
Key Points in this example:

We used a slightly different action name GetAssuranceDeviceEvents[AP-11-3A-45, pastHour]. In your environment, you might name it Get1hrEventsForDevice[...].
We’re returning a JSON with a top-level "response" array or object, consistent with many DNAC endpoints.
2.2 Scenario 2: AP is online but clients complain of poor performance
Context: Another scenario; the AP is up, but the engineer suspects channel interference or high load. They retrieve device detail, then AP config, then 2-day events to see if there’s a pattern.

Thought 1:
We have user complaints about poor Wi-Fi on AP-22-1B-09. Let's see device detail first.
Action 1: GetDeviceDetail[AP-22-1B-09]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-22-1B-09",
    "managementIpAddress": "10.10.33.80",
    "macAddress": "F8:7B:7A:98:76:54",
    "location": "Building-B-Floor-1",
    "softwareVersion": "17.3.2",
    "reachabilityStatus": "Reachable",
    "reachabilityFailureReason": ""
  }
}

Thought 2:
AP is reachable, software at 17.3.2. I'll see the current wireless config to check channel usage.
Action 2: GetWirelessDeviceConfig[F8:7B:7A:98:76:54]
Observation 2: {
  "response": {
    "radioFrequencyParameters": {
      "channel": 1,
      "channelWidth": 20,
      "txPowerLevel": 5
    },
    "ssidDetails": [
      { "ssidName": "CorpWiFi", "securityMode": "WPA2" }
    ],
    "apMode": "Local"
  }
}

Thought 3:
Channel 1 can be crowded in 2.4GHz. Let me see if there were events about interference in the past 2 days.
Action 3: GetAssuranceDeviceEvents[AP-22-1B-09, past2Days]
Observation 3: {
  "response": [
    {
      "timestamp": 1681051200000,
      "eventId": "HIGH_CHANNEL_UTILIZATION",
      "severity": "WARNING",
      "message": "Channel utilization above 80%."
    },
    {
      "timestamp": 1681137600000,
      "eventId": "AP_CLI_LOAD_HIGH",
      "severity": "WARNING",
      "message": "AP has high client load (30+)."
    }
  ]
}

Thought 4:
So, there's high channel utilization and high client load. This explains poor performance. I’ll wrap up.
Action 4: Finish[AP on channel 1 with high load and interference; recommend moving to 5GHz or changing channel to reduce congestion.]
Observation 4: Episode finished, reward = 0

"""


more_potentioal_prompts="""
Thought 1:
We have an alert that AP-101 is down. Let me check the AP’s device detail from DNAC first.
Action 1: GetDeviceDetail[AP-101]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-101",
    "managementIpAddress": "10.10.101.5",
    "macAddress": "AA:BB:CC:10:10:01",
    "location": "Building J - Floor 2",
    "softwareVersion": "17.3.3",
    "reachabilityStatus": "Unreachable",
    "reachabilityFailureReason": "SNMP Timeout",
    "associatedWlc": "WLC-1"
  }
}

Thought 2:
AP is unreachable, associated with WLC-1. Let me see the last hour’s events to see if there’s a PoE or cable issue or an AP_DOWN.
Action 2: GetAssuranceDeviceEvents[AP-101, pastHour]
Observation 2: {
  "response": [
    {
      "timestamp": 1682107000000,
      "eventId": "AP_DOWN",
      "severity": "CRITICAL",
      "issueCategory": "Connectivity",
      "message": "AP lost power or network connection"
    },
    {
      "timestamp": 1682107050000,
      "eventId": "SWITCH_PORT_ERR_DISABLED",
      "severity": "WARNING",
      "message": "AP’s switch port was err-disabled"
    }
  ]
}

Thought 3:
The switch port got err-disabled, possibly due to spanning-tree or security violation. Let me confirm the AP’s controller is up. 
The AP’s associated WLC is “WLC-1.” Let me do a device detail check on WLC-1, maybe it’s in DNAC under the same name.
Action 3: GetDeviceDetail[WLC-1]
Observation 3: {
  "response": {
    "nwDeviceName": "WLC-1",
    "managementIpAddress": "10.10.200.10",
    "reachabilityStatus": "Reachable",
    "softwareVersion": "17.3.3",
    "macAddress": "00:11:22:33:44:55",
    "location": "Data Center"
  }
}

Thought 4:
The controller (WLC-1) is reachable. So the problem is likely the AP’s switch port. Possibly a PoE or port security issue. Let me finalize the diagnosis.
Action 4: Finish[AP-101 is offline due to switch port err-disable. WLC is up. Recommend investigating switch port or PoE configuration for AP-101.]
Observation 4: Episode finished, reward = 0
Key Takeaways
The engineer began with only “AP-101 is down.”
They branched to check the WLC’s status using the same GetDeviceDetail[WLC-1] call.
The final recommendation is to investigate the switch/PoE config.


Scenario 2: AP is reachable, but clients complain about packet loss

Context: The engineer only knows that “AP-202” is causing slow or dropped connections. They suspect the controller, or maybe site-level issues, so they check site health and other potential clues.

Thought 1:
We have user complaints about AP-202 (packet loss, slow speed). Let’s see basic details first.
Action 1: GetDeviceDetail[AP-202]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-202",
    "managementIpAddress": "10.10.202.10",
    "macAddress": "DD:EE:FF:20:20:20",
    "location": "Building K - Floor 5",
    "softwareVersion": "17.3.3",
    "reachabilityStatus": "Reachable",
    "associatedWlc": "WLC-2"
  }
}

Thought 2:
AP is reachable, running 17.3.3. Let’s see if there’s a high channel utilization or interference event in the last 2 days.
Action 2: GetAssuranceDeviceEvents[AP-202, past2Days]
Observation 2: {
  "response": [
    {
      "timestamp": 1682000000000,
      "eventId": "HIGH_CHANNEL_UTILIZATION",
      "severity": "WARNING",
      "message": "Channel utilization above 85%"
    }
  ]
}

Thought 3:
That explains packet loss. Possibly the channel is overloaded. Let me see the AP’s wireless config for channel/band.
Action 3: GetWirelessDeviceConfig[DD:EE:FF:20:20:20]
Observation 3: {
  "response": {
    "radioFrequencyParameters": {
      "channel": 1,
      "channelWidth": 20,
      "txPowerLevel": 4
    },
    "ssidDetails": [
      {
        "ssidName": "CorpWiFi",
        "securityMode": "WPA2"
      }
    ],
    "apMode": "Local"
  }
}

Thought 4:
Channel 1 in 2.4GHz is often congested. Possibly we want to check overall site health to see if multiple APs are impacted.
Action 4: GetDeviceDetail[WLC-2]
Observation 4: {
  "response": {
    "nwDeviceName": "WLC-2",
    "managementIpAddress": "10.10.250.5",
    "reachabilityStatus": "Reachable",
    "softwareVersion": "17.3.3"
  }
}

Thought 5:
The WLC is up. We do see high channel utilization. Probably we can fix by changing channel or letting RRM do an update. 
Action 5: Finish[AP-202 has high channel utilization on 2.4GHz, causing packet loss. Recommend moving to 5GHz or adjusting RRM settings.]
Observation 5: Episode finished, reward = 0
Key Takeaways
Starts with “AP-202 is slow.”
Finds “HIGH_CHANNEL_UTILIZATION.”
Checks the AP’s WLC as well but sees no WLC problem, so the final recommendation is channel reconfiguration.


Scenario 3: AP intermittently flaps, possibly a WLC software bug

Context: The AP “AP-303” frequently goes up and down. The engineer doesn’t know if it’s a hardware issue, or maybe the WLC has a known bug.

Thought 1:
We have repeated up/down alerts for AP-303. Let’s see device detail first.
Action 1: GetDeviceDetail[AP-303]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-303",
    "managementIpAddress": "10.10.303.5",
    "macAddress": "FA:33:29:AA:BB:CC",
    "location": "Building L - Floor 1",
    "softwareVersion": "17.3.2",
    "reachabilityStatus": "Reachable",
    "associatedWlc": "WLC-3"
  }
}

Thought 2:
AP is reachable for now. Let’s see if the last hour events show multiple flaps.
Action 2: GetAssuranceDeviceEvents[AP-303, pastHour]
Observation 2: {
  "response": [
    {
      "timestamp": 1682111000000,
      "eventId": "AP_DOWN",
      "severity": "CRITICAL",
      "message": "AP unexpectedly disconnected"
    },
    {
      "timestamp": 1682111300000,
      "eventId": "AP_UP",
      "severity": "INFO",
      "message": "AP reconnected to the controller"
    }
  ]
}

Thought 3:
We do see a flap. Possibly the controller “WLC-3” is having issues. Let’s check WLC-3’s device detail.
Action 3: GetDeviceDetail[WLC-3]
Observation 3: {
  "response": {
    "nwDeviceName": "WLC-3",
    "managementIpAddress": "10.10.250.8",
    "reachabilityStatus": "Reachable",
    "softwareVersion": "17.3.1",
    "uptime": "45 days",
    "reachabilityFailureReason": ""
  }
}

Thought 4:
The WLC is also on 17.3.1, the AP is on 17.3.2. Possibly a mismatch or a known bug with this combination. Let me finalize.
Action 4: Finish[AP-303 repeatedly flaps between up and down. WLC-3 on older 17.3.1 may cause a known mismatch bug. Suggest updating WLC or AP firmware to stable release.]
Observation 4: Episode finished, reward = 0
Key Takeaways
The engineer sees repeated flaps, checks both AP and WLC.
They conclude a firmware mismatch might cause the flapping.
Scenario 4: AP down, suspecting site-level power outages or general meltdown

Context: “AP-404” is offline, but the entire site might be in trouble. The engineer checks the AP, then sees if the site or other devices are also impacted.

Thought 1:
We have an alert that AP-404 is down. Let’s see its detail first.
Action 1: GetDeviceDetail[AP-404]
Observation 1: {
  "response": {
    "nwDeviceName": "AP-404",
    "managementIpAddress": "10.10.404.5",
    "macAddress": "AA:BB:CC:40:40:04",
    "location": "Building M - Floor 4",
    "softwareVersion": "17.3.3",
    "reachabilityStatus": "Unreachable",
    "associatedWlc": "WLC-4"
  }
}

Thought 2:
The AP is unreachable. Let me see if the last hour of events mention a site-level power or meltdown.
Action 2: GetAssuranceDeviceEvents[AP-404, pastHour]
Observation 2: {
  "response": [
    {
      "timestamp": 1682208000000,
      "eventId": "SITE_POWER_ISSUE",
      "severity": "CRITICAL",
      "message": "Detected partial power outage in Building M"
    },
    {
      "timestamp": 1682208100000,
      "eventId": "AP_DOWN",
      "severity": "CRITICAL",
      "message": "AP-404 lost power"
    }
  ]
}

Thought 3:
So it’s site-level. Possibly the whole floor lost PoE or building power. Let me see the WLC though, in case it’s also unreachable.
Action 3: GetDeviceDetail[WLC-4]
Observation 3: {
  "response": {
    "nwDeviceName": "WLC-4",
    "managementIpAddress": "10.10.255.10",
    "reachabilityStatus": "Reachable",
    "softwareVersion": "17.3.3"
  }
}

Thought 4:
The WLC is fine. We have a partial power outage in Building M. That’s likely the cause. 
Action 4: Finish[AP-404 is offline due to a site-level power outage. WLC is okay. Restore power to Building M to bring AP-404 back online.]
Observation 4: Episode finished, reward = 0
Key Takeaways
The engineer sees a site-level meltdown indicated by an event “SITE_POWER_ISSUE.”
They confirm the WLC is up, so the final conclusion is about the building power problem.
"""




new_instructions = """
You are a network diagnosis assistant for Cisco Access Points.

You have **five actions** to diagnose AP problems:

1. GetDeviceInfo[device_name]
   - Retrieves basic data about the device (AP or WLC). 
   - Returns JSON with fields like:
     - "deviceName"
     - "connectivityStatus" (<=0 ⇒ device is DOWN, >0 ⇒ device is UP)
     - "ipAddress"
     - "softwareVersion"
     - "location"
     - "uptime"
   - **Important**: This does **not** reveal which controller the AP is connected to.

2. GetDeviceConfig[device_name]
   - Retrieves the AP’s wireless configuration (radio frequency info, SSIDs, etc.).
   - **Also** reveals "controllerName": the WLC that this AP is connected to, if any.

3. Get1hrEventsForDevice[device_name]
   - Retrieves the last 1 hour’s assurance events (AP_DOWN, AUTH_FAILURES, etc.).

4. Get2dayEventsForDevice[device_name]
   - Retrieves the last 2 days’ assurance events.

5. Finish[summary]
   - Ends the diagnostic session with an actionable recommendation.

**ReAct Format**:
- "Thought X": your chain-of-thought.
- "Action X": one of the five actions above.
- "Observation X": the environment’s returned JSON/text.

**Key Points**:
- If you suspect the AP’s controller might be relevant, first call GetDeviceConfig[theAP] to learn `controllerName`, then call `GetDeviceInfo[thatControllerName]` (or events on that controller) if needed.
- If `connectivityStatus <= 0` in GetDeviceInfo, that device is effectively DOWN.
- You can do up to 8 steps total. 
- Provide an **actionable suggestion** in `Finish[...]`.

Start from **only** the AP name and an alert (e.g., “AP-X is down” or “AP-Y has complaints”). Gather info step by step using these actions. 

"""

fsl_examples_3="""
Scenario A: AP is down, discovering the controller from config
Thought 1:
Alert: "AP-Alpha is down." Let's confirm if it’s truly down.
Action 1: GetDeviceInfo[AP-Alpha]
Observation 1: {
  "deviceName": "AP-Alpha",
  "connectivityStatus": 0,
  "ipAddress": "10.10.50.1",
  "softwareVersion": "17.3.3",
  "location": "Building A - Floor 2",
  "uptime": 0
}

Thought 2:
connectivityStatus=0 means AP-Alpha is indeed unreachable. Let me see the AP’s config to find the controller name.
Action 2: GetDeviceConfig[AP-Alpha]
Observation 2: {
  "radioFrequencyParameters": {
    "channel": 36,
    "txPowerLevel": 3
  },
  "controllerName": "WLC-Alpha",
  "ssidDetails": [
    { "ssidName": "CorpWiFi", "securityMode": "WPA2" }
  ]
}

Thought 3:
So it’s attached to WLC-Alpha. Let me check if WLC-Alpha is up.
Action 3: GetDeviceInfo[WLC-Alpha]
Observation 3: {
  "deviceName": "WLC-Alpha",
  "connectivityStatus": 2,
  "ipAddress": "10.10.200.5",
  "softwareVersion": "17.3.3",
  "location": "Data Center",
  "uptime": 500000
}

Thought 4:
WLC is up, so AP-Alpha might have lost PoE or a switch port. Let me confirm events from the last hour.
Action 5: Get1hrEventsForDevice[AP-Alpha]
Observation 5: {
  "events": [
    {
      "eventId": "AP_DOWN",
      "severity": "CRITICAL",
      "message": "AP has lost power or cable link"
    }
  ]
}

Thought 5:
Yes, it’s definitely offline. 
Action 6: Finish[AP-Alpha is unreachable. WLC is up. Suggest checking PoE or cable for AP-Alpha to restore connectivity.]
Observation 6: Episode finished, reward=0
Scenario B: AP is up, but suspect channel interference; also check the WLC
Thought 1:
Users say AP-Bravo is slow. Let’s confirm if AP-Bravo is up.
Action 1: GetDeviceInfo[AP-Bravo]
Observation 1: {
  "deviceName": "AP-Bravo",
  "connectivityStatus": 2,
  "ipAddress": "10.20.30.40",
  "softwareVersion": "17.2.1",
  "location": "Building B - Floor 1",
  "uptime": 36000
}

Thought 2:
connectivityStatus=2 => AP is up. Let me see the config to find the channel, plus the controller name.
Action 2: GetDeviceConfig[AP-Bravo]
Observation 2: {
  "radioFrequencyParameters": {
    "channel": 1,
    "txPowerLevel": 4
  },
  "controllerName": "WLC-East",
  "ssidDetails": [
    { "ssidName": "CorpWiFi", "securityMode": "WPA2" }
  ]
}

Thought 3:
Channel 1 can be congested. Also, the controller is WLC-East. Let me see events from the last hour for AP-Bravo.
Action 3: Get1hrEventsForDevice[AP-Bravo]
Observation 3: {
  "events": [
    {
      "eventId": "HIGH_CHANNEL_UTILIZATION",
      "severity": "WARNING",
      "message": "Channel utilization at 85%"
    }
  ]
}

Thought 4:
We have high channel utilization. Let me quickly see if the WLC is up or outdated.
Action 5: GetDeviceInfo[WLC-East]
Observation 5: {
  "deviceName": "WLC-East",
  "connectivityStatus": 2,
  "ipAddress": "10.10.200.10",
  "softwareVersion": "17.2.1",
  "location": "Data Center"
}

Thought 5:
The WLC is up. So the root cause is channel congestion. 
Action 6: Finish[AP-Bravo is on channel 1 with high utilization. Consider switching to 5GHz or adjusting RRM for better performance.]
Observation 6: Episode finished, reward=0
Scenario C: AP flapping, found repeated radio resets
Thought 1:
We have “AP-Charlie is flapping.” Let’s see if it’s currently up or down.
Action 1: GetDeviceInfo[AP-Charlie]
Observation 1: {
  "deviceName": "AP-Charlie",
  "connectivityStatus": 1,
  "ipAddress": "10.10.33.33",
  "softwareVersion": "17.3.2",
  "location": "Building C - Floor 4",
  "uptime": 18000
}

Thought 2:
It’s somewhat up (connectivityStatus=1). Let me see config for the controller name.
Action 2: GetDeviceConfig[AP-Charlie]
Observation 2: {
  "radioFrequencyParameters": {
    "channel": 149,
    "txPowerLevel": 3
  },
  "controllerName": "WLC-Charlie",
  "ssidDetails": [
    { "ssidName": "CorpWiFi", "securityMode": "WPA2" }
  ]
}

Thought 3:
So it’s on WLC-Charlie. Let me see 1hr events for AP-Charlie to confirm flapping or radio resets.
Action 3: Get1hrEventsForDevice[AP-Charlie]
Observation 3: {
  "events": [
    {
      "eventId": "AP_RADIO_RESET",
      "severity": "CRITICAL",
      "message": "Radio interface reset multiple times"
    }
  ]
}

Thought 4:
Yes, repeated radio resets. Let me also check 2 days of events for more pattern.
Action 5: Get2dayEventsForDevice[AP-Charlie]
Observation 5: {
  "events": [
    {
      "eventId": "AP_RADIO_RESET",
      "severity": "CRITICAL",
      "message": "Happened yesterday too"
    }
  ]
}

Thought 5:
So repeated radio resets. Possibly a firmware bug or hardware fault. 
Action 6: Finish[AP-Charlie flaps due to repeated radio resets. Recommend firmware upgrade or RMA if resets continue.]
Observation 6: Episode finished, reward=0
Scenario D: AP is actually up—false alarm, no mention of controller needed
Thought 1:
We have an alert that AP-Delta is down. Let me see if that’s accurate.
Action 1: GetDeviceInfo[AP-Delta]
Observation 1: {
  "deviceName": "AP-Delta",
  "connectivityStatus": 2,
  "ipAddress": "10.10.44.44",
  "softwareVersion": "17.3.3",
  "location": "Building D - Floor 2",
  "uptime": 72000
}

Thought 2:
connectivityStatus=2 means it’s definitely up. Possibly a false alarm. Let me see 1hr events to confirm no real issue.
Action 2: Get1hrEventsForDevice[AP-Delta]
Observation 2: {
  "events": []
}

Thought 3:
No events. It’s probably a monitoring glitch. I don’t need to check the controller if the AP is obviously up. 
Action 4: Finish[AP-Delta is up, no recent events. Alert is likely a false positive. Just monitor in case it flaps again.]
Observation 4: Episode finished, reward=0
Scenario E: AP is offline, config indicates WLC-Echo; WLC also down
Thought 1:
We got an alert: “AP-Echo is offline.” Let’s confirm AP-Echo’s device info.
Action 1: GetDeviceInfo[AP-Echo]
Observation 1: {
  "deviceName": "AP-Echo",
  "connectivityStatus": 0,
  "ipAddress": "10.10.60.60",
  "softwareVersion": "17.2.1",
  "location": "Building E - Floor 1"
}

Thought 2:
connectivityStatus=0 => AP-Echo is indeed unreachable. Let me see the config to find the WLC name.
Action 2: GetDeviceConfig[AP-Echo]
Observation 2: {
  "radioFrequencyParameters": {
    "channel": 11,
    "txPowerLevel": 4
  },
  "controllerName": "WLC-Echo",
  "ssidDetails": [
    { "ssidName": "GuestWiFi", "securityMode": "WPA2" }
  ]
}

Thought 3:
So the AP’s controller is WLC-Echo. Let me see if WLC-Echo is up.
Action 3: GetDeviceInfo[WLC-Echo]
Observation 3: {
  "deviceName": "WLC-Echo",
  "connectivityStatus": 0,
  "ipAddress": "10.10.250.60",
  "softwareVersion": "17.2.1",
  "location": "Data Center - East"
}

Thought 4:
WLC-Echo is also down (connectivityStatus=0). That’s likely why AP-Echo is offline. Let me finalize.
Action 5: Finish[AP-Echo is offline because WLC-Echo is also down. Restore WLC-Echo connectivity or power to bring AP-Echo back online.]
Observation 5: Episode finished, reward=0

"""