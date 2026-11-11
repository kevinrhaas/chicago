#!/usr/bin/env python3
"""Keep browser setup usable during Ubuntu archive DNS failures.

GitHub's Ubuntu 24.04 image uses apt-mirrors.txt for all Noble suites. The
2026-11-11 Prairie checks failed before opening a browser because every default
Ubuntu hostname failed DNS. On that failure only, prefer Kernel.org's Ubuntu
mirror after verifying every suite against the runner's existing Ubuntu keyring.
APT still performs its normal signature, expiry and package-hash checks.

Run --self-test for isolated tests; default execution is for the CI runner only.
"""
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit

MIRROR = 'https://mirrors.edge.kernel.org/ubuntu'
SUITES = ('noble', 'noble-updates', 'noble-backports', 'noble-security')
DEFAULT_HOSTS = {'azure.archive.ubuntu.com', 'archive.ubuntu.com', 'security.ubuntu.com'}


def mirror_url(line):
    fields = line.split()
    return fields[0].rstrip('/') if fields and not fields[0].startswith('#') else ''


def prefer_mirror(text):
    # apt-transport-mirror(1): lower explicit priorities run first; line order
    # alone is random. Preserve the runner's original fallback priorities.
    return MIRROR + '\tpriority:0\n' + ''.join(
        line for line in text.splitlines(keepends=True) if mirror_url(line) != MIRROR)


def prepare(root=Path('/'), run=subprocess.run):
    release = root / 'etc/os-release'
    if not release.is_file():
        print('Browser APT mirrors unchanged: no OS release record.')
        return False
    os_info = dict(line.split('=', 1) for line in release.read_text().splitlines()
                   if '=' in line and not line.startswith('#'))
    if (os_info.get('ID', '').strip('"\'') != 'ubuntu'
            or os_info.get('VERSION_ID', '').strip('"\'') != '24.04'):
        print('Browser APT mirrors unchanged: this is not Ubuntu 24.04.')
        return False
    targets = []
    for name in ('apt-mirrors.txt', 'apt-mirrors-security.txt'):
        file = root / 'etc/apt' / name
        if not file.is_file():
            continue
        text = file.read_text()
        first = next((line.strip() for line in text.splitlines()
                      if line.strip() and not line.lstrip().startswith('#')), '')
        host = urlsplit(mirror_url(first)).hostname
        if host in DEFAULT_HOSTS:
            targets.append((file, text, host))
    if not targets:
        print('Browser APT mirrors unchanged: no default Ubuntu mirror list to repair.')
        return False
    failed_hosts = []
    for host in sorted({item[2] for item in targets}):
        try:
            result = run(['getent', 'ahosts', host], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, timeout=10, check=False)
            if result.returncode:
                failed_hosts.append(host)
        except subprocess.TimeoutExpired:
            failed_hosts.append(host)
    if not failed_hosts:
        print('Browser APT mirrors unchanged: default mirror DNS is available.')
        return False
    keyring = root / 'usr/share/keyrings/ubuntu-archive-keyring.gpg'
    if not keyring.is_file():
        raise RuntimeError('Refusing mirror change without the installed Ubuntu archive keyring')
    # Verify every suite before making any configuration change. No downloaded
    # signing key is trusted, and none of APT's trust settings are changed.
    with tempfile.TemporaryDirectory(prefix='ubuntu-browser-mirror-') as directory:
        for suite in SUITES:
            signed = Path(directory) / f'{suite}.InRelease'
            run(['curl', '--fail', '--silent', '--show-error', '--location',
                 '--connect-timeout', '10', '--max-time', '30', '--retry', '1',
                 '--max-filesize', '2097152', '--output', str(signed),
                 f'{MIRROR}/dists/{suite}/InRelease'], check=True, timeout=75)
            run(['gpgv', '--keyring', str(keyring), str(signed)], check=True, timeout=15)
    for file, text, _ in targets:
        run(['sudo', '-n', 'tee', str(file)], input=prefer_mirror(text),
            text=True, stdout=subprocess.DEVNULL, check=True, timeout=10)
    print(f'Ubuntu DNS unavailable for {", ".join(failed_hosts)}; '
          f'preferred verified mirror {MIRROR} in {len(targets)} list(s).')
    return True


