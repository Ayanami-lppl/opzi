# 第三方组件

opzi 的源代码使用 MIT 许可证。第三方组件保留各自的许可证与版权：

- **pywebview**：桌面 WebView 封装，BSD-3-Clause。https://github.com/r0x0r/pywebview
- **pythonnet**：Windows 桌面后端使用的 .NET 互操作组件，MIT。https://github.com/pythonnet/pythonnet
- **Python**：运行时及标准库，Python Software Foundation License。https://www.python.org/psf/license/
- **PyInstaller**：打包工具，GPL-2.0-or-later 并附带允许分发所生成应用的例外。https://pyinstaller.org/en/stable/license.html
- **Microsoft Edge WebView2**：使用 Microsoft 相应许可条款；系统运行时不由本源码仓库分发。https://developer.microsoft.com/microsoft-edge/webview2/

以上是主要组件清单，并非冻结软件包的完整依赖清单。打包脚本会附带已安装 Python 包可识别的许可证文件；发布二进制包时应一并保留这些文件。
