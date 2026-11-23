"""Installer-only channel activation handles download and verification failures before trusting a key."""
from argparse import Namespace
from contextlib import redirect_stderr
from io import BytesIO, StringIO
from pathlib import Path
import runpy
import subprocess
from unittest import TestCase, main
from unittest.mock import patch
from urllib.error import HTTPError

helper = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                            "pkgs/arche-base/files/usr/bin/arche-enable-rolling"))
activate = helper["activate"]


class BootstrapTests(TestCase):
    def args(self, optional):
        return Namespace(server=helper["CHANNEL"], if_published=optional, key="test-key")

    def test_unavailable_server_leaves_bundled_repo(self):
        for error in (HTTPError(helper["CHANNEL"], 503, "Unavailable", {}, None), TimeoutError()):
            with self.subTest(error=error), patch("os.geteuid", return_value=0), \
                    patch.dict(activate.__globals__, urlopen=lambda *a, **kw: self.raise_error(error)), \
                    patch("subprocess.run") as run, redirect_stderr(StringIO()) as message:
                activate(self.args(True))
                self.assertIn("Keeping the bundled repository", message.getvalue())
                with self.assertRaises(type(error)):
                    activate(self.args(False))
                run.assert_not_called()

    @staticmethod
    def raise_error(error):
        raise error

    def test_invalid_signature_never_installs_key(self):
        def command(args, **kwargs):
            self.assertIn(args[0], ("gpg", "gpgv"))
            return subprocess.CompletedProcess(args, int(args[0] == "gpgv"))

        with patch("os.geteuid", return_value=0), \
                patch.dict(activate.__globals__, urlopen=lambda *a, **kw: BytesIO(b"invalid")), \
                patch("subprocess.run", side_effect=command), redirect_stderr(StringIO()) as message:
            activate(self.args(True))
            self.assertIn("signature verification failed", message.getvalue())
            with self.assertRaises(subprocess.CalledProcessError):
                activate(self.args(False))


if __name__ == "__main__":
    main()
