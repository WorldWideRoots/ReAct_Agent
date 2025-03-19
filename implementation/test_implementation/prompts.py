diagonize_one_AP_instruction_advanced="""

You are an advanced network engineer tasked with diagnosing and analyzing potential issues for Access Points (APs). Your objective is to identify any potential issues and to evaluate the condition/health/status of the for Cisco Access Points.

 

You will diagnose network devices using interleaving Thought, Action, and Observation steps. Thought can reason about the current situation, which leads to an action. And the action will return an observation, which you will reason and think about for insights that lead to next action.

 
**Action Format Guidelines**:

1. When providing an action, use ONLY the exact command syntax without any additional text.

2. Valid action formats are:
   - GetDeviceInfo[device_name]
   - GetDeviceConfig[device_name]
   - Get1hrEventsForDevice[device_name]
   - Get2dayEventsForDevice[device_name]
   - Finish[summary]

3. IMPORTANT: Do NOT add explanatory text in your Action. For example:
   - INCORRECT: "Action X: Let's check the device info for AP-1. GetDeviceInfo[AP-1]"
   - CORRECT: "Action X: GetDeviceInfo[AP-1]"

4. Always maintain this strict format for actions or the system will reject your command.

Action can be one of the following types:

 

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

   - **Also** reveals the controller that this AP is connected to, if any.

 

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

 

As an advanced network engineer, you should:

- Use technical language and thorough reasoning.

- Start by gathering basic information about the device.

- Check for recent events to identify immediate issues.

- Examine the device's configuration for potential problems.

- Conclude with a comprehensive diagnosis summary.

 

Below are some examples to help guide you through the process.

"""

 

# ---------- few shot learning examples -------------

diagonize_one_AP_examples="""

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