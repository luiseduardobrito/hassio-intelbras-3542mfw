# Intelbras 3542 MF-W Home Assistant Integration

A custom Home Assistant integration for the **Intelbras 3542 MF-W** facial recognition terminal, enabling monitoring and control of access control systems directly from your Home Assistant dashboard.

## 🚀 Features

- **Real-time Door Status Monitoring** - Track whether doors are open or closed
- **Remote Door Control** - Open doors remotely through Home Assistant
- **Live Camera Feed** - View RTSP video stream from the terminal's camera
- **Easy Configuration** - Simple setup through Home Assistant's configuration flow

## 📋 Requirements

- Home Assistant 2021.12 or newer
- Intelbras 3542 MF-W facial recognition terminal
- Network connectivity between Home Assistant and the terminal
- Device credentials (username and password)

## 🔧 Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository to HACS as a custom repository:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add repository URL: `https://github.com/luiseduardobrito/hassio-intelbras_3542mfw`
   - Category: Integration
3. Search for "Intelbras 3542 MF-W" in HACS
4. Install the integration
5. Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from the [releases page](https://github.com/luiseduardobrito/hassio-intelbras_3542mfw/releases)
2. Extract the files to your `custom_components` directory:
   ```
   custom_components/
   └── intelbras_3542mfw/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       ├── const.py
       ├── sensor.py
       ├── camera.py
       └── button.py
   ```
3. Restart Home Assistant

## ⚙️ Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Intelbras 3542 MF-W"
3. Fill in the required information:
   - **Host**: IP address or hostname of your device (e.g., `http://192.168.1.123`)
   - **Username**: Device authentication username
   - **Password**: Device authentication password
   - **Verify SSL**: Enable if using HTTPS with valid certificates

## 🏠 Entities Created

After successful configuration, the following entities will be available:

### Sensors

- **Door Status** (`sensor.door_status`)
  - Shows current door state (open/closed)
  - Updates every 60 seconds
  - Provides device information and configuration URL

### Camera

- **Intelbras Camera** (`camera.intelbras_camera`)
  - Live RTSP video stream from the terminal
  - Supports both HTTP and HTTPS connections
  - Automatic protocol selection based on SSL settings

### Buttons

- **Open Door** (`button.open_door`)
  - Remotely trigger door opening
  - Sends command directly to the terminal
  - Provides immediate feedback on success/failure

## 🛠️ Troubleshooting

### Common Issues

**Connection Failed**

- Verify the device IP address and network connectivity
- Ensure the username and password are correct
- Check if the device web interface is accessible
- Disable SSL verification if using self-signed certificates

**No Camera Stream**

- Verify RTSP is enabled on the device (port 554)
- Check firewall settings on both Home Assistant and device
- Ensure proper authentication credentials

### Debug Logging

Enable debug logging by adding to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.intelbras_3542mfw: debug
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ℹ️ Disclaimer

This integration is not officially affiliated with or endorsed by Intelbras. It is an independent project created to enhance Home Assistant functionality with Intelbras devices.

## Intelbras 3542 MFW Home Assistant Integration

This integration provides comprehensive monitoring and control capabilities for the Intelbras 3542 MFW video doorbell, including real-time event processing and Home Assistant event firing.

### Features

- **Camera Stream**: Live video feed from your doorbell
- **Door Control**: Open door via Home Assistant
- **Event Monitoring**: Real-time event processing with Home Assistant event bus integration
- **Sensors**: Multiple sensors for monitoring device status and events
- **Webhook Support**: Receive real-time notifications via webhooks

### Installation

1. Copy the `intelbras_3542mfw` folder to your `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "Intelbras 3542 MFW"
5. Enter your device configuration:
   - Host: IP address of your device
   - Username: Device username
   - Password: Device password
   - Verify SSL: Whether to verify SSL certificates

### Event System

The integration automatically fires Home Assistant events when new records are detected from the device. This allows you to create powerful automations based on doorbell events.

#### Event Structure

When new events are detected, the integration fires events of type `intelbras_3542mfw_event` with the following structure:

```yaml
event_type: intelbras_3542mfw_event
data:
  device_id: "abc123def456"  # Device ID for attribution
  type: "intelbras_event"
  RecNo: 12345              # Record number
  CreateTime: 1640995200    # Unix timestamp
  Door: 1                   # Door number
  Method: 1                 # Access method
  UserID: "user123"         # User identifier
  Status: 1                 # Event status
  # ... other event data
```

#### Creating Automations

Here are examples of how to create automations that respond to doorbell events:

##### Basic Event Notification

```yaml
automation:
  - alias: "Doorbell Event Notification"
    trigger:
      - platform: event
        event_type: intelbras_3542mfw_event
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Doorbell Event"
          message: "Event detected: {{ trigger.event.data.Method }} at door {{ trigger.event.data.Door }}"
          data:
            badge: 1
```

##### Door Access Log

```yaml
automation:
  - alias: "Log Door Access"
    trigger:
      - platform: event
        event_type: intelbras_3542mfw_event
        event_data:
          Method: 1  # Assuming 1 = card access
    action:
      - service: logbook.log
        data:
          name: "Door Access"
          message: "Card access by user {{ trigger.event.data.UserID }}"
          entity_id: sensor.intelbras_last_event
```

##### Conditional Response Based on Time

```yaml
automation:
  - alias: "After Hours Door Alert"
    trigger:
      - platform: event
        event_type: intelbras_3542mfw_event
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.porch_light
      - service: notify.family_group
        data:
          title: "After Hours Door Activity"
          message: "Door event detected at {{ now().strftime('%H:%M') }}"
```

##### Smart Security Response

```yaml
automation:
  - alias: "Security Event Response"
    trigger:
      - platform: event
        event_type: intelbras_3542mfw_event
    condition:
      # Only trigger if nobody is home
      - condition: state
        entity_id: group.family
        state: "not_home"
    action:
      # Take a snapshot
      - service: camera.snapshot
        target:
          entity_id: camera.intelbras_3542_mfw
        data:
          filename: "/config/www/security_snapshot_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
      # Send notification with image
      - service: notify.mobile_app_your_phone
        data:
          title: "🚨 Security Alert"
          message: "Door activity while away!"
          data:
            image: "/local/security_snapshot_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
```

### Available Sensors

The integration provides several sensors:

1. **Door Status** (`sensor.door_status`): Current door status
2. **Events Count** (`sensor.events_count`): Total number of events received
3. **Last Event** (`sensor.last_event`): Details of the most recent event

### Event Data Fields

The events may contain the following fields (depending on your device configuration):

- `RecNo`: Unique record number
- `CreateTime`: Event timestamp
- `Door`: Door number (for multi-door setups)
- `Method`: Access method (card, remote, etc.)
- `UserID`: User identifier
- `Status`: Event status code
- `AttendanceState`: Attendance tracking state
- `CardType`: Type of access card used
- `ErrorCode`: Error code if applicable
- `ReaderID`: Card reader identifier

### Debugging Events

To debug and see what events are being fired, you can:

1. **Use the Events tab in Developer Tools**:
   - Go to Developer Tools > Events
   - Listen for `intelbras_3542mfw_event`
   - Trigger an event on your device to see the data structure

2. **Enable debug logging**:
   ```yaml
   logger:
     logs:
       custom_components.intelbras_3542mfw: debug
   ```

3. **Create a debug automation**:
   ```yaml
   automation:
     - alias: "Debug Intelbras Events"
       trigger:
         - platform: event
           event_type: intelbras_3542mfw_event
       action:
         - service: persistent_notification.create
           data:
             title: "Intelbras Event Debug"
             message: "{{ trigger.event.data }}"
   ```

### Webhook Support

The integration also supports webhooks for real-time event delivery. Webhook events are fired as `intelbras_3542_mfw_webhook` events and can be used in automations similarly to the coordinator events.

### Troubleshooting

If events are not firing:

1. Check that the coordinator is properly initialized in the logs
2. Verify your device credentials are correct
3. Ensure the device is accessible from Home Assistant
4. Check the polling interval (default 30 seconds)
5. Enable debug logging to see detailed event processing

For issues with event parsing:
1. Check the raw event data in the logs
2. Verify the event parser is handling your device's event format
3. Consider adjusting the event signature fields in the coordinator if needed