def self_test():
    import contextlib
    import io
    import unittest

    class MirrorTests(unittest.TestCase):
        def setUp(self):
            self.directory = tempfile.TemporaryDirectory()
            self.addCleanup(self.directory.cleanup)
            self.root = Path(self.directory.name)
            (self.root / 'etc/apt').mkdir(parents=True)
            (self.root / 'etc/os-release').write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
            self.keyring = self.root / 'usr/share/keyrings/ubuntu-archive-keyring.gpg'
            self.keyring.parent.mkdir(parents=True)
            self.keyring.write_bytes(b'fixture keyring; never used by real gpgv')
            self.main = self.root / 'etc/apt/apt-mirrors.txt'
            self.original = '# existing fallbacks\nhttp://azure.archive.ubuntu.com/ubuntu\tpriority:1\nhttps://archive.ubuntu.com/ubuntu\tpriority:2\n'
            self.main.write_text(self.original)
            self.calls = []
            self.dns_ok = True
            self.fail_command = None
            self.dns_timeout = False

        def fake_run(self, command, **kwargs):
            self.calls.append((command, kwargs))
            if command[0] == self.fail_command:
                raise subprocess.CalledProcessError(1, command)
            if command[0] == 'getent':
                if self.dns_timeout:
                    raise subprocess.TimeoutExpired(command, 10)
                return subprocess.CompletedProcess(command, 0 if self.dns_ok else 2)
            if command[0] == 'curl':
                Path(command[command.index('--output') + 1]).write_text('fixture signed metadata')
            elif command[0] == 'sudo':
                Path(command[-1]).write_text(kwargs['input'])
            return subprocess.CompletedProcess(command, 0)

        def invoke(self):
            with contextlib.redirect_stdout(io.StringIO()):
                return prepare(self.root, self.fake_run)

        def test_healthy_defaults_untouched(self):
            self.assertFalse(self.invoke())
            self.assertEqual(self.main.read_text(), self.original)
            self.assertEqual([c[0][0] for c in self.calls], ['getent'])

        def test_dns_failure_verifies_all_suites_before_writing(self):
            self.dns_ok = False
            security = self.main.with_name('apt-mirrors-security.txt')
            security.write_text('https://security.ubuntu.com/ubuntu\n')
            self.assertTrue(self.invoke())
            self.assertEqual(self.main.read_text(), MIRROR + '\tpriority:0\n' + self.original)
            self.assertTrue(security.read_text().startswith(MIRROR + '\tpriority:0\n'))
            commands = [c[0] for c in self.calls]
            self.assertEqual([c[-1] for c in commands if c[0] == 'curl'],
                             [f'{MIRROR}/dists/{s}/InRelease' for s in SUITES])
            self.assertEqual(sum(c[0] == 'gpgv' for c in commands), 4)
            self.assertLess(max(i for i, c in enumerate(commands) if c[0] == 'gpgv'),
                            min(i for i, c in enumerate(commands) if c[0] == 'sudo'))
            self.assertTrue(all(str(self.keyring) in c for c in commands if c[0] == 'gpgv'))

        def test_bad_signature_leaves_all_lists_untouched(self):
            self.dns_ok = False
            self.fail_command = 'gpgv'
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke()
            self.assertEqual(self.main.read_text(), self.original)
            self.assertFalse(any(c[0][0] == 'sudo' for c in self.calls))

        def test_download_failure_leaves_lists_untouched(self):
            self.dns_ok = False
            self.fail_command = 'curl'
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke()
            self.assertEqual(self.main.read_text(), self.original)

        def test_missing_keyring_refuses_change(self):
            self.dns_ok = False
            self.keyring.unlink()
            with self.assertRaises(RuntimeError):
                self.invoke()
            self.assertFalse(any(c[0][0] in ('curl', 'sudo') for c in self.calls))

        def test_timeout_uses_verified_fallback(self):
            self.dns_timeout = True
            self.assertTrue(self.invoke())
            self.assertTrue(self.main.read_text().startswith(MIRROR + '\tpriority:0\n'))

        def test_existing_mirror_is_idempotent(self):
            self.main.write_text(MIRROR + '\tpriority:0\n' + self.original)
            self.assertFalse(self.invoke())
            self.assertEqual(self.main.read_text().count(MIRROR), 1)
            self.assertFalse(self.calls)

        def test_deduplicates_prioritized_mirror(self):
            original = self.original + MIRROR + '/\tpriority:9\n'
            preferred = prefer_mirror(original)
            self.assertEqual(preferred, MIRROR + '\tpriority:0\n' + self.original)

        def test_other_distribution_is_untouched(self):
            (self.root / 'etc/os-release').write_text('ID=debian\nVERSION_ID="13"\n')
            self.assertFalse(self.invoke())
            self.assertFalse(self.calls)

        def test_missing_lists_are_untouched(self):
            self.main.unlink()
            self.assertFalse(self.invoke())
            self.assertFalse(self.calls)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MirrorTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--self-test']:
        raise SystemExit(0 if self_test() else 1)
    if sys.argv[1:]:
        raise SystemExit('usage: prepare-ubuntu-browser-mirrors.py [--self-test]')
    prepare()
