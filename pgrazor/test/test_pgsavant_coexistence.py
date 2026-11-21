"""Execute the actual C++ startup policy without a phone or game process."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import native_build


class PgsavantCoexistenceTests(unittest.TestCase):
    def test_actual_cpp_policy_matrix(self):
        if not shutil.which('node'):
            self.skipTest('Node is required to execute the policy Wasm fixture')
        try:
            ndk, _ = native_build.resolve_ndk(ROOT)
        except RuntimeError as error:
            self.skipTest(str(error))
        compiler = native_build.ndk_tool(ndk, 'clang++')
        with tempfile.TemporaryDirectory(prefix='pgsavant-policy-') as folder:
            output = Path(folder) / 'coexistence.wasm'
            subprocess.run([str(compiler), '--target=wasm32', '-std=c++17', '-O2', '-nostdlib',
                '-Wl,--no-entry', '-Wl,--export=pgsavant_coexistence_matrix',
                str(ROOT / 'zygisk/coexistence_wasm.cpp'), '-o', str(output)], check=True, timeout=60)
            tested = subprocess.run(['node', '-e',
                "const fs=require('node:fs');const m=new WebAssembly.Module(fs.readFileSync(process.argv[1]));"
                "const n=new WebAssembly.Instance(m).exports.pgsavant_coexistence_matrix();"
                "if(n!==64)throw Error('Policy case '+n);console.log('PASS actual C++ policy: '+n+' states');",
                str(output)], check=True, capture_output=True, text=True, timeout=10)
            self.assertIn('PASS actual C++ policy: 64 states', tested.stdout)
