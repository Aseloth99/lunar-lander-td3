"""<proje_klasörü>/.pydeps altındaki paketleri sys.path'in başına ekler.

Her betik en üstte `import _deps` yapar; böylece PYTHONPATH ayarlamak gerekmez.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DEPS = os.path.join(ROOT, ".pydeps")

if os.path.isdir(DEPS) and DEPS not in sys.path:
    sys.path.insert(0, DEPS)
    # swig sarmalayıcısı vb. için
    os.environ["PATH"] = os.path.join(DEPS, "bin") + os.pathsep + os.environ.get("PATH", "")
