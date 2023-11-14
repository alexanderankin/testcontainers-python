from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import PosixPath
from tarfile import TarInfo, open as tarfile_open
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .container import DockerContainer


class Transferable(ABC):
    @abstractmethod
    def transfer_to(self, container: 'DockerContainer', location: str):
        pass


@dataclass
class StringTransferable(Transferable):
    contents: str

    def transfer_to(self, container: 'DockerContainer', location: str):
        return self._transfer_to(container, location, self.contents.encode())

    @staticmethod
    def _transfer_to(container: 'DockerContainer', location: str, contents_encoded: bytes):
        location_path = PosixPath(location)
        location_dir = str(location_path.parent)
        container.exec(command=['mkdir', '-p', location_dir])
        container.exec(command=['touch', str(location_path)])

        into = TarInfo(name=location_path.name)
        into.size = len(contents_encoded)
        content_bytes = BytesIO(contents_encoded)

        # setup tar
        output_bytes = BytesIO()
        with tarfile_open(fileobj=output_bytes, mode='w:gz') as tar:
            tar.addfile(into, content_bytes)

        # create tar
        data = output_bytes.getvalue()

        # perform docker api call
        container.get_wrapped_container() \
            .put_archive(location_dir, data)


@dataclass
class BytesTransferable(StringTransferable):
    contents: bytes

    def transfer_to(self, container: 'DockerContainer', location: str):
        return super()._transfer_to(container, location, self.contents)
