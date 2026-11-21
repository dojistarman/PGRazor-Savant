"""Verify a local Root-only PGSavant candidate without installing it."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pgrazor'))
import axml


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(data):
    result = zipfile.ZipFile(io.BytesIO(data))
    require(len(result.namelist()) == len(set(result.namelist())), 'Duplicate archive members')
    require(result.testzip() is None, 'Archive CRC failure')
    return result


def run(*args):
    return subprocess.run(list(map(str, args)), check=True, capture_output=True, text=True).stdout


def verify(folder, tag, expected_signer, tools, baseline_module):
    folder, tools = Path(folder), Path(tools)
    require(re.fullmatch(r'[0-9a-f]{64}', expected_signer) is not None, 'Expected signer must be SHA-256 hex')
    names = ('PGSavant-Root.apk', 'PGSavant-Root-module.zip')
    data = {name: (folder / name).read_bytes() for name in names}
    hashes = {name: digest(value) for name, value in data.items()}
    checksums = {}
    for line in (folder / 'SHA256SUMS.txt').read_text().splitlines():
        value, name = line.split('  ', 1)
        require(name not in checksums, 'Duplicate checksum name')
        checksums[name] = value
    require(checksums == hashes, 'Release checksums differ from the Root candidate')
    receipt = json.loads((folder / 'root-build-info.json').read_text())
    require(receipt['version'] == tag, 'Build version mismatch')
    require(receipt['installer_sha256'] == hashes[names[0]] and
            receipt['module_sha256'] == hashes[names[1]], 'Build receipt mismatch')
    schema = ROOT / 'pgrazor/native/schema/game'
    profile = json.loads((schema / json.loads((schema / 'current.json').read_text())['profile']).read_text())
    require(receipt['target']['package'] == 'com.nianticlabs.pokemongo' and
            receipt['target']['versionName'] == profile['game_version'] and
            receipt['target']['versionCode'] == profile['version_code'], 'Unsupported game target')

    signed = run(tools / 'apksigner.bat', 'verify', '--print-certs', folder / names[0])
    signers = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)', signed)
    require([value.lower() for value in signers] == [expected_signer], 'Candidate signer mismatch')
    run(tools / 'zipalign.exe', '-c', '4', folder / names[0])
    badging = run(tools / 'aapt.exe', 'dump', 'badging', folder / names[0])
    require("application-label:'PGSavant'" in badging, 'Visible app label mismatch')
    with archive(data[names[0]]) as apk:
        manifest = axml.inspect_manifest(apk.read('AndroidManifest.xml'))
        require(manifest['package'] == 'com.arevj.pgsavant', 'Installer application ID mismatch')
        require(manifest['versionName'] == tag.removeprefix('v'), 'Installer version mismatch')
        require(not manifest['providers'], 'Unexpected installer provider')
        require({a['name'] for a in manifest['activities']} ==
                {'dev.pgrazor.root.InstallerActivity', 'dev.pgrazor.root.RestartActivity'},
                'Unexpected installer activity')
        embedded = [name for name in apk.namelist() if name.startswith('assets/') and name.endswith('.zip')]
        require(len(embedded) == 1 and apk.read(embedded[0]) == data[names[1]], 'Embedded module mismatch')

    with archive(data[names[1]]) as module:
        props = dict(line.split('=', 1) for line in module.read('module.prop').decode().splitlines() if '=' in line)
        require(props['id'] == 'pgsavant' and props['name'] == 'PGSavant' and props['version'] == tag,
                'Module identity mismatch')
        require(module.read('pgrazor/injection-off') == b'', 'Candidate must ship Off')
        require(module.read('pgrazor/toggle-v1') == b'', 'Toggle capability missing')
        for abi, machine in (('arm64-v8a', 183), ('x86_64', 62)):
            loader = module.read('zygisk/' + abi + '.so')
            require(loader[:5] == b'\x7fELF\x02' and struct.unpack_from('<H', loader, 18)[0] == machine,
                    'Loader ABI mismatch: ' + abi)
            require(b'Original PGRazor is On or its state is unknown' in loader and
                    b'/data/adb/modules/pgrazor/pgrazor/injection-off' in loader,
                    'Original-runtime guard missing from loader: ' + abi)
        dex = module.read('pgrazor/classes.dex')
        for value in ('com.arevj.pgsavant', 'pgsavant-root', 'pgsavant-settings-v1.properties',
                      'pgsavant-accounts-v1', 'pgsavant-account-sessions-v1', 'pgsavant-shundo-tried.txt'):
            require(value.encode() in dex, 'Derivative runtime namespace missing: ' + value)
        for value in ('pgrazor-settings-v1.properties', 'pgrazor-accounts-v1', 'pgrazor-account-sessions-v1'):
            require(value.encode() not in dex, 'Original storage namespace retained: ' + value)
        with archive(module.read('pgrazor/payload.zip')) as payload:
            require(json.loads(payload.read('pgrazor/rooted/target.json')) == receipt['target'],
                    'Payload target mismatch')
            with archive(Path(baseline_module).read_bytes()) as original:
                with archive(original.read('pgrazor/payload.zip')) as baseline:
                    notices = [name for name in baseline.namelist() if name.startswith('pgrazor/native-notices/')]
                    require(notices, 'Baseline notices missing')
                    for name in notices:
                        require(payload.read(name) == baseline.read(name), 'Upstream notice changed: ' + name)
    return {'version': tag, 'package': manifest['package'], 'signer': expected_signer,
            'sha256': hashes, 'defaultInjection': 'OFF', 'gameTarget': receipt['target'],
            'nativeAbis': ['arm64-v8a', 'x86_64'], 'upstreamNoticesPreserved': True,
            'installed': False, 'deviceCoexistenceVerified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--expected-signer', required=True)
    parser.add_argument('--build-tools', type=Path, required=True)
    parser.add_argument('--baseline-module', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.folder, args.tag, args.expected_signer.lower(), args.build_tools, args.baseline_module)
    (args.folder / 'pgsavant-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
