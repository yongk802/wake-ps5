# Wake PS5 for Home Assistant

Custom Home Assistant integration to wake a PS5 over your local network.

This is a wake-only integration. It does not start a Remote Play session or stream games. It only talks to the PS5 discovery/wake endpoint that Sony uses for Remote Play capable clients, then exposes:

- a `Wake` button entity
- a `Reachable` binary sensor with a `power_state` attribute

## What you need

- Home Assistant
- PS5 and Home Assistant on the same LAN
- PS5 `Remote Play` enabled so the wake endpoint is available
- PS5 set to `Stay Connected to the Internet` in Rest Mode settings
- a PS5 Remote Play registration key

This works for waking a PS5 from Rest Mode and checking whether it is reachable. It does not power on a fully shut down console.

## Install

### HACS

1. Add this repository as a custom repository in HACS.
2. Choose `Integration`.
3. Install `Wake PS5`.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/wake_ps5` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Get a registration key

The wake packet still needs a PS5 registration credential. This integration uses that credential only to send the wake packet; it does not open a Remote Play session.

The simplest path is using `pyremoteplay` once on any machine on the same LAN:

```bash
pip install pyremoteplay
pyremoteplay <PS5_IP> --register
```

After registration, open the generated profile file in `~/.pyremoteplay/.profile.json` and copy the `RegistKey` for your PS5.

Use that `RegistKey` directly in this integration. The integration converts it to the wake credential automatically.

## Configure

1. In Home Assistant, go to `Settings -> Devices & services`.
2. Add `Wake PS5`.
3. Enter:
   - PS5 host or IP
   - registration key (`RegistKey`)
   - optional display name
   - optional polling interval

## Use in automations

The integration creates a button entity. You can wake the console with Home Assistant's built-in button service:

```yaml
action: button.press
target:
  entity_id: button.playstation_5_wake
```

## Notes

- The reachability sensor is `on` when the PS5 responds and `off` when it does not.
- The reachability sensor exposes `power_state` as `on`, `standby`, or `unreachable`.
- If your PS5 switches between Wi-Fi and Ethernet, update the integration if the console IP changes.
