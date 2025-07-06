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
