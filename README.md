# Felicity Battery (TCP) integration for Home Assistant

Custom integration for **Felicity FLA48200** (and similar) batteries which expose
a local TCP API on port `53970`.

The integration:

- connects to `IP:PORT` of the Felicity Wi-Fi module,
- sends `wifilocalMonitor:get dev real infor`,
- parses the JSON response,
- creates **one device** in Home Assistant with multiple sensors:
  - SOC, voltage, current, power
  - temperatures
  - max/min cell voltage and delta
  - charge/discharge current limits
  - state, fault, warning flags

Tested with FLA48200 battery and Wi-Fi module listening on TCP port `53970`.

## Installation

1. Copy this repository into your Home Assistant `config` directory, so that you have:

   ```text
   config/
     custom_components/
       felicity_battery/
         __init__.py
         manifest.json
         const.py
         api.py
         config_flow.py
         sensor.py
   ```

2. Restart Home Assistant.

3. Go to **Settings → Devices & Services → Add Integration**.

4. Search for **"Felicity Battery (TCP)"**.

5. Enter:
   - **Name** – any friendly name (e.g. `Felicity FLA48200`),
   - **Host** – IP of the Wi-Fi module (e.g. `192.168.1.68`),
   - **Port** – usually `53970`.

After that you should see one device with multiple sensors.

## Disclaimer

This integration uses an **unofficial local API** discovered by traffic analysis.
It is not affiliated with Felicity. Use at your own risk.
