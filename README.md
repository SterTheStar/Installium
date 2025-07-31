# Installium

Installium is a lightweight, user-friendly tool for installing packages on Linux distributions quickly and efficiently. Designed for users who want to avoid the terminal without losing control.

<img width="762" height="522" alt="imagem" src="https://github.com/user-attachments/assets/8725b37e-5af7-4ed7-ab6b-6c984f657a94" />

## 📦 Supported Distributions

| Distribution         | Format                  | Command |
|----------------------|-------------------------|---------|
| Debian/Ubuntu        | .deb                    | dpkg    |
| Arch Linux/Manjaro   | .pkg.tar.xz, .pkg.tar.zst | pacman  |
| Fedora/RHEL/CentOS   | .rpm                    | rpm     |
| Alpine Linux         | .apk                    | apk     |

## 🎯 How to Use

### Method 1: Double Click
1. After installation, double-click any supported package file
2. The installer will automatically open with the package details
3. Click "Install" to proceed

### Method 2: Command Line
```bash
Installium [path_to_package]
```

### Method 3: Application Menu
1. Look for "Universal Package Installer" in your app menu
2. Launch the application
3. Click "Select Package" to choose a file

## 📝 License

This project is licensed under the GPL-3.0

## 🤝 Contributions

Contributions are welcome! Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests
- Add support for new distributions
