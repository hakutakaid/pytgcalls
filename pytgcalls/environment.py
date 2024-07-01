#anukak
from .exceptions import TooOldPyrogramVersion
from .version_manager import VersionManager


class Environment:
    def __init__(
        self,
        min_pyrogram_version: str,
        client_name: str,
    ):
        self._REQUIRED_PYROGRAM_VERSION = min_pyrogram_version
        self._client_name = client_name

    def check_environment(self):
        if self._client_name == 'pyrogram':
            import pyrogram
            if VersionManager.version_tuple(
                pyrogram.__version__,
            ) < VersionManager.version_tuple(
                self._REQUIRED_PYROGRAM_VERSION,
            ):
                raise TooOldPyrogramVersion(
                    self._REQUIRED_PYROGRAM_VERSION,
                    pyrogram.__version__,
                )