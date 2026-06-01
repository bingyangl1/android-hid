"""手机端通用 Python 执行器 - 一次 SSH 运行任意 Python 代码"""
import sys, base64, os, time
code = base64.b64decode(sys.argv[1]).decode()
exec(code)
