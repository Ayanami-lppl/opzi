Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
base = fs.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = base
shell.Run "pythonw.exe """ & base & "\app.py""", 0, False
