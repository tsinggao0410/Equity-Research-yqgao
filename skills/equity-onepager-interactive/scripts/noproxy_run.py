# -*- coding: utf-8 -*-
"""noproxy launcher —— 本机 macOS 系统代理(_scproxy)会注入 requests/urllib 掐死国内行情腿。
在 import 目标脚本前把三处代理开关全部关掉,并给 requests 挂上重试。
用法: python3 noproxy_run.py <目标脚本.py> [目标脚本的参数...]
"""
import sys, os, runpy, importlib.util

# 1) urllib 层
import urllib.request
urllib.request.getproxies = lambda: {}
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

# 2) requests 层
try:
    import requests
    import requests.utils
    from requests.adapters import HTTPAdapter
    try:
        from urllib3.util.retry import Retry
    except Exception:
        from requests.packages.urllib3.util.retry import Retry  # type: ignore

    requests.utils.should_bypass_proxies = lambda *a, **k: True
    _orig_init = requests.Session.__init__

    def _patched_init(self, *a, **k):
        _orig_init(self, *a, **k)
        self.trust_env = False
        self.proxies = {}
        retry = Retry(total=8, backoff_factor=1.2,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=None)
        self.mount("http://", HTTPAdapter(max_retries=retry))
        self.mount("https://", HTTPAdapter(max_retries=retry))

    requests.Session.__init__ = _patched_init
except Exception as e:  # pragma: no cover
    print("[noproxy] requests patch skipped:", e, file=sys.stderr)

# 3) 环境变量层
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

target = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(target)))
spec = importlib.util.spec_from_file_location("__main__", target)
mod = importlib.util.module_from_spec(spec)
sys.modules["__main__"] = mod
spec.loader.exec_module(mod)
