#anukak
from .exceptions import TooOldTangosuperVersion
from .version_manager import VersionManager


class Environment:
    def __init__(
        self,
        min_tangosuper_version: str,
        client_name: str,
    ):
        self._REQUIRED_TANGOSUPER_VERSION = min_tangosuper_version
        self._client_name = client_name

    def check_environment(self):
        if self._client_name == 'tangosuper':
            import tangosuper
            if VersionManager.version_tuple(
                tangosuper.__version__,
            ) < VersionManager.version_tuple(
                self._REQUIRED_TANGOSUPER_VERSION,
            ):
                raise TooOldTangosuperVersion(
                    self._REQUIRED_TANGOSUPER_VERSION,
                    tangosuper.__version__,
                )