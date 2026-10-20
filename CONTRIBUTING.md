# 参与 opzi

欢迎提交 Issue 和 Pull Request。当前项目仍处于早期阶段，大功能改动建议先开 Issue 说明使用场景。

## 本地开发

创建 Python 虚拟环境后安装 requirements.txt。Python 负责目录扫描和本机 API；ui/ 为无需前端构建工具的 HTML、CSS、JavaScript 界面。

提交前运行：

```powershell
python -m unittest discover -s tests -v
node --check ui/app.js
```

修改界面时，请检查三栏拖动、窄区域、长文件名、空目录、进入与返回、动画关闭。更改扫描器时，请关注取消、权限错误、链接目录和总量一致性。

## 隐私与范围

- 不要提交个人目录、真实扫描结果、运行日志、访问令牌或本机账号信息。
- 测试使用临时文件或明确的演示目录。
- 当前版本仅读取元数据；删除和清理操作需要独立设计与评审。
- 提交 Pull Request 即表示你有权贡献相关代码，并同意按项目 MIT 许可证分发。
